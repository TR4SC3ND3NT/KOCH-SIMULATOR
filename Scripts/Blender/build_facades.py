# Builds phase-2 facade greyboxes (objects GBF_<id>_*) from Art/Blender/Specs/<BLD>.json (walls with real openings and reveals,
# window kit instances, surrounds, pilasters, cornice, plinth, mansard/hip roof, entrance stairs, canopy, ramp,
# light wells, sheds). Used by R1. Idempotent per building: removes objects tagged koch_gen="phase2:<id>".
# Run inside Blender: exec() with KOCH_SPECS="BLD_C" (comma list) or headless:
#   KOCH_SPECS=BLD_C blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_facades.py
# Spec units: metres in the building frame (x along the ring's first edge, y inward/north, z above FFL).
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from greybox.common import (FASCIA_M, SPECS, Terrain, bpypolyskel, ensure_collection, load,  # noqa: E402
                            make_object)
from greybox.kit import (Opening, WindowSpec, box, facade_frame, offset_ring, prism_profile,  # noqa: E402
                         railing, stair_flight, wall_piece, window_unit)

MAX_PIECE_M = 12.0   # Lumen SW: keep wall pieces well under ~15 m (distance field / card quality)
BURY_M = 0.3         # walls reach this far below the lowest ground along a facade

COL = {  # viewport object colours only (greybox review aid, not materials)
    "wall": (0.83, 0.78, 0.66, 1), "maroon": (0.50, 0.16, 0.14, 1), "plinth": (0.55, 0.22, 0.17, 1),
    "frame": (0.92, 0.92, 0.90, 1), "glass": (0.35, 0.45, 0.52, 1), "roof": (0.58, 0.22, 0.20, 1),
    "metal": (0.40, 0.42, 0.44, 1), "granite": (0.52, 0.40, 0.38, 1), "canopy": (0.75, 0.38, 0.22, 1),
    "sign": (0.20, 0.25, 0.45, 1), "brick": (0.45, 0.20, 0.16, 1), "low": (0.95, 0.55, 0.20, 1),
    "post": (0.55, 0.14, 0.12, 1),
}


# Spec keys whose numbers are not lengths (angles, counts, fractions, indices, world placement).
UNSCALED = {"scale", "pitch", "lower_pitch", "upper_pitch", "risers", "storeys", "mullions", "transoms", "edge",
            "anchor"}


def scale_spec(v, k, key=None):
    """Deep copy of spec value v with every length multiplied by k (bools/strings/UNSCALED keys untouched)."""
    if key in UNSCALED:
        return v
    if isinstance(v, bool) or isinstance(v, str) or v is None:
        return v
    if isinstance(v, (int, float)):
        return v * k
    if isinstance(v, list):
        return [scale_spec(x, k) for x in v]
    if isinstance(v, dict):
        return {kk: scale_spec(vv, k, kk) for kk, vv in v.items()}
    return v


class Building:
    def __init__(self, spec, ter):
        k = float(spec.get("scale", 1.0))
        if abs(k - 1.0) > 1e-9:  # grow about the ring centroid so the block stays centred on its satellite outline
            cx = sum(p[0] for p in spec["ring"]) / len(spec["ring"])
            cy = sum(p[1] for p in spec["ring"]) / len(spec["ring"])
            spec = scale_spec(spec, k)
            ax, ay = spec["anchor"]["x_dir"]
            n = math.hypot(ax, ay)
            ox, oy = (1 - k) * cx, (1 - k) * cy  # local shift of the anchor
            wx, wy = spec["anchor"]["world_xy"]
            spec["anchor"] = dict(spec["anchor"], world_xy=[wx + (ax * ox - ay * oy) / n, wy + (ay * ox + ax * oy) / n])
        self.s = spec
        self.id = spec["id"]
        self.gen = "phase2:" + self.id
        a = spec["anchor"]
        dx, dy = a["x_dir"]
        n = math.hypot(dx, dy)
        dx, dy = dx / n, dy / n
        self.ring = [tuple(p) for p in spec["ring"]]
        ox, oy = a["world_xy"]
        rot = Matrix(((dx, -dy, 0), (dy, dx, 0), (0, 0, 1))).to_4x4()
        # FFL: highest ground under the wall ring + plinth (the entrance side is the high side on this slope).
        wx = np.array([ox + dx * x - dy * y for x, y in self.ring])
        wy = np.array([oy + dy * x + dx * y for x, y in self.ring])
        g = ter.base(wx, wy)
        self.ffl = float(g.max()) + spec["plinth_m"]
        self.ground_local = g - self.ffl  # per ring vertex, local z of the ground
        self.M = Matrix.Translation((ox, oy, self.ffl)) @ rot
        self.col = ensure_collection(spec.get("collection", "BLD_" + self.id.split("_")[1]))
        self.edges = []
        for i in range(len(self.ring)):
            p, q = self.ring[i], self.ring[(i + 1) % len(self.ring)]
            L = math.dist(p, q)
            self.edges.append({"p": p, "q": q, "L": L, "frame": facade_frame(p, q, 0.0),
                               "zg": float(min(self.ground_local[i], self.ground_local[(i + 1) % len(self.ring)]))})
        self.kit_meshes = {}

    # ------------------------------------------------------------------ helpers
    def obj(self, name, bm, color, item_evidence=None, confidence=None):
        """Link one element; confidence 'low' is shown orange (unverified estimate, see photo_requests.md)."""
        it = {"id": self.id, "status": self.s.get("status", "probable"), "evidence": [item_evidence] if item_evidence else []}
        if confidence == "low":
            color = COL["low"]
        ob = make_object(f"GBF_{self.id}_{name}", bm, self.col, None, it, color, gen=self.gen, matrix=self.M)
        ob["koch_confidence"] = confidence or ""
        return ob

    def corner_cut(self, i, end):
        """Inner-face inset at the start (end=False) or end of edge i: +thk convex, -thk concave (90 deg)."""
        n = len(self.ring)
        a = self.ring[(i - 1) % n] if not end else self.ring[i]
        b = self.ring[i] if not end else self.ring[(i + 1) % n]
        c = self.ring[(i + 1) % n] if not end else self.ring[(i + 2) % n]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        t = self.s["wall_thk"]
        return t if cross > 0 else -t

    def openings_for(self, i):
        """[(Opening, type_name, spec)] for edge i from the facade spec."""
        f = next((f for f in self.s["facades"] if f["edge"] == i), None)
        out = []
        if not f:
            return out, None
        rows = self.s.get("rows", {})
        for grp in f.get("windows", []):
            wt = self.s["window_types"][grp["type"]]
            sills = [rows[r] for r in grp.get("rows", [])] + list(grp.get("sills", []))
            for u in grp["u"]:
                for z in sills:
                    out.append((Opening(u - wt["w"] / 2, u + wt["w"] / 2, z, z + wt["h"]), grp["type"], wt))
        ent = f.get("entrance")
        if ent:
            out.append((Opening(ent["u0"], ent["u1"], 0.02, ent["z1"]), "entrance", ent))
        return out, f

    def bands(self):
        st = self.s["storey_m"]
        levels = [st * k for k in range(1, self.s["storeys"])]
        return [0.0] + levels + [self.s["eave_z"]]

    # ------------------------------------------------------------------ walls + openings
    def build_walls(self):
        thk = self.s["wall_thk"]
        levels = self.bands()
        for i, e in enumerate(self.edges):
            ops, fspec = self.openings_for(i)
            L = e["L"]
            cut0, cut1 = self.corner_cut(i, False), self.corner_cut(i, True)
            z_bottom = e["zg"] - BURY_M
            bsm = self.s.get("basement")
            if bsm:  # walls continue down to the underside of the basement floor slab
                z_bottom = min(z_bottom, bsm["floor_z"] - bsm["slab_t"])
            bands = [(z_bottom, levels[0])] + list(zip(levels[:-1], levels[1:]))
            for bi, (z0, z1) in enumerate(bands):
                bo = [o for o, _, _ in ops if o.z0 >= z0 - 1e-6 and o.z1 <= z1 + 1e-6]
                # split long bands at wall gaps between openings
                cuts = self._split_points(bo, L, cut0, cut1)
                for ci, (u0, u1) in enumerate(cuts):
                    local = [Opening(o.u0 - u0, o.u1 - u0, o.z0, o.z1) for o in bo if o.u0 >= u0 and o.u1 <= u1]
                    fr = e["frame"] @ Matrix.Translation((u0, 0, 0))
                    bm = bmesh.new()
                    wall_piece(bm, fr, u1 - u0, z0, z1, thk, local,
                               cut_start=cut0 if abs(u0) < 1e-6 else 0.0,
                               cut_end=cut1 if abs(u1 - L) < 1e-6 else 0.0)
                    self.obj(f"Wall_E{i}_B{bi}_{ci}", bm, COL["maroon"] if fspec and fspec.get("name", "").startswith("south_tower") else COL["wall"],
                             fspec.get("evidence") if fspec else None)
            self.build_windows(i, ops)

    @staticmethod
    def _split_points(ops, L, cut0, cut1):
        if L <= MAX_PIECE_M:
            return [(0.0, L)]
        n = math.ceil(L / MAX_PIECE_M)
        target = [L * k / n for k in range(1, n)]
        gaps = []  # u ranges free of openings, away from the mitred ends
        edges = sorted([(o.u0, o.u1) for o in ops])
        prev = abs(cut0) + 0.2
        for a, b in edges + [(L - abs(cut1) - 0.2, L)]:
            if a - prev > 0.1:
                gaps.append((prev, a))
            prev = max(prev, b)
        cuts = []
        for t in target:
            best = min(gaps, key=lambda g: 0 if g[0] <= t <= g[1] else min(abs(t - g[0]), abs(t - g[1])), default=None)
            if best:
                cuts.append(min(max(t, best[0] + 0.05), best[1] - 0.05))
        us = [0.0] + sorted(cuts) + [L]
        return list(zip(us[:-1], us[1:]))

    def kit_mesh(self, key, builder):
        """One shared mesh per window/surround variant, placed as linked duplicates (UE instances later)."""
        if key in self.kit_meshes:
            return self.kit_meshes[key]
        name = f"KIT_{self.id}_{key}"
        me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
        bm = bmesh.new()
        builder(bm)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        self.kit_meshes[key] = me
        return me

    def build_windows(self, i, ops):
        e = self.edges[i]
        for k, (o, tname, wt) in enumerate(ops):
            ident = Matrix.Identity(4)
            w, h = o.u1 - o.u0, o.z1 - o.z0
            if tname == "entrance":
                me = self.kit_mesh(f"Entrance_{w:.2f}x{h:.2f}", lambda bm: window_unit(
                    bm, ident, Opening(0, w, 0, h), WindowSpec(reveal=0.25, mullions=[0.25, 0.5, 0.75], transoms=[0.78], sill_proj=0)))
                color = COL["frame"]
            else:
                spec = WindowSpec(reveal=wt.get("reveal", 0.16), mullions=wt.get("mullions", []), transoms=wt.get("transoms", []))
                me = self.kit_mesh(f"Window_{tname}", lambda bm: window_unit(bm, ident, Opening(0, w, 0, h), spec))
                color = COL["frame"]
            place = self.M @ e["frame"] @ Matrix.Translation((o.u0, 0, o.z0))
            self._link(f"Win_E{i}_{k:02d}", me, place, color)
            sw = wt.get("surround") if tname != "entrance" else None
            if sw and any(sw):
                l, r, b, t = sw
                proj = wt.get("surround_proj", 0.04)
                me2 = self.kit_mesh(f"Surround_{tname}", lambda bm: _surround(bm, w, h, l, r, b, t, proj))
                self._link(f"Sur_E{i}_{k:02d}", me2, place, COL["maroon"])

    def _link(self, name, me, matrix, color):
        ob = bpy.data.objects.new(f"GBF_{self.id}_{name}", me)
        ob.matrix_world = matrix
        ob["koch_gen"] = self.gen
        ob["koch_id"] = self.id
        ob.color = color
        self.col.objects.link(ob)

    # ------------------------------------------------------------------ bands, pilasters, plinth
    def build_trim(self):
        c = self.s.get("cornice")
        pl = self.s.get("plinth")
        if c:
            bm_c = bmesh.new()
            for i, e in enumerate(self.edges):
                ext0 = c["proj"] if self.corner_cut(i, False) > 0 else -c["proj"]
                ext1 = c["proj"] if self.corner_cut(i, True) > 0 else -c["proj"]
                box(bm_c, e["frame"], -ext0, e["L"] + ext1, 0.0, c["proj"], c["z0"], c["z1"])
            self.obj("Cornice", bm_c, COL["maroon"], c.get("evidence", "cornice band under the eaves"), c.get("confidence"))
        if pl:
            bm_pl = bmesh.new()
            for i, e in enumerate(self.edges):
                p0 = pl["proj"] if self.corner_cut(i, False) > 0 else -pl["proj"]
                p1 = pl["proj"] if self.corner_cut(i, True) > 0 else -pl["proj"]
                box(bm_pl, e["frame"], -p0, e["L"] + p1, 0.0, pl["proj"], e["zg"] - 0.05, pl["z_top"])
            self.obj("Plinth", bm_pl, COL["plinth"], pl.get("evidence", "brick-tile plinth"), pl.get("confidence"))
        for k, p in enumerate(self.s.get("pilasters", [])):
            e = self.edges[p["edge"]]
            bm_p = bmesh.new()
            box(bm_p, e["frame"], p["u0"], p["u1"], 0.0, p["proj"], p["z0"], p["z1"])
            self.obj(f"Pilaster_E{p['edge']}_{k:02d}", bm_p, COL["maroon"], p.get("evidence", "pilaster"), p.get("confidence"))

    # ------------------------------------------------------------------ roof
    def build_roof(self):
        r = self.s["roof"]
        kind = r.get("type", "hip")
        if kind == "none":
            return
        if kind == "flat":
            return self.build_flat_roof(r)
        if kind in ("gable", "shed"):
            return self.build_gable_or_shed(r, kind)
        if kind == "hip" and r.get("ridge_len") and len(self.ring) == 4:
            return self.build_rect_hip(r)
        z0 = self.s["eave_z"]
        outline = offset_ring(self.ring, -r["overhang"])
        bm = bmesh.new()
        bot = [bm.verts.new((x, y, z0 - FASCIA_M)) for x, y in outline]
        top = [bm.verts.new((x, y, z0)) for x, y in outline]
        n = len(outline)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((bot[i], bot[j], top[j], top[i]))
        bm.faces.new(list(reversed(bot)))
        base_ring, base_verts, zb = outline, top, z0
        if r["type"] == "mansard":
            inset = r["lower_h"] / math.tan(math.radians(r["lower_pitch"]))
            inner = offset_ring(outline, inset)
            zb = z0 + r["lower_h"]
            iv = [bm.verts.new((x, y, zb)) for x, y in inner]
            for i in range(n):
                j = (i + 1) % n
                bm.faces.new((top[i], top[j], iv[j], iv[i]))
            base_ring, base_verts = inner, iv
            pitch = r["upper_pitch"]
        else:
            pitch = r.get("pitch", 20)
        verts = [Vector((x, y, zb)) for x, y in base_ring]
        faces = bpypolyskel.polygonize(verts, 0, n, None, 0.0, math.tan(math.radians(pitch)))
        allv = base_verts + [bm.verts.new(v) for v in verts[n:]]
        for f in faces:
            if len(set(f)) == len(f):
                try:
                    bm.faces.new([allv[k] for k in f])
                except ValueError:
                    pass
        self.obj("Roof", bm, COL["roof"], r.get("evidence"), r.get("confidence"))
        if r.get("dormers"):
            self.build_dormers(outline, r)

    def build_rect_hip(self, r):
        """Hip roof on a rectangle with a given ridge length: long slopes at `pitch`, ends as steep as needed."""
        z0 = self.s["eave_z"]
        out = offset_ring(self.ring, -r.get("overhang", 0.5))
        P = [Vector(p) for p in out]
        e = [(P[(i + 1) % 4] - P[i]) for i in range(4)]
        k = 0 if e[0].length >= e[1].length else 1                  # edges k, k+2 are the long eaves
        a, b, c, d = P[k], P[(k + 1) % 4], P[(k + 2) % 4], P[(k + 3) % 4]
        L, W = (b - a).length, (d - a).length
        ridge = min(r["ridge_len"], L - 0.2)
        h = W / 2 * math.tan(math.radians(r.get("pitch", 20)))
        ax = (b - a).normalized()
        mid = (a + b + c + d) / 4
        r0, r1 = mid - ax * ridge / 2, mid + ax * ridge / 2
        bm = bmesh.new()
        bot = [bm.verts.new((p.x, p.y, z0 - FASCIA_M)) for p in (a, b, c, d)]
        top = [bm.verts.new((p.x, p.y, z0)) for p in (a, b, c, d)]
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((bot[i], bot[j], top[j], top[i]))
        bm.faces.new(list(reversed(bot)))
        R0 = bm.verts.new((r0.x, r0.y, z0 + h))
        R1 = bm.verts.new((r1.x, r1.y, z0 + h))
        ta, tb, tc, td = top
        bm.faces.new((ta, tb, R1, R0))    # long slope a-b
        bm.faces.new((tc, td, R0, R1))    # long slope c-d
        bm.faces.new((tb, tc, R1))        # hip end b-c
        bm.faces.new((td, ta, R0))        # hip end d-a
        self.obj("Roof", bm, COL["roof"], r.get("evidence", r.get("note")), r.get("confidence"))
        self.s["roof"]["_end_pitch_deg"] = round(math.degrees(math.atan2(h, (L - ridge) / 2)), 1)

    def build_flat_roof(self, r):
        """Parapet band on the wall ring (the eave slab already closes the top)."""
        h, t = r.get("parapet_h", 0.0), r.get("parapet_t", 0.25)
        if h <= 0:
            return
        z0 = self.s["eave_z"] - 0.02  # overlaps the wall top by 2 cm: no coincident faces
        bm = bmesh.new()
        _ring_band(bm, self.ring, offset_ring(self.ring, t), z0, self.s["eave_z"] + h)
        self.obj("Parapet", bm, COL["wall"], r.get("evidence"), r.get("confidence"))

    def build_gable_or_shed(self, r, kind):
        """Rectangular rings only: gable (ridge between the mid-points of the two gable ends) or mono-pitch."""
        if len(self.ring) != 4:
            print(f"  {self.id}: {kind} roof needs a 4-vertex ring, falling back to hip")
            r = dict(r, type="hip")
            self.s["roof"] = r
            return self.build_roof()
        z0 = self.s["eave_z"]
        out = offset_ring(self.ring, -r.get("overhang", 0.4))
        tp = math.tan(math.radians(r.get("pitch", 20)))
        bm = bmesh.new()
        if kind == "gable":
            g0 = r["gable_edges"][0] % 4
            g1 = (g0 + 2) % 4
            span = math.dist(out[g0], out[(g0 + 1) % 4])
            h = span / 2 * tp
            bot = [bm.verts.new((x, y, z0 - FASCIA_M)) for x, y in out]
            top = [bm.verts.new((x, y, z0)) for x, y in out]
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new((bot[i], bot[j], top[j], top[i]))
            bm.faces.new(list(reversed(bot)))

            def mid(e):
                a, b = out[e], out[(e + 1) % 4]
                return bm.verts.new(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z0 + h))
            m0, m1 = mid(g0), mid(g1)
            ea, eb = (g0 + 1) % 4, (g1 + 1) % 4
            bm.faces.new((top[ea], top[(ea + 1) % 4], m1, m0))
            bm.faces.new((top[eb], top[(eb + 1) % 4], m0, m1))
            bm.faces.new((top[g0], top[(g0 + 1) % 4], m0))
            bm.faces.new((top[g1], top[(g1 + 1) % 4], m1))
        else:  # shed: high side along edge high_edge
            hi = r["high_edge"] % 4
            a, b = Vector(out[hi]), Vector(out[(hi + 1) % 4])
            d = (b - a).normalized()
            nrm = Vector((-d.y, d.x))  # into the building from the high edge
            depth = abs((Vector(out[(hi + 2) % 4]) - a).dot(nrm))

            def zt(p):
                return z0 + (depth - (Vector(p) - a).dot(nrm)) * tp
            bot = [bm.verts.new((x, y, zt((x, y)) - FASCIA_M)) for x, y in out]
            top = [bm.verts.new((x, y, zt((x, y)))) for x, y in out]
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new((bot[i], bot[j], top[j], top[i]))
            bm.faces.new(list(reversed(bot)))
            bm.faces.new(top)
            # wall infill from the eave slab up to the sloped roof underside
            bm2 = bmesh.new()
            lo = [bm2.verts.new((x, y, z0 - 0.25)) for x, y in self.ring]
            up = [bm2.verts.new((x, y, zt((x, y)) - FASCIA_M + 0.01)) for x, y in self.ring]
            for i in range(4):
                j = (i + 1) % 4
                bm2.faces.new((lo[i], lo[j], up[j], up[i]))
            bm2.faces.new(list(reversed(lo)))
            bm2.faces.new(up)
            self.obj("RoofInfill", bm2, COL["wall"], r.get("evidence"), r.get("confidence"))
        self.obj("Roof", bm, COL["roof"], r.get("evidence"), r.get("confidence"))

    def build_dormers(self, outline, r):
        """Pointed (triangular) dormers standing on the roof slope, bodies buried in the roof solid."""
        d = r["dormer"]
        bm = bmesh.new()
        z0 = self.s["eave_z"]
        if r["type"] == "mansard":
            run = r["lower_h"] / math.tan(math.radians(r["lower_pitch"]))
            inset, rise = run * 0.35, r["lower_h"] * 0.35
        else:
            inset = d.get("inset", 1.2)
            rise = inset * math.tan(math.radians(r.get("pitch", 20)))
        w_front = r["overhang"] - inset          # w is outward from the wall face; the eave is at +overhang
        zf = z0 + rise
        back = w_front - d["h"] / math.tan(math.radians(max(r.get("pitch", 20), 10))) - 0.5
        for grp in r["dormers"]:
            fr = self.edges[grp["edge"]]["frame"]
            hw = d["w"] / 2
            for u in grp["u"]:
                c = []
                for w in (w_front, back):
                    c += [bm.verts.new(fr @ Vector((u - hw, w, zf - 0.3))), bm.verts.new(fr @ Vector((u + hw, w, zf - 0.3))),
                          bm.verts.new(fr @ Vector((u, w, zf + d["h"])))]
                for f in ((0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)):
                    bm.faces.new([c[k] for k in f])
        self.obj("Dormers", bm, COL["roof"], "pointed dormers on the roof slopes (render 2025, Esri 2020)")

    # ------------------------------------------------------------------ attachments
    def build_attachments(self):
        for a in self.s.get("attachments", []):
            e = self.edges[a["edge"]]
            fr = e["frame"]
            t = a["type"]
            bm = bmesh.new()
            cf = a.get("confidence")
            if t == "stairs":
                stair_flight(bm, fr, a["u0"], a["u1"], a["risers"], a["riser_h"], a["tread"], a["landing"],
                             z_base=-a["risers"] * a["riser_h"])
                self.obj(f"Stairs_E{a['edge']}_{a['u0']:.0f}", bm, COL["granite"], a.get("evidence"), cf)
            elif t == "gallery":
                self.build_gallery(a, e, fr)
            elif t == "wall_sign":  # lettering/logo panel on the wall face (content = KOCH branding later)
                box(bm, fr, a["u0"], a["u1"], 0.0, a.get("t", 0.08), a["z0"], a["z1"])
                self.obj(f"Sign_{a.get('name', a['u0'])}", bm, COL["sign"], a.get("evidence"), cf)
            elif t == "stair_well":
                self.build_stair_well(a, e, fr)
            elif t == "porch":
                self.build_porch(a, e, fr)
            elif t == "canopy":
                box(bm, fr, a["u0"], a["u1"], 0.0, a["depth"], a["z0"], a["z1"])
                s = a.get("sign")
                if s:
                    box(bm, fr, a["u0"], a["u1"], a["depth"] - s["t"], a["depth"], a["z1"], s["z1"])
                self.obj(f"Canopy_E{a['edge']}", bm, COL["canopy"], a.get("evidence"))
            elif t == "ramp":
                # wedge running along u: high end at u0 (landing), low end at u1 (plaza)
                prof = [(a["u0"], a["z_high"]), (a["u1"], a["z_low"]), (a["u1"], a["z_low"] - 0.25), (a["u0"], a["z_low"] - 0.25)]
                _prism_along_w(bm, fr, prof, a["w0"], a["w1"])
                self.obj(f"Ramp_E{a['edge']}", bm, COL["granite"], a.get("evidence"))
                if a.get("rails"):
                    bm2 = bmesh.new()
                    for w in (a["w0"] + 0.05, a["w1"] - 0.05):
                        pts = [fr @ Vector((a["u0"], w, a["z_high"])), fr @ Vector((a["u1"], w, a["z_low"]))]
                        railing(bm2, pts, height=0.9, spacing=1.5, mid_rails=1)
                    self.obj(f"RampRail_E{a['edge']}", bm2, COL["metal"], a.get("evidence"))
            elif t == "lightwell":
                prism_profile(bm, fr, [(0.0, a["z_wall"]), (a["depth"], a["z_edge"]), (a["depth"], a["z_edge"] - 0.06),
                                       (0.0, a["z_wall"] - 0.06)], a["u0"], a["u1"])
                self.obj(f"LightwellCover_E{a['edge']}_{a['u0']:.0f}", bm, COL["maroon"], a.get("evidence"))
            elif t == "shed":
                zg = e["zg"]
                prof = [(0.0, zg - BURY_M), (0.0, a["z_high"]), (a["depth"], a["z_low"]), (a["depth"], zg - BURY_M)]
                prism_profile(bm, fr, prof, a["u0"], a["u1"])
                bm2 = bmesh.new()  # corrugated roof sheet, 0.15 m overhang on three sides
                prism_profile(bm2, fr, [(0.0, a["z_high"] + 0.01), (a["depth"] + 0.15, a["z_low"] - 0.01),
                                        (a["depth"] + 0.15, a["z_low"] + 0.05), (0.0, a["z_high"] + 0.07)],
                              a["u0"] - 0.15, a["u1"] + 0.15)
                self.obj(a["name"], bm, COL["brick"], a.get("evidence"))
                self.obj(a["name"] + "_Roof", bm2, COL["metal"], a.get("evidence"))
            elif t == "stair_box":
                zg = e["zg"]
                box(bm, fr, a["u0"], a["u1"], 0.0, a["depth"], zg - BURY_M, a["z_top"])
                cn = a.get("canopy")
                bm2 = bmesh.new()
                if cn:
                    box(bm2, fr, cn["u0"], cn["u1"], 0.0, cn["depth"], cn["z"], cn["z"] + 0.12)
                    for u in (cn["u1"] - 0.1,):
                        box(bm2, fr, u - 0.05, u + 0.05, cn["depth"] - 0.1, cn["depth"], zg, cn["z"])
                self.obj(a["name"], bm, COL["brick"], a.get("evidence"))
                self.obj(a["name"] + "_Canopy", bm2, COL["metal"], a.get("evidence"))
            else:
                print(f"  {self.id}: skip unsupported attachment type {t!r}")

    def build_gallery(self, a, e, fr):
        """Covered colonnade along a wall: posts on the outer line, edge beam, sloped/flat roof slab, optional deck."""
        u0, u1, dep = a["u0"], a["u1"], a["depth"]
        pw, pd = a.get("post_w", 0.3), a.get("post_d", a.get("post_w", 0.3))
        zu, fall, thk, bh = a["z_underside"], a.get("roof_fall", 0.0), a.get("roof_thk", 0.15), a.get("beam_h", 0.3)
        zb = a["floor_z"] if "floor_z" in a else e["zg"]
        cf, ev = a.get("confidence"), a.get("evidence")
        tag = f"E{a['edge']}_{u0:.0f}"
        bm = bmesh.new()
        for u in a.get("posts_u", []):
            box(bm, fr, u - pw / 2, u + pw / 2, dep - pd, dep, zb - (0.0 if "floor_z" in a else BURY_M), zu - bh)
        self.obj(f"GalleryPosts_{tag}", bm, COL["post"], ev, cf)
        bm = bmesh.new()
        box(bm, fr, u0, u1, dep - pd - 0.02, dep + 0.02, zu - bh, zu)
        oh = a.get("roof_overhang", 0.15)
        prism_profile(bm, fr, [(0.0, zu + fall), (dep + oh, zu - oh * fall / max(dep, 1e-3)),
                               (dep + oh, zu - oh * fall / max(dep, 1e-3) + thk), (0.0, zu + fall + thk)], u0 - oh, u1 + oh)
        self.obj(f"GalleryRoof_{tag}", bm, COL["roof"], ev, cf)
        if "floor_z" in a:
            bm = bmesh.new()
            box(bm, fr, u0, u1, 0.0, dep, e["zg"] - BURY_M, a["floor_z"])
            self.obj(f"GalleryDeck_{tag}", bm, COL["granite"], ev, cf)

    def build_stair_well(self, a, e, fr):
        """Sunken stair along the wall (u_top at grade -> u_bottom at z_bottom), outer retaining wall + railing.
        The terrain heightfield still covers it until the phase-4 terrain carve."""
        ut, ub, w0, w1, zb = a["u_top"], a["u_bottom"], a["w0"], a["w1"], a["z_bottom"]
        zg = e["zg"]
        n = max(2, round((zg - zb) / a.get("riser_h", 0.165)))
        rh = (zg - zb) / n
        sgn = 1.0 if ut > ub else -1.0
        tread = abs(ut - ub) / n
        prof = [(ub, zb - 0.2), (ub, zb)]
        for k in range(1, n):
            u = ub + sgn * tread * k
            prof += [(u, zb + rh * (k - 1)), (u, zb + rh * k)]
        prof += [(ut, zb + rh * (n - 1)), (ut, zb - 0.2)]
        if sgn < 0:
            prof = prof[::-1]
        bm = bmesh.new()
        _prism_along_w(bm, fr, prof, w0, w1)
        self.obj(a["name"], bm, COL["granite"], a.get("evidence"), a.get("confidence"))
        bm = bmesh.new()
        wt = a.get("wall_t", 0.2)
        lo, hi = min(ut, ub), max(ut, ub)
        box(bm, fr, lo, hi, w1, w1 + wt, zb - 0.2, zg + 0.1)
        self.obj(a["name"] + "_Wall", bm, COL["wall"], a.get("evidence"), a.get("confidence"))
        bm = bmesh.new()
        railing(bm, [fr @ Vector((lo, w1 + wt / 2, zg + 0.1)), fr @ Vector((hi, w1 + wt / 2, zg + 0.1))],
                height=a.get("rail_h", 1.0) - 0.1, spacing=1.2, mid_rails=2)
        self.obj(a["name"] + "_Rail", bm, COL["metal"], a.get("evidence"), a.get("confidence"))

    def build_porch(self, a, e, fr):
        """Entrance pavilion: gable roof with its ridge perpendicular to the wall, on piers, with a pediment."""
        u0, u1, dep = a["u0"], a["u1"], a["depth"]
        ze, oh, pw = a["z_eave"], a.get("overhang", 0.4), a.get("pier_w", 0.5)
        tp = math.tan(math.radians(a.get("pitch", 25)))
        um = (u0 + u1) / 2
        hs = (u1 - u0) / 2 * tp
        thk = a.get("roof_thk", 0.2)
        cf, ev = a.get("confidence"), a.get("evidence")
        tag = f"E{a['edge']}_{u0:.0f}"
        bm = bmesh.new()
        for u in a.get("piers_u", [u0 + pw / 2, u1 - pw / 2]):
            box(bm, fr, u - pw / 2, u + pw / 2, dep - pw, dep, e["zg"] - BURY_M, ze)
        box(bm, fr, u0, u1, dep - pw, dep, ze - 0.35, ze)                                    # front beam
        _prism_along_w(bm, fr, [(u0, ze), (u1, ze), (um, ze + hs)], dep - pw, dep - 0.05)      # pediment
        self.obj(f"PorchPiers_{tag}", bm, COL["wall"], ev, cf)
        bm = bmesh.new()
        _prism_along_w(bm, fr, [(u0 - oh, ze - oh * tp), (um, ze + hs), (u1 + oh, ze - oh * tp), (u1 + oh, ze - oh * tp + thk),
                                (um, ze + hs + thk), (u0 - oh, ze - oh * tp + thk)], 0.0, dep + oh)
        self.obj(f"PorchRoof_{tag}", bm, COL["roof"], ev, cf)

    def build(self):
        self.build_walls()
        self.build_trim()
        self.build_roof()
        self.build_attachments()
        # ground floor slab and top ceiling close the shell (interiors come in phase 5)
        bm = bmesh.new()
        inner = offset_ring(self.ring, self.s["wall_thk"])
        slabs = [(-0.25, 0.0), (self.s["eave_z"] - 0.25, self.s["eave_z"])]
        bsm = self.s.get("basement")
        if bsm:
            slabs.append((bsm["floor_z"] - bsm["slab_t"], bsm["floor_z"]))
        for z0, z1 in slabs:
            lo = [bm.verts.new((x, y, z0)) for x, y in inner]
            hi = [bm.verts.new((x, y, z1)) for x, y in inner]
            for i in range(len(inner)):
                j = (i + 1) % len(inner)
                bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
            bm.faces.new(list(reversed(lo)))
            bm.faces.new(hi)
        self.obj("Slabs", bm, (0.6, 0.6, 0.6, 1), "closing slabs; floor plates come with the interior")


def _ring_band(bm, outer, inner, z0, z1):
    """Closed band between two rings with matching vertex order (e.g. a parapet), z0..z1."""
    n = len(outer)
    ob = [bm.verts.new((x, y, z0)) for x, y in outer]
    ot = [bm.verts.new((x, y, z1)) for x, y in outer]
    ib = [bm.verts.new((x, y, z0)) for x, y in inner]
    it = [bm.verts.new((x, y, z1)) for x, y in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((it[i], it[j], ib[j], ib[i]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ib[i], ib[j], ob[j], ob[i]))


def _surround(bm, w, h, l, r, b, t, proj):
    ident = Matrix.Identity(4)
    box(bm, ident, -l, w + r, 0.0, proj, -b, 0.0)          # bottom
    box(bm, ident, -l, w + r, 0.0, proj, h, h + t)         # top
    box(bm, ident, -l, 0.0, 0.0, proj, 0.0, h)             # left
    box(bm, ident, w, w + r, 0.0, proj, 0.0, h)            # right


def _prism_along_w(bm, fr, prof_uz, w0, w1):
    """Extrude a (u, z) profile along w0..w1 (ramps running along the facade)."""
    a = [bm.verts.new(fr @ Vector((u, w0, z))) for u, z in prof_uz]
    b = [bm.verts.new(fr @ Vector((u, w1, z))) for u, z in prof_uz]
    n = len(prof_uz)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)


def clear(gen):
    for ob in [o for o in bpy.data.objects if o.get("koch_gen") == gen]:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def main():
    ids = [s for s in os.environ.get("KOCH_SPECS", "BLD_C").split(",") if s]
    ter = Terrain(load("terrain.json"))
    for bid in ids:
        try:  # one broken or half-written spec must not stop the others
            spec = json.load(open(os.path.join(SPECS, bid + ".json"), encoding="utf-8"))
            b = Building(spec, ter)
            clear(b.gen)
            for name in spec.get("replaces", []):  # phase-1 massing stays in the file, hidden
                ob = bpy.data.objects.get(name)
                if ob:
                    ob.hide_set(True)
                    ob.hide_render = True
            b.build()
        except Exception as ex:
            print(f"{bid}: FAILED {ex!r}")
            continue
        n = sum(1 for o in bpy.data.objects if o.get("koch_gen") == b.gen)
        print(f"{bid}: {n} objects, FFL z={b.ffl:.2f} (ASL {b.ffl + 800:.2f})")
    if bpy.app.background:
        bpy.ops.wm.save_mainfile(compress=True)


main()
