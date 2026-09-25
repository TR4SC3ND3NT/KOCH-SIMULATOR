# Diagnostic views of a zone SfM model in its gravity frame (R1): top-down plan (colour = height) and side sections,
# with the camera path, so rooms/corridors/stairs can be read and measured before modelling.
# Run: uv run --python 3.12 --with numpy --with pillow python Scripts/Geo/sfm_views.py model.json out_prefix
#      [--scale M_PER_UNIT] [--res 0.02] [--hmin -3 --hmax 3]
import argparse
import json

import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def refine_up(m, up0):
    """Hand-held frames pitch a lot (stairs), so the mean camera 'up' is biased. Refine it as the direction most
    orthogonal to the normals of the dominant near-vertical planes (walls), weighted by inlier count."""
    from sfm_planes import find_planes
    P = np.array([p[:3] for p in m["points"]])
    planes, _ = find_planes(P, up0, 10, iters=1500)
    N = np.array([np.array(p["n"]) * np.sqrt(p["count"]) for p in planes if p["angle_to_up"] > 60])
    if len(N) < 2:
        return up0
    up = np.linalg.svd(N)[2][-1]
    return up if up @ up0 > 0 else -up


def frame(m):
    """Gravity-aligned basis: z = up (refined from walls), x = principal horizontal direction of the camera path."""
    up = np.array([-np.array(c["R"])[1] for c in m["cameras"]]).mean(0)
    up /= np.linalg.norm(up)
    up = refine_up(m, up)
    up /= np.linalg.norm(up)
    C = np.array([c["center"] for c in m["cameras"]])
    H = C - C.mean(0)
    H -= np.outer(H @ up, up)
    ex = np.linalg.svd(H)[2][0]
    ex -= up * (ex @ up)
    ex /= np.linalg.norm(ex)
    ey = np.cross(up, ex)
    return np.stack([ex, ey, up]), C.mean(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("out")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--res", type=float, default=0.02)
    ap.add_argument("--hmin", type=float)
    ap.add_argument("--hmax", type=float)
    a = ap.parse_args()
    m = json.load(open(a.model))
    B, o = frame(m)
    P = (np.array([p[:3] for p in m["points"]]) - o) @ B.T * a.scale
    RGB = np.array([p[3:6] for p in m["points"]])
    cams = sorted(m["cameras"], key=lambda c: c["name"])
    C = (np.array([c["center"] for c in cams]) - o) @ B.T * a.scale
    lo, hi = np.percentile(P, 1, 0), np.percentile(P, 99, 0)
    keep = np.all((P >= lo - 0.5) & (P <= hi + 0.5), 1)
    P, RGB = P[keep], RGB[keep]
    hmin = a.hmin if a.hmin is not None else lo[2]
    hmax = a.hmax if a.hmax is not None else hi[2]
    for view, (i, j) in (("plan", (0, 1)), ("side", (0, 2)), ("front", (1, 2))):
        x0, x1 = min(P[:, i].min(), C[:, i].min()) - 0.5, max(P[:, i].max(), C[:, i].max()) + 0.5
        y0, y1 = min(P[:, j].min(), C[:, j].min()) - 0.5, max(P[:, j].max(), C[:, j].max()) + 0.5
        W, Hh = int((x1 - x0) / a.res) + 1, int((y1 - y0) / a.res) + 1
        img = Image.new("RGB", (W, Hh), (15, 15, 15))
        px = img.load()
        sel = (P[:, 2] >= hmin) & (P[:, 2] <= hmax) if view == "plan" else np.ones(len(P), bool)
        order = np.argsort(P[:, 2]) if view == "plan" else np.arange(len(P))
        for k in order:
            if not sel[k]:
                continue
            u, v = int((P[k, i] - x0) / a.res), int((y1 - P[k, j]) / a.res)
            if 0 <= u < W and 0 <= v < Hh:
                if view == "plan":
                    t = np.clip((P[k, 2] - hmin) / max(hmax - hmin, 1e-6), 0, 1)
                    px[u, v] = (int(255 * t), int(255 * (1 - abs(2 * t - 1))), int(255 * (1 - t)))
                else:
                    px[u, v] = tuple(int(c) for c in RGB[k])
        d = ImageDraw.Draw(img)
        step = 1.0 if a.scale != 1.0 else 1.0
        for g in np.arange(np.floor(x0), x1, step):
            d.line([((g - x0) / a.res, 0), ((g - x0) / a.res, Hh)], fill=(60, 60, 60))
        for g in np.arange(np.floor(y0), y1, step):
            d.line([(0, (y1 - g) / a.res), (W, (y1 - g) / a.res)], fill=(60, 60, 60))
        for k, c in enumerate(C):
            u, v = (c[i] - x0) / a.res, (y1 - c[j]) / a.res
            d.ellipse([u - 3, v - 3, u + 3, v + 3], outline=(255, 255, 255))
            if k % 10 == 0:
                d.text((u + 4, v), cams[k]["name"].split("/")[-1][:4], fill=(255, 255, 0))
        img.save(f"{a.out}_{view}.png")
        print(view, W, Hh, "x", round(x0, 2), round(x1, 2), "y", round(y0, 2), round(y1, 2))
    json.dump({"B": B.tolist(), "o": o.tolist(), "scale": a.scale}, open(a.out + "_frame.json", "w"))


if __name__ == "__main__":
    main()
