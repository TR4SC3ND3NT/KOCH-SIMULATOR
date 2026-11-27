"""Builds a KOCH enemy BP (BP_Enemy_<Name>) from BP_Enemy_Donk and a built MetaHuman (Enemies/<Name>/Built/<Name>).
Run inside the editor (unreal-mcp / Python console):  exec(open(path).read()); make_enemy(ENEMIES["Guard"])
Sets body/face/grooms, outfit recolour MIs, weapon + grip, anim BP + montages, role, tuning. Spec: docs/design/enemies.md."""
import unreal

EAL = unreal.EditorAssetLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDF = unreal.SubobjectDataBlueprintFunctionLibrary
ROOT = "/Game/Developers/Azamat/Enemies/"
DONK = "/Game/Developers/Azamat/Donk/BP_Enemy_Donk"
ANIM = "/Game/KochSimulator/Animation/Enemy/"
WEAP = "/Game/KochSimulator/Weapons/"
KELLAN = "/Game/MetaHumans/Kellan/Shared/Materials/"
FACIAL_ROOT = "FACIAL_C_FacialRoot"

# Lyra weapon meshes are authored for the weapon_r bone; this is weapon_r relative to hand_r in Lyra's reference pose.
LYRA_GRIP = unreal.Transform(unreal.Vector(-1.163, 1.317, -0.520), unreal.Rotator(roll=-11.618, pitch=15.808, yaw=-8.517), unreal.Vector(1, 1, 1))

RIFLE = dict(abp=ANIM + "ABP_KochEnemy_Rifle", fire="/Game/Weapons/Rifle/Animations/AM_MM_Rifle_Fire",
             reload="/Game/Weapons/Rifle/Animations/AM_MM_Rifle_Reload", grip=None)  # grip None = keep Donk's AK grip
PISTOL = dict(abp=ANIM + "ABP_KochEnemy_Pistol", fire="/Game/Weapons/Pistol/Animations/AM_MM_Pistol_Fire",
              reload="/Game/Weapons/Pistol/Animations/AM_MM_Pistol_Reload", grip=LYRA_GRIP)
SHOTGUN = dict(abp=ANIM + "ABP_KochEnemy_Rifle", fire="/Game/Weapons/Shotgun/Animations/AM_MM_Shotgun_Fire",
               reload="/Game/Weapons/Shotgun/Animations/AM_MM_Shotgun_Reload", grip=LYRA_GRIP)


def tuning(base, easy, hard):
    """base = Medium FKochEnemyTuning fields; easy/hard = overrides."""
    out = {}
    for diff, extra in ((unreal.KochDifficulty.EASY, easy), (unreal.KochDifficulty.MEDIUM, {}), (unreal.KochDifficulty.HARD, hard)):
        t = unreal.KochEnemyTuning()
        for k, v in {**base, **extra}.items():
            t.set_editor_property(k, v)
        out[diff] = t
    return out


ENEMIES = {
    # name: height cm (as built: the preset heights; MHC height targets did not apply), Pac-Man role, weapon BP, anim set, burst (s), tuning, outfit textures
    "Guard": dict(height=187.5, role=unreal.KochGhostRole.CHASER, weapon="BP_Pistol_Koch", anim=PISTOL, burst=0.8,
                  tuning=tuning(dict(run_speed=400, reaction_time=0.35, aim_cone_still=3.5, aim_cone_running=12, damage_scale=3,
                                     max_health=100, engage_range_min=600, engage_range_max=1500),
                                dict(run_speed=340, reaction_time=0.6, aim_cone_still=6, damage_scale=2, max_health=80),
                                dict(run_speed=440, reaction_time=0.2, aim_cone_still=2, damage_scale=4, max_health=125))),
    "Interceptor": dict(height=187.8, role=unreal.KochGhostRole.AMBUSHER, weapon="BP_SMG_Koch", anim=RIFLE, burst=0.4,
                        tuning=tuning(dict(run_speed=430, reaction_time=0.35, aim_cone_still=4, aim_cone_running=14, damage_scale=2.5,
                                           max_health=90, engage_range_min=400, engage_range_max=1200, max_acceleration=2600),
                                      dict(run_speed=365, reaction_time=0.6, aim_cone_still=6.5, damage_scale=1.5, max_health=72),
                                      dict(run_speed=470, reaction_time=0.2, aim_cone_still=2.5, damage_scale=3.5, max_health=112))),
    "Flanker": dict(height=186.1, role=unreal.KochGhostRole.FLANKER, weapon="BP_Shotgun_Koch", anim=SHOTGUN, burst=0.1,
                    tuning=tuning(dict(run_speed=420, reaction_time=0.4, aim_cone_still=2, aim_cone_running=6, damage_scale=0.8,
                                       max_health=100, engage_range_min=300, engage_range_max=900),
                                  dict(run_speed=360, reaction_time=0.7, damage_scale=0.5, max_health=80),
                                  dict(run_speed=460, reaction_time=0.25, damage_scale=1.1, max_health=125))),
    "Heavy": dict(height=193.9, role=unreal.KochGhostRole.SHY, weapon="BP_LMG_Koch", anim=RIFLE, burst=1.2,
                  tuning=tuning(dict(run_speed=300, reaction_time=0.45, aim_cone_still=4.5, aim_cone_running=16, damage_scale=2.5,
                                     max_health=220, engage_range_min=1200, engage_range_max=2500, max_acceleration=1200,
                                     braking_deceleration=1200),
                                dict(run_speed=255, reaction_time=0.7, aim_cone_still=7, damage_scale=1.5, max_health=176),
                                dict(run_speed=330, reaction_time=0.3, aim_cone_still=3, damage_scale=3.5, max_health=275))),
}


def _handles(bp):
    return {str(SDF.get_variable_name(SDF.get_data(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def _obj(h):
    return SDF.get_associated_object(SDF.get_data(h))


def _outfit_mi(name, kind, parent):
    """MI_<Name>_<kind> = Kellan fabric MI with our recoloured base colour (texture imported beforehand)."""
    folder = ROOT + name + "/Outfit"
    path = "%s/MI_%s_%s" % (folder, name, kind)
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "MI_%s_%s" % (name, kind), folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", unreal.load_asset(KELLAN + parent))
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
        mi, "BaseColor", unreal.load_asset("%s/T_%s_%s_D" % (folder, name, kind)))
    unreal.MaterialEditingLibrary.update_material_instance(mi)
    EAL.save_loaded_asset(mi, False)
    return mi


def make_enemy(name):
    cfg = ENEMIES[name]
    built = "%s%s/Built/%s/" % (ROOT, name, name)
    path = "%s%s/BP_Enemy_%s" % (ROOT, name, name)
    if not EAL.does_asset_exist(path):
        EAL.duplicate_asset(DONK, path)
    bp = unreal.load_asset(path)
    comps = _handles(bp)
    half = cfg["height"] * 0.5

    body = _obj(comps["Mesh"])
    body.set_editor_property("skeletal_mesh_asset", unreal.load_asset(built + "Body/SKM_MHC_%s_BodyMesh" % name))
    body.set_editor_property("relative_location", unreal.Vector(0, 0, -half))
    body.set_editor_property("anim_class", unreal.load_object(None, cfg["anim"]["abp"] + "." + cfg["anim"]["abp"].split("/")[-1] + "_C"))
    _obj(comps["CapsuleComponent"]).set_editor_property("capsule_half_height", half)
    _obj(comps["FaceMesh"]).set_editor_property("skeletal_mesh_asset", unreal.load_asset(built + "Face/SKM_MHC_%s_FaceMesh" % name))

    # Grooms: copy assets/bindings from the generated MetaHuman BP; add components it has and Donk lacks.
    src = {n: _obj(h) for n, h in _handles(unreal.load_asset(built + "BP_" + name)).items() if isinstance(_obj(h), unreal.GroomComponent)}
    lod = next(_obj(h) for h in comps.values() if isinstance(_obj(h), unreal.LODSyncComponent))
    sync = list(lod.get_editor_property("components_to_sync"))
    mapping = lod.get_editor_property("custom_lod_mapping")
    for gname in ("Hair", "Eyebrows", "Mustache", "Beard"):
        s = src.get(gname)
        asset = s.get_editor_property("groom_asset") if s else None
        if gname not in comps:
            if not asset:
                continue
            h, _ = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=comps["FaceMesh"], new_class=unreal.GroomComponent, blueprint_context=bp))
            SDS.rename_subobject(h, unreal.Text(gname))
            comps[gname] = h
            e = unreal.ComponentSync(); e.set_editor_property("name", gname); e.set_editor_property("sync_option", unreal.SyncOption.PASSIVE)
            sync.append(e)
            mapping[gname] = mapping["Hair"]
        g = _obj(comps[gname])
        g.set_editor_property("groom_asset", asset)
        g.set_editor_property("binding_asset", s.get_editor_property("binding_asset") if s else None)
        g.set_editor_property("attachment_name", FACIAL_ROOT)
    lod.set_editor_property("components_to_sync", sync)
    lod.set_editor_property("custom_lod_mapping", mapping)

    _obj(comps["OutfitMesh"]).set_editor_property("override_materials", [_outfit_mi(name, "Hoodie", "MI_Fabric_Torso_Simplified")])
    _obj(comps["ShoesMesh"]).set_editor_property("override_materials", [_outfit_mi(name, "Sneakers", "MI_Fabric_Feet_Simplified")])

    cdo = unreal.get_default_object(unreal.load_object(None, path + ".BP_Enemy_%s_C" % name))
    cdo.set_editor_property("display_name", unreal.Text(name))  # TODO_LORE: in-game names
    cdo.set_editor_property("ghost_role", cfg["role"])
    cdo.set_editor_property("body_scale", 1.0)
    cdo.set_editor_property("burst_duration", cfg["burst"])
    cdo.set_editor_property("tuning", cfg["tuning"])
    cdo.set_editor_property("weapon_class", unreal.load_object(None, WEAP + cfg["weapon"] + "." + cfg["weapon"] + "_C"))
    cdo.set_editor_property("fire_montage", unreal.load_asset(cfg["anim"]["fire"]))
    cdo.set_editor_property("reload_montage", unreal.load_asset(cfg["anim"]["reload"]))
    if cfg["anim"]["grip"]:
        cdo.set_editor_property("weapon_fallback_offset", cfg["anim"]["grip"])

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    return EAL.save_loaded_asset(bp, False)
