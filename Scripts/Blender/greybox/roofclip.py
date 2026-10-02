# Attic-storey support for pitched roofs (R1): hollows a solid roof into a shell with a sloped underside, and clips
# interior elements of the storey inside the roof to that underside. Used by build_facades.py (roof "shell") and
# build_site.py (element "clip_roof"). Exact booleans through the Boolean modifier, applied via the evaluated mesh.
import bmesh
import bpy
from mathutils import Vector

from greybox.materials import mat

_CUTTERS = {}   # roof object name -> cutter object (solid above the roof underside), built once per run


def apply_boolean(ob, cutter, op="DIFFERENCE"):
    """Apply an exact boolean of `cutter` onto `ob` in place (object transforms respected). Operand faces keep
    their own material slots (TRANSFER). Returns ob."""
    m = ob.modifiers.new("koch_bool", "BOOLEAN")
    m.object, m.operation, m.solver, m.material_mode = cutter, op, "EXACT", "TRANSFER"
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    ob.modifiers.remove(m)
    old = ob.data
    ob.data = me
    me.name = old.name
    if old.users == 0:
        bpy.data.meshes.remove(old)
    _drop_unused_slots(me)
    return ob


def _drop_unused_slots(me):
    """TRANSFER appends the operand's slots even when none of its faces survive: keep only used slots."""
    used = sorted({p.material_index for p in me.polygons})
    if len(used) == len(me.materials):
        return
    remap = {old: new for new, old in enumerate(used)}
    keep = [me.materials[i] for i in used]
    idx = [remap[p.material_index] for p in me.polygons]
    me.materials.clear()
    for m_ in keep:
        me.materials.append(m_)
    me.polygons.foreach_set("material_index", idx)


def temp_object(name, bm, matrix, slot=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if slot:
        me.materials.append(mat(slot))
    ob = bpy.data.objects.new(name, me)
    ob.matrix_world = matrix
    bpy.context.scene.collection.objects.link(ob)   # in the depsgraph for the modifier; removed after use
    ob.hide_render = True
    return ob


def _alive(ob):
    try:
        return ob.name in bpy.data.objects
    except ReferenceError:
        return False


def drop(ob):
    me = ob.data
    bpy.data.objects.remove(ob)
    if me.users == 0:
        bpy.data.meshes.remove(me)


def hollow_roof(roof, t_v, lining_slot="M_Paint_White"):
    """Turn a closed roof solid (flat bottom at the eave) into a shell: subtract the same solid moved down by t_v
    (vertical thickness). The shell keeps the eave band/soffit where the moved top is under the old bottom; its
    sloped underside (the attic ceiling) gets `lining_slot`. Stores t_v on the object for clip_under_roof()."""
    bm = bmesh.new()
    bm.from_mesh(roof.data)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((0, 0, -t_v)))
    for f in bm.faces:
        f.material_index = 0
    inner = temp_object(roof.name + "_TMPInner", bm, roof.matrix_world, lining_slot)
    apply_boolean(roof, inner)
    drop(inner)
    roof["koch_shell_tv"] = round(t_v, 4)
    return roof


def roof_cutter(roof, lift=0.0):
    """Solid from the roof underside (its sloped top faces moved down by the stored t_v, then up by `lift`) to
    40 m above them. lift > 0 keeps a cut part's cap inside the shell (no face on the underside's plane)."""
    key = (roof.name, round(lift, 4))
    c = _CUTTERS.get(key)
    if c is not None and _alive(c):
        return c
    t_v = roof.get("koch_shell_tv", 0.0) - lift
    mw3 = roof.matrix_world.to_3x3()
    bm = bmesh.new()
    bm.from_mesh(roof.data)
    # the outer sheet: upward faces in the roof's own (first) slot; lining and dormer tunnels carry the lining slot
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if (mw3 @ f.normal).normalized().z < 0.05 or f.material_index != 0],
                     context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    _fill_inner_holes(bm)   # holes where dormer tunnels pass through: the cutter must stay one closed solid
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((0, 0, -t_v)))
    sheet = list(bm.faces)
    ext = bmesh.ops.extrude_face_region(bm, geom=sheet, use_keep_orig=True)
    bmesh.ops.translate(bm, verts=[v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)], vec=Vector((0, 0, 40.0)))
    bmesh.ops.reverse_faces(bm, faces=sheet)          # the original sheet is the cutter's bottom: faces down
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    c = temp_object(f"{roof.name}_TMPCutter{len(_CUTTERS)}", bm, roof.matrix_world, "M_Paint_White")   # cut faces: painted lining
    _CUTTERS[key] = c
    return c


def _fill_inner_holes(bm):
    """Fill every boundary loop of an open sheet except the longest one (its outer edge)."""
    left = {e for e in bm.edges if e.is_boundary}
    loops = []
    while left:
        stack, comp = [left.pop()], []
        while stack:
            e = stack.pop()
            comp.append(e)
            for v in e.verts:
                for e2 in v.link_edges:
                    if e2 in left:
                        left.discard(e2)
                        stack.append(e2)
        loops.append(comp)
    loops.sort(key=lambda c: -sum(e.calc_length() for e in c))
    for comp in loops[1:]:
        bmesh.ops.holes_fill(bm, edges=comp, sides=0)


def clip_under_roof(ob, building_id):
    """Cut everything of `ob` that lies above the underside of building `building_id`'s roof shell (attic walls,
    ceilings and doors under the slopes). No-op without that roof."""
    roof = bpy.data.objects.get(f"GBF_{building_id}_Roof")
    if roof is None or ob.type != "MESH":
        return ob
    return apply_boolean(ob, roof_cutter(roof))


def clear_cutters():
    """Remove the temporary cutters (call at the end of a builder run: they must never be saved)."""
    for c in list(_CUTTERS.values()):
        if _alive(c):
            drop(c)
    _CUTTERS.clear()
