# Ground settle pass, run by build_all.py after the site build and the ground-surface cut, before finalize (which
# moves pivots). Fixes what the per-builder ground field cannot see (owner walkthrough 2026-10-05):
#  0. neighbouring walk tops 2 mm..3 cm apart are put on one level and butt-jointed (_flush_slabs);
#  1. one continuous ground (owner msgs 116/121a/126: every 1-2 cm lip read as a separate "platform"): TER_Ground is
#     re-meshed so every walk-top outline (path, paving, stair tread, deck) is a chain of terrain edges; where a top lies
#     within LIP above (or anywhere below) the ground, the terrain under it is removed and the terrain rim is put
#     exactly on the top's edge (flush, no lip, no overlap so no z-fight). Higher tops (real kerbs, plinths, decks)
#     keep the terrain under them, SINK below the top;
#  2. props floating or buried: outdoor site props (benches, bins, lamps, trees, posts...) are moved vertically so
#     no foot floats over the real top below it (paving, stair tread, deck, bank/bed solid or terrain); trees use
#     their origin (trunk foot) and also find a raised bed top above it.
# Returns counts for the build log. Units: metres.
import math

import bmesh
import bpy
from mathutils import Vector

from .conflicts import _boolean
from mathutils.bvhtree import BVHTree

SUPPORT_TYPES = {"path", "roof_plane", "stairs_run", "slab", "steps", "zebra", "paint"}
SUPPORT_WORDS = ("Turf", "Pitch", "Court", "Field", "Track", "Paving", "Landing", "Platform", "Deck", "Slabs", "Floor", "Stair", "Step", "Ramp", "Walkway",
                 "Sidewalk", "Plaza", "Apron", "Porch")
NOT_SUPPORT = ("Roof", "Canopy", "Soffit", "Rail", "Cheek", "Wall", "Kerb", "Curb", "Coping", "Hedge", "Bed",
               "Bank", "Planter")   # walls/kerbs stay solid but are no ground; beds/banks support props only
SNAP_TYPES = {"bench", "bin", "lamp", "lamp_orn", "tree", "box", "floodlight", "bike_rack", "turnstile"}
MOUNTED = ("Plaque", "CCTV", "Bulkhead", "Meter", "Reader", "Terminal", "Motor", "Plate", "Vent", "Sign", "Board",
           "Lintel", "Hoop", "Cabinet", "Hood", "FaceID", "Camera", "board", "Goal")   # fittings on walls/posts: placed by z0, never snapped
BOX_PROPS = ("Post", "Bollard", "Pole", "Workout", "Bin", "SandBox", "Pallet", "ArtBox", "ArtColumn", "Hydrant",
             "Cone", "Stand", "Crate", "Bench", "Table", "Planter_Pot")
SINK = 0.012   # m: terrain kept under a raised top (see 1. above); >= 1 cm keeps the z-fight QA clean
LIP = 0.05     # m: a top up to this far above the ground beside it is laid flush with it (rim raised), see 1.
TOP_NZ = 0.7   # up-facing faces (normal z) form a support's walkable top
LIFT_FAIL = 0.003   # m: a piece that could not be butt-jointed sits this far over its neighbour (z-fight QA: >= 2 mm)
BAND = 1.0     # m: open ground around a flushed rim follows the rim's change, fading to 0 at this distance
WELD = 0.003   # m: z copies of one plan vertex closer than this are one vertex (plane-interpolation noise, not a step)
LIP_SLAB = 0.03   # m: neighbouring walk tops closer than this are one level (step 0); larger differences are real steps
FIXED_WORDS = ("Stair", "Step", "Ramp", "Landing", "Leg", "Grate", "Lawn", "Floor", "Deck", "Gallery", "Bed", "Bank",
               "Porch", "Drain", "Manhole")   # tops step 0 never moves (they carry risers, frames or soil)
BED_WORDS = ("Bed", "Bank", "Planter")   # raised soil solids: props stand on them, the terrain is not clamped to them


def _bvh(objs):
    bm = bmesh.new()
    for o in objs:
        me = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        b2 = bmesh.new()
        b2.from_mesh(me)
        b2.transform(o.matrix_world)
        me2 = bpy.data.meshes.new("_tmp_settle")
        b2.to_mesh(me2)
        b2.free()
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)
        o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def _is_support(o):
    if o.type != "MESH" or o.hide_render or o.name.startswith(("TER_", "CTX_", "REF_", "CAM_")):
        return False
    if "INT_C" in o.name:
        return False
    kt = o.get("koch_type", "")
    if kt == "box":   # boxes are slabs/turf/platforms too: only the free-standing box props are no ground
        if any(w in str(o.get("koch_id", "")) for w in BOX_PROPS):
            return False
    elif kt in SNAP_TYPES or kt in ("planter", "hedge", "hedge_arch", "wall", "fence", "gate_leaf", "pergola", "gazebo"):
        return False
    n = str(o.get("koch_id") or o.name)   # element name only: "GBS_CPlaza_Bench" must not match "Plaza"
    if any(w in n for w in NOT_SUPPORT):
        return False
    return kt in SUPPORT_TYPES or any(w in n for w in SUPPORT_WORDS)


def _down(tree, x, y, z0, reach):
    loc, _n, _i, d = tree.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), reach)
    return None if loc is None else loc.z


def _tops(o):
    """World bmesh of the up-facing faces of o (its walkable top), or None."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z <= TOP_NZ], context="FACES")
    if not bm.faces:
        bm.free()
        return None
    return bm


def _prism(name, top_bm, z0, z1):
    """Closed vertical prism over the plan of a top (z0..z1, m): the cutter of _flush_slabs."""
    bm = top_bm.copy()
    for v in bm.verts:
        v.co.z = z1
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
    for v in [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]:
        v.co.z = z0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(name, me)


def _flush_slabs(sup):
    """Step 0 (owner msgs 116/126): neighbouring walk tops that differ by 2 mm..LIP_SLAB (1 cm stacking against z-fight,
    path top offsets 16-28 mm, paint 7-8 mm over the field) are put on one level and butt-jointed:
     a. levels: tops touching (probes 4 cm outside each rim) form clusters; fixed tops (stairs, landings, ramps, floors,
        grates, beds) and then the largest paving anchor each cluster, every other paving piece is moved vertically
        (whole object) onto its neighbour's level along the cluster tree;
     b. joints: where a piece now lies on a larger one at the same level, the larger one is cut by the piece's plan
        (exact boolean), so the two tops meet edge to edge instead of overlapping (no z-fight, no lip)."""
    import statistics
    pave = [o for o in sup if o.name.startswith("GBS_") and not any(w in o.name for w in FIXED_WORDS)]
    pave_set = {o.name for o in pave}
    tops = {}
    for o in sup:
        bm = _tops(o)
        if bm is not None:
            tops[o.name] = (bm, BVHTree.FromBMesh(bm))
    area = {n: sum(f.calc_area() for f in bm.faces) for n, (bm, _t) in tops.items()}
    # contacts: rim probes of every top onto the other tops
    names = list(tops)
    lo_hi = {}
    for n in names:
        vs = tops[n][0].verts
        lo_hi[n] = (min(v.co.x for v in vs) - 0.1, min(v.co.y for v in vs) - 0.1, max(v.co.x for v in vs) + 0.1,
                    max(v.co.y for v in vs) + 0.1)
    dz = {}   # (a, b) -> [top_a - top_b] at a's rim over b
    for a in names:
        bm_a = tops[a][0]
        ax0, ay0, ax1, ay1 = lo_hi[a]
        near = [b for b in names if b != a and not (lo_hi[b][2] < ax0 or lo_hi[b][0] > ax1 or lo_hi[b][3] < ay0
                                                   or lo_hi[b][1] > ay1)]
        if not near:
            continue
        for f in bm_a.faces:
            for e in f.edges:
                if len(e.link_faces) != 1:
                    continue
                p0, p1 = e.verts[0].co, e.verts[1].co
                L = (p1 - p0).length
                if L < 0.05:
                    continue
                d = (p1 - p0) / L
                out = Vector((d.y, -d.x, 0.0))
                if (f.calc_center_median() - p0).dot(out) > 0:
                    out = -out
                k = max(1, int(L / 0.5))
                for j in range(k):
                    p = p0 + d * ((j + 0.5) * L / k)
                    q = p + out * 0.04
                    for b in near:
                        loc, _n, _i, _d = tops[b][1].ray_cast(Vector((q.x, q.y, p.z + 0.1)), Vector((0, 0, -1)), 0.2)
                        if loc is not None and 0.002 < abs(p.z - loc.z) <= LIP_SLAB:
                            dz.setdefault((a, b), []).append(p.z - loc.z)
    # a. levels along a BFS tree from the fixed tops, then from the largest paving piece of each cluster
    nb = {}
    for (a, b), v in dz.items():
        m = statistics.median(v)
        nb.setdefault(a, {})[b] = m          # top_a - top_b
        nb.setdefault(b, {}).setdefault(a, -m)
    shift, order = {}, []
    seeds = [n for n in nb if n not in pave_set] + sorted((n for n in nb if n in pave_set), key=lambda n: -area[n])
    for s in seeds:
        if s in shift:
            continue
        shift[s] = 0.0
        queue = [s]
        while queue:
            a = queue.pop(0)
            for b, m in sorted(nb[a].items(), key=lambda t: -area[t[0]]):
                if b in shift or b not in pave_set:
                    continue
                shift[b] = shift[a] + m           # b moves up by top_a - top_b (+ a's own move)
                if abs(shift[b]) > LIP_SLAB:
                    shift[b] = 0.0                # a chain drifting past LIP_SLAB is a real step: stop it here
                    continue
                queue.append(b)
                order.append(b)
    moved = 0
    for n, s in shift.items():
        if abs(s) > 1e-4 and n in pave_set:   # the top moves, the bottom stays (a lifted bottom met a parapet top)
            o = bpy.data.objects[n]
            mi = o.matrix_world.inverted()
            n3 = mi.transposed().to_3x3()
            top_v = {i for p in o.data.polygons if (n3 @ p.normal).normalized().z > TOP_NZ for i in p.vertices}
            for i in top_v:
                o.data.vertices[i].co += mi.to_3x3() @ Vector((0.0, 0.0, s))
            o.data.update()
            moved += 1
    bpy.context.view_layer.update()
    for n in list(tops):
        tops[n][0].free()
        bm = _tops(bpy.data.objects[n])
        tops[n] = (bm, BVHTree.FromBMesh(bm))
    # a2. drape: one shift per object matches a pair at its median, but paths that follow the ground with their own
    # sampling still differ by a few mm along a joint. Every top vertex of a smaller piece takes the top of a larger
    # neighbour found at it or 1 cm around it (within LIP_SLAB), smallest pieces first.
    offs = [(0.0, 0.0)] + [(0.01 * math.cos(k * math.pi / 4), 0.01 * math.sin(k * math.pi / 4)) for k in range(8)]
    n_drape = 0
    touched = {n for n, sh in shift.items() if abs(sh) > 1e-4 and n in pave_set}
    for a in sorted((n for n in tops if n in pave_set), key=lambda n: area[n]):
        ax0, ay0, ax1, ay1 = lo_hi[a]
        bigger = [b for b in names if b != a and area[b] > area[a] and not (
            lo_hi[b][2] < ax0 or lo_hi[b][0] > ax1 or lo_hi[b][3] < ay0 or lo_hi[b][1] > ay1)]
        if not bigger:
            continue
        ob = bpy.data.objects[a]
        mw, mi = ob.matrix_world, ob.matrix_world.inverted()
        n3 = mi.transposed().to_3x3()
        me = ob.data
        top_v = {i for p in me.polygons if (n3 @ p.normal).normalized().z > TOP_NZ for i in p.vertices}
        moved_v = 0
        for vi in top_v:
            w = mw @ me.vertices[vi].co
            best = None
            for ox, oy in offs:
                for b in bigger:
                    loc, _n, _i, _d = tops[b][1].ray_cast(Vector((w.x + ox, w.y + oy, w.z + 0.05)), Vector((0, 0, -1)), 0.1)
                    if loc is not None and abs(loc.z - w.z) <= LIP_SLAB and (best is None or abs(loc.z - w.z) < abs(best - w.z)):
                        best = loc.z
            if best is not None and abs(best - w.z) > 1e-4:
                w.z = best
                me.vertices[vi].co = mi @ w
                moved_v += 1
        if moved_v:
            me.update()
            n_drape += moved_v
            touched.add(a)
            tops[a][0].free()
            bm = _tops(ob)
            tops[a] = (bm, BVHTree.FromBMesh(bm))
    # b. joints: the smaller piece cuts the larger one where they now overlap at the same level
    cuts, fails, lifted = 0, [], set()
    done = set()
    for (a, b), v in dz.items():
        pa, pb = (a, b) if area[a] <= area[b] else (b, a)
        if (pa, pb) in done or pb not in pave_set:
            continue
        done.add((pa, pb))
        # overlap? some point of pa's top lies on pb's top (same level after a/a2)
        hit = False
        for f in tops[pa][0].faces:   # centre and points 1 mm inside each corner: a 2 cm overlap strip counts
            c = f.calc_center_median()
            for q in [c] + [v.co + (c - v.co).normalized() * 0.001 for v in f.verts]:
                loc, _n, _i, _d = tops[pb][1].ray_cast(Vector((q.x, q.y, q.z + 0.05)), Vector((0, 0, -1)), 0.1)
                if loc is not None and abs(loc.z - q.z) <= 0.003:
                    hit = True
                    break
            if hit:
                break
        if not hit:
            continue
        ob = bpy.data.objects[pb]
        zlo = min(v.co.z for v in tops[pb][0].verts) - 2.0
        zhi = max(v.co.z for v in tops[pb][0].verts) + 0.5
        cutter = _prism("_tmp_flush_cut", tops[pa][0], zlo, zhi)
        bpy.context.scene.collection.objects.link(cutter)
        me = _boolean(ob, cutter)
        cme = cutter.data
        bpy.data.objects.remove(cutter, do_unlink=True)
        bpy.data.meshes.remove(cme)
        if len(me.polygons) == 0:   # exact boolean failed (crossing paint strips make a non-manifold cutter):
            fails.append(pb)          # the piece stays LIFT_FAIL over the larger one: no flicker, no visible lip
            bpy.data.meshes.remove(me)
            if pa not in lifted:
                bpy.data.objects[pa].location.z += LIFT_FAIL
                lifted.add(pa)
            continue
        old = ob.data
        me.materials.clear()
        for m in old.materials:
            me.materials.append(m)
        ob.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)
        cuts += 1
        tops[pb][0].free()
        bm = _tops(ob) or bmesh.new()
        tops[pb] = (bm, BVHTree.FromBMesh(bm))
    # c. a moved piece now level with a top that is no walk surface (a lightwell parapet, a curb, a pit rim) would
    # z-fight with it: it is cut by that top's plan (the fixed element wins)
    n_fixed_cuts = 0
    for a in sorted(touched):
        ob = bpy.data.objects[a]
        bm_a = tops[a][0]
        hits = set()
        ob.hide_viewport = True
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        for f in bm_a.faces:
            c = f.calc_center_median()
            hit, loc, nor, _i, other, _m = bpy.context.scene.ray_cast(dg, c + Vector((0, 0, 0.003)), Vector((0, 0, -1)), distance=0.006)
            if hit and other.type == "MESH" and other.name not in tops and not other.name.startswith(("TER_", "CTX_")) \
                    and nor.z > TOP_NZ:
                hits.add(other.name)
        ob.hide_viewport = False
        bpy.context.view_layer.update()
        lo = Vector([min(v.co[i] for v in bm_a.verts) for i in range(3)])
        hi = Vector([max(v.co[i] for v in bm_a.verts) for i in range(3)])
        for n in sorted(hits):
            bm_o = _tops(bpy.data.objects[n])
            if bm_o is None:
                continue
            far = [f for f in bm_o.faces if not any(lo.x - 0.1 <= v.co.x <= hi.x + 0.1 and lo.y - 0.1 <= v.co.y <= hi.y + 0.1
                                                     and abs(v.co.z - (lo.z + hi.z) / 2) < 0.5 for v in f.verts)]
            bmesh.ops.delete(bm_o, geom=far, context="FACES")
            if bm_o.faces:
                cutter = _prism("_tmp_flush_cut", bm_o, lo.z - 2.0, hi.z + 0.5)
                bpy.context.scene.collection.objects.link(cutter)
                me = _boolean(ob, cutter)
                cme = cutter.data
                bpy.data.objects.remove(cutter, do_unlink=True)
                bpy.data.meshes.remove(cme)
                if len(me.polygons):
                    old = ob.data
                    me.materials.clear()
                    for m in old.materials:
                        me.materials.append(m)
                    ob.data = me
                    if old.users == 0:
                        bpy.data.meshes.remove(old)
                    n_fixed_cuts += 1
                else:
                    bpy.data.meshes.remove(me)
                    fails.append(f"{a} by {n}")
            bm_o.free()
    for bm, _t in tops.values():
        bm.free()
    return {"fixed_cuts": n_fixed_cuts, "slab_pairs": len({tuple(sorted(k)) for k in dz}), "moved": moved, "draped_verts": n_drape, "cuts": cuts, "cut_failed": fails[:10],
            "shifts_mm": sorted(((n[4:], round(s * 1000, 1)) for n, s in shift.items() if abs(s) > 1e-4),
                                key=lambda t: -abs(t[1]))[:30]}


def _top_outlines(sup):
    """World XY segments outlining every support's walkable top: edges of up-facing faces not shared with another
    up-facing face of the same mesh (slab rims, tread nosings and back edges, ramp sides)."""
    segs = []
    for o in sup:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        bm.normal_update()
        for e in bm.edges:
            if sum(1 for f in e.link_faces if f.normal.z > TOP_NZ) == 1:
                a, b = e.verts[0].co, e.verts[1].co
                if (a.xy - b.xy).length > 1e-3:
                    segs.append(((a.x, a.y), (b.x, b.y)))
        bm.free()
    return segs


def _seat_terrain(ter, sup, walk):
    """Step 1 (see the file header). The terrain is re-triangulated in plan (mathutils.geometry.delaunay_2d_cdt, the
    same constrained Delaunay as build_greybox._conform_hard_edges) with the top outlines as constraint edges; each new
    face keeps the z of the face it came from (exact at old vertices, its plane elsewhere), so the existing hard steps
    (pads, curbs) come back as z jumps and get their vertical faces again. Faces are then classed under their centroid:
    C (a top within LIP above, or below: removed, rim flush), U (a top higher than that: kept, SINK under it), O (open)."""
    import numpy as np
    from mathutils.geometry import delaunay_2d_cdt
    M = ter.matrix_world
    bm = bmesh.new()
    bm.from_mesh(ter.data)
    bm.transform(M)
    bm.normal_update()
    bm.verts.ensure_lookup_table()
    co = np.array([v.co[:] for v in bm.verts])
    faces, fmat, fplane = [], [], []
    for f in bm.faces:
        pa = 0.5 * abs(sum(a.co.x * b.co.y - b.co.x * a.co.y for a, b in zip(f.verts, f.verts[1:] + f.verts[:1])))
        if abs(f.normal.z) < 0.05 or pa < 1e-6:
            continue   # vertical step faces (rebuilt below from the z jumps) and plan slivers (they confuse the CDT)
        ids = [v.index for v in f.verts]
        faces.append(ids if f.normal.z > 0 else ids[::-1])   # the CDT wants CCW faces in plan
        fmat.append(f.material_index)
        c, n = f.calc_center_median(), f.normal
        fplane.append((c.x, c.y, c.z, n.x / n.z, n.y / n.z))
    smooth = any(f.smooth for f in bm.faces)
    bm.free()
    n_in = len(co)
    verts = [Vector((x, y)) for x, y in co[:, :2]]
    edges = []
    for a, b in _top_outlines(sup):
        verts += [Vector(a), Vector(b)]
        edges.append((len(verts) - 2, len(verts) - 1))
    # 5 = valid BMesh faces, regions outside every input face (terrain holes, the grid border) omitted
    vo, _eo, fo, vorig, _eorig, forig = delaunay_2d_cdt(verts, edges, faces, 5, 1e-5, True)
    vxy = np.array([v[:] for v in vo])
    fsets = [set(f) for f in faces]

    def contains(s, x, y):   # even-odd test of the input face s in plan
        ring, inside = faces[s], False
        for a, b in zip(ring, ring[1:] + ring[:1]):
            (x1, y1), (x2, y2) = co[a, :2], co[b, :2]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        return inside
    # z of every face corner: the old vertex of the source face, else the source face's plane. forig lists every
    # input face touching the output face (not only the one it lies in): the source is the one holding its centroid.
    key, xyz, pid, nf, nmat = {}, [], [], [], []   # pid: plan vertex of each z copy
    zcopies = {}   # plan vertex -> [z of its copies]: copies within WELD of each other are one vertex
    for i, f in enumerate(fo):
        if not forig[i]:
            continue
        cxy = vxy[f].mean(0)
        s = next((s for s in forig[i] if contains(s, cxy[0], cxy[1])), forig[i][0])
        cx, cy, cz, gx, gy = fplane[s]
        out = []
        for v in f:
            ov = next((k for k in vorig[v] if k < n_in and k in fsets[s]), None)
            x, y = vxy[v]
            z = float(co[ov, 2]) if ov is not None else cz - gx * (x - cx) - gy * (y - cy)
            zs = zcopies.setdefault(v, [])
            z = next((z0 for z0 in zs if abs(z0 - z) <= WELD), z)
            k = (v, z)
            if k not in key:
                zs.append(z)
                key[k] = len(xyz)
                xyz.append(Vector((x, y, z)))
                pid.append(v)
            out.append(key[k])
        nf.append(out)
        nmat.append(fmat[s])
    # classes from the top under each face centroid
    cen = [sum((xyz[v] for v in f), Vector()) / len(f) for f in nf]
    cls = []
    for c in cen:
        zs = _down(walk, c.x, c.y, c.z + 0.6, 1.1)    # a top within 0.6 above .. 0.5 below the face
        if zs is None:
            cls.append("O")
        elif zs - c.z <= LIP:
            cls.append("C")
        else:   # H: the raised solid reaches down to this face (its bottom within 2 cm): hidden, removed like C
            zb = _down(walk, c.x, c.y, zs - 0.002, zs - c.z + 0.05)
            cls.append("H" if zb is not None and zb <= c.z + 0.02 and zb < zs - 0.01 else "U")
    adj = [[] for _ in xyz]
    for i, f in enumerate(nf):
        for v in f:
            adj[v].append(i)
    # per plan vertex (its z copies together: a hard pad edge on a slab outline gives an inner and an outer copy)
    copies = {}
    for v, p0 in enumerate(pid):
        copies.setdefault(p0, []).append(v)
    n_flush = n_sink = 0
    rim_old = {}   # flushed rim vertex -> its z before
    for cv in copies.values():
        fs_all = [i for v in cv for i in adj[v]]
        kinds = {cls[i] for i in fs_all}
        if kinds <= {"O"}:
            continue
        inner = next((i for i in fs_all if cls[i] == "C"), None)
        if inner is None:
            inner = next(i for i in fs_all if cls[i] in "UH")
        p = xyz[cv[0]]
        d = cen[inner].xy - p.xy   # probe 2 mm inside the face: the rim vertex itself sits on the slab edge
        q = p.xy + d * min(1.0, 0.002 / max(d.length, 1e-9))
        zs = _down(walk, q.x, q.y, cen[inner].z + 0.6, 1.2)
        if zs is None:
            continue
        for v in cv:
            k = {cls[i] for i in adj[v]}
            pv = xyz[v]
            if "C" in kinds and "O" in k:
                if zs - pv.z <= LIP:   # ground up to LIP below the top (or above it) meets the top's edge
                    rim_old[v] = pv.z
                    pv.z = zs
                    n_flush += 1
            elif pv.z > zs - SINK:   # ground poking through a kept raised top goes under it
                pv.z = zs - SINK
                n_sink += 1
    # the rim moved by up to LIP: carry that change into the open ground around it, fading out over BAND, so the old
    # grid vertex a few cm outside a slab edge does not keep its level (a 1-2 cm micro-ramp instead of a lip)
    rim = [(v, xyz[v].z - z0) for v, z0 in rim_old.items() if abs(xyz[v].z - z0) > 1e-4]
    if rim:
        from mathutils.kdtree import KDTree
        kd = KDTree(len(rim))
        for k, (v, _d) in enumerate(rim):
            kd.insert((xyz[v].x, xyz[v].y, 0.0), k)
        kd.balance()
        rim_set = set(rim_old)
        for v, fs in enumerate(adj):
            if v in rim_set or not fs or any(cls[i] != "O" for i in fs):
                continue
            _co, k, d = kd.find((xyz[v].x, xyz[v].y, 0.0))
            if d < BAND:
                xyz[v].z += rim[k][1] * (1.0 - d / BAND)
    # rebuild: kept faces, vertical faces where a shared plan edge has two z, small vertical corner openings closed
    bm = bmesh.new()
    bv = [bm.verts.new(p) for p in xyz]
    emap = {}   # plan edge -> [(copy a, copy b) per kept face]
    for i, f in enumerate(nf):
        if cls[i] in "CH":
            continue
        try:
            bm.faces.new([bv[v] for v in f]).material_index = nmat[i]
        except ValueError:
            continue
        for a, b in zip(f, f[1:] + f[:1]):
            emap.setdefault((min(pid[a], pid[b]), max(pid[a], pid[b])), []).append((a, b))
    n_step = 0
    for uses in emap.values():
        if len(uses) != 2:
            continue
        (a1, b1), (a2, b2) = uses
        if pid[a2] == pid[a1]:   # orient so a2 is the copy of b1's plan vertex, b2 of a1's
            a2, b2 = b2, a2
        if a1 == b2 and b1 == a2:
            continue   # same copies: no jump
        ring = [bv[a1], bv[b1]] + ([bv[a2]] if a2 != b1 else []) + ([bv[b2]] if b2 != a1 else [])
        mid = sum((v.co for v in ring), Vector()) / len(ring)
        near = walk.find_nearest(mid, 0.003)
        if near[0] is not None and abs(near[1].z) < 0.2:
            continue   # a slab or stair side lies in this plane and closes the step: no coplanar twin (z-fight)
        if len(ring) >= 3:
            try:
                bm.faces.new(ring)
                n_step += 1
            except ValueError:
                pass
    filled = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=16)["faces"]
    big = [f for f in filled if (abs(f.normal.z) > 0.05 and f.calc_area() * abs(f.normal.z) > 1e-3)
           or walk.find_nearest(f.calc_center_median(), 0.003)[0] is not None]   # holes and support-closed steps
    bmesh.ops.delete(bm, geom=big, context="FACES_ONLY")   # keep slab-footprint and terrain holes open
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.normal_update()
    bm.transform(M.inverted())
    bm.to_mesh(ter.data)
    bm.free()
    ter.data.update()
    if smooth:
        ter.data.shade_smooth()
        ter.data.set_sharp_from_angle(angle=0.5236)   # 30 deg: steps/curbs crisp, gentle slopes smooth
    return {"outline_segments": len(edges), "faces_removed": cls.count("C"), "faces_hidden": cls.count("H"), "faces_under_raised": cls.count("U"),
            "rim_flush": n_flush, "sunk": n_sink, "step_faces": n_step, "corner_fills": len(filled) - len(big),
            "terrain_faces": len(ter.data.polygons)}


def run():
    ter = bpy.data.objects.get("TER_Ground")
    sup = [o for o in bpy.data.objects if _is_support(o)]
    beds = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and o.name.startswith("GBS_")
            and o.get("koch_type") == "roof_plane" and any(w in str(o.get("koch_id") or o.name) for w in BED_WORDS)]
    out = {"supports": len(sup)}
    out["slabs"] = _flush_slabs(sup)   # 0. neighbouring walk tops on one level, butt-jointed
    walk = _bvh(sup)
    if ter is not None:   # 1. one continuous ground (see the file header)
        out["terrain"] = _seat_terrain(ter, sup, walk)
    # 2. props onto the real surface. Multi-part elements (posts + bars + rungs as separate boxes) move as one
    # group, so bars stay on their posts; wall-mounted fittings never drop.
    ground = _bvh(sup + beds + ([ter] if ter is not None else []))
    bedtop = _bvh(beds) if beds else None   # plants in a raised bed can sit 2 m+ under its top (sloped stair cheeks)
    cand = {}
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render or not o.name.startswith("GBS_") or o.parent is not None:
            continue
        if o.get("koch_type") not in SNAP_TYPES or not str(o.get("koch_gen", "")).startswith("site:SITE_"):
            continue
        if any(w in o.name for w in MOUNTED):
            continue
        if o.get("koch_z0") and not (o.get("koch_type") == "box" and any(w in str(o.get("koch_id", "")) for w in BOX_PROPS)):
            continue   # absolute heights stay; ground-standing box props (posts, workout frames) still settle
        if o.get("koch_type") == "box" and not any(w in str(o.get("koch_id", "")) for w in BOX_PROPS):
            continue   # boxes are also walls, ramps, billboards, cladding: only free-standing props snap
        key = o.name.rsplit("_", 1)[0] if o.get("koch_type") == "box" else o.name
        cand.setdefault(key, []).append(o)
    moved, far, log = 0, [], []
    for key, parts in cand.items():
        if parts[0].get("koch_type") == "tree":   # trees: the origin is the trunk foot (crown verts are no feet)
            a0 = parts[0].location
            zs = _down(ground, a0.x, a0.y, a0.z + 1.0, 3.5)
            if bedtop is not None:
                zb = _down(bedtop, a0.x, a0.y, a0.z + 3.0, 6.5)
                if zb is not None and (zs is None or zb > zs):
                    zs = zb
            dz = None if zs is None else zs - a0.z
        else:   # each foot part (bottom within 10 cm of the group bottom) gets the surface under its bottom vertices;
            # the group moves by the smallest part lift so no foot floats (the others embed slightly). A part whose
            # bottom straddles a step (> 10 cm spread) stands on the median surface, not sunk to the lower one.
            feet = []
            for o in parts:
                vs = [o.matrix_world @ v.co for v in o.data.vertices]
                zmin = min(v.z for v in vs)
                feet.append((zmin, [v for v in vs if v.z < zmin + 0.02]))
            gmin = min(f[0] for f in feet)
            dz = None
            for zmin, vs in feet:
                if zmin > gmin + 0.1:
                    continue   # bars, rungs, heads: carried by the posts
                zs = sorted(z for z in (_down(ground, v.x, v.y, zmin + 1.0, 3.5) for v in vs) if z is not None)
                if not zs:
                    continue
                lift = (zs[len(zs) // 2] if zs[-1] - zs[0] > 0.1 else zs[0]) - zmin
                if dz is None or lift < dz:
                    dz = lift
            if dz is not None:
                dz -= 0.01   # 1 cm into the surface: no hairline gap
        if dz is None or abs(dz) < 0.015:
            continue
        if abs(dz) > 3.0:
            far.append((key, round(dz, 2)))
            continue
        for o in parts:
            o.location.z += dz
            moved += 1
        log.append((key, round(dz, 3)))
    out["props_moved"] = moved
    out["props_far"] = far[:20]
    out["moves"] = sorted(log, key=lambda t: -abs(t[1]))[:40]
    return out
