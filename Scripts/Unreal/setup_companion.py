# UE 5.8 editor script (R4 playtest aid): imports a static character mesh + its texture into a personal sandbox
# (Content/Developers/<user>/Companion, not committed: a real person's likeness stays out of the shared project, see
# AGENTS.md "Lore"), builds BP_KochCompanion (AKochCompanion) with it and binds T (IA_SpawnCompanion) on BP_KochPlayer.
# With a mannequin-rigged FBX (Scripts/Blender/rig_to_mannequin.py) it is imported on SK_Mannequin and animated by
# the template's ABP_Unarmed; the static mesh stays as the procedural fallback.
# Run (Output Log, Cmd = Python):
#   py "<repo>/Scripts/Unreal/setup_companion.py" <dir with character.fbx + character_texture.png> [user] [rigged.fbx]
import os
import sys

import unreal

SRC = sys.argv[1]
USER = sys.argv[2] if len(sys.argv) > 2 else "eldiiar"
RIGGED = sys.argv[3] if len(sys.argv) > 3 else ""
SKELETON = "/Game/Characters/Mannequins/Meshes/SK_Mannequin"
ANIM_BP = "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed"
ROOT = f"/Game/Developers/{USER}/Companion"
WEAPONS = "/Game/KochSimulator/Weapons"
L = unreal.EditorAssetLibrary.load_asset
tools = unreal.AssetToolsHelpers.get_asset_tools()


def import_file(path, name, options=None):
    t = unreal.AssetImportTask()
    for k, v in (("filename", path), ("destination_path", ROOT), ("destination_name", name), ("automated", True),
                 ("replace_existing", True), ("save", True)):
        t.set_editor_property(k, v)
    if options is not None:
        t.set_editor_property("options", options)
    tools.import_asset_tasks([t])
    return t.get_objects()


def main():
    tex = next(o for o in import_file(os.path.join(SRC, "character_texture.png"), "T_Companion") if isinstance(o, unreal.Texture2D))
    p = unreal.InterchangeGenericAssetsPipeline()
    mp = p.get_editor_property("mesh_pipeline")
    mp.set_editor_property("build_nanite", True)
    mp.set_editor_property("collision", False)
    p.get_editor_property("common_meshes_properties").set_editor_property(
        "force_all_mesh_as_type", unreal.InterchangeForceMeshType.IFMT_STATIC_MESH)
    p.get_editor_property("material_pipeline").set_editor_property("import_materials", False)
    p.set_editor_property("asset_name", "SM_Companion")
    ov = unreal.InterchangePipelineStackOverride()
    ov.add_pipeline(p)
    mesh = next(o for o in import_file(os.path.join(SRC, "character.fbx"), "SM_Companion", ov) if isinstance(o, unreal.StaticMesh))

    mpath = f"{ROOT}/M_Companion"
    if unreal.EditorAssetLibrary.does_asset_exist(mpath):
        mat = L(mpath)
    else:
        mel = unreal.MaterialEditingLibrary
        mat = tools.create_asset("M_Companion", ROOT, unreal.Material, unreal.MaterialFactoryNew())
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, 0)
        ts.set_editor_property("texture", tex)
        mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
        r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 250)
        r.set_editor_property("r", 0.75)
        mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
        mat.set_editor_property("used_with_nanite", True)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    mesh.set_material(0, mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)

    bp_path = f"{ROOT}/BP_KochCompanion"
    if unreal.EditorAssetLibrary.does_asset_exist(bp_path):
        bp = L(bp_path)
    else:
        f = unreal.BlueprintFactory()
        f.set_editor_property("parent_class", unreal.KochCompanion)
        bp = tools.create_asset("BP_KochCompanion", ROOT, unreal.Blueprint, f)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.get_editor_property("body_mesh").set_editor_property("static_mesh", mesh)
    cdo.set_editor_property("explosion_class",
                            L("/Game/Variant_Shooter/Blueprints/Pickups/Projectiles/BP_ShooterGrenadeExplosion").generated_class())
    cdo.set_editor_property("debris_mesh", L("/Engine/BasicShapes/Cube"))
    if RIGGED:
        sp = unreal.InterchangeGenericAssetsPipeline()
        smp = sp.get_editor_property("mesh_pipeline")
        smp.set_editor_property("import_skeletal_meshes", True)
        smp.set_editor_property("import_static_meshes", False)
        smp.set_editor_property("create_physics_asset", False)
        cp = sp.get_editor_property("common_skeletal_meshes_and_animations_properties")
        cp.set_editor_property("skeleton", L(SKELETON))
        sp.get_editor_property("common_meshes_properties").set_editor_property(
            "force_all_mesh_as_type", unreal.InterchangeForceMeshType.IFMT_SKELETAL_MESH)
        sp.get_editor_property("animation_pipeline").set_editor_property("import_animations", False)
        sp.get_editor_property("material_pipeline").set_editor_property("import_materials", False)
        sp.set_editor_property("asset_name", "SKM_Companion")
        sov = unreal.InterchangePipelineStackOverride()
        sov.add_pipeline(sp)
        skm = next((o for o in import_file(RIGGED, "SKM_Companion", sov) if isinstance(o, unreal.SkeletalMesh)), None)
        if skm is None:
            raise RuntimeError("setup_companion: rigged import failed (skeleton mismatch?)")
        mat.set_editor_property("used_with_skeletal_mesh", True)   # cooked/-game builds cannot add usages later
        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
        mats = []
        for old in skm.get_editor_property("materials"):   # struct copies: build new entries, then set the array
            m = unreal.SkeletalMaterial()
            m.set_editor_property("material_slot_name", old.get_editor_property("material_slot_name"))
            m.set_editor_property("material_interface", mat)
            mats.append(m)
        skm.set_editor_property("materials", mats)
        unreal.EditorAssetLibrary.save_loaded_asset(skm, False)
        mesh_comp = cdo.get_editor_property("mesh")
        mesh_comp.set_editor_property("skeletal_mesh_asset", skm)
        mesh_comp.set_editor_property("anim_class", L(ANIM_BP).generated_class())
        mesh_comp.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_BLUEPRINT)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, False)

    ia_path = f"{WEAPONS}/IA_SpawnCompanion"
    ia = L(ia_path) if unreal.EditorAssetLibrary.does_asset_exist(ia_path) else \
        tools.create_asset("IA_SpawnCompanion", WEAPONS, unreal.InputAction, unreal.InputAction_Factory())
    imc = L("/Game/Variant_Shooter/Input/IMC_Weapons")
    if not [m for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings")
            if m.get_editor_property("action") == ia]:
        k = unreal.Key()
        k.set_editor_property("key_name", "T")
        imc.map_key(ia, k)
        unreal.EditorAssetLibrary.save_loaded_asset(imc, False)
    unreal.EditorAssetLibrary.save_loaded_asset(ia, False)

    player = L(f"{WEAPONS}/BP_KochPlayer")
    pc = unreal.get_default_object(player.generated_class())
    pc.set_editor_property("spawn_companion_action", ia)
    pc.set_editor_property("companion_class", bp.generated_class())
    unreal.EditorAssetLibrary.save_loaded_asset(player, False)
    unreal.log(f"setup_companion: {mesh.get_path_name()} -> {bp.get_path_name()}, T bound")


main()
