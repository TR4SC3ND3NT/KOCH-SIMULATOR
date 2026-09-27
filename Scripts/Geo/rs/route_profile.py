# Walking-route level profile from the owner's videos (R1 photogrammetry, handoff section 0 pass P0/P1 "levels"):
# the phone was carried at a near-constant height, so the solved camera centres of one clip, ordered by time, trace
# the ground the owner walked on (ground = camera z - eye height). Every step, stair, ramp and level change on the route
# shows up as a jump or slope in that profile, with the frames around it, so levels are set from measurements and only
# the frames at the detected events need to be looked at (riser count, kerb, ramp).
#   - eye height: per clip, median(camera z - mesh ground under the camera) when --mesh is given, else --eye;
#   - level changes: two-window median difference along the walked distance (robust to gait bob and hand shake),
#     peaks above --thr become events between flat levels; each event gets class stair/step/ramp and a riser hint;
#   - frames seen in two zones' models give the zone-to-zone registration error in world metres (P0 control check).
# Output (<out>): <clip>.csv (samples), <clip>.png (profile plot), route.json (all clips, for Scripts/Blender/
# route_check.py), and a short summary on stdout (one line per event). Frames contain people: keep <out> outside git.
# Usage: python route_profile.py --zone zones/Gate/model.json zones/Gate/align.json [--zone ...] --out C:/koch/work/route
#          [--mesh world_mesh.ply] [--clips 20260924_070410255,...] [--video-fps 60] [--eye 1.45] [--win 0.8] [--thr 0.06]
import argparse
import json
import math
import os
import re
import sys

import cv2
import numpy as np

RISER = 0.15          # m, typical riser, only for the riser-count hint (confirm in the event frames)
NEW_NAME = re.compile(r"(\d{8}_\d{9})_f(\d+)\.\w+$")                 # select_frames.py: <clip>_fNNNNN.jpg
OLD_NAME = re.compile(r"v\d+_(\d{9})[/\\](\d+)\.\w+$")               # early extraction: v00_<id>/NNNN.jpg


def parse(name, video_fps, old_fps):
    m = NEW_NAME.search(name)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(2)) / video_fps
    m = OLD_NAME.search(name)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(2)) / old_fps
    return None       # stills and other image sets are not walks


def load_zone(model_path, align_path, a):
    model, al = json.load(open(model_path)), json.load(open(align_path))
    s, Rw, tw = al["scale"], np.array(al["R"]), np.array(al["t"])
    zone = model.get("zone") or os.path.basename(os.path.dirname(os.path.abspath(model_path)))
    out = {}
    for c in model["cameras"]:
        p = parse(c["name"], a.video_fps, a.old_fps)
        if p is None:
            continue
        clip, k, t = p
        pos = s * Rw @ np.array(c["center"]) + tw
        fwd = Rw @ np.array(c["R"]).T @ np.array([0.0, 0.0, 1.0])       # optical axis in world (COLMAP +Z forward)
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, fwd[2] / np.linalg.norm(fwd)))))
        out[(clip, k)] = {"t": t, "pos": pos, "pitch": pitch, "name": c["name"], "zone": zone}
    return zone, out


def rolling_median(v, n):
    h = n // 2
    return np.array([np.median(v[max(0, i - h):i + h + 1]) for i in range(len(v))])


def clean(S):
    """Drop pose outliers (bad registrations): Hampel filter on x, y, z over 7 samples, floor 0.3 m."""
    P = np.array([q["pos"] for q in S])
    keep = np.ones(len(S), bool)
    for d in range(3):
        med = rolling_median(P[:, d], 7)
        dev = np.abs(P[:, d] - med)
        mad = rolling_median(dev, 7) * 1.4826
        keep &= dev <= np.maximum(3 * mad, 0.3)
    # the phone tilted far from the walking posture (lowered at a clip end, raised to film a facade): the camera is
    # then not at the eye height above the ground, so the pose says nothing about the level
    pitch = np.array([q["pitch"] for q in S])
    keep &= np.abs(pitch - np.median(pitch)) <= 12.0
    return [q for q, k in zip(S, keep) if k]


def ground_from_mesh(P, mesh_path, eye_min):
    """Mesh ground under each camera: highest hit below z_cam - eye_min (skips railings/arms), median of 5 rays."""
    import trimesh
    lo, hi = P[:, :2].min(0) - 3.0, P[:, :2].max(0) + 3.0
    m = trimesh.load(mesh_path, force="mesh", process=False)
    c = m.triangles_center
    keep = np.nonzero((c[:, 0] >= lo[0]) & (c[:, 0] <= hi[0]) & (c[:, 1] >= lo[1]) & (c[:, 1] <= hi[1]))[0]
    g = np.full(len(P), np.nan)
    if not len(keep):
        return g
    m = m.submesh([keep], append=True)
    offs = np.array([[0, 0], [0.2, 0], [-0.2, 0], [0, 0.2], [0, -0.2]])
    O = np.repeat(P, len(offs), 0)
    O[:, :2] += np.tile(offs, (len(P), 1))
    D = np.tile([0.0, 0.0, -1.0], (len(O), 1))
    loc, ray, _ = m.ray.intersects_location(O, D, multiple_hits=True)
    best = np.full(len(O), np.nan)
    for z, r in zip(loc[:, 2], ray):
        if z < O[r, 2] - eye_min and not (best[r] >= z):
            best[r] = z
    best = best.reshape(len(P), len(offs))
    ok = np.isfinite(best).sum(1) >= 3
    g[ok] = np.nanmedian(best[ok], 1)
    return g


def levels_and_events(s, g, win, thr):
    """Two-window median difference along s; peaks of |d| > thr are change points, flat medians between are levels."""
    n = len(s)
    d = np.zeros(n)
    for i in range(n):
        L = g[(s >= s[i] - win) & (s < s[i])]
        R = g[(s > s[i]) & (s <= s[i] + win)]
        if len(L) >= 2 and len(R) >= 2:
            d[i] = np.median(R) - np.median(L)
    cps = []
    for i in np.argsort(-np.abs(d)):
        if abs(d[i]) < thr:
            break
        if s[i] < win or s[i] > s[-1] - win:      # half-empty windows at the clip ends give false steps
            continue
        if all(abs(s[i] - s[j]) >= win for j in cps):
            cps.append(i)
    cps.sort()
    while True:     # levels between change points; merge neighbours that differ by less than thr
        bounds = [0] + cps + [n - 1]
        lev = []
        for a, b in zip(bounds[:-1], bounds[1:]):
            sel = (s >= s[a] + (win / 2 if a else 0)) & (s <= s[b] - (win / 2 if b != n - 1 else 0))
            if sel.sum() < 2:
                sel = (s >= s[a]) & (s <= s[b])
            lev.append(float(np.median(g[sel])))
        weak = [k for k in range(len(cps)) if abs(lev[k + 1] - lev[k]) < thr]
        if not weak:
            return lev, cps, d
        cps.pop(min(weak, key=lambda k: abs(lev[k + 1] - lev[k])))


def classify(s, g, cp, l0, l1, tol):
    """Extent of the transition (last sample on l0 before, first on l1 after) -> run, grade, class."""
    i = cp
    while i > 0 and abs(g[i] - l0) > tol:
        i -= 1
    j = cp
    while j < len(g) - 1 and abs(g[j] - l1) > tol:
        j += 1
    dz = l1 - l0
    run = float(s[j] - s[i])
    grade = abs(dz) / max(run, 0.3)
    n = max(1, round(abs(dz) / RISER))
    if grade <= 0.12 and run > 1.5:
        kind = "ramp/slope"
    elif n == 1 and run < 1.2:
        kind = "step"
    elif grade >= 0.25:
        kind = "stair"
    else:
        kind = "stair or ramp?"
    return i, j, dz, run, grade, kind, n


def plot(path, s, gc, gm, lev, cps, ev, clip):
    W, H, m = 1600, 560, 60
    zs = np.concatenate([gc, gm[np.isfinite(gm)]])
    z0, z1 = float(np.min(zs)) - 0.2, float(np.max(zs)) + 0.2
    s1 = max(float(s[-1]), 1.0)
    X = lambda v: int(m + (W - 2 * m) * v / s1)
    Y = lambda z: int(H - m - (H - 2 * m) * (z - z0) / max(z1 - z0, 0.5))
    img = np.full((H, W, 3), 255, np.uint8)
    for zg in np.arange(math.floor(z0 * 10) / 10, z1, 0.1):
        cv2.line(img, (m, Y(zg)), (W - m, Y(zg)), (225, 225, 225) if round(zg * 10) % 10 else (170, 170, 170), 1)
        if round(zg * 10) % 5 == 0:
            cv2.putText(img, f"{zg:.1f}", (4, Y(zg) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1)
    for v in range(0, int(s1) + 1, 5):
        cv2.line(img, (X(v), m), (X(v), H - m), (235, 235, 235), 1)
        cv2.putText(img, f"{v} m", (X(v) - 10, H - m + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1)
    for a, b in zip(s, gc):
        cv2.circle(img, (X(a), Y(b)), 2, (130, 130, 130), -1)
    for a, b in zip(s, gm):
        if np.isfinite(b):
            cv2.circle(img, (X(a), Y(b)), 2, (200, 120, 0), -1)
    bounds = [0] + cps + [len(s) - 1]
    for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:])):
        cv2.line(img, (X(s[a]), Y(lev[k])), (X(s[b]), Y(lev[k])), (0, 160, 0), 2)
        cv2.putText(img, f"{lev[k]:.2f}", (X((s[a] + s[b]) / 2) - 16, Y(lev[k]) - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 120, 0), 1)
    for e in ev:
        x = X(e["s"])
        cv2.line(img, (x, m), (x, H - m), (0, 0, 220), 1)
        cv2.putText(img, f"{e['dz']:+.2f} {e['kind']}", (x + 3, m + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 200), 1)
    cv2.putText(img, f"{clip}: grey = camera z - eye, blue = mesh ground, green = levels, red = events",
                (m, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.imwrite(path, img)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone", nargs=2, action="append", required=True, metavar=("MODEL", "ALIGN"),
                    help="model.json + align.json (model -> world); repeat for every zone")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mesh", help="world-metre mesh (PLY/OBJ, rs_world.py apply) for the ground under the camera")
    ap.add_argument("--clips", help="comma list of clip ids (default: every video clip in the models)")
    ap.add_argument("--video-fps", type=float, default=60.0, help="source frame rate (frame index -> seconds)")
    ap.add_argument("--old-fps", type=float, default=3.0, help="rate of old v00_<id>/NNNN.jpg extractions")
    ap.add_argument("--eye", type=float, default=1.45, help="m, camera above ground when no mesh gives it")
    ap.add_argument("--win", type=float, default=0.8, help="m of walked distance on each side of a change test")
    ap.add_argument("--thr", type=float, default=0.06, help="m, smallest level change reported (< half a riser)")
    ap.add_argument("--min-frames", type=int, default=12)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    samples = {}
    for mp, alp in a.zone:
        _, zs = load_zone(mp, alp, a)
        for key, q in zs.items():
            samples.setdefault(key, []).append(q)
    # registration check: the same frame solved in two zones must land on the same world point
    pair = {}
    for qs in samples.values():
        for i in range(len(qs)):
            for j in range(i + 1, len(qs)):
                k = tuple(sorted((qs[i]["zone"], qs[j]["zone"])))
                pair.setdefault(k, []).append(np.linalg.norm(qs[i]["pos"] - qs[j]["pos"]))
    for (za, zb), dv in sorted(pair.items()):
        dv = np.array(dv)
        print(f"REG {za} vs {zb}: {len(dv)} shared frames, median {np.median(dv):.2f} m, p90 {np.percentile(dv, 90):.2f} m")

    want = set(a.clips.split(",")) if a.clips else None
    clips = {}
    for (clip, k), qs in samples.items():
        if want and clip not in want:
            continue
        q = dict(qs[0])
        q["pos"] = np.mean([x["pos"] for x in qs], 0)
        q["k"] = k
        clips.setdefault(clip, []).append(q)

    route = {"eye_default": a.eye, "clips": {}}
    for clip in sorted(clips):
        S = sorted(clips[clip], key=lambda q: q["k"])
        if len(S) < a.min_frames:
            continue
        S = clean(S)
        if len(S) < a.min_frames:
            print(f"{clip}: too few consistent poses after outlier removal, skipped")
            continue
        P = np.array([q["pos"] for q in S])
        xy = np.stack([rolling_median(P[:, 0], 5), rolling_median(P[:, 1], 5)], 1)
        s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))])
        gm = ground_from_mesh(P, a.mesh, 0.9) if a.mesh else np.full(len(P), np.nan)
        eh = P[:, 2] - gm
        good = np.isfinite(eh) & (eh > 1.0) & (eh < 1.9)
        eye, src = (float(np.median(eh[good])), "mesh") if good.sum() >= 10 else (a.eye, "default")
        gc = P[:, 2] - eye
        lev, cps, _ = levels_and_events(s, gc, a.win, a.thr)
        ev = []
        for k, cp in enumerate(cps):
            i, j, dz, run, grade, kind, n = classify(s, gc, cp, lev[k], lev[k + 1], a.thr / 2)
            ev.append({"s": float(s[cp]), "x": float(xy[cp, 0]), "y": float(xy[cp, 1]), "from": lev[k], "to": lev[k + 1],
                       "dz": dz, "run": run, "grade": grade, "kind": kind, "risers_hint": n if kind != "ramp/slope" else 0,
                       "frames": [S[i]["name"], S[cp]["name"], S[j]["name"]],
                       "t": [round(S[i]["t"], 2), round(S[j]["t"], 2)]})
        with open(os.path.join(a.out, f"{clip}.csv"), "w") as f:
            f.write("frame,t,x,y,z_cam,pitch_deg,s,ground_cam,ground_mesh\n")
            for q, sv, g1, g2 in zip(S, s, gc, gm):
                f.write(f"{q['name']},{q['t']:.2f},{q['pos'][0]:.3f},{q['pos'][1]:.3f},{q['pos'][2]:.3f},"
                        f"{q['pitch']:.1f},{sv:.2f},{g1:.3f},{'' if not np.isfinite(g2) else f'{g2:.3f}'}\n")
        plot(os.path.join(a.out, f"{clip}.png"), s, gc, gm, lev, cps, ev, clip)
        route["clips"][clip] = {"eye": eye, "eye_src": src, "levels": lev, "events": ev,
                                "samples": [[q["name"], float(q["pos"][0]), float(q["pos"][1]), float(q["pos"][2]),
                                             float(g1), None if not np.isfinite(g2) else float(g2)]
                                            for q, g1, g2 in zip(S, gc, gm)]}
        print(f"{clip}: {len(S)} poses, {s[-1]:.0f} m walked, eye {eye:.2f} ({src}), "
              f"levels {' '.join(f'{v:.2f}' for v in lev)}")
        for e in ev:
            hint = f" ~{e['risers_hint']} risers" if e["risers_hint"] else ""
            print(f"  s {e['s']:5.1f} ({e['x']:.1f},{e['y']:.1f}) {e['from']:.2f}->{e['to']:.2f} {e['dz']:+.2f} "
                  f"over {e['run']:.1f} m: {e['kind']}{hint}  t {e['t'][0]}-{e['t'][1]} s  {os.path.basename(e['frames'][1])}")
    json.dump(route, open(os.path.join(a.out, "route.json"), "w"))
    print(f"{a.out}: {len(route['clips'])} clips")


if __name__ == "__main__":
    sys.exit(main())
