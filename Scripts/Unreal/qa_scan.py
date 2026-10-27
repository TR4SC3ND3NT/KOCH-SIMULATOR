# UE 5.8 editor QA scan (R4 -> R1/everyone) of L_GreyboxTest, writes Saved/QA/scan.json:
#  holes     - 1 m grid of downward line traces over the campus; a column with no hit between +60 m and -30 m is a hole
#              in the walkable surface (sky shows through)
#  floating  - greybox props/placeholders (not ground, not walls) whose bounds bottom has no surface within GAP_CM below
#              its centre and its four bottom corners (wall-mounted items that touch a wall are skipped)
#  visible_placeholders - placeholder actors whose ue_asset tag is replaced by vegetation but which still render
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/qa_scan.py" [GRID_CM]
import json
import os
import sys

import unreal

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
GRID_CM = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0
GAP_CM = 8.0
# campus core in UE cm (manifest extents without the far OSM context ring)
X0, X1, Y0, Y1 = -9000.0, 26000.0, -9000.0, 15000.0
REPLACED = {"tree_cone", "conifer_small", "spruce_blue", "tree_round", "tree_ellipsoid", "tree_deciduous_young",
            "tree_deciduous_whitewashed", "shrub_rose", "shrub_rose_red", "rose_bush", "shrub_loose"}


def trace(world, a, b, ignore=()):
    hit = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                                 list(ignore), unreal.DrawDebugTrace.NONE, True)
    return hit[1] if isinstance(hit, tuple) else hit


def hit_z(res):
    if res is None:
        return None
    t = res.to_tuple()
    return t[4].z if t[0] else None   # (blocking, initial_overlap, time, distance, location, ...)


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues.get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    wpl = unreal.WorldPartitionBlueprintLibrary
    res = wpl.get_actor_descs()
    wpl.load_actors([d.get_editor_property("guid") for d in (res[1] if isinstance(res, tuple) else res)])
    world = ues.get_editor_world()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()

    holes = []
    x = X0
    with unreal.ScopedSlowTask(int((X1 - X0) / GRID_CM), "QA: hole scan") as task:
        task.make_dialog(True)
        while x < X1:
            task.enter_progress_frame(1)
            y = Y0
            while y < Y1:
                if hit_z(trace(world, unreal.Vector(x, y, 6000), unreal.Vector(x, y, -3000))) is None:
                    holes.append([round(x), round(y)])
                y += GRID_CM
            x += GRID_CM

    floating, visible = [], []
    for a in actors:
        tags = [str(t) for t in a.tags]
        if "KochGreybox" not in tags:
            continue
        ue_asset = next((t.split(":", 1)[1] for t in tags if t.startswith("UEAsset:")), "")
        comp = a.get_editor_property("static_mesh_component") if isinstance(a, unreal.StaticMeshActor) else None
        if ue_asset in REPLACED and comp is not None and comp.is_visible():
            visible.append({"name": a.get_actor_label(), "ue_asset": ue_asset})
        zone = next((t.split(":", 1)[1] for t in tags if t.startswith("KochZone:")), "")
        if comp is None or not comp.is_visible() or zone.startswith(("Ground", "CTX")):
            continue
        origin, ext = a.get_actor_bounds(False)
        if ext.z > 400 or ext.x > 1500 or ext.y > 1500:   # buildings, walls, big slabs are not "props"
            continue
        bottom = origin.z - ext.z
        probes = [(origin.x, origin.y)] + [(origin.x + sx * ext.x * 0.8, origin.y + sy * ext.y * 0.8)
                                          for sx in (-1, 1) for sy in (-1, 1)]
        supported = False
        for px, py in probes:
            z = hit_z(trace(world, unreal.Vector(px, py, bottom + 2), unreal.Vector(px, py, bottom - GAP_CM), [a]))
            if z is not None:
                supported = True
                break
        if not supported:   # ceiling-mounted? a surface within GAP_CM above the top
            top = origin.z + ext.z
            if hit_z(trace(world, unreal.Vector(origin.x, origin.y, top - 2), unreal.Vector(origin.x, origin.y, top + GAP_CM), [a])) is not None:
                supported = True
        if not supported:   # wall-mounted? look sideways for a surface within 5 cm
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                s = unreal.Vector(origin.x, origin.y, origin.z)
                e = unreal.Vector(origin.x + dx * (ext.x + 5), origin.y + dy * (ext.y + 5), origin.z)
                if hit_z(trace(world, s, e, [a])) is not None:
                    supported = True
                    break
        if not supported:
            below = hit_z(trace(world, unreal.Vector(origin.x, origin.y, bottom), unreal.Vector(origin.x, origin.y, bottom - 3000), [a]))
            floating.append({"name": a.get_actor_label(), "ue_asset": ue_asset, "zone": zone,
                             "loc": [round(origin.x), round(origin.y), round(bottom)],
                             "gap_cm": round(bottom - below) if below is not None else None})

    out = os.path.join(REPO, "Saved", "QA")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "scan.json"), "w", encoding="utf-8") as fh:
        json.dump({"grid_cm": GRID_CM, "holes": holes, "floating": floating, "visible_placeholders": visible}, fh, indent=1)
    unreal.log(f"qa_scan: {len(holes)} hole samples, {len(floating)} floating, {len(visible)} visible placeholders")


main()
