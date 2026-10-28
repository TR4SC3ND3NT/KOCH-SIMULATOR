# UE 5.8 editor script (R4 -> everyone): procedural apartment-block facades for the context buildings around the campus
# (CTX_* / GB_CTX_* / GB_BLD_* actors, R1's plain extruded volumes). One opaque material, M_FacadeApartment: a Custom
# HLSL node lays storeys, bays, windows (PVC/wood frames, fortochka transom, curtains/tulle/blinds), glazed balconies,
# AC units, panel joints, plinth, coping and grime from world/local position, so any wall size works without UVs.
# Roofs (|n.z| > 0.6) get dark bitumen. Per building variation from the object position. Assigned as component
# override materials, so re-running the greybox material scripts never undoes it. Idempotent.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/apply_facades.py"
import unreal

LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
ROOT = "/Game/KochSimulator/Environment/Facades"
MASTER = f"{ROOT}/M_FacadeApartment"
OFFICE = f"{ROOT}/MI_FacadeOffice"
PLASTER = "/Game/KochSimulator/Environment/Surfaces/PolyHaven/plastered_wall"
PLASTER_MEAN = 0.40                       # linear mean luminance of T_plastered_wall_diff (SOURCE.json mean_lum)
PREFIXES = ("CTX_", "GB_CTX_", "GB_BLD_")
OFFICE_PREFIXES = ("GB_BLD_",)   # BLD_Other: block E (BLD_W1) and the complex south of D are offices, not flats
REPLACE = ("MI_Context_Facade", "MI_Render_Beige")   # wall slots of those volumes; roofs/slabs in other slots stay
TAG = "KochFacade"

# Units: cm. Inputs: P world pos, N world vertex normal, LP local pos, LMin/LMax local bounds, OP object position,
# Cam camera position, Tl plaster luminance (UV0 = ue_prep box UVs). No ddx/fwidth: Nanite shades in compute.
HLSL = r"""
#define KH(p) frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453)
float3 n = normalize(N);
float seed = KH(float2(frac(OP.x * 0.00137), frac(OP.y * 0.00291)));
Rough = 0.88; Spec = 0.35; Glass = 0.0;
if (abs(n.z) > 0.6)
{
    float g = 0.12 + 0.03 * KH(floor(P.xy / 250.0));
    Rough = 0.92;
    return float3(g, g * 0.98, g * 0.95);
}
float2 t = normalize(float2(-n.y, n.x) + 1e-5);
float u = dot(P.xy, t) + seed * 997.0;
float v = LP.z - LMin.z;
float wallH = LMax.z - LMin.z;
float fw = max(length(P - Cam) * 0.002, 0.3);      // ~one pixel at 1080p / 90 deg, for line widths

bool office = Office > 0.5;                         // MI_FacadeOffice: no balconies/curtains/AC, alu ribbon windows
float FH = office ? 330.0 : seed < 0.5 ? 280.0 : 300.0;   // storey: office / panel block / older brick block
float BW = 290.0 + 70.0 * frac(seed * 3.71);       // bay
float WW = office ? 0.8 * BW : 125.0 + 45.0 * frac(seed * 5.27);   // window width
float WH = office ? 175.0 : 145.0, SILL = 85.0, PLINTH = 70.0;
float pi = frac(seed * 11.3);
float3 wall = pi < 0.22 ? float3(0.50, 0.49, 0.46) : pi < 0.42 ? float3(0.58, 0.48, 0.36) : pi < 0.56 ? float3(0.62, 0.55, 0.36)
            : pi < 0.70 ? float3(0.60, 0.46, 0.42) : pi < 0.86 ? float3(0.66, 0.66, 0.63) : float3(0.45, 0.50, 0.53);
wall *= lerp(1.0, Tl / Mean, 0.8);
wall *= lerp(0.80, 1.0, saturate(v / 300.0));        // splash grime near the ground

float fl = floor(v / FH);
float fv = v - fl * FH;
float bi = floor(u / BW);
float cu = u - bi * BW - 0.5 * BW;
bool ok = wallH > 380.0 && fl >= 0.0 && (fl + 1.0) * FH <= wallH - 30.0;
float3 col = wall;

// panel joints, faded out once thinner than a pixel
float jw = 1.2;
float jd = min(min(fv, FH - fv), 0.5 * BW - abs(cu));
col *= 1.0 - 0.35 * saturate((jw - jd) / fw + 0.5) * saturate(jw / fw);

if (v < PLINTH)
{
    col = float3(0.22, 0.21, 0.20) * lerp(1.0, Tl / Mean, 0.8);
}
else if (v > wallH - 40.0)
{
    col = v > wallH - 8.0 ? float3(0.33, 0.34, 0.35) : wall * 0.85;
}
else if (ok)
{
    float hb = KH(float2(bi * 1.7, seed * 53.0));
    float hw = KH(float2(bi + fl * 37.0, seed * 13.0 + fl));
    float hc = KH(float2(bi * 3.1 + fl * 1.3, seed * 7.0));
    bool bal = !office && fl >= 1.0 && hb < 0.33;
    if (bal && abs(cu) < BW * 0.44 && fv < 255.0)
    {
        if (fv < 12.0)
        {
            col = float3(0.42, 0.42, 0.41) * (cu > 0.0 ? 1.0 : 0.96);       // slab edge
        }
        else if (fv < 105.0)
        {
            float3 sheet = hc < 0.25 ? wall * 0.92 : hc < 0.45 ? float3(0.30, 0.40, 0.50) : hc < 0.60 ? float3(0.30, 0.40, 0.28)
                         : hc < 0.80 ? float3(0.70, 0.70, 0.68) : float3(0.33, 0.22, 0.15);
            float rib = hc > 0.25 ? 0.88 + 0.12 * step(0.5, frac(cu / 9.0)) : 1.0;
            col = sheet * rib * lerp(0.85, 1.0, saturate((fv - 12.0) / 40.0));
            Rough = 0.6;
        }
        else if (hw > 0.85)
        {
            col = wall * 0.30;                                                   // open loggia: back wall in shade
        }
        else
        {
            float3 fcol = hw < 0.55 ? float3(0.74, 0.74, 0.72) : hw < 0.75 ? float3(0.52, 0.52, 0.53) : float3(0.20, 0.12, 0.07);
            float gu = frac((cu + 1000.0) / 62.0) * 62.0;
            bool frame = gu < 5.0 || fv < 110.0 || fv > 249.0;
            if (frame)
            {
                col = fcol; Rough = 0.45; Spec = 0.5;
            }
            else
            {
                col = lerp(float3(0.025, 0.024, 0.022), float3(0.20, 0.18, 0.15), 0.25 * hc); Rough = 0.04; Spec = 0.5;
            }
            Glass = 1.0;
        }
    }
    else if (fl == 0.0 && hb > 0.93 && abs(cu) < 60.0 && fv < 230.0)
    {
        col = abs(cu) > 55.0 || fv > 225.0 ? float3(0.30, 0.30, 0.30) : float3(0.07, 0.06, 0.055);    // entrance door
        Rough = 0.5; Glass = 1.0;
    }
    else
    {
        float wy = fv - SILL;
        float hx = 0.5 * WW;
        if (abs(cu) < hx && wy > 0.0 && wy < WH)
        {
            float3 fcol = office ? float3(0.52, 0.53, 0.55) : hw < 0.65 ? float3(0.74, 0.74, 0.72) : hw < 0.9 ? float3(0.55, 0.53, 0.48) : float3(0.20, 0.12, 0.07);
            bool frame = abs(cu) > hx - 6.0 || wy < 6.0 || wy > WH - 6.0 || (WW > 120.0 && abs(cu) < 2.5)
                         || (cu < 0.0 && abs(wy - (WH - 45.0)) < 2.5);
            if (frame)
            {
                col = fcol; Rough = 0.45; Spec = 0.5;
            }
            else
            {
                float3 room = float3(0.02, 0.019, 0.018) * (1.0 + 1.5 * hc);
                float3 cur = hc < 0.3 ? float3(0.55, 0.48, 0.36) : hc < 0.55 ? float3(0.42, 0.18, 0.14) : hc < 0.8 ? float3(0.25, 0.32, 0.22) : float3(0.30, 0.22, 0.15);
                if (office) col = hw < 0.45 ? float3(0.45, 0.45, 0.44) * (0.8 + 0.2 * step(0.5, frac(wy / 4.0))) : room * 2.0;   // blinds / open office
                else if (hw < 0.30) col = room;                                                // bare
                else if (hw < 0.62) col = lerp(room, float3(0.55, 0.55, 0.52), 0.55);          // tulle
                else if (hw < 0.85) col = abs(cu) > WW * (0.12 + 0.2 * hc) ? cur : room;       // side curtains
                else col = float3(0.50, 0.49, 0.46) * (0.8 + 0.2 * step(0.5, frac(wy / 4.0)));  // blinds
                Rough = 0.04; Spec = 0.5;
            }
            Glass = 1.0;
        }
        else if (abs(cu) < hx + 4.0 && wy > -5.0 && wy <= 0.0)
        {
            col = float3(0.50, 0.50, 0.50); Rough = 0.5; Spec = 0.5; Glass = 1.0;                     // tin sill
        }
        else if (!office && hw < 0.12 && abs(cu - hx - 45.0) < 35.0 && wy > 15.0 && wy < 70.0)
        {
            col = float3(0.72, 0.72, 0.70) * (abs(cu - hx - 45.0) < 25.0 && frac(wy / 3.0) < 0.5 ? 0.8 : 1.0);   // AC unit
            Rough = 0.5; Spec = 0.5; Glass = 1.0;
        }
        else
        {
            if (abs(cu) < hx && wy >= WH && wy < WH + 8.0) col *= 0.55;                          // lintel shadow
            else if (abs(cu) < hx + 4.0 && wy > 0.0 && wy < WH) col *= 0.75;                     // reveal
            else if (abs(cu) < hx && wy > -60.0 && wy < -5.0) col *= lerp(0.86, 1.0, saturate((-5.0 - wy) / 55.0));  // drip stain
        }
    }
}
return col;
#undef KH
"""


def build_master(tools, mel):
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        mat = unreal.EditorAssetLibrary.load_asset(MASTER)
        mat.modify()
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_FacadeApartment", ROOT, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("used_with_nanite", True)
    mat.set_editor_property("used_with_static_lighting", True)

    def expr(cls, x, y, **props):
        e = mel.create_material_expression(mat, cls, x, y)
        for k, v in props.items():
            e.set_editor_property(k, v)
        return e

    def link(a, out, b, inp):
        if not mel.connect_material_expressions(a, out, b, inp):
            raise RuntimeError(f"apply_facades: cannot link {a.get_name()}.{out} -> {b.get_name()}.{inp}")

    def struct(cls, **props):   # 5.8 Python structs take no constructor kwargs
        s = cls()
        for k, v in props.items():
            s.set_editor_property(k, v)
        return s

    F1, F3 = unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.CustomMaterialOutputType.CMOT_FLOAT3
    names = ("P", "N", "LP", "LMin", "LMax", "OP", "Cam", "Tl", "Mean", "Office")
    custom = expr(unreal.MaterialExpressionCustom, -400, 0, code=HLSL, output_type=F3, description="Facade",
                  inputs=[struct(unreal.CustomInput, input_name=n) for n in names],
                  additional_outputs=[struct(unreal.CustomOutput, output_name=n, output_type=F1)
                                      for n in ("Rough", "Spec", "Glass")])
    link(expr(unreal.MaterialExpressionWorldPosition, -900, -300), "", custom, "P")
    link(expr(unreal.MaterialExpressionVertexNormalWS, -900, -200), "", custom, "N")
    link(expr(unreal.MaterialExpressionLocalPosition, -900, -100), "", custom, "LP")
    bounds = expr(unreal.MaterialExpressionObjectLocalBounds, -900, 0)
    link(bounds, "Min", custom, "LMin")
    link(bounds, "Max", custom, "LMax")
    link(expr(unreal.MaterialExpressionObjectPositionWS, -900, 150), "", custom, "OP")
    link(expr(unreal.MaterialExpressionCameraPositionWS, -900, 250), "", custom, "Cam")
    uv = expr(unreal.MaterialExpressionTextureCoordinate, -1300, 400, u_tiling=0.5, v_tiling=0.5)   # 2 m set
    diff = expr(unreal.MaterialExpressionTextureSample, -1100, 350,
                texture=unreal.EditorAssetLibrary.load_asset(f"{PLASTER}/T_plastered_wall_diff"))
    link(uv, "", diff, "UVs")
    lum = expr(unreal.MaterialExpressionDotProduct, -900, 350)
    link(diff, "RGB", lum, "A")
    link(expr(unreal.MaterialExpressionConstant3Vector, -1100, 550,
              constant=unreal.LinearColor(0.2126, 0.7152, 0.0722, 1)), "", lum, "B")
    link(lum, "", custom, "Tl")
    link(expr(unreal.MaterialExpressionConstant, -900, 450, r=PLASTER_MEAN), "", custom, "Mean")
    link(expr(unreal.MaterialExpressionScalarParameter, -900, 520, parameter_name="Office", default_value=0.0), "", custom, "Office")
    # plaster relief on walls, flat on glass/frames/sills (Glass mask)
    nrm = expr(unreal.MaterialExpressionTextureSample, -900, 650, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
               texture=unreal.EditorAssetLibrary.load_asset(f"{PLASTER}/T_plastered_wall_nor"))
    link(uv, "", nrm, "UVs")
    flat = expr(unreal.MaterialExpressionConstant3Vector, -900, 850, constant=unreal.LinearColor(0, 0, 1, 1))
    nl = expr(unreal.MaterialExpressionLinearInterpolate, -150, 600)
    link(nrm, "RGB", nl, "A")
    link(flat, "", nl, "B")
    link(custom, "Glass", nl, "Alpha")
    mel.connect_material_property(custom, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(custom, "Rough", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(custom, "Spec", unreal.MaterialProperty.MP_SPECULAR)
    mel.connect_material_property(nl, "", unreal.MaterialProperty.MP_NORMAL)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return mat


def main():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    mat = build_master(tools, mel)
    if unreal.EditorAssetLibrary.does_asset_exist(OFFICE):
        office = unreal.EditorAssetLibrary.load_asset(OFFICE)
    else:
        office = tools.create_asset("MI_FacadeOffice", ROOT, unreal.MaterialInstanceConstant,
                                    unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(office, mat)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(office, "Office", 1.0)
    unreal.EditorAssetLibrary.save_loaded_asset(office, False)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues.get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    wpl = unreal.WorldPartitionBlueprintLibrary
    res = wpl.get_actor_descs()
    wpl.load_actors([d.get_editor_property("guid") for d in (res[1] if isinstance(res, tuple) else res)])
    done = slots = 0
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    flat_done = set()
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor) or not a.get_actor_label().startswith(PREFIXES):
            continue
        comp = a.get_editor_property("static_mesh_component")
        sm = comp.get_editor_property("static_mesh")
        if sm is None:
            continue
        idx = [i for i, sl in enumerate(sm.get_editor_property("static_materials"))
               if sl.get_editor_property("material_interface") and
               sl.get_editor_property("material_interface").get_name() in REPLACE]
        if not idx and a.actor_has_tag(TAG):   # re-run: the slots already carry a facade material
            idx = [i for i, m in enumerate(comp.get_materials()) if m and m.get_name() in ("M_FacadeApartment", "MI_FacadeOffice")]
        if not idx:
            continue
        if sm not in flat_done:   # the facade reads the wall direction from the normal: keep the export's flat normals
            bs = sms.get_lod_build_settings(sm, 0)
            if bs.get_editor_property("recompute_normals"):
                bs.set_editor_property("recompute_normals", False)   # UE's recompute smoothed corners -> sheared windows
                sms.set_lod_build_settings(sm, 0, bs)
            flat_done.add(sm)
        a.modify()
        comp.modify()
        for i in idx:
            comp.set_material(i, office if a.get_actor_label().startswith(OFFICE_PREFIXES) else mat)
        tags = list(a.tags)
        if unreal.Name(TAG) not in tags:
            a.set_editor_property("tags", tags + [unreal.Name(TAG)])
        done += 1
        slots += len(idx)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"apply_facades: {done} buildings, {slots} slots")


main()
