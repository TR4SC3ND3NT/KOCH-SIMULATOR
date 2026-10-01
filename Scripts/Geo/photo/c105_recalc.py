# C105 recalculation with the lens focal calibrated on the door (owner 2026-10-01: a 187 cm person in the C204 door
# gives the outer door frame 2.12 m, clear opening 2.01 m). For each focal f: photo 151 -> ceiling distance from the
# 0.60 grid at the door-wall bulkhead, bulkhead depth, door-wall plane, door foot on the floor -> door height. The f
# that gives 2.12 is then used for photos 152/153 (same phone, same lens). R1 metrology, run with venv_sfm python.
import glob
import sys

import cv2
import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from room_svm import Room   # noqa: E402

D = "/home/faust/Desktop/Фото_2026-09-30"


def load(n):
    return cv2.imread(glob.glob(f"{D}/{n}_*.jpg")[0])


def axes(img, f, vps=None):
    R0 = Room(img, f, vps=vps, verbose=False)
    up = int(np.argmax([abs(d[1]) for d in R0.dirs])); hz = [k for k in range(3) if k != up]
    return R0.set_axes(up=up, x=max(hz, key=lambda k: abs(R0.dirs[k][0]))), R0.vps


def grid_scale(R, pts):
    P1 = [R.on_plane_y(p, 1.0) for p in pts]
    hc = 0.6 / np.median([np.linalg.norm(P1[i + 1] - P1[i]) for i in range(len(P1) - 1)])
    zj = float(np.median([R.on_plane_y(p, hc)[2] for p in pts]))
    return hc, zj


def m151(f, vps):
    R, _ = axes(load("151"), f, vps)
    hc, zj = grid_scale(R, [(1293, 254), (1642, 255), (1986, 256), (2329, 256), (2671, 254)])
    deps, drops = [], []
    for x, yb, yw in ((1500, 388, 421), (2000, 386, 418), (2500, 386, 418)):
        pf = R.on_plane((x, yb), 2, zj); pw = R.on_plane_y((x, yw), pf[1])
        deps.append(abs(pw[2]) - abs(zj)); drops.append(hc - pf[1])
    zw = zj + np.sign(zj) * np.mean(deps)
    foot, top = R.on_plane((760, 1795), 2, zw), R.on_plane((760, 808), 2, zw)
    L, Rr = R.on_plane((696, 1300), 2, zw), R.on_plane((1196, 1300), 2, zw)
    H = hc - foot[1]
    return dict(door_h=top[1] - foot[1], door_w=abs(Rr[0] - L[0]), ceiling=H, drop=np.mean(drops), depth=np.mean(deps),
                under=H - np.mean(drops))


def main():
    _, vps151 = axes(load("151"), 2875)
    rows = []
    for f in range(2000, 3401, 50):
        r = m151(f, vps151); rows.append((f, r))
    fs = np.array([f for f, _ in rows]); dh = np.array([r["door_h"] for _, r in rows])
    f_door = float(np.interp(2.12, dh, fs)) if dh[0] < dh[-1] else float(np.interp(2.12, dh[::-1], fs[::-1]))
    print("door outer height vs f:", [(f, round(r["door_h"], 3)) for f, r in rows[::4]])
    r = m151(f_door, vps151)
    print(f"\nf from the door = {f_door:.0f} px (EXIF 2833)")
    print({k: round(float(v), 3) for k, v in r.items()})
    return f_door


if __name__ == "__main__":
    main()
