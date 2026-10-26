# Third-party vegetation prep (R4): splits each Poly Haven FBX set (several plants side by side, e.g. fir_tree_01 a/b/c)
# into one FBX per plant with its pivot at the trunk base (bounding-box centre in XY, min Z), named SM_PH_<Asset>_<V>,
# plus split.json (height/width per variant) for Scripts/Unreal/place_vegetation.py. Never touches the greybox .blend.
# FBX settings = ue_prep/Epic Send2UE (forward -Y, up Z, apply unit scale, FBX_SCALE_NONE): 1 Blender m -> UE cm.
# Run: blender -b -P Scripts/Blender/split_polyhaven.py -- SRC_DIR OUT_DIR asset [asset ...]
import json
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, ASSETS = argv[0], argv[1], argv[2:]
os.makedirs(OUT, exist_ok=True)
meta = {}

for asset in ASSETS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Poly Haven's fir_tree_01 FBX ships without UVs (0 LayerElementUV), so the needle mask sampled one texel; prefer
    # the glTF download (<asset>_gltf/) when present
    gltf = os.path.join(SRC, f"{asset}_gltf", f"{asset}_2k.gltf")
    if os.path.exists(gltf):
        bpy.ops.import_scene.gltf(filepath=gltf)
    else:
        bpy.ops.import_scene.fbx(filepath=os.path.join(SRC, asset, f"{asset}_2k.fbx"))
    base = "".join(p.capitalize() for p in asset.split("_"))   # fir_tree_01 -> FirTree01
    for ob in [o for o in bpy.data.objects if o.type == "MESH"]:
        variant = ob.name.split("_LOD")[0].rsplit("_", 1)[-1].upper()   # fir_tree_01_a_LOD0 -> A
        name = f"SM_PH_{base}_{variant}"
        corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
        hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
        pivot = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        ob.data.transform(__import__("mathutils").Matrix.Translation(-(pivot - ob.matrix_world.translation)))
        ob.location = (0, 0, 0)
        ob.name = name
        bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, f"{name}.fbx"), use_selection=True, axis_forward="-Y",
                                 axis_up="Z", apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
                                 mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
                                 path_mode="STRIP", use_mesh_modifiers=True)
        meta[name] = {"asset": asset, "height_m": round(hi.z - lo.z, 3), "width_m": round(max(hi.x - lo.x, hi.y - lo.y), 3),
                      "slots": [m.name for m in ob.data.materials],
                      "tris": sum(len(p.vertices) - 2 for p in ob.data.polygons)}
        print(f"split_polyhaven: {name} {meta[name]['height_m']} m, {meta[name]['tris']} tris")
with open(os.path.join(OUT, "split.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=1)
