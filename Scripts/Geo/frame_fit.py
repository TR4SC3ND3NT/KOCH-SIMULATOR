# Per-frame camera solve for R1 video walk-throughs: picked pixels <-> points given in a building's local frame
# (Specs/BLD_*.json anchor, z relative to that building's FFL) or in world, solved by PnP with a focal search, then
# written as a one-camera model.json for Scripts/Blender/sfm_overlay.py and drawn back on the frame (all picks +
# optional check points) so the solve can be judged before the overlay render.
# Run: uv run --project Scripts --with opencv-python-headless python Scripts/Geo/frame_fit.py picks.json
# picks.json: {"image": "/abs/frame.jpg", "f_px": [lo, hi] | number, "out": "/abs/prefix",
#   "points": [{"n": "AW_post3_top", "px": [u, v], "b": "BLD_A_W", "l": [x, y, z]} | {"n":..., "px":..., "w": [x,y,z]}],
#   "check": [ same form without px ]}
import json
import math
import os
import sys

import cv2
import numpy as np

SPECS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Art", "Blender", "Specs")
FFL = {}


def ffl_of(bid, s):
    if "ffl_z" in s:
        return float(s["ffl_z"])
    if bid not in FFL:
        raise SystemExit(f"{bid}: no ffl_z in spec; pass world points instead")
    return FFL[bid]


FFL.update({"BLD_B": 6.92, "BLD_C": 6.40, "BLD_GateBooth": 7.34, "BLD_Hall": 5.25, "BLD_Canteen": 3.92})
_cache = {}


def to_world(p):
    if "w" in p:
        return np.array(p["w"], float)
    bid = p["b"]
    if bid not in _cache:
        s = json.load(open(os.path.join(SPECS, bid + ".json")))
        (ox, oy), (dx, dy) = s["anchor"]["world_xy"], s["anchor"]["x_dir"]
        n = math.hypot(dx, dy)
        _cache[bid] = (ox, oy, dx / n, dy / n, ffl_of(bid, s))
    ox, oy, dx, dy, f = _cache[bid]
    x, y, z = p["l"]
    return np.array([ox + dx * x - dy * y, oy + dy * x + dx * y, f + z])


def main():
    cfg = json.load(open(sys.argv[1]))
    img = cv2.imread(cfg["image"])
    H, W = img.shape[:2]
    obj = np.array([to_world(p) for p in cfg["points"]])
    px = np.array([p["px"] for p in cfg["points"]], float)
    fr = cfg.get("f_px", [0.6 * W, 1.6 * W])
    fs = [fr] if not isinstance(fr, list) else np.linspace(fr[0], fr[1], 121)
    best = None
    for f in fs:
        K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1.0]])
        ok, rv, tv = cv2.solvePnP(obj, px, K, None, flags=cv2.SOLVEPNP_SQPNP)
        if not ok:
            continue
        rv, tv = cv2.solvePnPRefineLM(obj, px, K, None, rv, tv)
        pr, _ = cv2.projectPoints(obj, rv, tv, K, None)
        e = np.linalg.norm(pr.reshape(-1, 2) - px, axis=1)
        rms = float(np.sqrt((e ** 2).mean()))
        if best is None or rms < best[0]:
            best = (rms, f, rv, tv, e, K)
    rms, f, rv, tv, e, K = best
    R = cv2.Rodrigues(rv)[0]
    t = tv.ravel()
    C = -R.T @ t
    fwd = R.T @ np.array([0, 0, 1.0])
    print(f"rms {rms:.1f} px, f {f:.0f} px ({f / math.hypot(W, H) * 43.27:.1f} mm-eq); camera {C.round(2)} "
          f"heading {math.degrees(math.atan2(fwd[1], fwd[0])):.0f} deg, pitch {math.degrees(math.asin(fwd[2])):.0f} deg")
    for p, ei in zip(cfg["points"], e):
        print(f"  {p['n']:>16s} {ei:6.1f}")
    vis = img.copy()
    for p, (u, v), q in zip(cfg["points"], px, cv2.projectPoints(obj, rv, tv, K, None)[0].reshape(-1, 2)):
        cv2.circle(vis, (int(u), int(v)), 7, (0, 255, 255), 2)
        cv2.line(vis, (int(u), int(v)), (int(q[0]), int(q[1])), (0, 0, 255), 2)
        cv2.putText(vis, p["n"], (int(u) + 8, int(v) - 6), 0, 0.6, (0, 255, 255), 2)
    chk = cfg.get("check", [])
    if chk:
        cw = np.array([to_world(p) for p in chk])
        for p, q, X in zip(chk, cv2.projectPoints(cw, rv, tv, K, None)[0].reshape(-1, 2), cw):
            if (R @ X + t)[2] > 0:
                cv2.drawMarker(vis, (int(q[0]), int(q[1])), (255, 0, 255), cv2.MARKER_CROSS, 18, 2)
                cv2.putText(vis, p["n"], (int(q[0]) + 8, int(q[1]) + 14), 0, 0.55, (255, 0, 255), 2)
    out = cfg["out"]
    cv2.imwrite(out + "_pnp.jpg", vis)
    name = os.path.basename(out)
    cam = {"name": name, "image": cfg["image"], "w": W, "h": H, "f": f, "fy": f, "cx": W / 2, "cy": H / 2,
           "R": R.tolist(), "t": t.tolist(), "center": C.tolist(), "rms_px": rms}
    json.dump({"zone": name, "cameras": [cam], "points": []}, open(out + "_cam.json", "w"), indent=1)


if __name__ == "__main__":
    main()
