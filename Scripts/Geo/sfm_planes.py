# Finds dominant planes in a zone SfM model (model.json from sfm_zone.py) and renders a textured ortho of any plane,
# used by R1 to read dimensions (tile pitch, step edges, door/window outlines) in model units before scaling.
# Run: uv run --python 3.12 --with numpy --with pillow python Scripts/Geo/sfm_planes.py model.json planes [--n 12]
#      ... model.json ortho <plane_idx> out.jpg [--res 0.005] [--extent u0 u1 v0 v1]
# planes.json (written next to model.json): gravity 'up' (from camera y axes) + planes [n, d, count, extent, kind].
import argparse
import json
import os

import numpy as np
from PIL import Image


def load(path):
    m = json.load(open(path))
    P = np.array([p[:3] for p in m["points"]])
    up = np.array([-np.array(c["R"])[1] for c in m["cameras"]]).mean(0)
    return m, P, up / np.linalg.norm(up)


def find_planes(P, up, n_planes, tol_frac=0.004, iters=3000, seed=0):
    rng = np.random.default_rng(seed)
    scale = np.median(np.linalg.norm(P - np.median(P, 0), axis=1))
    tol = tol_frac * scale * 3
    rem = np.arange(len(P))
    out = []
    for _ in range(n_planes):
        if len(rem) < 50:
            break
        Q = P[rem]
        best = None
        for _ in range(iters):
            a, b, c = Q[rng.choice(len(Q), 3, replace=False)]
            n = np.cross(b - a, c - a)
            if np.linalg.norm(n) < 1e-12:
                continue
            n /= np.linalg.norm(n)
            inl = np.abs((Q - a) @ n) < tol
            if best is None or inl.sum() > best[1].sum():
                best = (n, inl)
        n, inl = best
        R = Q[inl]
        c0 = R.mean(0)
        n = np.linalg.svd(R - c0)[2][-1]
        if n @ up < 0 and abs(n @ up) > 0.7:
            n = -n
        ang = np.degrees(np.arccos(min(1.0, abs(n @ up))))
        kind = "horizontal" if ang < 15 else ("vertical" if ang > 75 else "oblique")
        B = np.linalg.svd(R - c0)[2][:2]
        ext = np.ptp((R - c0) @ B.T, axis=0)
        out.append({"n": n.tolist(), "c": c0.tolist(), "count": int(inl.sum()), "angle_to_up": round(float(ang), 1),
                    "kind": kind, "extent": ext.round(3).tolist(), "height_along_up": round(float(c0 @ up), 4)})
        rem = rem[~inl]
    return out, tol


def ortho(m, plane, up, res, extent, out):
    n, c0 = np.array(plane["n"]), np.array(plane["c"])
    cams = [(c, np.array(c["center"])) for c in m["cameras"]]
    if np.mean([(C - c0) @ n for _, C in cams]) < 0:
        n = -n
    if abs(n @ up) > 0.7:           # floor/ceiling: axes = arbitrary horizontal pair
        e1 = np.cross(n, [1, 0, 0]) if abs(n[0]) < 0.9 else np.cross(n, [0, 1, 0])
    else:                           # wall: e1 horizontal along the wall, e2 = up projected
        e1 = np.cross(up, n)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    P = np.array([p[:3] for p in m["points"]])
    d = (P - c0) @ n
    uv = np.column_stack([(P - c0) @ e1, (P - c0) @ e2])[np.abs(d) < np.percentile(np.abs(d), 20)]
    if extent:
        u0, u1, v0, v1 = extent
    else:
        u0, u1 = np.percentile(uv[:, 0], [2, 98])
        v0, v1 = np.percentile(uv[:, 1], [2, 98])
    W, H = int((u1 - u0) / res), int((v1 - v0) / res)
    U, V = np.meshgrid(u0 + (np.arange(W) + 0.5) * res, v1 - (np.arange(H) + 0.5) * res)
    X = c0 + U[..., None] * e1 + V[..., None] * e2
    img = np.zeros((H, W, 3), np.float32)
    best = np.full((H, W), -1.0)
    for c, C in cams:
        R, t = np.array(c["R"]), np.array(c["t"])
        Xc = X.reshape(-1, 3) @ R.T + t
        z = Xc[:, 2]
        ok = z > 1e-6
        x = np.where(ok, c["f"] * Xc[:, 0] / np.where(ok, z, 1) + c["cx"], -1)
        y = np.where(ok, c.get("fy", c["f"]) * Xc[:, 1] / np.where(ok, z, 1) + c["cy"], -1)
        ok &= (x >= 0) & (y >= 0) & (x < c["w"] - 1) & (y < c["h"] - 1)
        view = R.T @ np.array([0, 0, 1.0])
        q = np.where(ok, abs(view @ n) / (1 + np.linalg.norm(Xc, axis=1)), -1).reshape(H, W)
        upd = q > best
        if not upd.any():
            continue
        im = np.asarray(Image.open(c["image"]).convert("RGB"), np.float32)
        xi, yi = np.clip(x.astype(int), 0, c["w"] - 1).reshape(H, W), np.clip(y.astype(int), 0, c["h"] - 1).reshape(H, W)
        img[upd] = im[yi, xi][upd]
        best[upd] = q[upd]
    Image.fromarray(img.astype(np.uint8)).save(out, quality=92)
    g = img.mean(2)
    g -= g.mean()
    F = np.abs(np.fft.fftshift(np.fft.fft2(g * np.outer(np.hanning(H), np.hanning(W)))))
    cy, cx = H // 2, W // 2
    yy, xx = np.mgrid[0:H, 0:W]
    fr = np.hypot((xx - cx) / (W * res), (yy - cy) / (H * res))
    F[fr < 3 / min(u1 - u0, v1 - v0)] = 0
    peaks = []
    for i in np.argsort(F.ravel())[::-1][:40]:
        p = 1 / fr.ravel()[i]
        if all(abs(p - q) / q > 0.03 for q, _ in peaks):
            peaks.append((p, float(np.degrees(np.arctan2((yy.ravel()[i] - cy), (xx.ravel()[i] - cx))))))
        if len(peaks) == 6:
            break
    return {"size_px": [W, H], "extent": [float(u0), float(u1), float(v0), float(v1)], "res": res,
            "fft_periods_units": [[round(p, 4), round(a, 1)] for p, a in peaks]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("cmd", choices=["planes", "ortho", "fit"])
    ap.add_argument("--box", type=float, nargs=6, metavar=("X0", "X1", "Y0", "Y1", "Z0", "Z1"),
                    help="fit: select points in this box of the sfm_views gravity frame (<prefix>_frame.json via --frame)")
    ap.add_argument("--frame", help="sfm_views *_frame.json")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--res", type=float, default=0.005)
    ap.add_argument("--extent", type=float, nargs=4)
    a = ap.parse_args()
    m, P, up = load(a.model)
    pj = os.path.join(os.path.dirname(a.model), "planes.json")
    if a.cmd == "planes":
        planes, tol = find_planes(P, up, a.n)
        json.dump({"up": up.tolist(), "tol": tol, "planes": planes}, open(pj, "w"), indent=1)
        for i, p in enumerate(planes):
            print(i, p["kind"], p["count"], "ang", p["angle_to_up"], "ext", p["extent"], "h", p["height_along_up"])
    elif a.cmd == "fit":  # fit one plane to the points inside a gravity-frame box, append it to planes.json
        f = json.load(open(a.frame))
        B, o = np.array(f["B"]), np.array(f["o"])
        Q = (P - o) @ B.T
        x0, x1, y0, y1, z0, z1 = a.box
        sel = (Q[:, 0] > x0) & (Q[:, 0] < x1) & (Q[:, 1] > y0) & (Q[:, 1] < y1) & (Q[:, 2] > z0) & (Q[:, 2] < z1)
        pl, _ = find_planes(P[sel], B[2], 1)
        data = json.load(open(pj)) if os.path.exists(pj) else {"up": B[2].tolist(), "planes": []}
        data["up"] = B[2].tolist()
        data["planes"].append(pl[0])
        json.dump(data, open(pj, "w"), indent=1)
        print(len(data["planes"]) - 1, int(sel.sum()), "pts ->", pl[0]["kind"], pl[0]["count"], "ang", pl[0]["angle_to_up"])
    else:
        data = json.load(open(pj))
        planes, up = data["planes"], np.array(data["up"])
        info = ortho(m, planes[int(a.args[0])], up, a.res, a.extent, a.args[1])
        print(json.dumps(info))


if __name__ == "__main__":
    main()
