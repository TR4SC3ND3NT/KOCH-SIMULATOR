# Builds the phase-1 campus greybox (terrain + building/site massing) from Art/Blender/Data/*.json into the open .blend.
# Used by R1 (Blender MCP or headless). Idempotent: removes objects tagged koch_gen="phase1" and rebuilds them.
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_greybox.py   (saves the file)
#      or exec() it inside a live Blender (then save manually).
# Units: metres, local campus frame (Scripts/Geo/campus_frame.py): X east, Y north, Z = ASL - 800 m.
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(REPO, "Art", "Blender", "Data")
CAPTURE_DIR = os.environ.get("KOCH_CAPTURE_DIR", os.path.expanduser("~/site-capture"))  # same as Scripts/Geo/campus_frame.py
ORTHO = os.path.join(CAPTURE_DIR, "ortho", "ortho_bing_z19.png")  # local tracing ref, never packed
sys.path.insert(0, os.path.join(HERE, "third_party"))
from bpypolyskel import bpypolyskel  # noqa: E402  (GPL-3.0 tool code, see third_party/bpypolyskel/SOURCE.txt)

GEN = "phase1"
FASCIA_M = 0.25        # roof edge thickness; keeps every roof a closed solid (no coplanar soffit/wall faces)
BURY_M = 0.3           # walls start this far below the lowest terrain point under the footprint
POST_M = 0.25          # canopy/gazebo post section
COLLINEAR_DEG = 1.0    # vertices straighter than this are dropped before the straight skeleton

GROUP_COLLECTION = {
    "A": "BLD_A", "B": "BLD_B", "C": "BLD_C", "D": "BLD_D", "Hall": "BLD_Gallery",
    "E": "BLD_Other", "W1": "BLD_Other", "Pavilion": "BLD_Other", "Canteen": "BLD_Other",
    "Gate": "SITE_Checkpoint", "Garden": "GRD_Gazebos", "Sport": "SITE_Sport", "Context": "CTX_Buildings",
}
EXTRA_COLLECTIONS = {"SITE_Sport": "03_Site", "CTX_Buildings": "08_Context"}
STATUS_COLOR = {  # viewport object colour only (not a material): review aid for phase 1
    "confirmed": (0.80, 0.80, 0.78, 1), "probable": (0.72, 0.72, 0.70, 1),
    "uncertain": (0.95, 0.55, 0.20, 1), "context": (0.45, 0.47, 0.50, 1),
}
ROOF_COLOR = (0.62, 0.25, 0.22, 1)


# ---------------------------------------------------------------------------------------------- data
def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


class Terrain:
    """Base quadratic surface (hectometre coords) plus lowered carriageways."""

    def __init__(self, spec):
        self.c = np.array(spec["base"]["coef"])
        self.curb = spec["curb_reveal_m"]
        self.streets = [(np.array(s["centerline"], float), s["width_m"] / 2) for s in spec["streets"]]

    def base(self, x, y):
        X, Y = np.asarray(x) / 100.0, np.asarray(y) / 100.0
        c = self.c
        return c[0] + c[1] * X + c[2] * Y + c[3] * X * X + c[4] * X * Y + c[5] * Y * Y

    def carriageway_mask(self, x, y):
        """True where (x, y) lies on any carriageway (distance to centreline < half width)."""
        inside = np.zeros(np.shape(x), bool)
        for line, hw in self.streets:
            for p, q in zip(line[:-1], line[1:]):
                d = q - p
                L2 = float(d @ d)
                if L2 < 1e-6:
                    continue
                t = np.clip(((x - p[0]) * d[0] + (y - p[1]) * d[1]) / L2, 0.0, 1.0)
                dx, dy = x - (p[0] + t * d[0]), y - (p[1] + t * d[1])
                inside |= dx * dx + dy * dy < hw * hw
        return inside


# ---------------------------------------------------------------------------------------------- geometry helpers
def ccw(r):
    a = 0.5 * sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r)))
    return r if a > 0 else r[::-1]


def drop_collinear(r):
    out = []
    n = len(r)
    for i in range(n):
        a, b, c = Vector(r[i - 1]), Vector(r[i]), Vector(r[(i + 1) % n])
        u, v = (b - a), (c - b)
        if u.length < 0.05:
            continue
        if v.length > 1e-6 and abs(math.degrees(u.angle_signed(v))) < COLLINEAR_DEG:
            continue
        out.append(list(r[i]))
    return out


def offset_ring(r, d):
    """Mitre offset of a CCW ring: d > 0 moves edges inward (left side), d < 0 outward."""
    n = len(r)
    lines = []
    for i in range(n):
        p, q = Vector(r[i]), Vector(r[(i + 1) % n])
        t = (q - p).normalized()
        nrm = Vector((-t.y, t.x))
        lines.append((p + nrm * d, t))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1.x * d2.y - d1.y * d2.x
        if abs(den) < 1e-9:
            out.append([p2.x, p2.y])
            continue
        s = ((p2.x - p1.x) * d2.y - (p2.y - p1.y) * d2.x) / den
        out.append([p1.x + d1.x * s, p1.y + d1.y * s])
    return out


def add_prism(bm, ring, levels):
    """Closed vertical prism over a CCW ring; one face band per consecutive pair in levels (z list)."""
    loops = [[bm.verts.new((x, y, z)) for x, y in ring] for z in levels]
    n = len(ring)
    for lo, hi in zip(loops[:-1], loops[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(list(reversed(loops[0])))
    bm.faces.new(loops[-1])


def add_box(bm, cx, cy, z0, z1, s):
    h = s / 2
    add_prism(bm, [[cx - h, cy - h], [cx + h, cy - h], [cx + h, cy + h], [cx - h, cy + h]], [z0, z1])


def add_roof(bm, ring, z_eave, roof):
    """Roof solid over the eave outline: fascia band + skeleton/gable faces. ring is CCW at eave outline."""
    kind = roof.get("type", "hip")
    pitch = math.radians(roof.get("pitch_deg", 20))
    z_soffit = z_eave - FASCIA_M
    ring = drop_collinear(ring)
    n = len(ring)
    bot = [bm.verts.new((x, y, z_soffit)) for x, y in ring]
    top = [bm.verts.new((x, y, z_eave)) for x, y in ring]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bm.faces.new(list(reversed(bot)))

    if kind == "gable" and n == 4:
        e = [Vector(ring[(i + 1) % 4]) - Vector(ring[i]) for i in range(4)]
        k = 0 if e[0].length >= e[1].length else 1           # long edges k and k+2 carry the slopes
        a, b, c, d = [top[(k + i) % 4] for i in range(4)]
        span = e[(k + 1) % 4].length
        h = span / 2 * math.tan(pitch)
        r1 = bm.verts.new(((d.co + a.co) / 2) + Vector((0, 0, h)))
        r2 = bm.verts.new(((b.co + c.co) / 2) + Vector((0, 0, h)))
        for f in ((a, b, r2, r1), (c, d, r1, r2), (b, c, r2), (d, a, r1)):
            bm.faces.new(f)
        return
    verts = [Vector((x, y, z_eave)) for x, y in ring]
    faces = bpypolyskel.polygonize(verts, 0, n, None, 0.0, math.tan(pitch))
    new = top + [bm.verts.new(v) for v in verts[n:]]
    for f in faces:
        if len(set(f)) != len(f):  # degenerate skeleton face (Bonsai roof.py safeguard)
            continue
        try:
            bm.faces.new([new[i] for i in f])
        except ValueError:          # duplicate face from a merged skeleton node
            pass


# ---------------------------------------------------------------------------------------------- scene helpers
def ensure_collection(name, parent_name=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    parent = bpy.data.collections.get(parent_name) if parent_name else bpy.context.scene.collection
    if parent is None:
        parent = ensure_collection(parent_name)
    if col.name not in parent.children:
        parent.children.link(col)
    return col


def clear_generated():
    for ob in [o for o in bpy.data.objects if o.get("koch_gen") == GEN]:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def make_object(name, bm, collection, origin, item=None, color=None):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.translate(bm, verts=bm.verts, vec=-Vector(origin))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = origin
    ob["koch_gen"] = GEN
    if item:
        ob["koch_id"] = item["id"]
        ob["koch_status"] = item.get("status", "")
        ob["koch_evidence"] = " | ".join(item.get("evidence", []))
        if item.get("notes"):
            ob["koch_notes"] = item["notes"]
    if color:
        ob.color = color
    collection.objects.link(ob)
    return ob


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


def main():
    ter_spec = load("terrain.json")
    items = load("footprints.json")["items"]
    ter = Terrain(ter_spec)
    for name, parent in EXTRA_COLLECTIONS.items():
        ensure_collection(parent)
        ensure_collection(name, parent)
    clear_generated()
    build_terrain(ter, ter_spec["grid"])
    n = 0
    for it in items:
        try:
            n += len(build_item(it, ter))
        except Exception as ex:  # keep building the rest; report the bad item
            print("FAILED", it["id"], repr(ex))
    build_reference()
    sc = bpy.context.scene
    sc["koch_origin_lat"], sc["koch_origin_lon"] = 42.8566, 74.6790
    sc["koch_z_datum_asl"] = ter_spec["frame"]["z_datum_asl"]
    print(f"phase1 greybox: terrain + {n} objects from {len(items)} items")
    if bpy.app.background:
        bpy.ops.wm.save_mainfile(compress=True)


main()
