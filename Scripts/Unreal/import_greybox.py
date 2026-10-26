# UE 5.8 editor importer for the R1 greybox hand-off (Scripts/Blender/ue_prep): imports OUT_DIR's FBX meshes into
# /Game/KochSimulator/Greybox/{Meshes,Ground} (Nanite on, collision from the UBX_/UCX_ nodes, no auto collision,
# complex-as-simple where the manifest says so) and places manifest.json into the open level: one outliner folder
# per building (ready for "Create Packed Level Actor"), ground tiles as plain StaticMeshActors, UE-asset placeholders
# tagged "UEAsset:<slot>", map barrier hidden in game with the InvisibleWall profile.
# UNTESTED IN-EDITOR (written on a machine without Unreal). Every API name was checked against Epic's Python API
# reference 5.6/5.7 (dev.epicgames.com/documentation/en-us/unreal-engine/python-api/); if a call fails in 5.8, compare
# with the editor's stub (Intermediate/PythonStub/unreal.py). Level Instance / Packed Level Actor creation is
# C++-only (ULevelInstanceSubsystem::CreateLevelInstanceFrom), so packing per building stays a manual step:
# select the building folder in the Outliner -> right-click -> Level -> Create Packed Level Actor (name from manifest).
# Run (Output Log, Cmd = Python, or `py <file> <args>`):
#   py "<repo>/Scripts/Unreal/import_greybox.py" D:/GreyboxExport [--import-only|--place-only] [--legacy]
#      [--only BLD_C] [--replace] [--limit N]
import argparse
import json
import os
import sys

import unreal

TAG = "KochGreybox"
BATCH = 50   # import tasks per import_asset_tasks call (progress + cancel granularity)


def _set(obj, prop, value):
    """set_editor_property that logs instead of raising when a property was renamed in this engine version."""
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception as e:   # unreal raises plain Exception for unknown properties
        unreal.log_warning(f"import_greybox: {type(obj).__name__}.{prop} not set ({e})")
        return False


def _enum(cls, value):
    """unreal.<cls>.<value> or None (logged) if this engine version names it differently."""
    v = getattr(getattr(unreal, cls, None), value, None)
    if v is None:
        unreal.log_warning(f"import_greybox: unreal.{cls}.{value} missing")
    return v


def _set_enum(obj, prop, cls, value):
    v = _enum(cls, value)
    return v is not None and _set(obj, prop, v)


def interchange_options(name, kind):
    p = unreal.InterchangeGenericAssetsPipeline()
    mp = p.get_editor_property("mesh_pipeline")
    _set(mp, "import_static_meshes", True)
    _set(mp, "import_skeletal_meshes", False)
    # UE-239640 (Interchange, 5.5+): with combining on, UCX nodes become render geometry. One mesh per file anyway.
    # 5.8: bCombineStaticMeshes is deprecated and not script-visible; the enum replaced it.
    _set_enum(mp, "combine_static_meshes_behavior", "InterchangeCombineStaticMeshesBehavior", "DO_NOT_COMBINE")
    _set(mp, "collision", kind not in ("none", "complex_as_simple"))
    _set(mp, "import_collision_according_to_mesh_name", True)
    _set(mp, "one_convex_hull_per_ucx", True)
    # No fallback override: EInterchangeMeshCollision has no "none" in 5.8, and every mesh with collision on ships
    # its own UBX_/UCX_ nodes, so the fallback shape is never generated.
    _set(mp, "build_nanite", True)
    _set(mp, "generate_lightmap_u_vs", False)   # Lumen, no baked lighting
    cp = p.get_editor_property("common_meshes_properties")
    _set_enum(cp, "force_all_mesh_as_type", "InterchangeForceMeshType", "IFMT_STATIC_MESH")
    _set(p.get_editor_property("material_pipeline"), "import_materials", False)   # slots only; team assigns M_*
    _set(p, "asset_name", name)
    ov = unreal.InterchangePipelineStackOverride()
    ov.add_pipeline(p)
    return ov


def legacy_options(kind):
    """Legacy FBX importer with Epic Send2UE's static-mesh settings (send2ue/resources/settings.json)."""
    ui = unreal.FbxImportUI()
    for k, v in (("import_mesh", True), ("import_as_skeletal", False), ("import_materials", False),
                 ("import_textures", False), ("automated_import_should_detect_type", False),
                 ("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)):
        _set(ui, k, v)
    sd = ui.get_editor_property("static_mesh_import_data")
    for k, v in (("combine_meshes", False), ("auto_generate_collision", False), ("one_convex_hull_per_ucx", True),
                 ("build_nanite", True), ("generate_lightmap_u_vs", False), ("convert_scene", False),
                 ("force_front_x_axis", False), ("convert_scene_unit", False), ("import_uniform_scale", 1.0),
                 ("transform_vertex_to_absolute", True), ("bake_pivot_in_vertex", False)):
        _set(sd, k, v)
    return ui


def import_meshes(out, man, names, legacy):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if legacy:   # route FBX through the legacy importer for this editor session
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        unreal.SystemLibrary.execute_console_command(world, "Interchange.FeatureFlags.Import.FBX 0")
    done = {}
    with unreal.ScopedSlowTask(len(names), "Importing greybox meshes") as task:
        task.make_dialog(True)
        for b in range(0, len(names), BATCH):
            if task.should_cancel():
                break
            chunk = names[b:b + BATCH]
            tasks = []
            for n in chunk:
                m = man["meshes"][n]
                t = unreal.AssetImportTask()
                t.set_editor_property("filename", os.path.join(out, m["file"]))
                t.set_editor_property("destination_path", m["ue_path"].rsplit("/", 1)[0])
                t.set_editor_property("destination_name", n)   # legacy path; Interchange uses asset_name
                t.set_editor_property("automated", True)
                t.set_editor_property("replace_existing", True)
                t.set_editor_property("save", False)
                t.set_editor_property("options", legacy_options(m["collision"]["kind"]) if legacy else
                                      interchange_options(n, m["collision"]["kind"]))
                tasks.append(t)
            tools.import_asset_tasks(tasks)
            for n, t in zip(chunk, tasks):
                sm = next((o for o in t.get_objects() if isinstance(o, unreal.StaticMesh)), None)
                if sm is None:
                    unreal.log_error(f"import_greybox: {n}: nothing imported")
                    continue
                if sm.get_name() != n:
                    unreal.log_warning(f"import_greybox: {n} imported as {sm.get_path_name()}")
                done[n] = sm
            task.enter_progress_frame(len(chunk), f"{min(b + BATCH, len(names))}/{len(names)}")
    return done


def configure(man, meshes):
    """Nanite, collision complexity and a collision/slot check against the manifest. Returns problem count."""
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    bad = 0
    for n, sm in meshes.items():
        m = man["meshes"][n]
        c = m["collision"]
        sm.modify()
        ns = sm.get_editor_property("nanite_settings")
        ns.set_editor_property("enabled", True)
        if c["kind"] == "complex_as_simple":   # complex collision is built from the Nanite fallback: keep it exact
            _set_enum(ns, "fallback_target", "NaniteFallbackTarget", "RELATIVE_ERROR")
            ns.set_editor_property("fallback_relative_error", 0.0)
        sms.set_nanite_settings(sm, ns, True)
        if c["kind"] in ("none", "complex_as_simple"):
            sms.remove_collisions(sm)
        bs = sm.get_editor_property("body_setup")
        if bs is not None:
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
                                   if c["kind"] == "complex_as_simple" else unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
        want = c["ubx"] + c["ucx"]
        got = sms.get_simple_collision_count(sm)
        if got != want:
            bad += 1
            unreal.log_warning(f"import_greybox: {n}: {got} simple collision shapes, manifest {want} ({c['kind']})")
        slots = [str(s.get_editor_property("material_slot_name")) for s in sm.get_editor_property("static_materials")]
        if slots != m["slots"]:
            unreal.log_warning(f"import_greybox: {n}: slots {slots} != manifest {m['slots']}")
        tris = sm.get_num_triangles(0)
        if tris and tris < m["tris"] * 0.5:   # Nanite fallback may report fewer; only flag gross loss
            unreal.log_warning(f"import_greybox: {n}: {tris} tris, manifest {m['tris']}")
    return bad


def place(man, meshes, only, limit):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    insts = [e for e in man["instances"] if not only or e["building"] in only][:limit or None]
    placed = 0
    with unreal.ScopedSlowTask(len(insts), "Placing greybox") as task:
        task.make_dialog(True)
        for e in insts:
            if task.should_cancel():
                break
            task.enter_progress_frame(1)
            sm = meshes.get(e["mesh"])
            if sm is None:
                continue
            p, y, r = e["rot"]
            a = eas.spawn_actor_from_object(sm, unreal.Vector(*e["loc"]), unreal.Rotator(roll=r, pitch=p, yaw=y))
            if a is None:
                unreal.log_error(f"import_greybox: spawn failed for {e['name']}")
                continue
            a.set_actor_scale3d(unreal.Vector(*e["scale"]))
            a.set_actor_label(e["name"])
            a.set_folder_path("Greybox/Ground" if e["role"] == "ground" else f"Greybox/{e['building']}/{e['zone']}")
            tags = [TAG, f"KochZone:{e['zone']}"]
            if e["koch_id"]:
                tags.append(f"KochId:{e['koch_id']}")
            if e["ue_asset"]:
                tags.append(f"UEAsset:{e['ue_asset']}")
            a.set_editor_property("tags", [unreal.Name(t) for t in tags])
            comp = a.get_editor_property("static_mesh_component")
            comp.set_mobility(unreal.ComponentMobility.STATIC)
            if e["role"] == "barrier":
                a.set_actor_hidden_in_game(True)
                comp.set_collision_profile_name("InvisibleWall")
            placed += 1
    return placed


def main(argv):
    ap = argparse.ArgumentParser(prog="import_greybox")
    ap.add_argument("out")
    ap.add_argument("--import-only", action="store_true")
    ap.add_argument("--place-only", action="store_true")
    ap.add_argument("--legacy", action="store_true", help="legacy FBX importer (Send2UE settings)")
    ap.add_argument("--only", nargs="*", default=[], help="buildings/groups to place (manifest 'building')")
    ap.add_argument("--replace", action="store_true", help="delete previously placed greybox actors first")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    with open(os.path.join(a.out, "manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    names = sorted(man["meshes"])
    if a.only:
        used = {e["mesh"] for e in man["instances"] if e["building"] in a.only}
        names = [n for n in names if n in used]
    if a.limit:
        names = names[:a.limit]
    if a.place_only:
        meshes = {}
        for n in names:
            sm = unreal.EditorAssetLibrary.load_asset(man["meshes"][n]["ue_path"])
            if sm is not None:
                meshes[n] = sm
    else:
        meshes = import_meshes(a.out, man, names, a.legacy)
        bad = configure(man, meshes)
        unreal.EditorAssetLibrary.save_directory(man["ue_root"], True, True)
        unreal.log(f"import_greybox: {len(meshes)}/{len(names)} meshes imported, {bad} collision mismatches")
    if a.import_only:
        return
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if a.replace:
        old = [x for x in eas.get_all_level_actors() if x.actor_has_tag(TAG)]
        eas.destroy_actors(old)
        unreal.log(f"import_greybox: removed {len(old)} old greybox actors")
    n = place(man, meshes, set(a.only), a.limit)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
    unreal.log(f"import_greybox: placed {n} actors; packed-level-actor names per building: "
               + ", ".join(f"{b}->{g['packed_level_actor']}" for b, g in man["groups"].items()))


main(sys.argv[1:])
