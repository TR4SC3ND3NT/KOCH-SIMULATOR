# Material slots for the R1 greybox detail kit: one Blender material per real material (UE maps each slot to its
# PBR material later); diffuse_color is only the viewport/Workbench review colour. Used by build_facades.py.
import bmesh
import bpy

# name -> viewport RGBA (review aid; the look comes from UE materials)
PALETTE = {
    "M_Render_Beige": (0.83, 0.78, 0.66, 1), "M_Paint_Maroon": (0.50, 0.16, 0.14, 1),
    "M_PVC_White": (0.94, 0.94, 0.92, 1), "M_Glass": (0.30, 0.40, 0.48, 1), "M_Steel_Galv": (0.72, 0.72, 0.74, 1),
    "M_Steel_Paint_Dark": (0.22, 0.24, 0.26, 1), "M_Granite_Red": (0.52, 0.36, 0.33, 1),
    "M_Tile_Brick_Red": (0.45, 0.20, 0.16, 1), "M_Sheet_Red": (0.55, 0.20, 0.18, 1), "M_Sheet_Brown": (0.35, 0.22, 0.17, 1),
    "M_PVC_Gutter_White": (0.95, 0.95, 0.95, 1), "M_Alu_Black": (0.08, 0.08, 0.09, 1),
    "M_Terracotta_Soffit": (0.75, 0.38, 0.22, 1), "M_Sign_Panel": (0.20, 0.25, 0.45, 1), "M_Concrete": (0.62, 0.61, 0.58, 1),
    "M_Steel_Grating": (0.30, 0.32, 0.34, 1), "M_Sign_Frame_White": (0.90, 0.90, 0.90, 1),
}


def mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.diffuse_color = PALETTE.get(name, (0.7, 0.7, 0.7, 1))
        m["koch_note"] = "greybox slot; the UE material of the same name replaces it"
    return m


def color_mat(rgba):
    """Plain review material for an element that has only a viewport colour (pre-detail builders)."""
    name = "VC_%02x%02x%02x" % tuple(int(round(c * 255)) for c in rgba[:3])
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.diffuse_color = tuple(rgba[:3]) + (1.0,)
    return m


def ensure_slot(me, rgba):
    if rgba is not None and not me.materials:
        me.materials.append(color_mat(rgba))


def parts_to_mesh(name, parts):
    """One mesh from {material_name: bmesh} (each bmesh a closed part); faces keep their part's material slot."""
    me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    me.clear_geometry()
    me.materials.clear()
    out = bmesh.new()
    for slot, (mname, bm) in enumerate(parts.items()):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        tmp = bpy.data.meshes.new("_tmp_part")
        bm.to_mesh(tmp)
        bm.free()
        for p in tmp.polygons:
            p.material_index = slot
        out.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
        me.materials.append(mat(mname))
    out.to_mesh(me)
    out.free()
    return me
