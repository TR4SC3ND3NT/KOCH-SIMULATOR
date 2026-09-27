# Metric world frame for the RealityScan site mesh (R1 photogrammetry, handoff sections 2.4 and 3).
#   level:  up vector from the mesh itself (area-weighted normals of the near-vertical faces are orthogonal to up;
#           seeded by the phone cameras' image-up axes), then a top-down orthophoto + height map of the levelled mesh
#           for picking plan points (<out>/plan_rgb.png, plan_z.npy, level.json).
#   fit:    similarity mesh -> world (scale, R, t) from picked plan correspondences (pixel in plan_rgb.png <-> world XY,
#           e.g. the handoff control corners), refined by ICP of the mesh wall points against the building-spec walls
#           (Art/Blender/Specs/BLD_*.json rings in world XY); z offset from a known level (C FFL 6.40, plaza 5.35).
#           Writes <out>/align.json {scale, R, t} (world = scale * R @ x + t), the format sfm_overlay.py reads.
#   apply:  the mesh in world metres as a binary PLY (for mesh_section.py and the Blender reference import).
# Usage: python rs_world.py level --mesh mesh.obj --model model.json --out dir [--px 0.02]
#        python rs_world.py fit --out dir --pairs pairs.json [--specs Art/Blender/Specs]
#        python rs_world.py apply --mesh mesh.obj --align dir/align.json --out world_mesh.ply
import argparse
import glob
import json
import math
import os
import sys

import cv2
import numpy as np
import open3d as o3d


def load_mesh(path):
    m = o3d.io.read_triangle_mesh(path, enable_post_processing=False)
    V = np.asarray(m.vertices)
    F = np.asarray(m.triangles)
    C = np.asarray(m.vertex_colors) if m.has_vertex_colors() else np.full_like(V, 0.6)
    return V, F, C


def tri_normals(V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-12)[:, None], a / 2


def camera_up(model):
    """Mean world direction of the image-up axis (-Y of an OpenCV camera) over all cameras."""
    ups = [np.array(c["R"]).T @ np.array([0.0, -1.0, 0.0]) for c in model["cameras"]]
    u = np.mean(ups, 0)
    return u / np.linalg.norm(u)


def refine_up(n, a, up, iters=6):
    """Up = least-area-weighted-variance direction of the near-vertical faces' normals (walls, kerb faces, posts)."""
    for tol in np.linspace(0.35, 0.12, iters):
        wall = np.abs(n @ up) < tol
        N, A = n[wall], a[wall]
        S = (N * A[:, None]).T @ N
        w, vec = np.linalg.eigh(S)
        u = vec[:, 0]
        up = u if u @ up > 0 else -u
    ground = (n @ up) > 0.97
    return up, wall.sum(), ground.sum()


def rot_to_z(up):
    """Rotation matrix taking `up` to +Z (Rodrigues)."""
    z = np.array([0.0, 0.0, 1.0])
    v, c = np.cross(up, z), float(up @ z)
    if np.linalg.norm(v) < 1e-12:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1 / (1 + c))


def ortho(V, F, C, px):
    """Top-down z-buffer render (max z per pixel) of the levelled mesh: colour + height, by rasterising
    vertices densely (face centroids + vertices); good enough for plan picking at a few cm/px."""
    P = np.concatenate([V, V[F].mean(1)])
    col = np.concatenate([C, C[F].mean(1)])
    lo, hi = np.percentile(P[:, :2], 0.2, 0), np.percentile(P[:, :2], 99.8, 0)
    W, H = int((hi[0] - lo[0]) / px) + 1, int((hi[1] - lo[1]) / px) + 1
    ix = ((P[:, 0] - lo[0]) / px).astype(int)
    iy = ((hi[1] - P[:, 1]) / px).astype(int)
    ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
    ix, iy, z, col = ix[ok], iy[ok], P[ok, 2], col[ok]
    order = np.argsort(z)  # later (higher) writes win
    zimg = np.full((H, W), np.nan, np.float32)
    rgb = np.zeros((H, W, 3), np.uint8)
    zimg[iy[order], ix[order]] = z[order]
    rgb[iy[order], ix[order]] = (col[order][:, ::-1] * 255).astype(np.uint8)
    return rgb, zimg, lo, hi


def cmd_level(a):
    V, F, C = load_mesh(a.mesh)
    model = json.load(open(a.model))
    n, ar = tri_normals(V, F)
    up0 = camera_up(model)
    up, nw, ng = refine_up(n, ar, up0)
    R = rot_to_z(up)
    L = V @ R.T
    ang = math.degrees(math.acos(max(-1.0, min(1.0, float(up @ up0)))))
    print(f"up {np.round(up, 5)} ({ang:.2f} deg from camera up), {nw} wall / {ng} ground faces")
    ext = np.percentile(L[:, :2], 99.8, 0) - np.percentile(L[:, :2], 0.2, 0)
    px = a.px or float(max(ext) / 8000)
    rgb, zimg, lo, hi = ortho(L, F, C, px)
    os.makedirs(a.out, exist_ok=True)
    cv2.imwrite(os.path.join(a.out, "plan_rgb.png"), rgb)
    np.save(os.path.join(a.out, "plan_z.npy"), zimg)
    json.dump({"R_level": R.tolist(), "up": up.tolist(), "px": px, "lo": lo.tolist(), "hi": hi.tolist(),
               "size": [rgb.shape[1], rgb.shape[0]], "mesh": os.path.abspath(a.mesh)},
              open(os.path.join(a.out, "level.json"), "w"), indent=1)
    print(f"plan {rgb.shape[1]}x{rgb.shape[0]} px at {px:.4g} mesh units/px -> {a.out}")


def spec_walls(specs):
    """World XY wall polylines (closed rings) from the building specs: world = anchor + rot(x_dir) @ ring."""
    out = {}
    for f in sorted(glob.glob(os.path.join(specs, "BLD_*.json"))):
        s = json.load(open(f, encoding="utf-8"))
        if "anchor" not in s or "ring" not in s:
            continue
        (ox, oy), (dx, dy) = s["anchor"]["world_xy"], s["anchor"]["x_dir"]
        k = math.hypot(dx, dy)
        dx, dy = dx / k, dy / k
        out[s["id"]] = np.array([[ox + dx * x - dy * y, oy + dy * x + dx * y] for x, y in s["ring"]])
    return out


def umeyama2(A, B, with_scale=True):
    """Similarity B ~ s R A + t in 2D (Umeyama 1991)."""
    ma, mb = A.mean(0), B.mean(0)
    A0, B0 = A - ma, B - mb
    U, S, Vt = np.linalg.svd(B0.T @ A0 / len(A))
    D = np.diag([1.0, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    s = float((S * np.diag(D)).sum() / (A0 ** 2).sum() * len(A)) if with_scale else 1.0
    return s, R, mb - s * R @ ma


def seg_dist(P, rings):
    """Distance from points P (n,2) to the nearest wall segment of any ring, and the closest points."""
    best = np.full(len(P), np.inf)
    cp = np.zeros_like(P)
    for ring in rings:
        for p, q in zip(ring, np.roll(ring, -1, 0)):
            d = q - p
            t = np.clip(((P - p) @ d) / max(d @ d, 1e-12), 0, 1)
            c = p + t[:, None] * d
            dist = np.linalg.norm(P - c, axis=1)
            m = dist < best
            best[m], cp[m] = dist[m], c[m]
    return best, cp


def cmd_fit(a):
    lv = json.load(open(os.path.join(a.out, "level.json")))
    pairs = json.load(open(a.pairs))
    px, lo, hi = lv["px"], np.array(lv["lo"]), np.array(lv["hi"])
    # plan pixel -> levelled mesh XY
    A = np.array([[lo[0] + u * px, hi[1] - v * px] for u, v in (p["px"] for p in pairs["points"])])
    B = np.array([p["world"] for p in pairs["points"]], float)
    s, R2, t2 = umeyama2(A, B)
    res = np.linalg.norm((s * (R2 @ A.T)).T + t2 - B, axis=1)
    print(f"pairs: scale {s:.5f} m/unit, rotation {math.degrees(math.atan2(R2[1, 0], R2[0, 0])):.3f} deg, "
          f"residuals {np.round(res, 2)} m")
    if a.icp:
        V, F, _ = load_mesh(lv["mesh"])
        L = V @ np.array(lv["R_level"]).T
        n, ar = tri_normals(L, F)
        wall = np.abs(n[:, 2]) < 0.1
        cen = L[F[wall]].mean(1)
        zmin = np.percentile(L[:, 2], 2)
        keep = cen[:, 2] > zmin + a.icp_zmin / s  # wall faces above kerbs/plinths only
        P = cen[keep, :2]
        if len(P) > 400000:
            P = P[np.random.default_rng(0).choice(len(P), 400000, replace=False)]
        rings = list(spec_walls(a.specs).values())
        for it in range(a.icp_iters):
            W = (s * (R2 @ P.T)).T + t2
            d, cp = seg_dist(W, rings)
            m = d < a.icp_max
            s_new, R_new, t_new = umeyama2(P[m], cp[m], with_scale=not a.fix_scale)
            s, R2, t2 = (s if a.fix_scale else s_new), R_new, t_new
            print(f"icp {it}: {m.sum()} wall pts within {a.icp_max} m, median {np.median(d[m]):.3f} m, scale {s:.5f}")
    # 3D similarity: world = s * Rz(R2) @ (R_level @ x) + t; z offset from a known level
    R3 = np.eye(3)
    R3[:2, :2] = R2
    Rw = R3 @ np.array(lv["R_level"])
    tz = 0.0
    if "z_ref" in pairs:  # {"px": [u, v], "z": 6.40}: a picked plan pixel on a surface of known world z
        u, v = pairs["z_ref"]["px"]
        zl = float(np.load(os.path.join(a.out, "plan_z.npy"))[int(v), int(u)])
        tz = pairs["z_ref"]["z"] - s * zl
    t = np.array([t2[0], t2[1], tz])
    json.dump({"scale": s, "R": Rw.tolist(), "t": t.tolist(), "rms_m": float(np.sqrt(np.mean(res ** 2))),
               "note": "RealityScan grid -> campus world (X east, Y north, Z = ASL - 800), rs_world.py fit"},
              open(os.path.join(a.out, "align.json"), "w"), indent=1)
    print("align.json written", os.path.join(a.out, "align.json"))


def world_walls(specs, footprints=None):
    """World XY wall rings: building specs (walls) + phase-1 footprints (buildings, context blocks, canopies)."""
    rings = list(spec_walls(specs).values())
    if footprints and os.path.exists(footprints):
        for it in json.load(open(footprints, encoding="utf-8"))["items"]:
            if it.get("kind") in ("building", "context", "canopy", "gazebo") and len(it.get("ring", [])) >= 3:
                rings.append(np.array(it["ring"], float))
    return rings


def raster_lines(rings, lo, px, shape, width=2):
    img = np.zeros(shape, np.float32)
    for r in rings:
        pts = np.round((r - lo) / px).astype(np.int32)
        pts[:, 1] = shape[0] - 1 - pts[:, 1]
        cv2.polylines(img, [pts.reshape(-1, 1, 2)], True, 1.0, width)
    return img


def cmd_register(a):
    """Global 2D search mesh -> world: wall points of the levelled mesh vs rasterised world walls, brute force over
    rotation and scale, translation from the FFT cross-correlation peak; then ICP (cmd_fit machinery)."""
    lv = json.load(open(os.path.join(a.out, "level.json")))
    V, F, _ = load_mesh(lv["mesh"])
    L = V @ np.array(lv["R_level"]).T
    n, ar = tri_normals(L, F)
    wall = (np.abs(n[:, 2]) < 0.1) & (ar > np.percentile(ar, 20))
    cen = L[F[wall]].mean(1)
    zg = np.percentile(L[:, 2], 5)
    P = cen[:, :2]
    rng = np.random.default_rng(0)
    if len(P) > a.max_pts:
        P = P[rng.choice(len(P), a.max_pts, replace=False)]
    pc = P.mean(0)
    P = P - pc
    rings = world_walls(a.specs, a.footprints)
    allw = np.concatenate(rings)
    wlo, whi = allw.min(0) - a.margin, allw.max(0) + a.margin
    px = a.px
    H = int(2 ** np.ceil(np.log2((whi[1] - wlo[1]) / px * 1.5)))
    W = int(2 ** np.ceil(np.log2((whi[0] - wlo[0]) / px * 1.5)))
    off = np.array([W - (whi[0] - wlo[0]) / px, H - (whi[1] - wlo[1]) / px]) / 2   # world raster centred in the canvas
    world = raster_lines(rings, wlo - off * px, px, (H, W), width=2)
    world = cv2.GaussianBlur(world, (0, 0), a.blur)
    Fw = np.fft.rfft2(world)
    best = []
    scales = np.geomspace(a.smin, a.smax, a.nscale)
    if a.thetas:  # narrow search around given rotations (e.g. from the dominant wall direction, +k*90)
        ths = np.concatenate([np.arange(t - a.th_span, t + a.th_span + 1e-9, a.dth)
                              for t in map(float, a.thetas.split(","))]) % 360
    else:
        ths = np.arange(0, 360, a.dth)
    for s in scales:
        for th in ths:
            c, si = math.cos(math.radians(th)), math.sin(math.radians(th))
            Q = s * (P @ np.array([[c, si], [-si, c]]))
            iu = np.round(Q[:, 0] / px + W / 2).astype(int)
            iv = np.round(H / 2 - Q[:, 1] / px).astype(int)
            ok = (iu >= 0) & (iu < W) & (iv >= 0) & (iv < H)
            img = np.zeros((H, W), np.float32)
            np.add.at(img, (iv[ok], iu[ok]), 1.0)
            img = np.minimum(img, 3.0)            # dense clutter (trees) must not dominate
            cc = np.fft.irfft2(Fw * np.conj(np.fft.rfft2(img)), s=(H, W))
            k = int(np.argmax(cc))
            best.append((float(cc.flat[k] / max(ok.sum(), 1)), s, th, k // W, k % W))
    best.sort(key=lambda b: -b[0])
    print("top solutions (score, scale m/unit, rotation deg):")
    for b in best[:8]:
        print(f"  {b[0]:.4f}  s {b[1]:.3f}  th {b[2]:.1f}")
    score, s, th, dy, dx = best[0]
    # translation: the mesh raster shifted by (dy, dx) (circular) lines up with the world raster
    dy = dy - H if dy > H / 2 else dy
    dx = dx - W if dx > W / 2 else dx
    c, si = math.cos(math.radians(th)), math.sin(math.radians(th))
    R2 = np.array([[c, -si], [si, c]])
    # canvas pixel (u, v) of world raster <-> world XY: x = wlo_x - off_x*px + u*px; y = wlo_y - off_y*px + (H-1-v)*px
    # mesh point q (centred) is drawn at u = q_x/px + W/2, v = H/2 - q_y/px, and matches the world at u + dx, v + dy
    x0 = wlo[0] - off[0] * px + (W / 2 + dx) * px
    y0 = wlo[1] - off[1] * px + (H - 1 - (H / 2 + dy)) * px
    t2 = np.array([x0, y0]) - s * R2 @ pc          # world_xy = s R2 p + t2 for levelled mesh xy p
    R3 = np.eye(3)
    R3[:2, :2] = R2
    Rw = R3 @ np.array(lv["R_level"])
    json.dump({"scale": float(s), "R": Rw.tolist(), "t": [float(t2[0]), float(t2[1]), 0.0], "score": score,
               "theta_deg": float(th), "top": [list(map(float, b[:3])) for b in best[:8]],
               "note": "rs_world.py register: 2D wall correlation, z offset not set yet"},
              open(os.path.join(a.out, "align_register.json"), "w"), indent=1)
    # verification drawing: world walls red, registered mesh wall points blue (0.25 m/px)
    Q = s * ((P + pc) @ R2.T) + t2
    vpx = 0.25
    vlo, vhi = wlo, whi
    VW, VH = int((vhi[0] - vlo[0]) / vpx) + 1, int((vhi[1] - vlo[1]) / vpx) + 1
    vis = np.full((VH, VW, 3), 255, np.uint8)
    iu = ((Q[:, 0] - vlo[0]) / vpx).astype(int)
    iv = (VH - 1 - (Q[:, 1] - vlo[1]) / vpx).astype(int)
    ok = (iu >= 0) & (iu < VW) & (iv >= 0) & (iv < VH)
    vis[iv[ok], iu[ok]] = (200, 120, 40)
    for r in rings:
        p = np.round((r - vlo) / vpx).astype(np.int32)
        p[:, 1] = VH - 1 - p[:, 1]
        cv2.polylines(vis, [p.reshape(-1, 1, 2)], True, (0, 0, 230), 1)
    cv2.imwrite(os.path.join(a.out, "register_check.png"), vis)
    print(f"best: scale {s:.3f} m/unit, rotation {th:.1f} deg; align_register.json + register_check.png written")


def cmd_apply(a):
    """Mesh in the RealityScan grid -> campus world metres (align.json), binary PLY with vertex colours."""
    al = json.load(open(a.align))
    m = o3d.io.read_triangle_mesh(a.mesh, enable_post_processing=False)
    V = np.asarray(m.vertices)
    W = float(al["scale"]) * (V @ np.array(al["R"]).T) + np.array(al["t"])
    m.vertices = o3d.utility.Vector3dVector(W)
    if m.has_triangle_uvs() and not a.keep_uv:
        m.triangle_uvs = o3d.utility.Vector2dVector(np.zeros((0, 2)))
    o3d.io.write_triangle_mesh(a.out, m, write_ascii=False, compressed=False, write_vertex_normals=False,
                               write_triangle_uvs=a.keep_uv)
    print(f"{a.out}: {len(W)} vertices, bbox {np.round(W.min(0), 2)} .. {np.round(W.max(0), 2)}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("register")
    p.add_argument("--out", required=True)
    p.add_argument("--specs", default=os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs"))
    p.add_argument("--footprints", default=os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender",
                                                        "Data", "footprints.json"))
    p.add_argument("--px", type=float, default=0.5, help="m per pixel of the search rasters")
    p.add_argument("--blur", type=float, default=2.0, help="px sigma: tolerance for the footprint error")
    p.add_argument("--margin", type=float, default=40.0)
    p.add_argument("--smin", type=float, default=5.0)
    p.add_argument("--smax", type=float, default=30.0)
    p.add_argument("--nscale", type=int, default=36)
    p.add_argument("--dth", type=float, default=2.0)
    p.add_argument("--max-pts", type=int, default=200000)
    p.add_argument("--thetas", help="comma list of rotation centres (deg) for a narrow search")
    p.add_argument("--th-span", type=float, default=3.0)
    p = sub.add_parser("apply")
    p.add_argument("--mesh", required=True)
    p.add_argument("--align", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--keep-uv", action="store_true")
    p = sub.add_parser("level")
    p.add_argument("--mesh", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--px", type=float)
    p = sub.add_parser("fit")
    p.add_argument("--out", required=True)
    p.add_argument("--pairs", required=True)
    p.add_argument("--specs", default=os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs"))
    p.add_argument("--icp", action="store_true")
    p.add_argument("--icp-iters", type=int, default=8)
    p.add_argument("--icp-max", type=float, default=0.8, help="m: wall points farther than this are ignored")
    p.add_argument("--icp-zmin", type=float, default=1.0, help="m above the low ground: skip kerbs and plinths")
    p.add_argument("--fix-scale", action="store_true", help="keep the pairs' scale (e.g. set from pavers)")
    a = ap.parse_args()
    return {"level": cmd_level, "fit": cmd_fit, "apply": cmd_apply, "register": cmd_register}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
