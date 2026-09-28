# Entrance check (R1 zone loop): for every exterior door of the building shells (GBF_BLD_*Door*), the surface just
# outside the door must be at the sill level (within TOL; a step/landing object counts). Prints mismatches.
# Run: blender -b FILE.blend -P Scripts/Blender/check_entrances.py
import re

import bpy
from mathutils import Vector

TOL = 0.20
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
DOWN = Vector((0, 0, -1))
bld_c = {}
for o in bpy.data.objects:
    m = re.match(r"GBF_BLD_([A-Za-z]+(?:_[A-Z])?)_", o.name)
    if m and o.type == "MESH":
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        acc = bld_c.setdefault(m.group(1), [0, Vector()])
        acc[0] += 8; acc[1] += sum(bb, Vector())
cen = {k: v[1] / v[0] for k, v in bld_c.items()}
rows = []
for o in bpy.data.objects:
    m = re.match(r"GBF_BLD_([A-Za-z]+(?:_[A-Z])?)_.*Door", o.name)
    if not m or o.type != "MESH" or "Roof" in o.name:
        continue
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    if not vs:
        continue
    z0 = min(v.z for v in vs)
    c = sum(vs, Vector()) / len(vs)
    d = Vector((c.x - cen[m.group(1)].x, c.y - cen[m.group(1)].y, 0))
    if d.length < 1e-6:
        continue
    # outward = the horizontal direction in which the thin door slab faces, signed away from the building centre
    xs = [v.x for v in vs]; ys = [v.y for v in vs]
    thin_x = (max(xs) - min(xs)) < (max(ys) - min(ys))
    out = Vector((1 if d.x > 0 else -1, 0, 0)) if thin_x else Vector((0, 1 if d.y > 0 else -1, 0))
    p = Vector((c.x, c.y, z0 + 0.6)) + out * 0.7
    hit, loc, n, _, ob, _ = sc.ray_cast(dg, p, DOWN, distance=3.0)
    if not hit:
        rows.append((o.name, round(z0, 2), None, None, "no surface")); continue
    dz = loc.z - z0
    if abs(dz) > TOL:
        rows.append((o.name, round(z0, 2), round(loc.z, 2), round(dz, 2), ob.name))
print("ENTRANCES mismatches > %.2f: %d" % (TOL, len(rows)))
for r in rows:
    print("DOOR", *r)
