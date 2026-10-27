# Far ground FBX (R4, used by Scripts/Unreal/place_far_ground.py): height grid sampled in UE (grid.json, UE cm) ->
# one smooth quad mesh SM_FarGround in the ue_prep FBX convention (Send2UE axes; UE mirrors Y, see ue_prep/common.py),
# UVs = world metres like ue_prep box_uvs on up faces. Built here, not with MeshDescription in UE: that path left the
# normals/tangents unset and the ground rendered black.
# Run: blender -b -P Scripts/Blender/build_far_ground.py -- Saved/FarGround/grid.json Saved/FarGround/SM_FarGround.fbx
import json
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ue_prep.export import FBX_KW   # noqa: E402

src, dst = sys.argv[sys.argv.index("--") + 1:][:2]
with open(src, encoding="utf-8") as fh:
    grid = json.load(fh)
c = np.asarray(grid["coords"], np.float64) / 100.0       # m, UE axes
z = np.asarray(grid["z"], np.float64) / 100.0             # z[i][j] at (c[i], c[j])
n = len(c)
X, Y = np.meshgrid(c, c, indexing="ij")
co = np.stack([X.ravel(), -Y.ravel(), z.ravel()], 1)       # Blender: y = -UE y
idx = np.arange(n * n).reshape(n, n)
a, b = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel()
cc, d = idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
quads = np.stack([a, b, cc, d], 1)
e1 = co[quads[:, 1]] - co[quads[:, 0]]
e2 = co[quads[:, 2]] - co[quads[:, 0]]
if np.cross(e1, e2)[:, 2].mean() < 0:                      # counter-clockwise from +Z = up in Blender
    quads = quads[:, ::-1]
me = bpy.data.meshes.new("SM_FarGround")
me.from_pydata(co.tolist(), [], quads.tolist())
me.materials.append(bpy.data.materials.get("M_Ground_Grass") or bpy.data.materials.new("M_Ground_Grass"))
lay = me.uv_layers.new(name="UVMap")
lv = np.empty(len(me.loops), np.int64)
me.loops.foreach_get("vertex_index", lv)
lay.uv.foreach_set("vector", np.stack([co[lv, 0], co[lv, 1]], 1).astype(np.float32).ravel())
me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
me.update()
ob = bpy.data.objects.new("SM_FarGround", me)
bpy.context.scene.collection.objects.link(ob)
os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
with bpy.context.temp_override(selected_objects=[ob], active_object=ob):
    bpy.ops.export_scene.fbx(filepath=dst, **FBX_KW)
print(f"build_far_ground: {len(me.polygons)} quads -> {dst}")
