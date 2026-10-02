# Player-view walk QA of the greybox (R1, before the UE hand-off). Read-only. On a 0.5 m grid over the campus + street
# frontage, outside the building footprints, it finds the walking surface under each point (foliage, roofs, canopies,
# lamps and signs are passed through: they get no collision in UE or are overhead) and reports
#   HOLE      nothing to stand on (the player falls out of the world)
#   DROP      a > 1.0 m step down between neighbour cells with no fence/railing/hedge/wall within 0.6 m (fall hazard)
#   SLIT      a one-cell trench > 0.15 m deep between higher neighbours (foot catches: slab/wall/curb joints)
#   HEADROOM  something solid < 2.0 m above the walking surface (player bumps / gets stuck), foliage excluded
#   STEEP     terrain steeper than 40 deg that is not covered by stairs/ramps/beds
# and per building: floor at FFL behind every door, and the storeys a window looks into without a floor (empty shell).
# Run: blender -b FILE.blend -P Scripts/Blender/walk_qa.py -- OUT.json [STEP_M]
import json
import math
import os
import re
import sys
from collections import defaultdict

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
STEP = float(argv[1]) if len(argv) > 1 else 0.5
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SPECS = os.path.join(REPO, "Art", "Blender", "Specs")
PASS = re.compile(r"(?<![Ss])Tree|conifer|broadleaf|Thuja|Juniper|Pine|Spruce|Poplar|Rose|Bush|Shrub|Crown|Roof|Canopy|Soffit|"
                  r"Fascia|Eave|Gutter|Downpipe|Lamp|Sign|Flag|_Net|String|Flood|Ceiling|Cornice|Pergola|Wire|Garland|"
                  r"Hoop|Backboard|Board|Cable|MapLimit|Capitals|Bulb|Globe|CCTV|^REF_|_Sur_|_Win_|Pilaster|Cladding|Glass|Sill", re.I)
FOLIAGE = re.compile(r"(?<![Ss])Tree|conifer|broadleaf|Thuja|Juniper|Pine|Spruce|Poplar|Rose|Bush|Shrub|Crown|Hedge|MapLimit|"
                     r"String|Garland|Wire|Cable", re.I)
BARRIER = re.compile(r"Fence|Rail|Hedge|Wall|Parapet|Cheek|Coping|Retain|Balustrade|Gate|Barrier|Bed|Planter", re.I)
WALKABLE_SLOPE = math.radians(40)
# surfaces a player walks on (DROP/SLIT are only judged between these; props, posts, parapets are obstacles)
WALK = re.compile(r"^TER_|Path|Paving|Walk|Landing|Slab|Deck|Plaza|Court|Pitch|Turf|Strip|Road|Crossing|Floor|Stair|Steps|"
                  r"Flight|Ramp|Terrace|Apron|Sidewalk|Parking|Lawn|Bank|Pad|Yard|Clover|Herringbone|Lot")   # case-sensitive:
# CamelCase name parts ("DForecourt" must not read as a Court)

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
DOWN, UP = Vector((0, 0, -1)), Vector((0, 0, 1))


def support(x, y, z_top=90.0):
    """First surface under (x, y) that is not passed through: (z, object name, normal z) or None."""
    p = Vector((x, y, z_top))
    for _ in range(80):
        hit, loc, n, _i, ob, _m = sc.ray_cast(dg, p, DOWN, distance=200.0)
        if not hit:
            return None
        if not PASS.search(ob.name):
            return loc.z, ob.name, n.z
        p = loc + DOWN * 1e-4
    return None


def point_in(poly, x, y):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) + 1e-12) + x1:
            inside = not inside
    return inside


def inside_np(P, ring):
    R = np.asarray(ring, float)
    x, y = P[:, 0], P[:, 1]
    res = np.zeros(len(P), bool)
    for (x1, y1), (x2, y2) in zip(R, np.roll(R, -1, axis=0)):
        res ^= ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / ((y2 - y1) + 1e-12) + x1)
    return res


def building_rings():
    rings = {}
    for fn in sorted(os.listdir(SPECS)):
        if not (fn.startswith("BLD_") and fn.endswith(".json")):
            continue
        s = json.load(open(os.path.join(SPECS, fn)))
        a = s["anchor"]
        ox, oy = a["world_xy"]
        dx, dy = a["x_dir"]
        n = math.hypot(dx, dy)
        dx, dy = dx / n, dy / n
        k = float(s.get("scale", 1.0))
        cx = sum(p[0] for p in s["ring"]) / len(s["ring"])
        cy = sum(p[1] for p in s["ring"]) / len(s["ring"])
        ring = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in s["ring"]]
        rings[s["id"]] = dict(ring=[(ox + dx * x - dy * y, oy + dy * x + dx * y) for x, y in ring], spec=s)
    return rings


def main():
    site = json.load(open(os.path.join(REPO, "Art", "Blender", "Data", "site_osm.json")))
    campus = site["campus_boundary"]
    front = [(88.0, -131.0), (216.0, -131.0), (216.0, -95.0), (88.0, -95.0)]   # street frontage, crossing, bus stop
    blds = building_rings()
    xs = np.arange(-212.0, 222.0, STEP)
    ys = np.arange(-131.0, 101.0, STEP)
    H, W = len(ys), len(xs)
    Z = np.full((H, W), np.nan)
    NZ = np.ones((H, W))
    OBJ = np.full((H, W), -1, int)
    names = []
    nid = {}
    area = np.zeros((H, W), bool)
    inbld = np.zeros((H, W), bool)
    rep = defaultdict(list)
    GX, GY = np.meshgrid(xs, ys)
    P = np.column_stack([GX.ravel(), GY.ravel()])
    area = (inside_np(P, campus) | inside_np(P, front)).reshape(H, W)
    for b in blds.values():
        inbld |= inside_np(P, b["ring"]).reshape(H, W)
    for j, i in zip(*np.nonzero(area & ~inbld)):
            x, y = float(xs[i]), float(ys[j])
            s = support(x, y)
            if s is None:
                rep["HOLE"].append((round(x, 1), round(y, 1)))
                continue
            Z[j, i], NZ[j, i] = s[0], s[2]
            if s[1] not in nid:
                nid[s[1]] = len(names)
                names.append(s[1])
            OBJ[j, i] = nid[s[1]]
    ok = area & ~inbld & ~np.isnan(Z)
    # DROP / SLIT between 4-neighbours
    for (dj, di) in ((0, 1), (1, 0)):
        a = ok[:H - dj, :W - di] & ok[dj:, di:]
        dz = Z[dj:, di:] - Z[:H - dj, :W - di]
        for j, i in zip(*np.nonzero(a & (np.abs(dz) > 1.0))):
            hi_j, hi_i, lo_j, lo_i = (j + dj, i + di, j, i) if dz[j, i] > 0 else (j, i, j + dj, i + di)
            if not (WALK.search(names[OBJ[hi_j, hi_i]]) and WALK.search(names[OBJ[lo_j, lo_i]])):
                continue
            if BARRIER.search(names[OBJ[hi_j, hi_i]]) or BARRIER.search(names[OBJ[lo_j, lo_i]]):
                continue
            # a barrier on the high side within 0.6 m toward the drop protects it; several heights, since one ray
            # can pass between the bars / mid rails of a railing
            d = Vector((xs[lo_i] - xs[hi_i], ys[lo_j] - ys[hi_j], 0)).normalized()
            guarded = False
            for hz in (0.15, 0.4, 0.65, 0.9):
                ph = Vector((xs[hi_i], ys[hi_j], Z[hi_j, hi_i] + hz))
                hit, _l, _n, _x, ob, _m = sc.ray_cast(dg, ph - d * 0.3, d, distance=0.9)
                if hit and BARRIER.search(ob.name):
                    guarded = True
                    break
            if guarded:
                continue
            rep["DROP"].append((round(float(xs[hi_i]), 1), round(float(ys[hi_j]), 1), round(abs(float(dz[j, i])), 2),
                                names[OBJ[hi_j, hi_i]], names[OBJ[lo_j, lo_i]]))
    c = ok[1:-1, 1:-1]
    for (a1, a2) in (((slice(1, -1), slice(0, -2)), (slice(1, -1), slice(2, None))),
                     ((slice(0, -2), slice(1, -1)), (slice(2, None), slice(1, -1)))):
        z0 = Z[1:-1, 1:-1]
        m = c & ok[a1] & ok[a2] & (Z[a1] - z0 > 0.15) & (Z[a2] - z0 > 0.15) & (np.abs(Z[a1] - Z[a2]) < 0.1)
        for j, i in zip(*np.nonzero(m)):
            if not all(WALK.search(names[OBJ[jj, ii]]) for jj, ii in ((j + 1, i + 1), (a1[0].start + j, a1[1].start + i),
                                                                      (a2[0].start + j, a2[1].start + i))):
                continue
            rep["SLIT"].append((round(float(xs[i + 1]), 1), round(float(ys[j + 1]), 1),
                                round(float(min(Z[a1][j, i], Z[a2][j, i]) - z0[j, i]), 2), names[OBJ[j + 1, i + 1]]))
    # HEADROOM (every other cell) and STEEP
    for j in range(0, H, 2):
        for i in range(0, W, 2):
            if not ok[j, i]:
                continue
            p = Vector((xs[i], ys[j], Z[j, i] + 0.05))
            for _ in range(6):
                hit, loc, _n, _x, ob, _m = sc.ray_cast(dg, p, UP, distance=2.0 - (p.z - Z[j, i]))
                if not hit:
                    break
                if FOLIAGE.search(ob.name) or ob.name == names[OBJ[j, i]] or ob.name.startswith("REF_"):
                    p = loc + UP * 1e-3
                    continue
                if loc.z - Z[j, i] < 1.0:   # a ground prop (bench, sign, bollard): walked round, not under
                    break
                rep["HEADROOM"].append((round(float(xs[i]), 1), round(float(ys[j]), 1), round(loc.z - Z[j, i], 2),
                                        ob.name, names[OBJ[j, i]]))
                break
            if names[OBJ[j, i]].startswith("TER_") and math.acos(max(-1.0, min(1.0, NZ[j, i]))) > WALKABLE_SLOPE:
                rep["STEEP"].append((round(float(xs[i]), 1), round(float(ys[j]), 1)))
    # buildings: floor behind every door; storeys without a floor behind their windows
    for bid, b in blds.items():
        s = b["spec"]
        base = next((o for o in bpy.data.objects if o.name == f"GBF_{bid}_Slabs"), None)
        ffl = float(base["koch_ffl"]) if base is not None and "koch_ffl" in base else None
        doors = []
        for o in bpy.data.objects:
            if o.type != "MESH" or not o.data.vertices or not o.name.startswith(f"GBF_{bid}_"):
                continue
            rest = o.name[len(f"GBF_{bid}_"):]
            if re.match(r"Entrance_E\d+_\d+_(Doors|Frame)$|DoorBay_[A-Z]$", rest):
                doors.append(o)
            elif ffl is not None and re.match(r"Win_E\d+_\d+$", rest):   # door-type window units (booths, hall end)
                zmin = min((o.matrix_world @ v.co).z for v in o.data.vertices)
                zmax = max((o.matrix_world @ v.co).z for v in o.data.vertices)
                if zmin < ffl + 0.12 and zmax - zmin > 1.8:
                    doors.append(o)
        ring = b["ring"]
        cx, cy = sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)
        for o in doors:
            W3 = np.array([o.matrix_world @ v.co for v in o.data.vertices])
            c = W3.mean(0)
            # inward = the door frame's thin horizontal axis, signed toward the building centre (a long narrow block's
            # centre direction runs nearly along the facade)
            ev, evec = np.linalg.eigh(np.cov((W3[:, :2] - W3[:, :2].mean(0)).T) + np.eye(2) * 1e-9)
            n2 = evec[:, 0]
            if n2[0] * (cx - c[0]) + n2[1] * (cy - c[1]) < 0:
                n2 = -n2
            d = Vector((float(n2[0]), float(n2[1]), 0))
            p = Vector((c[0], c[1], W3[:, 2].min() + 1.2)) + d * 1.2      # 1.2 m inside the door
            hit, loc, _n, _x, ob, _m = sc.ray_cast(dg, p, DOWN, distance=4.0)
            if not hit or abs(loc.z - W3[:, 2].min()) > 0.35:
                rep["DOOR_NO_FLOOR"].append((o.name, round(float(c[0]), 1), round(float(c[1]), 1),
                                             None if not hit else round(loc.z - W3[:, 2].min(), 2), ob.name if hit else None))
        st, n = s.get("storey_m", 3.3), int(s.get("storeys", 1))
        if not point_in(ring, cx, cy):
            xs_, ys_ = [p[0] for p in ring], [p[1] for p in ring]
            cand = [(x, y) for x in np.linspace(min(xs_), max(xs_), 9)[1:-1] for y in np.linspace(min(ys_), max(ys_), 9)[1:-1]
                    if point_in(ring, x, y)]
            cx, cy = cand[len(cand) // 2] if cand else (cx, cy)
        if n > 1 and not s.get("interior_floors"):
            zf = ffl if ffl is not None else 0.0
            missing = []
            for k in range(1, n):
                hit, loc, _n, _x, ob, _m = sc.ray_cast(dg, Vector((cx, cy, zf + st * k + 1.0)), DOWN, distance=1.5)
                if not hit or not re.search(r"Floor|Slab", ob.name):
                    missing.append(k + 1)
            if missing:
                rep["STOREYS_WITHOUT_FLOOR"].append((bid, n, missing))
    for k, v in rep.items():
        print(f"WALK {k}: {len(v)}", v[:8])
    if OUT:
        json.dump(rep, open(OUT, "w"), indent=1, default=str)
        np.savez(os.path.splitext(OUT)[0] + "_grid.npz", Z=Z, ok=ok, inbld=inbld, xs=xs, ys=ys)
        print("WALK written", OUT)


main()
