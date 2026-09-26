# Sharpest-frame extraction from phone videos for the RealityScan site mesh (R1 photogrammetry, see
# docs/roles/R1-photogrammetry-handoff.md section 2). Pass 1 decodes a small grey proxy through ffmpeg and scores
# every frame (variance of the Laplacian); pass 2 writes the best frame of each 1/fps window as a full-res JPEG
# named <clip>_f<frame>.jpg. Frames contain people: write them outside the repo only. A clip folder that already
# holds JPEGs is skipped (delete it to redo).
# Usage: python select_frames.py --out C:/koch/work/frames --fps 3 raw/PXL_a.mp4 raw/PXL_b.mp4 ...
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE", "ffprobe")
PROXY_LONG = 960  # px, long side of the scoring proxy


def probe(video):
    j = json.loads(subprocess.run([FFPROBE, "-v", "error", "-print_format", "json", "-show_streams", "-show_format",
                                   video], capture_output=True, check=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    rot = 0
    for sd in v.get("side_data_list", []):
        rot = int(sd.get("rotation", rot))
    w, h = int(v["width"]), int(v["height"])
    if abs(rot) % 180 == 90:  # ffmpeg autorotates on decode, so frames come out with swapped sides
        w, h = h, w
    return w, h, float(j["format"]["duration"])


def score_frames(video, w, h):
    """Per decoded frame: sharpness (variance of the Laplacian, grey proxy) and image motion from the previous
    frame (phase-correlation shift, as a fraction of the proxy width; pans and walking both show up as shift)."""
    s = PROXY_LONG / max(w, h)
    pw, ph = int(round(w * s / 2)) * 2, int(round(h * s / 2)) * 2
    cmd = [FFMPEG, "-v", "error", "-hwaccel", "auto", "-i", video, "-map", "0:v:0", "-fps_mode", "passthrough",
           "-vf", f"scale={pw}:{ph}", "-pix_fmt", "gray", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = pw * ph
    scores, motion, prev = [], [], None
    win = None
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        g = np.frombuffer(buf, np.uint8).reshape(ph, pw)
        scores.append(cv2.Laplacian(g, cv2.CV_32F).var())
        small = cv2.resize(g, (pw // 2, ph // 2), interpolation=cv2.INTER_AREA).astype(np.float32)
        if win is None:
            win = cv2.createHanningWindow(small.shape[::-1], cv2.CV_32F)
        if prev is None:
            motion.append(0.0)
        else:
            (dx, dy), _ = cv2.phaseCorrelate(prev, small, win)
            motion.append(float(np.hypot(dx, dy)) / small.shape[1])
        prev = small
    p.wait()
    return np.array(scores, np.float32), np.array(motion, np.float32)


def pick(scores, motion, frame_rate, fps, min_rel, max_shift):
    """Best frame per window of frame_rate/fps frames; drop windows far blurrier than the clip median. Adaptive:
    when the image has moved more than max_shift (fraction of the width) since the last pick, an extra pick is
    forced (sharpest of the frames just before the limit), so fast pans keep overlapping neighbours."""
    n = len(scores)
    if n == 0:
        return []
    win = max(1, int(round(frame_rate / fps)))
    med = float(np.median(scores))
    cum = np.concatenate([[0.0], np.cumsum(motion[1:])])   # cum[k]: image shift accumulated from frame 0 to k
    out, last = [], None
    while True:
        if last is None:
            lo, hi, by_motion = 0, min(n, win), False
        else:
            if last >= n - 1:
                break
            m = int(np.searchsorted(cum, cum[last] + max_shift, side="right"))  # first frame past the shift limit
            hi_t = last + win
            by_motion = m <= hi_t
            hi = min(n, m if by_motion else hi_t + 1)
            lo = min(last + max(1, win // 2), hi - 1)          # not too close to the last pick
            lo = max(lo, last + 1)
            if lo >= hi:
                hi = lo + 1
            if lo >= n:
                break
        j = lo + int(np.argmax(scores[lo:hi]))
        if last is None or by_motion or scores[j] >= min_rel * med:
            out.append(j)  # motion-forced picks are kept even when soft: they hold the chain together
        last = j
    return out


def select_expr(picks):
    """ffmpeg select expression true on the picked frame indices, as a balanced sum: a flat 'eq+eq+...' chain
    fails to parse past ~100 terms (recursion limit, reported as ENOMEM); a balanced tree stays ~log2(n) deep."""
    terms = [f"eq(n\\,{k})" for k in picks]
    while len(terms) > 1:
        terms = [f"({terms[i]}+{terms[i + 1]})" if i + 1 < len(terms) else terms[i] for i in range(0, len(terms), 2)]
    return terms[0]


def extract(video, picks, out_dir, clip):
    """Write the picked frames (decode-order index n) as full-res JPEGs in one decode."""
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([FFMPEG, "-v", "error", "-y", "-hwaccel", "auto", "-i", video, "-map", "0:v:0",
                    "-fps_mode", "passthrough", "-vf", f"select='{select_expr(picks)}'", "-q:v", "2",
                    os.path.join(tmp, "%05d.jpg")], check=True)
    for i, k in enumerate(picks):
        os.replace(os.path.join(tmp, f"{i + 1:05d}.jpg"), os.path.join(out_dir, f"{clip}_f{k:05d}.jpg"))
    os.rmdir(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--out", required=True, help="root folder; one subfolder per clip")
    ap.add_argument("--fps", type=float, default=3.0, help="frames kept per second of video")
    ap.add_argument("--min-rel", type=float, default=0.35, help="drop picks sharper than this x clip median only")
    ap.add_argument("--max-shift", type=float, default=0.12,
                    help="force a pick once the image moved this fraction of its width since the last one")
    a = ap.parse_args()
    log = []
    for v in a.videos:
        clip = os.path.splitext(os.path.basename(v))[0].replace("PXL_", "")
        out_dir = os.path.join(a.out, clip)
        if os.path.isdir(out_dir) and any(f.endswith(".jpg") for f in os.listdir(out_dir)):
            print("skip (done)", clip)
            continue
        w, h, dur = probe(v)
        scores, motion = score_frames(v, w, h)
        rate = len(scores) / dur if dur > 0 else 30.0
        picks = pick(scores, motion, rate, a.fps, a.min_rel, a.max_shift)
        extract(v, picks, out_dir, clip)
        rec = {"clip": clip, "w": w, "h": h, "dur": round(dur, 2), "frames": len(scores), "picked": len(picks),
               "median_sharp": round(float(np.median(scores)), 1)}
        log.append(rec)
        print(json.dumps(rec), flush=True)
    with open(os.path.join(a.out, "select_log.jsonl"), "a") as f:
        for r in log:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    sys.exit(main())
