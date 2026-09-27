# World pose of a zone component from building outlines (R1 pass P0, handoff section 4.2, automatic control
# "corners"): the BLD spec rings near the zone give 3D lines (wall base, eave, vertical corners); for a candidate
# pose (yaw, x, y, z) with up and scale fixed (zone_world.py: ground planes, eye height) the lines are projected into
# ~10 solved frames of the component and scored by the image gradient across them. Coarse grid inside the zone prior
# (job.json world_prior [x, y, r], optional yaw_prior [deg, span]) -> local refinement -> <comp>/align.json.
# Usage: python outline_fit.py <comp_dir> [--work C:/koch/work] [--eye 1.52] [--frames 10] [--out align.json]
import argparse
import glob
import json
import math
import os
import sys

import cv2
import numpy as np
import open3d as o3d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zone_world as zw  # noqa: E402

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")


def spec_rings(prior, pad=70.0):
    out = []
    for f in glob.glob(os.path.join(REPO, "Art", "Blender", "Specs", "BLD_*.json")):
        s = json.load(open(f, encoding="utf-8")); a = s.get("anchor")
        if not a:
            continue
        o = np.array(a["world_xy"]); xd = np.array(a["x_dir"], float); xd /= np.linalg.norm(xd); yd = np.array([-xd[1], xd[0]])
        W = np.array([o + p[0] * xd + p[1] * yd for p in s["ring"]], np.float32)
        if min(np.hypot(*(w - prior[:2])) for w in W) <= prior[2] + pad:
            out.append(W)
    return out


def spec_lines(prior, pad=70.0, n=24):
    """3D polylines (world) of the building outlines within prior radius + pad: base, eave, vertical corners."""
    L = []
    for f in glob.glob(os.path.join(REPO, "Art", "Blender", "Specs", "BLD_*.json")):
        s = json.load(open(f, encoding="utf-8"))
        a = s.get("anchor")
        if not a or s.get("ffl_z") is None:
            continue
        o = np.array(a["world_xy"]); xd = np.array(a["x_dir"], float); xd /= np.linalg.norm(xd); yd = np.array([-xd[1], xd[0]])
        W = [o + p[0] * xd + p[1] * yd for p in s["ring"]]
        if min(np.hypot(*(w - prior[:2])) for w in W) > prior[2] + pad:
            continue
        zb = s["ffl_z"] - s.get("plinth_m", 0.6); ze = s["ffl_z"] + s.get("eave_z", 6.0)
        t = np.linspace(0, 1, n)[:, None]
        for i in range(len(W)):
            A, B = W[i], W[(i + 1) % len(W)]
            if np.hypot(*(B - A)) < 1.0:
                continue
            seg = A + (B - A) * t
            for z in (zb, ze):
                L.append(np.c_[seg, np.full(n, z)])
            L.append(np.c_[np.tile(A, (n, 1)), zb + (ze - zb) * t[:, 0]])
    return np.array(L)


class Cams:
    def __init__(self, cams):
        self.c = []
        for c in cams:
            g = cv2.GaussianBlur(cv2.imread(c["image"], cv2.IMREAD_GRAYSCALE), (0, 0), 2.0).astype(np.float32)
            g = cv2.resize(g, None, fx=0.5, fy=0.5)
            gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1); nr = np.percentile(np.hypot(gx, gy), 99) + 1e-6
            self.c.append((c, gx / nr, gy / nr))

    def score(self, L, Rw, t, s):
        """Mean oriented gradient of lines L (k, n, 3 world) for the pose world = s Rw x + t."""
        tot, cnt = 0.0, 0
        P = L.reshape(-1, 3)
        for c, gx, gy in self.c:
            Rc = np.array(c["R"]); C = s * (Rw @ np.array(c["center"])) + t
            Y = (P - C) @ (Rc @ Rw.T).T
            z = Y[:, 2]; front = z > 0.5
            u = 0.5 * (c["f"] * Y[:, 0] / np.where(front, z, 1) + c["cx"]); v = 0.5 * (c["fy"] * Y[:, 1] / np.where(front, z, 1) + c["cy"])
            u, v, front = u.reshape(L.shape[:2]), v.reshape(L.shape[:2]), front.reshape(L.shape[:2])
            du, dv = np.gradient(u, axis=1), np.gradient(v, axis=1); ln = np.hypot(du, dv) + 1e-9
            ok = front & (u > 1) & (u < gx.shape[1] - 2) & (v > 1) & (v < gx.shape[0] - 2)
            if ok.sum() < 30:
                continue
            ui, vi = u[ok].astype(int), v[ok].astype(int)
            tot += np.abs(gx[vi, ui] * (-dv[ok] / ln[ok]) + gy[vi, ui] * (du[ok] / ln[ok])).mean(); cnt += 1
        return tot / max(cnt, 1), cnt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comp"); ap.add_argument("--work", default=r"C:\koch\work")
    ap.add_argument("--eye", type=float, default=1.52); ap.add_argument("--frames", type=int, default=10)
    ap.add_argument("--out", default="align.json")
    ap.add_argument("--eval", help="only score this align.json (debug)")
    a = ap.parse_args()
    zone = os.path.basename(os.path.dirname(os.path.abspath(a.comp)))
    job = json.load(open(os.path.join(a.work, "zones", zone, "job.json"), encoding="utf-8-sig"))
    prior = np.array(job["world_prior"], float)
    m = json.load(open(os.path.join(a.comp, "model.json")))
    tm = o3d.io.read_triangle_mesh(os.path.join(a.comp, "mesh.obj"), enable_post_processing=False)
    sc = o3d.t.geometry.RaycastingScene()
    sc.add_triangles(o3d.core.Tensor(np.asarray(tm.vertices).astype(np.float32)), o3d.core.Tensor(np.asarray(tm.triangles).astype(np.uint32)))
    gp = zw.ground_planes(sc, m); del tm, sc
    up = np.median([g[0] for g in gp], 0); up /= np.linalg.norm(up); h = float(np.median([g[1] for g in gp])); s = a.eye / h
    Rl = zw.rot_to_z(up)
    cams = m["cameras"]; sel = [cams[i] for i in np.linspace(0, len(cams) - 1, min(a.frames, len(cams))).astype(int)]
    CS = Cams(sel)
    L = spec_lines(prior)
    rings = spec_rings(prior)
    def inside(xy):   # cameras inside a building footprint: impossible pose (shrink 0.5 m for doorways)
        return any(cv2.pointPolygonTest(r.reshape(-1, 1, 2), (float(x), float(y)), True) > 0.5 for r in rings for x, y in xy)
    Cm = np.array([s * (Rl @ np.array(c["center"])) for c in cams]); cm = Cm.mean(0)
    zc = float(np.median([zw.terrain_z(*prior[:2])])) + a.eye            # camera height in the world (P0)
    if a.eval:
        al = json.load(open(a.eval)); print("score of", a.eval, CS.score(L, np.array(al["R"]) / al["scale"] * al["scale"] / np.linalg.norm(np.array(al["R"])[0]) if False else np.array(al["R"]), np.array(al["t"]), al["scale"]))
        return 0
    yp = job.get("yaw_prior")
    yaws = np.arange(yp[0] - yp[1], yp[0] + yp[1] + 1e-9, 3.0) if yp else np.arange(0, 360, 4.0)
    best = []
    step = 2.0
    for th in yaws:
        c, si = math.cos(math.radians(th)), math.sin(math.radians(th))
        R3 = np.array([[c, -si, 0], [si, c, 0], [0, 0, 1]]); Rw = R3 @ Rl
        cmr = R3 @ cm
        for dx in np.arange(-prior[2], prior[2] + 1e-9, step):
            for dy in np.arange(-prior[2], prior[2] + 1e-9, step):
                if dx * dx + dy * dy > prior[2] ** 2:
                    continue
                t = np.array([prior[0] + dx, prior[1] + dy, zc]) - cmr
                if inside((Cm[::max(1, len(Cm) // 12)] @ R3.T + t)[:, :2]):
                    continue
                sc_, n = CS.score(L, Rw, t, s)
                if n >= max(3, len(sel) // 2):
                    best.append((sc_, th, t))
    best.sort(key=lambda b: -b[0])
    def rz(th):
        c, si = math.cos(math.radians(th)), math.sin(math.radians(th)); return np.array([[c, -si, 0], [si, c, 0], [0, 0, 1]])
    def ev(th, pos):
        R3 = rz(th); t = pos - R3 @ cm
        if inside((Cm[::max(1, len(Cm) // 12)] @ R3.T + t)[:, :2]):
            return -1.0, t
        sc_, n = CS.score(L, R3 @ Rl, t, s)
        return (sc_ if n >= max(3, len(sel) // 2) else -1.0), t
    print("coarse top:", [(round(b[0], 3), round(b[1], 1), np.round((rz(b[1]) @ cm + b[2])[:2], 1).tolist()) for b in best[:5]])
    # coordinate descent on (yaw, centroid x, y, z) from the best 3 coarse poses, steps halving
    ref = []
    for sc0, th0, t0 in best[:3]:
        pos = rz(th0) @ cm + t0
        for st_th, st in ((1.0, 0.5), (0.5, 0.25), (0.2, 0.1)):
            while True:
                cand = [(th0 + d, pos) for d in (-st_th, st_th)] + [(th0, pos + np.array(v) * st) for v in
                        ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
                scs = [(ev(th, p_)[0], th, p_) for th, p_ in cand]
                b = max(scs, key=lambda x: x[0])
                if b[0] <= sc0 + 1e-6:
                    break
                sc0, th0, pos = b
        ref.append((sc0, th0, ev(th0, pos)[1]))
    ref.sort(key=lambda b: -b[0])
    sc0, th0, t0 = ref[0]
    Rw = rz(th0) @ Rl
    ratio = sc0 / max(best[min(len(best) - 1, 20)][0], 1e-9)
    json.dump({"scale": float(s), "R": Rw.tolist(), "t": t0.tolist(), "score": float(sc0), "theta_deg": float(th0),
               "peak_vs_20th": float(ratio), "frames": [c["name"] for c in sel],
               "note": "outline_fit.py P0: building outlines of the specs vs photo edges, up/scale from ground planes + eye height"},
              open(os.path.join(a.comp, a.out), "w"), indent=1)
    camw = np.array([s * (Rw @ np.array(c["center"])) + t0 for c in cams])
    print(f"{a.comp}: score {sc0:.3f} (x{ratio:.2f} over the 20th), yaw {th0:.1f}, scale {s:.4f}, cams x {camw[:, 0].min():.1f}..{camw[:, 0].max():.1f} y {camw[:, 1].min():.1f}..{camw[:, 1].max():.1f}")


if __name__ == "__main__":
    sys.exit(main())
