# Exports the greybox as world-space triangles with a per-triangle class, object and material id (one .npz), so the
# R1 photo-vs-model tools (Scripts/Geo/model_raycast.py) render class/id/depth/xyz maps for any camera on the CPU with
# Open3D, without Blender. Class names and rules come from render_semantic.py.
# Run: blender -b model.blend -P Scripts/Blender/export_tris.py -- OUT.npz
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_semantic import CLASSES, classify   # noqa: E402

out = sys.argv[sys.argv.index("--") + 1]
cls_names = list(CLASSES)
dg = bpy.context.evaluated_depsgraph_get()
V, F, C, O, M = [], [], [], [], []
names, mats, mat_id = [], [], {}
nv = 0
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    if ob.type != "MESH" or ob.hide_render or ob.name.startswith(("REF_", "CAM_", "TMP_")):
        continue
    me = ob.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    if not n:
        ob.evaluated_get(dg).to_mesh_clear()
        continue
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    mw = np.array(ob.matrix_world)
    W = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    tri = np.empty(n * 3, np.int64)
    me.loop_triangles.foreach_get("vertices", tri)
    pi = np.empty(n, np.int64)
    me.loop_triangles.foreach_get("polygon_index", pi)
    mi = np.empty(len(me.polygons), np.int64)
    me.polygons.foreach_get("material_index", mi)
    slot_cls, slot_mat = [], []
    for s in (ob.material_slots or [None]):
        m = s.material if s else None
        slot_cls.append(cls_names.index(classify(ob, m)))
        key = m.name if m else ""
        if key not in mat_id:
            mat_id[key] = len(mats)
            mats.append(key)
        slot_mat.append(mat_id[key])
    k = np.clip(mi[pi], 0, len(slot_cls) - 1)
    tc = np.array(slot_cls, np.uint8)[k]
    # roof-type sheet/shingle on a vertical face is cladding (shed hex band, sheet walls): class it as wall
    T = W[tri.reshape(-1, 3)]
    nz = np.abs(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])[:, 2]) / np.maximum(
        np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1), 1e-12)
    tc[(tc == cls_names.index("roof")) & (nz < 0.3)] = cls_names.index("wall")
    oid = len(names)
    names.append(ob.name)
    V.append(W.astype(np.float32))
    F.append((tri.reshape(-1, 3) + nv).astype(np.int32))
    C.append(tc)
    M.append(np.array(slot_mat, np.uint16)[k])
    O.append(np.full(n, oid, np.int32))
    nv += len(W)
    ob.evaluated_get(dg).to_mesh_clear()
np.savez_compressed(out, V=np.concatenate(V), F=np.concatenate(F), cls=np.concatenate(C), mat=np.concatenate(M),
                    oid=np.concatenate(O), names=np.array(names), mats=np.array(mats), classes=np.array(cls_names),
                    colours=np.array([CLASSES[c] for c in cls_names], np.uint8), source=bpy.data.filepath)
print("export_tris:", out, len(names), "objects", sum(len(f) for f in F), "triangles")
