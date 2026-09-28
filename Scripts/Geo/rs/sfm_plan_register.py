# Registers a small SfM model (pycolmap sparse folder) to the campus world by its plan (R1 stream B, handoff 0b):
#   1. level: RANSAC ground plane that the cameras stay at a near-constant height over; scale from the eye height;
#   2. plan: sparse points 0.6-2.8 m above the ground (posts, hedges, walls, parapets) are matched to a horizontal
#      slab section of the greybox (Scripts/Blender/plan_overlay.py --zband -> <out>.mask.png/.json) by brute force
#      over yaw (1 deg) and a scale factor, with the best shift per pose from an FFT cross-correlation; cameras that
#      land on solid geometry are penalised (the owner walked on open ground);
#   3. writes align.json (world = scale * R @ x + t, the format sfm_overlay.py / pick_cams.py read) and a check image
#      (section in grey, registered points in red, camera path in blue).
# Good enough for P0/P1 placement (~0.1-0.3 m) where the section has distinctive shapes; always check the overlay.
# Usage: python sfm_plan_register.py --sparse gd_sfm/sparse/9 --mask sec.png.mask.png --ground-z 5.38 --out dir
#          [--eye 1.50] [--scales 0.9,1.1,0.025] [--prior x,y,r] (search only shifts within r m of x,y)
import argparse
import json
import math
import os
import sys

import cv2
import numpy as np
import pycolmap


def cam_centres(rec):
    C = []
    for im in rec.images.values():
        T = im.cam_from_world() if callable(im.cam_from_world) else im.cam_from_world
        R = T.rotation.matrix()
        C.append(-R.T @ T.translation)
    return np.array(C)


def level(P, C, eye, seed=0):
    """Rotation + scale + offset that put the ground plane at z = 0 and the cameras at +eye."""
    rng = np.random.default_rng(seed)
    spread = np.linalg.norm(C - C.mean(0), axis=1).mean() + 1e-9
    best = None
    for _ in range(4000):
        s = P[rng.choice(len(P), 3, replace=False)]
        n = np.cross(s[1] - s[0], s[2] - s[0])
        nn = np.linalg.norm(n)
        if nn < 1e-12:
            continue
        n /= nn
        d = -n @ s[0]
        dc = C @ n + d
        if abs(np.mean(dc)) < 1e-9 or np.std(dc) > 0.15 * abs(np.mean(dc)):
            continue
        inl = np.abs(P @ n + d) < 0.01 * spread
        if best is None or inl.sum() > best[0]:
            best = (int(inl.sum()), n, d)
    if best is None:
        raise SystemExit("no ground plane with the cameras at a constant height over it")
    _, n, d = best
    inl = np.abs(P @ n + d) < 0.01 * spread                    # refit on the inliers (least squares)
    Q = P[inl]
    c = Q.mean(0)
    n = np.linalg.svd(Q - c)[2][2]
    d = -n @ c
    if np.mean(C @ n + d) < 0:
        n, d = -n, -d
    h = float(np.median(C @ n + d))
    s = eye / h
    z = np.array([0.0, 0.0, 1.0])
    ax = np.cross(n, z)
    sa, ca = np.linalg.norm(ax), float(n @ z)
    if sa < 1e-12:
        Rl = np.eye(3)
    else:
        k = ax / sa
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        Rl = np.eye(3) + sa * K + (1 - ca) * K @ K
    return s, Rl, np.array([0.0, 0.0, s * d]), best[0], float(np.std((C @ n + d) * s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sparse", required=True)
    ap.add_argument("--mask", required=True, help="<out>.mask.png from plan_overlay.py --zband (json next to it)")
    ap.add_argument("--ground-z", type=float, required=True, help="world z of the ground the owner walked on")
    ap.add_argument("--out", required=True)
    ap.add_argument("--eye", type=float, default=1.50)
    ap.add_argument("--scales", default="0.9,1.1,0.025", help="scale factor search on top of the eye-height scale")
    ap.add_argument("--band", default="0.6,2.8", help="m above the ground: points used for the plan match")
    ap.add_argument("--prior", help="x,y,r: only accept camera-path centres within r m of x,y")
    ap.add_argument("--cam-weight", type=float, default=3.0)
    ap.add_argument("--walk", help="mask of the walkable surfaces (same box/px as --mask): cameras on it are rewarded")
    ap.add_argument("--walk-weight", type=float, default=1.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rec = pycolmap.Reconstruction(a.sparse)
    P = np.array([p.xyz for p in rec.points3D.values()])
    C = cam_centres(rec)
    s0, Rl, tl, ninl, csd = level(P, C, a.eye)
    Pl, Cl = s0 * P @ Rl.T + tl, s0 * C @ Rl.T + tl
    b0, b1 = map(float, a.band.split(","))
    V = Pl[(Pl[:, 2] > b0) & (Pl[:, 2] < b1)][:, :2]
    print(f"level: {ninl} ground inliers, camera height sd {csd:.3f} m, {len(V)} points in the {a.band} m band")

    meta = json.load(open(os.path.splitext(a.mask)[0] + ".json"))
    x0, y0, x1, y1 = meta["box"]
    px = meta["px"]
    M = (cv2.imread(a.mask, cv2.IMREAD_GRAYSCALE) > 127).astype(np.float32)
    H, W = M.shape
    Mb = cv2.GaussianBlur(M, (0, 0), 0.12 / px)                 # ~0.12 m tolerance for points on the surfaces
    Mb /= Mb.max() + 1e-9
    FM, FC = np.fft.rfft2(Mb), np.fft.rfft2(M)
    FW = None
    if a.walk:
        Wm = (cv2.imread(a.walk, cv2.IMREAD_GRAYSCALE) > 127).astype(np.float32)
        if Wm.shape != M.shape:
            raise SystemExit("--walk mask must have the same size as --mask (same --box and --px)")
        FW = np.fft.rfft2(cv2.GaussianBlur(Wm, (0, 0), 0.15 / px))
    cm = Cl[:, :2].mean(0)
    s_lo, s_hi, s_st = map(float, a.scales.split(","))
    prior = list(map(float, a.prior.split(","))) if a.prior else None
    best = (-1e18,)
    for sf in np.arange(s_lo, s_hi + 1e-9, s_st):
        for yaw in range(360):
            th = math.radians(yaw)
            R2 = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
            v = (V - cm) * sf @ R2.T
            c = (Cl[:, :2] - cm) * sf @ R2.T
            # kernels: point positions relative to the image origin (wrap-around correlation)
            K = np.zeros((H, W), np.float32)
            np.add.at(K, (np.round(-v[:, 1] / px).astype(int) % H, np.round(v[:, 0] / px).astype(int) % W), 1.0)
            KC = np.zeros((H, W), np.float32)
            np.add.at(KC, (np.round(-c[:, 1] / px).astype(int) % H, np.round(c[:, 0] / px).astype(int) % W), 1.0)
            score = np.fft.irfft2(FM * np.conj(np.fft.rfft2(K)), s=(H, W)) / max(len(v), 1)
            FKC = np.conj(np.fft.rfft2(KC))
            score -= a.cam_weight * np.fft.irfft2(FC * FKC, s=(H, W)) / len(c)
            if FW is not None:
                score += a.walk_weight * np.fft.irfft2(FW * FKC, s=(H, W)) / len(c)
            if prior:
                rr, cc = np.mgrid[0:H, 0:W]
                wx, wy = x0 + cc * px, y1 - rr * px
                score[(wx - prior[0]) ** 2 + (wy - prior[1]) ** 2 > prior[2] ** 2] = -1e9
            i = int(np.argmax(score))
            if score.flat[i] > best[0]:
                r, cidx = divmod(i, W)
                best = (float(score.flat[i]), sf, yaw, x0 + cidx * px, y1 - r * px)
    sc, sf, yaw, wx, wy = best
    th = math.radians(yaw)
    Rz = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    # world = sf * Rz @ (Xl - [cm, 0]) + [wx, wy, ground_z]   with Xl = s0 * Rl @ X + tl
    R = Rz @ Rl
    s = s0 * sf
    t = sf * Rz @ (tl - np.array([cm[0], cm[1], 0.0])) + np.array([wx, wy, a.ground_z])
    json.dump({"scale": float(s), "R": R.tolist(), "t": t.tolist(), "rms_m": -1,
               "note": f"sfm_plan_register.py: ground plane + eye {a.eye} m x {sf:.3f}, yaw {yaw} deg, plan "
                       f"match score {sc:.3f} against {os.path.basename(a.mask)}"},
              open(os.path.join(a.out, "align.json"), "w"), indent=1)
    Pw, Cw = s * P @ R.T + t, s * C @ R.T + t
    img = np.dstack([255 - M * 90] * 3).astype(np.uint8)
    Vw = Pw[(Pw[:, 2] - a.ground_z > b0) & (Pw[:, 2] - a.ground_z < b1)]
    for p in Vw:
        cv2.circle(img, (int((p[0] - x0) / px), int((y1 - p[1]) / px)), 1, (0, 0, 220), -1)
    for p in Cw:
        cv2.circle(img, (int((p[0] - x0) / px), int((y1 - p[1]) / px)), 3, (220, 0, 0), -1)
    cv2.imwrite(os.path.join(a.out, "register.png"), img)
    print(f"best: score {sc:.3f}, scale x{sf:.3f} (total {s:.4f}), yaw {yaw} deg, path centre ({wx:.2f}, {wy:.2f}); "
          f"camera z median {np.median(Cw[:, 2]):.2f}")


if __name__ == "__main__":
    sys.exit(main())
