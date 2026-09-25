# Builds the phase-1 campus greybox (terrain + building/site massing) from Art/Blender/Data/*.json into the open .blend.
# Used by R1 (Blender MCP or headless). Idempotent: removes objects tagged koch_gen="phase1" and rebuilds them.
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_greybox.py   (saves the file)
#      or exec() it inside a live Blender (then save manually).
# Units: metres, local campus frame (Scripts/Geo/campus_frame.py): X east, Y north, Z = ASL - 800 m.
import json
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(REPO, "Art", "Blender", "Data")
CAPTURE_DIR = os.environ.get("KOCH_CAPTURE_DIR", os.path.expanduser("~/site-capture"))  # same as Scripts/Geo/campus_frame.py
ORTHO = os.path.join(CAPTURE_DIR, "ortho", "ortho_bing_z19.png")  # local tracing ref, never packed
sys.path.insert(0, HERE)
from greybox.common import (FASCIA_M, Terrain, add_box, add_prism, add_roof, ccw, clear_generated, drop_collinear,  # noqa: E402
                            ensure_collection, load, make_object, offset_ring)

GEN = "phase1"
BURY_M = 0.3           # walls start this far below the lowest terrain point under the footprint
POST_M = 0.25          # canopy/gazebo post section

GROUP_COLLECTION = {
    "A": "BLD_A", "B": "BLD_B", "C": "BLD_C", "D": "BLD_D", "Hall": "BLD_Gallery",
    "E": "BLD_Other", "Other": "BLD_Other", "W1": "BLD_Other", "Pavilion": "BLD_Other", "Canteen": "BLD_Other",
    "Gate": "SITE_Checkpoint", "Garden": "GRD_Gazebos", "Sport": "SITE_Sport", "Context": "CTX_Buildings",
}
EXTRA_COLLECTIONS = {"SITE_Sport": "03_Site", "CTX_Buildings": "08_Context"}
STATUS_COLOR = {  # viewport object colour only (not a material): review aid for phase 1
    "confirmed": (0.80, 0.80, 0.78, 1), "probable": (0.72, 0.72, 0.70, 1),
    "uncertain": (0.95, 0.55, 0.20, 1), "context": (0.45, 0.47, 0.50, 1),
}
ROOF_COLOR = (0.62, 0.25, 0.22, 1)


# ---------------------------------------------------------------------------------------------- builders
def build_terrain(ter, grid):
    x0, y0, x1, y1 = grid["extent"]
    s = grid["spacing_m"]
    xs = np.arange(x0, x1 + s / 2, s)
    ys = np.arange(y0, y1 + s / 2, s)
    X, Y = np.meshgrid(xs, ys)
    Z = ter.base(X, Y) - np.where(ter.carriageway_mask(X, Y), ter.curb, 0.0)
    nx, ny = len(xs), len(ys)
    co = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()]).astype(np.float32)
    idx = np.arange(nx * ny, dtype=np.int32).reshape(ny, nx)
    quads = np.column_stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()])
    me = bpy.data.meshes.new("TER_Ground")
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.ravel())
    me.loops.add(quads.size)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4, dtype=np.int32))
    me.update(calc_edges=True)
    me.validate()
    ob = bpy.data.objects.new("TER_Ground", me)
    ob["koch_gen"] = GEN
    ob["koch_notes"] = "GLO-30 quadratic base + carriageways lowered by the curb reveal; pads/terraces in phase 4"
    ob.color = (0.55, 0.60, 0.50, 1)
    ensure_collection("01_Terrain").objects.link(ob)
    return ob


def build_item(it, ter):
    ring = ccw([list(p) for p in it["ring"]])
    roof = it.get("roof", {"type": "flat"})
    kind = it.get("kind", "building")
    col = ensure_collection(GROUP_COLLECTION.get(it.get("group"), "BLD_Other"))
    color = STATUS_COLOR.get(it.get("status"), STATUS_COLOR["probable"])
    rx = np.array([p[0] for p in ring])
    ry = np.array([p[1] for p in ring])
    zg = ter.base(np.append(rx, rx.mean()), np.append(ry, ry.mean()))
    z_low, z_high = float(zg.min()), float(zg.max())
    ffl = z_high + it.get("plinth_m", 0.0)
    cx, cy = float(rx.mean()), float(ry.mean())
    origin = (cx, cy, ffl)
    name = "GB_" + it["id"]

    if kind == "pitch" or roof.get("type") == "none":
        bm = bmesh.new()
        add_prism(bm, ring, [z_low - BURY_M, ffl])
        return [make_object(name, bm, col, origin, it, (0.35, 0.55, 0.35, 1))]

    overhang = roof.get("overhang_m", 0.0) if roof.get("type") != "flat" else 0.0
    wall = offset_ring(ring, overhang) if overhang else ring
    storeys = max(1, int(it.get("storeys", 1)))
    ftf = float(it.get("ftf_m", 3.6))
    z_eave = ffl + storeys * ftf
    obs = []

    if roof.get("open_sides"):  # canopy / gazebo: posts at the wall-line corners, no walls
        bm = bmesh.new()
        if kind == "gazebo":
            add_prism(bm, wall, [z_low - BURY_M, ffl])  # raised floor platform
        for x, y in drop_collinear(wall):
            add_box(bm, x, y, ffl if kind == "gazebo" else z_low - BURY_M, z_eave - FASCIA_M, POST_M)
        obs.append(make_object(name, bm, col, origin, it, color))
    else:
        top = z_eave + (roof.get("parapet_m", 0.0) if roof.get("type") == "flat" else 0.0)
        levels = [z_low - BURY_M, ffl] + [ffl + ftf * k for k in range(1, storeys)] + [top]
        bm = bmesh.new()
        add_prism(bm, wall, sorted(set(round(z, 4) for z in levels)))
        obs.append(make_object(name, bm, col, origin, it, color))

    if roof.get("type") not in ("flat", None):
        bm = bmesh.new()
        add_roof(bm, ring, z_eave, roof)
        obs.append(make_object(name + "_Roof", bm, col, origin, it, ROOF_COLOR))
    return obs


def build_reference():
    """Top-down Bing ortho on a plane under the terrain (00_Reference, never exported, image not packed)."""
    meta_path = os.path.splitext(ORTHO)[0] + ".json"
    if not (os.path.exists(ORTHO) and os.path.exists(meta_path)):
        print("reference ortho missing, skipped:", ORTHO)
        return None
    meta = json.load(open(meta_path))
    x0, y0, x1, y1 = meta["extent_local"]
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, 0)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new("UVMap")
    for loop, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = t
    img = bpy.data.images.load(ORTHO, check_existing=True)
    mat = bpy.data.materials.get("REF_Ortho") or bpy.data.materials.new("REF_Ortho")
    nt = mat.node_tree
    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None) or nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    ob = make_object("REF_Ortho_Bing", bm, ensure_collection("REF_Satellite", "00_Reference"), (0, 0, -8.0))
    ob.data.materials.append(mat)
    ob["koch_notes"] = "Bing aerial <=2021-10, local tracing reference only: never pack, commit or export"
    ob.hide_render = True
    return ob


def cut_terrain_holes():
    """Delete terrain quads inside 'terrain_holes' rings of Specs/*.json (open stairwells, light wells)."""
    specs = os.path.join(REPO, "Art", "Blender", "Specs")
    rings = []
    for fn in sorted(os.listdir(specs)) if os.path.isdir(specs) else []:
        if fn.endswith(".json"):
            rings += json.load(open(os.path.join(specs, fn), encoding="utf-8")).get("terrain_holes", [])
    ob = bpy.data.objects.get("TER_Ground")
    if not rings or ob is None:
        return
    bm = bmesh.new()
    bm.from_mesh(ob.data)

    def inside(x, y, ring):
        c, n = False, len(ring)
        for i in range(n):
            (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                c = not c
        return c
    dead = [f for f in bm.faces if any(inside(f.calc_center_median().x, f.calc_center_median().y, r) for r in rings)]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    print(f"terrain: cut {len(dead)} quads for {len(rings)} holes")


def hide_replaced():
    """Phase-1 massing that a phase-2/site spec replaces stays in the file but hidden (Specs/*.json 'replaces')."""
    specs = os.path.join(REPO, "Art", "Blender", "Specs")
    for fn in sorted(os.listdir(specs)) if os.path.isdir(specs) else []:
        if fn.endswith(".json"):
            for name in json.load(open(os.path.join(specs, fn), encoding="utf-8")).get("replaces", []):
                ob = bpy.data.objects.get(name)
                if ob:
                    ob.hide_set(True)
                    ob.hide_render = True


def main():
    ter_spec = load("terrain.json")
    items = load("footprints.json")["items"]
    ter = Terrain(ter_spec)
    for name, parent in EXTRA_COLLECTIONS.items():
        ensure_collection(parent)
        ensure_collection(name, parent)
    clear_generated(GEN)
    build_terrain(ter, ter_spec["grid"])
    n = 0
    for it in items:
        try:
            n += len(build_item(it, ter))
        except Exception as ex:  # keep building the rest; report the bad item
            print("FAILED", it["id"], repr(ex))
    build_reference()
    hide_replaced()
    cut_terrain_holes()
    sc = bpy.context.scene
    sc["koch_origin_lat"], sc["koch_origin_lon"] = 42.8566, 74.6790
    sc["koch_z_datum_asl"] = ter_spec["frame"]["z_datum_asl"]
    print(f"phase1 greybox: terrain + {n} objects from {len(items)} items")
    if bpy.app.background:
        bpy.ops.wm.save_mainfile(compress=True)


main()
