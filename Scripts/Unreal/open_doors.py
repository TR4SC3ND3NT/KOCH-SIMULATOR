# UE 5.8 editor script (R4): makes a building walkable by swinging every door leaf open 90 deg about its hinge (leaf +
# glass of one door turn together). For each door it tries both hinge ends and both swing sides and keeps the first
# whose swept quarter-circle is clear (traces at 0.3/1.0/1.7 m over 0..90 deg), so leaves never swing into a wall.
# Entrance double doors modelled as one mesh (GBF_*_Entrance_*_Doors) are hidden with no collision: an open doorway.
# Doors with no clear swing keep their look but lose collision. Moves are relative to the manifest pose (idempotent);
# everything is listed in Saved/QA/doors.json. First pass: Block C only (owner, 2026-10-27).
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/open_doors.py" [BUILDING ...]   (default BLD_C)
import json
import math
import os
import re
import sys

import unreal

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
SCOPE = [a for a in sys.argv[1:] if not a.startswith("--")] or ["BLD_C"]
LEAF = re.compile(r"_(Leaf|Glass)$")
DOUBLE = re.compile(r"_Entrance_.*_Doors$")


def in_scope(e):
    zone_bld = "BLD_" + e["zone"].split("_")[1] if e["zone"].startswith("INT_") else e["building"]
    return e["building"] in SCOPE or zone_bld in SCOPE


def clear(world, hinge, start_dir, sign, length, ignore):
    for k in range(0, 10):
        a = math.radians(sign * 90.0 * k / 9)
        d = unreal.Vector(start_dir.x * math.cos(a) - start_dir.y * math.sin(a),
                          start_dir.x * math.sin(a) + start_dir.y * math.cos(a), 0.0)
        for z in (30.0, 100.0, 170.0):
            p0 = unreal.Vector(hinge.x + d.x * 8, hinge.y + d.y * 8, hinge.z + z)
            p1 = unreal.Vector(hinge.x + d.x * length, hinge.y + d.y * length, hinge.z + z)
            h = unreal.SystemLibrary.line_trace_single(world, p0, p1, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                                       ignore, unreal.DrawDebugTrace.NONE, True)
            if h is not None and h.to_tuple()[0]:
                return False
    return True


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues.get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    wpl = unreal.WorldPartitionBlueprintLibrary
    res = wpl.get_actor_descs()
    wpl.load_actors([d.get_editor_property("guid") for d in (res[1] if isinstance(res, tuple) else res)])
    world = ues.get_editor_world()
    with open(os.path.join(REPO, "Saved", "GreyboxExport", "manifest.json"), encoding="utf-8") as fh:
        man = {e["name"]: e for e in json.load(fh)["instances"]}
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    probe = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(12296, 8302, 6000), unreal.Vector(12296, 8302, -3000),
                                                   unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if probe is None or not probe.to_tuple()[0]:
        unreal.log_error("open_doors: traces hit nothing yet (actors just loaded); run the script again")
        return
    doors = {}
    report = {"opened": [], "doorway": [], "no_collision": []}
    for name, e in man.items():
        a = actors.get(name)
        if a is None or not in_scope(e) or not isinstance(a, unreal.StaticMeshActor):
            continue
        if DOUBLE.search(name):
            a.modify()
            c = a.get_editor_property("static_mesh_component")
            c.modify()
            c.set_visibility(False, True)
            c.set_collision_profile_name("NoCollision")   # a profile is saved; set_collision_enabled is runtime-only
            a.set_actor_hidden_in_game(True)
            report["doorway"].append(name)
        elif "Door" in name and (LEAF.search(name) or name.endswith("LandingDoor")):
            doors.setdefault(LEAF.sub("", name), []).append((a, e))
        elif "Door" not in name and LEAF.search(name):      # e.g. dormer glass caught by an earlier pass: restore
            c = a.get_editor_property("static_mesh_component")
            if c.get_collision_profile_name() == "NoCollision":
                a.modify()
                c.modify()
                c.set_collision_profile_name("BlockAll")
        if DOUBLE.search(name) or (name.startswith("GBF_") and "_Entrance_" in name and name.endswith("_Frame")):
            # entrance frames: their box collision includes the centre mullion between the two leaves
            c = a.get_editor_property("static_mesh_component")
            a.modify()
            c.modify()
            c.set_collision_profile_name("NoCollision")   # a profile is saved; set_collision_enabled is runtime-only
    for key, parts in doors.items():
        for a, e in parts:                                   # back to R1's closed pose first (idempotent reruns)
            a.modify()
            a.set_actor_location_and_rotation(unreal.Vector(*e["loc"]), unreal.Rotator(roll=e["rot"][2], pitch=e["rot"][0], yaw=e["rot"][1]), False, False)
        # the tallest part is the door body (upper-floor Door_*_Leaf is only a 9 cm kick plate under the glass)
        o, ext = max((a.get_actor_bounds(False) for a, _ in parts), key=lambda b: b[1].z)
        along_x = ext.x >= ext.y
        width = 2 * (ext.x if along_x else ext.y)
        axis = unreal.Vector(1, 0, 0) if along_x else unreal.Vector(0, 1, 0)
        frame = actors.get(key + "_Frame")
        ignore = [p for p, _ in parts] + ([frame] if frame else [])
        done = False
        for end in (-1, 1):
            hinge = unreal.Vector(o.x + axis.x * end * ext.x, o.y + axis.y * end * ext.y, o.z - ext.z)
            start = unreal.Vector(-axis.x * end, -axis.y * end, 0.0)      # from the hinge across the closed leaf
            for sign in (1, -1):
                if not clear(world, hinge, start, sign, width + 5, ignore):
                    continue
                for a, _ in parts:
                    loc = a.get_actor_location()
                    r = math.radians(sign * 90.0)
                    dx, dy = loc.x - hinge.x, loc.y - hinge.y
                    a.set_actor_location(unreal.Vector(hinge.x + dx * math.cos(r) - dy * math.sin(r),
                                                       hinge.y + dx * math.sin(r) + dy * math.cos(r), loc.z), False, False)
                    rot = a.get_actor_rotation()
                    a.set_actor_rotation(unreal.Rotator(roll=rot.roll, pitch=rot.pitch, yaw=rot.yaw + sign * 90.0), False)
                for a, _ in parts:                         # an open leaf may still stick into a corridor: walk-through
                    c = a.get_editor_property("static_mesh_component")
                    c.modify()
                    c.set_collision_profile_name("NoCollision")   # a profile is saved; set_collision_enabled is runtime-only
                report["opened"].append(key)
                done = True
                break
            if done:
                break
        if not done:
            for a, _ in parts:
                c = a.get_editor_property("static_mesh_component")
                c.modify()
                c.set_collision_profile_name("NoCollision")   # a profile is saved; set_collision_enabled is runtime-only
            report["no_collision"].append(key)
    out = os.path.join(REPO, "Saved", "QA")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "doors.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"open_doors: {len(report['opened'])} opened, {len(report['doorway'])} doorways, "
               f"{len(report['no_collision'])} walk-through, scope {SCOPE}")


main()
