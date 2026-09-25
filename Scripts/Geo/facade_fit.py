# Single-view facade metrology with a known focal (EXIF): jointly solves the camera pose and the unknown facade
# coordinates (window edge u's, row z's, cornice...) from picked corners on facade planes whose plan position is
# known from the footprint. Scale comes from the fixed plan coordinates (e.g. wing corners). R1 photo match.
# Run: uv run --project Scripts --with opencv-python-headless --with scipy python Scripts/Geo/facade_fit.py fit.json
# fit.json: {"image": "/abs/photo.jpg", "f35": 24, "free_focal": false,
#   "planes": {"E": {"p0": [x, y], "dir": [dx, dy]}},     # plane origin/direction in Block C local metres (z rel FFL)
#   "init": {"var": value, ...},                          # initial guesses for every named unknown
#   "points": [["E", "u_var_or_number", "z_var_or_number", px_u, px_v], ...]}
# Prints the solved unknowns, per-point residuals and the camera (world frame); writes <fit>.cam.json (model.json form).
import json
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, __import__("os").path.dirname(__file__))
from photo_pnp import DIAG_35MM, c_to_world  # noqa: E402

from PIL import Image, ImageOps  # noqa: E402


def main():
    cfg = json.load(open(sys.argv[1]))
    im = Image.open(cfg["image"])
    W, H = ImageOps.exif_transpose(im).size
    f35 = cfg.get("f35") or float(im.getexif().get_ifd(0x8769).get(41989) or 24)  # Pixel: 12 = 0.5x ultrawide
    f0 = f35 * np.hypot(W, H) / DIAG_35MM
    names = sorted({v for p in cfg["points"] for v in p[1:3] if isinstance(v, str)})
    x0 = np.array([cfg["init"][n] for n in names], float)
    planes = cfg["planes"]
    obs = np.array([p[3:5] for p in cfg["points"]], float)

    def world(xv):
        val = dict(zip(names, xv))
        out = []
        for pl, u, z, *_ in cfg["points"]:
            P = planes[pl]
            u = val[u] if isinstance(u, str) else u
            z = val[z] if isinstance(z, str) else z
            d = np.array(P["dir"], float) / np.linalg.norm(P["dir"])
            xy = np.array(P["p0"], float) + u * d
            out.append(c_to_world([xy[0], xy[1], z]))
        return np.array(out)

    # initial pose from PnP on the initial guesses
    K = lambda f: np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1.0]])  # noqa: E731
    ok, rv, tv = cv2.solvePnP(world(x0), obs, K(f0), None, flags=cv2.SOLVEPNP_SQPNP)
    free_f = cfg.get("free_focal", False)
    free_k = cfg.get("free_k1", False)  # residual radial term (ultrawide stills keep some after in-camera correction)
    nx = 6 + len(names)

    def resid(p):
        rv_, tv_, xv = p[:3], p[3:6], p[6:nx]
        f = p[nx] if free_f else f0
        dist = np.array([p[-1], 0, 0, 0]) if free_k else None
        proj, _ = cv2.projectPoints(world(xv), rv_, tv_, K(f), dist)
        return (proj.reshape(-1, 2) - obs).ravel()

    p0 = np.concatenate([rv.ravel(), tv.ravel(), x0] + ([[f0]] if free_f else []) + ([[0.0]] if free_k else []))
    sol = least_squares(resid, p0, loss="soft_l1", f_scale=4.0)
    r = sol.fun.reshape(-1, 2)
    e = np.linalg.norm(r, axis=1)
    J = sol.jac
    try:  # 1-sigma from the Gauss-Newton covariance scaled by the residual variance
        cov = np.linalg.inv(J.T @ J) * (np.sum(sol.fun ** 2) / max(1, len(sol.fun) - len(p0)))
        sig = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        sig = np.full(len(p0), np.nan)
    xv = sol.x[6:6 + len(names)]
    for n, v, s in zip(names, xv, sig[6:6 + len(names)]):
        print(f"  {n:>14s} = {v:8.3f}  ± {s:.3f}")
    f = sol.x[nx] if free_f else f0
    if free_k:
        print(f"k1 {sol.x[-1]:.4f}")
    R = cv2.Rodrigues(sol.x[:3])[0]
    t = sol.x[3:6]
    C = -R.T @ t
    print(f"rms {np.sqrt(np.mean(e ** 2)):.1f} px, max {e.max():.1f} px (pt {int(e.argmax())}); f {f:.0f} px "
          f"({f / np.hypot(W, H) * DIAG_35MM:.1f} mm-eq); camera world {C.round(2)}, z rel C FFL {C[2] - 5.53:.2f}")
    for i, (p, ei) in enumerate(zip(cfg["points"], e)):
        if ei > 3 * np.median(e):
            print(f"  outlier? #{i} {p[:3]} {ei:.1f} px")
    cam = {"name": cfg.get("name", "fit"), "image": cfg["image"], "w": W, "h": H, "f": float(f), "fy": float(f),
           "cx": W / 2, "cy": H / 2, "R": R.tolist(), "t": t.tolist(), "center": C.tolist()}
    json.dump({"zone": cam["name"], "cameras": [cam], "points": [], "solved": dict(zip(names, map(float, xv)))},
              open(sys.argv[1].replace(".json", ".cam.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
