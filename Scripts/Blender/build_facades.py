# Builds phase-2 facade greyboxes (objects GBF_<id>_*) from Art/Blender/Specs/<BLD>.json (walls with real openings and reveals,
# window kit instances, surrounds, pilasters, cornice, plinth, mansard/hip roof, entrance stairs, canopy, ramp,
# light wells, sheds). Used by R1. Idempotent per building: removes objects tagged koch_gen="phase2:<id>".
# Run inside Blender: exec() with KOCH_SPECS="BLD_C" (comma list) or headless:
#   KOCH_SPECS=BLD_C blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_facades.py
# Spec units: metres in the building frame (x along the ring's first edge, y inward/north, z above FFL).
import json
import math
import os
import re
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
                         railing, ring_box, stair_flight, wall_piece, window_unit)
from greybox import detail as D  # noqa: E402
from greybox.materials import ensure_slot, mat, parts_to_mesh  # noqa: E402

MAX_PIECE_M = 12.0   # Lumen SW: keep wall pieces well under ~15 m (distance field / card quality)
BURY_M = 0.3         # walls reach this far below the lowest ground along a facade
EAVE_BOARD = 0.025   # detail eave: soffit lining / fascia board thickness (m)
GUTTER_R = 0.0625    # detail eave: 125 mm half-round gutter radius (m)
GUTTER_DROP = 0.03   # gutter rim below the fascia top (m)

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



# part keyword (in the object name) -> default material slot; order matters (first match wins)
PART_KEYS = ["Glass", "Win", "Sur", "Pilaster", "Cladding", "Plinth", "Slabs", "Roof", "Eave", "Gutter", "Downpipe", "Cornice",
             "Entrance", "Door", "GalleryPosts", "Gallery", "Wall"]
PART_SLOT = {"Glass": "M_Glass", "Win": "M_PVC_White", "Sur": "M_Paint_Maroon", "Pilaster": "M_Paint_Maroon", "Cladding": "M_Render_Beige",
             "Plinth": "M_Tile_Brick_Red", "Slabs": "M_Concrete", "Roof": "M_Sheet_Red", "Eave": "M_PVC_Gutter_White",
             "Gutter": "M_PVC_Gutter_White", "Downpipe": "M_PVC_Gutter_White", "Cornice": "M_Paint_Maroon",
             "Entrance": "M_Alu_Black", "Door": "M_Alu_Black", "GalleryPosts": "M_Steel_Paint_Dark",
             "Gallery": "M_Sheet_Brown", "Wall": "M_Render_Beige"}

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
        # "ffl_z": measured absolute FFL (campus z) where the DEM-based rule is known to be off (e.g. A_W gallery).
        self.ffl = float(spec["ffl_z"]) if "ffl_z" in spec else float(g.max()) + spec["plinth_m"]
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
        self._slot(ob.data, name)
        return ob

    def _slot(self, me, name):
        """P2 material slot (handoff 4a) for a single-colour part: spec "slots" {keyword: M_...} first, then the
        default for the part keyword in its name; detail-kit parts already carry their own slots."""
        if len(me.materials) != 1 or not me.materials[0] or not me.materials[0].name.startswith("VC_"):
            return
        own = self.s.get("slots", {})
        for key in PART_KEYS:
            if re.search(r"(^|_)" + key, name):
                me.materials[0] = mat(own.get(key, PART_SLOT[key]))
                return

    def obj_parts(self, name, parts, item_evidence=None, confidence=None):
        """Link one detail-kit element built from several material parts {material_name: bmesh}."""
        parts = {k: v for k, v in parts.items() if len(v.faces)}
        if not parts:
            return None
        nm = f"GBF_{self.id}_{name}"
        me = parts_to_mesh(nm, parts)
        ob = bpy.data.objects.new(nm, me)
        ob.matrix_world = self.M
        ob["koch_gen"], ob["koch_id"] = self.gen, self.id
        ob["koch_status"] = self.s.get("status", "probable")
        ob["koch_evidence"] = item_evidence or ""
        ob["koch_confidence"] = confidence or ""
        ob.color = COL["low"] if confidence == "low" else tuple(me.materials[0].diffuse_color)  # OBJECT colour view
        self.col.objects.link(ob)
        return ob

    def obj_mat(self, name, bm, mats, item_evidence=None, confidence=None):
        """Link one element whose bmesh faces carry material_index into `mats` (material names)."""
        nm = f"GBF_{self.id}_{name}"
        me = bpy.data.meshes.new(nm)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        for m in mats:
            me.materials.append(mat(m))
        ob = bpy.data.objects.new(nm, me)
        ob.matrix_world = self.M
        ob["koch_gen"], ob["koch_id"] = self.gen, self.id
        ob["koch_status"] = self.s.get("status", "probable")
        ob["koch_evidence"] = item_evidence or ""
        ob["koch_confidence"] = confidence or ""
        ob.color = tuple(me.materials[0].diffuse_color)  # OBJECT colour view
        self.col.objects.link(ob)
        return ob

    def eave_geometry(self):
        """Detail eave levels (local z) and the gutter line offset from the wall face."""
        r = self.s["roof"]
        ov = r.get("overhang", 0.5)
        z_soffit = self.s["eave_z"] - FASCIA_M - EAVE_BOARD
        fh = FASCIA_M + EAVE_BOARD
        z_rim = z_soffit + fh - GUTTER_DROP
        return {"ov": ov, "z_soffit": z_soffit, "fascia_h": fh, "z_rim": z_rim, "w_gutter": ov + GUTTER_R + 0.005}

    def build_eave_detail(self):
        """Boxed eave round the whole ring: soffit + fascia (M_Sheet_Brown), gutter with brackets (M_Steel_Galv)."""
        g = self.eave_geometry()
        soffit, gutter = bmesh.new(), bmesh.new()
        D.eave_box({"soffit": soffit, "gutter": gutter}, self.ring, g["z_soffit"], g["ov"], fascia_h=g["fascia_h"],
                   board_t=EAVE_BOARD, gutter_r=GUTTER_R, gutter_drop=GUTTER_DROP)
        r = self.s["roof"]
        self.obj_parts("Eave", {r.get("eave_material", "M_Sheet_Brown"): soffit}, r.get("evidence"), r.get("confidence"))
        self.obj_parts("Gutter", {r.get("gutter_material", "M_Steel_Galv"): gutter}, r.get("evidence"), r.get("confidence"))

    def corner_cut(self, i, end):
        """Inner-face inset at the start (end=False) or end of edge i: +thk convex, -thk concave (90 deg)."""
        n = len(self.ring)
        a = self.ring[(i - 1) % n] if not end else self.ring[i]
        b = self.ring[i] if not end else self.ring[(i + 1) % n]
        c = self.ring[(i + 1) % n] if not end else self.ring[(i + 2) % n]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        t = self.s["wall_thk"]
        if abs(cross) < 1e-9:  # collinear ring vertex (e.g. C's tower bay flush with a wing): straight butt joint
            return 0.0
        return t if cross > 0 else -t

    def trim_ext(self, i, end, proj):
        """Band (cornice/plinth) extension at an edge end: +proj round a convex corner, -proj into a concave one,
        0 at a collinear vertex (the next edge's band continues flush)."""
        cut = self.corner_cut(i, end)
        return proj if cut > 0 else (-proj if cut < 0 else 0.0)

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
        for ent in ([f["entrance"]] if f.get("entrance") else []) + list(f.get("entrances", [])):
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
            if self.s.get("walls_to_ffl"):  # ground above FFL on some sides (block sunk into a slope / terrain pad)
                z_bottom = min(z_bottom, -BURY_M)
            bsm = self.s.get("basement")
            if bsm:  # walls continue down to the underside of the basement floor slab
                z_bottom = min(z_bottom, bsm["floor_z"] - bsm["slab_t"])
            bands = [(z_bottom, levels[0])] + list(zip(levels[:-1], levels[1:]))
            maroon_face = bool(fspec and fspec.get("name", "").startswith("south_tower"))
            for bi, (z0, z1) in enumerate(bands):
                bo = [(o, wt) for o, _, wt in ops if o.z0 >= z0 - 1e-6 and o.z1 <= z1 + 1e-6]
                # split long bands at wall gaps between openings
                cuts = self._split_points([o for o, _ in bo], L, cut0, cut1)
                for ci, (u0, u1) in enumerate(cuts):
                    inside = [(o, wt) for o, wt in bo if o.u0 >= u0 and o.u1 <= u1]
                    local = [Opening(o.u0 - u0, o.u1 - u0, o.z0, o.z1) for o, _ in inside]
                    fr = e["frame"] @ Matrix.Translation((u0, 0, 0))
                    bm = bmesh.new()
                    reveals = []
                    wall_piece(bm, fr, u1 - u0, z0, z1, thk, local,
                               cut_start=cut0 if abs(u0) < 1e-6 else 0.0,
                               cut_end=cut1 if abs(u1 - L) < 1e-6 else 0.0, reveal_faces=reveals)
                    ev = fspec.get("evidence") if fspec else None
                    if self.s.get("detail"):
                        # painted reveals: the maroon surround paint runs into the opening (photo 061621646 crops)
                        paint = next((wt.get("reveal_paint") for _, wt in inside if wt.get("reveal_paint")), None)
                        if paint is None and any(wt.get("surround") and any(wt["surround"]) for _, wt in inside):
                            paint = "M_Paint_Maroon"
                        base = "M_Paint_Maroon" if maroon_face else self.s.get("wall_material", "M_Render_Beige")
                        for f in reveals:
                            f.material_index = 1 if paint else 0
                        self.obj_mat(f"Wall_E{i}_B{bi}_{ci}", bm, [base, paint or base], ev)
                        continue
                    ob = self.obj(f"Wall_E{i}_B{bi}_{ci}", bm, COL["maroon"] if maroon_face else COL["wall"], ev)
                    ob.data.materials[0] = mat("M_Paint_Maroon" if maroon_face else
                                               self.s.get("wall_material", self.s.get("slots", {}).get("Wall", "M_Render_Beige")))
            self.build_windows(i, ops)
            # optional colour fields of cladding panels (e.g. Block D's maroon/light composite panels): a thin slab
            # `proj` proud of the wall over u0..u1 x z0..z1 with the edge's window openings cut through it
            for ci, c in enumerate(self.s.get("cladding", [])):
                if c["edge"] != i:
                    continue
                cu0, cu1, cz0, cz1, pj = c["u0"], c["u1"], c["z0"], c["z1"], c.get("proj", 0.02)
                holes = [Opening(max(o.u0, cu0) - cu0, min(o.u1, cu1) - cu0, max(o.z0, cz0), min(o.z1, cz1))
                         for o, _, _ in ops if o.u1 > cu0 + 0.05 and o.u0 < cu1 - 0.05 and o.z1 > cz0 + 0.05 and o.z0 < cz1 - 0.05]
                # an opening cut by the field edge would leave a sliver: keep holes strictly inside
                holes = [h for h in holes if h.u0 > 0.02 and h.u1 < cu1 - cu0 - 0.02 and h.z0 > cz0 + 0.02 and h.z1 < cz1 - 0.02]
                bm = bmesh.new()
                wall_piece(bm, e["frame"] @ Matrix.Translation((cu0, pj, 0)), cu1 - cu0, cz0, cz1, pj, holes,
                           cut_start=0.0, cut_end=0.0)
                ob = self.obj(f"Cladding_E{i}_{ci:02d}", bm, COL["wall"], c.get("evidence"), c.get("confidence"))
                ob.data.materials[0] = mat(c.get("slot", "M_Render_Beige"))

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

    def pvc_mesh(self, tname, wt, w, h):
        """Detailed PVC window (greybox/detail.py) for window type tname: frame+sash (PVC), glass, steel sill slots.
        wt['pvc'] overrides PvcWindow fields (measured profiles), wt['sashes'] lists the opening lights."""
        key = f"PVC_{tname}"
        if key in self.kit_meshes:
            return self.kit_meshes[key]
        pv = D.PvcWindow(reveal=wt.get("reveal", 0.16), mullions=wt.get("mullions", []), transoms=wt.get("transoms", []),
                         sashes=wt.get("sashes", []), **wt.get("pvc", {}))
        pvc, glass, sill = bmesh.new(), bmesh.new(), bmesh.new()
        D.pvc_window({"frame": pvc, "sash": pvc, "glass": glass, "sill": sill}, Matrix.Identity(4), Opening(0, w, 0, h), pv)
        me = parts_to_mesh(f"KIT_{self.id}_{key}", {"M_PVC_White": pvc, "M_Glass": glass, "M_Steel_Galv": sill})
        self.kit_meshes[key] = me
        return me

    def build_windows(self, i, ops):
        e = self.edges[i]
        placed = []   # surround extents on this edge (u_lo, u_hi, z_lo, z_hi): neighbours are trimmed to abut, not overlap
        for k, (o, tname, wt) in enumerate(ops):
            if wt.get("open"):   # open bay (pavilion between posts): the hole only, no window unit
                continue
            ident = Matrix.Identity(4)
            w, h = o.u1 - o.u0, o.z1 - o.z0
            if tname == "entrance":
                bays = wt.get("bays")  # [[width_m, "fixed"|"door"], ...] left to right, frame included
                if bays and self.s.get("detail"):
                    sf = D.AluStorefront(reveal=wt.get("reveal", 0.25), bays=bays, transom_z=wt.get("transom_z", h - 0.6),
                                         leaf_mid=wt.get("door_mid_z", 0.0), **wt.get("alu", {}))
                    parts = {k: bmesh.new() for k in ("alu", "glass", "steel", "leaf", "leaf_glass", "leaf_steel")}
                    D.alu_storefront(parts, e["frame"], o, sf)
                    ev, cf = wt.get("evidence"), wt.get("confidence")
                    self.obj_parts(f"Entrance_E{i}_{k:02d}_Frame", {"M_Alu_Black": parts["alu"], "M_Glass": parts["glass"]}, ev, cf)
                    # door leaves: own object so UE can swap them for hinged door actors
                    self.obj_parts(f"Entrance_E{i}_{k:02d}_Doors", {"M_Alu_Black": parts["leaf"], "M_Glass": parts["leaf_glass"],
                                                                    "M_Steel_Galv": parts["leaf_steel"]}, ev, cf)
                    for b in (parts["steel"],):
                        b.free()
                    continue
                if bays:
                    self.build_entrance_doors(i, k, o, wt)
                    continue
                me = self.kit_mesh(f"Entrance_{w:.2f}x{h:.2f}", lambda bm: window_unit(
                    bm, ident, Opening(0, w, 0, h), WindowSpec(reveal=0.25, mullions=[0.25, 0.5, 0.75], transoms=[0.78], sill_proj=0)))
                color = COL["frame"]
            elif self.s.get("detail"):
                me = self.pvc_mesh(tname, wt, w, h)
                color = COL["frame"]
            else:
                spec = WindowSpec(reveal=wt.get("reveal", 0.16), mullions=wt.get("mullions", []), transoms=wt.get("transoms", []))
                me = self.kit_mesh(f"Window_{tname}", lambda bm: window_unit(bm, ident, Opening(0, w, 0, h), spec))
                color = COL["frame"]
            place = self.M @ e["frame"] @ Matrix.Translation((o.u0, 0, o.z0))
            self._link(f"Win_E{i}_{k:02d}", me, place, color)
            sw = wt.get("surround") if tname != "entrance" else None
            if sw and any(sw) and wt.get("surround_proj", 0.04) > 0:
                l, r, b, t = sw
                proj = wt.get("surround_proj", 0.04)
                for a0, a1, z0_, z1_ in placed:   # adjacent surrounds of one row overlapped: coplanar fronts (z-fight)
                    if z0_ < o.z1 + t and z1_ > o.z0 - b:
                        if a0 < o.u0 - l < a1 <= o.u0:
                            l = o.u0 - a1
                        if o.u1 <= a0 < o.u1 + r < a1:
                            r = a0 - o.u1
                placed.append((o.u0 - l, o.u1 + r, o.z0 - b, o.z1 + t))
                me2 = self.kit_mesh(f"Surround_{tname}" + ("" if [l, r] == list(sw[:2]) else f"_{round(l * 1000)}_{round(r * 1000)}"),
                                    lambda bm: _surround(bm, w, h, l, r, b, t, proj))
                if self.s.get("detail") and not me2.materials:
                    me2.materials.append(mat(wt.get("reveal_paint", "M_Paint_Maroon")))
                self._link(f"Sur_E{i}_{k:02d}", me2, place, COL["maroon"])

    def build_stair_extras(self, a, fr, cf):
        """Optional stair side cheeks (solid blocks with a top sloping from the landing to the plaza) and handrails.
        cheeks: [{"u0", "u1", "w1" (outer end, m from the wall), "z_wall", "z_out"}]  (z rel FFL)
        handrails: [{"u": u, "h": 0.9}] along the flight nosing line, from the landing edge to the bottom step."""
        H = a["risers"] * a["riser_h"]
        zb = -H
        for n, c in enumerate(a.get("cheeks", [])):
            bm = bmesh.new()
            prism_profile(bm, fr, [(0.0, zb - 0.2), (0.0, c["z_wall"]), (c["w1"], c["z_out"]), (c["w1"], zb - 0.2)],
                          c["u0"], c["u1"])
            self.obj(f"StairCheek_E{a['edge']}_{n}", bm, COL["granite"], c.get("evidence", a.get("evidence")), c.get("confidence", cf))
        rails = a.get("handrails", [])
        if rails:
            bm = bmesh.new()
            w_top = a["landing"]
            w_bot = a["landing"] + (a["risers"] - 1) * a["tread"]
            for r in rails:
                pts = [fr @ Vector((r["u"], w_top - 0.3, 0.0)), fr @ Vector((r["u"], w_top, 0.0)),
                       fr @ Vector((r["u"], w_bot, zb + a["riser_h"])), fr @ Vector((r["u"], w_bot + 0.3, zb + a["riser_h"]))]
                railing(bm, pts, height=r.get("h", 0.9), spacing=1.6, mid_rails=r.get("mid_rails", 0))
            self.obj(f"StairRail_E{a['edge']}", bm, COL["metal"], a.get("evidence"), cf)

    def build_entrance_doors(self, i, k, o, ent):
        """Aluminium glazed entrance: outer frame, bay mullions, transom, glass, and per door bay a leaf frame,
        optional mid rail and a pull bar (doors are separate objects so UE can swap in hinged actors)."""
        fr = self.edges[i]["frame"]  # obj() applies self.M
        rev = ent.get("reveal", 0.25)
        fw, fd = ent.get("frame_w", 0.06), ent.get("frame_d", 0.08)
        w1, w0 = -rev, -rev - fd
        zt = ent.get("transom_z", o.z1 - 0.6)   # underside of the transom bar (m above FFL)
        bm = bmesh.new()
        ring_box(bm, fr, o.u0 + fw, o.u1 - fw, o.z0 + fw, o.z1 - fw, fw, w0, w1)
        box(bm, fr, o.u0 + fw, o.u1 - fw, w0, w1, zt, zt + fw)
        u = o.u0
        widths = [b[0] for b in ent["bays"]]
        sc = (o.u1 - o.u0) / sum(widths)  # bays are measured widths: rescale so they fill the opening exactly
        bm_d, bm_g = bmesh.new(), bmesh.new()
        for bw, kind in ent["bays"]:
            ua, ub = u, u + bw * sc
            if ub < o.u1 - 1e-3:
                box(bm, fr, ub - fw / 2, ub + fw / 2, w0, w1, o.z0 + fw, zt)
            if kind == "door":
                lw = 0.055  # leaf stile/rail width
                ring_box(bm_d, fr, ua + fw / 2 + lw + 0.005, ub - fw / 2 - lw - 0.005, o.z0 + 0.01 + lw, zt - 0.01 - lw, lw,
                         w0 + 0.01, w1 - 0.01)
                zm = ent.get("door_mid_z")  # optional leaf mid rail (only where a photo shows one)
                if zm:
                    box(bm_d, fr, ua + fw / 2 + 0.01, ub - fw / 2 - 0.01, w0 + 0.01, w1 - 0.01, zm - 0.05, zm + 0.05)
                hu = ub - fw / 2 - 0.12 if ent.get("hinge", "left") == "left" else ua + fw / 2 + 0.12
                box(bm_d, fr, hu - 0.015, hu + 0.015, w1 - 0.01, w1 + 0.05, 0.8, 1.6)  # vertical pull bar
            gm = (w0 + w1) / 2
            box(bm_g, fr, ua + fw / 2, ub - fw / 2, gm - 0.006, gm + 0.006, o.z0 + fw, zt)
            u = ub
        box(bm_g, fr, o.u0 + fw, o.u1 - fw, (w0 + w1) / 2 - 0.006, (w0 + w1) / 2 + 0.006, zt + fw, o.z1 - fw)
        self.obj(f"Entrance_E{i}_{k:02d}_Frame", bm, COL["frame"], ent.get("evidence"), ent.get("confidence"))
        self.obj(f"Entrance_E{i}_{k:02d}_Doors", bm_d, COL["frame"], ent.get("evidence"), ent.get("confidence"))
        self.obj(f"Entrance_E{i}_{k:02d}_Glass", bm_g, COL.get("glass", COL["frame"]), ent.get("evidence"), ent.get("confidence"))

    def _link(self, name, me, matrix, color):
        ensure_slot(me, color)
        self._slot(me, name)
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
            z0, z1 = c["z0"], c["z1"]
            r = self.s["roof"]
            if r.get("type", "hip") not in ("flat", "none") and r.get("overhang", 0.0) >= c["proj"]:
                # the roof's fascia band (eave_z - FASCIA_M .. eave_z) already covers the wall head: keep only the
                # part below its soffit, else the cornice is buried in the roof with its underside coplanar to it
                z1 = min(z1, self.s["eave_z"] - FASCIA_M)
            if c["proj"] > 0.005 and z1 - z0 > 0.01:
                bm_c = bmesh.new()
                for i, e in enumerate(self.edges):
                    ext0 = self.trim_ext(i, False, c["proj"])
                    ext1 = self.trim_ext(i, True, c["proj"])
                    box(bm_c, e["frame"], -ext0, e["L"] + ext1, 0.0, c["proj"], z0, z1)
                self.obj("Cornice", bm_c, COL["maroon"], c.get("evidence", "cornice band under the eaves"), c.get("confidence"))
        if pl and pl["proj"] > 0.005:
            bm_pl = bmesh.new()
            for i, e in enumerate(self.edges):
                p0 = self.trim_ext(i, False, pl["proj"])
                p1 = self.trim_ext(i, True, pl["proj"])
                # the band stops at door openings (a continuous band walled up every entrance up to z_top)
                cuts = sorted((o.u0, o.u1, False) for o, tn, _w in self.openings_for(i)[0] if tn == "entrance" or o.z0 < pl["z_top"])
                # "skip": {edge: [[u0, u1], ...]} spans against a neighbouring building (party walls): no band there,
                # it would run inside the neighbour with its faces on the neighbour's wall faces
                cuts = sorted(cuts + [(u0, u1, True) for u0, u1 in pl.get("skip", {}).get(str(i), [])])
                a = -p0
                for c0, c1, party in cuts + [(e["L"] + p1, e["L"] + p1, False)]:
                    if c0 - a > 0.01:
                        box(bm_pl, e["frame"], a, c0, 0.0, pl["proj"], e["zg"] - 0.05, pl["z_top"])
                    if c1 - c0 > 0.01 and e["zg"] < -0.07 and not party:   # under a door: band up to 2 cm below the threshold
                        box(bm_pl, e["frame"], c0, c1, 0.0, pl["proj"], e["zg"] - 0.05, min(-0.02, pl["z_top"]))
                    a = max(a, c1)
            self.obj("Plinth", bm_pl, COL["plinth"], pl.get("evidence", "brick-tile plinth"), pl.get("confidence"))
        for k, p in enumerate(self.s.get("pilasters", [])):
            e = self.edges[p["edge"]]
            z0 = p["z0"]
            if pl and p["proj"] < pl["proj"] + 0.016:  # plinth as proud as the pilaster: start on its top (no coplanar fronts)
                z0 = max(z0, pl["z_top"])
            elif pl and abs(z0 - pl["z_top"]) < 0.002:  # prouder pilaster standing on the plinth top: sink 2 cm into it
                z0 = pl["z_top"] - 0.02
            bm_p = bmesh.new()
            box(bm_p, e["frame"], p["u0"], p["u1"], 0.0, p["proj"], z0, p["z1"])
            self.obj(f"Pilaster_E{p['edge']}_{k:02d}", bm_p, COL["maroon"], p.get("evidence", "pilaster"), p.get("confidence"))

    # ------------------------------------------------------------------ roof
    def build_roof(self):
        r = self.s["roof"]
        kind = r.get("type", "hip")
        if kind == "none":
            return
        if kind == "flat":
            return self.build_flat_roof(r)
        if self.s.get("detail") and kind == "hip" and not r.get("overhang_edges") and not r.get("_eave_done"):
            # detail eave: the fascia board is its own part, so the roof solid stops just inside it (no coplanar
            # faces); built once per roof, the recursion below uses the shortened overhang
            self.s["roof"] = dict(r, overhang=r["overhang"] - EAVE_BOARD - 0.003, _eave_done=True)
            try:
                self.build_roof()
            finally:
                self.s["roof"] = r
            self.build_eave_detail()
            return
        if kind in ("gable", "shed"):
            return self.build_gable_or_shed(r, kind)
        if kind == "hip" and r.get("ridge_len") and len(self.ring) == 4:
            return self.build_rect_hip(r)
        z0 = self.s["eave_z"]
        ov = r["overhang"]
        if r.get("overhang_edges"):  # per-edge overrides {"edge": m}, e.g. 0 against a taller neighbour's wall
            ov = [float(r["overhang_edges"].get(str(i), ov)) for i in range(len(self.ring))]
        neg = [-v for v in ov] if isinstance(ov, list) else -ov
        outline = _drop_collinear(offset_ring(self.ring, neg))  # straight skeleton needs true corners
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
            # starts on the wall top (no coplanar overlap band) and sits 1 cm inside the outer faces: where a wall rises
            # above the eave (gable/parapet bays) its face and the infill face were coplanar (zaudit 2026-10-01)
            cx, cy = sum(p[0] for p in self.ring) / len(self.ring), sum(p[1] for p in self.ring) / len(self.ring)
            ins = [(x + 0.01 * (cx - x) / max(math.hypot(cx - x, cy - y), 1e-6) * 1.4142,
                    y + 0.01 * (cy - y) / max(math.hypot(cx - x, cy - y), 1e-6) * 1.4142) for x, y in self.ring]
            lo = [bm2.verts.new((x, y, z0)) for x, y in ins]
            up = [bm2.verts.new((x, y, zt((x, y)) - FASCIA_M + 0.01)) for x, y in ins]
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
    def build_attachment_detail(self, a, e, fr):
        """Detail-kit versions of the attachments (spec 'detail': true). Returns False for types without one."""
        t, cf, ev = a["type"], a.get("confidence"), a.get("evidence")
        if t == "downpipe":
            # round pipe (d = diameter), clamps every ~1.5 m, swan neck from the eave gutter outlet back to the wall,
            # kick-out shoe at the foot; 'top': 'gutter' (default) or 'free' (ends at z1 against the wall)
            g = self.eave_geometry()
            r = a.get("d", 0.09) / 2
            w_wall = a.get("off", 0.04) + r
            steel = bmesh.new()
            for u in a["u"]:
                pts = []
                if a.get("top", "gutter") == "gutter":
                    zo = g["z_rim"] - GUTTER_R - 0.02
                    pts += [fr @ Vector((u, g["w_gutter"], g["z_rim"] - GUTTER_R * 0.5)), fr @ Vector((u, g["w_gutter"], zo - 0.1))]
                    pts += [fr @ Vector((u, w_wall, zo - 0.1 - (g["w_gutter"] - w_wall) * 1.0))]
                else:
                    pts.append(fr @ Vector((u, w_wall, a["z1"])))
                foot = a["z0"]
                pts += [fr @ Vector((u, w_wall, foot + 0.3)), fr @ Vector((u, w_wall + 0.18, foot + 0.1))]
                D.tube(steel, pts, r, seg=16, bend_r=0.1)
                z_top = pts[-3].z if len(pts) >= 3 else a["z1"]
                n = max(1, int((z_top - foot - 0.6) / 1.5))
                for k in range(n + 1):
                    zc = foot + 0.5 + (z_top - foot - 1.0) * k / max(n, 1)
                    D.ring_clamp(steel, fr @ Vector((u, w_wall, zc)), fr.to_3x3() @ Vector((0, 0, 1)), r)
                    box(steel, fr, u - 0.01, u + 0.01, 0.0, w_wall - r, zc - 0.012, zc + 0.012)  # clamp stem to the wall
            self.obj_parts(f"Downpipe_E{a['edge']}_{a['u'][0]:.0f}", {a.get("material", "M_PVC_Gutter_White"): steel}, ev, cf)
            return True
        if t == "stairs":
            H = a["risers"] * a["riser_h"]
            stone = bmesh.new()
            D.stone_stair(stone, fr, a["u0"], a["u1"], a["risers"], a["riser_h"], a["tread"], a["landing"], 0.0,
                          w_back=-0.05, nosing=a.get("nosing", 0.02))
            self.obj_parts(f"Stairs_E{a['edge']}_{a['u0']:.0f}", {"M_Granite_Red": stone}, ev, cf)
            for n, c in enumerate(a.get("cheeks", [])):
                body, cap = bmesh.new(), bmesh.new()
                ct = c.get("cap_t", 0.04)
                ov = c.get("cap_over", 0.02)
                zb = -H - 0.2
                # optional knee: level top from the wall to w_knee (along the landing), then the slope to w1
                # w0: where the cheek starts (e.g. at a wing face in front of a recessed tower)
                w0 = c.get("w0", 0.0)
                wk = max(c.get("w_knee", 0.0), w0)
                sl = (c["z_wall"] - c["z_out"]) / (c["w1"] - wk)
                top = [(w0, c["z_wall"])] + ([(wk, c["z_wall"])] if wk > w0 else []) + [(c["w1"], c["z_out"])]
                prism_profile(body, fr, [(w0, zb)] + [(w, z - ct) for w, z in top] + [(c["w1"], zb)], c["u0"], c["u1"])
                capb = [(w, z - ct) for w, z in top[:-1]] + [(c["w1"] + ov, c["z_out"] - ct - ov * sl)]
                capt = [(c["w1"] + ov, c["z_out"] - ov * sl)] + top[-2::-1]
                prism_profile(cap, fr, capb + capt, c["u0"] - ov, c["u1"] + ov)
                self.obj_parts(f"StairCheek_E{a['edge']}_{n}", {c.get("material", "M_Tile_Brick_Red"): body, "M_Granite_Red": cap},
                               c.get("evidence", ev), c.get("confidence", cf))
            return True
        if t == "ramp":
            parts = {"frame": bmesh.new(), "deck": bmesh.new()}
            zg = a["z_low"]
            ground = lambda u: a.get("z_ground", zg)
            if a.get("along") == "w":
                # ramp running out from the wall (u0/u1 = distances from the wall, w0/w1 = -u along the wall):
                # frame turned +90 deg about z, so (u', w') -> (u = -w', w = u')
                fr = fr @ Matrix.Rotation(math.radians(90.0), 4, "Z")
                st = a.get("over_stairs")
                if st:
                    # legs stand on the flight it is laid over: landing, treads, then the plaza
                    s_ = next(x for x in self.s["attachments"] if x["type"] == "stairs" and x["edge"] == a["edge"])
                    L_, t_, h_, n_ = s_["landing"], s_["tread"], s_["riser_h"], s_["risers"]
                    ground = lambda w: 0.0 if w <= L_ else -min(n_, 1 + int((w - L_) / t_)) * h_
            D.steel_ramp(parts, fr, a["u0"], a["u1"], a["w0"], a["w1"], a["z_high"], a["z_low"], ground=ground)
            rails = bmesh.new()
            if a.get("rails"):
                sides = {"both": (a["w0"] + 0.03, a["w1"] - 0.03), "w0": (a["w0"] + 0.03,), "w1": (a["w1"] - 0.03,)}
                for w in sides[a.get("rail_sides", "both")]:
                    pts = [fr @ Vector((a["u0"], w, a["z_high"])), fr @ Vector((a["u1"], w, a["z_low"]))]
                    D.railing_detailed(rails, pts, height=a.get("rail_h", 0.9), post=0.04, spacing=a.get("post_pitch", 1.5),
                                       mid=tuple(a.get("mid_rails", [0.45])), base_plate=0.0, plate_t=0.0)
                for ue in a.get("rail_ends", []):   # guard across an open end ("u0"/"u1"), e.g. the top plate's outer edge
                    u_, z_ = (a["u0"] + 0.03, a["z_high"]) if ue == "u0" else (a["u1"] - 0.03, a["z_low"])
                    pts = [fr @ Vector((u_, a["w0"] + 0.03, z_)), fr @ Vector((u_, a["w1"] - 0.03, z_))]
                    D.railing_detailed(rails, pts, height=a.get("rail_h", 0.9), post=0.04, spacing=a.get("post_pitch", 1.5),
                                       mid=tuple(a.get("mid_rails", [0.45])), base_plate=0.0, plate_t=0.0)
            nm = a.get("name", "")
            self.obj_parts(f"Ramp{nm}_E{a['edge']}", {"M_Steel_Paint_Dark": parts["frame"], "M_Steel_Grating": parts["deck"]}, ev, cf)
            if a.get("rails"):
                self.obj_parts(f"RampRail{nm}_E{a['edge']}", {"M_Steel_Paint_Dark": rails}, ev, cf)
            return True
        if t == "canopy":
            parts = {k: bmesh.new() for k in ("frame", "panel", "soffit", "roof")}
            s = a.get("sign", {})
            D.canopy_box(parts, fr, a["u0"], a["u1"], a["depth"], a.get("z_soffit_wall", a["z0"]), a["z0"],
                         s.get("z1", a["z1"]), sign_frame=s.get("frame", 0.05), panel=a.get("panel", 0.6))
            self.obj_parts(f"Canopy_E{a['edge']}", {"M_Sign_Frame_White": parts["frame"], "M_Terracotta_Soffit": parts["soffit"],
                                                    "M_Sheet_Brown": parts["roof"]}, ev, cf)
            self.obj_parts(f"CanopySign_E{a['edge']}", {"M_Sign_Panel": parts["panel"]}, ev, cf)
            return True
        if t == "floodlight":
            bm = bmesh.new()
            for u in a["u"]:
                D.floodlight(bm, fr, u, a.get("w", 0.35), a["z"])
            self.obj_parts(f"Flood_E{a['edge']}_{a['u'][0]:.0f}", {"M_Alu_Black": bm}, ev, cf)
            return True
        if t == "wall_boxes" and a.get("kind", _box_kind(a.get("name", ""))) in ("ac", "cctv", "lamp", "vent", "sign"):
            # items [u, z, w, h, d]: z = underside; detail kit per kind (AC outdoor unit on brackets, CCTV, lamp, ...)
            kind = a.get("kind", _box_kind(a.get("name", "")))
            w0 = a.get("w0", 0.0)
            fr_w = fr @ Matrix.Translation((0.0, w0, 0.0))
            p = {"casing": bmesh.new(), "steel": bmesh.new(), "body": bmesh.new(), "diffuser": bmesh.new(),
                 "frame": bmesh.new(), "slats": bmesh.new(), "plate": bmesh.new(), "pins": bmesh.new()}
            for u, zb, bw, bh, bd in a["items"]:
                if kind == "ac":
                    D.ac_unit(p, fr_w, u, zb, w=bw, h=bh, d=bd, off=a.get("off", 0.12))
                elif kind == "cctv":
                    D.cctv_camera(p, fr_w, u, zb + bh / 2, arm=max(0.12, bd))
                elif kind == "lamp":
                    D.wall_lamp(p, fr_w, u, zb + bh / 2, w=bw, h=bh, d=bd)
                elif kind == "vent":
                    D.vent_grille(p, fr_w, u - bw / 2, u + bw / 2, zb, zb + bh)
                else:
                    D.sign_plate(p, fr_w, u - bw / 2, u + bw / 2, zb, zb + bh)
            mats = {"ac": {"M_AC_Casing": p["casing"], "M_Steel_Paint_Dark": p["steel"]},
                    "cctv": {"M_Plastic_White": p["body"]},
                    "lamp": {"M_Alu_Black": p["body"], "M_Lamp_Diffuser": p["diffuser"]},
                    "vent": {"M_Alu_Grey": p["frame"], "M_Alu_Grey_Slats": p["slats"]},
                    "sign": {"M_Sign_Panel": p["plate"], "M_Steel_Galv": p["pins"]}}[kind]
            self.obj_parts(f"{a.get('name', kind)}_E{a['edge']}", mats, ev, cf)
            return True
        if t == "lightwell":
            sheet = bmesh.new()
            D.corrugated_sheet(sheet, fr, a["u0"], a["u1"], 0.0, a["z_wall"], a["depth"] + 0.05, a["z_edge"] - 0.03,
                               pitch=a.get("rib_pitch", 0.2), rib_h=a.get("rib_h", 0.021))
            parts = {"M_Sheet_Red": sheet}
            pp = a.get("parapet")
            if pp:
                bm_p = bmesh.new()
                for u0, u1 in pp["spans"]:
                    box(bm_p, fr, u0, u1, a["depth"] - pp.get("t", 0.25), a["depth"], pp["z0"], a["z_edge"] - 0.06)
                self.obj_parts(f"LightwellParapet_E{a['edge']}_{a['u0']:.0f}", {"M_Tile_Brick_Red": bm_p}, pp.get("evidence"), cf)
            self.obj_parts(f"LightwellCover_E{a['edge']}_{a['u0']:.0f}", parts, ev, cf)
            return True
        return False

    def build_attachments(self):
        for a in self.s.get("attachments", []):
            e = self.edges[a["edge"]]
            fr = e["frame"]
            t = a["type"]
            if self.s.get("detail") and self.build_attachment_detail(a, e, fr):
                continue
            bm = bmesh.new()
            cf = a.get("confidence")
            if t == "stairs":
                stair_flight(bm, fr, a["u0"], a["u1"], a["risers"], a["riser_h"], a["tread"], a["landing"],
                             z_base=-a["risers"] * a["riser_h"])
                self.obj(f"Stairs_E{a['edge']}_{a['u0']:.0f}", bm, COL["granite"], a.get("evidence"), cf)
                self.build_stair_extras(a, fr, cf)
            elif t == "gallery":
                self.build_gallery(a, e, fr)
            elif t == "wall_boxes":  # small wall-mounted boxes (AC outdoor units, junction boxes): items [u, z, w, h, d]
                w0 = a.get("w0", 0.0)  # face offset along the outward normal (m; <0 = on a wall behind this edge)
                for u, zb, bw, bh, bd in a["items"]:
                    box(bm, fr, u - bw / 2, u + bw / 2, w0, w0 + bd, zb, zb + bh)
                ob = self.obj(f"{a.get('name', 'WallBoxes')}_E{a['edge']}", bm, COL["frame"], a.get("evidence"), cf)
                if a.get("slot"):                      # explicit material slot (AHU, ladders, ...)
                    ob.data.materials[0] = mat(a["slot"])
            elif t == "downpipe":  # rainwater downpipe: square-ish section d, off the wall by `off`, z0..z1 rel FFL
                d, off = a.get("d", 0.1), a.get("off", 0.04)
                for u in a["u"]:
                    box(bm, fr, u - d / 2, u + d / 2, off, off + d, a["z0"], a["z1"])
                self.obj(f"Downpipe_E{a['edge']}_{a['u'][0]:.0f}", bm, COL["frame"], a.get("evidence"), cf)
            elif t == "floodlight":  # small wall/sign-mounted flood lamps: box heads on short arms
                for u in a["u"]:
                    box(bm, fr, u - 0.12, u + 0.12, a.get("w", 0.35), a.get("w", 0.35) + 0.12, a["z"], a["z"] + 0.18)
                self.obj(f"Flood_E{a['edge']}_{a['u'][0]:.0f}", bm, COL["metal"], a.get("evidence"), cf)
            elif t == "wall_sign":  # lettering/logo panel on the wall face (content = KOCH branding later)
                w0 = a.get("w0", 0.0)  # face offset along the outward normal (m; <0 = on a wall behind this edge)
                box(bm, fr, a["u0"], a["u1"], w0, w0 + a.get("t", 0.08), a["z0"], a["z1"])
                self.obj(f"Sign_{a.get('name', a['u0'])}", bm, COL[a.get("color", "sign")], a.get("evidence"), cf)
            elif t == "stair_well":
                self.build_stair_well(a, e, fr)
            elif t == "porch":
                self.build_porch(a, e, fr)
            elif t == "interior":
                self.build_interior(a)
                bm.free()
            elif t == "glazed_porch":
                self.build_glazed_porch(a, e, fr)
                bm.free()
            elif t == "post_canopy":
                self.build_post_canopy(a, e, fr)
                bm.free()
            elif t == "canopy":
                box(bm, fr, a["u0"], a["u1"], 0.0, a["depth"], a["z0"], a["z1"])
                s = a.get("sign")
                if s:  # sign box on the canopy front: own object (content = KOCH branding in UE)
                    bm_s = bmesh.new()
                    box(bm_s, fr, a["u0"], a["u1"], a["depth"] - s["t"], a["depth"], a["z1"], s["z1"])
                    self.obj(f"CanopySign_E{a['edge']}", bm_s, COL["sign"], a.get("evidence"))
                self.obj(f"Canopy_E{a['edge']}" + (f"_{a['name']}" if a.get("name") else ""), bm, COL["canopy"], a.get("evidence"))
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
            elif t == "lightwell" and a.get("box"):
                # box cover (vertical front, flat top at z_wall) down to the ground; "wrap" {edge, u1} continues it
                # round the corner at this edge's u1 as ONE L solid (no shared/coplanar faces at the corner)
                d = a["depth"]
                pts = [fr @ Vector((a["u0"], 0.0, 0.0)), fr @ Vector((a["u0"], d, 0.0))]
                zb = e["zg"]
                wr = a.get("wrap")
                if wr:
                    e2 = self.edges[wr["edge"]]
                    f2 = e2["frame"]
                    zb = min(zb, e2["zg"])
                    pts += [f2 @ Vector((-d, d, 0.0)), f2 @ Vector((wr["u1"], d, 0.0)), f2 @ Vector((wr["u1"], 0.0, 0.0)),
                            f2 @ Vector((0.0, 0.0, 0.0))]
                else:
                    pts += [fr @ Vector((a["u1"], d, 0.0)), fr @ Vector((a["u1"], 0.0, 0.0))]
                zb -= BURY_M
                lo = [bm.verts.new((p.x, p.y, zb)) for p in pts]
                hi = [bm.verts.new((p.x, p.y, a["z_wall"])) for p in pts]
                n = len(pts)
                for i in range(n):
                    j = (i + 1) % n
                    bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
                bm.faces.new(list(reversed(lo)))
                bm.faces.new(hi)
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
                self.obj(f"LightwellCover_E{a['edge']}_{a['u0']:.0f}", bm, COL["maroon"], a.get("evidence"))
            elif t == "lightwell":
                prism_profile(bm, fr, [(0.0, a["z_wall"]), (a["depth"], a["z_edge"]), (a["depth"], a["z_edge"] - 0.06),
                                       (0.0, a["z_wall"] - 0.06)], a["u0"], a["u1"])
                self.obj(f"LightwellCover_E{a['edge']}_{a['u0']:.0f}", bm, COL["maroon"], a.get("evidence"))
                pp = a.get("parapet")  # optional low tile parapet the cover's outer edge rests on (z rel FFL)
                if pp:
                    bm_p = bmesh.new()
                    for u0, u1 in pp["spans"]:
                        box(bm_p, fr, u0, u1, a["depth"] - pp.get("t", 0.25), a["depth"], pp["z0"], a["z_edge"] - 0.06)
                    self.obj(f"LightwellParapet_E{a['edge']}_{a['u0']:.0f}", bm_p, COL["brick"], pp.get("evidence"), cf)
            elif t == "shed":
                zg = e["zg"]
                zg = a.get("z_base", zg - BURY_M) + BURY_M  # explicit base where a terrain pad lowers the ground
                if a.get("roof_only"):  # open roof over an entry: only the roof sheet below
                    pass
                elif a.get("hollow"):  # interior modelled separately (INT_* spec): roof deck + outer wall only
                    zb = a.get("z_floor", zg - BURY_M)
                    wt = a.get("wall_t", 0.3)
                    prism_profile(bm, fr, [(a["depth"] - wt, zb), (a["depth"] - wt, a["z_low"] - 0.02),
                                           (a["depth"], a["z_low"] - 0.02), (a["depth"], zb)], a["u0"], a["u1"])
                    prism_profile(bm, fr, [(0.0, a["z_high"] - 0.3), (0.0, a["z_high"]), (a["depth"], a["z_low"]),
                                           (a["depth"], a["z_low"] - 0.3)], a["u0"], a["u1"])  # roof deck under the sheet
                else:
                    prof = [(0.0, zg - BURY_M), (0.0, a["z_high"]), (a["depth"], a["z_low"]), (a["depth"], zg - BURY_M)]
                    prism_profile(bm, fr, prof, a["u0"], a["u1"])
                bm2 = bmesh.new()  # corrugated roof sheet, 0.15 m overhang on three sides
                prism_profile(bm2, fr, [(0.0, a["z_high"] + 0.01), (a["depth"] + 0.15, a["z_low"] - 0.01),
                                        (a["depth"] + 0.15, a["z_low"] + 0.05), (0.0, a["z_high"] + 0.07)],
                              a["u0"] - 0.15, a["u1"] + 0.15)
                if not a.get("roof_only"):
                    self.obj(a["name"], bm, COL["brick"], a.get("evidence"))
                self.obj(a["name"] + "_Roof", bm2, COL["roof"] if a.get("roof_only") else COL["metal"], a.get("evidence"))
            elif t == "stair_box":
                zg = a.get("z_base", e["zg"] - BURY_M) + BURY_M
                box(bm, fr, a["u0"], a["u1"], a.get("w0", 0.0), a["depth"], zg - BURY_M, a["z_top"])
                cn = a.get("canopy")
                bm2 = bmesh.new()
                if cn:
                    box(bm2, fr, cn["u0"], cn["u1"], cn.get("w0", 0.0), cn["depth"], cn["z"], cn["z"] + 0.12)
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
        inset = a.get("post_inset", 0.0)          # post centre this far inside the deck edge (m)
        for u in a.get("posts_u", []):
            zp0 = zb - (0.0 if "floor_z" in a else BURY_M)
            if a.get("post_round"):                # round steel tube, diameter post_w
                wc = dep - inset - pw / 2 if inset else dep - pd / 2
                bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=pw / 2, radius2=pw / 2,
                                      depth=zu - bh - zp0, matrix=fr @ Matrix.Translation((u, wc, (zp0 + zu - bh) / 2)))
            else:
                box(bm, fr, u - pw / 2, u + pw / 2, dep - pd - inset, dep - inset, zp0, zu - bh)
        self.obj(f"GalleryPosts_{tag}", bm, COL["post"], ev, cf)
        self.build_gallery_extras(a, fr, tag, ev, cf)
        bm = bmesh.new()
        if bh > 1e-3:   # beam_h 0 = no edge beam (a zero-height box is 4 zero-area faces)
            box(bm, fr, u0, u1, dep - pd - 0.02, dep + 0.02, zu - bh, zu)
        oh = a.get("roof_overhang", 0.15)
        if a.get("wedge"):  # lean-to with a flat boarded soffit: solid wedge from the wall (zu+fall+thk) to the eave (zu+thk)
            prism_profile(bm, fr, [(0.0, zu), (dep + oh, zu), (dep + oh, zu + thk), (0.0, zu + fall + thk)], u0 - oh, u1 + oh)
        else:
            prism_profile(bm, fr, [(0.0, zu + fall), (dep + oh, zu - oh * fall / max(dep, 1e-3)),
                                   (dep + oh, zu - oh * fall / max(dep, 1e-3) + thk), (0.0, zu + fall + thk)], u0 - oh, u1 + oh)
        self.obj(f"GalleryRoof_{tag}", bm, COL["roof"], ev, cf)
        if "floor_z" in a:
            bm = bmesh.new()
            cp = a.get("coping")  # {"t", "proj", "w"}: stone coping band on the exposed deck edge (front + both ends)
            zt = a["floor_z"] - (cp["t"] if cp else 0.0)
            dd = dep + a.get("deck_extra", 0.0)   # deck edge beyond the post/beam line (m)
            box(bm, fr, u0, u1, 0.0, dd, a.get("deck_bottom", e["zg"] - BURY_M), zt)
            self.obj(f"GalleryDeck_{tag}", bm, COL["brick"] if cp else COL["granite"], ev, cf)
            if cp:
                t, pr, cw = cp["t"], cp.get("proj", 0.03), cp.get("w", 0.3)
                bm = bmesh.new()
                box(bm, fr, u0 - pr, u1 + pr, dd - cw, dd + pr, zt, a["floor_z"])
                box(bm, fr, u0 - pr, u0 + cw, 0.0, dd - cw, zt, a["floor_z"])
                box(bm, fr, u1 - cw, u1 + pr, 0.0, dd - cw, zt, a["floor_z"])
                self.obj(f"GalleryCoping_{tag}", bm, COL["granite"], ev, cf)
                bm = bmesh.new()  # deck paving (ornamental concrete tiles) between wall and coping, 2 cm proud of the body
                box(bm, fr, u0 + cw, u1 - cw, 0.0, dd - cw, zt, a["floor_z"])
                self.obj(f"GalleryFloor_{tag}", bm, (0.62, 0.60, 0.58, 1), ev, cf)

    def build_gallery_extras(self, a, fr, tag, ev, cf):
        """Optional gallery parts: flat boarded soffit ('soffit_z', timber), eaves gutter and downpipes ('gutter',
        'downpipes_u'). Gallery frame: u along the wall, w outward from the wall face, z above FFL (m)."""
        u0, u1, dep = a["u0"], a["u1"], a["depth"]
        zu, bh, pd = a["z_underside"], a.get("beam_h", 0.3), a.get("post_d", a.get("post_w", 0.3))
        if "soffit_z" in a:
            bm = bmesh.new()
            box(bm, fr, u0, u1, 0.0, dep - pd - 0.02, a["soffit_z"], a["soffit_z"] + a.get("soffit_t", 0.03))
            self.obj(f"GallerySoffit_{tag}", bm, (0.55, 0.36, 0.20, 1), ev, cf)
        if a.get("end_boards"):   # opt-in: close the gallery ends between the soffit/beam and the sloped roof (fascia
            # board flush with the beam ends; without it the roof underside shows as an open wedge at each end)
            oh, fall = a.get("roof_overhang", 0.15), a.get("roof_fall", 0.0)
            zs = a.get("soffit_z", zu - bh)
            prof = [(0.0, zs), (dep + 0.02, zs), (dep + 0.02, zu - 0.02 * fall / max(dep, 1e-3)), (0.0, zu + fall)]
            bm = bmesh.new()
            for ua, ub in ((u0 - 0.03, u0), (u1, u1 + 0.03)):
                prism_profile(bm, fr, prof, ua, ub)
            self.obj(f"GalleryEnds_{tag}", bm, COL["frame"], ev, cf)
        if a.get("gutter") or a.get("downpipes_u"):
            oh = a.get("roof_overhang", 0.15)
            bm = bmesh.new()
            if a.get("gutter"):
                box(bm, fr, u0 - oh, u1 + oh, dep + oh, dep + oh + 0.12, zu - 0.12, zu)
            for u in a.get("downpipes_u", []):
                box(bm, fr, u - 0.045, u + 0.045, dep + 0.03, dep + 0.12, zu - bh - 0.1, zu - 0.12)  # fascia drop into the post
            self.obj(f"GalleryGutter_{tag}", bm, COL["frame"], ev, cf)

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

    def build_interior(self, a):
        """Basic fit-out of a hall that is seen through its glazing (mockup level, one object per group so UE can
        split them later). Items in building-local metres (x along ring edge 0, y inward/north), z above FFL:
        box {c, size [x, y, h], z0, rot}, table {c, top [x, y], h, pedestal} (café table), chair {c, rot} (seat + back
        + legs, 0.45 m seat), column {c, size [x, y], z1}. Every item: 'group' (object name part) and 'slot'."""
        groups = {}
        for it in a["items"]:
            key = (it.get("group", "Fitout"), it.get("slot", "M_Wood_Stained"))
            bm = groups.setdefault(key, bmesh.new())
            fr = Matrix.Translation((it["c"][0], it["c"][1], 0.0)) @ Matrix.Rotation(math.radians(it.get("rot", 0.0)), 4, "Z")
            k = it.get("kind", "box")
            if k == "box":
                sx, sy, h = it["size"]
                z0 = it.get("z0", 0.0)
                box(bm, fr, -sx / 2, sx / 2, -sy / 2, sy / 2, z0, z0 + h)
            elif k == "column":
                sx, sy = it["size"]
                box(bm, fr, -sx / 2, sx / 2, -sy / 2, sy / 2, -0.05, it["z1"])
            elif k == "table":
                tx, ty = it.get("top", [0.7, 0.7])
                h, pd = it.get("h", 0.75), it.get("pedestal", 0.08)
                box(bm, fr, -tx / 2, tx / 2, -ty / 2, ty / 2, h - 0.03, h)
                box(bm, fr, -pd / 2, pd / 2, -pd / 2, pd / 2, 0.02, h - 0.03)
                box(bm, fr, -0.22, 0.22, -0.22, 0.22, 0.0, 0.02)
            elif k == "chair":   # faces +y of its own frame; seat 0.42 x 0.42 at 0.45 m
                box(bm, fr, -0.21, 0.21, -0.21, 0.21, 0.42, 0.46)
                box(bm, fr, -0.21, 0.21, -0.25, -0.21, 0.46, 0.86)
                for lx, ly in ((-0.18, -0.18), (0.18, -0.18), (-0.18, 0.18), (0.18, 0.18)):
                    box(bm, fr, lx - 0.015, lx + 0.015, ly - 0.015, ly + 0.015, 0.0, 0.42)
        for (g, slot), bm in groups.items():
            self.obj_parts(f"Int_{a.get('name', 'Hall')}_{g}", {slot: bm}, a.get("evidence"), a.get("confidence"))

    def build_glazed_porch(self, a, e, fr):
        """Glazed entrance vestibule against the wall (Canteen NW porch, 070410255 t=46 s): floor slab at FFL, black
        aluminium corner posts + mullions (<= pane_w apart) on the 3 free faces, glass panes, one glazed door leaf
        (own object, UE swaps a hinged actor) and a flat roof slab with an overhang. u0..u1 along the wall, depth
        outward, z_top = roof underside (rel FFL). door: {"face": "front"|"u0"|"u1", "c": centre along that face, "w", "h"}."""
        u0, u1, dep, zt = a["u0"], a["u1"], a["depth"], a["z_top"]
        pw, pane = a.get("post_w", 0.08), a.get("pane_w", 1.2)
        dr = a.get("door", {"face": "front", "c": (u0 + u1) / 2, "w": 1.0, "h": 2.1})
        floor, alu, glass, roof, leaf, leaf_g = (bmesh.new() for _ in range(6))
        if a.get("floor", True):   # false when a stairs landing under the vestibule is its floor (no double deck)
            box(floor, fr, u0, u1, 0.0, dep, -0.3, -0.005)         # 5 mm under FFL: no coplanar floor with the hall slab
        # faces as (start, end) points in (u, w) and the along-face door span
        faces = {"u0": ((u0, 0.0), (u0, dep)), "front": ((u0, dep), (u1, dep)), "u1": ((u1, 0.0), (u1, dep))}
        for name, (pa, pb) in faces.items():
            L = math.dist(pa, pb)
            d = ((pb[0] - pa[0]) / L, (pb[1] - pa[1]) / L)
            at = lambda t: (pa[0] + d[0] * t, pa[1] + d[1] * t)
            # door span along this face; 'c' is measured from the face start (u0 face: from the wall, front: u0 side)
            dspan = (dr["c"] - dr["w"] / 2, dr["c"] + dr["w"] / 2) if dr["face"] == name else None
            cuts = [0.0, L] + ([dspan[0], dspan[1]] if dspan else [])
            n = max(1, int(math.ceil(L / pane)))
            cuts += [L * k / n for k in range(1, n) if not (dspan and dspan[0] - 0.3 < L * k / n < dspan[1] + 0.3)]
            cuts = sorted(set(round(c, 4) for c in cuts))
            for c in cuts:                                          # posts / mullions (square, on the face line)
                x, y = at(c)
                box(alu, fr, x - pw / 2, x + pw / 2, y - pw / 2, y + pw / 2, 0.0, zt)
            for c0, c1 in zip(cuts[:-1], cuts[1:]):
                is_door = dspan and abs(c0 - dspan[0]) < 1e-3 and abs(c1 - dspan[1]) < 1e-3
                z0 = dr["h"] if is_door else 0.1
                (xa, ya), (xb, yb) = at(c0 + pw / 2), at(c1 - pw / 2)
                if is_door:   # transom bar over the door + the door leaf (frame ring + glass)
                    (xa2, ya2), (xb2, yb2) = at(c0 + pw / 2 + 0.005), at(c1 - pw / 2 - 0.005)
                    lo_u, hi_u = min(xa2, xb2), max(xa2, xb2)
                    lo_w, hi_w = min(ya2, yb2), max(ya2, yb2)
                    th = 0.025
                    if hi_u - lo_u < hi_w - lo_w:
                        lo_u, hi_u = lo_u - th, lo_u + th
                        box(leaf, fr, lo_u, hi_u, lo_w, lo_w + 0.06, 0.01, dr["h"] - 0.01)
                        box(leaf, fr, lo_u, hi_u, hi_w - 0.06, hi_w, 0.01, dr["h"] - 0.01)
                        box(leaf, fr, lo_u, hi_u, lo_w + 0.06, hi_w - 0.06, 0.01, 0.12)
                        box(leaf, fr, lo_u, hi_u, lo_w + 0.06, hi_w - 0.06, dr["h"] - 0.07, dr["h"] - 0.01)
                        box(leaf_g, fr, lo_u + 0.019, hi_u - 0.019, lo_w + 0.06, hi_w - 0.06, 0.12, dr["h"] - 0.07)
                    else:
                        lo_w, hi_w = lo_w - th, lo_w + th
                        box(leaf, fr, lo_u, lo_u + 0.06, lo_w, hi_w, 0.01, dr["h"] - 0.01)
                        box(leaf, fr, hi_u - 0.06, hi_u, lo_w, hi_w, 0.01, dr["h"] - 0.01)
                        box(leaf, fr, lo_u + 0.06, hi_u - 0.06, lo_w, hi_w, 0.01, 0.12)
                        box(leaf, fr, lo_u + 0.06, hi_u - 0.06, lo_w, hi_w, dr["h"] - 0.07, dr["h"] - 0.01)
                        box(leaf_g, fr, lo_u + 0.06, hi_u - 0.06, lo_w + 0.019, hi_w - 0.019, 0.12, dr["h"] - 0.07)
                    box(alu, fr, min(xa, xb) - (0 if xa != xb else pw / 2), max(xa, xb) + (0 if xa != xb else pw / 2),
                        min(ya, yb) - (0 if ya != yb else pw / 2), max(ya, yb) + (0 if ya != yb else pw / 2),
                        dr["h"], dr["h"] + 0.06)
                    z0 = dr["h"] + 0.06
                g = 0.006
                box(glass, fr, min(xa, xb) - (g if xa == xb else 0), max(xa, xb) + (g if xa == xb else 0),
                    min(ya, yb) - (g if ya == yb else 0), max(ya, yb) + (g if ya == yb else 0), z0, zt - 0.02)
        oh = a.get("roof_overhang", 0.15)
        box(roof, fr, u0 - oh, u1 + oh, 0.0, dep + oh, zt, zt + a.get("roof_t", 0.15))
        cf, ev = a.get("confidence"), a.get("evidence")
        nm = a.get("name", f"GlazedPorch_E{a['edge']}")
        self.obj_parts(nm, {"M_Alu_Black": alu, "M_Glass": glass, "M_Concrete": floor, "M_Sheet_Brown": roof}, ev, cf)
        self.obj_parts(nm + "_Door", {"M_Alu_Black": leaf, "M_Glass": leaf_g}, ev, cf)

    def build_post_canopy(self, a, e, fr):
        """Flat entrance canopy slab cantilevered from the wall and carried by posts near its front edge (D_W west
        entrance, 2GIS aerial 30258560047688468): slab u0..u1 x 0..depth, soffit z0, top z1 (rel FFL), a fascia band of
        fascia_h round the free edges, posts (post_w square, from the ground to the soffit) at posts_u, set post_in
        behind the front edge. Frame: u along the wall, w outward (m)."""
        u0, u1, dep, z0, z1 = a["u0"], a["u1"], a["depth"], a["z0"], a["z1"]
        fh, ft, pw = a.get("fascia_h", 0.35), a.get("fascia_t", 0.06), a.get("post_w", 0.3)
        slab, fascia, posts = bmesh.new(), bmesh.new(), bmesh.new()
        box(slab, fr, u0 + ft, u1 - ft, 0.0, dep - ft, z0, z1 - 0.02)
        box(fascia, fr, u0, u1, dep - ft, dep, z1 - fh, z1)                  # front band
        for ua, ub in ((u0, u0 + ft), (u1 - ft, u1)):                        # side bands
            box(fascia, fr, ua, ub, 0.0, dep - ft, z1 - fh, z1)
        pin = a.get("post_in", 0.35)
        for u in a.get("posts_u", [u0 + pin, u1 - pin]):
            box(posts, fr, u - pw / 2, u + pw / 2, dep - pin - pw / 2, dep - pin + pw / 2, e["zg"] - BURY_M, z0)
        cf, ev = a.get("confidence"), a.get("evidence")
        tag = f"E{a['edge']}_{u0:.0f}"
        self.obj_parts(f"PostCanopy_{tag}", {a.get("slot", "M_Paint_Maroon"): fascia, a.get("soffit_slot", "M_Render_White"): slab},
                       ev, cf)
        self.obj_parts(f"PostCanopyPosts_{tag}", {a.get("post_slot", "M_Paint_Maroon"): posts}, ev, cf)

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
        if self.s["roof"].get("type", "hip") not in ("flat", "none"):
            # a pitched roof solid already closes the top at eave_z - FASCIA_M: an eave slab would only add a
            # coplanar ceiling face (z-fight seen through the windows) and a buried top face
            slabs = slabs[:1]
        # "interior_floors": true -> the INT_* specs model every floor plate (with stair openings); the shell only
        # keeps the basement slab (an eave slab would cut through an attic storey)
        if self.s.get("interior_floors"):
            slabs = []
        bsm = self.s.get("basement")
        if bsm and not bsm.get("slab_by_interior"):   # an INT_* spec models the basement floors itself (no coplanar double)
            slabs.append((bsm["floor_z"] - bsm["slab_t"], bsm["floor_z"]))
        # upper floor plates of a shell without an interior spec: without them every upper window looks into a void
        # down to the ground floor. A plate that would cut a window/door opening is skipped (reported).
        if not self.s.get("interior_floors") and self.s.get("storey_slabs", True):
            ops = [o for i in range(len(self.edges)) for o, _t, _w in self.openings_for(i)[0]]
            st = self.s["storey_m"]
            for k in range(1, int(self.s["storeys"])):
                z1 = st * k
                z0 = z1 - self.s.get("floor_slab_t", 0.25)
                if z1 > self.s["eave_z"] - 0.3:
                    break
                if any(o.z0 < z1 and o.z1 > z0 for o in ops):
                    print(f"  {self.id}: storey {k + 1} floor plate skipped (cuts an opening)")
                    continue
                slabs.append((z0, z1))
        for z0, z1 in slabs:
            lo = [bm.verts.new((x, y, z0)) for x, y in inner]
            hi = [bm.verts.new((x, y, z1)) for x, y in inner]
            for i in range(len(inner)):
                j = (i + 1) % len(inner)
                bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
            bm.faces.new(list(reversed(lo)))
            bm.faces.new(hi)
        ob = self.obj("Slabs", bm, (0.6, 0.6, 0.6, 1), "closing slabs; floor plates come with the interior")
        if ob is not None:
            ob["koch_ffl"] = self.ffl   # ground floor level (campus z), read by walk_qa / UE placement


def _box_kind(name):
    """Detail kind of a 'wall_boxes' attachment from its spec name (ACUnits, CCTV_W, Lamp..., Vent..., Sign...)."""
    n = name.lower()
    for key, kind in (("ac", "ac"), ("cctv", "cctv"), ("lamp", "lamp"), ("vent", "vent"), ("sign", "sign")):
        if n.startswith(key):
            return kind
    return "box"


def _drop_collinear(ring, eps=1e-6):
    """Remove vertices lying on the line of their neighbours (no-op for rings without them)."""
    n = len(ring)
    out = []
    for i in range(n):
        a, b, c = ring[i - 1], ring[i], ring[(i + 1) % n]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > eps:
            out.append(b)
    return out


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
    """Window surround bands; zero-width bands are skipped (a flat box has coincident faces and no inside)."""
    ident = Matrix.Identity(4)
    if proj <= 0:
        return
    if b > 0:
        box(bm, ident, -l, w + r, 0.0, proj, -b, 0.0)      # bottom
    if t > 0:
        box(bm, ident, -l, w + r, 0.0, proj, h, h + t)     # top
    if l > 0:
        box(bm, ident, -l, 0.0, 0.0, proj, 0.0, h)         # left
    if r > 0:
        box(bm, ident, w, w + r, 0.0, proj, 0.0, h)        # right


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


def merge_overlay(spec, ov):
    """Specs/Overlays/<id>.json: additions kept apart from the main spec (another session owns it). facades[]:
    {edge, windows[], entrances[], remove_windows[{u[], rows[]}]}; window_types{}, attachments[], cladding[] added."""
    spec = json.loads(json.dumps(spec))
    for k in ("window_types",):
        for name, wt in ov.get(k, {}).items():
            spec.setdefault(k, {}).setdefault(name, wt)
    drop = set(ov.get("remove_attachments", []))   # e.g. a placeholder box replaced by a detailed attachment
    spec["attachments"] = [a for a in spec.get("attachments", []) if a.get("name") not in drop]
    for k in ("attachments", "cladding"):
        spec.setdefault(k, []).extend(ov.get(k, []))
    for fo in ov.get("facades", []):
        f = next((f for f in spec["facades"] if f["edge"] == fo["edge"]), None)
        if f is None:
            f = {"edge": fo["edge"], "windows": []}
            spec["facades"].append(f)
        for rm in fo.get("remove_windows", []):   # e.g. the ground-floor window where a door goes in
            out = []
            for g in f.get("windows", []):
                hit_rows = [r for r in g.get("rows", []) if r in rm["rows"]]
                cut = [u for u in g["u"] if any(abs(u - x) < 0.05 for x in rm["u"])]
                if not hit_rows or not cut:
                    out.append(g)
                    continue
                keep_rows = [r for r in g["rows"] if r not in hit_rows]
                if keep_rows or g.get("sills"):
                    out.append({**g, "rows": keep_rows})
                rest = [u for u in g["u"] if u not in cut]
                if rest:
                    out.append({**g, "rows": hit_rows, "u": rest, "sills": []})
            f["windows"] = out
        f.setdefault("windows", []).extend(fo.get("windows", []))
        f.setdefault("entrances", []).extend(fo.get("entrances", []))
    spec["overlay_note"] = ov.get("note", "")
    return spec


def main():
    ids = [s for s in os.environ.get("KOCH_SPECS", "BLD_C").split(",") if s]
    ter = Terrain(load("terrain.json"))
    for bid in ids:
        try:  # one broken or half-written spec must not stop the others
            spec = json.load(open(os.path.join(SPECS, bid + ".json"), encoding="utf-8"))
            ovp = os.path.join(SPECS, "Overlays", bid + ".json")
            if os.path.exists(ovp):
                spec = merge_overlay(spec, json.load(open(ovp, encoding="utf-8")))
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
            bpy.app.driver_namespace.setdefault("koch_build_failures", []).append(f"{bid}: FAILED {ex!r}")
            continue
        n = sum(1 for o in bpy.data.objects if o.get("koch_gen") == b.gen)
        print(f"{bid}: {n} objects, FFL z={b.ffl:.2f} (ASL {b.ffl + 800:.2f})")
    if bpy.app.background:
        bpy.ops.wm.save_mainfile(compress=True)


main()
