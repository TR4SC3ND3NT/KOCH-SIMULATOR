# UE 5.8 editor script (R4 -> everyone): coloured greybox. Builds M_GreyboxMaster (BaseColor/Roughness/Metallic/
# Emissive parameters) and one MI_<slot> per greybox material slot from Saved/GreyboxExport/materials.json (R1's
# review palette, Scripts/Blender/export_material_colors.py), then assigns them to every imported greybox mesh by
# slot name. Placeholder look only: the real PBR materials replace MI_* per slot later. Idempotent.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/apply_greybox_materials.py" [EXPORT_DIR]
import json
import os
import sys

import unreal

ROOT = "/Game/KochSimulator/Greybox/Materials"
MASTER = f"{ROOT}/M_GreyboxMaster"
EXPORT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "Saved", "GreyboxExport")

# name fragment -> (roughness, metallic, emissive); first match wins. Values: typical PBR ranges for each surface
# class (painted metal ~0.4, raw metal metallic 1, glazing ~0.05, mineral/organic 0.75-0.9).
FAMILIES = [
    ("Mirror", 0.02, 1.0, 0.0), ("Glass", 0.05, 0.0, 0.0), ("Chrome", 0.15, 1.0, 0.0), ("Brass", 0.3, 1.0, 0.0),
    ("Steel_Galv", 0.45, 1.0, 0.0), ("Alu", 0.4, 1.0, 0.0), ("Steel_Grating", 0.5, 1.0, 0.0),
    ("LED_Panel", 0.5, 0.0, 6.0), ("Lamp_Diffuser", 0.4, 0.0, 3.0),
    ("Steel_Paint", 0.45, 0.0, 0.0), ("Wrought", 0.5, 0.0, 0.0), ("Fence_Mesh", 0.5, 0.0, 0.0),
    ("PVC", 0.35, 0.0, 0.0), ("Plastic", 0.4, 0.0, 0.0), ("Laminate", 0.35, 0.0, 0.0), ("Ceramic", 0.15, 0.0, 0.0),
    ("Terrazzo", 0.3, 0.0, 0.0), ("Tile_Wall", 0.25, 0.0, 0.0), ("Sport_Floor", 0.35, 0.0, 0.0),
    ("HPL", 0.3, 0.0, 0.0), ("Radiator", 0.35, 0.0, 0.0), ("AC_Casing", 0.4, 0.0, 0.0), ("Sign", 0.35, 0.0, 0.0),
    ("Paint", 0.6, 0.0, 0.0), ("Sheet", 0.5, 0.0, 0.0), ("Granite", 0.55, 0.0, 0.0),
    ("Wood", 0.65, 0.0, 0.0), ("Fabric", 0.9, 0.0, 0.0), ("Asphalt", 0.85, 0.0, 0.0),
    ("Grass", 0.9, 0.0, 0.0), ("Hedge", 0.85, 0.0, 0.0), ("Tree", 0.85, 0.0, 0.0), ("Soil", 0.95, 0.0, 0.0),
]
DEFAULT = (0.8, 0.0, 0.0)   # render, concrete, pavers, brick, shingle, gravel, sand


def srgb_to_linear(c):
    # R1's palette holds display (sRGB) values, e.g. maroon 0.50/0.16/0.14 = sRGB 128/41/36; UE params are linear
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def surface(name):
    return next(((r, m, e) for k, r, m, e in FAMILIES if k in name), DEFAULT)


def build_master(tools):
    mel = unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        return unreal.EditorAssetLibrary.load_asset(MASTER)
    mat = tools.create_asset("M_GreyboxMaster", ROOT, unreal.Material, unreal.MaterialFactoryNew())

    def param(cls, name, default, y):
        e = mel.create_material_expression(mat, cls, -600, y)
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("default_value", default)
        return e

    base = param(unreal.MaterialExpressionVectorParameter, "BaseColor", unreal.LinearColor(0.5, 0.5, 0.5, 1), 0)
    rough = param(unreal.MaterialExpressionScalarParameter, "Roughness", 0.8, 200)
    metal = param(unreal.MaterialExpressionScalarParameter, "Metallic", 0.0, 300)
    emis = param(unreal.MaterialExpressionScalarParameter, "Emissive", 0.0, 400)
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -300, 400)
    mel.connect_material_expressions(base, "", mul, "A")
    mel.connect_material_expressions(emis, "", mul, "B")
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mat.set_editor_property("used_with_nanite", True)
    mel.recompile_material(mat)
    return mat


def build_instance(tools, master, slot, props):
    path = f"{ROOT}/MI_{slot[2:] if slot.startswith('M_') else slot}"
    mi = (unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else
          tools.create_asset(path.rsplit("/", 1)[1], ROOT, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew()))
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_parent(mi, master)
    r, g, b = (srgb_to_linear(c) for c in (props["base_color"] if props else (0.5, 0.5, 0.5)))
    rough, metal, emis = surface(slot)
    mel.set_material_instance_vector_parameter_value(mi, "BaseColor", unreal.LinearColor(r, g, b, 1.0))
    mel.set_material_instance_scalar_parameter_value(mi, "Roughness", rough)
    mel.set_material_instance_scalar_parameter_value(mi, "Metallic", metal)
    mel.set_material_instance_scalar_parameter_value(mi, "Emissive", emis)
    mel.update_material_instance(mi)
    return mi


def main():
    with open(os.path.join(EXPORT, "manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    with open(os.path.join(EXPORT, "materials.json"), encoding="utf-8") as fh:
        colours = json.load(fh)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    master = build_master(tools)
    slots = sorted({s for m in man["meshes"].values() for s in m["slots"]})
    mis = {s: build_instance(tools, master, s, colours.get(s)) for s in slots}
    missing = [s for s in slots if s not in colours]
    if missing:
        unreal.log_warning(f"apply_greybox_materials: no review colour for {missing} (mid grey)")
    done = 0
    with unreal.ScopedSlowTask(len(man["meshes"]), "Assigning greybox materials") as task:
        task.make_dialog(True)
        for name, m in man["meshes"].items():
            if task.should_cancel():
                break
            task.enter_progress_frame(1)
            sm = unreal.EditorAssetLibrary.load_asset(m["ue_path"])
            if sm is None:
                continue
            for i, sl in enumerate(sm.get_editor_property("static_materials")):
                mi = mis.get(str(sl.get_editor_property("material_slot_name")))
                if mi is not None:
                    sm.set_material(i, mi)
            done += 1
    unreal.EditorAssetLibrary.save_directory(man["ue_root"], True, True)
    unreal.log(f"apply_greybox_materials: {len(mis)} instances, {done} meshes assigned")


main()
