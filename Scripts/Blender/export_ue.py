# UE export of the greybox (R1 -> everyone): one FBX per zone collection (BLD_A, SITE_Sport, INT_C_F1, ...) with world
# transforms, for UE "Import Into Level" (FBX scene import keeps every object as its own static mesh + actor), plus a
# manifest (object -> collection, material slots, koch_id/ue_asset hints). Hidden phase-1 massing is skipped; the map
# barrier walls (M_Invisible) go into their own FBX so UE can turn them into blocking volumes. Does not save the .blend.
# FBX settings = Epic's Send to Unreal defaults (github.com/EpicGamesExt/BlenderTools send2ue/resources/settings.json):
# forward Y, up Z, apply unit scale, FBX_SCALE_NONE, face smoothing; 1 Blender unit = 1 m -> UE cm.
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/export_ue.py -- [OUT_DIR]
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0]) if argv else os.path.join(REPO, "Saved", "BlenderExport")
SKIP_COLLECTIONS = ("00_Reference", "REF_Satellite", "99_Replaced_Phase1")


def leaf_collections(col, out):
    """Collections that hold objects directly (zone level); their children are handled on their own."""
    if col.name in SKIP_COLLECTIONS:
        return out
    if col.objects:
        out.append(col)
    for ch in col.children:
        leaf_collections(ch, out)
    return out


def main():
    sc = bpy.context.scene
    us = sc.unit_settings
    if us.system != "METRIC" or abs(us.scale_length - 1.0) > 1e-6:
        raise SystemExit(f"export_ue: scene units must be metric, scale 1.0 (got {us.system}, {us.scale_length})")
    os.makedirs(OUT, exist_ok=True)
    vl = bpy.context.view_layer
    manifest = {"units": "1 BU = 1 m (FBX apply unit scale -> UE cm)", "fbx": {}, "objects": {}}
    for col in leaf_collections(sc.collection, []):
        obs = [o for o in col.objects if o.type == "MESH" and (not o.hide_render or o.name.startswith("GBS_Barriers"))]
        if not obs:
            continue
        for o in vl.objects:
            o.select_set(False)
        was_hidden = []
        for o in obs:
            if o.hide_get():
                was_hidden.append(o)
                o.hide_set(False)
            o.select_set(True)
        path = os.path.join(OUT, f"{col.name}.fbx")
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, use_custom_props=False,
                                 global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
                                 axis_forward="Y", axis_up="Z", bake_space_transform=False, mesh_smooth_type="FACE",
                                 use_mesh_modifiers=True, use_mesh_edges=False, use_tspace=False, use_metadata=True,
                                 bake_anim=False)
        for o in was_hidden:
            o.hide_set(True)
        manifest["fbx"][col.name] = {"file": os.path.basename(path), "objects": len(obs)}
        for o in obs:
            manifest["objects"][o.name] = {
                "collection": col.name, "slots": [m.name for m in o.data.materials if m],
                "koch_id": o.get("koch_id", ""), "ue_asset": o.get("koch_ue_asset", o.get("ue_asset", "")),
                "confidence": o.get("koch_confidence", ""),
                "instance_of": o.data.name if o.data.users > 1 else ""}   # shared mesh = one UE asset, many actors
        print(f"export_ue: {col.name}: {len(obs)} objects -> {path}")
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"export_ue: {len(manifest['fbx'])} FBX files, {len(manifest['objects'])} objects -> {OUT}")


main()
