# Thin-shell QA for Lumen (R1, owner msg 141, before the UE hand-off). Read-only, never saves.
# Lumen software ray tracing traces mesh distance fields; opaque walls/roofs/floors thinner than ~10 cm leak light
# (Epic, "Lumen Technical Details" > Software Ray Tracing: "walls should be no thinner than 10 cm").
# For every large face (>= MIN_AREA m2) of an envelope object (building walls, roofs, slabs, floors, parapets,
# interior partitions) the solid thickness behind it is measured by a ray along -normal through the object's own mesh;
# faces under THIN_M with no other solid touching either side (a finish on its slab) are reported as "thin"; thin
# linings with a >= THIN_M solid within 1 m (suspended ceilings under the slab, cladding on a cavity) as "lining" (OK).
# Run: blender -b FILE.blend -P Scripts/Blender/thin_qa.py -- OUT.json
import json
import re
import sys
from collections import defaultdict

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
THIN_M = 0.10      # Lumen leak threshold (m)
MIN_AREA = 0.5     # m2: small trims, reveals and fittings do not matter for leaks
ENVELOPE = re.compile(r"(Wall|Roof|Slab|Floor|Ceiling|Infill|Parapet|Partition|Fascia|Soffit|Gable|Plinth|Attic|"
                      r"Shell|Storey|Deck)", re.I)
ZONE = re.compile(r"^GB[FS]_(INT_C_[A-Za-z0-9]+|BLD_[A-Za-z0-9]+)_")   # zone prefix ("INT_C_Floors" is no floor)
SKIP = re.compile(r"(^REF_|^CAM_|^CTX_|^TER_|Glass|Glaz|Pane|Window|Door|Rail|Fence|Sign|Hedge|Lawn|Soil|Bed_|Curtain|Blind)", re.I)

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()


def world_bvh(ob):
    mw = ob.matrix_world
    me = ob.data
    verts = [mw @ v.co for v in me.vertices]
    return BVHTree.FromPolygons(verts, [list(p.vertices) for p in me.polygons]), verts


def first_other(ob, p, d, dist):
    """First hit of another object along d from p within dist: (distance, entering?, object) or None."""
    start = p
    for _ in range(8):
        left = dist - (p - start).length
        if left <= 0:
            return None
        ok, loc, nrm, _i, hob, _m = sc.ray_cast(dg, p, d, distance=left)
        if not ok:
            return None
        if hob is not ob:
            return (loc - start).length, nrm.dot(d) < 0, hob
        p = loc + d * 1e-5
    return None


def side(ob, s, d):
    """What lies on the side d of a thin sheet whose outer face point is s:
    'backed' another solid touches it (within 1.2 cm, or s + 5 mm is already inside it: coincident faces),
    'lining' a solid >= THIN_M thick within 1 m (suspended ceiling under its slab, cladding on a cavity), else None."""
    h = first_other(ob, s + d * 0.005, d, 3.0)
    if h is not None and not h[1]:
        return "backed"   # first face of another object is left, not entered: s + 5 mm is inside it
    h = first_other(ob, s - d * 0.002, d, 1.0)
    if h is None or not h[1]:
        return None
    if h[0] < 0.014:
        return "backed"
    ok, loc, _n, _i, hob, _m = sc.ray_cast(dg, s + d * (h[0] + 1e-4), d, distance=THIN_M - 0.002)   # 2 mm slack: a 10 cm part passes
    return "lining" if not ok or hob is not h[2] else None


rep = defaultdict(list)
n_obj = n_face = 0
for ob in bpy.data.objects:
    if ob.type != "MESH" or not ob.users_collection or ob.hide_render or SKIP.search(ob.name):
        continue
    if not ob.name.startswith(("GBF_", "GBS_INT")) or not ENVELOPE.search(ZONE.sub("", ob.name)):
        continue
    me = ob.data
    if not me.polygons:
        continue
    n_obj += 1
    tree, verts = world_bvh(ob)
    nmat = ob.matrix_world.to_3x3().inverted().transposed()
    thin_area, lining_area, worst, area_all = 0.0, 0.0, 9.9, 0.0
    for p in me.polygons:
        if p.area < MIN_AREA:
            continue
        n = (nmat @ p.normal).normalized()
        c = ob.matrix_world @ p.center
        a = p.area * ob.matrix_world.to_3x3().determinant() ** (2 / 3)
        area_all += a
        n_face += 1
        hit = tree.ray_cast(c - n * 1e-4, -n, 1.0)
        if hit[0] is None:
            continue   # open shell: reported by scene_qa (non-manifold), not here
        t = hit[3] + 1e-4
        if t >= THIN_M:
            continue
        # back-to-back: another object's solid starts within 1 cm behind the exit face (a finish layer on its slab,
        # cladding on its wall) -> the stack is the wall. The ray starts just inside our back face, so a coincident
        # face of the other solid is still hit (entering it: its normal faces the ray).
        sides = (side(ob, c - n * t, -n), side(ob, c, n))   # behind the sheet, in front of it
        if "backed" in sides:
            continue
        if "lining" in sides:
            lining_area += a
            continue
        thin_area += a
        worst = min(worst, t)
    if lining_area > 0:
        rep["lining"].append((ob.name, round(lining_area, 2)))
    if thin_area > 0:
        rep["thin"].append((ob.name, round(worst, 3), round(thin_area, 2), round(area_all, 2)))
rep["thin"].sort(key=lambda r: -r[2])
# what a player sees from inside (Block C, the gym/canteen interiors, open galleries) leaks visibly; closed shells of
# buildings without interiors do not (nothing lit to see inside), so they are listed apart
SEEN_INSIDE = re.compile(r"(INT_C|_Int_|Gallery)")
rep["thin_exterior_only"] = [r for r in rep["thin"] if not SEEN_INSIDE.search(r[0])]
rep["thin"] = [r for r in rep["thin"] if SEEN_INSIDE.search(r[0])]
by_zone = defaultdict(float)
for nm, _t, a, _all in rep["thin"] + rep["thin_exterior_only"]:
    m = re.match(r"(GBF|GBS)_((?:BLD|INT)_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)?)", nm)
    by_zone[m.group(2) if m else "?"] += a
rep["thin_area_by_zone"] = dict(sorted(by_zone.items(), key=lambda kv: -kv[1]))
rep["checked"] = {"objects": n_obj, "faces": n_face}
print("THIN checked", rep["checked"], "seen-inside thin objects", len(rep["thin"]), "m2",
      round(sum(r[2] for r in rep["thin"]), 1), "| exterior-only", len(rep["thin_exterior_only"]))
for r in rep["thin"][:40]:
    print("THIN", *r)
print("THIN by zone", rep["thin_area_by_zone"])
if OUT:
    json.dump(rep, open(OUT, "w"), indent=1)
