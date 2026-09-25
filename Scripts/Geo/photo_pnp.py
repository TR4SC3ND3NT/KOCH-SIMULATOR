# Solves one photo's camera in the campus world frame from picked pixel <-> known 3D points (PnP, optional focal fit)
# and writes a one-camera model.json for Scripts/Blender/sfm_overlay.py (use with an identity align JSON). R1 photo match.
# Run: uv run --project Scripts --with opencv-python-headless python Scripts/Geo/photo_pnp.py picks.json out_cam.json
# picks.json: {"image": "/abs/photo.jpg", "f35": 24 (diag 35 mm-eq; omit to read EXIF), "fit_focal": true,
#   "frame": "C" (points in Block C local: x along the south facade, y north, z rel FFL) | "world",
#   "points": [{"name": "E1F4", "px": [u, v], "xyz": [x, y, z]}, ...]}   pixels in the EXIF-rotated full-res image
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

C_ORIGIN = np.array([173.264, -3.640])   # Block C SW corner (Specs/BLD_C.json anchor)
C_X = np.array([0.99920, -0.03985])
C_FFL = 5.53                             # C ground-floor finished level, world z
DIAG_35MM = 43.27


def c_to_world(p):
    x, y, z = p
    xy = C_ORIGIN + x * C_X + y * np.array([-C_X[1], C_X[0]])
    return np.array([xy[0], xy[1], C_FFL + z])


def solve(obj, img, f):
    h, w = img
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1.0]])
    ok, rv, tv = cv2.solvePnP(obj, img_pts, K, None, flags=cv2.SOLVEPNP_SQPNP)
    rv, tv = cv2.solvePnPRefineLM(obj, img_pts, K, None, rv, tv)
    proj, _ = cv2.projectPoints(obj, rv, tv, K, None)
    err = np.linalg.norm(proj.reshape(-1, 2) - img_pts, axis=1)
    return err, rv, tv


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    im = Image.open(cfg["image"])
    f35 = cfg.get("f35") or float(im.getexif().get_ifd(0x8769).get(41989) or 24)
    W, H = ImageOps.exif_transpose(im).size
    conv = c_to_world if cfg.get("frame", "C") == "C" else np.asarray
    obj = np.array([conv(p["xyz"]) for p in cfg["points"]], float)
    img_pts = np.array([p["px"] for p in cfg["points"]], float)
    f0 = f35 * np.hypot(W, H) / DIAG_35MM
    fs = np.linspace(0.8 * f0, 1.25 * f0, 91) if cfg.get("fit_focal") else [f0]
    best = min((solve(obj, (H, W), f) + (f,) for f in fs), key=lambda r: np.sqrt(np.mean(r[0] ** 2)))
    err, rv, tv, f = best
    R = cv2.Rodrigues(rv)[0]
    t = tv.ravel()
    C = -R.T @ t
    for p, e in zip(cfg["points"], err):
        print(f"  {p['name']:>10s} {e:6.1f} px")
    print(f"f {f:.0f} px ({f / np.hypot(W, H) * DIAG_35MM:.1f} mm-eq, EXIF {f35}); rms {np.sqrt(np.mean(err ** 2)):.1f} px; "
          f"camera world {C.round(2)}, height above C FFL {C[2] - C_FFL:.2f} m")
    name = cfg.get("name") or cfg["image"].rsplit("/", 1)[-1].split(".")[0]
    cam = {"name": name, "image": cfg["image"], "w": W, "h": H, "f": f, "fy": f, "cx": W / 2, "cy": H / 2,
           "R": R.tolist(), "t": t.tolist(), "center": C.tolist(), "rms_px": float(np.sqrt(np.mean(err ** 2)))}
    json.dump({"zone": name, "cameras": [cam], "points": []}, open(sys.argv[2], "w"), indent=1)
