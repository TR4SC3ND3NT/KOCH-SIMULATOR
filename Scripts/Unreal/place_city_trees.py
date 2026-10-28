# UE 5.8 editor script (R4 -> everyone): yard trees in the context city around the campus (the OSM blocks stood on
# bare far ground). One always-loaded actor with a HierarchicalInstancedStaticMeshComponent per mesh (Poly Haven fir
# + shrub variants, Nanite): ~1k instances cost a few primitives, culled past CULL_CM. Jittered grid, kept off the
# context buildings (+CLEAR_CM) and out of the campus core (R1 places those trees); z from the ground tiles, else
# from the far-ground grid (Saved/FarGround/grid.json, place_far_ground.py). Deterministic, re-running replaces.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/place_city_trees.py"
import json
import math
import os
import random

import unreal

LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
VEG = "/Game/KochSimulator/Environment/Vegetation/PolyHaven/Meshes"
# (mesh, weight, scale range): the Poly Haven fir is a young 5 m tree; yard spruces in the blocks are 10-15 m
MESHES = [("SM_PH_FirTree01_A", 3, (1.8, 2.8)), ("SM_PH_FirTree01_B", 3, (1.8, 2.8)), ("SM_PH_FirTree01_C", 3, (1.8, 2.8)),
          ("SM_PH_Shrub02_A", 1, (1.0, 1.5)), ("SM_PH_Shrub02_C", 1, (1.0, 1.5))]
AREA = (-70000.0, 75000.0, -65000.0, 52000.0)                       # cm, the OSM context extent
CORE = (-9500.0, 26500.0, -9500.0, 15500.0)                         # campus: R1's own trees
STEP, JITTER, KEEP = 3000.0, 1100.0, 0.55                           # grid cm, +- cm, share of cells planted
CLEAR_CM = 450.0
CULL_CM = 60000.0
CTX = ("CTX_", "GB_CTX_", "GB_BLD_")
TAG = "KochCityTrees"
GRID = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Saved", "FarGround", "grid.json")


def far_ground():
    """Bilinear z (cm) on the far-ground grid."""
    with open(GRID, encoding="utf-8") as fh:
        g = json.load(fh)
    c, z = g["coords"], g["z"]

    def at(x, y):
        i = max(0, min(len(c) - 2, next((k for k in range(len(c) - 1) if c[k + 1] >= x), len(c) - 2)))
        j = max(0, min(len(c) - 2, next((k for k in range(len(c) - 1) if c[k + 1] >= y), len(c) - 2)))
        tx = (x - c[i]) / (c[i + 1] - c[i])
        ty = (y - c[j]) / (c[j + 1] - c[j])
        return ((1 - tx) * (1 - ty) * z[i][j] + tx * (1 - ty) * z[i + 1][j] + (1 - tx) * ty * z[i][j + 1]
                + tx * ty * z[i + 1][j + 1])
    return at


def prepare(mesh):
    """Fir/shrub cards: instanced-mesh usage on their materials, and Nanite voxelised foliage (5.8, needs
    r.Nanite.AllowVoxels) so the far canopy keeps its density instead of thinning to bare twigs."""
    for sl in mesh.get_editor_property("static_materials"):
        base = sl.get_editor_property("material_interface").get_base_material()
        if not base.get_editor_property("used_with_instanced_static_meshes"):
            base.set_editor_property("used_with_instanced_static_meshes", True)
            unreal.MaterialEditingLibrary.recompile_material(base)
            unreal.EditorAssetLibrary.save_loaded_asset(base, False)
    ns = mesh.get_editor_property("nanite_settings")
    if ns.get_editor_property("shape_preservation") != unreal.NaniteShapePreservation.VOXELIZE:
        ns.set_editor_property("shape_preservation", unreal.NaniteShapePreservation.VOXELIZE)
        unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).set_nanite_settings(mesh, ns, True)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)


def add_hism(actor, mesh):
    """New HISM on a placed actor through the subobject system (Python cannot construct components directly)."""
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_instance(actor)
    root = handles[1] if len(handles) > 1 else handles[0]       # [actor, root component, ...]
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", root)
    params.set_editor_property("new_class", unreal.HierarchicalInstancedStaticMeshComponent)
    handle, fail = sds.add_new_subobject(params)
    if not fail.is_empty():
        raise RuntimeError(f"place_city_trees: {fail}")
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    comp = lib.get_object(lib.get_data(handle))
    comp.set_static_mesh(mesh)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    comp.set_collision_profile_name("NoCollision")
    comp.set_editor_property("instance_end_cull_distance", int(CULL_CM))
    return comp


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
    eas.destroy_actors([a for a in actors if a.actor_has_tag(TAG)])
    blocks = []
    for a in actors:
        if a.get_actor_label().startswith(CTX):
            o, e = a.get_actor_bounds(False)
            blocks.append((o.x - e.x - CLEAR_CM, o.x + e.x + CLEAR_CM, o.y - e.y - CLEAR_CM, o.y + e.y + CLEAR_CM))
    ground = far_ground()
    rnd = random.Random(1956)
    picks = [(m, sc) for m, w, sc in MESHES for _ in range(w)]
    spots = {m: [] for m, _, _ in MESHES}
    x = AREA[0]
    while x < AREA[1]:
        y = AREA[2]
        while y < AREA[3]:
            px, py = x + rnd.uniform(-JITTER, JITTER), y + rnd.uniform(-JITTER, JITTER)
            keep = rnd.random() < KEEP
            mesh, rng = rnd.choice(picks)
            yaw, scale = rnd.uniform(0, 360), rnd.uniform(*rng)
            y += STEP
            if not keep or (CORE[0] < px < CORE[1] and CORE[2] < py < CORE[3]):
                continue
            if any(b[0] < px < b[1] and b[2] < py < b[3] for b in blocks):
                continue
            h = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(px, py, 20000), unreal.Vector(px, py, -20000),
                                                       unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
                                                       unreal.DrawDebugTrace.NONE, True)
            t = h.to_tuple() if h is not None else None
            if t and t[0]:
                if not (t[9] and t[9].get_actor_label().startswith("SM_Ground_")):
                    continue                                   # landed on something else (a roof, a wall)
                z = t[4].z
            else:
                z = ground(px, py)
            spots[mesh].append(unreal.Transform(unreal.Vector(px, py, z - 5.0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw),
                                                unreal.Vector(scale, scale, scale)))
        x += STEP
    holder = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))   # empty root to hang HISMs on
    holder.set_actor_label("CityTrees")
    holder.set_folder_path("Environment")
    holder.set_editor_property("tags", [unreal.Name(TAG)])
    total = 0
    for name, tfs in spots.items():
        mesh = unreal.EditorAssetLibrary.load_asset(f"{VEG}/{name}")
        if mesh is None or not tfs:
            continue
        prepare(mesh)
        comp = add_hism(holder, mesh)
        comp.add_instances(tfs, False, True)
        total += len(tfs)
    holder.set_editor_property("is_spatially_loaded", False)   # skyline: never streams out (see set_streaming.py)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"place_city_trees: {total} trees, {len(blocks)} blocks avoided")


main()
