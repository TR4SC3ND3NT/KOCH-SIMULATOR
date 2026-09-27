# Picks the solved cameras that see an element best, for the per-element photo check (R1, handoff 4a step 4):
# projects the element's world box (8 corners) through every camera of model.json (+ align.json model -> world) and
# ranks by visible projected area, penalising boxes cut by the frame edge or seen at grazing angles.
# Prints the top N as a comma list for KOCH_SFM_CAMS (Scripts/Blender/sfm_overlay.py).
# Usage: python pick_cams.py model.json align.json --box x0,y0,z0,x1,y1,z1 [--n 4] [--min-sep 2.0] [--dist 2,15]
import argparse
import json
import sys

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("align")
    ap.add_argument("--box", required=True)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--min-sep", type=float, default=2.0, help="m between picked camera centres (diverse views)")
    ap.add_argument("--dist", help="min,max m from the box centre (pass bands: P1 wide 8,80; P2 2,15; P3 0,5)")
    a = ap.parse_args()
    model, al = json.load(open(a.model)), json.load(open(a.align))
    s, Rw, tw = al["scale"], np.array(al["R"]), np.array(al["t"])
    x0, y0, z0, x1, y1, z1 = map(float, a.box.split(","))
    corners = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    centre = corners.mean(0)
    # world -> model: X_m = Rw^T (X_w - t) / s
    Cm = ((corners - tw) @ Rw) / s
    rows = []
    for c in model["cameras"]:
        R, t = np.array(c["R"]), np.array(c["t"])
        X = Cm @ R.T + t
        if (X[:, 2] <= 0.05 / s).any():
            continue
        u = c["f"] * X[:, 0] / X[:, 2] + c["cx"]
        v = c["fy"] * X[:, 1] / X[:, 2] + c["cy"]
        W, H = c["w"], c["h"]
        uc, vc = np.clip(u, 0, W), np.clip(v, 0, H)
        full = (u.max() - u.min()) * (v.max() - v.min())
        vis = (uc.max() - uc.min()) * (vc.max() - vc.min())
        if vis <= 0 or full <= 0:
            continue
        inside = vis / full
        cw = s * Rw @ np.array(c["center"]) + tw
        view = (centre - cw) / np.linalg.norm(centre - cw)
        axis = Rw @ (R.T @ np.array([0, 0, 1.0]))
        cos = float(view @ axis)
        score = vis / (W * H) * inside ** 2 * max(cos, 0) ** 2
        d = float(np.linalg.norm(centre - cw))
        if a.dist and not (float(a.dist.split(",")[0]) <= d <= float(a.dist.split(",")[1])):
            continue
        rows.append((score, c["name"], cw, inside, vis / (W * H), float(np.linalg.norm(centre - cw))))
    rows.sort(key=lambda r: -r[0])
    picked = []
    for r in rows:
        if all(np.linalg.norm(r[2] - p[2]) >= a.min_sep for p in picked):
            picked.append(r)
        if len(picked) >= a.n:
            break
    for sc, name, cw, ins, cov, dist in picked:
        print(f"{name}  score {sc:.3f}  coverage {cov:.2f}  inside {ins:.2f}  dist {dist:.1f} m")
    print(",".join(p[1] for p in picked))


if __name__ == "__main__":
    sys.exit(main())
