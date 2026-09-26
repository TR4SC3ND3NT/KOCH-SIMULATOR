# RealityScan registration export -> model.json for Scripts/Blender/sfm_overlay.py (R1 photogrammetry).
# Inputs from one RealityScan session on the selected component (see rs_export.py):
#   <exp>/colmap/sparse/0/{cameras,images,points3D}.txt  COLMAP text, PINHOLE on undistorted <exp>/colmap/images/NNNNN.png
#   <exp>/cams.csv   "Internal/External camera parameters" (original names + centres, same frame as the COLMAP export)
# The COLMAP export names images by index and uses a Y-down world ((x, -z, y) of the CSV's Z-up frame in RS 2.2):
# the signed axis permutation is found automatically, poses are brought into the CSV (RealityScan grid, Z-up) frame,
# and each image is matched to its original name by camera centre (unique and tight match checked).
# Output model.json: {zone, cameras: [{name, image, w, h, f, fy, cx, cy, R (world->cam), t, center}], points: [...]}
# Usage: python rs_to_model.py <exp> <out/model.json> [--zone campus] [--max-points 300000]
import argparse
import itertools
import json
import os
import sys

import numpy as np


def qvec2rot(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def read_cameras(path):
    cams = {}
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        cid, model, w, h = int(p[0]), p[1], int(p[2]), int(p[3])
        prm = list(map(float, p[4:]))
        if model != "PINHOLE":
            raise SystemExit(f"camera {cid}: {model}, expected PINHOLE (export with undistorted images)")
        cams[cid] = {"w": w, "h": h, "f": prm[0], "fy": prm[1], "cx": prm[2], "cy": prm[3]}
    return cams


def read_images(path):
    out, lines = [], [l for l in open(path) if not l.startswith("#")]
    for i in range(0, len(lines) - 1, 2):
        p = lines[i].split()
        if len(p) < 10:
            continue
        q, t = np.array(list(map(float, p[1:5]))), np.array(list(map(float, p[5:8])))
        R = qvec2rot(q / np.linalg.norm(q))
        out.append({"id": int(p[0]), "cam": int(p[8]), "file": p[9], "R": R, "t": t, "center": -R.T @ t})
    return out


def read_points(path, max_points):
    pts = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        err, track = float(p[7]), (len(p) - 8) // 2
        if err < 2.0 and track >= 3:
            pts.append([float(p[1]), float(p[2]), float(p[3]), int(p[4]), int(p[5]), int(p[6]), round(err, 3), track])
    if len(pts) > max_points:
        idx = np.random.default_rng(0).choice(len(pts), max_points, replace=False)
        pts = [pts[i] for i in sorted(idx)]
    return pts


def read_csv(path):
    rows = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        p = line.strip().split(",")
        rows.append((p[0], np.array(list(map(float, p[1:4])))))
    return rows


def axis_map(ims, C, tol):
    """Signed permutation M with colmap_world = M @ csv_world that makes every COLMAP centre hit a CSV centre."""
    best = None
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            M = np.zeros((3, 3))
            for r, (c, s) in enumerate(zip(perm, signs)):
                M[r, c] = s
            if np.linalg.det(M) < 0:
                continue
            d = np.array([np.min(np.linalg.norm(C - M.T @ im["center"], axis=1)) for im in ims[:50]])
            if best is None or d.max() < best[0]:
                best = (d.max(), M)
    if best[0] > tol:
        raise SystemExit(f"no axis permutation maps COLMAP centres onto the CSV ones (best max residual {best[0]:.3g})")
    return best[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp")
    ap.add_argument("out")
    ap.add_argument("--zone", default="campus")
    ap.add_argument("--max-points", type=int, default=300000)
    a = ap.parse_args()
    sp = os.path.join(a.exp, "colmap", "sparse", "0")
    cams = read_cameras(os.path.join(sp, "cameras.txt"))
    ims = read_images(os.path.join(sp, "images.txt"))
    csv = read_csv(os.path.join(a.exp, "cams.csv"))
    C = np.array([c for _, c in csv])
    scale = np.median(np.linalg.norm(C - np.median(C, 0), axis=1)) + 1e-9
    tol = 1e-4 * scale
    M = axis_map(ims, C, tol)
    used, out = {}, {"zone": a.zone, "frame": "RealityScan grid (Z up), same as cams.csv", "cameras": [], "points": []}
    for im in ims:
        R, cen = im["R"] @ M, M.T @ im["center"]   # x_cam = R_col (M X) + t
        d = np.linalg.norm(C - cen, axis=1)
        k = int(np.argmin(d))
        if d[k] > tol:
            raise SystemExit(f"{im['file']}: no CSV camera at its centre (nearest {d[k]:.3g})")
        name = csv[k][0]
        if name in used:
            raise SystemExit(f"{im['file']} and {used[name]} both match {name}")
        used[name] = im["file"]
        c = cams[im["cam"]]
        out["cameras"].append({"name": name, "image": os.path.join(a.exp, "colmap", "images", im["file"]), **c,
                               "R": R.tolist(), "t": im["t"].tolist(), "center": cen.tolist()})
    pts = read_points(os.path.join(sp, "points3D.txt"), a.max_points)
    for p in pts:
        p[:3] = (M.T @ np.array(p[:3])).tolist()
    out["points"] = pts
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"))
    print(f"{a.out}: {len(out['cameras'])} cameras (of {len(csv)} in the CSV), {len(out['points'])} points")


if __name__ == "__main__":
    sys.exit(main())
