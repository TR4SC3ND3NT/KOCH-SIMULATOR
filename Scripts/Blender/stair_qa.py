# Outdoor stair conflict QA (R1, owner msg 127): every stair-family object (steps, flights, landings, cheeks, ramps, rails,
# nosings; with KOCH_QA_ALL=1 every outdoor site object, msg 135) outside the interiors is tested against every other
# mesh whose bbox it touches. Designed contacts (a rail
# post on a tread, a cheek against a wall) are ignored by shrinking both meshes 6 mm along the vertex normals first; what
# still intersects is a real interpenetration. Read-only, never saves.
# Run: blender -b FILE.blend -P Scripts/Blender/stair_qa.py -- OUT.json
import json
import os
import re
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
STAIR = re.compile(r"^GBS_" if os.environ.get("KOCH_QA_ALL") else
                   r"(Stair|Step|Landing|Cheek|Ramp|Rail|Nosing|Riser|Tread|Flight|Balustrade)", re.I)
SKIP = re.compile(r"(^TER_|^CTX_|^REF_|^CAM_|INT_C|_Int_|Interior)")
SHRINK = 0.006   # m: contacts up to this deep are designed (posts on treads, cheeks on walls)
DEEP = 0.03      # m: a vertex more than this inside another solid is a conflict to fix (embeds below are seams)


def shrunk_bvh(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    bm.normal_update()
    for v in bm.verts:
        if v.link_faces:
            v.co -= v.normal * SHRINK
    t = BVHTree.FromBMesh(bm)
    lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)]) if bm.verts else Vector()
    hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)]) if bm.verts else Vector()
    pts = [v.co.copy() for v in bm.verts]
    bm.free()
    return t, lo, hi, pts


def inside(tree, p, dirs=(Vector((0.31, 0.27, 0.91)), Vector((-0.6, 0.52, -0.6)))):
    """Ray-parity inside test (same as overlap_qa.inside): both directions must give an odd hit count."""
    for d in dirs:
        n, o = 0, p.copy()
        while n < 64:
            loc, _n, _i, _d = tree.ray_cast(o, d)
            if loc is None:
                break
            n += 1
            o = loc + d * 1e-4
        if n % 2 == 0:
            return False
    return True


def main():
    obs = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and o.visible_get() is not False
           and len(o.data.polygons) and not SKIP.search(o.name)]
    data = {o.name: shrunk_bvh(o) for o in obs}
    stairs = [o for o in obs if STAIR.search(o.name)]
    seen, rows = set(), []
    for a in stairs:
        ta, lo_a, hi_a, pa = data[a.name]
        for b in obs:
            if b is a or (b.name, a.name) in seen:
                continue
            tb, lo_b, hi_b, pb = data[b.name]
            if any(hi_a[i] < lo_b[i] or hi_b[i] < lo_a[i] for i in range(3)):
                continue
            seen.add((a.name, b.name))
            pairs = ta.overlap(tb)
            if not pairs:
                continue
            # how deep: farthest vertex of either mesh inside the other closed mesh, to the other's surface
            depth, at = 0.0, None
            for pts, tree in ((pa, tb), (pb, ta)):
                for p in pts:
                    if inside(tree, p):
                        _l, _n, _i, d = tree.find_nearest(p)
                        if d is not None and d > depth:
                            depth, at = d + SHRINK, p
            c = at or (Vector([max(lo_a[i], lo_b[i]) for i in range(3)]) + Vector([min(hi_a[i], hi_b[i]) for i in range(3)])) / 2
            rows.append({"a": a.name, "b": b.name, "tris": len(pairs), "depth": round(depth, 3),
                         "at": [round(c.x, 2), round(c.y, 2), round(c.z, 2)]})
    rows.sort(key=lambda r: -r["depth"])
    deep = [r for r in rows if r["depth"] > DEEP]
    print(f"stair_qa: {len(stairs)} stair-family objects, {len(rows)} interpenetrating pairs, {len(deep)} deeper than {DEEP} m")
    for r in rows[:400]:
        print(f'  {r["depth"]:6.3f} {r["tris"]:5d}  {r["a"]}  x  {r["b"]}  @ {r["at"]}')
    if OUT:
        json.dump(rows, open(OUT, "w"), indent=1)


main()
