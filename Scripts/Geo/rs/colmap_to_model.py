# COLMAP model -> model.json for Scripts/Blender/sfm_overlay.py (R1 photogrammetry): undistorts the chosen images
# with COLMAP's image_undistorter (PINHOLE, JPEG) and writes the cameras in the RealityScan grid frame, so they line up
# with a mesh RealityScan built after -loadColmap (RS 2.2 keeps the COLMAP model as grid = (x, z, -y); verified on a
# 40-frame test: medians and extents match). Use rs_world.py's align.json (grid -> campus world) with it.
# Usage: python colmap_to_model.py --colmap colmap.exe --model sfm/sparse/0 --images sfm/images --out dir
#          [--names name1,name2 | --every 10]   (names as in images.txt, e.g. 20260924_061757320/..._f00123.jpg)
import argparse
import json
import os
import subprocess
import sys

import numpy as np

# colmap_world = M @ grid_world
M = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])


def qvec2rot(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def read_images(path):
    lines = [l for l in open(path) if not l.startswith("#")]
    out = []
    for i in range(0, len(lines) - 1, 2):
        p = lines[i].split()
        if len(p) >= 10:
            out.append({"cam": int(p[8]), "name": p[9], "q": np.array(list(map(float, p[1:5]))),
                        "t": np.array(list(map(float, p[5:8])))})
    return out


def read_cameras(path):
    cams = {}
    for l in open(path):
        if l.startswith("#") or not l.strip():
            continue
        p = l.split()
        cams[int(p[0])] = (p[1], int(p[2]), int(p[3]), list(map(float, p[4:])))
    return cams


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--colmap", required=True)
    ap.add_argument("--model", required=True, help="sparse model folder with cameras/images .txt")
    ap.add_argument("--images", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--names")
    ap.add_argument("--every", type=int, default=0)
    ap.add_argument("--zone", default="campus")
    ap.add_argument("--poses-only", action="store_true", help="write model_poses.json for all cameras, no undistortion")
    a = ap.parse_args()
    ims = read_images(os.path.join(a.model, "images.txt"))
    names = [im["name"] for im in ims]
    if a.names:
        want = set(a.names.split(","))
        names = [n for n in names if n in want or os.path.basename(n) in want]
    elif a.every:
        names = sorted(names)[::a.every]
    os.makedirs(a.out, exist_ok=True)
    if a.poses_only:  # every camera, original images, distortion ignored (for levelling / camera picking only)
        cams = read_cameras(os.path.join(a.model, "cameras.txt"))
        out = {"zone": a.zone, "frame": "RealityScan grid (poses only, not undistorted)", "cameras": [], "points": []}
        for im in ims:
            _, w, h, prm = cams[im["cam"]]
            Rc = qvec2rot(im["q"])
            out["cameras"].append({"name": im["name"], "image": os.path.join(a.images, im["name"]), "w": w, "h": h,
                                   "f": prm[0], "fy": prm[0], "cx": prm[1], "cy": prm[2], "R": (Rc @ M).tolist(),
                                   "t": im["t"].tolist(), "center": (M.T @ (-Rc.T @ im["t"])).tolist()})
        json.dump(out, open(os.path.join(a.out, "model_poses.json"), "w"))
        print(f"{os.path.join(a.out, 'model_poses.json')}: {len(out['cameras'])} cameras")
        return 0
    lst = os.path.join(a.out, "image_list.txt")
    open(lst, "w").write("\n".join(names) + "\n")
    und = os.path.join(a.out, "undist")
    subprocess.run([a.colmap, "image_undistorter", "--image_path", a.images, "--input_path", a.model,
                    "--output_path", und, "--image_list_path", lst, "--jpeg_quality", "95"], check=True,
                   stdout=subprocess.DEVNULL)
    sp = os.path.join(und, "sparse")
    if os.path.exists(os.path.join(sp, "cameras.bin")) and not os.path.exists(os.path.join(sp, "cameras.txt")):
        subprocess.run([a.colmap, "model_converter", "--input_path", sp, "--output_path", sp, "--output_type", "TXT"],
                       check=True, stdout=subprocess.DEVNULL)
    cams = read_cameras(os.path.join(sp, "cameras.txt"))
    out = {"zone": a.zone, "frame": "RealityScan grid (after -loadColmap of this COLMAP model)", "cameras": [], "points": []}
    chosen = set(names)
    for im in read_images(os.path.join(sp, "images.txt")):
        if im["name"] not in chosen:  # the undistorter keeps every pose but writes only the listed images
            continue
        model, w, h, prm = cams[im["cam"]]
        if model == "PINHOLE":
            f, fy, cx, cy = prm
        else:  # SIMPLE_PINHOLE
            f, cx, cy = prm
            fy = f
        Rc = qvec2rot(im["q"])
        R = Rc @ M                       # x_cam = Rc (M X_grid) + t
        c_col = -Rc.T @ im["t"]
        out["cameras"].append({"name": im["name"], "image": os.path.join(und, "images", im["name"]), "w": w, "h": h,
                               "f": f, "fy": fy, "cx": cx, "cy": cy, "R": R.tolist(), "t": im["t"].tolist(),
                               "center": (M.T @ c_col).tolist()})
    json.dump(out, open(os.path.join(a.out, "model.json"), "w"))
    print(f"{os.path.join(a.out, 'model.json')}: {len(out['cameras'])} undistorted cameras")


if __name__ == "__main__":
    sys.exit(main())
