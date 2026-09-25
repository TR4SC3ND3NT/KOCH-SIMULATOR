# Aligns a zone SfM model to the campus world frame from ONE photo whose world camera is known (PnP on facade
# points, sfm_overlay-style camera JSON) plus one world plane for scale (e.g. Block C's west facade x = 0 in C local).
# Rotation = R_world^T R_sfm of that photo; scale = world distance camera->plane / model distance camera->plane
# (plane found in the model as the vertical plane whose normal best matches the world plane normal).
# Run: uv run --python 3.12 --with numpy python Scripts/Geo/sfm_world_align.py model.json photo_cam.json NAME_SUBSTR \
#        PLANE_NX PLANE_NY PLANE_NZ PLANE_D out_align.json      (world plane n.x = d, n unit)
import json
import sys

import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__file__))
from sfm_planes import find_planes  # noqa: E402


def main():
    model = json.load(open(sys.argv[1]))
    wcam = json.load(open(sys.argv[2]))["cameras"][0]
    sub = sys.argv[3]
    n_w = np.array(list(map(float, sys.argv[4:7])))
    d_w = float(sys.argv[7])
    out = sys.argv[8]
    cam = next(c for c in model["cameras"] if sub in c["name"])
    Rs, Cs = np.array(cam["R"]), np.array(cam["center"])
    Rw, Cw = np.array(wcam["R"]), np.array(wcam["center"])
    R = Rw.T @ Rs                       # model axes -> world axes
    up_model = R.T @ np.array([0, 0, 1.0])
    P = np.array([p[:3] for p in model["points"]])
    planes, _ = find_planes(P, up_model, 16, iters=2500)
    best = max(planes, key=lambda p: abs((R @ np.array(p["n"])) @ n_w) * np.sqrt(p["count"]) * (p["extent"][0] > 5))
    n_m, c_m = np.array(best["n"]), np.array(best["c"])
    dist_m = abs((Cs - c_m) @ n_m)
    dist_w = abs(Cw @ n_w - d_w)
    s = dist_w / dist_m
    t = Cw - s * R @ Cs
    ang = np.degrees(np.arccos(min(1.0, abs((R @ n_m) @ n_w))))
    json.dump({"scale": s, "R": R.tolist(), "t": t.tolist(), "rms_m": -1,
               "note": f"from photo '{sub}' + plane (normal error {ang:.2f} deg, {best['count']} pts)"}, open(out, "w"), indent=1)
    print(f"scale {s:.4f} m/unit; model plane {best['count']} pts, normal error {ang:.2f} deg; cam->plane {dist_w:.2f} m")


if __name__ == "__main__":
    main()
