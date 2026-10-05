# Ground settle pass, run by build_all.py after the site build and the ground-surface cut, before finalize (which
# moves pivots). Fixes what the per-builder ground field cannot see (owner walkthrough 2026-10-05):
#  1. terrain showing through walk surfaces: TER_Ground vertices under a path / paving / stair / deck top are put
#     5 cm below that top (the slab sides hide the step);
#  2. props floating or buried: outdoor site props (benches, bins, lamps, trees, posts...) are moved vertically so
#     their anchor (object origin = the ground z the builder used, + z_rel for boxes) sits on the real top below
#     them (paving, stair tread, deck, bank/bed solid or terrain).
# Returns counts for the build log. Units: metres.
import bmesh
import bpy
from mathutils import Vector
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


def run():
    ter = bpy.data.objects.get("TER_Ground")
    sup = [o for o in bpy.data.objects if _is_support(o)]
    beds = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and o.name.startswith("GBS_")
            and o.get("koch_type") == "roof_plane" and any(w in str(o.get("koch_id") or o.name) for w in BED_WORDS)]
    out = {"supports": len(sup)}
    walk = _bvh(sup)
    # 1. terrain clamp. The terrain grid is ~1 m: a face can rise over a narrow stair or path between vertices that
    # lie outside it, so faces whose interior pokes through a top are split (up to 5 halvings, ~3 cm) and every
    # vertex under a top is put 5 cm below it.
    if ter is not None:
        M, Mi = ter.matrix_world, ter.matrix_world.inverted()
        bm = bmesh.new()
        bm.from_mesh(ter.data)
        bm.transform(M)

        def pokes(pt):
            zs = _down(walk, pt.x, pt.y, pt.z + 0.6, 1.1)    # a top within 0.6 above .. 0.5 below the point
            return zs is not None and pt.z > zs - 0.03, zs

        n_low = 0
        for it in range(6):
            for v in bm.verts:
                hit, zs = pokes(v.co)
                if hit:
                    v.co.z = zs - 0.05
                    n_low += 1
            if it == 5:
                break
            mark = set()
            for f in bm.faces:
                c = f.calc_center_median()
                pts = [c] + [c.lerp(v.co, 0.6) for v in f.verts] + [(e.verts[0].co + e.verts[1].co) / 2 for e in f.edges]
                if any(pokes(p)[0] for p in pts):
                    mark.update(f.edges)
            if not mark:
                break
            bmesh.ops.subdivide_edges(bm, edges=list(mark), cuts=1, use_grid_fill=True)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        bm.transform(Mi)
        bm.to_mesh(ter.data)
        bm.free()
        ter.data.update()
        out["terrain_lowered"] = n_low
        out["terrain_faces"] = len(ter.data.polygons)
    # 2. props onto the real surface. Multi-part elements (posts + bars + rungs as separate boxes) move as one
    # group by the dz of their lowest part, so bars stay on their posts; wall-mounted fittings never drop.
    ground = _bvh(sup + beds + ([ter] if ter is not None else []))
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
        a = o.location.copy()
        a.z -= float(o.get("koch_zrel", 0.0))
        if o.get("koch_type") in ("bench", "bin", "box", "bike_rack"):   # no bury: the real foot is the lowest vertex
            a.z = min((o.matrix_world @ v.co).z for v in o.data.vertices) + 0.01
        cand.setdefault(key, []).append((o, a))
    moved, far, log = 0, [], []
    for key, parts in cand.items():
        o0, a0 = min(parts, key=lambda t: t[1].z)        # the part standing on the ground
        zs = _down(ground, a0.x, a0.y, a0.z + 1.0, 3.5)
        if zs is None:
            continue
        dz = zs - a0.z
        if abs(dz) < 0.015:
            continue
        if abs(dz) > 3.0:
            far.append((key, round(dz, 2)))
            continue
        for o, _a in parts:
            o.location.z += dz
            moved += 1
        log.append((key, round(dz, 3)))
    out["props_moved"] = moved
    out["props_far"] = far[:20]
    out["moves"] = sorted(log, key=lambda t: -abs(t[1]))[:40]
    return out
