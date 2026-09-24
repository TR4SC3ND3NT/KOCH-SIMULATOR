# Shared greybox helpers for the Blender builders (build_greybox.py phase 1, build_facades.py phase 2). R1 tooling.
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
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DATA = os.path.join(REPO, "Art", "Blender", "Data")
SPECS = os.path.join(REPO, "Art", "Blender", "Specs")
sys.path.insert(0, os.path.join(HERE, "..", "third_party"))
from bpypolyskel import bpypolyskel  # noqa: E402  (GPL-3.0 tool code, see third_party/bpypolyskel/SOURCE.txt)

FASCIA_M = 0.25        # roof edge thickness; keeps every roof a closed solid (no coplanar soffit/wall faces)
COLLINEAR_DEG = 1.0    # vertices straighter than this are dropped before the straight skeleton


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

def ensure_collection(name, parent_name=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    parent = bpy.data.collections.get(parent_name) if parent_name else bpy.context.scene.collection
    if parent is None:
        parent = ensure_collection(parent_name)
    if col.name not in parent.children:
        parent.children.link(col)
    return col

def clear_generated(gen):
    for ob in [o for o in bpy.data.objects if o.get("koch_gen") == gen]:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)

def make_object(name, bm, collection, origin, item=None, color=None, gen="phase1", matrix=None):
    """Link a new object whose mesh is bm. bm is in world space (origin subtracted), or in local space when matrix
    (object matrix_world) is given; the object origin is origin / matrix."""
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if matrix is None:
        bmesh.ops.translate(bm, verts=bm.verts, vec=-Vector(origin))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    if matrix is None:
        ob.location = origin
    else:
        ob.matrix_world = matrix
    ob["koch_gen"] = gen
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
