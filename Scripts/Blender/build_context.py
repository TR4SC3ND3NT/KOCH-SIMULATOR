# Surroundings ring, pass P0 (handoff sections 0 and 6): every OSM building within ~500 m of the campus
# (Art/Blender/Data/ctx_osm.json, © OpenStreetMap contributors, ODbL) as a massing prism on its footprint, height
# from OSM building:levels/height, else a type/area estimate flagged `koch_height_src = estimate` (floors to be counted
# from photos in P1). Buildings already in footprints.json (group Context, hand-set) and campus buildings are skipped.
# Base = lowest terrain under the footprint (TER ray cast) minus 0.3 m. Collections: CTX_Near (<= 150 m), CTX_Far,
# both under 08_Context. Run from build_all.py (after build_greybox.py, which makes the terrain).
import json
import os

import bmesh
import bpy
from mathutils import Vector

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DATA = os.path.join(REPO, "Art", "Blender", "Data")


def est_height(b):
    t = b["tags"]; kind = t.get("building", "yes"); area = b.get("area_m2", 100.0)
    if b.get("height_m"):
        return float(b["height_m"]), "osm"
    if b.get("levels"):
        return float(b["levels"]) * 3.0 + 1.5, "osm levels"
    table = {"garage": 2.6, "garages": 2.6, "shed": 2.6, "kiosk": 3.0, "house": 6.5, "detached": 6.5,
             "apartments": 16.5, "residential": 16.5, "industrial": 8.0, "warehouse": 8.0, "commercial": 8.0,
             "retail": 5.0, "school": 10.0, "kindergarten": 6.5, "university": 13.0, "service": 3.5}
    if kind in table:
        return table[kind], "estimate"
    return (3.5 if area < 150 else 7.0 if area < 600 else 10.0), "estimate"


def collection(name, parent):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in parent.children:
        parent.children.link(c)
    return c


def main():
    d = json.load(open(os.path.join(DATA, "ctx_osm.json"), encoding="utf-8"))
    known = {str(i.get("osm", "")).split("/")[-1] for i in json.load(open(os.path.join(DATA, "footprints.json"), encoding="utf-8"))["items"]}
    par = bpy.data.collections.get("08_Context") or bpy.data.collections.new("08_Context")
    if par.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(par)
    cols = {"near": collection("CTX_Near", par), "far": collection("CTX_Far", par)}
    for c in cols.values():
        for ob in list(c.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    ter = next((o for o in bpy.data.objects if o.name.startswith("TER")), None)
    dg = bpy.context.evaluated_depsgraph_get(); te = ter.evaluated_get(dg) if ter else None
    inv = ter.matrix_world.inverted() if ter else None
    coef = json.load(open(os.path.join(DATA, "terrain.json"), encoding="utf-8"))["base"]["coef"]
    def base(x, y):   # DEM quadratic of terrain.json (X, Y in hectometres): the ground outside the campus terrain
        X, Y = x / 100.0, y / 100.0
        return coef[0] + coef[1] * X + coef[2] * Y + coef[3] * X * X + coef[4] * X * Y + coef[5] * Y * Y
    def gz(x, y):
        if te:
            ok, loc, _, _ = te.ray_cast(inv @ Vector((x, y, 500.0)), Vector((0, 0, -1)))
            if ok:
                return (ter.matrix_world @ loc).z
        return base(x, y)
    n = 0
    for b in d["buildings"]:
        if b.get("in_campus") or str(b["osm_id"]).split("/")[-1] in known or len(b["footprint"]) < 3:
            continue
        ring = [tuple(p) for p in b["footprint"]]
        if ring[0] == ring[-1]:
            ring = ring[:-1]
        # counter-clockwise for outward faces
        area2 = sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1] for i in range(len(ring)))
        if area2 < 0:
            ring = ring[::-1]
        h, src = est_height(b)
        z0 = min(gz(x, y) for x, y in ring) - 0.3
        top = max(gz(x, y) for x, y in ring) + h
        bm = bmesh.new()
        lo = [bm.verts.new((x, y, z0)) for x, y in ring]; hi = [bm.verts.new((x, y, top)) for x, y in ring]
        bm.faces.new(lo[::-1]); bm.faces.new(hi)
        k = len(ring)
        for i in range(k):
            j = (i + 1) % k
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bm.normal_update()
        me = bpy.data.meshes.new(f"CTX_OSM_{b['osm_id']}".replace("/", "_"))
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(me.name, me)
        ob["koch_gen"] = "build_context.py"; ob["koch_osm"] = str(b["osm_id"]); ob["koch_height_m"] = h
        ob["koch_height_src"] = src; ob["koch_dist_m"] = float(b.get("dist_m", 0.0))
        ob.color = (0.62, 0.62, 0.66, 1) if src != "estimate" else (0.75, 0.62, 0.55, 1)
        cols["near" if b.get("dist_m", 999) <= 150 else "far"].objects.link(ob)
        n += 1
    print(f"build_context: {n} OSM buildings ({len(cols['near'].objects)} near, {len(cols['far'].objects)} far)")


main()
