# Helpers for room_svm.py: find ceiling-grid crossings along a straight ceiling/wall (or ceiling/bulkhead) junction.
# The junction is given by two image points; tile joints are dark thin lines that hit it, so the intensity profile
# sampled a few px on the ceiling side of the junction has minima at the crossings. (R1, C105/C204 metrology)
import cv2
import numpy as np


def crossings(gray, p0, p1, off=8, band=5, min_gap=120, prom=3.0):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    L = np.linalg.norm(p1 - p0); u = (p1 - p0) / L; n = np.array([u[1], -u[0]])   # n: image "up" side for left->right
    if n[1] > 0: n = -n
    t = np.arange(0, L, 1.0)
    prof = np.zeros_like(t)
    for k in range(off, off + band):
        q = p0[None] + t[:, None] * u[None] + k * n[None]
        prof += cv2.remap(gray, q[:, 0].astype(np.float32).reshape(1, -1), q[:, 1].astype(np.float32).reshape(1, -1),
                          cv2.INTER_LINEAR).ravel()
    prof /= band
    bg = cv2.GaussianBlur(prof.reshape(1, -1), (0, 0), 12).ravel()
    d = bg - prof
    idx = [i for i in range(3, len(d) - 3) if d[i] == d[i - 3:i + 4].max() and d[i] > prom]
    idx = sorted(idx, key=lambda i: -d[i]); keep = []
    for i in idx:
        if all(abs(i - j) > min_gap for j in keep): keep.append(i)
    keep.sort()
    return [tuple((p0 + t[i] * u).round(1)) for i in keep], [round(float(d[i]), 1) for i in keep]
