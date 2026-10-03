# Door clearance QA (R1, 2026-10-03): every spec door (SITE_* / INT_* "door" elements) needs a free walk-through zone
# on both sides of its opening; any other mesh reaching into that zone (a panel painted over the opening, a cabinet,
# a wall stub, a blocking volume) is reported. Owner 2026-10-03: the C WC doors were hidden behind blue accent panels.
# Zone per side: opening width - 6 cm, from 2 cm off the wall face to DEPTH m out, floor + 8 cm .. head - 5 cm.
# Read-only, never saves. Run: blender -b FILE.blend -P Scripts/Blender/door_qa.py -- OUT.json
import glob
import json
import os
import sys

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
DEPTH = 0.6   # m of clear floor in front of each face of the opening
DEPTH_CUBICLE = 0.3   # WC cubicle (outward door): pan front to the door line


def spec_doors():
    for fn in sorted(glob.glob(os.path.join(REPO, "Art", "Blender", "Specs", "*.json"))):
        sid = os.path.basename(fn)[:-5]
        for e in json.load(open(fn, encoding="utf-8")).get("elements", []):
            if e.get("type") == "door" and "line" in e:
                yield sid, e


def zone_boxes(e):
    (ax, ay), (bx, by) = e["line"][0][:2], e["line"][1][:2]
    a, b = Vector((ax, ay, 0.0)), Vector((bx, by, 0.0))
    d = (b - a).normalized()
    n = Vector((-d.y, d.x, 0.0))
    um = (e["u0"] + e["u1"]) / 2
    hw = (e["u1"] - e["u0"]) / 2 - 0.03
    t = e.get("wall_thk", 0.2)
    z0, z1 = e["z0"] + 0.08, e["z1"] - 0.05
    dep = DEPTH_CUBICLE if "Cubicle" in e["name"] else DEPTH
    out = []
    for s in (1, -1):
        c = a + d * um + n * s * (t / 2 + 0.02 + dep / 2)
        out.append((s, c, d, n, hw, dep / 2, z0, z1))
    return out


def box_bvh(c, d, n, hu, hv, z0, z1):
    corners = [c + d * su * hu + n * sv * hv + Vector((0, 0, z)) for z in (z0, z1) for su in (-1, 1) for sv in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return BVHTree.FromPolygons(corners, faces), corners


def inside(bvh, p, dirs=(Vector((0.31, 0.27, 0.91)), Vector((-0.6, 0.52, -0.6)))):
    """Ray-parity inside test; both directions must agree."""
    votes = 0
    for dv in dirs:
        dv = dv.normalized()
        q, k = p.copy(), 0
        for _ in range(64):
            hit = bvh.ray_cast(q, dv)
            if hit[0] is None:
                break
            k += 1
            q = hit[0] + dv * 1e-4
        votes += k % 2
    return votes == 2


def main():
    dg = bpy.context.evaluated_depsgraph_get()
    meshes = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.data.polygons:
            continue
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector((min(p.x for p in bb), min(p.y for p in bb), min(p.z for p in bb)))
        hi = Vector((max(p.x for p in bb), max(p.y for p in bb), max(p.z for p in bb)))
        meshes.append((ob, lo, hi))
    cache = {}

    def bvh_of(ob):
        if ob.name not in cache:
            bm = bmesh.new()
            bm.from_object(ob, dg)
            bm.transform(ob.matrix_world)
            cache[ob.name] = BVHTree.FromBMesh(bm)
            bm.free()
        return cache[ob.name]

    issues, n_doors = [], 0
    for sid, e in spec_doors():
        n_doors += 1
        own = f"GBS_{sid}_{e['name']}"
        for s, c, d, n, hu, hv, z0, z1 in zone_boxes(e):
            zb, corners = box_bvh(c, d, n, hu, hv, z0, z1)
            lo = Vector((min(p.x for p in corners), min(p.y for p in corners), z0))
            hi = Vector((max(p.x for p in corners), max(p.y for p in corners), z1))
            hits = []
            for ob, olo, ohi in meshes:
                if ob.name.startswith(own) or olo.x > hi.x or ohi.x < lo.x or olo.y > hi.y or ohi.y < lo.y \
                        or olo.z > hi.z or ohi.z < lo.z:
                    continue
                if ob.get("koch_collision_only") is None and (ob.hide_render or ob.hide_get() or ob.hide_viewport):
                    continue   # replaced phase-1 massing, cutters, helpers (blocking volumes still count)
                bv = bvh_of(ob)
                if zb.overlap(bv) or inside(bv, c + Vector((0, 0, (z0 + z1) / 2))):
                    hits.append(ob.name)
            if hits:
                issues.append({"spec": sid, "door": e["name"], "side": s, "centre": [round(c.x, 2), round(c.y, 2)],
                               "z": [round(z0, 2), round(z1, 2)], "hits": hits})
    print(f"door_qa: {n_doors} doors, {len(issues)} blocked sides")
    for i in issues:
        print(f"  {i['spec']}:{i['door']} side {i['side']:+d} at {i['centre']}: {', '.join(i['hits'][:6])}"
              + (" ..." if len(i["hits"]) > 6 else ""))
    if OUT:
        json.dump({"doors": n_doors, "issues": issues}, open(OUT, "w"), indent=1)


main()
