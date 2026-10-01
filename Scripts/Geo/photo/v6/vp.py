# Vanishing points from LSD segments (least squares on homogeneous lines, iterative outlier rejection).
import numpy as np
def hline(s):
    p = np.array([s[0], s[1], 1.0]); q = np.array([s[2], s[3], 1.0]); l = np.cross(p, q)
    return l / np.hypot(l[0], l[1])
def fit_vp(S, iters=5, thr=3.0):
    S = np.asarray(S); L = np.array([hline(s) for s in S]); w = np.hypot(S[:,2]-S[:,0], S[:,3]-S[:,1])
    keep = np.ones(len(S), bool)
    for _ in range(iters):
        A = L[keep] * np.sqrt(w[keep])[:, None]
        v = np.linalg.svd(A)[2][-1]
        # residual: angle between the segment and the line from its midpoint to v, in px at the segment end
        m = (S[:, :2] + S[:, 2:]) / 2
        d = np.array([v[0] - v[2]*m[:,0], v[1] - v[2]*m[:,1]]).T
        dirs = (S[:, 2:] - S[:, :2]) / w[:, None]
        sinang = np.abs(dirs[:,0]*d[:,1] - dirs[:,1]*d[:,0]) / (np.hypot(d[:,0], d[:,1]) + 1e-12)
        res = sinang * w / 2
        keep = res < thr
    return v, keep, res
