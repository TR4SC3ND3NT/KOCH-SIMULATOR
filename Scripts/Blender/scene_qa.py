# Whole-scene production QA of the greybox (R1, before the UE export). Read-only: never saves.
# Mesh hygiene (empty / zero-area / loose / inconsistent winding / inside-out), transforms (negative, unapplied scale,
# far origins), exact duplicates, material slots, orphan data, naming (forbidden real names), per-object support
# (floating props, props buried in the terrain) and a per-building / per-zone inventory of doors, stairs and props.
# Run: blender -b FILE.blend -P Scripts/Blender/scene_qa.py -- OUT.json
import json
import re
import sys
from collections import Counter, defaultdict

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
FORBIDDEN = re.compile(r"ala.?too|\baiu\b|iaau|university|универ", re.I)
PROP = re.compile(r"_(bench|bin|lamp|tree|planter|sign|bike|floodlight|sink|chair|desk|table|cabinet|locker|"
                  r"shelf|stool|piano|board|bed|pot)", re.I)
AREA_EPS = 1e-8

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
rep = defaultdict(list)


def wverts(ob):
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    mw = np.array(ob.matrix_world)
    return co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]


# ------------------------------------------------------------------ collections
def col_tree(col, depth=0, out=None):
    out = [] if out is None else out
    out.append(("  " * depth) + f"{col.name}: {len(col.objects)}")
    for c in col.children:
        col_tree(c, depth + 1, out)
    return out


tree = col_tree(sc.collection)
unlinked = [o.name for o in bpy.data.objects if not o.users_collection]
rep["collections"] = tree
rep["objects_not_in_scene"] = unlinked
root_objs = [o.name for o in sc.collection.objects]
rep["objects_in_scene_root"] = root_objs

# ------------------------------------------------------------------ meshes
meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.users_collection]
seen, geo_hash = {}, defaultdict(list)
for ob in meshes:
    me = ob.data
    nm = ob.name
    if nm.startswith(("REF_", "CAM_")):
        continue
    if not me.polygons:
        rep["empty_mesh"].append(nm)
        continue
    mw = ob.matrix_world
    sx, sy, sz = ob.matrix_world.to_scale()
    det = mw.to_3x3().determinant()
    if det < 0:
        rep["negative_scale"].append(nm)
    if abs(det) < 1e-9:
        rep["degenerate_matrix"].append(nm)
    if max(abs(sx - 1), abs(sy - 1), abs(sz - 1)) > 1e-4:
        rep["unapplied_scale"].append((nm, round(sx, 3), round(sy, 3), round(sz, 3)))
    W = wverts(ob)
    lo, hi = W.min(0), W.max(0)
    if np.abs(W).max() > 3000:
        rep["far_geometry"].append((nm, [round(v, 1) for v in lo]))
    oloc = np.array(mw.translation)
    if np.linalg.norm(oloc - np.clip(oloc, lo, hi)) > 5.0:
        rep["origin_off_object"].append(nm)
    if hi[2] - lo[2] < 1e-6 or hi[0] - lo[0] < 1e-6 or hi[1] - lo[1] < 1e-6:
        rep["flat_zero_volume"].append(nm)
    # exact duplicates: same geometry hash at the same world place
    key = (len(me.vertices), len(me.polygons), tuple(np.round(lo, 3)), tuple(np.round(hi, 3)),
           round(float(W.sum()), 2))
    geo_hash[key].append(nm)
    # slots
    nslot = len(me.materials)
    if nslot == 0:
        rep["no_material"].append(nm)
    else:
        mi = np.empty(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", mi)
        used = set(np.unique(mi).tolist())
        if max(used) >= nslot:
            rep["material_index_out_of_range"].append(nm)
        if any(m is None for m in me.materials):
            rep["empty_slot"].append(nm)
        unused = [me.materials[i].name for i in range(nslot) if i not in used and me.materials[i]]
        if unused:
            rep["unused_slot"].append((nm, unused))
        for m in me.materials:
            if m and not m.name.startswith("M_"):
                rep["non_M_slot"].append((nm, m.name))
    if me.name in seen:
        continue
    seen[me.name] = nm
    if nm.startswith("TER_"):
        continue
    bm = bmesh.new()
    bm.from_mesh(me)
    za = [f for f in bm.faces if f.calc_area() < AREA_EPS]
    if za:
        rep["zero_area_faces"].append((nm, len(za)))
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        rep["loose_verts"].append((nm, len(loose)))
    bad_wind = 0
    for e in bm.edges:
        if len(e.link_loops) == 2 and e.link_loops[0].vert == e.link_loops[1].vert:
            bad_wind += 1
    if bad_wind:
        rep["inconsistent_winding"].append((nm, bad_wind))
    elif all(e.is_manifold for e in bm.edges):
        vol = bm.calc_volume(signed=True) * (1 if det > 0 else -1)
        if vol < -1e-9:
            rep["inside_out"].append((nm, round(vol, 4)))
    bm.free()

rep["exact_duplicates"] = [v for v in geo_hash.values() if len(v) > 1]

# ------------------------------------------------------------------ names / orphans
for o in bpy.data.objects:
    if FORBIDDEN.search(o.name) or FORBIDDEN.search(o.data.name if o.data else ""):
        rep["forbidden_name"].append(o.name)
    if " " in o.name or not o.name.isascii():
        rep["bad_name_chars"].append(o.name)
for coll in ("materials", "images", "collections", "texts"):
    for d in getattr(bpy.data, coll):
        if FORBIDDEN.search(d.name):
            rep["forbidden_name"].append(f"{coll}:{d.name}")
for coll in ("meshes", "materials", "images", "curves", "node_groups", "textures", "cameras", "lights"):
    orph = [d.name for d in getattr(bpy.data, coll) if d.users == 0]
    if orph:
        rep["orphans"].append((coll, len(orph), orph[:8]))
rep["non_generated_objects"] = [o.name for o in bpy.data.objects if o.users_collection and not o.get("koch_gen")]

# ------------------------------------------------------------------ support (props floating / buried)
ter = bpy.data.objects.get("TER_Ground")
ter_bvh = None
if ter:
    tv = wverts(ter)
    ter_bvh = BVHTree.FromPolygons([Vector(v) for v in tv], [list(p.vertices) for p in ter.data.polygons])
DOWN = Vector((0, 0, -1))
for ob in meshes:
    if not PROP.search(ob.name) or ob.name.startswith(("REF_", "CTX_")) or not ob.data.vertices:
        continue
    W = wverts(ob)
    lo, hi = W.min(0), W.max(0)
    c = (lo + hi) / 2
    # support: first surface under the lowest point (start 2 cm above it so a flush floor is found)
    gaps = []
    for dx, dy in ((0, 0), (-.3, -.3), (.3, .3), (-.3, .3), (.3, -.3)):
        px = np.clip(c[0] + dx * (hi[0] - lo[0]), lo[0], hi[0])
        py = np.clip(c[1] + dy * (hi[1] - lo[1]), lo[1], hi[1])
        p = Vector((px, py, lo[2] + 0.02))
        hit, loc, n, _, hob, _ = sc.ray_cast(dg, p, DOWN, distance=5.0)
        while hit and hob == ob:  # skip self
            hit, loc, n, _, hob, _ = sc.ray_cast(dg, loc + DOWN * 1e-3, DOWN, distance=5.0)
        gaps.append(lo[2] - loc.z if hit else 99.0)
    g = min(gaps)
    if g > 0.05:
        rep["floating_prop"].append((ob.name, round(g, 2)))
    if ter_bvh:
        hit = ter_bvh.ray_cast(Vector((c[0], c[1], 500)), DOWN)
        if hit[0] is not None:
            tz = hit[0].z
            if tz > hi[2] - 0.01:
                rep["hidden_in_terrain"].append((ob.name, round(tz - hi[2], 2)))
            elif tz - lo[2] > 0.35 and not re.search(r"tree|lamp|floodlight|sign|planter", ob.name, re.I):
                rep["buried_prop"].append((ob.name, round(tz - lo[2], 2)))

# ------------------------------------------------------------------ inventory
inv = defaultdict(Counter)
KINDS = ("Door", "Window", "Win", "Stair", "Step", "Ramp", "Rail", "Roof", "Slab", "Floor", "Ceiling", "Canopy",
         "Bench", "Bin", "Lamp", "Tree", "Planter", "Hedge", "Sign", "Sink", "Desk", "Chair", "Table", "Board",
         "WC", "Stall", "Locker", "Cabinet", "Shelf", "HVAC", "Vent", "Pipe", "Gutter", "Downpipe", "Fence", "Wall")
for ob in bpy.data.objects:
    m = re.match(r"(GBF|GBS)_((?:BLD|SITE|INT)_[A-Za-z0-9]+(?:_[A-Z][A-Za-z0-9]?)?)_(.*)", ob.name)
    if not m:
        continue
    zone, rest = m.group(2), m.group(3)
    inv[zone]["_objects"] += 1
    for k in KINDS:
        if k.lower() in rest.lower():
            inv[zone][k] += 1
rep["inventory"] = {z: dict(c) for z, c in sorted(inv.items())}

# ------------------------------------------------------------------ print
for k, v in rep.items():
    if k in ("collections", "inventory"):
        continue
    print(f"QA {k}: {len(v)}", v[:6] if isinstance(v, list) else v)
print("QA collections:\n" + "\n".join(tree))
for z, c in rep["inventory"].items():
    print("INV", z, " ".join(f"{k}={n}" for k, n in sorted(c.items())))
if OUT:
    json.dump(rep, open(OUT, "w"), indent=1, default=str)
    print("QA written", OUT)
