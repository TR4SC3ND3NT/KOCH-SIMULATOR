# Whole-map terrain audit (R1): TER_Ground sampled on a 0.5 m grid against the rest of the scene.
#  1. terrain z (TER BVH) + what covers each point (first scene hit from above) -> visible / covered-by-<object>
#  2. Zevenbergen-Thorne derivatives (3x3 quadratic fit): slope, profile/plan curvature, 8-neighbour Z-jumps
#  3. protected features (never smoothed): hard pad edges (terraces, retaining walls, building pads), carriageway
#     curbs, and every covering object classified by name (stair, ramp, curb, retaining/bed wall, building, path)
#  4. defects on VISIBLE, UNPROTECTED ground: bumps/pits (> 2 cm off the local plane), creases, Z-jumps, over-steep
#     banks; clustered into zones and classified by the protected features around them
#  5. transitions: objects floating over the ground (2-30 cm gap, nothing under or holding them; hung-by-design and
#     under-slab-in-a-building-shell listed apart), terrain poking through up-facing faces, open terrain cracks
#  6. optional baseline (<tag>_grid.npz of an earlier run): changed cells, how many in protected zones
# Outputs: Art/Blender/Audit/<tag>_report.json, <tag>_grid.npz + PNG maps (height, slope, curvature, classes);
# before/after figures and cross-sections: Scripts/Geo/terrain_audit_plots.py.
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/terrain_audit.py -- TAG [BASE_grid.npz]
import json
import math
import os
import re
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SPECS = os.path.join(REPO, "Art", "Blender", "Specs")
OUT = os.path.join(REPO, "Art", "Blender", "Audit")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TAG = argv[0] if argv else "audit"
BASE = argv[1] if len(argv) > 1 else None
X0, X1, Y0, Y1, S = -130.0, 240.0, -150.0, 100.0, 0.5   # campus core + street frontage, 0.5 m
TH_BUMP, TH_CREASE, TH_JUMP, TH_STEEP = 0.02, 0.05, 0.12, 0.45   # m off plane / m per m / m per 0.5 m / slope
CLASS_RULES = [   # (label, regex on object name) for covering geometry; first match wins
    ("stair", r"Steps|Stair(?!Coping)|StairsRun|_Flight"), ("ramp", r"Ramp"), ("curb", r"Curb|Kerb|Edging"),
    ("retaining", r"Retaining|BedWall|Cheek|Coping|Parapet|Wall(?!way)|Plinth|Boulder"),
    ("bed", r"Bed|Planter|Pit|Hedge|Lawn(?!End)"), ("building", r"^GBF_|^GB_BLD|^BLD_|^GB_CTX|Booth|Canopy|Porch"),
    ("path", r"Paving|Path|Walk|Landing|Slab|Deck|Plaza|Court|Pitch|Strip|Road|Crossing"),
    ("prop", r"."),
]


def classify(name):
    for lab, rx in CLASS_RULES:
        if re.search(rx, name):
            return lab
    return "prop"


def load_pads():
    pads = []
    for fn in sorted(os.listdir(SPECS)):
        if fn.endswith(".json"):
            try:
                pads += [dict(p, _spec=fn[:-5]) for p in json.load(open(os.path.join(SPECS, fn))).get("terrain_pads", [])]
            except ValueError:
                pass
    return pads


def in_ring(ring, x, y):
    inside = np.zeros(np.shape(x), bool)
    n = len(ring)
    for i in range(n):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % n]
        inside ^= ((y1 > y) != (y2 > y)) & (x < x1 + (y - y1) * (x2 - x1) / (y2 - y1 if y2 != y1 else 1e-12))
    return inside


def ring_dist(ring, x, y):
    d = np.full(np.shape(x), np.inf)
    n = len(ring)
    for i in range(n):
        a, b = np.array(ring[i], float), np.array(ring[(i + 1) % n], float)
        ab = b - a
        t = np.clip(((x - a[0]) * ab[0] + (y - a[1]) * ab[1]) / max(ab @ ab, 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(x - (a[0] + t * ab[0]), y - (a[1] + t * ab[1])))
    return d


def dilate(m, it):
    for _ in range(it):
        g = m.copy()
        g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
        m = g
    return m


def sample(blend_objects=None):
    """Terrain z and cover (first scene hit from above) on the grid."""
    dg = bpy.context.evaluated_depsgraph_get()
    ter = bpy.data.objects["TER_Ground"]
    tb = BVHTree.FromObject(ter, dg)
    xs = np.arange(X0, X1 + 1e-6, S); ys = np.arange(Y0, Y1 + 1e-6, S)
    nx, ny = len(xs), len(ys)
    Z = np.full((ny, nx), np.nan); CZ = np.full((ny, nx), np.nan); cover = np.full((ny, nx), -1, np.int32)
    names = []
    idx = {}
    scene = bpy.context.scene
    down = Vector((0, 0, -1))
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            h = tb.ray_cast(Vector((x, y, 100.0)), down, 300)
            if h[0] is None:
                continue
            tz = h[0].z
            Z[j, i] = tz
            if j % 2 or i % 2:   # cover on a 1 m lattice (the scene cast is the slow part), filled below
                continue
            hit, loc, nor, fi, ob, _ = scene.ray_cast(dg, Vector((x, y, 100.0)), down)
            if hit and ob is not None and ob.name != "TER_Ground" and loc.z > tz - 0.02 and not ob.name.startswith(("REF_", "CAM_")):
                k = idx.get(ob.name)
                if k is None:
                    k = idx[ob.name] = len(names); names.append(ob.name)
                cover[j, i] = k; CZ[j, i] = loc.z
    # nearest 1 m sample for the in-between 0.5 m nodes
    cover[1::2, :] = cover[0:-1:2, :][: cover[1::2, :].shape[0]]
    cover[:, 1::2] = cover[:, 0:-1:2][:, : cover[:, 1::2].shape[1]]
    return xs, ys, Z, cover, CZ, names


def zt_derivatives(Z, s):
    """Zevenbergen & Thorne (1987) on a 3x3 window: z_x, z_y, z_xx, z_yy, z_xy (edge rows nan)."""
    zx = np.full(Z.shape, np.nan); zy = zx.copy(); zxx = zx.copy(); zyy = zx.copy(); zxy = zx.copy()
    c = Z[1:-1, 1:-1]
    zx[1:-1, 1:-1] = (Z[1:-1, 2:] - Z[1:-1, :-2]) / (2 * s)
    zy[1:-1, 1:-1] = (Z[2:, 1:-1] - Z[:-2, 1:-1]) / (2 * s)
    zxx[1:-1, 1:-1] = (Z[1:-1, 2:] - 2 * c + Z[1:-1, :-2]) / s ** 2
    zyy[1:-1, 1:-1] = (Z[2:, 1:-1] - 2 * c + Z[:-2, 1:-1]) / s ** 2
    zxy[1:-1, 1:-1] = (Z[2:, 2:] - Z[2:, :-2] - Z[:-2, 2:] + Z[:-2, :-2]) / (4 * s ** 2)
    return zx, zy, zxx, zyy, zxy


def label_regions(mask):
    """4-connected components (numpy flood fill, no scipy in Blender)."""
    lab = np.zeros(mask.shape, np.int32)
    n = 0
    todo = np.argwhere(mask)
    for j, i in todo:
        if lab[j, i]:
            continue
        n += 1
        stack = [(j, i)]; lab[j, i] = n
        while stack:
            a, b = stack.pop()
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p, q = a + da, b + db
                if 0 <= p < mask.shape[0] and 0 <= q < mask.shape[1] and mask[p, q] and not lab[p, q]:
                    lab[p, q] = n; stack.append((p, q))
    return lab, n


SUSPENDED = re.compile(r"Rung|_Mesh$|Sign|Win|Glass|Board|Lamp|Crown|Leaf|Canopy|Roof", re.I)   # hung by design


def _world_bvh(o, dg, cache):
    if o.name not in cache:
        me = o.evaluated_get(dg).to_mesh()
        mw = o.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        me.calc_loop_triangles()
        cache[o.name] = BVHTree.FromPolygons(vs, [tuple(t.vertices) for t in me.loop_triangles])
        o.evaluated_get(dg).to_mesh_clear()
    return cache[o.name]


def transitions(dg, enclosed=()):
    """Per object, its BASE faces (down-facing, within 5 cm of the object's lowest point): floating = a 2-30 cm gap to
    the terrain with no other object under the face, touching it (coplanar band on a band) or holding it (an inlay
    inside a paving slab); objects hung by design (rungs, fence mesh, signs, windows, canopies) are reported apart.
    poke = terrain above an up-facing face of the object."""
    ter = bpy.data.objects["TER_Ground"]
    tb = BVHTree.FromObject(ter, dg)
    floating, poking, hung, enc = [], [], [], []
    DOWN, UP = Vector((0, 0, -1)), Vector((0, 0, 1))
    objs = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and len(o.data.vertices)
            and not o.name.startswith(("TER_", "REF_", "CAM_", "TMP_"))]
    boxes = {}
    for o in objs:
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        boxes[o.name] = (min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb),
                         min(v.z for v in bb), max(v.z for v in bb))
    cache = {}
    for o in objs:
        mw = o.matrix_world; rot = mw.to_3x3()
        zmin = boxes[o.name][4]
        worst_p = (0.0, None); cand = []
        polys = list(o.data.polygons)
        for p in polys[::max(1, len(polys) // 3000)]:
            n = (rot @ p.normal).normalized()
            if abs(n.z) < 0.7 or p.area < 0.004:
                continue
            c = mw @ p.center
            h = tb.ray_cast(Vector((c.x, c.y, c.z + 3.0)), DOWN, 8.0)
            if h[0] is None:
                continue
            gap = c.z - h[0].z
            if n.z > 0 and gap < -0.01 and -gap > worst_p[0]:
                worst_p = (-gap, (round(c.x, 2), round(c.y, 2), round(c.z, 2)))
            if n.z < 0 and c.z < zmin + 0.05 and 0.02 < gap < 0.30:
                cand.append((gap, c, h[0].z))
        if worst_p[1]:
            poking.append((o.name, round(worst_p[0], 3), worst_p[1]))
        if not cand:
            continue
        x0, x1, y0, y1, z0, z1 = boxes[o.name]
        nbs = [_world_bvh(q, dg, cache) for q in objs if q is not o and
               boxes[q.name][0] < x1 + 0.3 and boxes[q.name][1] > x0 - 0.3 and boxes[q.name][2] < y1 + 0.3 and
               boxes[q.name][3] > y0 - 0.3 and boxes[q.name][4] < z1 + 0.3 and boxes[q.name][5] > z0 - 0.5]
        worst_f = (0.0, None)
        for gap, c, tz in sorted(cand, key=lambda t: -t[0])[:40]:
            top = c + Vector((0, 0, 0.01))
            held = False
            for t in nbs:
                hd = t.ray_cast(top, DOWN, top.z - tz - 0.004)          # something between the face and the ground
                if hd[0] is not None:
                    held = True; break
                hu = t.ray_cast(c - Vector((0, 0, 0.005)), UP, 5.0)     # inside a neighbour (its face above looks up)
                if hu[0] is not None and hu[1].z > 0.5:
                    held = True; break
            if not held and gap > worst_f[0]:
                worst_f = (gap, (round(c.x, 2), round(c.y, 2), round(c.z, 2)))
        if worst_f[1]:
            c = worst_f[1]
            if o.name.endswith("_Slabs") or any(bool(in_ring(r, c[0], c[1])) for r in enclosed):   # under a slab inside a closed building shell
                enc.append((o.name, round(worst_f[0], 3), c))
            else:
                (hung if SUSPENDED.search(o.name) else floating).append((o.name, round(worst_f[0], 3), c))
    for lst in (floating, poking, hung, enc):
        lst.sort(key=lambda t: -t[1])
    return floating, poking, hung, enc


def terrain_holes(pads_holes):
    """Open boundary edges of TER_Ground that are not on the outer border or an intentional terrain hole."""
    ter = bpy.data.objects["TER_Ground"]
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ter.data)
    bad = []
    for e in bm.edges:
        if e.is_boundary:
            m = (e.verts[0].co + e.verts[1].co) / 2
            if abs(m.x - (-340)) < 0.6 or abs(m.x - 240) < 0.6 or abs(m.y - (-150)) < 0.6 or abs(m.y - 160) < 0.6:
                continue
            if any(bool(in_ring(np.array(r, float), m.x, m.y)) or float(ring_dist(np.array(r, float), m.x, m.y)) < 1.1
                   for r in pads_holes):
                continue
            bad.append((round(m.x, 2), round(m.y, 2), round(m.z, 2)))
    bm.free()
    return bad


def save_png(path, rgb):
    """Minimal PNG writer (Blender image API): rgb (h, w, 3) uint8, row 0 = north."""
    h, w, _ = rgb.shape
    img = bpy.data.images.new("tmp_audit", w, h, alpha=False)
    px = np.ones((h, w, 4), np.float32)
    px[..., :3] = rgb[::-1].astype(np.float32) / 255.0   # Blender images start at the bottom row
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path; img.file_format = "PNG"; img.save()
    bpy.data.images.remove(img)


def colormap(v, lo, hi, stops):
    t = np.clip((v - lo) / (hi - lo), 0, 1)
    out = np.zeros(v.shape + (3,))
    for k in range(3):
        out[..., k] = np.interp(t, np.linspace(0, 1, len(stops)), [s[k] for s in stops])
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    dg = bpy.context.evaluated_depsgraph_get()
    xs, ys, Z, cover, CZ, names = sample()
    X, Y = np.meshgrid(xs, ys)
    pads = load_pads()
    holes = []
    for fn in sorted(os.listdir(SPECS)):
        if fn.endswith(".json"):
            try:
                holes += json.load(open(os.path.join(SPECS, fn))).get("terrain_holes", [])
            except ValueError:
                pass
    ter_spec = json.load(open(os.path.join(REPO, "Art", "Blender", "Data", "terrain.json")))
    # ---- protected masks
    klass = np.array([classify(n) for n in names] + ["-"])
    cov_cls = np.where(cover >= 0, klass[np.clip(cover, 0, None)], "")
    visible = (cover < 0) & ~np.isnan(Z)
    prot = {}
    hard_edge = np.zeros(Z.shape, bool); terrace = np.zeros(Z.shape, bool); bpad = np.zeros(Z.shape, bool)
    soft_edge = np.zeros(Z.shape, bool)
    for p in pads:
        r = np.array(p["ring"], float)
        dist = ring_dist(r, X, Y)
        if float(p.get("blend", 0)) <= 0:
            near = dist < 1.3          # a vertical step: the 5x5 (1 m) analysis window must not straddle it
            hard_edge |= near
            (bpad if "Inside" in str(p.get("name", "")) else terrace).__ior__(near)
        else:
            soft_edge |= dist < 0.8    # a flat/planar pad meeting the slope: its crease is the terrace edge
    road = np.zeros(Z.shape, bool)
    for st in ter_spec["streets"]:
        L = np.array(st["centerline"], float); hw = st["width_m"] / 2
        for a, b in zip(L[:-1], L[1:]):
            ab = b - a; l2 = ab @ ab
            if l2 < 1e-6:
                continue
            t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / l2, 0, 1)
            d = np.hypot(X - a[0] - t * ab[0], Y - a[1] - t * ab[1])
            road |= np.abs(d - hw) < 1.3   # curb = vertical 0.15 m breakline
    prot["terrace_or_retaining_edge"] = terrace
    prot["building_pad_edge"] = bpad
    prot["road_curb"] = road
    for lab in ("stair", "ramp", "curb", "retaining", "bed", "building", "path"):
        prot[lab] = dilate(cov_cls == lab, 2)   # + 1 m around covered footprints (their transitions)
    protected = np.zeros(Z.shape, bool)
    for m in prot.values():
        protected |= m
    # ---- surface analysis
    zx, zy, zxx, zyy, zxy = zt_derivatives(Z, S)
    slope = np.hypot(zx, zy)
    g2 = zx ** 2 + zy ** 2
    with np.errstate(invalid="ignore", divide="ignore"):
        prof = -(zxx * zx ** 2 + 2 * zxy * zx * zy + zyy * zy ** 2) / (g2 * np.sqrt((1 + g2) ** 3))
        plan = -(zxx * zy ** 2 - 2 * zxy * zx * zy + zyy * zx ** 2) / np.sqrt(g2 ** 3)
    prof = np.where(slope > 0.01, prof, 0.0); plan = np.where(slope > 0.01, plan, 0.0)
    lap = zxx + zyy
    # local plane residual over 5x5 (bump/pit), second-difference crease, 8-neighbour jumps
    Zf = np.where(np.isnan(Z), np.nanmean(Z), Z)
    k = 2
    P = np.pad(Zf, k, mode="edge")   # edge-padded (no wrap-around across the map)
    acc = np.zeros(Z.shape); cnt = 0
    for dj in range(-k, k + 1):
        for di in range(-k, k + 1):
            acc += P[k + dj:k + dj + Z.shape[0], k + di:k + di + Z.shape[1]]; cnt += 1
    resid = Zf - acc / cnt          # a plane's mean over a symmetric window equals its centre value
    crease = np.nanmax(np.abs(np.stack([zxx, zyy, 2 * zxy])), axis=0) * S   # slope change over one cell (m/m)
    jump = np.zeros(Z.shape)
    P1 = np.pad(Zf, 1, mode="edge")
    for dj, di in ((0, 1), (1, 0), (1, 1), (1, -1)):
        d = np.abs(P1[1 + dj:1 + dj + Z.shape[0], 1 + di:1 + di + Z.shape[1]] - Zf)
        jump = np.maximum(jump, d)
    free = visible & ~protected & ~dilate(np.isnan(Z), 2)
    free[:3] = free[-3:] = False; free[:, :3] = free[:, -3:] = False
    bump = free & (resid > TH_BUMP); pit = free & (resid < -TH_BUMP)
    kink = free & (crease > TH_CREASE) & ~soft_edge   # creases on a soft pad edge are that terrace's edge
    prot["terrace_edge_soft (creases only)"] = soft_edge
    zjump = free & (jump > TH_JUMP)
    steep = free & (slope > TH_STEEP)
    defect = bump | pit | kink | zjump | steep
    lab, n = label_regions(dilate(defect, 1) & ~dilate(protected, 0) | defect)
    zones = []
    for r in range(1, n + 1):
        m = lab == r
        cells = int((m & defect).sum())
        if cells < 2:
            continue
        jj, ii = np.nonzero(m & defect)
        cx, cy = float(xs[ii].mean()), float(ys[jj].mean())
        ring = dilate(m, 4) & ~m
        nearby = sorted({lb for lb, mm in prot.items() if (mm & ring).any()})
        kinds = [nm for nm, mm in (("bump", bump), ("pit", pit), ("crease", kink), ("zjump", zjump), ("steep", steep)) if (mm & m).any()]
        # classification: a defect beside a protected feature is that feature's transition; else ordinary ground
        cls = ("transition:" + "+".join(nearby)) if nearby else "ordinary_ground"
        zones.append(dict(x=round(cx, 1), y=round(cy, 1), cells=cells, area_m2=cells * S * S, kinds=kinds, near=nearby, cls=cls,
                          max_resid=round(float(np.nanmax(np.abs(np.where(m, resid, 0)))), 3),
                          max_crease=round(float(np.nanmax(np.where(m, crease, 0))), 3),
                          max_jump=round(float(np.nanmax(np.where(m, jump, 0))), 3),
                          max_slope=round(float(np.nanmax(np.where(m, slope, 0))), 3)))
    zones.sort(key=lambda z: -z["cells"] * (z["max_resid"] + z["max_crease"] + z["max_jump"]))
    floating, poking, hung, enc = transitions(dg, [np.array(p["ring"], float) for p in pads if float(p.get("blend", 0)) <= 0
                                                  and ("Inside" in str(p.get("name", "")) or p.get("field") is False)])
    tholes = terrain_holes(holes)
    # pad interiors hold their planes
    pad_dev = []
    from itertools import islice
    for p in pads:
        r = np.array(p["ring"], float)
        m = in_ring(r, X, Y) & ~np.isnan(Z) & (ring_dist(r, X, Y) > 0.6)
        if not m.any():
            continue
        zp = p["z"] + (p["grad"][0] * (X - p["ref"][0]) + p["grad"][1] * (Y - p["ref"][1]) if "grad" in p else 0)
        dev = np.abs(Z - zp)[m]
        # a later pad may own part of it: report the share within 1 cm
        pad_dev.append(dict(pad=p.get("name") or p["_spec"], spec=p["_spec"], blend=p.get("blend", 0),
                            within_1cm=round(float((dev < 0.01).mean()), 3), p95=round(float(np.percentile(dev, 95)), 3)))
    rep = dict(tag=TAG, grid=dict(x=[X0, X1], y=[Y0, Y1], s=S), visible_share=round(float(visible.mean()), 3),
               protected_share=round(float(protected.mean()), 3),
               free_cells=int(free.sum()), defects=dict(bump=int(bump.sum()), pit=int(pit.sum()), crease=int(kink.sum()),
                                                         zjump=int(zjump.sum()), steep=int(steep.sum())),
               zones=zones, floating=floating[:60], poking=poking[:60], hung=hung[:60], enclosed=enc[:60], terrain_holes=tholes[:60], pads=pad_dev,
               stats=dict(max_slope_free=round(float(np.nanmax(np.where(free, slope, 0))), 3),
                          p99_crease_free=round(float(np.nanpercentile(np.where(free, crease, np.nan), 99)), 4),
                          max_abs_resid_free=round(float(np.nanmax(np.abs(np.where(free, resid, 0)))), 3)))
    # ---- baseline comparison
    if BASE:
        base = np.load(BASE) if BASE.endswith(".npz") else None
        if base is not None:
            B = base["Z"]
            dz = Z - B
            rep["delta"] = dict(changed_cells=int((np.abs(dz) > 0.01).sum()), max_abs=round(float(np.nanmax(np.abs(dz))), 3),
                                changed_in_protected=int(((np.abs(dz) > 0.01) & protected).sum()))
            np.save(os.path.join(OUT, TAG + "_dz.npy"), dz)
    np.savez(os.path.join(OUT, TAG + "_grid.npz"), Z=Z, cover=cover, xs=xs, ys=ys, protected=protected, visible=visible,
             defect=defect, slope=slope, crease=crease, resid=resid)
    json.dump(dict(names=names), open(os.path.join(OUT, TAG + "_names.json"), "w"))
    json.dump(rep, open(os.path.join(OUT, TAG + "_report.json"), "w"), indent=1)
    # ---- images (row 0 = north)
    flip = lambda a: a[::-1]
    zc = np.where(np.isnan(Z), np.nanmin(Z), Z)
    hs = np.clip(0.55 + (-zx * 0.7 + zy * 0.7) * 2.5, 0, 1)
    hs = np.nan_to_num(hs, nan=0.5)
    height = colormap(zc, np.nanpercentile(Z, 1), np.nanpercentile(Z, 99), [(40, 80, 160), (60, 170, 110), (230, 220, 120), (200, 110, 60)])
    height = height * (0.45 + 0.55 * hs[..., None])
    cont = (np.floor(zc / 0.25) != np.floor(np.roll(zc, 1, 0) / 0.25)) | (np.floor(zc / 0.25) != np.floor(np.roll(zc, 1, 1) / 0.25))
    height[cont] *= 0.55
    height[cover >= 0] = height[cover >= 0] * 0.55 + 90
    save_png(os.path.join(OUT, TAG + "_height.png"), flip(np.clip(height, 0, 255)).astype(np.uint8))
    sl = colormap(np.nan_to_num(slope), 0, 0.6, [(30, 110, 40), (160, 200, 60), (240, 200, 40), (230, 90, 30), (150, 20, 20)])
    sl[cover >= 0] = sl[cover >= 0] * 0.4 + 120
    save_png(os.path.join(OUT, TAG + "_slope.png"), flip(sl).astype(np.uint8))
    cv = colormap(np.nan_to_num(np.clip(lap, -2, 2)), -2, 2, [(40, 60, 200), (235, 235, 235), (200, 40, 40)])
    cv[cover >= 0] = cv[cover >= 0] * 0.4 + 120
    save_png(os.path.join(OUT, TAG + "_curvature.png"), flip(cv).astype(np.uint8))
    cls_img = np.full(Z.shape + (3,), 225.0)
    palette = {"stair": (220, 60, 200), "ramp": (255, 140, 0), "curb": (240, 220, 0), "retaining": (140, 70, 20),
               "bed": (60, 150, 60), "building": (120, 120, 120), "path": (170, 170, 210), "road_curb": (40, 40, 40),
               "terrace_or_retaining_edge": (0, 160, 230), "building_pad_edge": (90, 90, 90)}
    for lb, col in palette.items():
        if lb in prot:
            cls_img[prot[lb]] = col
    cls_img[defect] = (255, 0, 0)
    save_png(os.path.join(OUT, TAG + "_classes.png"), flip(cls_img).astype(np.uint8))
    print(f"AUDIT {TAG}: visible {rep['visible_share']:.2f}, protected {rep['protected_share']:.2f}, defects {rep['defects']}, "
          f"zones {len(zones)}, floating {len(floating)} (+{len(hung)} hung by design, {len(enc)} enclosed in a building shell), poking {len(poking)}, terrain holes {len(tholes)}")


main()
