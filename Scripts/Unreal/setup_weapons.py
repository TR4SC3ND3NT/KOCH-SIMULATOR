# UE 5.8 editor script (R4 playtest setup; R3 owns combat): the player gets the shooter-template character with an
# AK-style rifle on Q (draw / holster), R reload (also automatic on an empty magazine), LMB fire, ejected cases.
# Thin Blueprint children of the template classes, tuned here; logic is C++ (AShooterCharacter / AShooterWeapon).
# Creates under /Game/KochSimulator/Weapons: IA_DrawWeapon, IA_Reload (mapped in IMC_Weapons), AM_Rifle_Reload
# (MM_Rifle_Reload on the FP "Arms" slot), SM_Shell_762 (brass case), BP_Rifle_AK, BP_KochPlayer,
# BP_KochPlayerController, BP_KochGameMode; sets BP_KochGameMode on L_GreyboxTest. Idempotent.
# AK: 30 rounds, 600 rpm full auto (7.62x39). The mesh is the template rifle until an AK model is licensed (Fab).
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/setup_weapons.py"
import unreal

ROOT = "/Game/KochSimulator/Weapons"
LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
L = unreal.EditorAssetLibrary.load_asset
tools = unreal.AssetToolsHelpers.get_asset_tools()


def asset(name, cls, factory):
    path = f"{ROOT}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return L(path)
    return tools.create_asset(name, ROOT, cls, factory)


def child_bp(name, parent_path):
    path = f"{ROOT}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return L(path)
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", L(parent_path).generated_class())
    return tools.create_asset(name, ROOT, unreal.Blueprint, f)


def cdo(bp):
    return unreal.get_default_object(bp.generated_class())


def input_action(name, key):
    ia = asset(name, unreal.InputAction, unreal.InputAction_Factory())
    ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    imc = L("/Game/Variant_Shooter/Input/IMC_Weapons")
    have = [m for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings")
            if m.get_editor_property("action") == ia]
    if not have:
        k = unreal.Key()
        k.set_editor_property("key_name", key)
        imc.map_key(ia, k)
        unreal.EditorAssetLibrary.save_loaded_asset(imc, False)
    unreal.EditorAssetLibrary.save_loaded_asset(ia, False)
    return ia


def reload_montage():
    path = f"{ROOT}/AM_Rifle_Reload"
    src = L("/Game/Characters/Mannequins/Anims/Rifle/MM_Rifle_Reload")
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        m = L(path)
    else:
        f = unreal.AnimMontageFactory()
        f.set_editor_property("source_animation", src)
        m = tools.create_asset("AM_Rifle_Reload", ROOT, unreal.AnimMontage, f)
    tracks = m.get_editor_property("slot_anim_tracks")
    for t in tracks:
        t.set_editor_property("slot_name", "Arms")   # the slot ABP_FP_Weapon plays FP_Rifle_Shoot_Montage on
    m.set_editor_property("slot_anim_tracks", tracks)
    unreal.EditorAssetLibrary.save_loaded_asset(m, False)
    return m, src.get_play_length()


def shell_mesh():
    path = f"{ROOT}/SM_Shell_762"
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.duplicate_asset("/Engine/BasicShapes/Cylinder", path)
    sm = L(path)
    mpath = f"{ROOT}/M_Brass"
    if unreal.EditorAssetLibrary.does_asset_exist(mpath):
        mat = L(mpath)
    else:
        mel = unreal.MaterialEditingLibrary
        mat = tools.create_asset("M_Brass", ROOT, unreal.Material, unreal.MaterialFactoryNew())
        c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
        c.set_editor_property("constant", unreal.LinearColor(0.78, 0.55, 0.22, 1.0))   # linear brass
        mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
        for v, prop, y in ((1.0, unreal.MaterialProperty.MP_METALLIC, 150), (0.3, unreal.MaterialProperty.MP_ROUGHNESS, 250)):
            k = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, y)
            k.set_editor_property("r", v)
            mel.connect_material_property(k, "", prop)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    sm.set_material(0, mat)
    unreal.EditorAssetLibrary.save_loaded_asset(sm, False)
    return sm


def main():
    draw = input_action("IA_DrawWeapon", "Q")
    reload_ia = input_action("IA_Reload", "R")
    montage, reload_s = reload_montage()
    shell = shell_mesh()

    ak = child_bp("BP_Rifle_AK", "/Game/Variant_Shooter/Blueprints/Pickups/Weapons/BP_ShooterWeapon_Rifle")
    w = cdo(ak)
    for k, v in (("magazine_size", 30), ("full_auto", True), ("refire_rate", 0.1), ("aim_variance", 6.0),
                 ("firing_recoil", -0.15), ("reload_montage", montage), ("reload_time", reload_s),
                 ("shell_mesh", shell)):
        w.set_editor_property(k, v)
    unreal.EditorAssetLibrary.save_loaded_asset(ak, False)

    player = child_bp("BP_KochPlayer", "/Game/Variant_Shooter/Blueprints/BP_ShooterCharacter")
    c = cdo(player)
    c.set_editor_property("starter_weapon_class", ak.generated_class())
    c.set_editor_property("draw_weapon_action", draw)
    c.set_editor_property("reload_action", reload_ia)
    unreal.EditorAssetLibrary.save_loaded_asset(player, False)

    pc = child_bp("BP_KochPlayerController", "/Game/Variant_Shooter/Blueprints/BP_ShooterPlayerController")
    cdo(pc).set_editor_property("character_class", player.generated_class())
    unreal.EditorAssetLibrary.save_loaded_asset(pc, False)

    gm = child_bp("BP_KochGameMode", "/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode")
    g = cdo(gm)
    g.set_editor_property("default_pawn_class", player.generated_class())
    g.set_editor_property("player_controller_class", pc.generated_class())
    unreal.EditorAssetLibrary.save_loaded_asset(gm, False)

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues.get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    ws = ues.get_editor_world().get_world_settings()
    ws.modify()
    ws.set_editor_property("default_game_mode", gm.generated_class())
    les.save_current_level()
    unreal.log(f"setup_weapons: AK ready (reload {reload_s:.2f} s), game mode set")


main()
