# Single-view room metrology (R1): Manhattan reconstruction of a box-like room from ONE photo, after Criminisi, Reid &
# Zisserman, "Single View Metrology" (IJCV 2000) and Hartley-Zisserman ch. 8.
#   1. LSD segments -> 3 orthogonal vanishing points (RANSAC, one family at a time) -> focal length from the VPs
#      (cross-check with EXIF) -> camera rotation R (room axes X, Y=up, Z).
#   2. Metric scale from a known length on a known plane: consecutive ceiling-grid crossings along a wall/ceiling
#      junction (0.60 m) fix the camera height below the ceiling (rays scale linearly with that height).
#   3. Every other point is measured by intersecting its ray with a plane: ceiling y=h, a wall found from its
#      junction with the ceiling, floor y=h-H, ...
# Used from small driver scripts; prints VPs, f and R so the calibration can be checked by eye.
import math

import cv2
import numpy as np


def lsd(img, mask=None, minlen=40):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    s = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(g)[0].reshape(-1, 4)
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    s = s[L > minlen]
    if mask is not None:
        m = np.array([mask[int((a[1] + a[3]) / 2), int((a[0] + a[2]) / 2)] > 0 for a in s])
        s = s[m]
    return s


def _lines(S):
    a = np.column_stack([S[:, 0], S[:, 1], np.ones(len(S))]); b = np.column_stack([S[:, 2], S[:, 3], np.ones(len(S))])
    l = np.cross(a, b); return l / np.linalg.norm(l[:, :2], axis=1)[:, None]


def vp_ransac(S, it=5000, tol_deg=1.5, seed=0):
    rng = np.random.default_rng(seed)
    L = _lines(S)
    mid = np.column_stack([(S[:, 0] + S[:, 2]) / 2, (S[:, 1] + S[:, 3]) / 2])
    d = np.column_stack([S[:, 2] - S[:, 0], S[:, 3] - S[:, 1]]); w = np.linalg.norm(d, axis=1); d /= w[:, None]
    best = (0, None, None)
    c = math.cos(math.radians(tol_deg))
    for _ in range(it):
        i, j = rng.choice(len(S), 2, replace=False)
        v = np.cross(L[i], L[j])
        if np.linalg.norm(v) < 1e-12: continue
        if abs(v[2]) < 1e-9 * np.linalg.norm(v[:2]):
            ray = np.tile(v[:2] / np.linalg.norm(v[:2]), (len(S), 1))
        else:
            ray = v[:2] / v[2] - mid; ray /= np.linalg.norm(ray, axis=1)[:, None] + 1e-12
        inl = np.abs(np.sum(ray * d, axis=1)) > c
        sc = w[inl].sum()
        if sc > best[0]: best = (sc, v, inl)
    # refine: least squares VP from inlier lines (smallest singular vector)
    Li = L[best[2]] * w[best[2]][:, None]
    v = np.linalg.svd(Li)[2][-1]
    return v, best[2]


class Room:
    def __init__(self, img, f_exif, S=None, vps=None, verbose=True):
        self.h_img, self.w_img = img.shape[:2]
        self.c = np.array([self.w_img / 2, self.h_img / 2])
        if vps is None:
            S = lsd(img) if S is None else S
            vps, rest = [], S
            for k in range(3):
                v, inl = vp_ransac(rest, seed=k)
                vps.append(v); rest = rest[~inl]
                if verbose: print(f"VP{k}: {inl.sum()} segs", (v[:2] / v[2]).round(1) if abs(v[2]) > 1e-9 else "inf")
        self.vps = vps
        # focal from each finite orthogonal pair: (v1-c).(v2-c) + f^2 = 0
        fs = []
        for a, b in ((0, 1), (0, 2), (1, 2)):
            va, vb = vps[a], vps[b]
            if abs(va[2]) > 1e-9 and abs(vb[2]) > 1e-9:
                p = va[:2] / va[2] - self.c; q = vb[:2] / vb[2] - self.c
                dd = -np.dot(p, q)
                if dd > 0: fs.append(math.sqrt(dd))
        self.f_vp = fs
        self.f = f_exif
        if verbose: print("focal from VP pairs", [round(x) for x in fs], "EXIF", round(f_exif))
        K = np.array([[self.f, 0, self.c[0]], [0, self.f, self.c[1]], [0, 0, 1.0]])
        self.K, self.Ki = K, np.linalg.inv(K)
        dirs = [self.Ki @ v for v in vps]; dirs = [d / np.linalg.norm(d) for d in dirs]
        self.dirs = dirs

    def set_axes(self, up, x, flip_x=False, flip_up=False):
        """Room frame: Y = up (index of the vertical VP), X = index of a horizontal VP; orthonormalised."""
        Y = self.dirs[up].copy()
        # up in camera coords points to image top (camera y axis points down)
        if (Y[1] > 0) != flip_up: Y = -Y
        X = self.dirs[x].copy(); X -= Y * (X @ Y); X /= np.linalg.norm(X)
        if flip_x: X = -X
        Z = np.cross(X, Y)
        self.R = np.vstack([X, Y, Z])       # rows: room axes in camera coords -> room = R @ cam
        return self

    def ray(self, px):
        d = self.Ki @ np.array([px[0], px[1], 1.0]); d /= np.linalg.norm(d)
        return self.R @ d                    # direction in room coords (camera at origin)

    def on_plane_y(self, px, y):
        r = self.ray(px); return r * (y / r[1])

    def on_plane(self, px, axis, val):
        r = self.ray(px); return r * (val / r[axis])
