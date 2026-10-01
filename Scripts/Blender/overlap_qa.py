# Model-in-model QA (R1, 2026-10-01): props / furniture / trees that interpenetrate walls, buildings or each other, and
# objects buried entirely inside another closed solid (hidden waste). Read-only, never saves.
# Prop vs solid: >= 30 % of the prop's sample points (bbox lattice 5x5x5, shrunk 2 cm) lie inside the other closed mesh
# (ray-parity test on a BVH). Designed contacts (a radiator on its wall, a desk on the floor) stay below that.
# Run: blender -b FILE.blend -P Scripts/Blender/overlap_qa.py -- OUT.json
import json
import re
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
PROP = re.compile(r"(Bench|Bin|Tree|Lamp|Desk|Chair|Sink|Toilet|Radiator|Planter|Sign|Locker|Cabinet|Piano|PCs|Monitor|"
                  r"Vending|Coffee|Cooler|Table|Bollard|Bike|Pole|Terminal|Board|TV|AC|Hydrant|Hose|Mirror|Soap|Pot|Shed)", re.I)
SOLID = re.compile(r"(Wall|Slab|Roof|Plinth|Pilaster|Stair|Step|Landing|Partition|Column|Box|Beam|Floor|Parapet)", re.I)


def world_bvh(ob):
    me = ob.data
    mw = ob.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    return BVHTree.FromPolygons(verts, polys, epsilon=0.0), verts


def inside(bvh, p, dirs=(Vector((0.31, 0.27, 0.91)), Vector((-0.6, 0.52, -0.6)))):
    """Ray-parity inside test, two directions must agree (robust to grazing hits)."""
    votes = 0
    for d in dirs:
        n, o = 0, p.copy()
        for _ in range(64):
            hit = bvh.ray_cast(o, d)
            if hit[0] is None:
                break
            n += 1
            o = hit[0] + d * 1e-4
        votes += n % 2
    return votes == len(dirs)


def bbox(verts):
    xs, ys, zs = zip(*verts)
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def main():
    obs = [o for o in bpy.context.scene.objects if o.type == "MESH" and len(o.data.polygons) and not o.hide_render]
    data = {}
    for o in obs:
        bvh, verts = world_bvh(o)
        data[o.name] = (bvh, bbox(verts))
    props = [o.name for o in obs if PROP.search(o.name) and not o.name.startswith("TER_")]
    solids = [o.name for o in obs if (SOLID.search(o.name) or PROP.search(o.name)) and not o.name.startswith("TER_")]
    # coarse grid over solids' bboxes
    cell = 4.0
    grid = {}
    for n in solids:
        lo, hi = data[n][1]
        for i in range(int(lo.x // cell), int(hi.x // cell) + 1):
            for j in range(int(lo.y // cell), int(hi.y // cell) + 1):
                grid.setdefault((i, j), []).append(n)
    res = []
    for n in props:
        lo, hi = data[n][1]
        size = hi - lo
        if min(size) < 0.02:
            continue
        sh = Vector([min(0.02, 0.2 * size[k]) for k in range(3)])     # thin props (boards, skins): shrink less
        a, b = lo + sh, hi - sh
        pts = [Vector((a.x + (b.x - a.x) * i / 4, a.y + (b.y - a.y) * j / 4, a.z + (b.z - a.z) * k / 4))
               for i in range(5) for j in range(5) for k in range(5)]
        cands = set()
        for i in range(int(lo.x // cell), int(hi.x // cell) + 1):
            for j in range(int(lo.y // cell), int(hi.y // cell) + 1):
                cands.update(grid.get((i, j), ()))
        cands.discard(n)
        own = n.rsplit("_", 1)[0]
        for m in cands:
            if re.search(r"Tree|Hedge|Shrub", m):        # foliage proxies are not solids (UE foliage has no collision)
                continue
            mlo, mhi = data[m][1]
            if any(hi[k] <= mlo[k] or lo[k] >= mhi[k] for k in range(3)):
                continue
            if m.startswith(own) or n.startswith(m.rsplit("_", 1)[0] + "_"):   # parts of one prop (seat / legs, frame / leaf)
                continue
            ins = sum(1 for p in pts if mlo.x <= p.x <= mhi.x and mlo.y <= p.y <= mhi.y and mlo.z <= p.z <= mhi.z
                      and inside(data[m][0], p))
            if ins >= 0.30 * len(pts):
                res.append({"prop": n, "in": m, "frac": round(ins / len(pts), 2), "at": [round(v, 2) for v in (lo + hi) / 2]})
    res.sort(key=lambda r: -r["frac"])
    print("props", len(props), "solids", len(solids), "interpenetrations", len(res))
    for r in res[:80]:
        print(r["frac"], r["prop"], "IN", r["in"], r["at"])
    if OUT:
        json.dump(res, open(OUT, "w"), indent=0)


main()
