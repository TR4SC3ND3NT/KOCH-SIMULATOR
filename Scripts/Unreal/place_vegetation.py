# UE 5.8 editor script (R4 -> R1/everyone): real vegetation over the greybox placeholders: Epic PVE sample trees (see
# PVE_ASSETS) and, as fallback, the split Poly Haven
# plants (Scripts/Blender/split_polyhaven.py; CC0, see Saved/ThirdParty/PolyHaven/*/SOURCE.json) as Nanite meshes with
# their 2k textures and two materials (opaque bark, masked two-sided foliage), then puts one plant on every placeholder
# whose ue_asset tag is in MAPPING: same base point, uniform scale to the placeholder's height, deterministic yaw.
# Placeholders stay in the level (R1's data and collision proxy) but are hidden. Re-running replaces the plants.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/place_vegetation.py" [EXPORT_DIR] [SPLIT_DIR] [--reimport]
import hashlib
import json
import os
import sys

import unreal

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
EXPORT = ARGS[0] if len(ARGS) > 0 else os.path.join(REPO, "Saved", "GreyboxExport")
SPLIT = ARGS[1] if len(ARGS) > 1 else os.path.join(REPO, "Saved", "ThirdParty", "PolyHaven", "_split")
PH = os.path.dirname(SPLIT)
ROOT = "/Game/KochSimulator/Environment/Vegetation/PolyHaven"
LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
TAG = "KochVegetation"

# Epic's Procedural Vegetation Editor samples shipped with UE 5.8 (Nanite assemblies, Dynamic Wind skeletal meshes;
# need r.Nanite.Foliage). Denser and closer to the campus species than the Poly Haven forest fir, which stays as a
# fallback (SM_PH_* keys) for when the plugin is off.
PVE = "/ProceduralVegetationEditor/SampleAssets/StarterContent"
PVE_ASSETS = {"PVE_Conifer": f"{PVE}/ConiferTree_01/PVE_Conifer_01",
              "PVE_Tree": f"{PVE}/DeciduousTree_01/PVE_Deciduous_Tree_01",
              "PVE_Shrub": f"{PVE}/Deciduous_Shrub_01/PVE_Deciduous_Shrub_01"}
# placeholder ue_asset -> plant variants (picked by a hash of the placeholder name)
MAPPING = {
    "tree_cone": ["PVE_Conifer"], "conifer_small": ["PVE_Conifer"], "spruce_blue": ["PVE_Conifer"],
    "tree_round": ["PVE_Tree"], "tree_ellipsoid": ["PVE_Tree"], "tree_deciduous_young": ["PVE_Tree"],
    "tree_deciduous_whitewashed": ["PVE_Tree"],
    "shrub_rose": ["PVE_Shrub"], "shrub_rose_red": ["PVE_Shrub"], "rose_bush": ["PVE_Shrub"], "shrub_loose": ["PVE_Shrub"],
    # remaining R1 placeholder kinds (playtest 2026-10-27: still drawn as cones/icosahedra)
    "juniper_tree_multistem": ["PVE_Conifer"], "juniper_tree_leaning": ["PVE_Conifer"], "pine_black": ["PVE_Conifer"],
    "thuja_columnar_young": ["PVE_Conifer"], "conifer_clipped_small": ["PVE_Conifer"], "elm_whitewashed": ["PVE_Tree"],
    "shrub_clipped_round": ["PVE_Shrub"],
}
SCALE_LIMITS = (0.2, 2.0)   # beyond this the plant reads wrong; keep the placeholder's footprint roughly right
SCALE_JITTER = 0.12         # +-12 % so identical samples don't read as clones

# material per asset: (texture prefix, foliage slot name fragments) -> slots containing one of them use the foliage MI
MATERIALS = {
    "fir_tree_01": {"Bark": ("fir_tree_01_bark", False), "Twig": ("fir_tree_01_twig", True), "foliage_slots": ["twig"]},
    "shrub_02": {"Leaf": ("shrub_02", True), "foliage_slots": ["shrub_02"]},
}


def tune_wind_tick(a):
    """PVE trees are skeletal (Dynamic Wind bones). Default ALWAYS_TICK_POSE animated all ~385 every frame, seen or
    not; tick only when rendered, and let update-rate optimisation thin out the far ones (UE's URO: fewer pose
    updates with screen size). Saves game + render thread ms (perf capture 2026-10-28: RT-bound at 17.7 ms)."""
    comp = a.get_editor_property("skeletal_mesh_component")
    comp.set_editor_property("visibility_based_anim_tick_option",
                             unreal.VisibilityBasedAnimTickOption.ONLY_TICK_POSE_WHEN_RENDERED)
    comp.set_editor_property("enable_update_rate_optimizations", True)


def hashed(name, n):
    return int(hashlib.md5(name.encode()).hexdigest(), 16) % n


def import_textures(tools, asset):
    tex_dir = os.path.join(PH, asset, "textures")
    tasks = []
    for f in sorted(os.listdir(tex_dir)):
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(tex_dir, f))
        t.set_editor_property("destination_path", f"{ROOT}/Textures")
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", False)
        tasks.append(t)
    tools.import_asset_tasks(tasks)
    out = {}
    for t in tasks:
        tex = next((o for o in t.get_objects() if isinstance(o, unreal.Texture2D)), None)
        if tex is None:
            continue
        stem = os.path.splitext(os.path.basename(t.get_editor_property("filename")))[0]
        kind = stem.rsplit("_", 1)[0].rsplit("_", 1)[-1]   # ..._nor_gl_2k -> gl, ..._diff_2k -> diff
        kind = "nor" if "_nor_" in stem else kind
        if kind == "nor":
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property("srgb", False)
        elif kind in ("rough", "alpha", "mask", "disp"):
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
            tex.set_editor_property("srgb", False)
        out[stem] = tex
    return out


def fix_sampler_defaults(mat, grey_default):
    """Each TextureSampleParameter2D needs a default texture of its sampler type, or the material fails to compile
    ("Sampler type is Normal, should be Color for DefaultTexture") and renders as the default grid."""
    st = unreal.MaterialSamplerType
    normal = unreal.EditorAssetLibrary.load_asset("/Engine/EngineMaterials/DefaultNormal")
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
        if isinstance(e, unreal.MaterialExpressionTextureSampleParameter2D):
            kind = e.get_editor_property("sampler_type")
            if kind == st.SAMPLERTYPE_NORMAL:
                e.set_editor_property("texture", normal)
            elif kind == st.SAMPLERTYPE_LINEAR_GRAYSCALE:
                e.set_editor_property("texture", grey_default)
    unreal.MaterialEditingLibrary.recompile_material(mat)


def master(tools, name, masked):
    path = f"{ROOT}/Materials/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    mel = unreal.MaterialEditingLibrary
    mat = tools.create_asset(name, f"{ROOT}/Materials", unreal.Material, unreal.MaterialFactoryNew())

    def tex_param(pname, y, sampler):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -700, y)
        e.set_editor_property("parameter_name", pname)
        e.set_editor_property("sampler_type", sampler)
        return e

    base = tex_param("BaseColorTex", 0, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    nrm = tex_param("NormalTex", 300, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    rough = tex_param("RoughnessTex", 600, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    tint = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -700, -250)
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -350, 0)
    mel.connect_material_expressions(base, "RGB", mul, "A")
    mel.connect_material_expressions(tint, "", mul, "B")
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(nrm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(rough, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    if masked:
        alpha = tex_param("OpacityTex", 900, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
        mel.connect_material_property(alpha, "R", unreal.MaterialProperty.MP_OPACITY_MASK)
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        mat.set_editor_property("two_sided", True)
    mat.set_editor_property("used_with_nanite", True)
    mel.recompile_material(mat)
    return mat


def instance(tools, name, parent, texs, prefix, masked):
    path = f"{ROOT}/Materials/{name}"
    mi = (unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else
          tools.create_asset(name, f"{ROOT}/Materials", unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew()))
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_parent(mi, parent)

    def pick(kind):
        return next((t for s, t in texs.items() if s.startswith(prefix) and f"_{kind}_" in s + "_"), None)

    for param, kind in (("BaseColorTex", "diff"), ("NormalTex", "nor"), ("RoughnessTex", "rough")) + (
            (("OpacityTex", "alpha"),) if masked else ()):
        tex = pick(kind)
        if tex is not None:
            mel.set_material_instance_texture_parameter_value(mi, param, tex)
        else:
            unreal.log_warning(f"place_vegetation: no {kind} texture for {prefix}")
    mel.update_material_instance(mi)
    return mi


def import_meshes(tools, split):
    # 4M-tri firs: import once; --reimport forces a fresh import of every split FBX
    out = {n: unreal.EditorAssetLibrary.load_asset(f"{ROOT}/Meshes/{n}") for n in split
           if "--reimport" not in sys.argv and unreal.EditorAssetLibrary.does_asset_exist(f"{ROOT}/Meshes/{n}")}
    tasks = []
    for name in (n for n in split if n not in out):
        p = unreal.InterchangeGenericAssetsPipeline()
        mp = p.get_editor_property("mesh_pipeline")
        mp.set_editor_property("build_nanite", True)
        mp.set_editor_property("collision", False)   # the hidden placeholder keeps its collision (trunk/crown proxy)
        mp.set_editor_property("generate_lightmap_u_vs", False)
        p.get_editor_property("material_pipeline").set_editor_property("import_materials", False)
        p.set_editor_property("asset_name", name)
        ov = unreal.InterchangePipelineStackOverride()
        ov.add_pipeline(p)
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(SPLIT, f"{name}.fbx"))
        t.set_editor_property("destination_path", f"{ROOT}/Meshes")
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", False)
        t.set_editor_property("options", ov)
        tasks.append(t)
    if tasks:
        tools.import_asset_tasks(tasks)
    for t in tasks:
        out[t.get_editor_property("destination_name") or
            os.path.splitext(os.path.basename(t.get_editor_property("filename")))[0]] = next(
            (o for o in t.get_objects() if isinstance(o, unreal.StaticMesh)), None)
    return out


def main():
    with open(os.path.join(EXPORT, "manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    with open(os.path.join(SPLIT, "split.json"), encoding="utf-8") as fh:
        split = json.load(fh)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    m_bark, m_leaf = master(tools, "M_PH_Bark", False), master(tools, "M_PH_Foliage", True)

    meshes = import_meshes(tools, split)
    for asset, spec in MATERIALS.items():
        texs = import_textures(tools, asset)
        grey = next((t for s, t in texs.items() if "_rough_" in s + "_"), None)
        if grey is not None:
            for m in (m_bark, m_leaf):
                fix_sampler_defaults(m, grey)
        mis = {}
        for key, (prefix, masked) in ((k, v) for k, v in spec.items() if k != "foliage_slots"):
            mis[masked] = instance(tools, f"MI_PH_{''.join(p.capitalize() for p in asset.split('_'))}_{key}",
                                   m_leaf if masked else m_bark, texs, prefix, masked)
        for name, sm in meshes.items():
            if sm is None or split[name]["asset"] != asset:
                continue
            sm.modify()
            for i, sl in enumerate(sm.get_editor_property("static_materials")):
                slot = str(sl.get_editor_property("material_slot_name")).lower()
                leafy = any(f in slot for f in spec["foliage_slots"])
                sm.set_material(i, mis.get(leafy) or mis.get(True))
    unreal.EditorAssetLibrary.save_directory(ROOT, False, True)

    # place into the campus level: after an editor restart the template's startup map is open
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    # World Partition: after a level (re)load the editor only holds actors in loaded regions; load every actor desc so
    # all placeholders are reachable (DevelopmentOnly API, editor-side)
    wpl = unreal.WorldPartitionBlueprintLibrary
    res = wpl.get_actor_descs()
    descs = res[1] if isinstance(res, tuple) else res
    wpl.load_actors([d.get_editor_property("guid") for d in descs])
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    eas.destroy_actors([a for a in actors if a.actor_has_tag(TAG)])
    by_label = {a.get_actor_label(): a for a in actors if a.actor_has_tag("KochGreybox")}
    # asset key -> (mesh, height m, base z offset m at scale 1)
    plants = {n: (sm, split[n]["height_m"], 0.0) for n, sm in meshes.items() if sm is not None}
    for key, path in PVE_ASSETS.items():
        sk = unreal.EditorAssetLibrary.load_asset(path)
        if sk is not None:
            b = sk.get_bounds()
            plants[key] = (sk, 2 * b.box_extent.z / 100.0, (b.origin.z - b.box_extent.z) / 100.0)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "owner_removed.json"), encoding="utf-8") as fh:
        removed = set(json.load(fh))   # not on the real site (owner review); apply_removals.py hides the placeholders
    placed = 0
    for e in man["instances"]:
        variants = MAPPING.get(e.get("ue_asset") or "")
        if not variants or e["name"] in removed:
            continue
        name = variants[hashed(e["name"], len(variants))]
        ph = by_label.get(e["name"])
        if name not in plants or ph is None:
            continue
        mesh, height, base = plants[name]
        (x0, y0, z0), (x1, y1, z1) = man["meshes"][e["mesh"]]["bounds_m"]
        jitter = 1.0 + SCALE_JITTER * (hashed(e["name"] + "s", 2001) / 1000.0 - 1.0)
        scale = min(max((z1 - z0) / height * jitter, SCALE_LIMITS[0]), SCALE_LIMITS[1])
        # placeholder base, UE cm; lift by the mesh's own below-pivot depth so the trunk base lands on it
        loc = unreal.Vector(e["loc"][0], e["loc"][1], e["loc"][2] + (z0 - base * scale) * 100.0)
        a = eas.spawn_actor_from_object(mesh, loc, unreal.Rotator(roll=0, pitch=0, yaw=hashed(e["name"] + "yaw", 360)))
        a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        a.set_actor_label(f"VEG_{e['name']}")
        a.set_folder_path(f"Vegetation/{e['zone']}")
        a.set_editor_property("tags", [unreal.Name(TAG), unreal.Name(f"Replaces:{e['name']}")])
        if isinstance(a, unreal.StaticMeshActor):
            a.get_editor_property("static_mesh_component").set_mobility(unreal.ComponentMobility.STATIC)
        elif isinstance(a, unreal.SkeletalMeshActor):
            tune_wind_tick(a)
        ph.modify()   # external (OFPA) actor: without Modify its package is not dirtied and the hide is lost on save
        comp = ph.get_editor_property("static_mesh_component")
        comp.modify()
        comp.set_visibility(False, True)
        ph.set_actor_hidden_in_game(True)
        placed += 1
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"place_vegetation: {len([m for m in meshes.values() if m])} meshes, {placed} plants placed")


main()
