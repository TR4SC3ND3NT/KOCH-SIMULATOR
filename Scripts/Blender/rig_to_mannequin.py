# Rig a static humanoid mesh to the UE5 mannequin skeleton (R4 playtest aid): the skeleton comes from any mannequin
# animation exported as FBX (e.g. MM_Idle), the arm chains are turned to hang like the mesh's arms and applied as the
# rest pose (bone frames turn with them, so mannequin animations still drive the bones correctly), the mesh is bound
# with region-limited nearest-bone weights (Blender heat weighting fails on such meshes) and exported for UE with the
# armature object named "root" (Send2UE convention: it becomes the root bone). Import in UE with
# skeleton = SK_Mannequin and every mannequin animation plays on it. Mesh must face -Y (Blender), feet at z = 0.
# Run: blender -b -P Scripts/Blender/rig_to_mannequin.py -- SKELETON_ANIM.fbx MESH.fbx OUT.fbx
import sys

import bpy
from mathutils import Vector

skel_fbx, mesh_fbx, out_fbx = sys.argv[sys.argv.index("--") + 1:][:3]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=skel_fbx, automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
arm.animation_data_clear()
for pb in arm.pose.bones:   # the clip's last evaluated pose stays on the bones (cm-sized offsets): back to rest
    pb.location = (0.0, 0.0, 0.0)
    pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    pb.rotation_euler = (0.0, 0.0, 0.0)
    pb.scale = (1.0, 1.0, 1.0)
for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:   # a preview mesh, if the export had one
    bpy.data.objects.remove(o)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)   # cm-scaled import -> metres, scale 1

bpy.ops.import_scene.fbx(filepath=mesh_fbx)
mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = [mesh.matrix_world @ v.co for v in mesh.data.vertices]


def arm_point(side, z0, z1):
    """Centroid of the mesh's arm vertices (|x| > 0.19 on this side) in the height band z0..z1 (m)."""
    pts = [c for c in co if c.x * side > 0.19 and z0 <= c.z <= z1]
    return sum(pts, Vector()) / len(pts) if pts else None


def aim(name, child, target):
    """Turn pose bone `name` so its child's head points at target (armature space = world here)."""
    bpy.context.view_layer.update()
    pb, cb = arm.pose.bones[name], arm.pose.bones[child]
    head, cur = pb.head.copy(), cb.head - pb.head
    q = cur.normalized().rotation_difference((target - head).normalized())
    m = pb.matrix.copy()
    rot = (q.to_matrix() @ m.to_3x3()).to_4x4()
    rot.translation = m.translation
    pb.matrix = rot


bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
hand_z = min(c.z for c in co if abs(c.x) > 0.19)
for side, s in ((1, "l"), (-1, "r")):
    elbow = arm_point(side, 1.08, 1.18)
    wrist = arm_point(side, hand_z + 0.10, hand_z + 0.18)
    if elbow is None or wrist is None:
        print(f"rig_to_mannequin: no {s} arm found, chain left as is")
        continue
    aim(f"upperarm_{s}", f"lowerarm_{s}", elbow)
    aim(f"lowerarm_{s}", f"hand_{s}", wrist)
    aim(f"hand_{s}", f"middle_metacarpal_{s}" if f"middle_metacarpal_{s}" in arm.pose.bones else f"middle_01_{s}",
        Vector((wrist.x, wrist.y, hand_z)))
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode="OBJECT")

# helper bones carry no skin (ik targets, the interaction / centre-of-mass markers)
for b in arm.data.bones:
    if b.name.startswith("ik_") or b.name in ("interaction", "center_of_mass", "root"):
        b.use_deform = False

bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_NAME")   # empty groups: heat weighting fails on this kind of mesh

# weights: per body region, blended weights of the two nearest bone segments, w ~ 1 / d^2, the second only when it
# is within BLEND x the nearest distance (soft elbows and knees)
BLEND = 1.6
SKIP = ("twist", "corrective", "metacarpal", "thumb", "index", "middle", "ring", "pinky")   # fine bones grab patches
deform = [b for b in arm.data.bones if b.use_deform and not any(k in b.name + "_" for k in SKIP)]
segs = []
for b in deform:
    a = b.head_local.copy()
    kids = [c for c in b.children if c.use_deform and not any(k in c.name + "_" for k in SKIP)]
    t = kids[0].head_local.copy() if len(kids) == 1 else b.tail_local.copy()
    segs.append((b.name, a, t - a))
# body regions keep limbs apart: hands hang beside the thighs, so plain nearest-bone weights tore the jeans with
# the arm swing (owner playtest 2026-10-28: a "leg" kicking up while walking)
ARM_X, CROTCH_Z, NECK_Z = 0.19, 0.92, 1.50   # m, from the mesh: arm |x| beyond the torso, leg top, chin
REGIONS = {
    "arm_l": ("clavicle_l", "upperarm_l", "lowerarm_l", "hand_l"),
    "arm_r": ("clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"),
    "leg_l": ("pelvis", "thigh_l", "calf_l", "foot_l", "ball_l"),
    "leg_r": ("pelvis", "thigh_r", "calf_r", "foot_r", "ball_r"),
    "torso": ("pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "clavicle_l", "clavicle_r", "neck_01"),
    "head": ("neck_01", "neck_02", "head"),
}


def region(p):
    if abs(p.x) > ARM_X and p.z > 0.55:
        return "arm_l" if p.x > 0 else "arm_r"
    if p.z < CROTCH_Z:
        return "leg_l" if p.x >= 0 else "leg_r"
    return "head" if p.z > NECK_Z else "torso"


segs_by = {r: [sg for sg in segs if sg[0] in names] for r, names in REGIONS.items()}
empty = 0
for v in mesh.data.vertices:
    p = mesh.matrix_world @ v.co
    ds = []
    for name, a, ab in segs_by[region(p)]:
        k = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
        ds.append(((a + ab * k - p).length, name))
    ds.sort()
    picks = [ds[0]] + ([ds[1]] if ds[1][0] < ds[0][0] * BLEND else [])
    ws = [1.0 / max(d, 1e-3) ** 2 for d, _ in picks]
    for (d, name), w in zip(picks, ws):
        vg = mesh.vertex_groups.get(name) or mesh.vertex_groups.new(name=name)
        vg.add([v.index], w / sum(ws), "REPLACE")
    empty += 1
print(f"rig_to_mannequin: {empty} verts weighted, groups {sorted(g.name for g in mesh.vertex_groups if g.name in {s[0] for s in segs})}")

# Send2UE units: scene in centimetres, armature and mesh scaled x100 and applied, so the FBX root bone has scale 1
# (metres with apply_unit_scale put 100 on the root bone and mannequin animations then tore the pose apart)
bpy.context.scene.unit_settings.scale_length = 0.01
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
for o in (arm, mesh):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    o.scale = (100.0, 100.0, 100.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
mesh.parent = arm          # the armature modifier stays: plain parenting, no second modifier

arm.name = "root"
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
arm.select_set(True)
bpy.ops.export_scene.fbx(filepath=out_fbx, use_selection=True, object_types={"ARMATURE", "MESH"},
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", add_leaf_bones=False,
                         bake_anim=False, use_armature_deform_only=False, mesh_smooth_type="FACE",
                         primary_bone_axis="Y", secondary_bone_axis="X", axis_forward="-Y", axis_up="Z",
                         path_mode="STRIP")   # Z-up like the UE export it came from: no root re-orientation
print(f"rig_to_mannequin: wrote {out_fbx}")
