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
from greybox.kit import box  # noqa: E402
from greybox.sweep import hedge_profile, rect_profile, sweep_profile  # noqa: E402

BURY = 0.3
COL = {
    "hedge": (0.25, 0.42, 0.22, 1), "wall": (0.62, 0.60, 0.55, 1), "brick": (0.50, 0.22, 0.17, 1),
    "metal": (0.18, 0.18, 0.19, 1), "white": (0.90, 0.90, 0.88, 1), "roof": (0.45, 0.25, 0.18, 1),
    "wood": (0.40, 0.27, 0.16, 1), "stone": (0.55, 0.53, 0.50, 1), "paint": (0.95, 0.95, 0.92, 1),
    "glass": (0.40, 0.50, 0.55, 1), "low": (0.95, 0.55, 0.20, 1),
}


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

    def gz(self, x, y):
        """Ground z: terrain base, minus the curb reveal on carriageways."""
        z = float(self.ter.base(x, y))
        if self.ter.carriageway_mask(x, y):
            z -= self.ter.curb
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
        return ob

    # ------------------------------------------------------------------ element builders
    def b_fence(self, el):
        pts = el["line"]
        h, sp, post = el.get("height", 2.0), el.get("post_spacing", 2.5), el.get("post", 0.06)
        gap, panel = el.get("bottom_gap", 0.05), el.get("panel", "mesh")
        bm = bmesh.new()
        for a, b in zip(pts[:-1], pts[1:]):
            A, B = Vector(a), Vector(b)
            L = (B - A).length
            if L < 1e-3:
                continue
            d = (B - A) / L
            n = max(1, round(L / sp))
            m = _frame2(A, d)
            for k in range(n + 1):
                p = A + d * (L * k / n)
                z = self.gz(p.x, p.y)
                box(bm, m, L * k / n - post / 2, L * k / n + post / 2, -post / 2, post / 2, z - BURY, z + h)
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
        bm = bmesh.new()
        cap = el.get("cap_proj", 0.0)
        sweep_profile(bm, el["line"], rect_profile(el.get("thk", 0.3), el["height"], BURY), self.gz, el.get("closed", False))
        if cap > 0:
            sweep_profile(bm, el["line"], [(el["thk"] / 2 + cap, el["height"]), (el["thk"] / 2 + cap, el["height"] + 0.06),
                                           (-el["thk"] / 2 - cap, el["height"] + 0.06), (-el["thk"] / 2 - cap, el["height"])],
                          self.gz, el.get("closed", False))
        p = el["line"][0]
        self.emit(el, bm, COL.get(el.get("material", "stone"), COL["stone"]), (p[0], p[1], self.gz(*p)))

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
            sweep_profile(bm, el["line"], hedge_profile(el["width"], el["height"], rt, BURY), self.gz, el.get("closed", False))
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
        c = Vector(el["center"])
        N = int(el.get("sides", 8))
        R = el["across_flats"] / 2 / math.cos(math.pi / N)
        rot = math.radians(el.get("rot_deg", 0.0))
        z0 = self.gz(c.x, c.y)
        fh, ph, pw = el.get("floor_h", 0.15), el.get("post_h", 2.4), el.get("post_w", 0.25)
        par_h, par_t = el.get("parapet_h", 0.8), el.get("parapet_t", 0.25)
        open_sides = set(el.get("open_sides", []))

        def poly(r, z, extra=0.0):
            return [Vector((c.x + r * math.cos(rot + math.pi / N + 2 * math.pi * k / N + extra),
                            c.y + r * math.sin(rot + math.pi / N + 2 * math.pi * k / N + extra), z)) for k in range(N)]
        bm = bmesh.new()   # floor platform
        lo, hi = [bm.verts.new(v) for v in poly(R + 0.1, z0 - BURY)], [bm.verts.new(v) for v in poly(R + 0.1, z0 + fh)]
        _close_loops(bm, [lo, hi])
        self.emit(dict(el, name=el.get("name", "Gazebo") + "_Floor"), bm, COL["stone"], (c.x, c.y, z0))
        bm = bmesh.new()   # posts + parapets + ring beam
        corners = poly(R, 0)
        zf = z0 + fh
        for k in range(N):
            p = corners[k]
            m = _frame2(Vector((p.x, p.y)), (Vector((c.x, c.y)) - Vector((p.x, p.y))).normalized())
            box(bm, m, -pw / 2, pw / 2, -pw / 2, pw / 2, zf, zf + ph)
        for k in range(N):
            if k in open_sides:
                continue
            a, b = corners[k], corners[(k + 1) % N]
            A, B = Vector((a.x, a.y)), Vector((b.x, b.y))
            d = (B - A).normalized()
            L = (B - A).length
            m = _frame2(A, d)
            box(bm, m, pw / 2, L - pw / 2, -par_t / 2, par_t / 2, zf, zf + par_h)
        rb = 0.22
        _ring_band(bm, poly(R + pw / 2 + 0.02, 0), poly(R - pw / 2 - 0.02, 0), zf + ph, zf + ph + rb)
        self.emit(dict(el, name=el.get("name", "Gazebo") + "_Frame"), bm, COL["white"], (c.x, c.y, z0))
        bm = bmesh.new()   # pyramid roof with fascia
        zt = zf + ph + rb
        ro = R + el.get("overhang", 0.4)
        apo = ro * math.cos(math.pi / N)
        apex = Vector((c.x, c.y, zt + 0.15 + apo * math.tan(math.radians(el.get("roof_pitch", 30)))))
        bot = [bm.verts.new(v) for v in poly(ro, zt)]
        top = [bm.verts.new(v) for v in poly(ro, zt + 0.15)]
        _close_loops(bm, [bot, top], cap_top=False)
        av = bm.verts.new(apex)
        for k in range(N):
            bm.faces.new((top[k], top[(k + 1) % N], av))
        self.emit(dict(el, name=el.get("name", "Gazebo") + "_Roof"), bm, COL["roof"], (c.x, c.y, z0))

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
            z_top = zc + (hr * (1 - min(1.0, abs(across) / (W / 2))) if pitch > 0 else 0.0)
            zb = self.gz(P.x, P.y) - BURY
            if el.get("post_shape", "round") == "round":
                _cyl(bm, P, r, zb, z_top, 12)
            else:
                box(bm, _frame2(P, ax), -r, r, -r, r, zb, z_top)
        self.emit(dict(el, name=el.get("name", "Canopy") + "_Posts"), bm, COL["metal"], (cen.x, cen.y, zc))

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
        z = self.gz(P.x, P.y)
        m = _frame2(P, left)         # u along the bench, w = forward (facing)
        bm = bmesh.new()
        box(bm, m, -L / 2, L / 2, -D / 2, D / 2, z + sh - 0.05, z + sh)                 # seat
        box(bm, m, -L / 2, L / 2, -D / 2 - 0.04, -D / 2, z + sh + 0.1, z + bh)          # back
        for u in (-L / 2 + 0.1, L / 2 - 0.1):                                          # legs / side frames
            box(bm, m, u - 0.03, u + 0.03, -D / 2, D / 2, z, z + sh - 0.05)
        self.emit(el, bm, COL["wood"], (P.x, P.y, z))

    def b_lamp(self, el):
        P = Vector(el["pos"])
        z = self.gz(P.x, P.y)
        h = el.get("height", 3.5)
        bm = bmesh.new()
        _cyl(bm, P, 0.05, z - BURY, z + h, 10)
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

    def b_planter(self, el):
        bm = bmesh.new()
        w, h = el.get("curb_w", 0.08), el.get("curb_h", 0.15)
        sweep_profile(bm, _ccw(el["ring"]), [(0.0, -BURY), (0.0, h), (w, h), (w, -BURY)][::-1], self.gz, closed=True)
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
        w, t = el.get("width", 1.5), el.get("thk", 0.08)
        # top 2 cm above the terrain so it reads over the heightfield; slab reaches t below it
        sweep_profile(bm, el["line"], [(w / 2, 0.02 - t), (w / 2, 0.02), (-w / 2, 0.02), (-w / 2, 0.02 - t)],
                      self.gz, el.get("closed", False))
        p = el["line"][0]
        self.emit(el, bm, COL["stone"], (p[0], p[1], self.gz(*p)))

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


def _cyl(bm, p, r, z0, z1, seg):
    lo = [bm.verts.new((p.x + r * math.cos(2 * math.pi * k / seg), p.y + r * math.sin(2 * math.pi * k / seg), z0)) for k in range(seg)]
    hi = [bm.verts.new((v.co.x, v.co.y, z1)) for v in lo]
    _close_loops(bm, [lo, hi])


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
            continue
        print(f"{sid}: {n} elements built")
    if bpy.app.background:
        bpy.ops.wm.save_mainfile(compress=True)


main()
