# UE 5.8 editor script (R4 -> everyone): street furniture over R1's ue_asset placeholders (bench_*, bins, containers).
# Imports Scripts/Blender/build_props.py's FBX kit (Nanite, materials = the greybox MI_<slot> set), puts one prop on each
# placeholder: same base, yaw from the placeholder (its long side), length scaled to it; a bench turns its back to the
# nearer wall/hedge. Placeholders are hidden but keep their collision (a clean box per prop). Re-running replaces props.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/place_props.py" [PROPS_DIR] [--reimport]
import json
import os
import sys

import unreal

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PROPS = ARGS[0] if ARGS else os.path.join(REPO, "Saved", "ThirdParty", "Props")
LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
ROOT = "/Game/KochSimulator/Environment/Props/Street"
MI_ROOT = "/Game/KochSimulator/Greybox/Materials"
TAG = "KochProp"
# ue_asset prefix -> prop; first match wins
MAPPING = [("bench", "SM_Prop_Bench_Park"), ("bin_wrought_iron", "SM_Prop_Bin_WroughtIron"),
           ("bin_container", "SM_Prop_Container1100"), ("waste_container", "SM_Prop_Container1100"),
           ("bin_generic", "SM_Prop_Bin_Wheelie240")]
LENGTH_SCALE = (0.75, 1.35)      # a 2.2 m slat bench is the 1.8 m kit stretched; beyond this it reads wrong


def import_props(names):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    out = {n: unreal.EditorAssetLibrary.load_asset(f"{ROOT}/{n}") for n in names
           if "--reimport" not in sys.argv and unreal.EditorAssetLibrary.does_asset_exist(f"{ROOT}/{n}")}
    tasks = []
    for n in (n for n in names if n not in out):
        p = unreal.InterchangeGenericAssetsPipeline()
        mp = p.get_editor_property("mesh_pipeline")
        mp.set_editor_property("build_nanite", True)
        mp.set_editor_property("collision", False)     # the hidden placeholder keeps a clean box collision
        mp.set_editor_property("generate_lightmap_u_vs", False)
        p.get_editor_property("material_pipeline").set_editor_property("import_materials", False)
        p.set_editor_property("asset_name", n)
        ov = unreal.InterchangePipelineStackOverride()
        ov.add_pipeline(p)
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(PROPS, f"{n}.fbx"))
        t.set_editor_property("destination_path", ROOT)
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", False)
        t.set_editor_property("options", ov)
        tasks.append((n, t))
    if tasks:
        tools.import_asset_tasks([t for _, t in tasks])
    for n, t in tasks:
        out[n] = next((o for o in t.get_objects() if isinstance(o, unreal.StaticMesh)), None)
    for sm in out.values():
        if sm is None:
            continue
        sm.modify()
        for i, sl in enumerate(sm.get_editor_property("static_materials")):
            slot = str(sl.get_editor_property("material_slot_name"))
            mi = unreal.EditorAssetLibrary.load_asset(f"{MI_ROOT}/MI_{slot[2:]}") if slot.startswith("M_") else None
            if mi is not None:
                sm.set_material(i, mi)
    unreal.EditorAssetLibrary.save_directory(ROOT, False, True)
    return out


def trace_dist(world, a, b, ignore):
    h = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
                                               unreal.DrawDebugTrace.NONE, True)
    if h is None:
        return None
    t = h.to_tuple()
    return t[3] if t[0] else None


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues.get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    wpl = unreal.WorldPartitionBlueprintLibrary
    res = wpl.get_actor_descs()
    wpl.load_actors([d.get_editor_property("guid") for d in (res[1] if isinstance(res, tuple) else res)])
    world = ues.get_editor_world()
    with open(os.path.join(PROPS, "props.json"), encoding="utf-8") as fh:
        kit = json.load(fh)
    with open(os.path.join(REPO, "Saved", "GreyboxExport", "manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    meshes = import_props(sorted(kit))
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    eas.destroy_actors([a for a in actors if a.actor_has_tag(TAG)])
    by_label = {a.get_actor_label(): a for a in actors if a.actor_has_tag("KochGreybox")}
    placed = 0
    for e in man["instances"]:
        kind = (e.get("ue_asset") or "").lower()
        prop = next((p for k, p in MAPPING if kind.startswith(k)), None)
        ph = by_label.get(e["name"])
        if prop is None or ph is None or meshes.get(prop) is None or e["zone"].startswith("INT"):
            continue
        (x0, y0, z0), (x1, y1, z1) = man["meshes"][e["mesh"]]["bounds_m"]
        long_y = (y1 - y0) > (x1 - x0)                      # placeholder's long side in its local frame
        length_m = max(x1 - x0, y1 - y0)
        yaw = e["rot"][1] + (90.0 if long_y else 0.0)
        origin, ext = ph.get_actor_bounds(False)            # current placement (fix_site may have dropped it)
        base = unreal.Vector(origin.x, origin.y, origin.z - ext.z)
        size = kit[prop]["size_m"]
        sx = min(max(length_m / size[0], LENGTH_SCALE[0]), LENGTH_SCALE[1])
        sz = min(max((z1 - z0) / size[2], 0.8), 1.25)
        if prop == "SM_Prop_Bench_Park":
            # front faces local -Y: put the back (+Y) toward the nearer obstacle within 2 m at seat height
            import math
            r = math.radians(yaw)
            fwd = unreal.Vector(-math.sin(r), math.cos(r), 0.0)   # local +Y in world
            p0 = unreal.Vector(origin.x, origin.y, base.z + 50)
            d_back = trace_dist(world, p0, p0 + fwd * 200.0, [ph])
            d_front = trace_dist(world, p0, p0 - fwd * 200.0, [ph])
            if d_front is not None and (d_back is None or d_front < d_back):
                yaw += 180.0
        a = eas.spawn_actor_from_object(meshes[prop], base, unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        a.set_actor_scale3d(unreal.Vector(sx, 1.0, sz))
        a.set_actor_label(f"PROP_{e['name']}")
        a.set_folder_path(f"Props/{e['zone']}")
        a.set_editor_property("tags", [unreal.Name(TAG), unreal.Name(f"Replaces:{e['name']}")])
        a.get_editor_property("static_mesh_component").set_mobility(unreal.ComponentMobility.STATIC)
        ph.modify()
        comp = ph.get_editor_property("static_mesh_component")
        comp.modify()
        comp.set_visibility(False, True)
        ph.set_actor_hidden_in_game(True)
        placed += 1
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"place_props: {len([m for m in meshes.values() if m])} props, {placed} placed")


main()
