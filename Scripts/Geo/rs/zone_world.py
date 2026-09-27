# One world frame for every zone component of the GPU queue (R1 pass P0, handoff section 4.2): each RealityScan
# component (C:\koch\work\zones\<zone>\c<N>\ with model.json + mesh.obj) gets its own similarity to the campus world:
#   up     median normal of the ground planes fitted under the phone cameras (forward-down rays into the mesh);
#   scale  eye height / median camera height over that ground (the same owner, phone at chest/face: --eye 1.52 m,
#          measured on the C entrance where the scale came from the 0.20 x 0.10 paver module);
#   yaw+xy wall points of the levelled mesh (near-vertical faces 1-12 m above the ground) cross-correlated with the
#          building-spec walls (Art/Blender/Specs/BLD_*.json rings + footprints.json) over 360 deg, refined at 0.2 deg;
#   z      terrain base of Art/Blender/Data/terrain.json under the camera path (P0 only; route_profile.py REG lines
#          and the known levels refine it).
# Writes <comp>/align.json {scale, R, t} (world = scale * R @ x + t, the sfm_overlay.py / route_profile.py format),
# <comp>/register_check.png, and one summary line per component. A component whose best/second-best peak ratio is low
# is flagged "weak" (ambiguous walls) and needs control points or a manual yaw.
# Usage: python zone_world.py [--zones C_sw,AW,Gate] [--work C:/koch/work] [--eye 1.52] [--force]
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
from rs_world import raster_lines, world_walls  # noqa: E402

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")


def rot_to_z(up):
    up = up / np.linalg.norm(up); z = np.array([0.0, 0.0, 1.0])
    v = np.cross(up, z); s = np.linalg.norm(v); c = up @ z
    if s < 1e-9:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)


def ground_planes(scene, model):
    """Per camera: plane of forward-down ray hits -> (normal pointing to the camera, camera height in units)."""
    out = []
    for c in model["cameras"]:
        R = np.array(c["R"]); o = np.array(c["center"])
        us, vs = np.meshgrid(np.linspace(0.2, 0.8, 9) * c["w"], np.linspace(0.78, 0.97, 6) * c["h"])
        d = np.stack([(us.ravel() - c["cx"]) / c["f"], (vs.ravel() - c["cy"]) / c["fy"], np.ones(us.size)], 1) @ R
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        t = scene.cast_rays(o3d.core.Tensor(np.concatenate([np.tile(o, (len(d), 1)), d], 1).astype(np.float32)))["t_hit"].numpy()
        ok = np.isfinite(t)
        if ok.sum() < 20:
            continue
        P = o + d[ok] * t[ok, None]; ctr = P.mean(0)
        _, sv, vt = np.linalg.svd(P - ctr, full_matrices=False)
        if sv[2] > 0.25 * sv[1]:
            continue                                  # not a plane (hit a wall, a car, a tree)
        n = vt[2] if vt[2] @ (o - ctr) > 0 else -vt[2]
        out.append((n, float((o - ctr) @ n), c["center"]))
    return out


def robust_up(gp, model, max_dev=20.0):
    """Up and camera height from the ground planes that agree with the cameras' image-up axis (planes fitted on
    hole-filled mesh next to the walker can be anything); falls back to the camera up when too few agree."""
    cu = np.mean([np.array(c["R"]).T @ np.array([0.0, -1.0, 0.0]) for c in model["cameras"]], 0); cu /= np.linalg.norm(cu)
    good = [g for g in gp if np.degrees(np.arccos(np.clip(g[0] @ cu, -1, 1))) < max_dev]
    if len(good) >= 8:
        up = np.median([g[0] for g in good], 0); up /= np.linalg.norm(up)
    else:
        up = cu
    hs = [g[1] for g in good] if good else [g[1] for g in gp]
    return up, float(np.median(hs)), len(good)


def terrain_z(x, y):
    t = json.load(open(os.path.join(REPO, "Art", "Blender", "Data", "terrain.json")))
    c = t["base"]["coef"]; X, Y = x / 100.0, y / 100.0
    return c[0] + c[1] * X + c[2] * Y + c[3] * X * X + c[4] * X * Y + c[5] * Y * Y


def register(P, rings, s, px=0.5, blur=2.0, margin=40.0, ths=None, prior=None):
    allw = np.concatenate(rings)
    wlo, whi = allw.min(0) - margin, allw.max(0) + margin
    H = int(2 ** np.ceil(np.log2((whi[1] - wlo[1]) / px * 1.5))); W = int(2 ** np.ceil(np.log2((whi[0] - wlo[0]) / px * 1.5)))
    off = np.array([W - (whi[0] - wlo[0]) / px, H - (whi[1] - wlo[1]) / px]) / 2
    world = cv2.GaussianBlur(raster_lines(rings, wlo - off * px, px, (H, W), width=2), (0, 0), blur)
    Fw = np.fft.rfft2(world)
    pc = P.mean(0); Pc = P - pc
    # translation window: the wall centroid must land within prior radius of the prior centre (zone position)
    mask = None
    if prior:
        yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
        dxs = np.where(xx > W / 2, xx - W, xx); dys = np.where(yy > H / 2, yy - H, yy)
        X0 = wlo[0] - off[0] * px + (W / 2 + dxs) * px; Y0 = wlo[1] - off[1] * px + (H - 1 - (H / 2 + dys)) * px
        mask = np.hypot(X0 - prior[0], Y0 - prior[1]) <= prior[2]
    res = []
    for th in ths:
        c, si = math.cos(math.radians(th)), math.sin(math.radians(th))
        Q = s * (Pc @ np.array([[c, si], [-si, c]]))
        iu = np.round(Q[:, 0] / px + W / 2).astype(int); iv = np.round(H / 2 - Q[:, 1] / px).astype(int)
        ok = (iu >= 0) & (iu < W) & (iv >= 0) & (iv < H)
        img = np.zeros((H, W), np.float32); np.add.at(img, (iv[ok], iu[ok]), 1.0); img = np.minimum(img, 3.0)
        cc = np.fft.irfft2(Fw * np.conj(np.fft.rfft2(img)), s=(H, W))
        if mask is not None:
            cc = np.where(mask, cc, -1e9)
        k = int(np.argmax(cc)); res.append((float(cc.flat[k] / max(ok.sum(), 1)), th, k // W, k % W))
    res.sort(key=lambda r: -r[0])
    score, th, dy, dx = res[0]
    dy = dy - H if dy > H / 2 else dy; dx = dx - W if dx > W / 2 else dx
    c, si = math.cos(math.radians(th)), math.sin(math.radians(th)); R2 = np.array([[c, -si], [si, c]])
    x0 = wlo[0] - off[0] * px + (W / 2 + dx) * px; y0 = wlo[1] - off[1] * px + (H - 1 - (H / 2 + dy)) * px
    t2 = np.array([x0, y0]) - s * R2 @ pc
    # second best more than 10 deg away: ambiguity of the wall pattern
    alt = next((r for r in res[1:] if min(abs(r[1] - th), 360 - abs(r[1] - th)) > 10), None)
    return score, th, R2, t2, (alt[0] if alt else 0.0), wlo, whi


def ortho_ground(tm, Rl, s, zg, px=0.25):
    """Top-down colour image of the levelled, scaled mesh, ground-level hits only (<= 1.2 m above the ground:
    paving, planters, kerbs, wall bases), for matching against the satellite orthophoto."""
    V = (np.asarray(tm.vertices) @ Rl.T) * s; F = np.asarray(tm.triangles)
    col = np.asarray(tm.vertex_colors) if tm.has_vertex_colors() else None
    sc = o3d.t.geometry.RaycastingScene()
    sc.add_triangles(o3d.core.Tensor(V.astype(np.float32)), o3d.core.Tensor(F.astype(np.uint32)))
    lo, hi = np.percentile(V[:, :2], 1, axis=0), np.percentile(V[:, :2], 99, axis=0)
    xs = np.arange(lo[0], hi[0], px); ys = np.arange(hi[1], lo[1], -px)
    X, Y = np.meshgrid(xs, ys)
    z0 = zg * s + 1.2
    R = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z0), np.zeros(X.size), np.zeros(X.size), -np.ones(X.size)], 1)
    ans = sc.cast_rays(o3d.core.Tensor(R.astype(np.float32)))
    t = ans["t_hit"].numpy(); pid = ans["primitive_ids"].numpy(); uv = ans["primitive_uvs"].numpy()
    ok = np.isfinite(t) & (t < 3.0)
    img = np.zeros((X.size, 3), np.float32)
    if col is not None:
        f = F[pid[ok]]; w = np.stack([1 - uv[ok, 0] - uv[ok, 1], uv[ok, 0], uv[ok, 1]], 1)
        img[ok] = (col[f] * w[:, :, None]).sum(1) * 255
    else:
        img[ok] = 128
    return img.reshape(X.shape + (3,))[:, :, ::-1].astype(np.uint8), ok.reshape(X.shape), (xs[0], ys[0])


def register_ortho(img, mask, origin, sat, sat_origin, px, prior, ths):
    """Rotation search + FFT cross-correlation of gradient images (mesh ground ortho vs satellite)."""
    def grad(g):
        g = cv2.GaussianBlur(cv2.cvtColor(g, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0)
        return np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    Gs = grad(sat); Gs = (Gs - Gs.mean()) / (Gs.std() + 1e-6)
    Gm = grad(img); Gm[cv2.erode(mask.astype(np.uint8), np.ones((5, 5), np.uint8)) == 0] = 0
    Gm = (Gm - Gm[mask].mean()) / (Gm[mask].std() + 1e-6); Gm[~mask] = 0
    H, W = Gs.shape; Fs = np.fft.rfft2(Gs)
    h, w = Gm.shape; c0 = np.array([w / 2, h / 2])
    # world position of the mesh image centre for a correlation shift (dy, dx): mesh pixel (u,v) -> sat pixel (u+dx, v+dy)
    res = []
    for th in ths:
        M = cv2.getRotationMatrix2D(tuple(c0), th, 1.0)   # rotates the image by +th (counter-clockwise in the picture)
        Wd = int(np.ceil(np.hypot(w, h))); M[:, 2] += (Wd / 2 - c0)
        R = cv2.warpAffine(Gm, M, (Wd, Wd)); Rm = cv2.warpAffine(mask.astype(np.float32), M, (Wd, Wd)) > 0.5
        canvas = np.zeros((H, W), np.float32); canvas[:Wd, :Wd] = R
        cc = np.fft.irfft2(Fs * np.conj(np.fft.rfft2(canvas)), s=(H, W)) / max(Rm.sum(), 1)
        yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
        cx = sat_origin[0] + (xx + Wd / 2) * px; cy = sat_origin[1] - (yy + Wd / 2) * px   # world of the rotated centre
        cc = np.where(np.hypot(cx - prior[0], cy - prior[1]) <= prior[2], cc, -1e9)
        k = int(np.argmax(cc)); res.append((float(cc.flat[k]), th, k // W, k % W, Wd))
    res.sort(key=lambda r: -r[0])
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones"); ap.add_argument("--work", default=r"C:\koch\work")
    ap.add_argument("--eye", type=float, default=1.52); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    specs = os.path.join(REPO, "Art", "Blender", "Specs"); fps = os.path.join(REPO, "Art", "Blender", "Data", "footprints.json")
    rings = world_walls(specs, fps)
    zones = a.zones.split(",") if a.zones else sorted(os.listdir(os.path.join(a.work, "zones")))
    for z in zones:
        for comp in sorted(glob.glob(os.path.join(a.work, "zones", z, "c[0-9]*"))):
            mj, mo = os.path.join(comp, "model.json"), os.path.join(comp, "mesh.obj")
            outp = os.path.join(comp, "align.json")
            if not (os.path.exists(mj) and os.path.exists(mo)) or (os.path.exists(outp) and not a.force):
                continue
            tag = f"{z}/{os.path.basename(comp)}"
            m = json.load(open(mj))
            tm = o3d.io.read_triangle_mesh(mo, enable_post_processing=False)
            V = np.asarray(tm.vertices); F = np.asarray(tm.triangles)
            sc = o3d.t.geometry.RaycastingScene()
            sc.add_triangles(o3d.core.Tensor(V.astype(np.float32)), o3d.core.Tensor(F.astype(np.uint32)))
            gp = ground_planes(sc, m)
            if len(gp) < 5:
                print(f"{tag}: {len(gp)} ground planes, skipped"); continue
            up, h, ngood = robust_up(gp, m); s = a.eye / h
            Rl = rot_to_z(up)
            L = V @ Rl.T
            T = L[F]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ar = np.linalg.norm(n, axis=1); n = n / (ar[:, None] + 1e-12)
            C = np.array([Rl @ np.array(g[2]) for g in gp]); zg = np.median(C[:, 2]) - h
            cen = T.mean(1)
            wall = (np.abs(n[:, 2]) < 0.1) & (cen[:, 2] > zg + 1.0 / s) & (cen[:, 2] < zg + 12.0 / s) & (ar > np.percentile(ar, 20))
            P = cen[wall][:, :2]
            if len(P) < 500:
                print(f"{tag}: only {len(P)} wall points, skipped"); continue
            if len(P) > 200000:
                P = P[np.random.default_rng(0).choice(len(P), 200000, replace=False)]
            job = json.load(open(os.path.join(a.work, "zones", z, "job.json"), encoding="utf-8-sig"))
            prior = job.get("world_prior")               # [x, y, radius] of the zone's wall centroid, world metres
            # yaw prior [deg, span] = heading of the levelled mesh x axis in the world (from a known pair of views or
            # the walking direction); the search is 360 deg without it
            yp = job.get("yaw_prior")
            ths = np.arange(yp[0] - yp[1], yp[0] + yp[1] + 1e-9, 1.0) if yp else np.arange(0, 360, 1.0)
            score, th, R2, t2, alt, wlo, whi = register(P, rings, s, ths=ths, prior=prior)
            score, th, R2, t2, _, wlo, whi = register(P, rings, s, px=0.25, blur=1.5, ths=np.arange(th - 1.5, th + 1.51, 0.2), prior=prior)
            R3 = np.eye(3); R3[:2, :2] = R2; Rw = R3 @ Rl
            cam_w = s * (Rw @ np.array(m["cameras"][len(m["cameras"]) // 2]["center"]))
            camxy = s * np.array([Rw @ np.array(c["center"]) for c in m["cameras"]])[:, :2] + t2
            zc = float(np.median([terrain_z(*p) for p in camxy]))
            tz = zc + a.eye - s * float(np.median(C[:, 2]))
            ratio = score / max(alt, 1e-9)
            json.dump({"scale": float(s), "R": Rw.tolist(), "t": [float(t2[0]), float(t2[1]), float(tz)],
                       "theta_deg": float(th), "score": score, "peak_ratio": float(ratio), "eye_m": a.eye,
                       "cam_height_units": float(h), "ground_planes": len(gp),
                       "note": "zone_world.py P0: up from ground planes, scale from eye height, yaw/xy from walls vs specs, z from terrain base"},
                      open(outp, "w"), indent=1)
            # check image: spec walls red, registered wall points blue, camera path green (0.25 m/px)
            Q = s * (P @ R2.T) + t2; vpx = 0.25
            VW, VH = int((whi[0] - wlo[0]) / vpx) + 1, int((whi[1] - wlo[1]) / vpx) + 1
            vis = np.full((VH, VW, 3), 255, np.uint8)
            for pts, col in ((Q, (200, 120, 40)), (camxy, (0, 170, 0))):
                iu = ((pts[:, 0] - wlo[0]) / vpx).astype(int); iv = (VH - 1 - (pts[:, 1] - wlo[1]) / vpx).astype(int)
                ok = (iu >= 0) & (iu < VW) & (iv >= 0) & (iv < VH); vis[iv[ok], iu[ok]] = col
            for r in rings:
                p = np.round((r - wlo) / vpx).astype(np.int32); p[:, 1] = VH - 1 - p[:, 1]
                cv2.polylines(vis, [p.reshape(-1, 1, 2)], True, (0, 0, 230), 1)
            lo = np.clip(((camxy.min(0) - 40 - wlo) / vpx).astype(int), 0, None); hi = ((camxy.max(0) + 40 - wlo) / vpx).astype(int)
            crop = vis[max(0, VH - 1 - hi[1]):VH - 1 - lo[1], lo[0]:hi[0]]
            cv2.imwrite(os.path.join(comp, "register_check.png"), crop if crop.size else vis)
            flag = "ok" if ratio > 1.25 else "WEAK"
            print(f"{tag}: {len(m['cameras'])} cams, scale {s:.4f} m/u, yaw {th:.1f}, score {score:.3f}, peak ratio {ratio:.2f} {flag}, "
                  f"cams at x {camxy[:, 0].min():.0f}..{camxy[:, 0].max():.0f} y {camxy[:, 1].min():.0f}..{camxy[:, 1].max():.0f}")


if __name__ == "__main__":
    sys.exit(main())
