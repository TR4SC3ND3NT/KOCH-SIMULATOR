# Photo-vs-model check for R1 (handoff 4a, per-element loop step 4): reads <dir>/manifest.json from
# Scripts/Blender/sfm_overlay.py (undistorted frame + transparent Workbench render per camera) and writes
#   ovl_<name>.jpg: frame | 55 % blend | render, plus an edge view (photo edges grey, model edges green where they
#   sit on a photo edge, red where they miss by more than --tol px),
#   metrics.json: per camera the model-edge -> photo-edge distance (median / p90 px) and the share within --tol.
# The distance only scores model edges (Canny on the render inside its alpha); photo clutter can make it optimistic,
# so the images are still reviewed by eye. Usage: python overlay_compose.py <dir> [--tol 3] [--height 1200]
import argparse
import json
import os
import sys

import cv2
import numpy as np


def edges(gray, lo, hi):
    return cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), lo, hi) > 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--tol", type=float, default=3.0)
    ap.add_argument("--height", type=int, default=1200)
    a = ap.parse_args()
    man = json.load(open(os.path.join(a.dir, "manifest.json")))
    out = []
    for m in man:
        photo = cv2.imread(m["image"])
        rgba = cv2.imread(m["render"], cv2.IMREAD_UNCHANGED)
        if photo is None or rgba is None:
            continue
        if rgba.shape[:2] != photo.shape[:2]:
            rgba = cv2.resize(rgba, (photo.shape[1], photo.shape[0]), interpolation=cv2.INTER_NEAREST)
        alpha = rgba[:, :, 3:4].astype(np.float32) / 255.0
        blend = (photo * (1 - 0.55 * alpha) + rgba[:, :, :3] * 0.55 * alpha).astype(np.uint8)
        flat = (rgba[:, :, :3] * alpha + 48 * (1 - alpha)).astype(np.uint8)
        pe = edges(cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY), 40, 120)
        re = edges(cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_BGR2GRAY), 20, 60) | edges((alpha[:, :, 0] * 255).astype(np.uint8), 50, 150)
        dt = cv2.distanceTransform((~pe).astype(np.uint8), cv2.DIST_L2, 5)
        d = dt[re]
        ev = (photo * 0.35).astype(np.uint8)
        ev[pe] = (150, 150, 150)
        hit = re & (dt <= a.tol)
        ev[hit] = (0, 230, 0)
        ev[re & ~hit] = (0, 0, 255)
        rec = {"name": m["name"], "model_edge_px": int(re.sum())}
        if len(d):
            rec.update(median_px=round(float(np.median(d)), 2), p90_px=round(float(np.percentile(d, 90)), 2),
                       within_tol=round(float((d <= a.tol).mean()), 3))
        out.append(rec)
        s = a.height / photo.shape[0]
        row = np.hstack([cv2.resize(x, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) for x in (photo, blend, flat, ev)])
        tag = os.path.splitext(os.path.basename(m["render"]))[0][2:]
        cv2.imwrite(os.path.join(a.dir, f"ovl_{tag}.jpg"), row, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(json.dumps(rec))
    json.dump(out, open(os.path.join(a.dir, "metrics.json"), "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
