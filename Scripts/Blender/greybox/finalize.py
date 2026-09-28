# Production clean-up pass run by build_all.py after every builder (R1, before validate/save): leaves the scene ready
# for the UE export without changing any world-space geometry.
#  - mirrored placements (left-handed facade frames, det < 0) -> mesh mirrored once, objects get pure rotations
#  - closed meshes that are inside-out in world space -> faces reversed
#  - zero-area faces dissolved (only if the mesh stays closed), empty meshes removed
#  - unused / out-of-range material slots removed
#  - pivots at the local bounding-box bottom centre (UE static-mesh pivot), rotation kept
#  - collections: every zone collection under its numbered parent (never twice), empty ones removed, the phase-1
#    massing replaced by detailed buildings moved to the excluded 99_Replaced_Phase1
#  - orphan data purged
import bmesh
import bpy
import numpy as np
from mathutils import Matrix

SKIP = ("TER_", "REF_", "CAM_")
FLIP_W = Matrix.Diagonal((1.0, -1.0, 1.0, 1.0))   # facade frames are (u, w_out, z): flipping w makes them right-handed
PARENT = (("BLD_", "02_Buildings"), ("SITE_", "03_Site"), ("GRD_", "04_Garden"), ("STR_", "05_Street"),
          ("VEG_", "06_Vegetation"), ("INT_", "07_BlockC_Interior"), ("CTX_", "08_Context"), ("REF_", "00_Reference"))
REPLACED = "99_Replaced_Phase1"


def _users():
    users = {}
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.users_collection and not ob.name.startswith(SKIP):
            users.setdefault(ob.data, []).append(ob)
    return users


def _closed(bm):
    return all(e.is_manifold for e in bm.edges) and not any(
        len(e.link_loops) == 2 and e.link_loops[0].vert == e.link_loops[1].vert for e in bm.edges)


def fix_meshes():
    st = dict(empty=[], mirrored=0, inside_out=[], degenerate=[], slots=0, pivots=0)
    users = _users()
    for me, obs in list(users.items()):
        if not me.polygons:
            st["empty"] += [o.name for o in obs]
            for o in obs:
                bpy.data.objects.remove(o, do_unlink=True)
            continue
        neg = [o for o in obs if o.matrix_world.to_3x3().determinant() < 0]
        if neg:
            if len(neg) < len(obs):   # mixed users: the mirrored ones get their own copy
                me2 = me.copy()
                for o in neg:
                    o.data = me2
                users[me2] = neg
                users[me] = [o for o in obs if o not in neg]
                me, obs = me2, neg
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.transform(bm, matrix=FLIP_W, verts=bm.verts)
            bmesh.ops.reverse_faces(bm, faces=bm.faces)   # mirror + reverse keeps the displayed (outward) winding
            bm.to_mesh(me)
            bm.free()
            for o in obs:
                o.matrix_world = o.matrix_world @ FLIP_W
            st["mirrored"] += len(obs)
    for me, obs in _users().items():
        bm = bmesh.new()
        bm.from_mesh(me)
        changed = False
        za = [f for f in bm.faces if f.calc_area() < 1e-9]
        if za:
            tmp = bm.copy()
            bmesh.ops.dissolve_degenerate(tmp, dist=1e-5, edges=tmp.edges)
            bmesh.ops.delete(tmp, geom=[v for v in tmp.verts if not v.link_faces], context="VERTS")
            if tmp.faces and _closed(tmp) == _closed(bm) and not any(f.calc_area() < 1e-9 for f in tmp.faces):
                bm.free()
                bm, changed = tmp, True
                st["degenerate"].append(obs[0].name)
            else:
                tmp.free()
        if _closed(bm) and bm.calc_volume(signed=True) < -1e-9:   # all users have det > 0 here
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
            st["inside_out"].append(obs[0].name)
            changed = True
        if changed:
            bm.to_mesh(me)
        bm.free()
        # material slots: drop unused ones, keep the order of the used ones
        n = len(me.materials)
        if n:
            mi = np.empty(len(me.polygons), np.int32)
            me.polygons.foreach_get("material_index", mi)
            mi = np.clip(mi, 0, n - 1)
            used = sorted(set(np.unique(mi).tolist()))
            if len(used) < n:
                keep = [me.materials[i] for i in used]
                remap = np.zeros(n, np.int32)
                remap[used] = np.arange(len(used))
                me.materials.clear()
                for m in keep:
                    me.materials.append(m)
                me.polygons.foreach_set("material_index", remap[mi])
                st["slots"] += n - len(used)
        # pivot: local bbox bottom centre
        co = np.empty(len(me.vertices) * 3, np.float64)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        lo, hi = co.min(0), co.max(0)
        c = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
        if np.abs(c).max() > 1e-3:
            me.transform(Matrix.Translation((-c).tolist()))
            for o in obs:
                o.matrix_world = o.matrix_world @ Matrix.Translation(c.tolist())
            st["pivots"] += len(obs)
        me.update()
    bpy.context.view_layer.update()   # bake the new matrices before objects move into the excluded collection
    return st


def _parents():
    par = {}
    for c in [bpy.context.scene.collection] + list(bpy.data.collections):
        for ch in c.children:
            par.setdefault(ch.name, []).append(c)
    return par


def fix_collections():
    root = bpy.context.scene.collection
    par = _parents()
    moved = []
    for col in list(bpy.data.collections):
        if col.name[:2].isdigit() or col.name == REPLACED:
            continue
        target = next((p for k, p in PARENT if col.name.startswith(k)), None)
        tp = bpy.data.collections.get(target) if target else None
        if tp is None or col.name == target:
            continue
        if tp.name not in root.children and not any(tp.name in c.children for c in bpy.data.collections):
            root.children.link(tp)
        if col.name not in tp.children:
            tp.children.link(col)
        for p in par.get(col.name, []):
            if p != tp:
                p.children.unlink(col)
                moved.append(col.name)
    # phase-1 massing hidden by a detailed spec ("replaces"): out of the export, kept for review
    rep = [o for o in bpy.data.objects if o.name.startswith("GB_") and o.hide_render]
    if rep:
        rc = bpy.data.collections.get(REPLACED) or bpy.data.collections.new(REPLACED)
        if rc.name not in root.children:
            root.children.link(rc)
        for o in rep:
            for c in list(o.users_collection):
                if c != rc:
                    c.objects.unlink(o)
            if rc not in o.users_collection:
                rc.objects.link(o)

        def exclude(lc):
            for ch in lc.children:
                if ch.collection == rc:
                    ch.exclude = True
                exclude(ch)
        for vl in bpy.context.scene.view_layers:
            exclude(vl.layer_collection)

    def prune(col):
        n = 0
        for ch in list(col.children):
            n += prune(ch)
            if not ch.objects and not ch.children:
                col.children.unlink(ch)
                if ch.users == 0:
                    bpy.data.collections.remove(ch)
                n += 1
        return n
    return dict(reparented=sorted(set(moved)), replaced=len(rep), empty_removed=prune(root))


def run():
    st = fix_meshes()
    st.update(fix_collections())
    st["orphans_purged"] = bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    return st
