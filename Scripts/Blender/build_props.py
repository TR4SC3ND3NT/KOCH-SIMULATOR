# Street furniture kit (R4): park bench, wrought-iron bin, 240 L wheelie bin, 1100 L euro container, built at real size
# from the owner's garden photos (black wrought-iron scroll frame + red-brown timber slats; dark iron basket bins) and
# common EN 840 dimensions. One FBX per prop (pivot at the base centre, length along +X, the bench's front faces -Y),
# material slots named like the greybox palette (M_Wood_Stained, M_Steel_Paint_Dark, ...) so UE reuses the MI_* set,
# UVs cube-projected at 1 UV = 1 m to match M_SurfacePBR's metre tiling. Writes props.json (sizes) for
# Scripts/Unreal/place_props.py. Same FBX axis settings as ue_prep (1 Blender m -> UE cm).
# Run: blender -b -P Scripts/Blender/build_props.py -- OUT_DIR
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

OUT = sys.argv[sys.argv.index("--") + 1]
os.makedirs(OUT, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name):
    return bpy.data.materials.get(name) or bpy.data.materials.new(name)


def box(name, size, loc, material, bevel=0.0, rot_z=0.0, rot_x=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=2, affect="EDGES")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rot_z, 4, "Z") @ Matrix.Rotation(rot_x, 4, "X")
    me.materials.append(mat(material))
    return ob


def cyl(name, r, h, loc, material, verts=16, rot=None, r_top=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r if r_top is None else r_top, depth=h)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    m = Matrix.Translation(Vector(loc))
    if rot is not None:
        m = m @ rot
    ob.matrix_world = m
    me.materials.append(mat(material))
    return ob


def tube(name, points, radius, material, closed=False):
    """Round bar along a smooth (auto-handled bezier) path: wrought-iron scrolls and frames."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    cu.resolution_u = 8
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = Vector(p)
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    sp.use_cyclic_u = closed
    cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(mat(material))
    return ob


def finish(name, meta):
    """Join, convert curves, cube-project UVs at 1 m, pivot = base centre, export FBX."""
    obs = [o for o in bpy.context.scene.objects]
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=False, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    lo = Vector([min(v.co[i] for v in ob.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in ob.data.vertices) for i in range(3)])
    ob.data.transform(Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))))
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, f"{name}.fbx"), use_selection=True, axis_forward="-Y",
                             axis_up="Z", apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
                             mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False, path_mode="STRIP")
    meta[name] = {"size_m": [round(hi[i] - lo[i], 3) for i in range(3)],
                  "slots": [m.name for m in ob.data.materials], "tris": sum(len(p.vertices) - 2 for p in ob.data.polygons)}
    print(f"build_props: {name} {meta[name]}")


meta = {}
WOOD, IRON, GALV, PLASTIC, PLASTIC_DARK, RUBBER = ("M_Wood_Stained", "M_Steel_Paint_Dark", "M_Steel_Galv",
                                                   "M_Plastic_Grey", "M_Plastic_Black", "M_Plastic_Black")

# --- park bench 1.80 m: two scroll side frames, 4 seat + 3 back slats (owner photo, garden) -----------------------
reset()
L, seat_h, depth = 1.80, 0.45, 0.62
for sx in (-0.78, 0.78):
    r = 0.012
    tube("frame_leg_front", [(sx, -0.26, 0.0), (sx, -0.25, 0.22), (sx, -0.27, seat_h - 0.03)], r, IRON)
    tube("frame_leg_back", [(sx, 0.24, 0.0), (sx, 0.22, 0.25), (sx, 0.20, seat_h - 0.03), (sx, 0.26, 0.62), (sx, 0.31, 0.84)], r, IRON)
    tube("frame_seat_rail", [(sx, -0.30, seat_h - 0.035), (sx, 0.0, seat_h - 0.045), (sx, 0.21, seat_h - 0.035)], r, IRON)
    # armrest scroll: from the back post forward, curling down over the front leg (the photo's swan-neck arm)
    tube("frame_arm", [(sx, 0.24, 0.66), (sx, 0.05, 0.70), (sx, -0.20, 0.67), (sx, -0.30, 0.58), (sx, -0.26, 0.52),
                       (sx, -0.21, 0.56), (sx, -0.24, 0.60)], r, IRON)
    tube("frame_scroll_low", [(sx, -0.25, 0.10), (sx, -0.15, 0.06), (sx, -0.05, 0.14), (sx, -0.12, 0.20), (sx, -0.17, 0.15)], 0.008, IRON)
    cyl("foot_f", 0.025, 0.012, (sx, -0.26, 0.006), IRON)
    cyl("foot_b", 0.025, 0.012, (sx, 0.24, 0.006), IRON)
for i in range(4):                                   # seat slats 70 x 28 mm, 15 mm gaps
    box(f"seat_{i}", (L, 0.07, 0.028), (0, -0.24 + i * 0.085, seat_h - 0.014), WOOD, bevel=0.004)
for i in range(3):                                   # back slats on the reclined back posts
    z = 0.56 + i * 0.09
    y = 0.22 + (z - 0.45) * 0.28
    box(f"back_{i}", (L, 0.075, 0.025), (0, y, z), WOOD, bevel=0.004, rot_x=math.radians(-15))
finish("SM_Prop_Bench_Park", meta)

# --- wrought-iron bin 0.45 x 0.75 m: bar basket, rim rings, three legs, galvanised liner ----------------------------
reset()
R, H0, H1 = 0.21, 0.12, 0.75
cyl("liner", R - 0.02, H1 - H0 - 0.04, (0, 0, (H0 + H1) / 2), GALV, verts=24)
for z in (H0 + 0.01, (H0 + H1) / 2, H1 - 0.01):
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, segments=32, radius=R)
    pts = [tuple(v.co) for v in bm.verts]
    bm.free()
    tube("ring", [(x, y, z) for x, y, _ in pts], 0.009, IRON, closed=True)
for k in range(16):
    a = 2 * math.pi * k / 16
    tube("bar", [(R * math.cos(a), R * math.sin(a), H0), (R * 1.02 * math.cos(a), R * 1.02 * math.sin(a), (H0 + H1) / 2),
                 (R * math.cos(a), R * math.sin(a), H1)], 0.006, IRON)
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.3
    tube("leg", [(R * 0.9 * math.cos(a), R * 0.9 * math.sin(a), H0 + 0.02), (R * 1.05 * math.cos(a), R * 1.05 * math.sin(a), 0.05),
                 (R * 1.25 * math.cos(a), R * 1.25 * math.sin(a), 0.0)], 0.012, IRON)
finish("SM_Prop_Bin_WroughtIron", meta)

# --- 240 L wheelie bin (EN 840): 0.58 x 0.73 x 1.07 m, tapered body, hinged lid, two wheels, handle ------------------
reset()
bm = bmesh.new()
for z, w, d in ((0.06, 0.48, 0.60), (0.98, 0.56, 0.70)):    # tapered body: bottom ring, top ring
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        bm.verts.new((sx * w / 2, sy * d / 2, z))
bm.verts.ensure_lookup_table()
v = bm.verts
for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
    bm.faces.new([v[i] for i in f])
bmesh.ops.bevel(bm, geom=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5], offset=0.05, segments=3, affect="EDGES")
me = bpy.data.meshes.new("body")
bm.to_mesh(me)
bm.free()
ob = bpy.data.objects.new("body", me)
bpy.context.scene.collection.objects.link(ob)
me.materials.append(mat(PLASTIC))
box("lid", (0.60, 0.74, 0.035), (0, 0.0, 1.0), PLASTIC_DARK, bevel=0.01)
box("rim", (0.58, 0.04, 0.05), (0, 0.37, 0.96), PLASTIC_DARK, bevel=0.008)
tube("handle", [(-0.22, 0.40, 0.92), (-0.22, 0.43, 0.97), (0.22, 0.43, 0.97), (0.22, 0.40, 0.92)], 0.016, PLASTIC_DARK)
for sx in (-0.26, 0.26):
    cyl("wheel", 0.10, 0.05, (sx, 0.30, 0.10), RUBBER, verts=20, rot=Matrix.Rotation(math.pi / 2, 4, "Y"))
cyl("axle", 0.012, 0.56, (0, 0.30, 0.10), GALV, rot=Matrix.Rotation(math.pi / 2, 4, "Y"))
finish("SM_Prop_Bin_Wheelie240", meta)

# --- 1100 L euro container (EN 840-3): 1.37 x 1.07 x 1.30 m galvanised body, dark domed lids, 4 castors --------------
reset()
bm = bmesh.new()
for z, w, d in ((0.20, 1.20, 0.90), (1.15, 1.37, 1.07)):
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        bm.verts.new((sx * w / 2, sy * d / 2, z))
bm.verts.ensure_lookup_table()
v = bm.verts
for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
    bm.faces.new([v[i] for i in f])
bmesh.ops.bevel(bm, geom=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5], offset=0.08, segments=3, affect="EDGES")
me = bpy.data.meshes.new("body")
bm.to_mesh(me)
bm.free()
ob = bpy.data.objects.new("body", me)
bpy.context.scene.collection.objects.link(ob)
me.materials.append(mat(GALV))
box("top_rim", (1.40, 1.10, 0.05), (0, 0, 1.16), GALV, bevel=0.01)
for sx in (-0.35, 0.35):                                     # two-part domed lid
    box("lid", (0.68, 1.08, 0.08), (sx, 0, 1.22), PLASTIC_DARK, bevel=0.03)
for sx in (-0.69, 0.69):                                     # lifting trunnions on the short sides
    cyl("trunnion", 0.035, 0.08, (sx * 1.02, 0, 0.95), GALV, rot=Matrix.Rotation(math.pi / 2, 4, "Y"))
for sx, sy in ((-0.52, -0.38), (0.52, -0.38), (0.52, 0.38), (-0.52, 0.38)):
    box("castor_plate", (0.12, 0.12, 0.02), (sx, sy, 0.19), GALV)
    box("castor_fork", (0.04, 0.10, 0.10), (sx, sy, 0.14), GALV)
    cyl("castor_wheel", 0.08, 0.05, (sx, sy, 0.08), RUBBER, verts=20, rot=Matrix.Rotation(math.pi / 2, 4, "Y"))
box("front_handle", (0.9, 0.03, 0.03), (0, -0.56, 1.05), GALV)
finish("SM_Prop_Container1100", meta)

with open(os.path.join(OUT, "props.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=1)
