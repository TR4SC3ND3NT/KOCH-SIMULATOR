# Plan cuts between site elements, run by build_all.py after the site build and before settle (R1, owner msg 127:
# stairs growing through beds, lawns, copings and retaining walls). A spec element with "cut_by": ["OtherName", ...]
# (names of elements of the same spec, "SITE_X:Name" for another spec, or a full object name GB_/GBF_/GBS_...) loses everything inside the plan of each
# named element, at every height: the stair (cutter) keeps its full shape, the bed/lawn/wall now ends at its flank.
# The plan is the convex hull of the cutter's up-facing faces (stair treads, landing): exact for straight and fan
# flights. Exact boolean, so the result stays a closed manifold. Units: metres.
import json
import os

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import convex_hull_2d


def _objs(spec_short, name):
    """Built objects of element `name` in spec SITE_<spec_short> (one element may emit several objects)."""
    pre = f"GBS_{spec_short}_{name}"
    return [o for o in bpy.data.objects if o.type == "MESH" and (o.name == pre or (
        o.name.startswith(pre + "_") and str(o.get("koch_id", "")) == name))]


def _hull_prism(objs, z0, z1):
    pts = []
    for o in objs:
        mw = o.matrix_world
        n3 = mw.inverted_safe().transposed().to_3x3()
        for p in o.data.polygons:
            if (n3 @ p.normal).normalized().z > 0.7:
                pts += [(mw @ o.data.vertices[i].co).xy for i in p.vertices]
    if len(pts) < 3:
        return None
    hull = [pts[i] for i in convex_hull_2d(pts)]
    bm = bmesh.new()
    bot = [bm.verts.new((p.x, p.y, z0)) for p in hull]
    top = [bm.verts.new((p.x, p.y, z1)) for p in hull]
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    n = len(hull)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("_tmp_plan_cut")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("_tmp_plan_cut", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _boolean(ob, cutter):
    """ob minus cutter as a new mesh (ob untouched). Exact solver; elements built from overlapping boxes (a wall and its
    coping in one mesh) need its self-intersection mode, tried second because it is slower. Last resort: the MANIFOLD
    solver (Blender 4.5+, Manifold library), which always returns a closed solid for closed inputs."""
    me = None
    for solver, use_self in (("EXACT", False), ("EXACT", True), ("MANIFOLD", False)):
        mod = ob.modifiers.new("_plan_cut", "BOOLEAN")
        mod.operation, mod.solver, mod.object = "DIFFERENCE", solver, cutter
        if solver == "EXACT":
            mod.use_self = use_self
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.remove(mod)
        if len(me.polygons) and _manifold(me) and _kept_outside(ob, cutter, me):
            break
        bpy.data.meshes.remove(me)
        me = bpy.data.meshes.new("_empty")
    return me   # empty = failed (no polygons, an open result or geometry lost outside the cutter)


def _kept_outside(ob, cutter, me):
    """A difference never touches ob outside the cutter: every ob vertex outside the cutter's world bbox (+1 mm) must
    still be in the result. Catches the silent failures of self-overlapping cutters (crossing paint strips: the EXACT
    solver returned two 5 cm slivers of the 1100 m2 sports-courts slab, 2026-10-20)."""
    from mathutils.kdtree import KDTree
    cw = [cutter.matrix_world @ v.co for v in cutter.data.vertices]
    lo = Vector([min(v[i] for v in cw) - 0.001 for i in range(3)])
    hi = Vector([max(v[i] for v in cw) + 0.001 for i in range(3)])
    mw = ob.matrix_world
    keep = [v.co for v in ob.data.vertices if any(not (lo[i] <= (mw @ v.co)[i] <= hi[i]) for i in range(3))]
    if not keep:
        return True
    kd = KDTree(len(me.vertices))
    for i, v in enumerate(me.vertices):
        kd.insert(v.co, i)
    kd.balance()
    return all(kd.find(c)[2] < 1e-5 for c in keep)


def _manifold(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    ok = all(e.is_manifold for e in bm.edges)
    bm.free()
    return ok


def _cut(ob, cutter):
    me = _boolean(ob, cutter)
    old = ob.data
    if len(me.polygons) == 0:   # boolean failure (or fully inside): keep the element, report it
        bpy.data.meshes.remove(me)
        return "FAILED"
    me.materials.clear()
    for m in old.materials:
        me.materials.append(m)
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return "cut"


def run(specs_dir):
    out, missing = [], []
    for fn in sorted(os.listdir(specs_dir)):
        if not (fn.startswith("SITE_") and fn.endswith(".json")):
            continue
        spec = json.load(open(os.path.join(specs_dir, fn), encoding="utf-8"))
        short = spec.get("id", fn[:-5]).replace("SITE_", "")
        for el in spec.get("elements", []):
            if not el.get("cut_by"):
                continue
            targets = _objs(short, el.get("name", ""))
            if not targets:
                missing.append(el.get("name"))
                continue
            for ref in el["cut_by"]:
                if ref.startswith(("GB_", "GBF_", "GBS_")):   # a built object by its full name (buildings, context)
                    n2, cutters = ref, [o for o in [bpy.data.objects.get(ref)] if o is not None]
                else:
                    s2, n2 = ref.split(":", 1) if ":" in ref else (short, ref)
                    cutters = _objs(s2.replace("SITE_", ""), n2)
                if not cutters:
                    missing.append(ref)
                    continue
                zs = [(o.matrix_world @ Vector(c)).z for o in targets + cutters for c in o.bound_box]
                cutter = _hull_prism(cutters, min(zs) - 1.0, max(zs) + 1.0)
                if cutter is None:
                    missing.append(ref)
                    continue
                for t in targets:
                    out.append((t.name[4:], n2, _cut(t, cutter)))
                me = cutter.data
                bpy.data.objects.remove(cutter, do_unlink=True)
                bpy.data.meshes.remove(me)
    return {"cuts": out, "missing": missing}
