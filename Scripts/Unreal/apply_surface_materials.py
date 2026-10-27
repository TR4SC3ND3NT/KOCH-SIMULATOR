# UE 5.8 editor script (R4 -> everyone): PBR surfaces for the greybox. Re-parents the MI_<slot> instances made by
# apply_greybox_materials.py onto M_SurfacePBR with CC0 Poly Haven texture sets (Saved/ThirdParty/PolyHaven/Textures,
# SOURCE.json per set: licence, author, real size). Texture scale is physical: greybox UVs are world metres (ue_prep
# box_uvs, 1 UV = 1 m), so UV / size_m tiles each set at its true size. Painted/rendered surfaces keep R1's palette
# colour: base = lerp(texture, tint * lum / mean_lum, TintAmount), so the paint colour stays and the texture adds
# plaster/brick variation. Slots not in SURFACES keep the flat M_GreyboxMaster look. Idempotent.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/apply_surface_materials.py" [EXPORT_DIR] [TEX_DIR]
import json
import os
import sys

import unreal

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EXPORT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "Saved", "GreyboxExport")
TEXDIR = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "Saved", "ThirdParty", "PolyHaven", "Textures")
MAT_ROOT = "/Game/KochSimulator/Greybox/Materials"
TEX_ROOT = "/Game/KochSimulator/Environment/Surfaces/PolyHaven"
MASTER = f"{MAT_ROOT}/M_SurfacePBR"

PAINT = ("plastered_wall", 1.0)   # even fine-grain stucco; painted_plaster_wall read as stained once tinted
# slot -> (texture set, TintAmount 0 = texture colour .. 1 = R1 palette colour); optional 3rd: metallic
SURFACES = {s: PAINT for s in (
    "M_Paint_White", "M_Render_White", "M_Render_Beige", "M_Render_Pink", "M_Paint_Maroon", "M_Paint_Sage",
    "M_Paint_Yellow", "M_Paint_Blue", "M_Paint_Brown", "M_Paint_Greige", "M_Paint_RedPink", "M_Paint_Orange",
    "M_Fascia_Beige")}
SURFACES.update({
    "M_Context_Facade": ("plastered_wall", 1.0), "M_Render_Shuba_Grey": ("white_rough_plaster", 1.0),
    "M_Tile_Brick_Red": ("red_brick_03", 0.25), "M_Tile_Brick_Maroon": ("red_brick_03", 0.6),
    "M_Block_RockFace_Red": ("castle_brick_02_red", 0.3),
    "M_Paver_Clover_Grey": ("hexagonal_concrete_paving", 0.5), "M_Paver_Clover_GreyPink": ("hexagonal_concrete_paving", 0.5),
    "M_Paver_GreyPink": ("hexagonal_concrete_paving", 0.5), "M_Paver_CircleDisc": ("hexagonal_concrete_paving", 0.5),
    "M_Paver_Herringbone_Grey": ("pavement_02", 0.5), "M_Paving_Generic": ("pavement_03", 0.5),
    "M_Paving_Diamond_Tile": ("floor_tiles_08", 0.5), "M_Paving_Diamond_Tile_Pink": ("floor_tiles_08", 0.6),
    "M_Paving_Octagon_Tile": ("floor_tiles_08", 0.5),
    "M_Asphalt": ("asphalt_02", 0.0), "M_Concrete": ("concrete_floor_02", 0.3), "M_Concrete_Precast": ("concrete_floor_02", 0.3),
    "M_Ground_Grass": ("leafy_grass", 0.6),   # leafy_grass alone reads as late-summer dry lawn
    "M_Granite_Red": ("granite_tile", 0.6), "M_Granite_Pink": ("granite_tile", 0.6), "M_Granite_Beige": ("granite_tile", 0.6),
    "M_Wood_Stained": ("wood_floor", 0.55), "M_Wood_Oak_Light": ("weathered_brown_planks", 0.6),
    "M_Steel_Paint_Dark": ("metal_plate", 1.0), "M_Steel_Paint_Green": ("metal_plate", 1.0),
    "M_Steel_Paint_Maroon": ("metal_plate", 1.0), "M_Steel_Paint_Grey": ("metal_plate", 1.0),
    "M_Steel_Paint_YellowBlack": ("metal_plate", 1.0), "M_Wrought_Iron": ("metal_plate", 1.0),
    "M_Sheet_Red": ("corrugated_iron", 1.0), "M_Sheet_Brown": ("corrugated_iron", 1.0),
    "M_Sheet_DarkGrey": ("corrugated_iron", 1.0), "M_Sheet_Grey": ("corrugated_iron", 1.0),
    "M_Gravel_Compacted": ("gravelly_sand", 0.3), "M_Sand": ("gravelly_sand", 0.3),
    "M_Soil_Mulch": ("forrest_ground_01", 0.2), "M_Ground_Dirt": ("forrest_ground_01", 0.2),
    # hedge core under the leaf shells: seamless tile made from the owner's close-up of the garden hedge (dusty privet)
    "M_Hedge_Foliage": ("hedge_leaves_photo", 0.0),
})
ALBEDO_MIN, ALBEDO_MAX = 0.03, 0.75   # same physical clamp as apply_greybox_materials.py
# sRGB tints that differ from R1's review palette, from reference photos (reported to R1, palette untouched)
COLOUR_OVERRIDES = {"M_Wood_Stained": (0.78, 0.48, 0.24)}   # gazebo ceiling/benches: honey varnished pine (2022 tour photo)
# slot -> (MacroAmount, MacroSizeM): lawns patchy like the owner photos (dry/lush), hard surfaces subtle
MACRO = {"M_Ground_Grass": (0.35, 6.0), "M_Asphalt": (0.15, 10.0), "M_Soil_Mulch": (0.25, 5.0), "M_Hedge_Foliage": (0.15, 3.0)}
MACRO_DEFAULT = (0.08, 8.0)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


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


def build_master(tools):
    """(Re)builds the graph every run, in place, so the MIs keep their parent and graph edits are reproducible."""
    mel = unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        mat = unreal.EditorAssetLibrary.load_asset(MASTER)
        mat.modify()
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_SurfacePBR", MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())

    def expr(cls, x, y, **props):
        e = mel.create_material_expression(mat, cls, x, y)
        for k, v in props.items():
            e.set_editor_property(k, v)
        return e

    def link(a, out, b, inp):
        mel.connect_material_expressions(a, out, b, inp)

    S, V = unreal.MaterialExpressionScalarParameter, unreal.MaterialExpressionVectorParameter
    tex0 = expr(unreal.MaterialExpressionTextureCoordinate, -2400, 300)
    # WorldUV (static switch, for level-side fix boxes built from the engine cube, whose UVs are 0..1 per face):
    # box projection in metres from world position, axis picked by the dominant vertex normal, same rule as ue_prep
    wpos = expr(unreal.MaterialExpressionWorldPosition, -3000, 600)
    wm = expr(unreal.MaterialExpressionDivide, -2800, 600, const_b=100.0)
    link(wpos, "", wm, "A")
    planes = {}
    for key, (r, g, b) in {"xy": (True, True, False), "yz": (False, True, True), "xz": (True, False, True)}.items():
        planes[key] = expr(unreal.MaterialExpressionComponentMask, -2600, 500 + 80 * len(planes), r=r, g=g, b=b, a=False)
        link(wm, "", planes[key], "")
    nrm_ws = expr(unreal.MaterialExpressionVertexNormalWS, -3000, 900)
    nabs = expr(unreal.MaterialExpressionAbs, -2800, 900)
    link(nrm_ws, "", nabs, "")
    nc = {}
    for i, c in enumerate("xyz"):
        nc[c] = expr(unreal.MaterialExpressionComponentMask, -2600, 850 + 60 * i, r=c == "x", g=c == "y", b=c == "z", a=False)
        link(nabs, "", nc[c], "")
    side = expr(unreal.MaterialExpressionIf, -2400, 700)              # |nx| >= |ny| -> YZ plane else XZ
    link(nc["x"], "", side, "A")
    link(nc["y"], "", side, "B")
    link(planes["yz"], "", side, "A > B")
    link(planes["yz"], "", side, "A == B")
    link(planes["xz"], "", side, "A < B")
    nmax = expr(unreal.MaterialExpressionMax, -2400, 900)
    link(nc["x"], "", nmax, "A")
    link(nc["y"], "", nmax, "B")
    boxuv = expr(unreal.MaterialExpressionIf, -2200, 650)             # |nz| >= max(|nx|,|ny|) -> XY plane
    link(nc["z"], "", boxuv, "A")
    link(nmax, "", boxuv, "B")
    link(planes["xy"], "", boxuv, "A > B")
    link(planes["xy"], "", boxuv, "A == B")
    link(side, "", boxuv, "A < B")
    uv0 = expr(unreal.MaterialExpressionStaticSwitchParameter, -1900, 300, parameter_name="WorldUV", default_value=False)
    link(boxuv, "", uv0, "True")
    link(tex0, "", uv0, "False")
    tile = expr(S, -1600, 450, parameter_name="TileSizeM", default_value=2.0)
    uv = expr(unreal.MaterialExpressionDivide, -1400, 350)
    link(uv0, "", uv, "A")
    link(tile, "", uv, "B")
    T2D = unreal.MaterialExpressionTextureSampleParameter2D
    st = unreal.MaterialSamplerType
    diff = expr(T2D, -1150, 0, parameter_name="BaseColorTex", sampler_type=st.SAMPLERTYPE_COLOR)
    nrm = expr(T2D, -1150, 400, parameter_name="NormalTex", sampler_type=st.SAMPLERTYPE_NORMAL)
    rough = expr(T2D, -1150, 700, parameter_name="RoughnessTex", sampler_type=st.SAMPLERTYPE_LINEAR_GRAYSCALE)
    for t in (diff, nrm, rough):
        link(uv, "", t, "UVs")
    # painted = Tint * lum(tex) / MeanLum
    lumw = expr(unreal.MaterialExpressionConstant3Vector, -1150, -200, constant=unreal.LinearColor(0.2126, 0.7152, 0.0722, 1))
    lum = expr(unreal.MaterialExpressionDotProduct, -850, -150)
    link(diff, "RGB", lum, "A")
    link(lumw, "", lum, "B")
    mean = expr(S, -850, -50, parameter_name="TexMeanLum", default_value=0.5)
    rel = expr(unreal.MaterialExpressionDivide, -650, -150)
    link(lum, "", rel, "A")
    link(mean, "", rel, "B")
    # DetailContrast < 1 flattens the texture's light/dark patches so paint reads as one colour with subtle relief
    one = expr(unreal.MaterialExpressionConstant, -650, -50, r=1.0)
    contrast = expr(S, -650, 50, parameter_name="DetailContrast", default_value=1.0)
    relc = expr(unreal.MaterialExpressionLinearInterpolate, -500, -100)
    link(one, "", relc, "A")
    link(rel, "", relc, "B")
    link(contrast, "", relc, "Alpha")
    tint = expr(V, -650, -300, parameter_name="Tint", default_value=unreal.LinearColor(0.5, 0.5, 0.5, 1))
    painted = expr(unreal.MaterialExpressionMultiply, -350, -200)
    link(tint, "", painted, "A")
    link(relc, "", painted, "B")
    amount = expr(S, -450, 0, parameter_name="TintAmount", default_value=1.0)
    base = expr(unreal.MaterialExpressionLinearInterpolate, -250, -50)
    link(diff, "RGB", base, "A")
    link(painted, "", base, "B")
    link(amount, "", base, "Alpha")
    rmul = expr(S, -850, 850, parameter_name="RoughnessMul", default_value=1.0)
    rr = expr(unreal.MaterialExpressionMultiply, -650, 750)
    link(rough, "R", rr, "A")
    link(rmul, "", rr, "B")
    metal = expr(S, -650, 950, parameter_name="Metallic", default_value=0.0)
    # macro variation: large soft brightness patches (engine T_Default_MacroVariation at MacroSizeM) break tiling and
    # give lawns their dry/lush patches; base *= lerp(1 - MacroAmount, 1 + MacroAmount, macro)
    msize = expr(S, -1600, -600, parameter_name="MacroSizeM", default_value=8.0)
    muv = expr(unreal.MaterialExpressionDivide, -1400, -600)
    link(uv0, "", muv, "A")
    link(msize, "", muv, "B")
    mvar = unreal.EditorAssetLibrary.load_asset("/Engine/EngineMaterials/T_Default_MacroVariation")
    cs = mvar.get_editor_property("compression_settings")
    stype = (st.SAMPLERTYPE_LINEAR_GRAYSCALE if cs == unreal.TextureCompressionSettings.TC_GRAYSCALE else
             st.SAMPLERTYPE_MASKS if cs == unreal.TextureCompressionSettings.TC_MASKS else
             st.SAMPLERTYPE_COLOR if mvar.get_editor_property("srgb") else st.SAMPLERTYPE_LINEAR_COLOR)
    mtex = expr(unreal.MaterialExpressionTextureSample, -1150, -600, texture=mvar, sampler_type=stype)   # must match
    link(muv, "", mtex, "UVs")
    mamt = expr(S, -1150, -400, parameter_name="MacroAmount", default_value=0.1)
    lo = expr(unreal.MaterialExpressionOneMinus, -900, -450)
    link(mamt, "", lo, "")
    hi = expr(unreal.MaterialExpressionAdd, -900, -350, const_a=1.0)
    link(mamt, "", hi, "B")
    mfac = expr(unreal.MaterialExpressionLinearInterpolate, -700, -500)
    link(lo, "", mfac, "A")
    link(hi, "", mfac, "B")
    link(mtex, "R", mfac, "Alpha")
    based = expr(unreal.MaterialExpressionMultiply, -100, -50)
    link(base, "", based, "A")
    link(mfac, "", based, "B")
    mel.connect_material_property(based, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(nrm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(rr, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mat.set_editor_property("used_with_nanite", True)
    mel.recompile_material(mat)
    return mat


def import_set(tools, tex_id):
    d = os.path.join(TEXDIR, tex_id)
    with open(os.path.join(d, "SOURCE.json"), encoding="utf-8") as fh:
        src = json.load(fh)
    out = {}
    for kind, fname in src["maps"].items():
        path = f"{TEX_ROOT}/{tex_id}/T_{tex_id}_{kind}"
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            out[kind] = unreal.EditorAssetLibrary.load_asset(path)
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(d, fname))
        t.set_editor_property("destination_path", f"{TEX_ROOT}/{tex_id}")
        t.set_editor_property("destination_name", f"T_{tex_id}_{kind}")
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", False)
        tools.import_asset_tasks([t])
        tex = next((o for o in t.get_objects() if isinstance(o, unreal.Texture2D)), None)
        if tex is None:
            unreal.log_error(f"apply_surface_materials: {fname} did not import")
            continue
        if kind == "nor":
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property("srgb", False)
        elif kind == "rough":
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
            tex.set_editor_property("srgb", False)
        out[kind] = tex
    return src, out


WORLD_UV_VARIANTS = ("M_Granite_Red", "M_Concrete_Precast", "M_Paver_Clover_Grey")   # used by fix_site.py's cube boxes


def world_uv_variant(tools, slot):
    """MI_<slot>_World: same look as MI_<slot> with the WorldUV switch on, for meshes without metre UVs."""
    mel = unreal.MaterialEditingLibrary
    src = unreal.EditorAssetLibrary.load_asset(f"{MAT_ROOT}/MI_{slot[2:]}")
    name = f"MI_{slot[2:]}_World"
    path = f"{MAT_ROOT}/{name}"
    mi = (unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else
          tools.create_asset(name, MAT_ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()))
    mi.modify()
    mel.set_material_instance_parent(mi, src.get_editor_property("parent"))
    for p in src.get_editor_property("scalar_parameter_values"):
        mel.set_material_instance_scalar_parameter_value(mi, p.get_editor_property("parameter_info").get_editor_property("name"), p.get_editor_property("parameter_value"))
    for p in src.get_editor_property("vector_parameter_values"):
        mel.set_material_instance_vector_parameter_value(mi, p.get_editor_property("parameter_info").get_editor_property("name"), p.get_editor_property("parameter_value"))
    for p in src.get_editor_property("texture_parameter_values"):
        mel.set_material_instance_texture_parameter_value(mi, p.get_editor_property("parameter_info").get_editor_property("name"), p.get_editor_property("parameter_value"))
    mel.set_material_instance_static_switch_parameter_value(mi, "WorldUV", True)
    mel.update_material_instance(mi)
    return mi


def main():
    with open(os.path.join(EXPORT, "materials.json"), encoding="utf-8") as fh:
        colours = json.load(fh)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    master = build_master(tools)
    mel = unreal.MaterialEditingLibrary
    sets = {}
    done = []
    for slot, spec in sorted(SURFACES.items()):
        tex_id, amount = spec[0], spec[1]
        mi_path = f"{MAT_ROOT}/MI_{slot[2:]}"
        if not unreal.EditorAssetLibrary.does_asset_exist(mi_path) or not os.path.isdir(os.path.join(TEXDIR, tex_id)):
            continue
        if tex_id not in sets:
            sets[tex_id] = import_set(tools, tex_id)
            if len(sets) == 1 and "rough" in sets[tex_id][1]:
                fix_sampler_defaults(master, sets[tex_id][1]["rough"])
        src, texs = sets[tex_id]
        mi = unreal.EditorAssetLibrary.load_asset(mi_path)
        mi.modify()
        mel.set_material_instance_parent(mi, master)
        r, g, b = (min(max(srgb_to_linear(c), ALBEDO_MIN), ALBEDO_MAX)
                   for c in COLOUR_OVERRIDES.get(slot) or colours.get(slot, {}).get("base_color", (0.5, 0.5, 0.5)))
        mel.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(r, g, b, 1.0))
        mel.set_material_instance_scalar_parameter_value(mi, "TintAmount", amount)
        mel.set_material_instance_scalar_parameter_value(mi, "DetailContrast", 0.4 if amount >= 0.9 else 1.0)
        macro = MACRO.get(slot, MACRO_DEFAULT)
        mel.set_material_instance_scalar_parameter_value(mi, "MacroAmount", macro[0])
        mel.set_material_instance_scalar_parameter_value(mi, "MacroSizeM", macro[1])
        mel.set_material_instance_scalar_parameter_value(mi, "TileSizeM", float(src["size_m"][0]))
        mel.set_material_instance_scalar_parameter_value(mi, "TexMeanLum", float(src.get("mean_lum", 0.5)))
        mel.set_material_instance_scalar_parameter_value(mi, "Metallic", float(spec[2]) if len(spec) > 2 else 0.0)
        for param, kind in (("BaseColorTex", "diff"), ("NormalTex", "nor"), ("RoughnessTex", "rough")):
            if kind in texs:
                mel.set_material_instance_texture_parameter_value(mi, param, texs[kind])
        mel.update_material_instance(mi)
        done.append(slot)
    for slot in WORLD_UV_VARIANTS:
        world_uv_variant(tools, slot)
    unreal.EditorAssetLibrary.save_directory(MAT_ROOT, False, True)
    unreal.EditorAssetLibrary.save_directory(TEX_ROOT, False, True)
    unreal.log(f"apply_surface_materials: {len(done)} slots on PBR, {len(sets)} texture sets")


main()
