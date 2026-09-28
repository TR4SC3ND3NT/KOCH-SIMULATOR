# Rebuilds the whole campus greybox in order: phase-1 terrain/massing, every building spec (Specs/BLD_*.json),
# every site spec (Specs/SITE_*.json), the clean-up pass (greybox/finalize.py), then validates (unique dot-free names, closed manifold meshes). Used by R1.
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_all.py   (saves the file)
import os
import runpy
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.abspath(os.path.join(HERE, "..", "..", "Art", "Blender", "Specs"))


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


def main():
    background = bpy.app.background
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
        bpy.ops.wm.save_mainfile(compress=True)
    elif background:
        print("build_all: NOT SAVED (fix the failures above)")
    print("build_all:", "OK" if ok else "CHECK FAILED", "| buildings:", bld, "| site:", site)


main()
