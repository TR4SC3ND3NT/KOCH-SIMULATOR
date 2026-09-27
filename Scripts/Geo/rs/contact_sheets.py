# Contact sheets for triaging third-party campus videos (R1 photogrammetry): N frames evenly over each video, tiled
# with their timestamps, one JPEG per video in <out>. Used to pick the campus parts (drone, exteriors, stairs) that
# are worth frames for alignment or reference. Media contains people: keep outputs outside the repo.
# Usage: python contact_sheets.py --out C:/koch/web/sheets --n 20 C:/koch/web/koch_web_media/videos/*.mp4
import argparse
import glob
import json
import os
import subprocess
import sys

import cv2
import numpy as np

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE", "ffprobe")


def duration(v):
    j = json.loads(subprocess.run([FFPROBE, "-v", "error", "-print_format", "json", "-show_format", v],
                                  capture_output=True, check=True).stdout)
    return float(j["format"]["duration"])


def grab(v, t, w):
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.2f}", "-i", v, "-frames:v", "1", "-vf", f"scale={w}:-2",
                        "-f", "image2pipe", "-vcodec", "mjpeg", "-"], capture_output=True)
    if not r.stdout:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--w", type=int, default=360)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    vids = [p for g in a.videos for p in (glob.glob(g) or [g])]
    for v in sorted(vids):
        name = os.path.splitext(os.path.basename(v))[0]
        dst = os.path.join(a.out, name + ".jpg")
        if os.path.exists(dst):
            continue
        try:
            dur = duration(v)
        except Exception as ex:
            print("skip", name, ex)
            continue
        tiles = []
        for k in range(a.n):
            t = dur * (k + 0.5) / a.n
            im = grab(v, t, a.w)
            if im is None:
                im = np.zeros((a.w * 9 // 16, a.w, 3), np.uint8)
            cv2.putText(im, f"{int(t // 60)}:{t % 60:04.1f}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
            cv2.putText(im, f"{int(t // 60)}:{t % 60:04.1f}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            tiles.append(im)
        h = max(t.shape[0] for t in tiles)
        tiles = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 0, cv2.BORDER_CONSTANT) for t in tiles]
        rows = [np.hstack(tiles[i:i + a.cols]) for i in range(0, len(tiles), a.cols)]
        rows[-1] = np.hstack([rows[-1], np.zeros((h, rows[0].shape[1] - rows[-1].shape[1], 3), np.uint8)])
        sheet = np.vstack(rows)
        cv2.imwrite(dst, sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
        print(f"{name}: {dur:.0f} s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
