# Focal length from one photo of a square ceiling grid (Zhang-style plane calibration with a single view: square
# pixels, principal point at the image centre -> 2 equations in f). The grid lines of each family are found with
# LSD + vanishing point (room_svm.vp_ransac), clustered into lines, intersected, and the intersections indexed
# (i, j) by order along each family. H: grid (i, j) -> image; f from h1.w.h2 = 0 and h1.w.h1 = h2.w.h2.
# Usage: python grid_focal.py PHOTO YMAX [XMIN XMAX]
import sys

import cv2
import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from room_svm import _lines, lsd, vp_ransac   # noqa: E402


def cluster_lines(S, vp):
    """Group segments of one family into individual grid lines by their angle about the vanishing point."""
    v = vp[:2] / vp[2] if abs(vp[2]) > 1e-9 else None
    mids = np.column_stack([(S[:, 0] + S[:, 2]) / 2, (S[:, 1] + S[:, 3]) / 2])
    if v is None:
        d = vp[:2] / np.linalg.norm(vp[:2]); n = np.array([-d[1], d[0]]); key = mids @ n
    else:
        key = np.arctan2(mids[:, 1] - v[1], mids[:, 0] - v[0])
    o = np.argsort(key); groups = []
    span = np.ptp(key)
    for i in o:
        if groups and key[i] - key[groups[-1][-1]] < span / 400: groups[-1].append(i)
        else: groups.append([i])
    lines = []
    for gi in groups:
        L = _lines(S[gi]); w = np.hypot(S[gi, 2] - S[gi, 0], S[gi, 3] - S[gi, 1])
        if w.sum() < 150: continue
        L = L * np.sign(L[:, 2:3] + 1e-12)                       # same sign so the segments' lines average
        l = (L * w[:, None]).sum(0)                              # weighted mean line of the group
        lines.append((l / np.linalg.norm(l[:2]), w.sum(), float(np.mean(key[gi]))))
    return lines


def main(path, ymax, xmin=0, xmax=None):
    img = cv2.imread(path); H0, W0 = img.shape[:2]; xmax = xmax or W0
    mask = np.zeros((H0, W0), np.uint8); mask[:ymax, xmin:xmax] = 1
    S = lsd(img, mask, minlen=50)
    v1, i1 = vp_ransac(S, tol_deg=1.0, seed=1); r = S[~i1]; v2, i2 = vp_ransac(r, tol_deg=1.0, seed=2)
    F1, F2 = cluster_lines(S[i1], v1), cluster_lines(r[i2], v2)
    print("lines", len(F1), len(F2))
    pts_img, pts_grid = [], []
    for a, (la, wa, ka) in enumerate(sorted(F1, key=lambda t: t[2])):
        for b, (lb, wb, kb) in enumerate(sorted(F2, key=lambda t: t[2])):
            p = np.cross(la, lb)
            if abs(p[2]) < 1e-9: continue
            p = p[:2] / p[2]
            if 0 <= p[0] < W0 and 0 <= p[1] < ymax:
                pts_img.append(p); pts_grid.append((a, b))
    pts_img, pts_grid = np.array(pts_img, np.float32), np.array(pts_grid, np.float32)
    Hm, inl = cv2.findHomography(pts_grid, pts_img, cv2.RANSAC, 3.0)
    print("crossings", len(pts_img), "inliers", int(inl.sum()))
    c = np.array([W0 / 2, H0 / 2])
    T = np.array([[1, 0, -c[0]], [0, 1, -c[1]], [0, 0, 1.0]]); Hc = T @ Hm
    h1, h2 = Hc[:, 0], Hc[:, 1]
    # w = diag(1/f^2, 1/f^2, 1): h1.w.h2 = 0 -> (h1x h2x + h1y h2y)/f^2 + h1z h2z = 0
    f_a = np.sqrt(max(-(h1[0] * h2[0] + h1[1] * h2[1]) / (h1[2] * h2[2]), 0)) if abs(h1[2] * h2[2]) > 1e-12 else np.nan
    num = (h1[0] ** 2 + h1[1] ** 2) - (h2[0] ** 2 + h2[1] ** 2); den = h2[2] ** 2 - h1[2] ** 2
    f_b = np.sqrt(num / den) if den != 0 and num / den > 0 else np.nan
    print(f"f (orthogonality) {f_a:.0f} px, f (equal sides) {f_b:.0f} px")
    return f_a, f_b


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], int(a[1]), *(int(v) for v in a[2:]))
