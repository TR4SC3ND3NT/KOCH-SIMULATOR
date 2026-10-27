# UE 5.8 editor script (R4): see-through chain-link for the sports-court fence panels. Builds M_FenceMesh (masked,
# two-sided, procedural 50 mm diamond wire from the panels' metre UVs: no texture, no tiling seams) and re-parents
# MI_Fence_Mesh_Green onto it, keeping R1's green. Owner playtest 2026-10-27: the courts read as solid green walls.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/make_fence_mesh.py"
import unreal

ROOT = "/Game/KochSimulator/Greybox/Materials"
MASTER = f"{ROOT}/M_FenceMesh"
CELL_M = 0.05        # diamond pitch (common 50 x 50 mm chain-link)
WIRE = 0.06          # wire half-width as a fraction of the cell (~3 mm wire)
GREEN = unreal.LinearColor(0.05, 0.16, 0.08, 1.0)   # linear; PVC-coated green wire


def main():
    mel = unreal.MaterialEditingLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        mat = unreal.EditorAssetLibrary.load_asset(MASTER)
        mat.modify()
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_FenceMesh", ROOT, unreal.Material, unreal.MaterialFactoryNew())

    def expr(cls, x, y, **props):
        e = mel.create_material_expression(mat, cls, x, y)
        for k, v in props.items():
            e.set_editor_property(k, v)
        return e

    def link(a, b, inp, out=""):
        mel.connect_material_expressions(a, out, b, inp)

    uv = expr(unreal.MaterialExpressionTextureCoordinate, -1400, 0)
    cells = expr(unreal.MaterialExpressionMultiply, -1250, 0, const_b=1.0 / CELL_M)
    link(uv, cells, "A")
    u = expr(unreal.MaterialExpressionComponentMask, -1100, -60, r=True, g=False, b=False, a=False)
    v = expr(unreal.MaterialExpressionComponentMask, -1100, 60, r=False, g=True, b=False, a=False)
    link(cells, u, "")
    link(cells, v, "")
    add = expr(unreal.MaterialExpressionAdd, -950, -60)        # diamond axes: u+v and u-v
    sub = expr(unreal.MaterialExpressionSubtract, -950, 60)
    for e in (add, sub):
        link(u, e, "A")
        link(v, e, "B")
    dists = []
    for k, e in enumerate((add, sub)):
        f = expr(unreal.MaterialExpressionFrac, -800, -60 + 120 * k)
        link(e, f, "")
        om = expr(unreal.MaterialExpressionOneMinus, -650, -20 + 120 * k)
        link(f, om, "")
        mn = expr(unreal.MaterialExpressionMin, -500, -60 + 120 * k)
        link(f, mn, "A")
        link(om, mn, "B")
        dists.append(mn)
    d = expr(unreal.MaterialExpressionMin, -350, 0)
    link(dists[0], d, "A")
    link(dists[1], d, "B")
    mask = expr(unreal.MaterialExpressionSubtract, -200, 0, const_a=WIRE + 0.5)   # > 0.5 on the wire
    link(d, mask, "B")
    col = expr(unreal.MaterialExpressionVectorParameter, -350, -250, parameter_name="BaseColor", default_value=GREEN)
    rough = expr(unreal.MaterialExpressionScalarParameter, -350, 250, parameter_name="Roughness", default_value=0.55)
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(mask, "", unreal.MaterialProperty.MP_OPACITY_MASK)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property("opacity_mask_clip_value", 0.5)
    mat.set_editor_property("two_sided", True)
    mat.set_editor_property("used_with_nanite", True)
    mel.recompile_material(mat)

    mi = unreal.EditorAssetLibrary.load_asset(f"{ROOT}/MI_Fence_Mesh_Green")
    mi.modify()
    mel.set_material_instance_parent(mi, mat)
    mel.set_material_instance_vector_parameter_value(mi, "BaseColor", GREEN)
    mel.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_directory(ROOT, False, True)
    unreal.log("make_fence_mesh: MI_Fence_Mesh_Green -> M_FenceMesh (see-through chain-link)")


main()
