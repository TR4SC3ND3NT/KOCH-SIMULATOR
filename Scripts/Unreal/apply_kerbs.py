# UE 5.8 editor script (R4 -> everyone): painted kerbs. R1's MI_Kerb_Painted_YW is one flat yellow; site kerbs are
# painted in alternating yellow / white bands (owner playtest 2026-10-28). M_KerbStriped: BAND_CM bands along the
# kerb's longer local axis, over the concrete texture, worn where it is dark. Assigned as component override on every actor using the kerb slot. Idempotent.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/apply_kerbs.py"
import unreal

LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
ROOT = "/Game/KochSimulator/Environment/Kerbs"
MASTER = f"{ROOT}/M_KerbStriped"
CONCRETE = "/Game/KochSimulator/Environment/Surfaces/PolyHaven/concrete_floor_02"
SLOTS = ("MI_Kerb_Painted_YW",)
TAG = "KochKerb"

# LP local position cm, LMin/LMax local bounds: the bands run along the kerb's longer local axis (kerb meshes are long
# boxes in their own frame, so tops and sides band alike at any heading); Tl concrete luminance, Mean its mean
HLSL = r"""
float3 ext = LMax - LMin;
float u = ext.x >= ext.y ? LP.x - LMin.x : LP.y - LMin.y;
float band = frac(u / (2.0 * Band));
float3 yellow = float3(0.80, 0.58, 0.04), white = float3(0.78, 0.77, 0.72);
float3 paint = band < 0.5 ? yellow : white;
float rel = Tl / Mean;
float wear = saturate((0.6 - rel) * 4.0);                          // dark pits of the concrete show through the paint
return lerp(paint * lerp(0.85, 1.05, saturate(rel)), float3(0.30, 0.29, 0.27) * rel, wear);
"""
BAND_CM = 50.0


def build(tools, mel):
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        mat = unreal.EditorAssetLibrary.load_asset(MASTER)
        mat.modify()
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_KerbStriped", ROOT, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("used_with_nanite", True)

    def expr(cls, x, y, **props):
        e = mel.create_material_expression(mat, cls, x, y)
        for k, v in props.items():
            e.set_editor_property(k, v)
        return e

    def link(a, out, b, inp):
        if not mel.connect_material_expressions(a, out, b, inp):
            raise RuntimeError(f"apply_kerbs: cannot link {a.get_name()}.{out} -> {b.get_name()}.{inp}")

    def struct(cls, **props):   # 5.8 Python structs take no constructor kwargs
        s = cls()
        for k, v in props.items():
            s.set_editor_property(k, v)
        return s

    custom = expr(unreal.MaterialExpressionCustom, -300, 0, code=HLSL, description="KerbStripes",
                  output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
                  inputs=[struct(unreal.CustomInput, input_name=n) for n in ("LP", "LMin", "LMax", "Tl", "Mean", "Band")])
    link(expr(unreal.MaterialExpressionLocalPosition, -800, -200), "", custom, "LP")
    bounds = expr(unreal.MaterialExpressionObjectLocalBounds, -800, -100)
    link(bounds, "Min", custom, "LMin")
    link(bounds, "Max", custom, "LMax")
    uv = expr(unreal.MaterialExpressionTextureCoordinate, -1100, 200, u_tiling=0.5, v_tiling=0.5)
    diff = expr(unreal.MaterialExpressionTextureSample, -900, 150,
                texture=unreal.EditorAssetLibrary.load_asset(f"{CONCRETE}/T_concrete_floor_02_diff"))
    link(uv, "", diff, "UVs")
    lum = expr(unreal.MaterialExpressionDotProduct, -650, 150)
    link(diff, "RGB", lum, "A")
    link(expr(unreal.MaterialExpressionConstant3Vector, -900, 350,
              constant=unreal.LinearColor(0.2126, 0.7152, 0.0722, 1)), "", lum, "B")
    link(lum, "", custom, "Tl")
    link(expr(unreal.MaterialExpressionConstant, -650, 300, r=0.1645), "", custom, "Mean")   # SOURCE.json mean_lum
    link(expr(unreal.MaterialExpressionScalarParameter, -650, 380, parameter_name="BandCm", default_value=BAND_CM),
         "", custom, "Band")
    mel.connect_material_property(custom, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(expr(unreal.MaterialExpressionConstant, -300, 200, r=0.75), "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return mat


def main():
    mat = build(unreal.AssetToolsHelpers.get_asset_tools(), unreal.MaterialEditingLibrary)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues.get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    wpl = unreal.WorldPartitionBlueprintLibrary
    res = wpl.get_actor_descs()
    wpl.load_actors([d.get_editor_property("guid") for d in (res[1] if isinstance(res, tuple) else res)])
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        comp = a.get_editor_property("static_mesh_component")
        sm = comp.get_editor_property("static_mesh")
        if sm is None:
            continue
        idx = [i for i, sl in enumerate(sm.get_editor_property("static_materials"))
               if sl.get_editor_property("material_interface") and
               sl.get_editor_property("material_interface").get_name() in SLOTS]
        if not idx:
            continue
        a.modify()
        comp.modify()
        for i in idx:
            comp.set_material(i, mat)
        if unreal.Name(TAG) not in list(a.tags):
            a.set_editor_property("tags", list(a.tags) + [unreal.Name(TAG)])
        n += 1
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"apply_kerbs: {n} kerbs striped")


main()
