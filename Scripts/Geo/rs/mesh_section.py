# Measuring on the world-aligned photogrammetry mesh (R1, handoff 4a per-element loop step 2): plane sections drawn
# to scale with a metric grid, plus automatic reading of what the elements need:
#   plan:    horizontal section at z (walls at a given height): RANSAC line fit of wall faces -> world lines,
#            printed as point + direction + offset, and a PNG (1 px = --px m) with a 0.1/1 m grid.
#   profile: vertical section along a world line p0 -> p1 (stairs, ramps, kerbs, plinths): (s, z) polyline,
#            horizontal runs (treads/landings/paving) and vertical steps (risers/kerbs) listed with their levels.
# Mesh: PLY/OBJ in campus world metres (Scripts/Blender/import_photogrammetry.py writes world_mesh.ply).
# Usage: python mesh_section.py plan --mesh m.ply --z 8.4 --bbox 170,-10,210,20 --out plan.png
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
        m = m.submesh([np.nonzero(keep)[0]], append=True)
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


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
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
    p.add_argument("--out", required=True)
    a = ap.parse_args()
    return {"plan": cmd_plan, "profile": cmd_profile}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
