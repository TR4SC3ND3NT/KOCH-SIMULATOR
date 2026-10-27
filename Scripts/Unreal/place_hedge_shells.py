# UE 5.8 editor script (R4 -> everyone): imports the clipped-hedge leaf shells from Scripts/Blender/build_hedge_shells.py
# (world-space meshes, placed at the origin) as Nanite meshes with masked two-sided leaves (M_PH_Foliage + Poly Haven
# shrub_02 textures, MI_HedgeLeaves). The greybox hedge mass underneath gets the photo leaf texture from
# apply_surface_materials.py (M_Hedge_Foliage), so gaps between sprigs show real foliage. Re-running replaces the shells.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/place_hedge_shells.py" [SHELL_DIR] [--reimport]
import json
import os
import sys

import unreal

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SHELLS = ARGS[0] if ARGS else os.path.join(REPO, "Saved", "ThirdParty", "HedgeShells")
ROOT = "/Game/KochSimulator/Environment/Vegetation/Hedges"
VEG = "/Game/KochSimulator/Environment/Vegetation/PolyHaven/Materials"
LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
TAG = "KochHedgeShell"
LEAF_TINT = unreal.LinearColor(0.72, 0.82, 0.78, 1.0)   # shrub_02 olive -> the dusty grey-green of the garden privet (owner photos)


def leaf_material(tools):
    mel = unreal.MaterialEditingLibrary
    path = f"{ROOT}/MI_HedgeLeaves"
    src = unreal.EditorAssetLibrary.load_asset(f"{VEG}/MI_PH_Shrub02_Leaf")
    mi = (unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else
          tools.create_asset("MI_HedgeLeaves", ROOT, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew()))
    mel.set_material_instance_parent(mi, src.get_editor_property("parent"))
    for p in src.get_editor_property("texture_parameter_values"):
        mel.set_material_instance_texture_parameter_value(
            mi, p.get_editor_property("parameter_info").get_editor_property("name"), p.get_editor_property("parameter_value"))
    mel.set_material_instance_vector_parameter_value(mi, "Tint", LEAF_TINT)
    mel.update_material_instance(mi)
    return mi


def import_shells(names):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    out = {n: unreal.EditorAssetLibrary.load_asset(f"{ROOT}/Meshes/{n}") for n in names
           if "--reimport" not in sys.argv and unreal.EditorAssetLibrary.does_asset_exist(f"{ROOT}/Meshes/{n}")}
    tasks = []
    for n in (n for n in names if n not in out):
        p = unreal.InterchangeGenericAssetsPipeline()
        mp = p.get_editor_property("mesh_pipeline")
        mp.set_editor_property("build_nanite", True)
        mp.set_editor_property("collision", False)   # the greybox mass keeps the hedge's collision
        mp.set_editor_property("distance_field_resolution_scale", 0.0)   # never build DFs for leaf shells (see main)
        mp.set_editor_property("generate_lightmap_u_vs", False)
        p.get_editor_property("material_pipeline").set_editor_property("import_materials", False)
        p.set_editor_property("asset_name", n)
        ov = unreal.InterchangePipelineStackOverride()
        ov.add_pipeline(p)
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(SHELLS, f"{n}.fbx"))
        t.set_editor_property("destination_path", f"{ROOT}/Meshes")
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", False)
        t.set_editor_property("options", ov)
        tasks.append((n, t))
    if tasks:
        tools.import_asset_tasks([t for _, t in tasks])
    for n, t in tasks:
        out[n] = next((o for o in t.get_objects() if isinstance(o, unreal.StaticMesh)), None)
    return out


def main():
    with open(os.path.join(SHELLS, "shells.json"), encoding="utf-8") as fh:
        shells = json.load(fh)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    leaves = leaf_material(tools)
    meshes = import_shells(sorted(shells))
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for sm in meshes.values():
        if sm is not None:
            sm.modify()
            sm.set_material(0, leaves)
            # no mesh distance field: leaf cards gain nothing in Lumen SW, and building DFs for 7M faces of foliage
            # exhausted RAM/commit on the 24 GB laptop (editor D3D12 E_OUTOFMEMORY, 2026-10-27)
            bs = sms.get_lod_build_settings(sm, 0)
            if bs.get_editor_property("distance_field_resolution_scale") != 0.0:
                bs.set_editor_property("distance_field_resolution_scale", 0.0)
                sms.set_lod_build_settings(sm, 0, bs)
    unreal.EditorAssetLibrary.save_directory(ROOT, False, True)

    # place into the campus level: after an editor restart the template's startup map is open
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    eas.destroy_actors([a for a in eas.get_all_level_actors() if a.actor_has_tag(TAG)])
    placed = 0
    for n, sm in sorted(meshes.items()):
        if sm is None:
            continue
        a = eas.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0), unreal.Rotator())   # world-space vertices
        a.set_actor_label(n.replace("SM_HedgeShell_", "HEDGE_"))
        a.set_folder_path("Vegetation/Hedges")
        a.set_editor_property("tags", [unreal.Name(TAG), unreal.Name(f"Covers:{shells[n]['hedge']}")])
        a.get_editor_property("static_mesh_component").set_mobility(unreal.ComponentMobility.STATIC)
        placed += 1
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"place_hedge_shells: {placed} shells, {sum(s['faces'] for s in shells.values())} faces")


main()
