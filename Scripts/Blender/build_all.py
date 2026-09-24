# Rebuilds the whole campus greybox in order: phase-1 terrain/massing, every building spec (Specs/BLD_*.json),
# every site spec (Specs/SITE_*.json), then validates (unique dot-free names, closed manifold meshes). Used by R1.
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_all.py   (saves the file)
import os
import runpy

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
    files = sorted(f[:-5] for f in os.listdir(SPECS) if f.endswith(".json"))
    bld = [f for f in files if f.startswith("BLD_")]
    site = [f for f in files if f.startswith("SITE_")]
    run("build_greybox.py")
    if bld:
        run("build_facades.py", "KOCH_SPECS", bld)
    if site:
        run("build_site.py", "KOCH_SITE", site)
    ok = validate()
    if background:
        bpy.ops.wm.save_mainfile(compress=True)
    print("build_all:", "OK" if ok else "CHECK FAILED", "| buildings:", bld, "| site:", site)


main()
