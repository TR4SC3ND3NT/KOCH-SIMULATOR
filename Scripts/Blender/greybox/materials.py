# Material slots for the R1 greybox detail kit: one Blender material per real material (UE maps each slot to its
# PBR material later); diffuse_color is only the viewport/Workbench review colour. Used by build_facades.py.
import bmesh
import bpy

# name -> viewport RGBA (review aid; the look comes from UE materials)
PALETTE = {
    "M_Render_Beige": (0.83, 0.78, 0.66, 1), "M_Paint_Maroon": (0.50, 0.16, 0.14, 1),
    "M_Block_PaleYellow": (0.87, 0.81, 0.60, 1), "M_Block_Grey": (0.55, 0.55, 0.53, 1),
    "M_Sand": (0.84, 0.75, 0.55, 1),   # jump pit sand (sports lower yard)   # pale yellow cast sand-concrete fence panels (N boundary)
    "M_PVC_White": (0.94, 0.94, 0.92, 1), "M_Glass": (0.30, 0.40, 0.48, 1), "M_Steel_Galv": (0.72, 0.72, 0.74, 1),
    "M_Steel_Paint_Dark": (0.22, 0.24, 0.26, 1), "M_Granite_Red": (0.52, 0.36, 0.33, 1),
    "M_Tile_Brick_Red": (0.45, 0.20, 0.16, 1), "M_Sheet_Red": (0.55, 0.20, 0.18, 1), "M_Sheet_Brown": (0.35, 0.22, 0.17, 1),
    "M_PVC_Gutter_White": (0.95, 0.95, 0.95, 1), "M_Alu_Black": (0.08, 0.08, 0.09, 1),
    "M_Terracotta_Soffit": (0.75, 0.38, 0.22, 1), "M_Sign_Panel": (0.20, 0.25, 0.45, 1), "M_Concrete": (0.62, 0.61, 0.58, 1),
    "M_Steel_Grating": (0.30, 0.32, 0.34, 1), "M_Sign_Frame_White": (0.90, 0.90, 0.90, 1),
    "M_AC_Casing": (0.88, 0.88, 0.86, 1), "M_Plastic_White": (0.92, 0.92, 0.92, 1), "M_Lamp_Diffuser": (0.96, 0.95, 0.85, 1),
    "M_Alu_Grey": (0.60, 0.61, 0.62, 1), "M_Alu_Grey_Slats": (0.55, 0.56, 0.57, 1), "M_Wrought_Iron": (0.10, 0.10, 0.10, 1),
    # site surfaces (build_site.py slots)
    "M_Paver_Clover_Grey": (0.66, 0.65, 0.63, 1), "M_Paver_Herringbone_Grey": (0.64, 0.63, 0.61, 1),
    "M_Paving_Generic": (0.62, 0.61, 0.59, 1), "M_Asphalt": (0.28, 0.28, 0.29, 1), "M_Road_Paint_White": (0.93, 0.93, 0.90, 1),
    "M_Concrete_Precast": (0.66, 0.65, 0.61, 1), "M_Hedge_Foliage": (0.22, 0.38, 0.20, 1), "M_Tree": (0.30, 0.45, 0.25, 1),
    "M_Soil_Mulch": (0.36, 0.28, 0.20, 1), "M_Wood_Stained": (0.42, 0.28, 0.17, 1), "M_Paint_White": (0.93, 0.93, 0.91, 1), "M_Paving_Diamond_Tile": (0.62, 0.58, 0.56, 1), "M_Paving_Diamond_Tile_Pink": (0.70, 0.56, 0.53, 1), "M_Paving_Octagon_Tile": (0.60, 0.57, 0.55, 1), "M_Steel_Paint_Maroon": (0.38, 0.16, 0.13, 1), "M_Steel_Paint_Green": (0.16, 0.36, 0.26, 1), "M_Fence_Mesh_Green": (0.30, 0.50, 0.40, 1), "M_Invisible": (0.42, 0.52, 0.85, 1), "M_Render_White": (0.92, 0.92, 0.90, 1), "M_Render_Pink": (0.86, 0.71, 0.68, 1), "M_Paint_Yellow": (0.90, 0.72, 0.08, 1), "M_Kerb_Painted_YW": (0.90, 0.80, 0.35, 1), "M_Paver_GreyPink": (0.66, 0.58, 0.56, 1), "M_Paver_CircleDisc": (0.65, 0.60, 0.58, 1), "M_Block_RockFace_Red": (0.52, 0.26, 0.21, 1), "M_Paint_RedPink": (0.62, 0.32, 0.29, 1), "M_Sheet_DarkGrey": (0.18, 0.19, 0.21, 1), "M_HPL_Black": (0.10, 0.10, 0.11, 1), "M_Tile_Wall_Grey": (0.62, 0.6, 0.57, 1), "M_Mirror": (0.75, 0.8, 0.84, 1), "M_Ceramic_White": (0.95, 0.95, 0.94, 1), "M_Paint_Brown": (0.28, 0.18, 0.12, 1),
    "M_Paint_Blue": (0.36, 0.48, 0.80, 1), "M_Terrazzo": (0.80, 0.79, 0.76, 1), "M_Plastic_Grey": (0.45, 0.46, 0.47, 1),
    "M_Plastic_Red": (0.70, 0.12, 0.12, 1), "M_Sport_Floor": (0.20, 0.55, 0.30, 1), "M_Ground_Dirt": (0.52, 0.45, 0.36, 1), "M_Fabric_Flag": (0.80, 0.15, 0.12, 1), "M_Plastic_Black": (0.06, 0.06, 0.07, 1),
    "M_Steel_Paint_YellowBlack": (0.85, 0.72, 0.10, 1), "M_Shingle_Brown": (0.36, 0.24, 0.20, 1),
    "M_Context_Facade": (0.70, 0.68, 0.64, 1), "M_Context_Roof": (0.45, 0.33, 0.28, 1),
    "M_Ground_Grass": (0.36, 0.45, 0.27, 1), "M_Tile_Beige": (0.86, 0.80, 0.68, 1),
    "M_Laminate_White": (0.94, 0.94, 0.93, 1), "M_Ceiling_Tile_600": (0.95, 0.95, 0.94, 1),
    "M_Ceiling_Grid_White": (0.90, 0.90, 0.90, 1), "M_LED_Panel_600": (1.0, 1.0, 0.97, 1),
    "M_Tile_Floor_600": (0.74, 0.72, 0.68, 1), "M_Tile_Grout": (0.82, 0.81, 0.78, 1), "M_Paint_Sage": (0.58, 0.69, 0.55, 1), "M_Granite_Beige": (0.74, 0.66, 0.58, 1), "M_Render_Shuba_Grey": (0.74, 0.72, 0.68, 1), "M_Clay_Pot": (0.55, 0.33, 0.25, 1), "M_Plastic_Pot_Pink": (0.85, 0.66, 0.66, 1), "M_Laminate_Oak_Grey": (0.55, 0.50, 0.45, 1), "M_Laminate_Beech_Orange": (0.80, 0.42, 0.20, 1),
    "M_Plastic_Orange": (0.78, 0.40, 0.18, 1), "M_Wood_Oak_Light": (0.66, 0.52, 0.36, 1), "M_Fabric_Curtain_Brown": (0.33, 0.25, 0.22, 1), "M_PVC_Ceiling_Panel": (0.95, 0.95, 0.95, 1),
    "M_Shingle_Hex_Dark": (0.25, 0.23, 0.22, 1),   # granulated hexagonal bitumen shingle on a wall (C west shed band)
    "M_Sheet_Grey": (0.45, 0.46, 0.48, 1), "M_Brass_Trim": (0.72, 0.58, 0.30, 1),
    "M_Sign_KOCH": (0.16, 0.24, 0.55, 1),   # KOCH-branded sign face (logo + lettering in UE; never real names)
    "M_Roof_Membrane": (0.35, 0.35, 0.36, 1),   # bituminous flat-roof membrane
    "M_Gravel_Compacted": (0.50, 0.46, 0.41, 1),   # compacted grey-brown gravel (parking east of the C plaza)
    "M_Fascia_Beige": (0.78, 0.75, 0.69, 1), "M_Steel_Paint_Grey": (0.62, 0.63, 0.64, 1),
    "M_PVC_Anthracite": (0.21, 0.22, 0.24, 1), "M_Chrome": (0.80, 0.81, 0.83, 1), "M_Radiator_White": (0.95, 0.95, 0.94, 1),
    "M_Fabric_Pleated_Cream": (0.93, 0.91, 0.85, 1), "M_Paint_Greige": (0.78, 0.76, 0.73, 1), "M_Plastic_Green": (0.25, 0.50, 0.30, 1), "M_Terrazzo_Grey_Tile": (0.74, 0.74, 0.72, 1),
    "M_Terrazzo_Grey": (0.58, 0.58, 0.57, 1), "M_Paint_Orange": (0.90, 0.45, 0.15, 1), "M_Granite_Pink": (0.57, 0.50, 0.48, 1),
}

# object-name keyword -> slot for parts still on a plain review colour after all builders ran (attachments, P0/P1
# massing, the context ring); first match wins, matched case-insensitively
NAME_SLOTS = [("ter_ground", "", "M_Ground_Grass"), ("ctx", "_roof", "M_Context_Roof"), ("ctx", "", "M_Context_Facade"),
              ("ac_units", "", "M_AC_Casing"), ("porchpiers", "", "M_Tile_Brick_Red"), ("porchroof", "", "M_Shingle_Brown"),
              ("sign", "", "M_Sign_Panel"), ("cctv", "", "M_Plastic_White"), ("downpipe", "", "M_PVC_Gutter_White"),
              ("_flood_", "", "M_Alu_Black"), ("_ac_", "", "M_AC_Casing"), ("_stairs_e", "", "M_Granite_Red"),
              ("_ramp_e", "", "M_Concrete"), ("_staircheek_", "", "M_Tile_Brick_Red"), ("glazedporch_canopy", "", "M_Sheet_Brown"), ("glazedporch", "", "M_Glass"),
              ("canopy", "", "M_Sheet_Brown"), ("lightwellcover", "", "M_Sheet_Red"), ("dancehallentry", "", "M_Tile_Brick_Red"),
              ("dormers", "", "M_Sheet_Red"), ("westshed", "", "M_Sheet_Red"), ("_roof", "", "M_Sheet_Red"),
              ("_vent_", "", "M_Alu_Grey"), ("gb_", "", "M_Render_Beige")]


def assign_name_slots(objects):
    """Replace the single plain review colour (VC_*) of every remaining mesh, or give an empty mesh its slot, from its
    name (NAME_SLOTS); returns how many objects got a slot."""
    n = 0
    for ob in objects:
        if ob.type != "MESH":
            continue
        me = ob.data
        if len(me.materials) > 1 or (len(me.materials) == 1 and me.materials[0] and not me.materials[0].name.startswith("VC_")):
            continue
        low = ob.name.lower()
        for a, b, slot in NAME_SLOTS:
            if a in low and b in low:
                if me.materials:
                    me.materials[0] = mat(slot)
                else:
                    me.materials.append(mat(slot))
                n += 1
                break
    return n


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


def assign_ground_surfaces(ter, specs_dir):
    """Per-face slots on the terrain from the specs' "ground_surfaces" [{"name", "ring": [[x, y], ...], "slot": M_*}]
    (paved areas that are ground, not separate objects: carriageway, forecourts, yards, plazas). Base slot 0 stays
    M_Ground_Grass; later rings (spec file order, then list order) win. Returns the face count per surface."""
    import json
    import os
    import numpy as np

    def inside_ring(P, ring):   # even-odd rule, vectorised over the points (Blender's Python has no matplotlib)
        R = np.asarray(ring, float); x, y = P[:, 0], P[:, 1]; res = np.zeros(len(P), bool)
        for (x1, y1), (x2, y2) in zip(R, np.roll(R, -1, axis=0)):
            c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / ((y2 - y1) + 1e-12) + x1)
            res ^= c
        return res
    surf = []
    for fn in sorted(os.listdir(specs_dir)):
        if fn.endswith(".json"):
            try:
                surf += json.load(open(os.path.join(specs_dir, fn), encoding="utf-8")).get("ground_surfaces", [])
            except (ValueError, AttributeError):
                pass
    if ter is None or not surf:
        return {}
    me = ter.data
    if not me.materials:
        me.materials.append(mat("M_Ground_Grass"))
    M = ter.matrix_world
    cen = np.array([(M @ p.center)[:2] for p in me.polygons])
    idx = np.zeros(len(cen), int)
    counts = {}
    for sf in surf:
        slot = sf["slot"]
        names = [m.name for m in me.materials]
        if slot not in names:
            me.materials.append(mat(slot)); names.append(slot)
        R = np.asarray(sf["ring"], float)
        sel = np.flatnonzero((cen[:, 0] >= R[:, 0].min()) & (cen[:, 0] <= R[:, 0].max()) &
                             (cen[:, 1] >= R[:, 1].min()) & (cen[:, 1] <= R[:, 1].max()))   # bbox prefilter
        inside = np.zeros(len(cen), bool)
        inside[sel] = inside_ring(cen[sel], sf["ring"])
        idx[inside] = names.index(slot)
        counts[sf.get("name", slot)] = int(inside.sum())
    me.polygons.foreach_set("material_index", idx.astype(np.int32))
    me.update()
    return counts