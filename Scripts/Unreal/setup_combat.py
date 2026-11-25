# UE 5.8 editor script (R3 combat): assets for simulated bullets, hit zones, hit reactions and impact effects.
# Logic is C++ (Source/KochSimulator/Combat, AI/KochGuard); this only creates data and thin Blueprint children.
# Creates under /Game/KochSimulator/Combat: decal textures and materials (blood splatter / pool / wound, bullet hole),
# gunshot and impact Sound Cues with attenuation, DA_KochImpactEffects. Under /Game/KochSimulator/AI: BP_KochGuard
# (BP_ShooterNPC re-parented to AKochGuard). Under Weapons: BP_Rifle_AK_Guard; BP_Rifle_AK switched to simulated bullets.
# Idempotent: existing assets are kept, their tuning values are re-applied.
# BP_Rifle_AK is LFS-lockable: lock it first (git lfs lock), or the script changes it in memory only and says so.
# No module-level aliases of unreal classes or bound methods (EAL = unreal.EditorAssetLibrary, L = unreal.EditorAssetLibrary.load_asset):
# when Python garbage-collects a script namespace holding them, the 5.8.4 editor dies with an access violation in
# python311.dll (seen right after this script and at the next PIE start). Call unreal.* by its full name instead.
# Compile a Blueprint after changing its class defaults: spawned instances only receive the defaults that were
# listed at compile time, so an uncompiled change shows on the default object but not in the game.
# Sources (not in the repo, see _local/): textures from gen_combat_textures.py; gunshots cut by slice_gunshots.py from
# The Free Firearm Sound Library (CC0, opengameart.org/content/the-free-firearm-sound-library); impacts from
# Kenney Impact Sounds 1.0 (CC0, kenney.nl/assets/impact-sounds). Sound Cues are built with VibeUE's SoundCueService.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/setup_combat.py"
import os

import unreal

ROOT = "/Game/KochSimulator/Combat"
TEX, MAT, AUDIO = f"{ROOT}/Textures", f"{ROOT}/Materials", f"{ROOT}/Audio"
AI = "/Game/KochSimulator/AI"
WEAPONS = "/Game/KochSimulator/Weapons"
ANIMS = "/Game/Characters/Mannequins/Anims"

LOCAL = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "_local")
TEX_SRC = os.path.join(LOCAL, "generated", "combat_textures")
SHOT_SRC = os.path.join(LOCAL, "generated", "combat_audio")
IMPACT_SRC = os.path.join(LOCAL, "downloads", "kenney_impact", "extracted", "Audio")



def L(path):
    return unreal.EditorAssetLibrary.load_asset(path)


def exists(path):
    return unreal.EditorAssetLibrary.does_asset_exist(path)


def create_asset(name, folder, cls, factory):
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)


def save(asset):
    """Saves, or warns when the file is read-only (an LFS-lockable asset that is not locked)."""
    filename = unreal.SystemLibrary.get_system_path(asset)
    if filename and os.path.isfile(filename) and not os.access(filename, os.W_OK):
        unreal.log_warning(f"setup_combat: {asset.get_name()} is read-only (not locked): changed in memory only")
        return
    unreal.EditorAssetLibrary.save_loaded_asset(asset, False)


def cdo(bp):
    return unreal.get_default_object(bp.generated_class())


def import_file(src, dest, name):
    """Imports src as dest/name unless it is already there."""
    path = f"{dest}/{name}"
    if exists(path):
        return L(path)
    if not os.path.isfile(src):
        raise FileNotFoundError(f"{src}: run gen_combat_textures.py / slice_gunshots.py or fetch the CC0 packs first")
    task = unreal.AssetImportTask()
    task.filename, task.destination_path, task.destination_name = src, dest, name
    task.automated, task.save, task.replace_existing = True, True, False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return L(path)


# ---------------------------------------------------------------- textures

def decal_textures(name):
    """Mask (R thickness, G dust, A opacity) and normal map of one decal."""
    mask = import_file(os.path.join(TEX_SRC, f"{name}_M.png"), TEX, f"{name}_M")
    normal = import_file(os.path.join(TEX_SRC, f"{name}_N.png"), TEX, f"{name}_N")
    for tex, compression in ((mask, unreal.TextureCompressionSettings.TC_MASKS), (normal, unreal.TextureCompressionSettings.TC_NORMALMAP)):
        if tex.get_editor_property("compression_settings") != compression or tex.get_editor_property("srgb"):
            tex.set_editor_property("srgb", False)
            tex.set_editor_property("compression_settings", compression)
            save(tex)
    return mask, normal


# ---------------------------------------------------------------- materials

def expr(material, cls, x, y, **props):
    e = unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)
    for key, value in props.items():
        e.set_editor_property(key, value)
    return e


def link(src, out, dst, pin):
    if not unreal.MaterialEditingLibrary.connect_material_expressions(src, out, dst, pin):
        raise RuntimeError(f"material link failed: {src.get_name()}.{out} -> {dst.get_name()}.{pin}")


def color_param(material, name, rgb, y):
    return expr(material, unreal.MaterialExpressionVectorParameter, -900, y, parameter_name=name,
                default_value=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))


def lerp(material, a, b, alpha, alpha_out, x, y):
    e = expr(material, unreal.MaterialExpressionLinearInterpolate, x, y)
    link(a, "", e, "A")
    link(b, "", e, "B")
    link(alpha, alpha_out, e, "Alpha")
    return e


def decal_master(name, textures, build_color, roughness):
    """Deferred decal: opacity = mask alpha x decal lifetime (so SetFadeIn/Out work), normal map, constant roughness."""
    path = f"{MAT}/{name}"
    if exists(path):
        return L(path)
    m = create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)

    mask = expr(m, unreal.MaterialExpressionTextureSampleParameter2D, -900, 0, parameter_name="Mask", texture=textures[0],
                sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    normal = expr(m, unreal.MaterialExpressionTextureSampleParameter2D, -900, 300, parameter_name="Normal", texture=textures[1],
                  sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    unreal.MaterialEditingLibrary.connect_material_property(build_color(m, mask), "", unreal.MaterialProperty.MP_BASE_COLOR)

    life = expr(m, unreal.MaterialExpressionDecalLifetimeOpacity, -600, 180)
    opacity = expr(m, unreal.MaterialExpressionMultiply, -350, 120)
    link(mask, "A", opacity, "A")
    link(life, "", opacity, "B")
    unreal.MaterialEditingLibrary.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)

    rough = expr(m, unreal.MaterialExpressionScalarParameter, -600, 520, parameter_name="Roughness", default_value=roughness)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)

    unreal.MaterialEditingLibrary.recompile_material(m)
    save(m)
    return m


def blood_color(m, mask):
    # fresh blood: bright where thin, almost black where it pools
    thin = color_param(m, "ThinColor", (0.30, 0.008, 0.006), -520)
    thick = color_param(m, "ThickColor", (0.07, 0.0, 0.0), -330)
    return lerp(m, thin, thick, mask, "R", -350, -420)


def hole_color(m, mask):
    # soot-dark surround, pale chipped dust ring (G), black core (R)
    soot = color_param(m, "SootColor", (0.035, 0.03, 0.03), -720)
    chip = color_param(m, "ChipColor", (0.50, 0.48, 0.44), -530)
    core = color_param(m, "CoreColor", (0.008, 0.008, 0.008), -340)
    ring = lerp(m, soot, chip, mask, "G", -550, -620)
    return lerp(m, ring, core, mask, "R", -350, -420)


def decal_instance(name, parent, textures, roughness=None):
    path = f"{MAT}/{name}"
    mi = L(path) if exists(path) else create_asset(name, MAT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, "Mask", textures[0])
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, "Normal", textures[1])
    if roughness is not None:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Roughness", roughness)
    unreal.MaterialEditingLibrary.update_material_instance(mi)
    save(mi)
    return mi


# ---------------------------------------------------------------- audio

def attenuation(name, inner, falloff):
    """Full volume inside `inner` cm, natural (dB-linear) falloff over the next `falloff` cm."""
    path = f"{AUDIO}/{name}"
    a = L(path) if exists(path) else create_asset(name, AUDIO, unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
    s = a.get_editor_property("attenuation")
    s.set_editor_property("distance_algorithm", unreal.AttenuationDistanceModel.NATURAL_SOUND)
    s.set_editor_property("attenuation_shape_extents", unreal.Vector(inner, 0.0, 0.0))
    s.set_editor_property("falloff_distance", falloff)
    a.set_editor_property("attenuation", s)
    save(a)
    return path


def sound_cue(name, wave_files, src_dir, attenuation_path, volume=1.0, pitch=(0.96, 1.04)):
    """Random pick of the waves, then a little pitch/volume variation so repeats never sound identical."""
    path = f"{AUDIO}/{name}"
    waves = [import_file(os.path.join(src_dir, f), AUDIO, "A_" + os.path.splitext(f)[0]) for f in wave_files]
    if exists(path):
        return L(path)
    if not unreal.SoundCueService.create_sound_cue(path, "").success:
        raise RuntimeError(f"could not create {path}")
    for i, wave in enumerate(waves):
        unreal.SoundCueService.add_wave_player_node(path, wave.get_path_name().split(".")[0], -600, i * 130)
    unreal.SoundCueService.add_random_node(path, -330, 0)
    unreal.SoundCueService.add_modulator_node(path, -120, 0)
    nodes = unreal.SoundCueService.list_nodes(path)
    players = [i for i, n in enumerate(nodes) if "WavePlayer" in n.node_class]
    random = next(i for i, n in enumerate(nodes) if "Random" in n.node_class)
    modulator = next(i for i, n in enumerate(nodes) if "Modulator" in n.node_class)
    for slot, player in enumerate(players):
        if not unreal.SoundCueService.connect_nodes(path, random, player, slot):
            raise RuntimeError(f"{name}: wave {slot} not connected")
    if not unreal.SoundCueService.connect_nodes(path, modulator, random, 0):
        raise RuntimeError(f"{name}: random not connected")
    for prop, value in (("PitchMin", pitch[0]), ("PitchMax", pitch[1]), ("VolumeMin", 0.9), ("VolumeMax", 1.0)):
        unreal.SoundCueService.set_node_property(path, modulator, prop, str(value))
    unreal.SoundCueService.set_root_node(path, modulator)
    unreal.SoundCueService.set_volume_multiplier(path, volume)
    unreal.SoundCueService.set_attenuation(path, attenuation_path)
    unreal.SoundCueService.save_sound_cue(path)
    return L(path)


def kenney(prefix):
    return [f"{prefix}_{i:03d}.ogg" for i in range(5)]


# ---------------------------------------------------------------- data and Blueprints

def impact_effect(decals, radius, sound):
    e = unreal.KochImpactEffect()
    e.set_editor_property("decals", decals)
    e.set_editor_property("decal_radius", unreal.Vector2D(radius[0], radius[1]))
    e.set_editor_property("sound", sound)
    return e


def child_bp(folder, name, parent_class):
    path = f"{folder}/{name}"
    if exists(path):
        return L(path)
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", parent_class)
    return create_asset(name, folder, unreal.Blueprint, f)


def apply_defaults(bp):
    """Compiles (see the header note) and saves a Blueprint whose class defaults were just changed."""
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    save(bp)


def set_bullet(weapon_cdo, damage, effects):
    spec = weapon_cdo.get_editor_property("bullet_spec")
    spec.set_editor_property("damage", damage)
    spec.set_editor_property("impact_effects", effects)
    weapon_cdo.set_editor_property("bullet_spec", spec)


def anims(folder, names):
    return [L(f"{ANIMS}/{folder}/{n}") for n in names]


def main():
    # decals
    splat_tex = [decal_textures(f"T_BloodSplat_{i:02d}") for i in range(1, 5)]
    pool_tex = [decal_textures(f"T_BloodPool_{i:02d}") for i in range(1, 3)]
    wound_tex = decal_textures("T_BloodWound_01")
    hole_tex = [decal_textures(f"T_BulletHole_{i:02d}") for i in range(1, 4)]

    m_blood = decal_master("M_Decal_Blood", splat_tex[0], blood_color, 0.12)
    m_hole = decal_master("M_Decal_BulletHole", hole_tex[0], hole_color, 0.9)
    splats = [decal_instance(f"MI_Decal_BloodSplat_{i:02d}", m_blood, t) for i, t in enumerate(splat_tex, 1)]
    pools = [decal_instance(f"MI_Decal_BloodPool_{i:02d}", m_blood, t, 0.06) for i, t in enumerate(pool_tex, 1)]
    wound = decal_instance("MI_Decal_BloodWound_01", m_blood, wound_tex)
    holes = [decal_instance(f"MI_Decal_BulletHole_{i:02d}", m_hole, t) for i, t in enumerate(hole_tex, 1)]

    # audio: a rifle shot carries a few hundred metres, an impact a few tens
    att_shot = attenuation("ATT_Gunshot", 800.0, 40000.0)
    att_impact = attenuation("ATT_Impact", 200.0, 5000.0)
    sc_ak = sound_cue("A_AK_Fire_Cue", [f"AK_Shot_{i:02d}.wav" for i in range(1, 5)], SHOT_SRC, att_shot, 1.0, (0.97, 1.03))
    sound_cue("A_Pistol_Fire_Cue", [f"Pistol_Shot_{i:02d}.wav" for i in range(1, 4)], SHOT_SRC, att_shot, 1.0, (0.97, 1.03))
    sc_default = sound_cue("A_Impact_Default_Cue", kenney("impactMining"), IMPACT_SRC, att_impact, 0.9, (0.9, 1.15))
    sc_metal = sound_cue("A_Impact_Metal_Cue", kenney("impactMetal_light"), IMPACT_SRC, att_impact, 0.9, (0.9, 1.15))
    sc_wood = sound_cue("A_Impact_Wood_Cue", kenney("impactWood_medium"), IMPACT_SRC, att_impact, 0.9, (0.9, 1.15))
    sc_glass = sound_cue("A_Impact_Glass_Cue", kenney("impactGlass_light"), IMPACT_SRC, att_impact, 0.9, (0.9, 1.15))
    sc_flesh = sound_cue("A_Impact_Flesh_Cue", kenney("impactSoft_heavy"), IMPACT_SRC, att_impact, 1.0, (0.85, 1.1))

    # impact effect set
    da_path = f"{ROOT}/DA_KochImpactEffects"
    if exists(da_path):
        effects = L(da_path)
    else:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.KochImpactEffectSet)
        effects = create_asset("DA_KochImpactEffects", ROOT, unreal.KochImpactEffectSet, factory)
    effects.set_editor_property("default", impact_effect(holes, (3.0, 5.5), sc_default))
    effects.set_editor_property("surfaces", {
        unreal.KochSurface.CONCRETE: impact_effect(holes, (3.0, 5.5), sc_default),
        unreal.KochSurface.BRICK: impact_effect(holes, (3.0, 5.5), sc_default),
        unreal.KochSurface.METAL: impact_effect(holes, (1.5, 2.5), sc_metal),
        unreal.KochSurface.WOOD: impact_effect(holes, (2.0, 3.5), sc_wood),
        unreal.KochSurface.GLASS: impact_effect(holes, (2.0, 3.5), sc_glass),
        unreal.KochSurface.FLESH: impact_effect([wound], (2.5, 4.0), sc_flesh),
    })
    effects.set_editor_property("blood_splatter_decals", splats)
    effects.set_editor_property("blood_pool_decals", pools)
    save(effects)

    # player rifle: simulated 7.62x39. AimVariance is the resting hip spread (cone half-angle, degrees); aiming down
    # sights scales it by 0.15 (UKochStanceComponent), sustained fire adds up to 2.5 (FKochRecoilSpec).
    ak = L(f"{WEAPONS}/BP_Rifle_AK")
    c = cdo(ak)
    c.set_editor_property("use_ballistics", True)
    c.set_editor_property("aim_variance", 1.0)
    c.set_editor_property("fire_sound", sc_ak)
    c.set_editor_property("sight_offset", unreal.Vector(-38.0, 0.0, 6.3))  # optic window of the template rifle, tuned by eye
    set_bullet(c, 55.0, effects)
    del c  # no Python reference to the old default object across the compile
    apply_defaults(ak)

    # guard rifle: same gun, weaker hits and a wider cone so a fight lasts longer than one burst
    guard_rifle = child_bp(WEAPONS, "BP_Rifle_AK_Guard", ak.generated_class())
    c = cdo(guard_rifle)
    c.set_editor_property("aim_variance", 1.5)
    set_bullet(c, 16.0, effects)
    del c
    apply_defaults(guard_rifle)

    # guard: the template NPC (mesh, anim BP, AI controller, StateTree) on the AKochGuard class
    guard_path = f"{AI}/BP_KochGuard"
    if not exists(guard_path):
        unreal.EditorAssetLibrary.duplicate_asset("/Game/Variant_Shooter/Blueprints/AI/BP_ShooterNPC", guard_path)
        unreal.BlueprintEditorLibrary.reparent_blueprint(L(guard_path), unreal.KochGuard)
        unreal.BlueprintEditorLibrary.compile_blueprint(L(guard_path))
    guard = L(guard_path)
    c = cdo(guard)
    c.set_editor_property("weapon_class", guard_rifle.generated_class())
    c.set_editor_property("deferred_destruction_time", 0.0)
    c.set_editor_property("aim_variance_half_angle", 4.0)
    reaction = c.get_editor_property("hit_reaction")
    reaction.set_editor_property("hit_anims_front", anims("Rifle/HitReact", [f"MM_HitReact_Front_Lgt_{i:02d}" for i in range(1, 5)] + ["MM_HitReact_Front_Med_01", "MM_HitReact_Front_Med_02"]))
    reaction.set_editor_property("hit_anims_back", anims("Rifle/HitReact", ["MM_HitReact_Back_Med_01"]))
    reaction.set_editor_property("death_anims_front", anims("Death", ["MM_Death_Front_01", "MM_Death_Front_02", "MM_Death_Front_03"]))
    reaction.set_editor_property("death_anims_back", anims("Death", ["MM_Death_Back_01"]))
    reaction.set_editor_property("blood_effects", effects)
    del c, reaction
    apply_defaults(guard)

    unreal.log(f"setup_combat: done ({len(splats)} splatters, {len(holes)} bullet holes, guard at {guard_path})")


main()
