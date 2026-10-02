# Rebuilds the whole campus greybox in order: phase-1 terrain/massing, every building spec (Specs/BLD_*.json),
# every site spec (Specs/SITE_*.json), the clean-up pass (greybox/finalize.py), then validates (unique dot-free names, closed manifold meshes). Used by R1.
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_all.py   (saves the file)
#  or, without the LFS .blend: blender -b -P Scripts/Blender/build_all.py   (builds from an empty scene and saves to
#  Art/Blender/KOCH_Campus_Greybox.blend, or to $KOCH_BLEND_OUT). Everything comes from Specs/, Data/ and these scripts.
import json
import math
import os
import runpy
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.abspath(os.path.join(HERE, "..", "..", "Art", "Blender", "Specs"))
DATA = os.path.join(os.path.dirname(SPECS), "Data")
DEFAULT_BLEND = os.path.join(os.path.dirname(SPECS), "KOCH_Campus_Greybox.blend")


def run(script, env_key=None, ids=()):
    if env_key:
        os.environ[env_key] = ",".join(ids)
    runpy.run_path(os.path.join(HERE, script), run_name="__main__")


def validate():
    bad_names, open_meshes, seen = [], [], set()
    for ob in bpy.data.objects:
        if not ob.get("koch_gen") or ob.name.startswith(("TER_", "REF_")):  # terrain/reference are open by design
            continue
        if "." in ob.name:
            bad_names.append(ob.name)
        if ob.type == "MESH" and ob.data.name not in seen:
            seen.add(ob.data.name)
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            if any(not e.is_manifold for e in bm.edges):
                open_meshes.append(ob.name)
            bm.free()
    print(f"validate: {len(seen)} meshes, {len(bad_names)} dotted names {bad_names[:5]}, "
          f"{len(open_meshes)} non-manifold {open_meshes[:5]}")
    return not bad_names and not open_meshes


def clear_startup_scene():
    """New (unsaved) file: drop the factory startup objects (cube, light, camera) so the build starts empty."""
    if bpy.data.filepath:
        return
    for ob in [o for o in bpy.data.objects if not o.get("koch_gen") and o.name.split(".")[0] in ("Cube", "Light", "Camera")]:
        bpy.data.objects.remove(ob, do_unlink=True)   # their orphaned mesh/light/camera data is not saved
    col = bpy.data.collections.get("Collection")
    if col is not None and not col.objects and not col.children:
        bpy.data.collections.remove(col)
    sys.path.insert(0, HERE)
    from init_campus_file import setup_scene   # metric units, collection tree, viewport clipping
    setup_scene()


def build_review_cameras():
    """Review cameras (00_Reference) from Data/review_cameras.json: created or updated in place, never duplicated."""
    path = os.path.join(DATA, "review_cameras.json")
    if not os.path.exists(path):
        return 0
    from greybox.common import ensure_collection
    spec = json.load(open(path))
    col = ensure_collection("00_Reference")
    for c in spec["cameras"]:
        ob = bpy.data.objects.get(c["name"])
        if ob is None or ob.type != "CAMERA":
            ob = bpy.data.objects.new(c["name"], bpy.data.cameras.new(c["name"]))
            col.objects.link(ob)
        ob.location = c["location"]
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = [math.radians(a) for a in c["rotation_deg"]]
        ob.data.lens, ob.data.sensor_width = c["lens"], c.get("sensor_width", 36.0)
        ob.data.clip_start, ob.data.clip_end = 0.1, c.get("clip_end", 1000.0)
        if c.get("notes"):
            ob["koch_notes"] = c["notes"]
    act = bpy.data.objects.get(spec.get("active", ""))
    if act is not None:
        bpy.context.scene.camera = act
    return len(spec["cameras"])


def main():
    background = bpy.app.background
    os.environ["KOCH_BUILD_ALL"] = "1"   # sub-builders skip their own save: no half-built file on disk
    clear_startup_scene()
    # a live Blender session keeps imported helper modules: drop them so edited kit/common/sweep code is used
    for m in [m for m in sys.modules if m == "greybox" or m.startswith("greybox.")]:
        del sys.modules[m]
    files = sorted(f[:-5] for f in os.listdir(SPECS) if f.endswith(".json"))
    bld = [f for f in files if f.startswith("BLD_")]
    site = [f for f in files if f.startswith(("SITE_", "INT_"))]  # INT_* = interiors, same element builder
    bpy.app.driver_namespace["koch_build_failures"] = []
    run("build_greybox.py")
    if os.path.exists(os.path.join(os.path.dirname(SPECS), "Data", "ctx_osm.json")):
        run("build_context.py")   # surroundings ring from OSM (P0 massing)
    if bld:
        run("build_facades.py", "KOCH_SPECS", bld)
    if site:
        run("build_site.py", "KOCH_SITE", site)
    sys.path.insert(0, HERE)
    print("review cameras:", build_review_cameras())
    from greybox.materials import assign_ground_surfaces, assign_name_slots
    print("material slots by name:", assign_name_slots(bpy.data.objects))
    print("ground surfaces:", assign_ground_surfaces(bpy.data.objects.get("TER_Ground"), SPECS))
    from greybox.finalize import run as finalize
    print("finalize:", {k: (v if not isinstance(v, list) else (len(v), v[:4])) for k, v in finalize().items()})
    ok = validate()
    fails = bpy.app.driver_namespace.get("koch_build_failures", [])
    if fails:   # a failed building/element must not be saved silently (a missing Block C was committed once)
        print(f"build failures ({len(fails)}):", "; ".join(fails[:10]))
        ok = False
    # detail-kit parts carry several material slots: show material colours in every 3D view and in Workbench
    for scr in bpy.data.screens:
        for area in scr.areas:
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.color_type = "MATERIAL"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    if background and ok:
        out = os.environ.get("KOCH_BLEND_OUT") or bpy.data.filepath or DEFAULT_BLEND
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
        print("saved", out)
    elif background:
        print("build_all: NOT SAVED (fix the failures above)")
    print("build_all:", "OK" if ok else "CHECK FAILED", "| buildings:", bld, "| site:", site)


main()
