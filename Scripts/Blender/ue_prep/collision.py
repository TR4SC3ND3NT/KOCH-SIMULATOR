# Simple-collision generation per unique mesh (ue_prep, inside Blender): exact UBX boxes for boxes and box unions,
# UCX hulls for convex parts, one ramp hull per stair flight, CoACD for non-convex leftovers (coacd_worker.py),
# otherwise complex-as-simple. Works in asset (canonical) space, so every instance shares the result.
# UE naming (FBX, same file as the render mesh, numbered from 00): UBX_/UCX_<RenderMeshName>_NN
# (dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine).
# UBX must be a true rectangular box and breaks under non-uniform scale -> instances always have scale 1 here.
import bmesh
import numpy as np

PRIM_CAP = 32          # max UBX+UCX per mesh from the exact analysis
DECOMP_CAP = 8         # max CoACD hulls
DECOMP_MAX_DIM = 30.0  # m; bigger non-convex meshes (perimeter walls, long gutters) -> complex-as-simple
DECOMP_MAX_FACES = 20000
TINY = 0.10            # m; smaller objects get no collision
GRID_CAP = 200000      # max cells for the orthogonal box decomposition
STAIR_GAP = 0.05       # m; stair parts closer than this belong to the same flight / prims merge candidates
MAX_PARTS = 600        # more loose parts -> straight to decomposition / complex-as-simple
MERGE_RATIO = 1.3      # merged hull volume <= 1.3 x the members' hull volumes

BOX_TRIS = np.array([[0, 2, 1], [1, 2, 3], [4, 5, 6], [5, 7, 6], [0, 1, 4], [1, 5, 4],
                     [2, 6, 3], [3, 6, 7], [0, 4, 2], [2, 4, 6], [1, 3, 5], [3, 7, 5]])


def box_prim(lo, hi):
    c = np.array([[(hi if i & 1 else lo)[0], (hi if i & 2 else lo)[1], (hi if i & 4 else lo)[2]] for i in range(8)])
    return ("UBX", c, BOX_TRIS)


def merged_ids(co, tol=1e4):
    _, vid = np.unique(np.rint(co * tol).astype(np.int64), axis=0, return_inverse=True)
    return vid.reshape(-1)


def loose_parts(g):
    """Face index arrays of connected components (vertices merged at 0.1 mm)."""
    if g.nfaces == 0:
        return []
    vid = merged_ids(g.co)
    lv = vid[g.loop_vert]
    lab = np.arange(vid.max() + 1)
    while True:   # min-label propagation + pointer jumping
        fm = np.minimum.reduceat(lab[lv], g.loop_start)
        new = lab.copy()
        np.minimum.at(new, lv, np.repeat(fm, g.loop_total))
        new = new[new]
        if np.array_equal(new, lab):
            break
        lab = new
    flab = lab[lv[g.loop_start]]
    order = np.argsort(flab, kind="stable")
    cuts = np.nonzero(np.diff(flab[order]))[0] + 1
    return np.split(order, cuts)


def is_closed(g):
    """Every directed edge used once and its reverse once (closed, consistently oriented 2-manifold)."""
    vid = merged_ids(g.co)
    lv = vid[g.loop_vert]
    nxt = np.arange(len(lv)) + 1
    ends = g.loop_start + g.loop_total
    nxt[ends - 1] = g.loop_start
    a, b = lv, lv[nxt]
    n = int(vid.max()) + 1
    fwd = a * n + b
    if len(np.unique(fwd)) != len(fwd):
        return False
    return bool(np.isin(b * n + a, fwd).all())


def hull(co):
    """Convex hull via bmesh -> (verts (n,3), tris (m,3), volume) or None if degenerate."""
    pts = np.unique(np.rint(co * 1e4), axis=0) / 1e4
    if len(pts) < 4:
        return None
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p.tolist())
    try:
        bmesh.ops.convex_hull(bm, input=bm.verts[:])
    except RuntimeError:
        bm.free()
        return None
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    if not bm.faces:
        bm.free()
        return None
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    vol = bm.calc_volume()
    bm.verts.index_update()
    v = np.array([x.co[:] for x in bm.verts])
    t = np.array([[x.index for x in f.verts] for f in bm.faces])
    bm.free()
    return (v, t, abs(vol)) if abs(vol) > 1e-9 else None


def _axis_aligned(g):
    n, area = g.face_normals()
    big = area > 1e-10
    return bool((np.abs(n[big]).max(1) > 1 - 1e-6).all()), n


def ortho_boxes(g, normals, cap):
    """Exact box decomposition of an axis-aligned (orthogonal) closed polyhedron: grid on the unique vertex
    coordinates, cell inside test by +Z ray parity against the horizontal faces (cell centres never touch a grid
    line, so no degenerate hits), then greedy maximal boxes, best of the 6 axis orders."""
    co = g.co
    axes = [np.unique(np.round(co[:, i], 5)) for i in range(3)]
    nx, ny, nz = (len(a) - 1 for a in axes)
    if min(nx, ny, nz) < 1 or nx * ny * nz > GRID_CAP:
        return None
    cx, cy, cz = ((a[:-1] + a[1:]) * 0.5 for a in axes)
    count = np.zeros((nx, ny, nz), np.int32)
    for f in np.nonzero(np.abs(normals[:, 2]) > 0.5)[0]:
        loop = g.loop_vert[g.loop_start[f]:g.loop_start[f] + g.loop_total[f]]
        p = co[loop]
        zf = p[0, 2]
        ix = np.nonzero((cx > p[:, 0].min()) & (cx < p[:, 0].max()))[0]
        iy = np.nonzero((cy > p[:, 1].min()) & (cy < p[:, 1].max()))[0]
        if not len(ix) or not len(iy):
            continue
        px, py = np.meshgrid(cx[ix], cy[iy], indexing="ij")
        ins = np.zeros(px.shape, bool)
        a, b = p, np.roll(p, -1, 0)
        for (ax, ay), (bx, by) in zip(a[:, :2], b[:, :2]):
            if ay == by:
                continue
            cond = (ay > py) != (by > py)
            xint = ax + (py - ay) * (bx - ax) / (by - ay)
            ins ^= cond & (px < xint)
        kz = np.searchsorted(cz, zf)   # cells strictly below the face
        if kz:
            count[np.ix_(ix, iy, np.arange(kz))] += ins[:, :, None]
    inside = (count & 1).astype(bool)
    best = None
    perms = [(0, 1, 2), (1, 0, 2), (0, 2, 1), (2, 0, 1), (1, 2, 0), (2, 1, 0)] if inside.size < 20000 else [(0, 1, 2)]
    for perm in perms:
        boxes = _greedy(inside.transpose(perm), cap if best is None else min(cap, len(best)))
        if boxes is None:
            continue
        inv = np.argsort(perm)
        boxes = [(tuple(lo[inv]), tuple(hi[inv])) for lo, hi in ((np.array(b[0]), np.array(b[1])) for b in boxes)]
        if best is None or len(boxes) < len(best):
            best = boxes
    if best is None:
        return None
    out = []
    for lo, hi in best:
        out.append((np.array([axes[i][lo[i]] for i in range(3)]), np.array([axes[i][hi[i]] for i in range(3)])))
    vol = sum(float(np.prod(h - l)) for l, h in out)
    if abs(vol - abs(g.volume())) > 1e-3 * max(vol, 1e-6):
        return None   # not a clean solid (self-intersections / open) -> other strategies
    return out


def _greedy(inside, cap):
    nx, ny, nz = inside.shape
    boxes = []
    free = inside.copy()
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                if not free[i, j, k]:
                    continue
                i2 = i
                while i2 + 1 < nx and free[i2 + 1, j, k]:
                    i2 += 1
                j2 = j
                while j2 + 1 < ny and free[i:i2 + 1, j2 + 1, k].all():
                    j2 += 1
                k2 = k
                while k2 + 1 < nz and free[i:i2 + 1, j:j2 + 1, k2 + 1].all():
                    k2 += 1
                free[i:i2 + 1, j:j2 + 1, k:k2 + 1] = False
                boxes.append(((i, j, k), (i2 + 1, j2 + 1, k2 + 1)))
                if len(boxes) > cap:
                    return None
    return boxes


def _dominant_yaw(g):
    """Area-weighted dominant wall direction mod 90 deg (radians, in (-45, 45]) from the near-vertical faces."""
    n, area = g.face_normals()
    side = (np.abs(n[:, 2]) < 0.1) & (area > 1e-10)
    if not side.any():
        return 0.0
    ang = np.arctan2(n[side, 1], n[side, 0]) * 4.0   # 4x folds the 4 wall directions onto one
    w = area[side]
    return float(np.arctan2((w * np.sin(ang)).sum(), (w * np.cos(ang)).sum()) / 4.0)


def _rz(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def _boxes_aligned(g):
    """Exact boxes for an axis-aligned closed part, or None."""
    aa, normals = _axis_aligned(g)
    if not aa:
        return None
    lo, hi = g.co.min(0), g.co.max(0)
    on_box = np.all((np.abs(g.co - lo) < 1e-5) | (np.abs(g.co - hi) < 1e-5))
    if on_box and abs(abs(g.volume()) - np.prod(hi - lo)) < 1e-6 * max(np.prod(hi - lo), 1e-9):
        return [(lo, hi)]
    return ortho_boxes(g, normals, PRIM_CAP)


def _part_prims(g):
    """Exact primitives for one connected part, or None if it needs decomposition. [] = skip (flat open sheet).
    Boxes: axis-aligned -> UBX; aligned after one yaw (mesh built rotated inside its object) -> rotated UCX boxes."""
    if not is_closed(g):
        h = hull(g.co)
        return [] if h is None else None
    boxes = _boxes_aligned(g)
    if boxes is not None:
        return [box_prim(lo, hi) for lo, hi in boxes]
    t = _dominant_yaw(g)
    if abs(t) > 1e-6:
        r = _rz(t)
        boxes = _boxes_aligned(g.transformed(r.T))
        if boxes is not None:
            return [("UCX", box_prim(lo, hi)[1] @ r.T, BOX_TRIS) for lo, hi in boxes]
    h = hull(g.co)
    if h is None:
        return []
    if abs(g.volume()) >= 0.98 * h[2]:
        return [("UCX", h[0], h[1])]
    return None


def merge_prims(prims, cap, ratio=MERGE_RATIO, gap=STAIR_GAP):
    """Greedy agglomeration of neighbouring convex prims (AABBs within `gap`) into hulls while the merged hull stays
    within `ratio` x the members' hull volumes; cheapest pair first. Returns <= cap prims or None."""
    import heapq
    items = {}
    for i, (pre, v, t) in enumerate(prims):
        h = hull(v)
        items[i] = (pre, v, t, h[2] if h else 0.0, v.min(0) - gap, v.max(0) + gap)
    heap = []

    def push(i, j):
        a, b = items[i], items[j]
        if np.all(a[4] <= b[5]) and np.all(b[4] <= a[5]):
            h = hull(np.vstack([a[1], b[1]]))
            if h is not None:
                cost = h[2] / max(a[3] + b[3], 1e-12)
                if cost <= ratio:
                    heapq.heappush(heap, (cost, i, j, h))
    keys = list(items)
    for x in range(len(keys)):
        for y in range(x + 1, len(keys)):
            push(keys[x], keys[y])
    nxt = len(prims)
    while len(items) > cap and heap:
        cost, i, j, h = heapq.heappop(heap)
        if i not in items or j not in items:
            continue
        del items[i], items[j]
        items[nxt] = ("UCX", h[0], h[1], h[2], h[0].min(0) - gap, h[0].max(0) + gap)
        for k in list(items):
            if k != nxt:
                push(k, nxt)
        nxt += 1
    if len(items) > cap:
        return None
    return [(it[0], it[1], it[2]) for _, it in sorted(items.items())]


def _clusters(g, parts, gap):
    """Vertex sets of part groups whose AABBs are within `gap` (one stair flight may be separate step boxes)."""
    pts = [g.subset(p).co for p in parts]
    box = [(c.min(0) - gap, c.max(0) + gap) for c in pts]
    lab = list(range(len(parts)))

    def root(i):
        while lab[i] != i:
            lab[i] = lab[lab[i]]
            i = lab[i]
        return i
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            if np.all(box[i][0] <= box[j][1]) and np.all(box[j][0] <= box[i][1]):
                lab[root(i)] = root(j)
    groups = {}
    for i, c in enumerate(pts):
        groups.setdefault(root(i), []).append(c)
    return [np.concatenate(v) for _, v in sorted(groups.items())]


def classify(g, none_reason="", stairs=False, force_complex=False):
    """-> (kind, prims, info). kind: none | boxes | convex | stairs | decomp (prims filled later) | complex_as_simple.
    prims: list of (prefix 'UBX'|'UCX', verts (n,3) m, tris (m,3))."""
    dims = np.ptp(g.co, 0)
    if none_reason:
        return "none", [], {"reason": none_reason}
    if dims.max() < TINY:
        return "none", [], {"reason": "tiny"}
    if force_complex:
        return "complex_as_simple", [], {"reason": "collision_only"}
    parts = loose_parts(g)
    if stairs:
        hulls = [h for h in (hull(c) for c in _clusters(g, parts, STAIR_GAP)) if h is not None]
        if hulls and len(hulls) <= PRIM_CAP:   # hull of a straight flight = ramp through the nosings
            fill = sum(h[2] for h in hulls) / max(abs(g.volume()), 1e-9)
            return "stairs", [("UCX", h[0], h[1]) for h in hulls], {"flights": len(hulls), "fill": round(fill, 3)}
    prims = []
    ok = len(parts) <= MAX_PARTS
    for p in parts if ok else []:
        r = _part_prims(g.subset(p))
        if r is None:
            ok = False
            break
        prims += r
    info = {"parts": len(parts)}
    if ok and len(prims) > PRIM_CAP:   # many small convex parts (tiles, curb segments): merge neighbours
        merged = merge_prims(prims, PRIM_CAP)
        ok = merged is not None
        info["merged_from"] = len(prims)
        prims = merged or []
    if ok and prims:
        return ("boxes" if all(p[0] == "UBX" for p in prims) else "convex"), prims, info
    if ok and not prims:
        return "none", [], {"reason": "open_or_flat"}
    if dims.max() > DECOMP_MAX_DIM or g.nfaces > DECOMP_MAX_FACES:
        return "complex_as_simple", [], {"reason": "large_nonconvex"}
    return "decomp", [], {"parts": len(parts)}


def tri_soup(g):
    t, _ = g.tris()
    return g.co, t
