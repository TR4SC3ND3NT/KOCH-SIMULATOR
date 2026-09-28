# Export every exterior mesh object's up-facing triangles (world XY + z) to an .npz for top-view zone plans (R1 zone
# loop, Scripts/Geo/zone_plan.py). Read-only. Run: blender -b FILE.blend -P Scripts/Blender/export_tops.py -- OUT.npz
import sys

import bpy
import numpy as np

out = sys.argv[sys.argv.index("--") + 1]
dg = bpy.context.evaluated_depsgraph_get()
names, zr, tris, owner = [], [], [], []
SKIP = ("_F1_", "_F2_", "_F3_", "_F4_", "_F5_", "INT_", "_Basement_", "CeilPanel", "Slabs")
for o in bpy.data.objects:
    if o.type != "MESH" or o.hide_render or o.name.startswith(("TER_", "REF_", "CAM_", "TMP_")) or any(k in o.name for k in SKIP):
        continue
    ev = o.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles()
    mw = o.matrix_world; rot = mw.to_3x3()
    co = np.array([mw @ v.co for v in me.vertices], np.float32)
    T = [t.vertices[:] for t in me.loop_triangles if (rot @ t.normal).z > 0.3] if len(co) else []
    if T:
        tris.append(co[np.array(T)]); owner.append(np.full(len(T), len(names), np.int32))
        names.append(o.name); zr.append((float(co[:, 2].min()), float(co[:, 2].max())))
    ev.to_mesh_clear()
np.savez_compressed(out, tris=np.concatenate(tris), owner=np.concatenate(owner), names=np.array(names), zr=np.array(zr))
print("EXPORT", len(names), "objects")
