# Clipped-hedge leaf shells (R4, read-only on R1's .blend): for every hedge/arch object, scatters leaf sprigs cut from
# Poly Haven shrub_02 (CC0, 0.1-0.2 m leafy twigs) over its M_Hedge_Foliage faces, area-weighted, each sprig turned to
# face out of the hedge with a random spin/tilt and pushed slightly in/out, so the flat greybox mass reads as a dense
# trimmed hedge (it stays inside as the dark core). One FBX per hedge in world space (place at the UE origin), plus
# shells.json. Same FBX axis settings as ue_prep (1 Blender m -> UE cm, UE y = -Blender y).
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_hedge_shells.py -- SHRUB_FBX OUT_DIR [density] [name]
import json
import math
import os
import re
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SHRUB, OUT = argv[0], argv[1]
DENSITY = float(argv[2]) if len(argv) > 2 else 240.0   # sprigs per m2: 3-4 overlapping layers, the core barely shows
ONLY = argv[3] if len(argv) > 3 else ""                  # optional name filter for quick tests
HEDGE_MAT = "M_Hedge_Foliage"
NAME = re.compile(r"Hedge|Arch_Bnd|PathHedge", re.I)
SPRIG_MAX_M = 0.3            # larger connected pieces are branches, not leaf sprigs
SCALE_RANGE = (1.3, 2.2)   # sprigs this big read as a trimmed hedge surface, not single leaves
TILT_DEG = 35.0              # how far a sprig may lean off the surface normal
OFFSET_M = (-0.04, 0.05)     # below/above the clipped surface
rng = np.random.default_rng(7)
os.makedirs(OUT, exist_ok=True)

hedges = [o for o in bpy.data.objects if o.type == "MESH" and NAME.search(o.name) and ONLY in o.name
          and any(m and m.name == HEDGE_MAT for m in o.data.materials)]
print(f"build_hedge_shells: {len(hedges)} hedge objects")

# --- sprig library: connected components of shrub_02, centred, local frame with +Z = mean face normal -------------
for o in list(bpy.data.objects):
    o.select_set(False)
bpy.ops.import_scene.fbx(filepath=SHRUB)
library = []
for src in [o for o in bpy.context.selected_objects if o.type == "MESH"]:
    me = src.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(src.matrix_world)
    uv = bm.loops.layers.uv.active
    seen = set()
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        stack, comp = [f0], []
        while stack:
            f = stack.pop()
            if f.index in seen:
                continue
            seen.add(f.index)
            comp.append(f)
            stack.extend(h for e in f.edges for h in e.link_faces if h.index not in seen)
        verts = sorted({v.index for f in comp for v in f.verts})
        bm.verts.ensure_lookup_table()
        co = np.array([bm.verts[i].co[:] for i in verts])
        if np.ptp(co, axis=0).max() > SPRIG_MAX_M:
            continue
        n = sum((f.normal * f.calc_area() for f in comp), Vector())
        n = n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
        to_local = n.to_track_quat("Z", "Y").to_matrix().inverted()
        centre = co.mean(0)
        local = np.array([(to_local @ Vector(c - centre))[:] for c in co])
        remap = {vi: k for k, vi in enumerate(verts)}
        faces = [[remap[v.index] for v in f.verts] for f in comp]
        uvs = [[l[uv].uv[:] for l in f.loops] for f in comp]
        library.append((local, faces, uvs))
    bm.free()
    bpy.data.objects.remove(src)
print(f"build_hedge_shells: {len(library)} sprigs in the library")


def rot_to(n):
    """Matrix taking +Z to unit vector n."""
    return Vector(n).to_track_quat("Z", "Y").to_matrix()


meta = {}
for ob in hedges:
    me = ob.data
    mw = ob.matrix_world
    nmat = mw.to_3x3().inverted().transposed()
    slot = [i for i, m in enumerate(me.materials) if m and m.name == HEDGE_MAT]
    tris = []
    me.calc_loop_triangles()
    for t in me.loop_triangles:
        if t.material_index in slot:
            a, b, c = (mw @ me.vertices[i].co for i in t.vertices)
            area = ((b - a).cross(c - a)).length / 2
            nw = (nmat @ t.normal).normalized()
            if area > 1e-6 and nw.z > -0.5:   # skip faces lying on the ground
                tris.append((a, b, c, nw, area))
    if not tris:
        continue
    areas = np.array([t[4] for t in tris])
    count = int(areas.sum() * DENSITY)
    pick = rng.choice(len(tris), size=count, p=areas / areas.sum())
    V, F, UV = [], [], []
    base = 0
    for ti in pick:
        a, b, c, n, _ = tris[ti]
        r1, r2 = rng.random(2)
        if r1 + r2 > 1:
            r1, r2 = 1 - r1, 1 - r2
        p = a + (b - a) * r1 + (c - a) * r2
        local, faces, uvs = library[rng.integers(len(library))]
        tilt = Matrix.Rotation(math.radians(rng.uniform(-TILT_DEG, TILT_DEG)), 3, "X")
        spin = Matrix.Rotation(rng.uniform(0, 2 * math.pi), 3, "Z")
        m = np.array(rot_to(n) @ tilt @ spin) * rng.uniform(*SCALE_RANGE)
        pos = np.array((p + n * rng.uniform(*OFFSET_M))[:])
        V.append(local @ m.T + pos)
        F.extend([[base + i for i in f] for f in faces])
        UV.extend(uvs)
        base += len(local)
    verts = np.concatenate(V)
    name = f"SM_HedgeShell_{re.sub(r'[^A-Za-z0-9_]', '_', ob.name)}"
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], F)
    uvl = mesh.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", np.array([c for face in UV for c in face], dtype=np.float32).ravel())
    mesh.materials.append(bpy.data.materials.get("M_HedgeLeaves") or bpy.data.materials.new("M_HedgeLeaves"))
    shell = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(shell)
    bpy.ops.object.select_all(action="DESELECT")
    shell.select_set(True)
    bpy.context.view_layer.objects.active = shell
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, f"{name}.fbx"), use_selection=True, axis_forward="-Y",
                             axis_up="Z", apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
                             mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False, path_mode="STRIP")
    meta[name] = {"hedge": ob.name, "area_m2": round(float(areas.sum()), 1), "sprigs": count, "faces": len(F)}
    print(f"build_hedge_shells: {name} {meta[name]}")
    bpy.data.objects.remove(shell)
    bpy.data.meshes.remove(mesh)
with open(os.path.join(OUT, "shells.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=1)
print(f"build_hedge_shells: {len(meta)} shells, {sum(m['faces'] for m in meta.values())} faces")
