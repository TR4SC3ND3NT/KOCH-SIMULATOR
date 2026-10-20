# Z-fight fix pass, run by build_all.py after finalize (R1, owner msg 141, before the UE hand-off). Faces of different
# objects that coincide (< COPLANAR apart) with the same outward normal and overlap flicker. For each such pair the
# plane of the larger object (its faces in that plane, by area) is pushed back along -normal by PUSH; the smaller
# detail (paint, trim, cladding piece, lawn on its bed) stays in front. Only vertices move (topology and manifoldness
# unchanged). TER_Ground never moves; a thin part moves at most a third of its thickness along the normal.
# Why these numbers: UE 5.8 renders reversed-Z float32 depth (near 10 cm): it resolves ~0.01 mm at 100 m and ~0.3 mm
# at 500 m, so only true coincidences flicker. PUSH is an odd 1.3 mm because the builders stack layers at 1/2/3/5 mm
# (a 2 mm push landed planes on the next layer: 44 -> 83 pairs, 2026-10-20); PASSES re-check what a push created.
# Units: metres.
import math
from collections import defaultdict

import numpy as np
from mathutils import Vector

import bpy

PUSH = 0.0013       # m
COPLANAR = 0.0003   # m: coincident for UE depth (see the header)
PASSES = 6   # each pass re-detects; stops when no coincidence is left
MIN_OVERLAP = 1e-3  # m2


def _faces(objs):
    """World plane data of every face: object index, outward normal, centre, area, polygon index, bbox lo/hi."""
    oi, N, C, A, polys, LO, HI = [], [], [], [], [], [], []
    for k, o in enumerate(objs):
        me = o.data
        n = len(me.polygons)
        if not n:
            continue
        mw = np.array(o.matrix_world)
        nm = np.array(o.matrix_world.to_3x3().inverted_safe().transposed())
        ln = np.empty(n * 3); me.polygons.foreach_get("normal", ln)
        lc = np.empty(n * 3); me.polygons.foreach_get("center", lc)
        la = np.empty(n); me.polygons.foreach_get("area", la)
        ls = np.empty(n, np.int64); me.polygons.foreach_get("loop_start", ls)
        lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get("vertex_index", lv)
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
        W = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        LW = W[lv]
        LO.append(np.minimum.reduceat(LW, ls, axis=0)); HI.append(np.maximum.reduceat(LW, ls, axis=0))
        wn = ln.reshape(-1, 3) @ nm.T
        wn = wn / np.maximum(np.linalg.norm(wn, axis=1, keepdims=True), 1e-12)
        wc = lc.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        det = abs(np.linalg.det(mw[:3, :3]))
        oi.append(np.full(n, k)); N.append(wn); C.append(wc); A.append(la * det ** (2 / 3))
        polys.append(np.arange(n))
    cat = np.concatenate
    return cat(oi), cat(N), cat(C), cat(A), cat(polys), cat(LO), cat(HI)


def _clip(subj, clipp):
    """Sutherland-Hodgman: convex polygon clipped by a convex CCW polygon (2D)."""
    out = subj
    for i in range(len(clipp)):
        if not out:
            break
        a, b = clipp[i - 1], clipp[i]
        inp, out = out, []
        side = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-12

        def cut(p, q):
            dx, dy = b[0] - a[0], b[1] - a[1]
            den = (q[0] - p[0]) * dy - (q[1] - p[1]) * dx
            t = ((a[0] - p[0]) * dy - (a[1] - p[1]) * dx) / den if abs(den) > 1e-15 else 0.0
            return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
        s = inp[-1]
        for e in inp:
            if side(e):
                if not side(s):
                    out.append(cut(s, e))
                out.append(e)
            elif side(s):
                out.append(cut(s, e))
            s = e
    return out


def _area2(p):
    return 0.5 * sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))


_TRI = {}   # object name -> {polygon index: [loop-triangle vertex triples]} (Blender's tessellation: concave faces too)


def _tris2d(o, pi, ax):
    """Face pi of o as world triangles projected on the two axes other than ax (CCW)."""
    me, mw = o.data, o.matrix_world
    if o.name not in _TRI:
        me.calc_loop_triangles()
        by = defaultdict(list)
        for t in me.loop_triangles:
            by[t.polygon_index].append(tuple(t.vertices))
        _TRI[o.name] = by
    idx = [k for k in range(3) if k != ax]
    out = []
    for tri in _TRI[o.name][pi]:
        vs = [mw @ me.vertices[i].co for i in tri]
        t = [(v[idx[0]], v[idx[1]]) for v in vs]
        out.append(t if _area2(t) > 0 else t[::-1])
    return out


def _overlap(oa, pa, ob, pb, n):
    ax = int(np.argmax(np.abs(n)))
    total = 0.0
    tb = _tris2d(ob, pb, ax)
    for A in _tris2d(oa, pa, ax):
        for B in tb:
            P = _clip(A, B)
            if len(P) >= 3:
                total += abs(_area2(P))
    return total


def run():
    out = []
    for _ in range(PASSES):
        r = _pass()
        out.append(r)
        if not r["pairs"]:
            break
    return {"passes": [(r["pairs"], r["planes_pushed"]) for r in out], "objects": sum(r["objects"] for r in out),
            "top": out[0]["top"]}


def _pass():
    _TRI.clear()   # geometry moved in the previous pass
    objs = [o for o in bpy.data.objects if o.type == "MESH" and o.data.polygons and not o.hide_render
            and not o.name.startswith(("REF_", "CAM_"))]
    oi, N, C, A, P, LO, HI = _faces(objs)
    keep = A > MIN_OVERLAP
    oi, N, C, A, P, LO, HI = oi[keep], N[keep], C[keep], A[keep], P[keep], LO[keep], HI[keep]
    # canonical plane key: normal flipped to a fixed hemisphere, offset along it in COPLANAR bins
    flip = (N[:, 2] < -1e-6) | ((np.abs(N[:, 2]) <= 1e-6) & ((N[:, 1] < -1e-6) | ((np.abs(N[:, 1]) <= 1e-6) & (N[:, 0] < 0))))
    Nc = np.where(flip[:, None], -N, N)
    D = np.einsum("ij,ij->i", Nc, C)
    key = np.round(Nc, 2)
    bins = defaultdict(list)
    for i, (k, d) in enumerate(zip(map(tuple, key), np.floor(D / COPLANAR).astype(np.int64))):
        bins[(k, d)].append(i)
    plane_area = defaultdict(float)   # (object index, outward normal key, offset mm) -> area in that plane
    for i in range(len(oi)):
        plane_area[(oi[i], tuple(np.round(N[i], 2)), int(round(float(N[i] @ C[i]) * 1000)))] += A[i]
    rep = {}               # plane id (object index, normal key, offset mm) -> (normal, offset) of one of its faces
    adj = defaultdict(set)   # plane id -> plane ids it coincides with and overlaps
    pairs = 0
    for (k, d), ids in bins.items():
        cand = np.array(ids + bins.get((k, d + 1), []))
        if len(np.unique(oi[cand])) < 2:
            continue
        for x, i in enumerate(ids):
            js = cand[x + 1:]
            if not len(js):
                break
            m = ((oi[js] != oi[i]) & (N[js] @ N[i] >= 0.999) & (np.abs(D[js] - D[i]) <= COPLANAR)
                 & np.all(LO[js] <= HI[i] + 0.001, axis=1) & np.all(HI[js] >= LO[i] - 0.001, axis=1))   # bboxes touch
            for j in js[m]:
                if _overlap(objs[oi[i]], P[i], objs[oi[j]], P[j], N[i]) < MIN_OVERLAP:
                    continue
                pairs += 1
                ks = []
                for f in (i, j):
                    kk = (oi[f], tuple(np.round(N[f], 2)), int(round(float(N[f] @ C[f]) * 1000)))
                    rep.setdefault(kk, (Vector(N[f]), float(N[f] @ C[f])))
                    ks.append(kk)
                adj[ks[0]].add(ks[1])
                adj[ks[1]].add(ks[0])
    # levels instead of pairwise pushes (pairs cycled when three planes coincided: a wall, its plinth band and a
    # lightwell cover, 2026-10-20): smallest planes first, each one level behind the deepest smaller plane it overlaps;
    # TER_Ground is fixed at level 0. A wall with 50 trim pieces in its plane goes back one level, not 50.
    level = {kk: 0 for kk in rep if objs[kk[0]].name.startswith("TER_")}
    pushes = {}
    for kk in sorted((kk for kk in rep if kk not in level), key=lambda kk: plane_area[kk]):
        lv = max((level[nb] + 1 for nb in adj[kk] if nb in level), default=0)
        level[kk] = lv
        if not lv:
            continue
        o = objs[kk[0]]
        n, d = rep[kk]
        W = np.array([o.matrix_world @ v.co for v in o.data.vertices])
        ext = float((W @ np.array(n)).max() - (W @ np.array(n)).min())
        push = min(lv * PUSH, ext / 3)   # a thin sheet keeps two thirds of its thickness
        if push >= 0.0005:
            pushes[kk] = (n, d, push)
    moved = defaultdict(int)
    for (k, _nk, _dk), (n, d, push) in pushes.items():
        o = objs[k]
        me, mw = o.data, o.matrix_world
        n3 = mw.to_3x3().inverted_safe().transposed()
        vs = set()
        for p in me.polygons:
            wn = (n3 @ p.normal).normalized()
            if wn.dot(n) > 0.999 and abs(n.dot(mw @ p.center) - d) < 0.0005:
                vs.update(p.vertices)
        delta = mw.to_3x3().inverted_safe() @ (-n * push)
        for v in vs:
            me.vertices[v].co += delta
        me.update()
        moved[o.name] += 1
    return {"pairs": pairs, "planes_pushed": len(pushes), "objects": len(moved),
            "top": sorted(moved, key=lambda n: -moved[n])[:8]}
