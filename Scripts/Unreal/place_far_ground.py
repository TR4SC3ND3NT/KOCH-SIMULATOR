# UE 5.8 editor script (R4 -> everyone): far ground under the context city. R1's terrain tiles stop ~200 m around the
# campus while the OSM context blocks reach 800 m out, so they stood on nothing and the sky showed under them and at
# the tile edge (owner playtest 2026-10-27). Builds SM_FarGround (MeshDescription, 16 km): heights interpolated (IDW)
# from the context buildings' bases (+BURY, so none floats) and terrain traces (-DROP, so it never pokes through the
# campus tiles); beyond the data it eases into a least-squares plane. Three steps (the mesh is built in Blender):
#   py "<repo>/Scripts/Unreal/place_far_ground.py" --sample     -> Saved/FarGround/grid.json
#   blender -b -P Scripts/Blender/build_far_ground.py -- Saved/FarGround/grid.json Saved/FarGround/SM_FarGround.fbx
#   py "<repo>/Scripts/Unreal/place_far_ground.py"              -> import + place (re-run replaces)
import json
import os
import sys

import unreal

LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
PATH = "/Game/KochSimulator/Environment/FarGround"
NAME = "SM_FarGround"
MI = "/Game/KochSimulator/Greybox/Materials/MI_Ground_Grass"
CTX = ("CTX_", "GB_CTX_", "GB_BLD_")
TAG = "KochFarGround"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Saved", "FarGround")
STEP, INNER = 5000.0, 120000.0        # cm: fine grid spacing / half size; outer rings below reach the horizon
OUTER = (200000.0, 400000.0, 800000.0)
TER_STEP = 2500.0                     # cm: terrain trace spacing
BURY, DROP = 40.0, 150.0              # cm: under building bases / under the campus terrain
RADIUS = 40000.0                      # cm: IDW reach; nodes farther from all data take the plane


def samples(world, actors):
    """[(x, y, z, kind)] kind 0 = building base, 1 = terrain; plus the ground tile XY boxes."""
    pts, tiles = [], []
    for a in actors:
        label = a.get_actor_label()
        if label.startswith(CTX):
            o, e = a.get_actor_bounds(False)
            z = o.z - e.z + BURY
            for sx, sy in ((0, 0), (-0.8, -0.8), (0.8, -0.8), (-0.8, 0.8), (0.8, 0.8)):
                pts.append((o.x + sx * e.x, o.y + sy * e.y, z, 0))
        elif label.startswith("SM_Ground_"):
            o, e = a.get_actor_bounds(False)
            tiles.append((o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y))
    for x0, y0, x1, y1 in tiles:
        x = x0 + TER_STEP * 0.5
        while x < x1:
            y = y0 + TER_STEP * 0.5
            while y < y1:
                h = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 20000), unreal.Vector(x, y, -20000),
                                                           unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
                                                           unreal.DrawDebugTrace.NONE, True)
                t = h.to_tuple() if h is not None else None
                if t and t[0] and t[9] and t[9].get_actor_label().startswith("SM_Ground_"):
                    pts.append((x, y, t[4].z - DROP, 1))
                y += TER_STEP
            x += TER_STEP
    return pts, tiles


def plane_fit(pts):
    """Least squares z = a x + b y + c (3x3 normal equations, Cramer)."""
    sxx = sxy = syy = sx = sy = n = sxz = syz = sz = 0.0
    for x, y, z, _ in pts:
        x, y = x / 1e5, y / 1e5
        sxx += x * x; sxy += x * y; syy += y * y; sx += x; sy += y; n += 1
        sxz += x * z; syz += y * z; sz += z
    m = ((sxx, sxy, sx), (sxy, syy, sy), (sx, sy, n))
    r = (sxz, syz, sz)

    def det(a):
        return (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
                + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    d = det(m)
    sol = []
    for c in range(3):
        mc = [list(row) for row in m]
        for i in range(3):
            mc[i][c] = r[i]
        sol.append(det(mc) / d)
    a, b, c = sol
    return lambda x, y: a * x / 1e5 + b * y / 1e5 + c


def height(x, y, pts, plane, tiles):
    inside = any(x0 - STEP <= x <= x1 + STEP and y0 - STEP <= y <= y1 + STEP for x0, y0, x1, y1 in tiles)
    wsum = zsum = 0.0
    zmin = None
    for px, py, pz, kind in pts:
        d2 = (px - x) ** 2 + (py - y) ** 2
        if d2 > RADIUS * RADIUS:
            continue
        if inside and kind == 1 and d2 < (STEP * 1.5) ** 2:
            zmin = pz if zmin is None else min(zmin, pz)
        w = 1.0 / (d2 + 1e6)
        wsum += w
        zsum += w * pz
    if inside and zmin is not None:
        return zmin                     # under the campus tiles: below every terrain sample around the node
    zp = plane(x, y)
    if wsum == 0.0:
        return zp
    near = min(1.0, wsum * 1e6 * 4.0)  # fades to the plane where only far samples contribute
    return zp + (zsum / wsum - zp) * near


def import_fbx(fbx):
    p = unreal.InterchangeGenericAssetsPipeline()
    mp = p.get_editor_property("mesh_pipeline")
    mp.set_editor_property("build_nanite", True)
    mp.set_editor_property("collision", False)
    mp.set_editor_property("generate_lightmap_u_vs", False)
    p.get_editor_property("material_pipeline").set_editor_property("import_materials", False)
    p.set_editor_property("asset_name", NAME)
    ov = unreal.InterchangePipelineStackOverride()
    ov.add_pipeline(p)
    t = unreal.AssetImportTask()
    for k, v in (("filename", fbx), ("destination_path", PATH), ("automated", True), ("replace_existing", True),
                 ("save", False), ("options", ov)):
        t.set_editor_property(k, v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return next(o for o in t.get_objects() if isinstance(o, unreal.StaticMesh))


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
    if "--sample" in sys.argv:
        pts, tiles = samples(world, actors)
        plane = plane_fit(pts)
        k = int(INNER / STEP)
        coords = sorted({-o for o in OUTER} | {o for o in OUTER} | {s * STEP for s in range(-k, k + 1)})
        zf = [[round(height(x, y, pts, plane, tiles), 1) for y in coords] for x in coords]
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "grid.json"), "w", encoding="utf-8") as fh:
            json.dump({"coords": coords, "z": zf}, fh)
        unreal.log(f"place_far_ground: sampled {len(pts)} points, {len(tiles)} tiles, {len(coords) ** 2} vertices")
        return
    sm = import_fbx(os.path.join(OUT, "SM_FarGround.fbx"))
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    bs = sms.get_lod_build_settings(sm, 0)
    bs.set_editor_property("distance_field_resolution_scale", 0.0)   # a 16 km SDF is mush and darkens Lumen
    sms.set_lod_build_settings(sm, 0, bs)
    sm.set_material(0, unreal.EditorAssetLibrary.load_asset(MI))
    unreal.EditorAssetLibrary.save_loaded_asset(sm, False)
    eas.destroy_actors([a for a in actors if a.actor_has_tag(TAG)])
    a = eas.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0))
    a.set_actor_label("FarGround")
    a.set_folder_path("Environment")
    a.set_editor_property("tags", [unreal.Name(TAG)])
    comp = a.get_editor_property("static_mesh_component")
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    comp.set_collision_profile_name("NoCollision")      # beyond the map barrier, never walked on
    comp.set_editor_property("affect_distance_field_lighting", False)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("place_far_ground: placed")


main()
