# Measuring on the world-aligned photogrammetry mesh (R1, handoff 4a per-element loop step 2): plane sections drawn
# to scale with a metric grid, plus automatic reading of what the elements need:
#   plan:    horizontal section at z (walls at a given height): RANSAC line fit of wall faces -> world lines,
#            printed as point + direction + offset, and a PNG (1 px = --px m) with a 0.1/1 m grid.
#   profile: vertical section along a world line p0 -> p1 (stairs, ramps, kerbs, plinths): (s, z) polyline,
#            horizontal runs (treads/landings/paving) and vertical steps (risers/kerbs) listed with their levels.
# Mesh: PLY/OBJ in campus world metres (Scripts/Blender/import_photogrammetry.py writes world_mesh.ply).
#   facade:  depth map of a wall along p0 -> p1 (u, z grid, value = offset from the wall plane) with the openings
#            read as recessed/empty rectangles -> facade u/z of every window and door, sill/head levels.
# Usage: python mesh_section.py plan --mesh m.ply --z 8.4 --bbox 170,-10,210,20 --out plan.png
#        python mesh_section.py facade --mesh m.ply --p0 173.26,-3.64 --p1 186.05,-4.15 --z 5,21 --out s.png
#        python mesh_section.py profile --mesh m.ply --p0 187.4,-10 --p1 187.2,-1 --band 0.15 --out prof.png
import argparse
import json
import sys

import cv2
import numpy as np
import trimesh


def load(path, bbox=None, zr=None):
    m = trimesh.load(path, force="mesh", process=False)
    if bbox is not None:
        x0, y0, x1, y1 = bbox
        c = m.triangles_center
        keep = (c[:, 0] >= x0) & (c[:, 0] <= x1) & (c[:, 1] >= y0) & (c[:, 1] <= y1)
        if zr is not None:
            keep &= (c[:, 2] >= zr[0]) & (c[:, 2] <= zr[1])
        if not keep.any():
            raise SystemExit(f"no mesh triangles in bbox {bbox} z {zr}: check the world coordinates")
        m = m.submesh([np.nonzero(keep)[0]], append=True)
        if isinstance(m, list):
            m = trimesh.util.concatenate(m)
    return m


def segments(m, origin, normal):
    lines = trimesh.intersections.mesh_plane(m, plane_normal=normal, plane_origin=origin)
    return np.asarray(lines).reshape(-1, 2, 3)


def draw(segs2, lo, hi, px, grid=(0.1, 1.0), labels=()):
    W, H = int((hi[0] - lo[0]) / px) + 1, int((hi[1] - lo[1]) / px) + 1
    img = np.full((H, W, 3), 255, np.uint8)
    for g, col in ((grid[0], (235, 235, 235)), (grid[1], (190, 190, 190))):
        for x in np.arange(np.ceil(lo[0] / g) * g, hi[0], g):
            u = int((x - lo[0]) / px)
            cv2.line(img, (u, 0), (u, H - 1), col, 1)
        for y in np.arange(np.ceil(lo[1] / g) * g, hi[1], g):
            v = int((hi[1] - y) / px)
            cv2.line(img, (0, v), (W - 1, v), col, 1)
    for x in np.arange(np.ceil(lo[0]), hi[0], 1.0):
        cv2.putText(img, f"{x:.0f}", (int((x - lo[0]) / px) + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1)
    for y in np.arange(np.ceil(lo[1]), hi[1], 1.0):
        cv2.putText(img, f"{y:.0f}", (2, int((hi[1] - y) / px) - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1)
    for a, b in segs2:
        pa = (int((a[0] - lo[0]) / px), int((hi[1] - a[1]) / px))
        pb = (int((b[0] - lo[0]) / px), int((hi[1] - b[1]) / px))
        cv2.line(img, pa, pb, (0, 0, 0), 1, cv2.LINE_AA)
    for (x, y), text, col in labels:
        p = (int((x - lo[0]) / px), int((hi[1] - y) / px))
        cv2.circle(img, p, 3, col, -1)
        cv2.putText(img, text, (p[0] + 4, p[1] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1)
    return img


def ransac_lines(P, tol=0.02, min_pts=80, max_lines=30, seed=0):
    """Sequential RANSAC of 2D lines through dense section points (wall faces). Returns [(c, d, n_in, extent)]."""
    rng = np.random.default_rng(seed)
    out, R = [], P.copy()
    while len(R) >= min_pts and len(out) < max_lines:
        best = None
        for _ in range(400):
            i, j = rng.choice(len(R), 2, replace=False)
            d = R[j] - R[i]
            if np.linalg.norm(d) < 0.3:
                continue
            d = d / np.linalg.norm(d)
            nrm = np.array([-d[1], d[0]])
            inl = np.abs((R - R[i]) @ nrm) < tol
            if best is None or inl.sum() > best[0].sum():
                best = (inl, R[i], d)
        if best is None or best[0].sum() < min_pts:
            break
        Q = R[best[0]]
        c = Q.mean(0)
        _, _, vt = np.linalg.svd(Q - c)
        d = vt[0]
        t = (Q - c) @ d
        out.append((c, d, int(len(Q)), (float(t.min()), float(t.max()))))
        R = R[~best[0]]
    return out


def cmd_plan(a):
    bbox = list(map(float, a.bbox.split(",")))
    m = load(a.mesh, bbox, (a.z - 1.0, a.z + 1.0))
    s = segments(m, [0, 0, a.z], [0, 0, 1])
    segs2 = s[:, :, :2]
    P = segs2.reshape(-1, 2)
    # densify along segments so RANSAC sees surface length, not vertex count
    pts = []
    for p, q in segs2:
        n = max(1, int(np.linalg.norm(q - p) / 0.01))
        pts.append(p + (q - p) * np.linspace(0, 1, n + 1)[:, None])
    P = np.concatenate(pts) if pts else np.zeros((0, 2))
    lines = ransac_lines(P, tol=a.tol, min_pts=int(a.min_len / 0.01))
    labels, rep = [], []
    for k, (c, d, n, (t0, t1)) in enumerate(lines):
        ang = (np.degrees(np.arctan2(d[1], d[0])) + 180) % 180
        p0, p1 = c + d * t0, c + d * t1
        rep.append({"id": k, "p0": np.round(p0, 3).tolist(), "p1": np.round(p1, 3).tolist(), "heading_deg": round(float(ang), 3),
                    "length": round(t1 - t0, 3), "support": n})
        labels.append(((c[0], c[1]), f"L{k}", (0, 0, 255)))
    lo, hi = np.array(bbox[:2]), np.array(bbox[2:])
    cv2.imwrite(a.out, draw(segs2, lo, hi, a.px, labels=labels))
    json.dump(rep, open(a.out.rsplit(".", 1)[0] + ".json", "w"), indent=1)
    for r in rep:
        print(json.dumps(r))


def cmd_profile(a):
    p0, p1 = np.array(list(map(float, a.p0.split(",")))), np.array(list(map(float, a.p1.split(","))))
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    nrm = np.array([-d[1], d[0], 0.0])
    x0, x1 = min(p0[0], p1[0]) - 1, max(p0[0], p1[0]) + 1
    y0, y1 = min(p0[1], p1[1]) - 1, max(p0[1], p1[1]) + 1
    m = load(a.mesh, [x0, y0, x1, y1])
    if a.up_only:  # walking surfaces only: under a canopy the top surface would otherwise be its soffit
        up = m.face_normals[:, 2] > 0.8
        m = m.submesh([np.nonzero(up)[0]], append=True)
    L = float(np.linalg.norm(p1 - p0))
    all_sz = []
    for off in np.linspace(-a.band, a.band, a.slices):  # several parallel cuts: median profile resists holes/noise
        o = np.array([p0[0], p0[1], 0.0]) + nrm * off
        s = segments(m, o, nrm)
        sz = []
        for q, r in s:
            for pt in (q, r):
                t = (pt[:2] - p0) @ d
                if -0.2 <= t <= L + 0.2:
                    sz.append((t, pt[2]))
        all_sz.append(np.array(sz))
    # top surface along s: max z per 1 cm bin in each slice, then the median over slices
    bins = np.arange(-0.2, L + 0.2, 0.01)
    tops = []
    for sz in all_sz:
        if not len(sz):
            continue
        idx = np.digitize(sz[:, 0], bins)
        top = np.full(len(bins), np.nan)
        for k in np.unique(idx):
            if 0 < k < len(bins):
                top[k] = sz[idx == k, 1].max()
        tops.append(top)
    prof = np.nanmedian(np.array(tops), 0)
    # read horizontal runs (|slope| < 5 %, length >= min_run) and steps between them
    runs, k = [], 0
    ok = ~np.isnan(prof)
    while k < len(bins) - 1:
        if not ok[k]:
            k += 1
            continue
        j = k
        while j + 1 < len(bins) and ok[j + 1] and abs(prof[j + 1] - prof[k]) < a.flat_tol:
            j += 1
        if (j - k) * 0.01 >= a.min_run:
            runs.append((bins[k], bins[j], float(np.median(prof[k:j + 1]))))
        k = j + 1
    print(f"profile {L:.2f} m, {len(runs)} flat runs (s0, s1, z):")
    prev = None
    for s0, s1, z in runs:
        step = "" if prev is None else f"  step {z - prev:+.3f}"
        print(f"  s {s0:6.2f}..{s1:6.2f}  ({s1 - s0:5.2f} m)  z {z:7.3f}{step}")
        prev = z
    # drawing: s horizontal, z vertical
    zmin, zmax = np.nanmin(prof) - 0.3, np.nanmax(prof) + 0.3
    pts = [(bins[i], prof[i]) for i in range(len(bins)) if ok[i]]
    segs2 = [(np.array(pts[i]), np.array(pts[i + 1])) for i in range(len(pts) - 1) if pts[i + 1][0] - pts[i][0] < 0.05]
    labels = [((s0, z), f"{z:.3f}", (0, 0, 255)) for s0, s1, z in runs]
    img = draw(segs2, np.array([-0.2, zmin]), np.array([L + 0.2, zmax]), a.px, labels=labels)
    cv2.imwrite(a.out, img)
    json.dump({"p0": p0.tolist(), "p1": p1.tolist(), "runs": runs}, open(a.out.rsplit(".", 1)[0] + ".json", "w"), indent=1)


def cmd_facade(a):
    """Depth map of a facade: the mesh surface sampled on a (u, z) grid along the world wall line p0 -> p1, value =
    offset w from the wall plane (+ outward = right of p0->p1, the CCW-ring convention of the specs). Openings are
    read as connected regions recessed by more than --recess (or empty: glass reconstructs as holes) inside the wall.
    Writes <out>.png (colour-coded depth + 0.1/1 m grid), <out>_rgb.png (mesh colours) and <out>.json (openings in
    facade u/z, z in world metres)."""
    p0, p1 = np.array(list(map(float, a.p0.split(",")))), np.array(list(map(float, a.p1.split(","))))
    L = float(np.linalg.norm(p1 - p0))
    d = (p1 - p0) / L
    out_n = np.array([d[1], -d[0]])               # right of travel = outside for a CCW ring
    z0, z1 = map(float, a.z.split(","))
    lo = np.minimum(p0, p1) - 2.0
    hi = np.maximum(p0, p1) + 2.0
    m = load(a.mesh, [lo[0], lo[1], hi[0], hi[1]], (z0 - 0.5, z1 + 0.5))
    n_samples = int(L * (z1 - z0) / a.px ** 2 * 3)
    pts, fi = trimesh.sample.sample_surface(m, n_samples, seed=0)
    col = None
    if hasattr(m.visual, "vertex_colors") and len(m.visual.vertex_colors):
        col = m.visual.vertex_colors[m.faces[fi][:, 0], :3]
    u = (pts[:, :2] - p0) @ d
    w = (pts[:, :2] - p0) @ out_n
    zz = pts[:, 2]
    keep = (u >= 0) & (u <= L) & (zz >= z0) & (zz <= z1) & (w >= -a.back) & (w <= a.front)
    u, w, zz = u[keep], w[keep], zz[keep]
    if col is not None:
        col = col[keep]
    W, H = int(L / a.px) + 1, int((z1 - z0) / a.px) + 1
    iu, iz = (u / a.px).astype(int), ((z1 - zz) / a.px).astype(int)
    order = np.argsort(w)                          # front-most sample wins
    depth = np.full((H, W), np.nan, np.float32)
    depth[iz[order], iu[order]] = w[order]
    rgb = np.zeros((H, W, 3), np.uint8)
    if col is not None:
        rgb[iz[order], iu[order]] = col[order][:, ::-1]
    # wall plane: the dominant depth near w = 0 (robust), then openings = recessed or empty cells inside the wall
    ref = float(np.nanmedian(depth[np.abs(depth) < 0.1])) if np.any(np.abs(depth) < 0.1) else 0.0
    rel = depth - ref
    recess = np.nan_to_num(rel, nan=0.0) < -a.recess
    # empty cells enclosed by data (glass reconstructs as holes) count as openings too: pad with empties, flood the
    # outside from the border, what stays empty is enclosed
    holes = np.pad(np.isnan(rel).astype(np.uint8), 1, constant_values=1)
    cv2.floodFill(holes, None, (0, 0), 0)
    recess |= holes[1:-1, 1:-1] > 0
    recess = cv2.morphologyEx(recess.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(recess, 8)
    openings = []
    for k in range(1, n):
        x, y, bw, bh, area = stats[k]
        if area * a.px ** 2 < a.min_area or bw * a.px < 0.3 or bh * a.px < 0.3:
            continue
        ys, xs = np.nonzero(lab == k)
        uu = np.percentile(xs, [2, 98]) * a.px
        zt = z1 - np.percentile(ys, [2, 98]) * a.px
        fill = area / (bw * bh)
        dep = float(np.nanmedian(rel[lab == k])) if np.any(~np.isnan(rel[lab == k])) else float("nan")
        openings.append({"u0": round(float(uu[0]), 3), "u1": round(float(uu[1]), 3), "z0": round(float(zt[1]), 3),
                         "z1": round(float(zt[0]), 3), "w": round(float(uu[1] - uu[0]), 3), "h": round(float(zt[0] - zt[1]), 3),
                         "rectangularity": round(float(fill), 2), "recess_m": round(dep, 3)})
    openings.sort(key=lambda o: (round(-o["z1"], 0), o["u0"]))
    # drawing: depth colour map (blue = recessed, red = proud), grid, opening boxes
    vis = np.clip((np.nan_to_num(rel, nan=-0.5) + 0.3) / 0.6, 0, 1)
    img = cv2.applyColorMap((vis * 255).astype(np.uint8), cv2.COLORMAP_JET)
    img[np.isnan(rel)] = (40, 40, 40)
    for g, c in ((0.1, (90, 90, 90)), (1.0, (255, 255, 255))):
        for x in np.arange(0, L, g):
            cv2.line(img, (int(x / a.px), 0), (int(x / a.px), 6 if g < 1 else H - 1), c, 1)
        for zg in np.arange(np.ceil(z0), z1, g):
            v = int((z1 - zg) / a.px)
            cv2.line(img, (0, v), (6 if g < 1 else W - 1, v), c, 1)
    for i, o in enumerate(openings):
        cv2.rectangle(img, (int(o["u0"] / a.px), int((z1 - o["z1"]) / a.px)), (int(o["u1"] / a.px), int((z1 - o["z0"]) / a.px)),
                      (255, 255, 255), 1)
        cv2.putText(img, str(i), (int(o["u0"] / a.px) + 3, int((z1 - o["z1"]) / a.px) + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (255, 255, 255), 1)
    base = a.out.rsplit(".", 1)[0]
    cv2.imwrite(a.out, img)
    cv2.imwrite(base + "_rgb.png", rgb)
    np.save(base + "_depth.npy", rel)
    json.dump({"p0": p0.tolist(), "p1": p1.tolist(), "z": [z0, z1], "px": a.px, "wall_ref_w": ref, "openings": openings},
              open(base + ".json", "w"), indent=1)
    print(f"facade {L:.2f} m x {z1 - z0:.2f} m, wall plane at w {ref:+.3f}, {len(openings)} openings")
    for i, o in enumerate(openings):
        print(i, json.dumps(o))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("facade")
    p.add_argument("--mesh", required=True)
    p.add_argument("--p0", required=True, help="wall line start x,y (world)")
    p.add_argument("--p1", required=True, help="wall line end x,y (world); outside = right of p0->p1")
    p.add_argument("--z", required=True, help="z0,z1 world")
    p.add_argument("--px", type=float, default=0.01)
    p.add_argument("--front", type=float, default=0.6, help="m in front of the wall plane kept")
    p.add_argument("--back", type=float, default=0.6, help="m behind the wall plane kept")
    p.add_argument("--recess", type=float, default=0.07, help="m behind the wall plane that counts as an opening")
    p.add_argument("--min-area", type=float, default=0.25, help="m2")
    p.add_argument("--out", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--mesh", required=True)
    p.add_argument("--z", type=float, required=True)
    p.add_argument("--bbox", required=True, help="x0,y0,x1,y1 world metres")
    p.add_argument("--px", type=float, default=0.01)
    p.add_argument("--tol", type=float, default=0.02)
    p.add_argument("--min-len", type=float, default=0.8, help="m of wall face for a line")
    p.add_argument("--out", required=True)
    p = sub.add_parser("profile")
    p.add_argument("--mesh", required=True)
    p.add_argument("--p0", required=True)
    p.add_argument("--p1", required=True)
    p.add_argument("--band", type=float, default=0.1, help="half width of the band of parallel cuts (m)")
    p.add_argument("--slices", type=int, default=7)
    p.add_argument("--px", type=float, default=0.005)
    p.add_argument("--flat-tol", type=float, default=0.012)
    p.add_argument("--min-run", type=float, default=0.12)
    p.add_argument("--up-only", action="store_true", help="only upward-facing faces (treads, landings, paving)")
    p.add_argument("--out", required=True)
    a = ap.parse_args()
    return {"plan": cmd_plan, "profile": cmd_profile, "facade": cmd_facade}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
