# Imports the RealityScan site mesh as REF_Photogrammetry (R1, handoff section 4.1). The mesh shows people/texture and
# is large, so it never goes into git: it is saved into Art/Blender/Reference/REF_Photogrammetry.blend (gitignored)
# and only LINKED into the greybox file's 00_Reference collection (locked, never exported; builders skip REF_*).
# Step 1 (fresh Blender): OBJ in the RealityScan grid frame -> world via align.json (world = s R x + t), saved:
#   KOCH_REF_OBJ=mesh.obj KOCH_REF_ALIGN=align.json blender -b --factory-startup -P Scripts/Blender/import_photogrammetry.py
# Step 2 (link into the greybox; saves it):
#   KOCH_REF_LINK=1 blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/import_photogrammetry.py
import json
import os

import bpy
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
REF_BLEND = os.path.abspath(os.path.join(HERE, "..", "..", "Art", "Blender", "Reference", "REF_Photogrammetry.blend"))
NAME = "REF_Photogrammetry"


def import_mesh():
    obj, al = os.environ["KOCH_REF_OBJ"], json.load(open(os.environ["KOCH_REF_ALIGN"]))
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    # RealityScan OBJ is Z-up with the grid axes as they are: keep them (no axis conversion)
    bpy.ops.wm.obj_import(filepath=obj, forward_axis="Y", up_axis="Z", validate_meshes=False)
    parts = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    s, R, t = al["scale"], Matrix(al["R"]), al["t"]
    M = Matrix.Translation(t) @ Matrix.Diagonal((s, s, s, 1.0)) @ R.to_4x4()
    col = bpy.data.collections.get(NAME) or bpy.data.collections.new(NAME)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for i, ob in enumerate(parts):
        ob.data.transform(M)          # bake: vertex coordinates become campus world metres
        ob.matrix_world = Matrix.Identity(4)
        ob.name = NAME if len(parts) == 1 else f"{NAME}_{i:02d}"
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
        ob.hide_select = True
        ob.hide_render = True
        ob["koch_notes"] = f"photogrammetry reference (RealityScan 2.2), {os.path.basename(obj)}; never export"
    os.makedirs(os.path.dirname(REF_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=REF_BLEND, compress=True)
    print(f"saved {REF_BLEND}: {len(parts)} objects, {sum(len(o.data.polygons) for o in parts)} faces")


def link_into_greybox():
    ref = bpy.data.collections.get("00_Reference") or bpy.data.collections.new("00_Reference")
    old = bpy.data.collections.get(NAME)
    if old and old.library:
        for p in [c for c in bpy.data.collections if old.name in c.children]:
            p.children.unlink(old)
    rel = bpy.path.relpath(REF_BLEND)
    with bpy.data.libraries.load(rel, link=True) as (src, dst):
        dst.collections = [NAME] if NAME in src.collections else []
    col = dst.collections[0] if dst.collections else None
    if col is None:
        raise SystemExit(f"{REF_BLEND} has no collection {NAME}")
    if col.name not in ref.children:
        ref.children.link(col)
    bpy.ops.wm.save_mainfile(compress=True)
    print(f"linked {col.name} from {rel} into 00_Reference")


if os.environ.get("KOCH_REF_LINK"):
    link_into_greybox()
else:
    import_mesh()
