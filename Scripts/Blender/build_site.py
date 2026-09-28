# Builds site greybox elements from Art/Blender/Specs/SITE_<Name>.json (gazebos, hedges, hedge arch, walls, fences,
# gate canopy, turnstiles, gate leaves, benches, lamps, bins, bike racks, steps, planters, signs, zebra, bus shelter).
# Used by R1. Idempotent per spec: removes objects tagged koch_gen="site:<id>". Objects are named GBS_<id>_<name>.
# Run inside Blender with KOCH_SITE="SITE_Gate,SITE_Garden" or headless:
#   KOCH_SITE=SITE_Garden blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_site.py
# Coordinates: world local XY (m); z relative to the local ground at each point unless the element has "z_abs": true.
import json
import math
import os
import re
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from greybox.common import SPECS, Terrain, ensure_collection, load, make_object  # noqa: E402
from greybox.materials import mat  # noqa: E402
from greybox.kit import Opening, box, wall_piece  # noqa: E402
from greybox.sweep import hedge_profile, rect_profile, sweep_profile  # noqa: E402

BURY = 0.3
COL = {
    "hedge": (0.25, 0.42, 0.22, 1), "wall": (0.62, 0.60, 0.55, 1), "brick": (0.50, 0.22, 0.17, 1),
    "metal": (0.18, 0.18, 0.19, 1), "white": (0.90, 0.90, 0.88, 1), "roof": (0.45, 0.25, 0.18, 1),
    "wood": (0.40, 0.27, 0.16, 1), "stone": (0.55, 0.53, 0.50, 1), "paint": (0.95, 0.95, 0.92, 1),
    "glass": (0.40, 0.50, 0.55, 1), "low": (0.95, 0.55, 0.20, 1), "accent": (0.42, 0.52, 0.85, 1),
    "terrazzo": (0.80, 0.79, 0.76, 1), "granite": (0.52, 0.40, 0.38, 1),
}


SURFACE_SLOT = (("clover", "M_Paver_Clover_Grey"), ("herringbone", "M_Paver_Herringbone_Grey"), ("asphalt", "M_Asphalt"),
                ("granite", "M_Granite_Red"), ("grating", "M_Steel_Grating"), ("terrazzo", "M_Terrazzo"))
MATERIAL_SLOT = {"metal": "M_Steel_Paint_Dark", "stone": "M_Concrete_Precast", "brick": "M_Tile_Brick_Red",
                 "granite": "M_Granite_Red", "hedge": "M_Hedge_Foliage", "wood": "M_Wood_Stained", "white": "M_Paint_White",
                 "paint": "M_Paint_White", "glass": "M_Glass", "terrazzo": "M_Terrazzo", "accent": "M_Paint_Blue",
                 "roof": "M_Sheet_Brown", "concrete": "M_Concrete", "wrought_iron": "M_Wrought_Iron"}
TYPE_SLOT = {"tree": "M_Tree", "hedge": "M_Hedge_Foliage", "planter": "M_Concrete_Precast", "lamp": "M_Steel_Paint_Dark",
             "lamp_orn": "M_Steel_Paint_Dark", "bench": "M_Wood_Stained", "roof_plane": "M_Paving_Generic",
             "path": "M_Paving_Generic", "zebra": "M_Road_Paint_White", "wall": "M_Concrete", "fence": "M_Steel_Paint_Dark",
             "stairs_run": "M_Granite_Red", "sign": "M_Sign_Panel", "bin": "M_Plastic_Grey", "bike_rack": "M_Steel_Galv",
             "turnstile": "M_Steel_Galv", "gate_leaf": "M_Steel_Paint_Dark", "canopy": "M_Sheet_Brown", "slab": "M_Concrete",
             "box": "M_Concrete", "rail3d": "M_Steel_Paint_Dark",
             "pergola": "M_Steel_Paint_Maroon", "sink": "M_Ceramic_White"}


TYPE_UE = {"bench": "bench_generic", "bin": "bin_generic", "lamp": "street_lamp", "lamp_orn": "lamp_ornamental",
           "bike_rack": "bike_rack", "tree": "tree", "hedge": "hedge", "sign": "sign_board"}


def site_slot(el):
    """Material slot of a site element: its "slots" {part keyword: slot} for multi-part elements (keyword found in the
    part name, e.g. Canopy_Roof), explicit "slot", else its surface, else its material, else its type."""
    for key, slot in (el.get("slots") or {}).items():
        if key.lower() in str(el.get("name", "")).lower():
            return slot
    if el.get("slot"):
        return el["slot"]
    srf = str(el.get("surface", "")).lower()
    for key, slot in SURFACE_SLOT:
        if key in srf:
            return slot
    if el.get("material") in MATERIAL_SLOT:
        return MATERIAL_SLOT[el["material"]]
    return TYPE_SLOT.get(el.get("type"), "M_Concrete")


def rot2(deg):
    a = math.radians(deg)
    return Vector((math.cos(a), math.sin(a))), Vector((-math.sin(a), math.cos(a)))


class Site:
    def __init__(self, spec, ter):
        self.s = spec
        self.id = spec["id"]
        self.gen = "site:" + self.id
        self.ter = ter
        self.col = ensure_collection(spec.get("collection", "03_Site"))
        self.names = set()
        # opt-in ("ground": "pads"): gz follows the terrain_pads of all specs like TER_Ground does
        self.pads = _all_pads() if spec.get("ground") == "pads" else None

    def gz(self, x, y):
        """Ground z: terrain base, minus the curb reveal on carriageways (+ terrain pads if the spec opts in)."""
        z = float(self.ter.base(x, y))
        if self.ter.carriageway_mask(x, y):
            z -= self.ter.curb
        if self.pads:
            z = _pad_z(self.pads, x, y, z)
        return z

    def name(self, el):
        base = re.sub(r"[^A-Za-z0-9_]", "_", el.get("name") or el["type"])
        n, k = base, 2
        while n in self.names:
            n, k = f"{base}_{k}", k + 1
        self.names.add(n)
        return f"GBS_{self.id.replace('SITE_', '')}_{n}"

    def emit(self, el, bm, color, origin):
        if el.get("confidence") == "low":
            color = COL["low"]
        it = {"id": el.get("name", el["type"]), "status": el.get("confidence", ""),
              "evidence": [el.get("evidence", "")] if el.get("evidence") else []}
        ob = make_object(self.name(el), bm, self.col, origin, it, color, gen=self.gen)
        ob["koch_confidence"] = el.get("confidence", "")
        # P2 material slot (handoff 4a): one M_<Material>_<Finish> slot instead of the plain review colour; the
        # object colour keeps the confidence flag (orange = low)
        # generic props are placeholders that UE swaps for Fab/Megascans assets (handoff 4a "Leave to Unreal")
        ue = el.get("ue_asset") or TYPE_UE.get(el.get("type"))
        if ue:
            ob["koch_ue_asset"] = ue if ue != "tree" else f"tree_{el.get('shape', 'cone')}"
        me = ob.data
        if len(me.materials) == 1 and me.materials[0] and me.materials[0].name.startswith("VC_"):
            me.materials[0] = mat(site_slot(el))
            ob["koch_slot"] = me.materials[0].name
        return ob

    # ------------------------------------------------------------------ element builders
    def b_fence(self, el):
        pts = el["line"]
        h, sp, post = el.get("height", 2.0), el.get("post_spacing", 2.5), el.get("post", 0.06)
        gap, panel = el.get("bottom_gap", 0.05), el.get("panel", "mesh")
        bm = bmesh.new()
        first = True
        for a, b in zip(pts[:-1], pts[1:]):
            A, B = Vector(a), Vector(b)
            L = (B - A).length
            if L < 1e-3:
                continue
            d = (B - A) / L
            n = max(1, round(L / sp))
            m = _frame2(A, d)
            for k in range(0 if first else 1, n + 1):  # joint post only once (a second one would z-fight in it)
                p = A + d * (L * k / n)
                z = self.gz(p.x, p.y)
                box(bm, m, L * k / n - post / 2, L * k / n + post / 2, -post / 2, post / 2, z - BURY, z + h)
            first = False
            for k in range(n):
                u0, u1 = L * k / n + post / 2, L * (k + 1) / n - post / 2
                pm = A + d * ((u0 + u1) / 2)
                z = self.gz(pm.x, pm.y)
                if panel == "bars":
                    nb = max(2, int((u1 - u0) / 0.12))
                    for j in range(nb):
                        uc = u0 + (u1 - u0) * (j + 0.5) / nb
                        box(bm, m, uc - 0.01, uc + 0.01, -0.01, 0.01, z + gap, z + h - 0.05)
                    for zr in (z + gap + 0.05, z + h - 0.1):
                        box(bm, m, u0, u1, -0.02, 0.02, zr - 0.02, zr + 0.02)
                else:  # welded mesh panel as a thin plate with a frame
                    box(bm, m, u0, u1, -0.01, 0.01, z + gap, z + h - 0.05)
        self.emit(el, bm, COL["metal"], (pts[0][0], pts[0][1], self.gz(*pts[0])))

    def b_wall(self, el):
        if el.get("kind") == "scalloped_edging":
            return self.b_scalloped_edging(el)
        if self._painted(el, el["line"], el.get("closed", False),
                         rect_profile(el.get("thk", 0.3), el["height"], el.get("bury", BURY)), COL["stone"]):
            return
        bm = bmesh.new()
        cap = el.get("cap_proj", 0.0)
        # "bury": depth below the ground line (retaining walls reaching down to a lower terrace level)
        kw = _sweep_kw(el)
        sweep_profile(bm, el["line"], rect_profile(el.get("thk", 0.3), el["height"], el.get("bury", BURY)), self.gz,
                      el.get("closed", False), **kw)
        if cap > 0:
            sweep_profile(bm, el["line"], [(el["thk"] / 2 + cap, el["height"]), (el["thk"] / 2 + cap, el["height"] + 0.06),
                                           (-el["thk"] / 2 - cap, el["height"] + 0.06), (-el["thk"] / 2 - cap, el["height"])],
                          self.gz, el.get("closed", False), **kw)
        p = el["line"][0]
        self.emit(el, bm, COL.get(el.get("material", "stone"), COL["stone"]), (p[0], p[1], self.gz(*p)))

    def b_scalloped_edging(self, el):
        """Precast garden edging as separate round-topped blocks (owner footage 081856511, 081924271: ~0.2 m pitch,
        ~0.22 m high, ~0.1 m thick, ~1 cm joints). Each block: rectangle + semicircle top, sat on the ground under
        its own centre, so the row follows the paving levels. `pitch`, `joint`, `height`, `thk` in metres."""
        bm = bmesh.new()
        pitch, joint = el.get("pitch", 0.20), el.get("joint", 0.01)
        h, thk, segs = el["height"], el.get("thk", 0.1), 8
        pts = el["line"] + ([el["line"][0]] if el.get("closed") else [])
        for a, b in zip(pts[:-1], pts[1:]):
            A, B = Vector(a), Vector(b)
            L = (B - A).length
            if L < pitch * 0.5:
                continue
            d = (B - A) / L
            m = _frame2(A, d)
            n = max(1, round(L / pitch))
            pe = L / n
            r = max(0.02, (pe - joint) / 2)
            for k in range(n):
                uc = pe * (k + 0.5)
                c = A + d * uc
                z = self.gz(c.x, c.y)
                zs = z + max(h - r, 0.02)
                prof = [(uc - r, z - BURY), (uc + r, z - BURY), (uc + r, zs)]
                prof += [(uc + r * math.cos(math.pi * i / segs), zs + r * math.sin(math.pi * i / segs))
                         for i in range(1, segs)]
                prof.append((uc - r, zs))
                sides = []
                for w in (-thk / 2, thk / 2):
                    sides.append([bm.verts.new((m @ Vector((u, w, 0.0))).xy.to_3d() + Vector((0, 0, zz)))
                                  for u, zz in prof])
                fr, bk = sides
                bm.faces.new(fr)
                bm.faces.new(list(reversed(bk)))
                for i in range(len(prof)):
                    j = (i + 1) % len(prof)
                    bm.faces.new((fr[j], fr[i], bk[i], bk[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        p = el["line"][0]
        self.emit(el, bm, COL.get(el.get("material", "stone"), COL["stone"]), (p[0], p[1], self.gz(*p)))

    def b_pergola(self, el):
        """Steel pergola over a walk (SITE_Garden south walk, owner clip 081904575 t5-t9): pointed arches of thin
        maroon tube every `pitch` m, straight legs to `post_h`, apex at `apex_h`, three longitudinal ties (apex and
        both shoulders). The legs stand at the walk edges (`width` apart); sizes in metres."""
        bm = bmesh.new()
        A, B = Vector(el["line"][0]), Vector(el["line"][1])
        L = (B - A).length
        d = (B - A) / L
        m = _frame2(A, d)
        W, pitch, ph, ah = el["width"], el.get("pitch", 2.5), el.get("post_h", 2.2), el.get("apex_h", 2.9)
        tube, seg = el.get("tube", 0.05), 10
        n = max(1, round(L / pitch))

        def rod(p0, p1):
            v = p1 - p0
            ln = v.length
            if ln < 1e-4:
                return
            u = v / ln
            s = u.cross(Vector((0, 0, 1)))
            s = (s if s.length > 1e-6 else Vector((1, 0, 0))).normalized() * (tube / 2)
            w = u.cross(s).normalized() * (tube / 2)
            ring0 = [bm.verts.new(p0 + a * s + b * w) for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
            ring1 = [bm.verts.new(p1 + a * s + b * w) for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
            _close_loops(bm, [ring0, ring1])

        def world(u, w, z):
            q = m @ Vector((u, w, 0.0))
            return Vector((q.x, q.y, z))
        gaps = [(Vector(g[:2]), g[2]) for g in el.get("gaps", [])]   # [x, y, r]: no arch there (e.g. a hedge arch)
        tops = []
        for k in range(n + 1):
            u = L * k / n
            c = A + d * u
            if any(min((c + d * (s * W / 2) - p).length for s in (0,)) < r or
                   min((c + Vector((-d.y, d.x)) * s * W / 2 - p).length for s in (1, -1)) < r for p, r in gaps):
                tops.append(None)
                continue
            z = self.gz(c.x, c.y)
            pts = []
            for side in (1, -1):
                half = [world(u, side * W / 2, z - 0.1), world(u, side * W / 2, z + ph)]
                for i in range(1, seg + 1):
                    f = i / seg
                    half.append(world(u, side * W / 2 * (1 - f), z + ph + (ah - ph) * math.sin(f * math.pi / 2)))
                for p0, p1 in zip(half[:-1], half[1:]):
                    rod(p0, p1)
                pts.append(half)
            tops.append((world(u, 0, z + ah), world(u, W / 2, z + ph), world(u, -W / 2, z + ph)))
        for t0, t1 in zip(tops[:-1], tops[1:]):
            if t0 is None or t1 is None:
                continue
            for i in range(3):
                rod(t0[i], t1[i])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self.emit(el, bm, COL["metal"], (A.x, A.y, self.gz(A.x, A.y)))

    def b_barrier(self, el):
        """Invisible map-limit wall (SITE_Barriers): a closed/open polyline swept `thk` wide from 2 m below the ground
        to `height` above it. Never rendered (wire in the viewport); UE converts it to a Blocking Volume."""
        bm = bmesh.new()
        h, t = el.get("height", 40.0), el.get("thk", 0.3)
        sweep_profile(bm, el["line"], rect_profile(t, h, 2.0), self.gz, el.get("closed", False), **_sweep_kw(el, 5.0))
        p = el["line"][0]
        ob = self.emit(dict(el, ue_asset="blocking_volume", slot="M_Invisible"), bm, COL["accent"], (p[0], p[1], self.gz(*p)))
        ob.hide_render = True
        ob.display_type = "WIRE"
        ob["koch_collision_only"] = True

    def b_hedge(self, el):
        bm = bmesh.new()
        rt = el.get("top", "round") == "round"
        if "ring" in el:
            ring = _ccw(el["ring"])
            h = el["height"]
            inset = 0.12 if rt else 0.0
            lo = [bm.verts.new((x, y, self.gz(x, y) - BURY)) for x, y in ring]
            mid = [bm.verts.new((x, y, self.gz(x, y) + h - inset)) for x, y in ring]
            loops = [lo, mid]
            if rt:
                inner = _offset(ring, inset)
                loops.append([bm.verts.new((x, y, self.gz(x, y) + h)) for x, y in inner])
            n = len(ring)
            for A, B in zip(loops[:-1], loops[1:]):
                for i in range(n):
                    j = (i + 1) % n
                    bm.faces.new((A[i], A[j], B[j], B[i]))
            bm.faces.new(list(reversed(lo)))
            bm.faces.new(loops[-1])
            p = ring[0]
        else:
            sweep_profile(bm, el["line"], hedge_profile(el["width"], el["height"], rt, BURY), self.gz, el.get("closed", False),
                          **_sweep_kw(el))
            p = el["line"][0]
        self.emit(el, bm, COL["hedge"], (p[0], p[1], self.gz(*p)))

    def b_hedge_arch(self, el):
        c = Vector(el["center"])
        fwd, left = rot2(el.get("dir_deg", 0.0))
        s, h, t, dep = el["span"], el["height"], el.get("thk", 0.6), el.get("depth", 1.0)
        r_in = s / 2
        zs = h - r_in                                    # springing height of the semicircle (clear height = h)
        prof = [(-(r_in + t), -BURY), (-(r_in + t), zs)]
        for k in range(1, 12):
            a = math.pi - math.pi * k / 12
            prof.append(((r_in + t) * math.cos(a), zs + (r_in + t) * math.sin(a)))
        prof += [(r_in + t, zs), (r_in + t, -BURY), (r_in, -BURY), (r_in, zs)]
        for k in range(1, 12):
            a = math.pi * k / 12
            prof.append((r_in * math.cos(a), zs + r_in * math.sin(a)))
        prof += [(-r_in, zs), (-r_in, -BURY)]
        z0 = self.gz(c.x, c.y)
        bm = bmesh.new()
        m = Matrix.Identity(4)
        m.col[0].xyz, m.col[1].xyz, m.col[2].xyz = left.to_3d(), fwd.to_3d(), Vector((0, 0, 1))
        m.col[3].xyz = Vector((c.x, c.y, z0))
        a_ = [bm.verts.new(m @ Vector((x, -dep / 2, z))) for x, z in prof]
        b_ = [bm.verts.new(m @ Vector((x, dep / 2, z))) for x, z in prof]
        n = len(prof)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a_[i], a_[j], b_[j], b_[i]))
        bm.faces.new(list(reversed(a_)))
        bm.faces.new(b_)
        self.emit(el, bm, COL["hedge"], (c.x, c.y, z0))

    def b_gazebo(self, el):
        """Octagonal garden gazebo (SITE_Garden Gazebo_1/2): floor, white posts + ring beam, red brick-tile parapet
        with the timber bench inside, white fascia with the dark triangular shingle tabs (owner frames 081924271 t1-t18,
        081946180), shingle pyramid roof. `eave_h`: fascia bottom above the floor (m); parts get their own slots."""
        c = Vector(el["center"])
        N = int(el.get("sides", 8))
        R = el["across_flats"] / 2 / math.cos(math.pi / N)
        rot = math.radians(el.get("rot_deg", 0.0))
        z0 = self.gz(c.x, c.y)
        fh, ph, pw = el.get("floor_h", 0.15), el.get("post_h", 2.4), el.get("post_w", 0.25)
        par_h, par_t = el.get("parapet_h", 0.8), el.get("parapet_t", 0.25)
        open_sides = set(el.get("open_sides", []))
        el = dict(el, slots={"_Floor": "M_Paving_Diamond_Tile", "_Parapet": "M_Tile_Brick_Red", "_BenchLegs": "M_Steel_Paint_Dark", "_Bench": "M_Wood_Stained",
                             "_Frame": "M_Paint_White", "_Posts": "M_Render_White", "_Capitals": "M_Paint_Brown", "_Ceiling": "M_Wood_Stained", "_Downlights": "M_Lamp_Diffuser", "_Sign": "M_Sign_Panel", "_FasciaTabs": "M_Shingle_Brown", "_Fascia": "M_Paint_White",
                             "_Roof": "M_Shingle_Brown", **(el.get("slots") or {})})

        def poly(r, z, extra=0.0):
            return [Vector((c.x + r * math.cos(rot + math.pi / N + 2 * math.pi * k / N + extra),
                            c.y + r * math.sin(rot + math.pi / N + 2 * math.pi * k / N + extra), z)) for k in range(N)]
        nm = el.get("name", "Gazebo")
        bm = bmesh.new()   # floor platform
        lo, hi = [bm.verts.new(v) for v in poly(R + 0.1, z0 - BURY)], [bm.verts.new(v) for v in poly(R + 0.1, z0 + fh)]
        _close_loops(bm, [lo, hi])
        self.emit(dict(el, name=nm + "_Floor"), bm, COL["stone"], (c.x, c.y, z0))
        corners = poly(R, 0)
        zf = z0 + fh
        cw = el.get("opening_clear_w")      # clear opening in an open side (the rest is parapet stubs)
        bm, bb, bl = bmesh.new(), bmesh.new(), bmesh.new()   # parapet, bench seat, bench legs
        for k in range(N):
            a, b = corners[k], corners[(k + 1) % N]
            A, B = Vector((a.x, a.y)), Vector((b.x, b.y))
            d = (B - A).normalized()
            L = (B - A).length
            m = _frame2(A, d)
            if k in open_sides:
                if not cw:
                    continue
                g0, g1 = (L - cw) / 2, (L + cw) / 2   # centred gap
                box(bm, m, pw / 2, g0, -par_t / 2, par_t / 2, zf, zf + par_h)
                box(bm, m, g1, L - pw / 2, -par_t / 2, par_t / 2, zf, zf + par_h)
            else:
                box(bm, m, pw / 2, L - pw / 2, -par_t / 2, par_t / 2, zf, zf + par_h)
                # timber bench inside the parapet (seat 0.45 m, 0.4 m deep); w+ is toward the centre
                box(bb, m, pw / 2 + 0.05, L - pw / 2 - 0.05, par_t / 2 + 0.01, par_t / 2 + 0.41, zf + 0.40, zf + 0.45)
                # steel legs under the seat (INV.GDN.2: polygonal timber bench on steel legs), ~1.2 m apart
                nl = max(2, round((L - pw - 0.1) / 1.2) + 1)
                for j in range(nl):
                    ul = pw / 2 + 0.12 + (L - pw - 0.24) * j / (nl - 1)
                    box(bl, m, ul - 0.02, ul + 0.02, par_t / 2 + 0.3, par_t / 2 + 0.34, zf, zf + 0.40)
        self.emit(dict(el, name=nm + "_Parapet"), bm, COL["brick"], (c.x, c.y, z0))
        self.emit(dict(el, name=nm + "_Bench"), bb, COL["wood"], (c.x, c.y, z0))
        self.emit(dict(el, name=nm + "_BenchLegs"), bl, COL["metal"], (c.x, c.y, z0))
        bm = bmesh.new()   # posts + ring beam + centre column
        for k in range(N):
            p = corners[k]
            m = _frame2(Vector((p.x, p.y)), (Vector((c.x, c.y)) - Vector((p.x, p.y))).normalized())
            box(bm, m, -pw / 2, pw / 2, -pw / 2, pw / 2, zf, zf + ph)
        cc = el.get("center_column")
        if cc:
            _cyl(bm, Vector((c.x, c.y)), cc.get("d", 0.2) / 2, zf, zf + ph, 12)
        self.emit(dict(el, name=nm + "_Posts"), bm, COL["white"], (c.x, c.y, z0))
        bm = bmesh.new()   # dark-brown capital band at the post tops (spec notes: ~0.12 m), 1 cm proud of the post
        cap = el.get("capital_h", 0.12)
        for k in range(N):
            p = corners[k]
            m = _frame2(Vector((p.x, p.y)), (Vector((c.x, c.y)) - Vector((p.x, p.y))).normalized())
            box(bm, m, -pw / 2 - 0.01, pw / 2 + 0.01, -pw / 2 - 0.01, pw / 2 + 0.01, zf + ph - cap, zf + ph - 0.003)
        self.emit(dict(el, name=nm + "_Capitals"), bm, COL["wood"], (c.x, c.y, z0))
        bm = bmesh.new()   # ring beam
        zt = zf + el["eave_h"] if el.get("eave_h") else zf + ph + 0.22     # fascia bottom
        rb = max(0.05, zt - (zf + ph))
        _ring_band(bm, poly(R + pw / 2 + 0.02, 0), poly(R - pw / 2 - 0.02, 0), zf + ph, zf + ph + rb)
        self.emit(dict(el, name=nm + "_Frame"), bm, COL["white"], (c.x, c.y, z0))
        ro = (el["roof_across_flats"] / 2 / math.cos(math.pi / N)) if el.get("roof_across_flats") else R + el.get("overhang", 0.4)
        fas = el.get("fascia_h", 0.15)
        bm = bmesh.new()   # white fascia band (a ring, so it never overlaps the roof soffit)
        _ring_band(bm, poly(ro, 0), poly(ro - 0.03, 0), zt, zt + fas)
        self.emit(dict(el, name=nm + "_Fascia"), bm, COL["white"], (c.x, c.y, z0))
        bm = bmesh.new()   # flat slatted timber ceiling on the ring beam (pano: ceiling = post-top level)
        _close_loops(bm, [[bm.verts.new(v) for v in poly(ro - 0.031, zt)],
                          [bm.verts.new(v) for v in poly(ro - 0.031, zt + 0.02)]])
        self.emit(dict(el, name=nm + "_Ceiling"), bm, COL["wood"], (c.x, c.y, z0))
        bm = bmesh.new()   # 2 round recessed downlights in the soffit (INV.GDN.1, 082013462)
        for s in (-1, 1):
            _cyl(bm, Vector((c.x + s * 0.9 * math.cos(rot), c.y + s * 0.9 * math.sin(rot))), 0.09, zt - 0.012, zt - 0.002, 12)
        self.emit(dict(el, name=nm + "_Downlights"), bm, COL["white"], (c.x, c.y, z0))
        sp = el.get("sign_post")   # small blank sign plate on one post (INV.GDN.3; the text is a UE decal)
        if sp is not None:
            p = corners[int(sp)]
            m = _frame2(Vector((p.x, p.y)), (Vector((c.x, c.y)) - Vector((p.x, p.y))).normalized())
            bs = bmesh.new()
            box(bs, m, -pw / 2 - 0.012, -pw / 2 - 0.002, -0.1, 0.1, zf + 1.45, zf + 1.75)
            self.emit(dict(el, name=nm + "_Sign", ue_asset="sign_plate"), bs, COL["white"], (c.x, c.y, z0))
        bm = bmesh.new()   # shingle tabs: dark triangles over the fascia, points down (~0.3 m pitch, ~0.12 m deep)
        tp, td, tt = el.get("tab_pitch", 0.3), min(el.get("tab_depth", 0.12), fas), 0.012
        cr = poly(ro, 0)
        for k in range(N):
            A, B = Vector((cr[k].x, cr[k].y)), Vector((cr[(k + 1) % N].x, cr[(k + 1) % N].y))
            L = (B - A).length
            d = (B - A) / L
            m = _frame2(A, d)                  # w+ = left of d = toward the centre for this CCW ring
            n = max(1, round(L / tp))
            for j in range(n):
                u0, u1 = L * j / n, L * (j + 1) / n
                tri = [(u0, zt + fas), (u1, zt + fas), ((u0 + u1) / 2, zt + fas - td)]
                fr = [bm.verts.new(m @ Vector((u, -0.01 - tt, 0.0)) + Vector((0, 0, z))) for u, z in tri]
                bk = [bm.verts.new(m @ Vector((u, -0.01, 0.0)) + Vector((0, 0, z))) for u, z in tri]
                bm.faces.new(fr)
                bm.faces.new(list(reversed(bk)))
                for i in range(3):
                    bm.faces.new((fr[(i + 1) % 3], fr[i], bk[i], bk[(i + 1) % 3]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self.emit(dict(el, name=nm + "_FasciaTabs"), bm, COL["roof"], (c.x, c.y, z0))
        bm = bmesh.new()   # pyramid roof above the fascia
        zr = zt + fas
        apo = ro * math.cos(math.pi / N)
        apex = Vector((c.x, c.y, zr + apo * math.tan(math.radians(el.get("roof_pitch", 30)))))
        rim = [bm.verts.new(v) for v in poly(ro, zr)]
        av = bm.verts.new(apex)
        for k in range(N):
            bm.faces.new((rim[k], rim[(k + 1) % N], av))
        bm.faces.new(list(reversed(rim)))     # flat soffit/ceiling under the roof
        self.emit(dict(el, name=nm + "_Roof"), bm, COL["roof"], (c.x, c.y, z0))

    def b_canopy(self, el):
        o = [Vector(p) for p in el["outline"]]
        e01, e12 = (o[1] - o[0]).length, (o[2] - o[1]).length
        long_first = e01 >= e12
        if el.get("ridge", "long") == "short":
            long_first = not long_first
        a, b, c_, d = (o[0], o[1], o[2], o[3]) if long_first else (o[1], o[2], o[3], o[0])
        ax = (b - a).normalized()
        L = (b - a).length
        W = (d - a).length
        acr = (d - a).normalized()
        cen = (a + b + c_ + d) / 4
        zc = self.gz(cen.x, cen.y) + el["z_underside"]
        pitch = math.radians(el.get("pitch", 0.0))
        thk = el.get("thk", 0.2)
        hr = (W / 2) * math.tan(pitch)
        prof = [(-W / 2, 0.0), (0.0, hr), (W / 2, 0.0), (W / 2, thk), (0.0, hr + thk), (-W / 2, thk)] if pitch > 0 else \
               [(-W / 2, 0.0), (W / 2, 0.0), (W / 2, thk), (-W / 2, thk)]
        if pitch > 0 and el.get("soffit") == "flat":  # boarded horizontal soffit under the gable (gate canopy)
            prof = [(-W / 2, 0.0), (W / 2, 0.0), (W / 2, thk), (0.0, hr + thk), (-W / 2, thk)]
        m = Matrix.Identity(4)
        m.col[0].xyz, m.col[1].xyz, m.col[2].xyz = ax.to_3d(), acr.to_3d(), Vector((0, 0, 1))
        m.col[3].xyz = Vector((cen.x, cen.y, zc))
        bm = bmesh.new()
        A = [bm.verts.new(m @ Vector((-L / 2, y, z))) for y, z in prof]
        B = [bm.verts.new(m @ Vector((L / 2, y, z))) for y, z in prof]
        n = len(prof)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((A[i], A[j], B[j], B[i]))
        bm.faces.new(list(reversed(A)))
        bm.faces.new(B)
        self.emit(dict(el, name=el.get("name", "Canopy") + "_Roof"), bm, COL["roof"], (cen.x, cen.y, zc))
        bm = bmesh.new()
        r = el.get("post_d", 0.3) / 2
        for p in el.get("posts", []):
            P = Vector(p)
            across = (P - cen).dot(acr)
            z_top = zc + (hr * (1 - min(1.0, abs(across) / (W / 2))) if pitch > 0 and el.get("soffit") != "flat" else 0.0)
            zb = self.gz(P.x, P.y) - BURY
            if el.get("post_shape", "round") == "round":
                _cyl(bm, P, r, zb, z_top, 12)
            else:
                box(bm, _frame2(P, ax), -r, r, -r, r, zb, z_top)
        self.emit(dict(el, name=el.get("name", "Canopy") + "_Posts"), bm, COL.get(el.get("post_material", "metal"), COL["metal"]),
                  (cen.x, cen.y, zc))
        pb = el.get("post_base")  # coloured plinth ring at the column foot: {"h": m, "material": COL key}
        if pb and el.get("posts"):
            bm = bmesh.new()
            for p in el["posts"]:
                P = Vector(p)
                _cyl(bm, P, r + 0.01, self.gz(P.x, P.y) - BURY, self.gz(P.x, P.y) + pb["h"], 12)
            self.emit(dict(el, name=el.get("name", "Canopy") + "_PostBase"), bm, COL.get(pb.get("material", "brick")),
                      (cen.x, cen.y, zc))
        tr = el.get("trim")  # sawtooth fascia trim along both long eaves: {"h": tooth height, "pitch": m, "t": m}
        if tr:
            bm = bmesh.new()
            th, tp, tt = tr.get("h", 0.2), tr.get("pitch", 0.35), tr.get("t", 0.02)
            n = max(1, int(L / tp))
            for side in (-1.0, 1.0):
                y0 = side * (W / 2 + 0.005)
                y1 = y0 + side * tt
                for k in range(n):
                    u0 = -L / 2 + (L - n * tp) / 2 + k * tp
                    tri = [(u0, 0.02), (u0 + tp, 0.02), (u0 + tp / 2, 0.02 + th)]
                    va = [bm.verts.new(m @ Vector((u, y0, z))) for u, z in tri]
                    vb = [bm.verts.new(m @ Vector((u, y1, z))) for u, z in tri]
                    if side < 0:
                        va, vb = vb, va
                    bm.faces.new(va)
                    bm.faces.new(list(reversed(vb)))
                    for i in range(3):
                        j = (i + 1) % 3
                        bm.faces.new((va[j], va[i], vb[i], vb[j]))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            self.emit(dict(el, name=el.get("name", "Canopy") + "_Trim"), bm, COL["white"], (cen.x, cen.y, zc))

    def b_turnstile(self, el):
        P = Vector(el["pos"])
        fwd, left = rot2(el.get("dir_deg", 0.0))
        cnt, pw, hh, hw = int(el.get("count", 2)), el.get("passage_w", 0.55), el.get("height", 1.0), el.get("housing_w", 0.3)
        length = el.get("housing_l", 0.8)
        z = self.gz(P.x, P.y)
        total = cnt * pw + (cnt + 1) * hw
        m = _frame2(P, fwd)          # u along the walking direction, w to the left
        bm = bmesh.new()
        w = -total / 2
        for k in range(cnt + 1):
            box(bm, m, -length / 2, length / 2, w, w + hw, z, z + hh)
            if k < cnt:  # one tripod arm across the passage at 0.9 m
                box(bm, m, -0.02, 0.02, w + hw, w + hw + pw, z + 0.88, z + 0.92)
            w += hw + pw
        self.emit(el, bm, COL["metal"], (P.x, P.y, z))

    def b_gate_leaf(self, el):
        self.b_fence(dict(el, panel=el.get("panel", "bars"), post_spacing=1e9, post=0.08))

    def b_bench(self, el):
        P = Vector(el["pos"])
        fwd, left = rot2(el.get("dir_deg", 0.0))
        L, D, sh, bh = el.get("length", 1.8), el.get("depth", 0.45), el.get("seat_h", 0.45), el.get("back_h", 0.85)
        z = el["z"] if "z" in el else self.gz(P.x, P.y)  # explicit z: indoor benches stand on a floor slab
        m = _frame2(P, left)         # u along the bench, w = forward (facing)
        bm = bmesh.new()
        box(bm, m, -L / 2, L / 2, -D / 2, D / 2, z + sh - 0.05, z + sh)                 # seat
        if el.get("back", True):  # corridor benches in C have no backrest
            box(bm, m, -L / 2, L / 2, -D / 2 - 0.04, -D / 2, z + sh + 0.1, z + bh)      # back
        for u in (-L / 2 + 0.1, L / 2 - 0.1):                                          # legs / side frames
            box(bm, m, u - 0.03, u + 0.03, -D / 2, D / 2, z, z + sh - 0.05)
        self.emit(el, bm, COL["wood"], (P.x, P.y, z))

    def b_lamp(self, el):
        P = Vector(el["pos"])
        z = self.gz(P.x, P.y)
        h = el.get("height", 3.5)
        bm = bmesh.new()
        _cyl(bm, P, el.get("pole_r", 0.05), z - BURY, z + h, 10)
        if el.get("head", "ball") == "ball":
            bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=0.18,
                                      matrix=Matrix.Translation((P.x, P.y, z + h + 0.16)))
        else:
            box(bm, Matrix.Translation((P.x, P.y, 0)), -0.15, 0.15, -0.15, 0.15, z + h, z + h + 0.35)
        self.emit(el, bm, COL["metal"], (P.x, P.y, z))

    def b_bin(self, el):
        P = Vector(el["pos"])
        z = self.gz(P.x, P.y)
        s = el.get("size", [0.6, 0.6, 1.0])
        bm = bmesh.new()
        box(bm, _frame2(P, rot2(el.get("dir_deg", 0.0))[0]), -s[0] / 2, s[0] / 2, -s[1] / 2, s[1] / 2, z, z + s[2])
        self.emit(el, bm, (0.85, 0.75, 0.15, 1), (P.x, P.y, z))

    def b_bike_rack(self, el):
        A, B = Vector(el["line"][0]), Vector(el["line"][-1])
        n = int(el.get("count", 5))
        d = (B - A).normalized()
        bm = bmesh.new()
        for k in range(n):
            P = A + (B - A) * ((k + 0.5) / n)
            z = self.gz(P.x, P.y)
            m = _frame2(P, Vector((-d.y, d.x)))   # hoop plane perpendicular to the rack line
            for u in (-0.35, 0.35):
                box(bm, m, u - 0.02, u + 0.02, -0.02, 0.02, z - 0.1, z + 0.75)
            box(bm, m, -0.37, 0.37, -0.02, 0.02, z + 0.71, z + 0.75)
        self.emit(el, bm, COL["metal"], (A.x, A.y, self.gz(A.x, A.y)))

    def b_steps(self, el):
        P = Vector(el["pos"])
        fwd, left = rot2(el.get("dir_deg", 0.0))
        n, rh, tr, W = int(el["risers"]), el["riser_h"], el["tread"], el["width"]
        z0 = self.gz(P.x, P.y)
        prof = [(0.0, -BURY)]
        for k in range(n):
            prof += [(k * tr, (k + 1) * rh), ((k + 1) * tr if k < n - 1 else k * tr + el.get("top_landing", tr), (k + 1) * rh)]
        prof += [(prof[-1][0], -BURY)]
        m = Matrix.Identity(4)
        m.col[0].xyz, m.col[1].xyz, m.col[2].xyz = left.to_3d(), fwd.to_3d(), Vector((0, 0, 1))
        m.col[3].xyz = Vector((P.x, P.y, z0))
        bm = bmesh.new()
        A = [bm.verts.new(m @ Vector((-W / 2, y, z))) for y, z in prof]
        B = [bm.verts.new(m @ Vector((W / 2, y, z))) for y, z in prof]
        k = len(prof)
        for i in range(k):
            j = (i + 1) % k
            bm.faces.new((A[i], A[j], B[j], B[i]))
        bm.faces.new(list(reversed(A)))
        bm.faces.new(B)
        self.emit(el, bm, COL["stone"], (P.x, P.y, z0))

    def _painted(self, el, pts, closed, profile, color):
        """Curb swept in painted pieces (el["paint"] = [[slot, length m], ...] cycled along the line, e.g. the campus'
        yellow 1.0 / white 0.5 kerbs): one object per slot, <name>_<Slot> (owner frames 070410255 t20-t44,
        070541257). Returns False when the element has no paint pattern."""
        pat = el.get("paint")
        if not pat:
            return False
        P = [Vector(p) for p in pts] + ([Vector(pts[0])] if closed else [])
        seg = [(P[i], P[i + 1]) for i in range(len(P) - 1) if (P[i + 1] - P[i]).length > 1e-6]
        pieces, cur, k, left = [], [seg[0][0]], 0, pat[0][1]
        for A, B in seg:
            L, s = (B - A).length, 0.0
            while L - s > left + 1e-6:
                s += left
                q = A + (B - A) * (s / L)
                cur.append(q)
                pieces.append((pat[k % len(pat)][0], cur))
                k += 1
                cur, left = [q], pat[k % len(pat)][1]
            left -= L - s
            cur.append(B)
        if len(cur) > 1:
            pieces.append((pat[k % len(pat)][0], cur))
        by = {}
        for slot, pl in pieces:
            bm = by.setdefault(slot, bmesh.new())
            sweep_profile(bm, [(v.x, v.y) for v in pl], profile, self.gz, False, max_seg=1.0)
        p = pts[0]
        for slot, bm in by.items():
            self.emit(dict(el, name=el.get("name", el["type"]) + "_" + slot.replace("M_", "").replace("_", ""),
                           slot=slot), bm, color, (p[0], p[1], self.gz(*p)))
        return True

    def b_planter(self, el):
        w, h = el.get("curb_w", 0.08), el.get("curb_h", 0.15)
        if self._painted(el, _ccw(el["ring"]), True, [(0.0, -BURY), (0.0, h), (w, h), (w, -BURY)][::-1],
                         (0.70, 0.25, 0.20, 1)):
            return
        bm = bmesh.new()
        sweep_profile(bm, _ccw(el["ring"]), [(0.0, -BURY), (0.0, h), (w, h), (w, -BURY)][::-1], self.gz, closed=True,
                      **_sweep_kw(el, 1.0))   # subdivided every 1 m: long curbs follow the pads, not a chord
        p = el["ring"][0]
        self.emit(el, bm, (0.70, 0.25, 0.20, 1), (p[0], p[1], self.gz(*p)))

    def b_sign(self, el):
        P = Vector(el["pos"])
        z = self.gz(P.x, P.y) + el.get("z0", 0.0)
        bm = bmesh.new()
        m = _frame2(P, rot2(el.get("dir_deg", 0.0))[1])   # facing dir_deg: panel spans along the left axis
        box(bm, m, -el["w"] / 2, el["w"] / 2, -el.get("t", 0.1) / 2, el.get("t", 0.1) / 2, z, z + el["h"])
        self.emit(el, bm, (0.20, 0.25, 0.45, 1), (P.x, P.y, z))

    def b_path(self, el):
        """Paved path strip: thin slab following the ground (surface texture comes later in UE)."""
        bm = bmesh.new()
        w, t, top = el.get("width", 1.5), el.get("thk", 0.08), el.get("top", 0.02)
        # "top": 2 cm above the terrain by default; a joining path gets a few mm less so the two tops never coincide
        # top 2 cm above the terrain so it reads over the heightfield; slab reaches t below it. Subdivided every
        # 0.5 m so it follows pad blends/edges instead of bridging them (terrain poking through or a floating strip)
        sweep_profile(bm, el["line"], [(w / 2, top - t), (w / 2, top), (-w / 2, top), (-w / 2, top - t)],
                      self.gz, el.get("closed", False), **_sweep_kw(el, 0.5))
        p = el["line"][0]
        self.emit(el, bm, COL["stone"], (p[0], p[1], self.gz(*p)))

    def b_tree(self, el):
        """Tree proxy: trunk cylinder + cone (conifer) or octahedral-ish ellipsoid crown. Real foliage comes in UE."""
        P = Vector(el["pos"])
        z = el["z"] if "z" in el else self.gz(P.x, P.y)   # explicit z: planted on a raised bed solid
        h, cd = el.get("height", 5.0), el.get("crown_d", 2.5)
        td = el.get("trunk_d", 0.25)
        cb = el.get("crown_base", h * 0.3)
        bm = bmesh.new()
        _cyl(bm, P, td / 2, z - BURY, z + cb + 0.2, 8)
        seg = 10
        if el.get("shape", "cone") == "cone":
            ring = [bm.verts.new((P.x + cd / 2 * math.cos(2 * math.pi * k / seg), P.y + cd / 2 * math.sin(2 * math.pi * k / seg), z + cb)) for k in range(seg)]
            apex = bm.verts.new((P.x, P.y, z + h))
            bm.faces.new(list(reversed(ring)))
            for k in range(seg):
                bm.faces.new((ring[k], ring[(k + 1) % seg], apex))
        else:
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0,
                                       matrix=Matrix.Translation((P.x, P.y, z + (cb + h) / 2)) @ Matrix.Diagonal((cd / 2, cd / 2, (h - cb) / 2, 1)))
        self.emit(el, bm, COL["hedge"], (P.x, P.y, z))

    # ------------------------------------------------------------------ interior / absolute-z elements
    def b_slab(self, el):
        """Horizontal slab over a world ring between absolute z0..z1 (floors, landings, ceilings)."""
        ring = _ccw(el["ring"])
        bm = bmesh.new()
        if el.get("holes"):  # cut-outs (inset fields/surfaces sit flush in them instead of overlapping the top)
            _slab_with_holes(bm, ring, [_ccw(h)[::-1] for h in el["holes"]], el["z0"], el["z1"])
        else:
            lo = [bm.verts.new((x, y, el["z0"])) for x, y in ring]
            hi = [bm.verts.new((x, y, el["z1"])) for x, y in ring]
            _close_loops(bm, [lo, hi])
        self.emit(el, bm, COL.get(el.get("material", "stone"), COL["stone"]), (ring[0][0], ring[0][1], el["z1"]))

    def b_roof_plane(self, el):
        """Planar sloped roof sheet: ring (4 world corners) with absolute z per corner, thickness thk (m)."""
        ring, zs, t = el["ring"], el["z"], el.get("thk", 0.12)
        bm = bmesh.new()
        lo = [bm.verts.new((x, y, z - t)) for (x, y), z in zip(ring, zs)]
        hi = [bm.verts.new((x, y, z)) for (x, y), z in zip(ring, zs)]
        _close_loops(bm, [lo, hi])
        self.emit(el, bm, COL.get(el.get("material", "roof"), COL["roof"]), (ring[0][0], ring[0][1], zs[0]))

    def b_int_wall(self, el):
        """Straight wall between two world points, absolute z0..z1, thickness to the LEFT of p0->p1 (w negative),
        openings [{u0,u1,z0,z1}] with u along p0->p1 (m) and z absolute."""
        A, Bp = Vector(el["line"][0]), Vector(el["line"][1])
        L = (Bp - A).length
        d = (Bp - A) / L
        m = Matrix.Identity(4)
        # facade frame: u along the wall, w = right-hand normal (outer face at w=0), z absolute
        m.col[0].xyz, m.col[1].xyz, m.col[2].xyz = d.to_3d(), Vector((d.y, -d.x, 0)), Vector((0, 0, 1))
        m.col[3].xyz = Vector((A.x, A.y, 0))
        ops = [Opening(o["u0"], o["u1"], o["z0"], o["z1"]) for o in el.get("openings", [])]
        bm = bmesh.new()
        wall_piece(bm, m, L, el["z0"], el["z1"], el.get("thk", 0.25), ops, cut_start=0.0, cut_end=0.0)
        self.emit(el, bm, COL.get(el.get("material", "white"), COL["white"]), (A.x, A.y, el["z0"]))

    def b_door(self, el):
        """Door set in a wall opening: frame (jambs + head), leaf (closed; UE swaps in a hinged actor), optional
        glass panels and a lever/pull handle. line = the host int_wall line, u0..u1 = frame outer width along it,
        z0..z1 absolute (frame outer), w_face = frame face offset (m, right-hand normal; host wall occupies -thk..0).
        leaf: "solid" | "glass" | "glass2" (two panes split by a mid rail at z0 + mid)."""
        A, Bp = Vector(el["line"][0]), Vector(el["line"][1])
        d = (Bp - A) / (Bp - A).length
        m = Matrix.Identity(4)
        m.col[0].xyz, m.col[1].xyz, m.col[2].xyz = d.to_3d(), Vector((d.y, -d.x, 0)), Vector((0, 0, 1))
        m.col[3].xyz = Vector((A.x, A.y, 0))
        u0, u1, z0, z1 = el["u0"], el["u1"], el["z0"], el["z1"]
        fw, fd = el.get("frame_w", 0.06), el.get("frame_d", 0.07)
        wf = el.get("w_face", -el.get("wall_thk", 0.2) / 2 + fd / 2)
        bm = bmesh.new()
        box(bm, m, u0, u0 + fw, wf - fd, wf, z0, z1)          # jambs + head
        box(bm, m, u1 - fw, u1, wf - fd, wf, z0, z1)
        box(bm, m, u0 + fw, u1 - fw, wf - fd, wf, z1 - fw, z1)
        self.emit({**el, "name": el.get("name", "Door") + "_Frame"}, bm, COL[el.get("material", "metal")], (A.x, A.y, z0))
        lu0, lu1, lz0, lz1 = u0 + fw + 0.004, u1 - fw - 0.004, z0 + 0.01, z1 - fw - 0.004
        lt, sw = el.get("leaf_t", 0.05), el.get("stile", 0.09)
        wl1 = wf - (fd - lt) / 2
        wl0 = wl1 - lt
        bl, bg = bmesh.new(), bmesh.new()
        kind = el.get("leaf", "solid")
        if kind == "solid":
            box(bl, m, lu0, lu1, wl0, wl1, lz0, lz1)
        else:  # stiles/rails + glass panes
            box(bl, m, lu0, lu0 + sw, wl0, wl1, lz0, lz1)
            box(bl, m, lu1 - sw, lu1, wl0, wl1, lz0, lz1)
            box(bl, m, lu0 + sw, lu1 - sw, wl0, wl1, lz1 - sw, lz1)
            box(bl, m, lu0 + sw, lu1 - sw, wl0, wl1, lz0, lz0 + el.get("bottom_rail", 0.12))
            zs = [lz0 + el.get("bottom_rail", 0.12), lz1 - sw]
            if kind == "glass2":
                zm = z0 + el.get("mid", 1.0)
                box(bl, m, lu0 + sw, lu1 - sw, wl0, wl1, zm - sw / 2, zm + sw / 2)
                panes = [(zs[0], zm - sw / 2), (zm + sw / 2, zs[1])]
            else:
                panes = [tuple(zs)]
            gm = (wl0 + wl1) / 2
            for pa, pb in panes:
                box(bg, m, lu0 + sw, lu1 - sw, gm - 0.004, gm + 0.004, pa, pb)
        left = el.get("hinge", "left") == "left"      # hinge side seen from the +w face; handle on the other side
        hu = lu1 - 0.07 if left else lu0 + 0.07
        ha, hb = (hu - 0.12, hu) if left else (hu, hu + 0.12)
        box(bl, m, ha, hb, wl1, wl1 + 0.05, z0 + 1.0, z0 + 1.03)  # lever handles on both faces, 1.0 m
        box(bl, m, ha, hb, wl0 - 0.05, wl0, z0 + 1.0, z0 + 1.03)
        self.emit({**el, "name": el.get("name", "Door") + "_Leaf"}, bl, COL[el.get("leaf_material", el.get("material", "metal"))], (A.x, A.y, z0))
        if bg.verts:
            self.emit({**el, "name": el.get("name", "Door") + "_Glass"}, bg, COL["glass"], (A.x, A.y, z0))
        else:
            bg.free()

    def b_stairs_run(self, el):
        """Straight flight: 'top' = world point at the centre of the top nosing line, dir_deg = downhill direction,
        z_top absolute; risers of riser_h, treads of tread; solid down to z_top - risers*riser_h - 0.2."""
        P = Vector(el["top"])
        fwd, left = rot2(el["dir_deg"])
        n, rh, tr, W = int(el["risers"]), el["riser_h"], el["tread"], el["width"]
        zt = el["z_top"]
        rb = el.get("bottom_riser_h", rh)   # optional lower first (bottom) riser, e.g. a half step at the hall floor
        zb = zt - (n - 1) * rh - rb
        prof = [(0.0, zb - 0.2), (0.0, zt)]
        x = 0.0
        z = zt
        for k in range(n):
            z -= rb if k == n - 1 else rh
            prof.append((x, z))
            if k < n - 1:
                x += tr
                prof.append((x, z))
        prof += [(x + el.get("run_out", 0.0), z), (x + el.get("run_out", 0.0), zb - 0.2)]
        st = el.get("soffit_thk")
        if st:  # sloped waist slab instead of a solid block (headroom under the flight): underside parallel to the
            # pitch line, st (m, normal to the slope) below the inner step corners; flat 0.2 m slab end at the bottom
            k = math.hypot(tr, rh) / tr                      # normal -> vertical thickness
            prof[0] = (0.0, zt - rh - st * k)
            prof[-1] = (prof[-1][0], zb - 0.2)
            ts = el.get("top_slab_t")
            if ts and ts > rh:
                # hung from a landing / floor slab of thickness ts: the top riser IS the slab edge, so the flight
                # starts 5 mm inside the slab (no face coplanar with the slab edge) and its waist underside starts at
                # the slab underside (no notch under the top nosing; map owner 2026-09-28)
                prof[0:2] = [(-0.005, zt - ts), (-0.005, zt - rh)]
        m = Matrix.Identity(4)
        m.col[0].xyz, m.col[1].xyz, m.col[2].xyz = left.to_3d(), fwd.to_3d(), Vector((0, 0, 1))
        m.col[3].xyz = Vector((P.x, P.y, 0))
        bm = bmesh.new()
        A = [bm.verts.new(m @ Vector((-W / 2, y, zz))) for y, zz in prof]
        Bv = [bm.verts.new(m @ Vector((W / 2, y, zz))) for y, zz in prof]
        k = len(prof)
        for i in range(k):
            j = (i + 1) % k
            bm.faces.new((A[i], A[j], Bv[j], Bv[i]))
        bm.faces.new(list(reversed(A)))
        bm.faces.new(Bv)
        self.emit(el, bm, (0.62, 0.45, 0.42, 1), (P.x, P.y, zt))

    def b_sink(self, el):
        """Pedestal wash basin (C WCs, 075931189 t4.4): round pedestal + oval bowl with a flat rim, on the floor
        against a wall. pos = centre of the bowl in plan, dir_deg = facing direction (away from the wall), z = floor."""
        P = Vector(el["pos"])
        fwd, left = rot2(el.get("dir_deg", 0.0))
        z = el["z"] if "z" in el else self.gz(P.x, P.y)
        w, dpt, h = el.get("width", 0.55), el.get("depth", 0.45), el.get("height", 0.85)
        bm = bmesh.new()
        ped = P - fwd * (dpt * 0.15)
        _cyl(bm, ped, 0.075, z, z + h - 0.16, 12)
        seg = 16
        def ring(zz, sc):
            return [bm.verts.new((P.x + (left.x * math.cos(a) * w / 2 + fwd.x * math.sin(a) * dpt / 2) * sc,
                                  P.y + (left.y * math.cos(a) * w / 2 + fwd.y * math.sin(a) * dpt / 2) * sc, zz))
                    for a in (2 * math.pi * k / seg for k in range(seg))]
        lo, hi = ring(z + h - 0.18, 0.78), ring(z + h, 1.0)
        _close_loops(bm, [lo, hi])
        self.emit(el, bm, COL["white"], (P.x, P.y, z))

    def b_box(self, el):
        """Axis box: centre (world xy), size [along dir, across, height], dir_deg, z0 absolute (furniture, cabinets)."""
        P = Vector(el["center"])
        fwd, _ = rot2(el.get("dir_deg", 0.0))
        a, b, h = el["size"]
        bm = bmesh.new()
        z0 = el["z0"] if "z0" in el else self.gz(P.x, P.y) + el.get("z_rel", 0.0)   # no z0: on the ground (+ z_rel)
        box(bm, _frame2(P, fwd), -a / 2, a / 2, -b / 2, b / 2, z0, z0 + h)
        self.emit(el, bm, COL.get(el.get("material", "wood"), COL["wood"]), (P.x, P.y, z0))

    def b_zebra(self, el):
        A, B = Vector(el["line"][0]), Vector(el["line"][-1])
        L = (B - A).length
        d = (B - A) / L
        W, sw, gap = el.get("width", 4.0), el.get("stripe_w", 0.4), el.get("gap", 0.6)
        m = _frame2(A, d)
        bm = bmesh.new()
        u = gap / 2
        while u + sw <= L - gap / 2 + 1e-6:
            pm = A + d * (u + sw / 2)
            z = self.gz(pm.x, pm.y)
            box(bm, m, u, u + sw, -W / 2, W / 2, z + 0.002, z + 0.008)  # raised 2-8 mm: no z-fight with the road
            u += sw + gap
        self.emit(el, bm, COL["paint"], (A.x, A.y, self.gz(A.x, A.y)))

    def b_bus_shelter(self, el):
        P = Vector(el["pos"])
        fwd, left = rot2(el.get("dir_deg", 0.0))
        L, D, H = el.get("length", 4.0), el.get("depth", 1.5), el.get("height", 2.5)
        z = self.gz(P.x, P.y)
        m = _frame2(P, left)      # u along the road, w toward the road (front)
        bm = bmesh.new()
        box(bm, m, -L / 2, L / 2, -D / 2, D / 2, z + H, z + H + 0.1)            # roof
        box(bm, m, -L / 2, L / 2, -D / 2, -D / 2 + 0.03, z + 0.1, z + H)         # back panel
        for u in (-L / 2, L / 2 - 0.03):
            box(bm, m, u, u + 0.03, -D / 2, D / 2 - 0.3, z + 0.1, z + H)       # side panels
        for u in (-L / 2 + 0.05, L / 2 - 0.05):
            for w in (-D / 2 + 0.05, D / 2 - 0.05):
                box(bm, m, u - 0.04, u + 0.04, w - 0.04, w + 0.04, z - BURY, z + H)
        box(bm, m, -L / 2 + 0.4, L / 2 - 0.4, -D / 2 + 0.05, -D / 2 + 0.45, z + 0.42, z + 0.47)  # bench
        self.emit(el, bm, COL["glass"], (P.x, P.y, z))

    # ------------------------------------------------------------------ sports area (SITE_Sports)
    def b_paint(self, el):
        """Line markings 5 mm proud of an absolute surface z: 'lines' (polylines) and 'arcs' {c, r, a0, a1 deg}.
        The strips start 2 mm above z, so their undersides are never coplanar with the field (z-fight audit)."""
        w, z = el.get("width", 0.05), el["z"]
        polys = [[Vector(p) for p in ln] for ln in el.get("lines", [])]
        for a in el.get("arcs", []):
            c, r, a0, a1 = Vector(a["c"]), a["r"], math.radians(a["a0"]), math.radians(a["a1"])
            n = max(4, int(abs(a1 - a0) * r / 0.4))       # ~0.4 m chords
            polys.append([c + Vector((math.cos(a0 + (a1 - a0) * k / n), math.sin(a0 + (a1 - a0) * k / n))) * r
                          for k in range(n + 1)])
        bm = bmesh.new()
        for pl in polys:
            for A, B in zip(pl[:-1], pl[1:]):
                L = (B - A).length
                if L > 1e-4:   # segments overlap by w/2 at joints: each piece stays a closed box
                    box(bm, _frame2(A, B - A), -w / 2, L + w / 2, -w / 2, w / 2, z + 0.002, z + 0.007)
        p = polys[0][0]
        self.emit(el, bm, COL["paint"], (p.x, p.y, z))

    def b_cage_fence(self, el):
        """Tall sports fence: square posts every ~post_spacing, horizontal rails at 'rails' heights (m above the base),
        one thin mesh plate per bay (masked mesh/net material later). Base = absolute 'z_base' or the ground.
        Two objects: <name>_Frame (posts + rails, painted green steel) and <name>_Mesh (the bay plates, one masked
        chain-link/net slot in UE) - owner frames 070410255 t49-t66, 070541257: green posts, see-through green mesh."""
        el = dict(el, slots={"_Frame": "M_Steel_Paint_Green", "_Mesh": "M_Fence_Mesh_Green", **(el.get("slots") or {})})
        pts = [Vector(p) for p in el["line"]]
        h, sp, ps, rs = el["height"], el.get("post_spacing", 3.0), el.get("post", 0.08), el.get("rail", 0.05)
        zb = el.get("z_base")
        mt = el.get("mesh_thk", 0.01)
        bm, bp = bmesh.new(), bmesh.new()
        first = True
        for A, B in zip(pts[:-1], pts[1:]):
            L = (B - A).length
            if L < 1e-3:
                continue
            m = _frame2(A, B - A)
            n = max(1, round(L / sp))
            z0 = zb if zb is not None else self.gz(*((A + B) / 2))
            for k in range(0 if first else 1, n + 1):  # corner post once
                q = A + (B - A) * (k / n)
                zp = zb if zb is not None else self.gz(q.x, q.y)
                box(bm, m, L * k / n - ps / 2, L * k / n + ps / 2, -ps / 2, ps / 2, zp - BURY, zp + h)
            first = False
            for zr in el.get("rails", [h - rs / 2]):
                box(bm, m, ps / 2, L - ps / 2, -rs / 2, rs / 2, z0 + zr - rs / 2, z0 + zr + rs / 2)
            xb = el.get("xbrace")          # [z0, z1] above the base: diagonal X in every bay (ball-stop section)
            if xb:
                for k in range(n):
                    for a0, a1 in ((0, 1), (1, 0)):
                        p0 = m @ Vector((L * (k + a0) / n, 0.0, 0.0))
                        p1 = m @ Vector((L * (k + a1) / n, 0.0, 0.0))
                        _rod(bm, Vector((p0.x, p0.y, z0 + xb[0])), Vector((p1.x, p1.y, z0 + xb[1])), rs * 0.8)
            for k in range(n):
                box(bp, m, L * k / n + ps / 2, L * (k + 1) / n - ps / 2, -mt / 2, mt / 2,
                    z0 + el.get("bottom_gap", 0.03), z0 + h - rs)
        p = pts[0]
        org = (p.x, p.y, zb if zb is not None else self.gz(p.x, p.y))
        self.emit(dict(el, name=el.get("name", "CageFence") + "_Frame"), bm, COL["metal"], org)
        self.emit(dict(el, name=el.get("name", "CageFence") + "_Mesh"), bp, COL["metal"], org)

    def b_net_roof(self, el):
        """Rope net over a cage: 'ring' (4 corners, world), absolute z, rope grid every 'spacing' m both ways."""
        o = [Vector(p) for p in el["ring"]]
        z, sp, t = el["z"], el.get("spacing", 2.0), el.get("rope", 0.03)
        bm = bmesh.new()
        for a, b, c_, d in ((o[0], o[1], o[3], o[2]), (o[0], o[3], o[1], o[2])):   # ropes parallel to a->b
            n = max(1, round((c_ - a).length / sp))
            for k in range(n + 1):
                A, B = a + (c_ - a) * (k / n), b + (d - b) * (k / n)
                box(bm, _frame2(A, B - A), 0.0, (B - A).length, -t / 2, t / 2, z - t, z)
        self.emit(el, bm, COL["metal"], (o[0].x, o[0].y, z))

    def b_floodlight(self, el):
        """Floodlight mast: round pole from the base to 'height', crossbar with 'heads' lamp boxes facing dir_deg."""
        P = Vector(el["pos"])
        zb = el.get("z_base", self.gz(P.x, P.y))
        h, nh = el.get("height", 9.0), int(el.get("heads", 2))
        fwd, left = rot2(el.get("dir_deg", 0.0))
        bm = bmesh.new()
        _cyl(bm, P, el.get("pole_d", 0.14) / 2, zb - BURY, zb + h, 12)
        span = 0.45 * nh
        m = _frame2(P, left)
        box(bm, m, -span / 2, span / 2, -0.03, 0.03, zb + h - 0.05, zb + h + 0.01)
        for k in range(nh):
            u = -span / 2 + span * (k + 0.5) / nh
            box(bm, m, u - 0.19, u + 0.19, -0.15, -0.03, zb + h + 0.01, zb + h + 0.33)  # lamp body, facing dir_deg
        self.emit(el, bm, COL["metal"], (P.x, P.y, zb))

    def b_lamp_orn(self, el):
        """Ornamental cast lamp post: pole, symmetric scroll arms (simplified to bars) with a globe at each end."""
        P = Vector(el["pos"])
        z = self.gz(P.x, P.y)
        h, span, n = el.get("height", 3.6), el.get("arm_span", 1.0), int(el.get("globes", 2))
        r = el.get("globe_d", 0.3) / 2
        fwd, left = rot2(el.get("dir_deg", 0.0))
        bm = bmesh.new()
        _cyl(bm, P, 0.11, z, z + 0.5, 10)                     # cast base
        _cyl(bm, P, 0.045, z + 0.5, z + h + 0.35, 10)         # pole + finial
        m = _frame2(P, left)
        box(bm, m, -span / 2, span / 2, -0.02, 0.02, z + h - 0.22, z + h - 0.18)   # arm bar
        for k in range(n):
            u = -span / 2 + span * k / max(1, n - 1)
            q = P + left * u
            box(bm, _frame2(q, fwd), -0.02, 0.02, -0.02, 0.02, z + h - 0.22, z + h - r)     # drop to the globe
            bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=r,
                                      matrix=Matrix.Translation((q.x, q.y, z + h)))
        self.emit(el, bm, COL["metal"], (P.x, P.y, z))

    def b_string_lights(self, el):
        """Festoon: wire between 'ends' [[x, y, z_above_ground], ...] sagging 'sag' m, bulbs every 'spacing' m."""
        E = el["ends"]
        sag, sp, r = el.get("sag", 0.3), el.get("spacing", 0.8), el.get("bulb_d", 0.08) / 2
        bm = bmesh.new()
        for a, b in zip(E[:-1], E[1:]):
            A = Vector((a[0], a[1], self.gz(a[0], a[1]) + a[2]))
            B = Vector((b[0], b[1], self.gz(b[0], b[1]) + b[2]))
            L = (B - A).length
            n = max(2, round(L / sp))
            pts = [A.lerp(B, k / n) - Vector((0, 0, 4 * sag * (k / n) * (1 - k / n))) for k in range(n + 1)]
            for p0, p1 in zip(pts[:-1], pts[1:]):
                d = p1 - p0
                m = Matrix.Identity(4)
                u = d.normalized()
                w_ = Vector((-u.y, u.x, 0)).normalized() if abs(u.z) < 0.99 else Vector((1, 0, 0))
                m.col[0].xyz, m.col[1].xyz, m.col[2].xyz, m.col[3].xyz = u, w_, u.cross(w_), p0
                box(bm, m, 0.0, d.length, -0.006, 0.006, -0.006, 0.006)
            for p in pts[1:-1]:
                bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=r,
                                          matrix=Matrix.Translation(p - Vector((0, 0, r + 0.02))))
        self.emit(el, bm, COL["white"], (E[0][0], E[0][1], self.gz(E[0][0], E[0][1])))

    def b_rail3d(self, el):
        """Handrail/railing along a 3D polyline 'points' [[x, y, z_abs], ...] (walking surface, e.g. stair nosings)."""
        from greybox.kit import railing
        pts = [Vector(p) for p in el["points"]]
        bm = bmesh.new()
        if el.get("unique_posts"):   # opt-in: one post per joint (kit.railing doubles them -> coincident faces)
            _railing_unique(bm, pts, el.get("height", 1.0), el.get("post", 0.05), el.get("rail", 0.05),
                            el.get("spacing", 1.2), el.get("mid_rails", 1))
        else:
            railing(bm, pts, height=el.get("height", 1.0), post=el.get("post", 0.05), rail=el.get("rail", 0.05),
                    spacing=el.get("spacing", 1.2), mid_rails=el.get("mid_rails", 1))
        self.emit(el, bm, COL.get(el.get("material", "metal"), COL["metal"]), tuple(pts[0]))

    def build(self):
        n = 0
        for el in self.s["elements"]:
            fn = getattr(self, "b_" + el["type"], None)
            if fn is None:
                if el["type"] not in ("pitch",):
                    print(f"  skip {el.get('name', '?')}: unsupported type {el['type']}")
                continue
            try:
                fn(el)
                n += 1
            except Exception as ex:  # keep building the rest; report the bad element
                print(f"  FAILED {el.get('name', el['type'])}: {ex!r}")
                bpy.app.driver_namespace.setdefault("koch_build_failures", []).append(f"  FAILED {el.get('name', el['type'])}: {ex!r}")
        return n


# ---------------------------------------------------------------------- small geometry helpers
def _frame2(p, d):
    """Matrix: u along 2D unit d, w to its left, z up, origin at 2D point p (z = 0)."""
    d = Vector((d.x, d.y)).normalized()
    m = Matrix.Identity(4)
    m.col[0].xyz = Vector((d.x, d.y, 0))
    m.col[1].xyz = Vector((-d.y, d.x, 0))
    m.col[2].xyz = Vector((0, 0, 1))
    m.col[3].xyz = Vector((p.x, p.y, 0))
    return m


def _railing_unique(bm, points, height, post, rail, spacing, mid_rails):
    """Like greybox.kit.railing, but a post within 8 cm (xy) of an earlier one is skipped (polyline joints)."""
    from greybox.kit import _sloped_bar
    placed = []
    for p, q in zip(points[:-1], points[1:]):
        seg = q - p
        flat = Vector((seg.x, seg.y, 0))
        run = flat.length
        if run < 1e-6:
            continue
        flat /= run
        m = Matrix.Identity(4)
        m.col[0].xyz, m.col[1].xyz, m.col[2].xyz, m.col[3].xyz = flat, Vector((-flat.y, flat.x, 0)), Vector((0, 0, 1)), p
        slope = seg.z / run
        n = max(1, round(run / spacing))
        for k in range(n + 1):
            u = run * k / n
            c = p + flat * u
            if any((c.x - a) ** 2 + (c.y - b) ** 2 < 0.08 ** 2 for a, b in placed):
                continue
            placed.append((c.x, c.y))
            box(bm, m, u - post / 2, u + post / 2, -post / 2, post / 2, slope * u, slope * u + height)
        for zr in [height] + [height * (i + 1) / (mid_rails + 1) for i in range(mid_rails)]:
            _sloped_bar(bm, m, run, slope, zr, rail)


def _cyl(bm, p, r, z0, z1, seg):
    lo = [bm.verts.new((p.x + r * math.cos(2 * math.pi * k / seg), p.y + r * math.sin(2 * math.pi * k / seg), z0)) for k in range(seg)]
    hi = [bm.verts.new((v.co.x, v.co.y, z1)) for v in lo]
    _close_loops(bm, [lo, hi])


def _rod(bm, p0, p1, tube):
    """Square tube of side `tube` from p0 to p1 (closed box)."""
    v = p1 - p0
    ln = v.length
    if ln < 1e-4:
        return
    u = v / ln
    s = u.cross(Vector((0, 0, 1)))
    s = (s if s.length > 1e-6 else Vector((1, 0, 0))).normalized() * (tube / 2)
    w = u.cross(s).normalized() * (tube / 2)
    r0 = [bm.verts.new(p0 + a * s + b * w) for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    r1 = [bm.verts.new(p1 + a * s + b * w) for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    _close_loops(bm, [r0, r1])


def _close_loops(bm, loops, cap_top=True):
    n = len(loops[0])
    for A, B in zip(loops[:-1], loops[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((A[i], A[j], B[j], B[i]))
    bm.faces.new(list(reversed(loops[0])))
    if cap_top:
        bm.faces.new(loops[-1])


def _ring_band(bm, outer, inner, z0, z1):
    """Closed band between an outer and an inner polygon (same vertex count), z0..z1."""
    n = len(outer)
    ob = [bm.verts.new((v.x, v.y, z0)) for v in outer]
    ot = [bm.verts.new((v.x, v.y, z1)) for v in outer]
    ib = [bm.verts.new((v.x, v.y, z0)) for v in inner]
    it = [bm.verts.new((v.x, v.y, z1)) for v in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((it[i], it[j], ib[j], ib[i]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ib[i], ib[j], ob[j], ob[i]))


def _sweep_kw(el, max_seg=None):
    """Optional sweep controls of a line element: 'follow_m' (subdivision step, m), 'cut_start_deg'/'cut_end_deg'."""
    return {"max_seg": el.get("follow_m", max_seg), "cut0": el.get("cut_start_deg"), "cut1": el.get("cut_end_deg")}


def _slab_with_holes(bm, ring, holes, z0, z1):
    """Closed slab z0..z1 over a CCW ring minus CW hole rings: triangulated caps, outer and hole side walls."""
    from mathutils.geometry import tessellate_polygon
    loops = [ring] + holes
    flat = [p for lp in loops for p in lp]
    tris = tessellate_polygon([[(x, y, 0.0) for x, y in lp] for lp in loops])
    lo = [bm.verts.new((x, y, z0)) for x, y in flat]
    hi = [bm.verts.new((x, y, z1)) for x, y in flat]
    for a, b, c in tris:
        bm.faces.new((hi[a], hi[b], hi[c]))
        bm.faces.new((lo[c], lo[b], lo[a]))
    k = 0
    for lp in loops:
        n = len(lp)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((lo[k + i], lo[k + j], hi[k + j], hi[k + i]))
        k += n


def _all_pads():
    """terrain_pads of every spec, in the order build_greybox.apply_terrain_pads applies them."""
    pads = []
    for fn in sorted(os.listdir(SPECS)):
        if fn.endswith(".json"):
            try:
                pads += json.load(open(os.path.join(SPECS, fn), encoding="utf-8")).get("terrain_pads", [])
            except ValueError:   # a half-written spec of another zone: its pads are skipped here too
                pass
    return pads


def _pad_z(pads, x, y, z):
    """Same blend as build_greybox.apply_terrain_pads for one point (inside -> pad z, linear over 'blend' m)."""
    for pad in pads:
        ring, blend = pad["ring"], float(pad.get("blend", 0.0))
        n, inside, d = len(ring), False, float("inf")
        for i in range(n):
            (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
            ax, ay = x2 - x1, y2 - y1
            t = min(1.0, max(0.0, ((x - x1) * ax + (y - y1) * ay) / (ax * ax + ay * ay)))
            d = min(d, math.hypot(x - x1 - t * ax, y - y1 - t * ay))
        w = 1.0 if inside else (max(0.0, 1.0 - d / blend) if blend > 0 else 0.0)
        zp = pad["z"]
        if "grad" in pad:  # sloped pad plane, same as build_greybox.pad_plane_z
            zp += pad["grad"][0] * (x - pad["ref"][0]) + pad["grad"][1] * (y - pad["ref"][1])
        z = z * (1 - w) + zp * w
    return z


def _ccw(r):
    a = 0.5 * sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r)))
    return [list(p) for p in (r if a > 0 else r[::-1])]


def _offset(ring, d):
    from greybox.kit import offset_ring
    return offset_ring(ring, d)


def clear(gen):
    for ob in [o for o in bpy.data.objects if o.get("koch_gen") == gen]:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def main():
    ids = [s for s in os.environ.get("KOCH_SITE", "").split(",") if s]
    ter = Terrain(load("terrain.json"))
    for sid in ids:
        try:  # one broken or half-written spec must not stop the others
            spec = json.load(open(os.path.join(SPECS, sid + ".json"), encoding="utf-8"))
            site = Site(spec, ter)
            clear(site.gen)
            for name in spec.get("replaces", []):
                ob = bpy.data.objects.get(name)
                if ob:
                    ob.hide_set(True)
                    ob.hide_render = True
            n = site.build()
        except Exception as ex:
            print(f"{sid}: FAILED {ex!r}")
            bpy.app.driver_namespace.setdefault("koch_build_failures", []).append(f"{sid}: FAILED {ex!r}")
            continue
        print(f"{sid}: {n} elements built")
    if bpy.app.background:
        bpy.ops.wm.save_mainfile(compress=True)


main()
