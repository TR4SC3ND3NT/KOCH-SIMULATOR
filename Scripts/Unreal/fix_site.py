# UE 5.8 editor script (R4): level-side fixes over R1's greybox in L_GreyboxTest, found by Scripts/Unreal/qa_scan.py and
# playtests; every fix is an actor tagged KochFix (or a recorded move) and is listed in Saved/QA/fixes.json so R1 can fix
# the source (.blend/specs) and this script can be retired. Idempotent: old KochFix actors are removed and moves are
# applied relative to the manifest position, never accumulated.
#  1 risers   - ground steps (>= RISER_MIN_CM) whose vertical face is missing: the upper terrain is a one-sided sheet, so
#               from below you look under it and see sky. A concrete wall closes each open edge.
#  2 floating - outdoor props hovering 2..200 cm over the surface below are dropped onto it; face terminals sit on their pole
#  3 stairs   - GBS_GateAlley_PavilionStair: rebuilt to its spec (flight down east to the walkway); the mesh is 90 deg off
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/fix_site.py"
import json
import math
import os

import unreal

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
TAG = "KochFix"
CUBE = "/Engine/BasicShapes/Cube"          # 100 cm cube, pivot at the centre, simple box collision
WALL_MAT = "/Game/KochSimulator/Greybox/Materials/MI_Concrete_Precast"
STAIR_MAT = "/Game/KochSimulator/Greybox/Materials/MI_Granite_Red"
X0, X1, Y0, Y1 = -9000.0, 26000.0, -9000.0, 15000.0   # campus core, UE cm
GRID = 50.0
GROUND_PREFIX = "SM_Ground_"              # ground tile actor labels (ue_prep terrain tiles)
VERTICAL_SHARE = 0.8                      # a real step: >= 80 % of the height change happens within +-8 cm of the edge
RISER_MIN_CM, RISER_MAX_CM = 20.0, 300.0
WALL_T = 12.0
FLOAT_MIN, FLOAT_MAX = 2.0, 200.0
SNAP_NO_ROOF_CM = 30.0
# only free-standing street furniture is dropped; wall/fence/canopy-mounted items keep R1's height
FREE_STANDING = ("bench", "bin", "bollard", "sign_aframe", "bike_rack", "waste_container", "planter", "face",
                 "turnstile", "lamp_bollard", "manhole")                    # props with a surface this close above are ceiling/canopy-mounted: leave them


def trace(world, a, b, ignore=()):
    return unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                                  list(ignore), unreal.DrawDebugTrace.NONE, True)


def hit(res):
    """(z or y/x location vector, actor) of a blocking hit, else None."""
    if res is None:
        return None
    t = res.to_tuple()
    return (t[4], t[9]) if t[0] else None


def ground_z(world, x, y, ground_only=False):
    """Top surface z; with ground_only, None unless that surface is one of R1's baked ground tiles (SM_Ground_*)."""
    h = hit(trace(world, unreal.Vector(x, y, 6000), unreal.Vector(x, y, -3000)))
    if h is None or (ground_only and not (h[1] and h[1].get_actor_label().startswith(GROUND_PREFIX))):
        return None
    return h[0].z


def spawn_box(eas, mesh, mat, centre, size, yaw, label, folder):
    a = eas.spawn_actor_from_object(mesh, centre, unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    a.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.set_editor_property("tags", [unreal.Name(TAG)])
    c = a.get_editor_property("static_mesh_component")
    c.set_material(0, mat)
    c.set_mobility(unreal.ComponentMobility.STATIC)
    return a


def find_risers(world):
    """Open ground steps on a GRID lattice, edge refined by bisection; returns [(x, y, axis, side, z_lo, z_hi)]."""
    out = []
    nx, ny = int((X1 - X0) / GRID), int((Y1 - Y0) / GRID)
    rows = []
    with unreal.ScopedSlowTask(nx, "fix_site: ground heights") as task:
        task.make_dialog(True)
        for i in range(nx):
            task.enter_progress_frame(1)
            rows.append([ground_z(world, X0 + i * GRID, Y0 + j * GRID, True) for j in range(ny)])
    for i in range(nx):
        for j in range(ny):
            z = rows[i][j]
            for di, dj, axis in ((1, 0, "x"), (0, 1, "y")):
                if i + di >= nx or j + dj >= ny:
                    continue
                z2 = rows[i + di][j + dj]
                if z is None or z2 is None or not RISER_MIN_CM <= abs(z2 - z) <= RISER_MAX_CM:
                    continue
                p_lo = (X0 + i * GRID, Y0 + j * GRID) if z < z2 else (X0 + (i + di) * GRID, Y0 + (j + dj) * GRID)
                p_hi = (X0 + (i + di) * GRID, Y0 + (j + dj) * GRID) if z < z2 else (X0 + i * GRID, Y0 + j * GRID)
                z_lo, z_hi = min(z, z2), max(z, z2)
                mid = z_lo + min((z_hi - z_lo) * 0.5, 40.0)
                # an existing face between the two samples blocks a horizontal trace at mid height
                if hit(trace(world, unreal.Vector(p_lo[0], p_lo[1], mid), unreal.Vector(p_hi[0], p_hi[1], mid))):
                    continue
                a, b = list(p_lo), list(p_hi)           # bisect the edge position (where the ground rises)
                for _ in range(6):
                    m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
                    zm = ground_z(world, m[0], m[1])
                    if zm is not None and zm > z_lo + (z_hi - z_lo) / 2:
                        b = m
                    else:
                        a = m
                side = 1 if (p_hi[0] - p_lo[0] + p_hi[1] - p_lo[1]) > 0 else -1   # +: high side is +axis
                ex, ey = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                ox, oy = (8.0 * side, 0.0) if axis == "x" else (0.0, 8.0 * side)
                zl, zh = ground_z(world, ex - ox, ey - oy, True), ground_z(world, ex + ox, ey + oy, True)
                if zl is None or zh is None or zh - zl < VERTICAL_SHARE * (z_hi - z_lo):
                    continue                                                   # a slope, not a step
                out.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, axis, side, z_lo, z_hi))
    return out


def merge_risers(segs):
    """Join lattice-length pieces that continue each other along the same edge into long walls."""
    walls = []
    key = lambda s: (s[2], s[3], round(s[0] / 25) if s[2] == "x" else round(s[1] / 25))
    groups = {}
    for s in segs:
        groups.setdefault(key(s), []).append(s)
    for (axis, side, _), g in groups.items():
        g.sort(key=lambda s: s[1] if axis == "x" else s[0])
        run = [g[0]]
        for s in g[1:]:
            prev = run[-1]
            along = (s[1] - prev[1]) if axis == "x" else (s[0] - prev[0])
            if along <= GRID * 1.01 and abs(s[4] - prev[4]) < 15 and abs(s[5] - prev[5]) < 15:
                run.append(s)
            else:
                walls.append((axis, side, run))
                run = [s]
        walls.append((axis, side, run))
    return walls


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
    eas.destroy_actors([a for a in eas.get_all_level_actors() if a.actor_has_tag(TAG)])
    cube = unreal.EditorAssetLibrary.load_asset(CUBE)
    wall_mat = unreal.EditorAssetLibrary.load_asset(WALL_MAT)
    stair_mat = unreal.EditorAssetLibrary.load_asset(STAIR_MAT)
    with open(os.path.join(REPO, "Saved", "GreyboxExport", "manifest.json"), encoding="utf-8") as fh:
        man = {e["name"]: e for e in json.load(fh)["instances"]}
    report = {"risers": [], "floating": [], "stairs": []}
    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}

    # 1 risers
    for axis, side, run in merge_risers(find_risers(world)):
        z_lo = min(s[4] for s in run) - 5.0               # 5 cm into the lower ground so no light slit shows
        z_hi = max(s[5] for s in run)
        along = [s[1] if axis == "x" else s[0] for s in run]
        across = sum(s[0] if axis == "x" else s[1] for s in run) / len(run) + side * WALL_T / 2   # on the high side
        length = max(along) - min(along) + GRID
        mid_along = (max(along) + min(along)) / 2
        cx, cy = (across, mid_along) if axis == "x" else (mid_along, across)
        size = (WALL_T, length, z_hi - z_lo) if axis == "x" else (length, WALL_T, z_hi - z_lo)
        spawn_box(eas, cube, wall_mat, unreal.Vector(cx, cy, (z_lo + z_hi) / 2), size, 0.0,
                  f"FIX_Riser_{len(report['risers']):03d}", "Fixes/Risers")
        report["risers"].append({"centre_cm": [round(cx), round(cy)], "axis": axis, "length_cm": round(length),
                                 "z_cm": [round(z_lo + 5), round(z_hi)]})

    # 2 floating props (re-measured here, not trusted from the old scan)
    for label, a in actors.items():
        e = man.get(label)
        if e is None or e["zone"].startswith(("INT", "Ground", "CTX")) or not isinstance(a, unreal.StaticMeshActor):
            continue
        kind = (e.get("ue_asset") or "").lower()
        if not (kind.startswith(FREE_STANDING) or "FaceTerminal" in label):
            if a.get_actor_location() != unreal.Vector(*e["loc"]):
                a.set_actor_location(unreal.Vector(*e["loc"]), False, False)   # undo an earlier, wider pass
            continue
        comp = a.get_editor_property("static_mesh_component")
        if not comp.is_visible():
            continue
        loc0 = unreal.Vector(*e["loc"])
        a.set_actor_location(loc0, False, False)          # back to R1's position before measuring
        origin, ext = a.get_actor_bounds(False)
        if max(ext.x, ext.y) > 125 or ext.z > 250:
            continue
        bottom, top = origin.z - ext.z, origin.z + ext.z
        if hit(trace(world, unreal.Vector(origin.x, origin.y, top + 1), unreal.Vector(origin.x, origin.y, top + SNAP_NO_ROOF_CM), [a])):
            continue
        below = [hit(trace(world, unreal.Vector(origin.x + sx * ext.x * 0.7, origin.y + sy * ext.y * 0.7, bottom + 1),
                           unreal.Vector(origin.x + sx * ext.x * 0.7, origin.y + sy * ext.y * 0.7, bottom - FLOAT_MAX - 5), [a]))
                 for sx, sy in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))]
        zs = [h[0].z for h in below if h]
        if not zs:
            continue
        gap = bottom - max(zs)
        if "FaceTerminal" in label or (e.get("ue_asset") or "").startswith("face"):
            pass                                            # sits on its pole: the pole top is the highest hit
        elif not FLOAT_MIN <= gap <= FLOAT_MAX:
            continue
        if gap <= 0.5:
            continue
        a.set_actor_location(unreal.Vector(loc0.x, loc0.y, loc0.z - gap), False, False)
        report["floating"].append({"name": label, "zone": e["zone"], "ue_asset": e.get("ue_asset") or "", "dropped_cm": round(gap, 1)})

    # 3 pavilion stair: the built mesh runs its steps north/south (yaw off by 90) with a 1.2 m wall facing the walkway;
    #   the spec (SITE_GateAlley.json "PavilionStair": dir_deg -2.808 = east, tread 0.34, width 3.88, top x 155.632) has
    #   the flight going down EAST to the walkway. Rebuild it: hide the mesh, cheeks on both sides at landing height,
    #   treads descending east from the landing to the walkway.
    st = actors.get("GBS_GateAlley_PavilionStair")
    if st is not None:
        o, ext = st.get_actor_bounds(False)
        x0, x1, y0, y1, zb = o.x - ext.x, o.x + ext.x, o.y - ext.y, o.y + ext.y, o.z - ext.z
        top_x, mid_y, width, tread = 15563.2, 8366.7, 388.0, 34.0     # spec top (155.632, -83.667) m -> UE cm
        hz = hit(trace(world, unreal.Vector(top_x - 20, mid_y, zb + 2 * ext.z + 30), unreal.Vector(top_x - 20, mid_y, zb - 100)))
        hw = hit(trace(world, unreal.Vector(x1 + 30, mid_y, zb + 2 * ext.z + 30), unreal.Vector(x1 + 30, mid_y, zb - 100)))
        if hz and hw:
            z_top, z_walk = hz[0].z, hw[0].z
            n = max(2, round((z_top - z_walk) / 17.5))
            rise = (z_top - z_walk) / n
            comp = st.get_editor_property("static_mesh_component")
            comp.set_visibility(False, True)
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            sy0, sy1 = mid_y - width / 2, mid_y + width / 2

            def box(xa, xb, ya, yb, za, zb_, name):
                spawn_box(eas, cube, stair_mat, unreal.Vector((xa + xb) / 2, (ya + yb) / 2, (za + zb_) / 2),
                          (xb - xa, yb - ya, zb_ - za), 0.0, name, "Fixes/Stairs")

            box(x0, x1, y0, sy0, zb, z_top, "FIX_PavilionStair_CheekN")      # where the mesh's wrong north steps were
            box(x0, x1, sy1, y1, zb, z_top, "FIX_PavilionStair_CheekS")
            box(x0, top_x, sy0, sy1, zb, z_top, "FIX_PavilionStair_Landing")
            for k in range(1, n):                                            # tread k top = z_top - k*rise
                xa, xb = top_x + (k - 1) * tread, top_x + k * tread
                box(xa, xb, sy0, sy1, zb, z_top - k * rise, f"FIX_PavilionStair_Tread{k}")
            last = top_x + (n - 1) * tread
            if last < x1:                                                    # rest of the old footprint at walkway level
                box(last, x1, sy0, sy1, zb, z_walk, "FIX_PavilionStair_Foot")
            report["stairs"].append({"name": "GBS_GateAlley_PavilionStair", "rebuilt": "flight down east per spec",
                                     "risers": n, "rise_cm": round(rise, 1), "tread_cm": tread,
                                     "z_top_cm": round(z_top), "z_walkway_cm": round(z_walk),
                                     "why": "mesh steps run N/S (90 deg off spec dir_deg -2.808), 1.2 m wall faced the walkway"})
        else:
            unreal.log_warning("fix_site: PavilionStair heights not found, stair left as is")

    out = os.path.join(REPO, "Saved", "QA")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "fixes.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"fix_site: {len(report['risers'])} riser walls, {len(report['floating'])} props dropped, "
               f"{len(report['stairs'])} stairs extended")


main()
