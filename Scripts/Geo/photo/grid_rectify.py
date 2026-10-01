# Ceiling-grid photogrammetry (R1): rectifies the plane of a suspended ceiling from ONE photo using its tile grid
# (square module, default 0.60 m). LSD line segments -> two vanishing points (RANSAC) -> lines of each family ->
# homography that maps the grid to integer tile coordinates -> top view in metres. Prints the grid lines found with
# their tile index and writes a labelled top view (1 px = 1 cm) for checking by eye.
# Usage: python grid_rectify.py PHOTO OUT_PREFIX [--ymax PX] [--tile 0.6]
import argparse
import itertools
import math

import cv2
import numpy as np


def segments(img, ymax, minlen):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    s = lsd.detect(g[:ymax])[0].reshape(-1, 4)
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    return s[L > minlen]


def homog_line(s):
    a = np.array([s[0], s[1], 1.0]); b = np.array([s[2], s[3], 1.0])
    l = np.cross(a, b)
    return l / np.linalg.norm(l[:2])


def vp_ransac(S, it=4000, tol_deg=1.0, rng=np.random.default_rng(0)):
    """Vanishing point with the most segments pointing at it (angle between the segment and the ray to the VP)."""
    lines = np.array([homog_line(s) for s in S])
    mids = np.column_stack([(S[:, 0] + S[:, 2]) / 2, (S[:, 1] + S[:, 3]) / 2])
    dirs = np.column_stack([S[:, 2] - S[:, 0], S[:, 3] - S[:, 1]]); dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    w = np.hypot(S[:, 2] - S[:, 0], S[:, 3] - S[:, 1])
    best = (0, None, None)
    for _ in range(it):
        i, j = rng.choice(len(S), 2, replace=False)
        v = np.cross(lines[i], lines[j])
        if abs(v[2]) < 1e-12:
            ray = np.tile(v[:2] / np.linalg.norm(v[:2]), (len(S), 1))
        else:
            ray = v[:2] / v[2] - mids
            ray /= np.linalg.norm(ray, axis=1)[:, None] + 1e-12
        cosang = np.abs(np.sum(ray * dirs, axis=1))
        inl = cosang > math.cos(math.radians(tol_deg))
        sc = w[inl].sum()
        if sc > best[0]:
            best = (sc, v, inl)
    return best[1], best[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo"); ap.add_argument("out")
    ap.add_argument("--ymax", type=int, default=10 ** 9)
    ap.add_argument("--tile", type=float, default=0.6)
    ap.add_argument("--minlen", type=float, default=60)
    ap.add_argument("--span", type=float, default=6.0, help="half size of the top view around the grid centre (m)")
    a = ap.parse_args()
    img = cv2.imread(a.photo)
    H0, W0 = img.shape[:2]
    S = segments(img, min(a.ymax, H0), a.minlen)
    v1, in1 = vp_ransac(S)
    rest = S[~in1]
    v2, in2r = vp_ransac(rest)
    fam = [S[in1], rest[in2r]]
    print("segments", len(S), "family sizes", [len(f) for f in fam])
    # projective -> affine: send the vanishing line to infinity
    vl = np.cross(v1, v2); vl = vl / vl[2]
    Hp = np.array([[1, 0, 0], [0, 1, 0], vl], float)
    def tr(H, p):
        q = H @ np.array([p[0], p[1], 1.0]); return q[:2] / q[2]
    # in the affine frame each family is a set of parallel lines; take their directions
    def fam_dir(F, H):
        d = []
        for s in F:
            p, q = tr(H, s[:2]), tr(H, s[2:])
            v = q - p; v /= np.linalg.norm(v)
            if v[0] < 0 or (abs(v[0]) < 1e-9 and v[1] < 0): v = -v
            d.append(v)
        d = np.median(np.array(d), axis=0); return d / np.linalg.norm(d)
    d1, d2 = fam_dir(fam[0], Hp), fam_dir(fam[1], Hp)
    # affine -> similarity: make d1 _|_ d2 (grid is square): map d1 -> x, d2 -> y
    A = np.linalg.inv(np.column_stack([d1, d2]))
    Ha = np.eye(3); Ha[:2, :2] = A
    H = Ha @ Hp
    # line offsets: family 1 lines are y = const? (d1 -> x axis, so family-1 lines are horizontal: offset = y)
    def offsets(F, axis):
        o, w = [], []
        for s in F:
            p, q = tr(H, s[:2]), tr(H, s[2:])
            o.append((p[axis] + q[axis]) / 2); w.append(np.linalg.norm(q - p))
        return np.array(o), np.array(w)
    oy, wy = offsets(fam[0], 1)   # horizontal lines (family 1): their y
    ox, wx = offsets(fam[1], 0)   # vertical lines (family 2): their x
    def cluster(o, w, tol):
        idx = np.argsort(o); cl = []
        for i in idx:
            if cl and o[i] - cl[-1][-1][0] < tol: cl[-1].append((o[i], w[i]))
            else: cl.append([(o[i], w[i])])
        return [(sum(p * q for p, q in c) / sum(q for _, q in c), sum(q for _, q in c)) for c in cl]
    # spacing: robust median gap between strong clusters, both families must agree up to the unknown scale
    span = max(np.ptp(oy), np.ptp(ox))
    cy = cluster(oy, wy, span / 200); cx = cluster(ox, wx, span / 200)
    def module(c):
        c = [p for p, w in c if w > 0.5 * np.median([w for _, w in c])]
        g = np.diff(sorted(c)); g = g[g > 0.3 * np.median(g)]
        return np.median(g)
    my, mx = module(cy), module(cx)
    print("module (affine units) y", round(my, 5), "x", round(mx, 5), "ratio", round(my / mx, 4))
    # final metric: scale so that one module = tile (m); fix the x/y ratio from the square module
    Hs = np.diag([a.tile / mx, a.tile / my, 1.0])
    Hm = Hs @ H
    res = {"H": Hm.tolist(), "lines_x_m": [], "lines_y_m": []}
    for name, c, m in (("x", cx, mx), ("y", cy, my)):
        vals = sorted(p * a.tile / m for p, w in c)
        res[f"lines_{name}_m"] = [round(v, 3) for v in vals]
        base = vals[0]
        print(f"{name}-lines (m):", [round(v - base, 3) for v in vals])
    np.save(a.out + "_H.npy", Hm)
    # top view: 1 px = 1 cm over the ceiling region
    corners = np.array([[0, 0], [W0, 0], [W0, min(a.ymax, H0)], [0, min(a.ymax, H0)]], float)
    pc = np.array([tr(Hm, p) for p in corners])
    x0, y0 = pc.min(0); x1, y1 = pc.max(0)
    cx_, cy_ = np.median(res["lines_x_m"]), np.median(res["lines_y_m"])
    x0, y0 = max(x0, cx_ - a.span), max(y0, cy_ - a.span)          # far-away parts of the plane blow up: clip
    x1, y1 = min(x1, cx_ + a.span), min(y1, cy_ + a.span)
    T = np.array([[100, 0, -100 * x0], [0, 100, -100 * y0], [0, 0, 1]], float)
    Wt, Ht = int(100 * (x1 - x0)), int(100 * (y1 - y0))
    top = cv2.warpPerspective(img, T @ Hm, (Wt, Ht), flags=cv2.INTER_LINEAR)
    for v in res["lines_x_m"]:
        X = int(100 * (v - x0)); cv2.line(top, (X, 0), (X, 12), (0, 0, 255), 2)
        cv2.putText(top, f"{v - res['lines_x_m'][0]:.2f}", (X + 2, 26), 0, 0.45, (0, 0, 255), 1)
    for v in res["lines_y_m"]:
        Y = int(100 * (v - y0)); cv2.line(top, (0, Y), (12, Y), (255, 0, 0), 2)
        cv2.putText(top, f"{v - res['lines_y_m'][0]:.2f}", (14, Y + 5), 0, 0.45, (255, 0, 0), 1)
    cv2.imwrite(a.out + "_top.jpg", top)
    dbg = img[:min(a.ymax, H0)].copy()
    for s, col in itertools.chain(((s, (0, 0, 255)) for s in fam[0]), ((s, (255, 0, 0)) for s in fam[1])):
        cv2.line(dbg, (int(s[0]), int(s[1])), (int(s[2]), int(s[3])), col, 3)
    cv2.imwrite(a.out + "_lines.jpg", cv2.resize(dbg, None, fx=0.5, fy=0.5))
    print("top view", Wt, "x", Ht, "cm")


if __name__ == "__main__":
    main()
