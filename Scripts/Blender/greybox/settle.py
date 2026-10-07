# Ground settle pass, run by build_all.py after the site build and the ground-surface cut, before finalize (which
# moves pivots). Fixes what the per-builder ground field cannot see (owner walkthrough 2026-10-05):
#  1. terrain showing through walk surfaces: TER_Ground vertices under a path / paving / stair / deck top are put
#     12 mm below that top: flush enough that a slab edge shows no lip (5 cm read as a separate "platform" around every
#     slab, owner 2026-10-07), still clear of z-fighting;
#  2. props floating or buried: outdoor site props (benches, bins, lamps, trees, posts...) are moved vertically so
#     no foot floats over the real top below it (paving, stair tread, deck, bank/bed solid or terrain); trees use
#     their origin (trunk foot) and also find a raised bed top above it.
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
SINK = 0.012   # m: terrain under a walk top (see 1. above); >= 1 cm keeps the z-fight QA clean
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
    # vertex under a top is put SINK below it.
    if ter is not None:
        M, Mi = ter.matrix_world, ter.matrix_world.inverted()
        bm = bmesh.new()
        bm.from_mesh(ter.data)
        bm.transform(M)

        def pokes(pt):
            zs = _down(walk, pt.x, pt.y, pt.z + 0.6, 1.1)    # a top within 0.6 above .. 0.5 below the point
            return zs is not None and pt.z > zs - SINK + 0.002, zs

        n_low = 0
        for it in range(6):
            for v in bm.verts:
                hit, zs = pokes(v.co)
                if hit:
                    v.co.z = zs - SINK
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
