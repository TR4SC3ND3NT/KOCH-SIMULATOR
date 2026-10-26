# Greybox material colours for UE (R4, read-only on the .blend): every material's review colour (diffuse_color, set from
# greybox/materials.py PALETTE; the Principled BSDF is left at defaults) + roughness/metallic -> JSON keyed by name, so
# Scripts/Unreal/apply_greybox_materials.py can build one material instance per greybox slot. Colours are linear.
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/export_material_colors.py -- OUT.json
import json
import sys

import bpy

out = sys.argv[sys.argv.index("--") + 1]


def principled(mat):
    if not mat.use_nodes or mat.node_tree is None:
        return None
    return next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def val(node, name, default):
    s = node.inputs.get(name) if node else None
    if s is None or s.is_linked:
        return default
    v = s.default_value
    return list(v) if hasattr(v, "__len__") else float(v)


res = {}
for mat in bpy.data.materials:
    p = principled(mat)
    base = list(mat.diffuse_color)   # the builders only set the review colour; Principled stays at 0.8 grey
    res[mat.name] = {
        "base_color": [round(c, 4) for c in base[:3]],
        "roughness": round(val(p, "Roughness", mat.roughness), 3),
        "metallic": round(val(p, "Metallic", mat.metallic), 3),
        "transmission": round(val(p, "Transmission Weight", 0.0), 3),
        "alpha": round(val(p, "Alpha", mat.diffuse_color[3]), 3),
        "emission": round(val(p, "Emission Strength", 0.0), 3),
        "users": mat.users,
    }
with open(out, "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1, sort_keys=True)
print(f"export_material_colors: {len(res)} materials -> {out}")
