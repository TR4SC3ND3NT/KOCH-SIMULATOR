# Garden layout generator (R1, SITE_Garden.json): the hedged path network of the formal garden, MEASURED (owner
# 2026-09-29 "etalon" sketch drawn on Google Earth, registered on the georeferenced Google z20 ortho: 538 SIFT inliers,
# rms 0.24 m; each path then refined on the ortho's light paving strips where the strip is visible). Boundary = the
# owner's 7-sided outline (chamfered SW and SE corners) on the lawn/paving edge; paths: G1 N, W, SW, SSE + link; centre
# square spine N/S + links; G2 E, SSW, SE (to the SE chamfer vertex) + link. All hedges are one kind (clipped box
# hedge, same width/height as the arches): boundary = hedge - arch - hedge (topiary arch flush in the line at every
# path exit, owner 2026-09-28), path hedges run unbroken from the gazebo ring / square hedge to the boundary hedge,
# ring hedges open only at the paths. Gazebo centres stay where the owner put them (2026-09-28). Rewrites only OWN.
# Usage: uv run --project Scripts python Scripts/Geo/zones/zone_garden.py
import json
import math
import os
import re

from shapely.geometry import LineString, MultiLineString, Point, Polygon
from shapely.ops import unary_union

SPEC = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs", "SITE_Garden.json")
OWN = re.compile(r"^(G[12]_\w+|Centre_NS_\w+|Hedge_\w+|Edging_\w+|Arch_\w+|CentreSquare_\w+)$")
PATH_W, EDGE_OFF, HEDGE_OFF, HEDGE_W, HEDGE_H = 1.2, 0.65, 1.05, 0.7, 1.05
R_APRON, R_EDGE, R_HEDGE = 5.3, 5.75, 6.35       # path start (under the apron), ring edging, ring hedge centre (m)
ARCH_T, ARCH_H = 0.35, 2.25                      # topiary arch leg thickness / height (m)
SQ_P = 2.7                                       # centre square paving half size: sketch outline 6.1 m = hedge centre line
THETA = -3.0                                     # square / spine frame heading (deg; sketch N/S lines and gazebo axis)
SQ_C = (130.00, -27.55)                          # square centre: the sketch square (corners +-0.1 m)
# gazebo centres (owner 2026-09-29 "ставь как верно"): G1 = N x W path lines (116.98, -26.56) ~ roof octagon fit
# (117.4, -26.9) less the ~0.4 m east/north lean of a 4 m roof on this ortho; G2 = SSW x SE path lines (144.53, -28.65),
# sketch disc (144.57, -28.13), roof fit (145.1, -28.3) less the lean -> 1.3 m west of the 2026-09-28 position
GAZ = {"G1": (116.96, -26.65), "G2": (144.60, -28.35)}
EV = "[B] zone_garden.py 2026-09-29 v2: owner etalon sketch (Google Earth 5/27/2024) registered on Google z20 (rms 0.24 m), paths refined on the ortho paving strips; boundary hedge continuous: hedge-arch-hedge"
# outer face of the boundary hedge (lawn/paving edge), in order N, E, SE1, SE2, S, SW, W (world m); corners = intersections
OUTER = [((100.74, -9.84), (158.02, -13.74)),    # N: ortho paving edge, inner envelope (sketch -8.8..-13.8)
         ((158.30, -13.70), (156.90, -39.00)),   # E: ortho lawn edge x 157.0 at y -36 (sketch 158.0..159.0)
         ((156.90, -39.00), (154.20, -44.20)),   # SE chamfer, steep part (sketch, moved onto the ortho edge)
         ((154.20, -44.20), (150.85, -46.35)),   # SE chamfer, flat part
         ((150.89, -46.68), (103.45, -44.99)),   # S: sketch = lawn edge north of the light strip / pergola
         ((103.30, -45.40), (98.80, -36.90)),    # SW chamfer: NE side of the light sidewalk strip
         ((98.80, -36.90), (100.60, -9.10))]     # W: ortho lawn edge (sketch 97.1..100.5)
# path centre lines: (name, start, a, b, end) - start 'G1'/'G2' (gazebo ring) or 'SQ' (square paving edge); a-b = the
# measured line (a near the start); end 'bnd' = through the boundary (arch) or 'SQ'/'G1'/'G2' for the links
PATHS = [("G1_N", "G1", (117.199, -21.136), (117.599, -11.271), "bnd"),    # ortho strip (radial, miss 0.03 m)
         ("G1_W", "G1", (111.501, -25.686), (100.220, -23.886), "bnd"),    # sketch (under crowns on the ortho)
         ("G1_SW", "G1", (113.903, -32.341), (102.090, -42.218), "bnd"),   # ortho strip (2.3 m off-radial, clearly seen)
         ("G1_SSE", "G1", (119.585, -30.897), (122.440, -46.011), "bnd"),  # ortho strip
         ("G2_E", "G2", None, (158.327, -29.374), "bnd"),                  # radial to the ortho/sketch mean end
         ("G2_SSW", "G2", (142.665, -33.251), (137.492, -46.009), "bnd"),  # ortho = sketch
         ("G2_SE", "G2", (147.173, -33.357), (154.098, -45.701), "bnd")]   # ortho strip; ends at the SE chamfer vertex


def _xy(g):
    """Flatten a shapely line result into a list of coordinate lists (pieces)."""
    if g.is_empty:
        return []
    if isinstance(g, LineString):
        return [list(g.coords)]
    if isinstance(g, MultiLineString) or hasattr(g, "geoms"):
        out = []
        for q in g.geoms:
            out += _xy(q)
        return out
    return []


def _r(p):
    return [round(p[0], 3), round(p[1], 3)]


def _isect(l1, l2):
    """Intersection of two infinite lines given as point pairs."""
    (x1, y1), (x2, y2) = l1
    (x3, y3), (x4, y4) = l2
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    a, b = x1 * y2 - y1 * x2, x3 * y4 - y3 * x4
    return ((a * (x3 - x4) - (x1 - x2) * b) / den, (a * (y3 - y4) - (y1 - y2) * b) / den)


def _ext(a, b, L=80.0):
    """Line a->b extended L m beyond b and 2 m before a."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    return LineString([(a[0] - 2 * ux, a[1] - 2 * uy), (b[0] + L * ux, b[1] + L * uy)])


def main():
    d = json.load(open(SPEC))
    E = d["elements"]
    by = {e["name"]: e for e in E}
    old = {n for n in by if OWN.match(n)}
    # gazebos to the measured centres; their aprons and apron lamps move with them
    for g, gname, extra in (("G1", "Gazebo_1", ("Apron_G1", "Lamp_G1_Apron")), ("G2", "Gazebo_2", ("Apron_G2", "Lamp_G2_Apron"))):
        cur = by[gname]["center"]
        dx, dy = GAZ[g][0] - cur[0], GAZ[g][1] - cur[1]
        if abs(dx) + abs(dy) < 1e-4:
            continue
        by[gname]["center"] = list(GAZ[g])
        by[gname]["evidence"] = by[gname].get("evidence", "") + f" | 2026-09-29 measured centre {list(GAZ[g])} (zone_garden.py v2)"
        for n in extra:
            e = by.get(n)
            if not e:
                continue
            if "line" in e:
                e["line"] = [[round(q[0] + dx, 3), round(q[1] + dy, 3)] for q in e["line"]]
            if "pos" in e:
                e["pos"] = [round(e["pos"][0] + dx, 3), round(e["pos"][1] + dy, 3)]
    C = dict(GAZ)
    th = math.radians(THETA)
    U, V = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
    sq = lambda u, v: (SQ_C[0] + u * U[0] + v * V[0], SQ_C[1] + u * U[1] + v * V[1])
    # SE chamfer vertex: on the G2_SE centre line where it meets the lawn edge (sketch: the path ends in the corner)
    g2se = next(p for p in PATHS if p[0] == "G2_SE")
    a, b = g2se[2], g2se[3]
    L = math.dist(a, b)
    dv = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    hint = OUTER[2][1]
    t = (hint[0] - a[0]) * dv[0] + (hint[1] - a[1]) * dv[1]
    vse = (a[0] + dv[0] * t, a[1] + dv[1] * t)
    outer_lines = list(OUTER)
    outer_lines[2] = (OUTER[2][0], vse)
    outer_lines[3] = (vse, OUTER[3][1])
    ring = [_isect(outer_lines[k - 1], outer_lines[k]) for k in range(len(outer_lines))]
    outer = Polygon(ring)
    inner = outer.buffer(-HEDGE_W, join_style=2)                # inner face of the boundary hedge
    hedge_c = outer.buffer(-HEDGE_W / 2, join_style=2)          # its centre line
    new = []

    def edging(name, pts):
        new.append({"type": "wall", "name": name, "line": [_r(p) for p in pts], "height": 0.22, "thk": 0.1,
                    "cap_proj": 0.0, "material": "stone", "kind": "scalloped_edging", "confidence": "medium", "evidence": EV})

    # --- path centre lines (start, far end) ---
    cl = {}
    for name, st, pa, pb, end in PATHS:
        c = C[st]
        line = _ext(c if pa is None else pa, pb)
        hits = line.intersection(Point(c).buffer(R_APRON, 64).exterior)
        pts = [hits] if isinstance(hits, Point) else list(getattr(hits, "geoms", []))
        s0 = min(pts, key=line.project)
        far = line.intersection(outer.exterior)
        fp = [far] if isinstance(far, Point) else list(getattr(far, "geoms", []))
        f = max(fp, key=line.project)
        cl[name] = ((s0.x, s0.y), (f.x, f.y), st)
    for name, st, s in (("G1_Link", "G1", -1), ("G2_Link", "G2", 1)):
        c = C[st]
        e_ = sq(s * SQ_P, 0.0)
        dx, dy = e_[0] - c[0], e_[1] - c[1]
        n = math.hypot(dx, dy)
        cl[name] = ((c[0] + dx / n * R_APRON, c[1] + dy / n * R_APRON), e_, st)
    for name, v0, sgn in (("Centre_NS_N", SQ_P, 1), ("Centre_NS_S", -SQ_P, -1)):
        line = LineString([sq(0, v0), sq(0, sgn * 60)])
        far = line.intersection(outer.exterior)
        fp = [far] if isinstance(far, Point) else list(far.geoms)
        f = min(fp, key=line.project)
        cl[name] = (sq(0, v0), (f.x, f.y), "SQ")

    def corridor(a, b, half, back=1.5, fwd=0.0):
        """Strip of half width `half` along a->b, reaching `back` m behind a (into the apron / square) and fwd past b."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        return LineString([(a[0] - ux * back, a[1] - uy * back), (b[0] + ux * fwd, b[1] + uy * fwd)]).buffer(half, cap_style=2)

    open_h = unary_union([corridor(a, b, HEDGE_OFF - HEDGE_W / 2, fwd=1.0) for a, b, _ in cl.values()])   # hedge-free
    open_e = unary_union([corridor(a, b, EDGE_OFF - 0.05, fwd=1.0) for a, b, _ in cl.values()])           # edging-free
    # --- paths ---
    for name, (a, b, st) in cl.items():
        new.append({"type": "path", "name": name, "line": [_r(a), _r(b)], "width": PATH_W, "thk": 0.08, "top": 0.016,
                    "confidence": "medium", "evidence": EV})
    # --- ONE solid hedge mass (owner 2026-09-29: "сплошное везде"): boundary band + path hedge strips + gazebo ring
    # bands + square frame, unioned, minus the path openings / aprons / square paving / arch slots; every connected piece
    # (the hedge round one lawn bed) is one hedge element = footprint polygon with its bed as the hole ---
    mass = [outer.difference(inner)]
    for name, (a, b, st) in cl.items():
        mass.append(corridor(a, b, HEDGE_OFF + HEDGE_W / 2, back=0.0, fwd=1.0).difference(corridor(a, b, HEDGE_OFF - HEDGE_W / 2, back=0.0, fwd=1.0)))
    for g in C:
        mass.append(Point(C[g]).buffer(R_HEDGE + HEDGE_W / 2, 96).difference(Point(C[g]).buffer(R_HEDGE - HEDGE_W / 2, 96)))
    sqp = lambda h_: Polygon([sq(-h_, -h_), sq(h_, -h_), sq(h_, h_), sq(-h_, h_)])
    mass.append(sqp(SQ_P + HEDGE_W).difference(sqp(SQ_P)))
    solid = unary_union(mass).intersection(outer)
    cut = [open_h, sqp(SQ_P)] + [Point(C[g]).buffer(R_HEDGE - HEDGE_W / 2, 96) for g in C]
    # arches: in the boundary line (legs along the boundary, opening across it), clear span = the path opening measured
    # along the boundary; the slot they stand in is cut from the mass so arch legs and hedge meet face to face
    hg = HEDGE_OFF - HEDGE_W / 2 + 0.02
    bl = LineString(list(hedge_c.exterior.coords))
    arches = []
    for name, (a, b, st) in cl.items():
        if name.endswith("_Link"):
            continue
        x = LineString([a, b]).intersection(bl)
        if x.is_empty:
            continue
        x = x if isinstance(x, Point) else list(x.geoms)[0]
        sp = bl.project(x)
        p0, p1 = bl.interpolate(max(0.0, sp - 0.5)), bl.interpolate(min(bl.length, sp + 0.5))
        tx, ty = p1.x - p0.x, p1.y - p0.y
        tl = math.hypot(tx, ty)
        tx, ty = tx / tl, ty / tl                               # boundary tangent at the crossing
        px, py = (b[0] - a[0]) / math.dist(a, b), (b[1] - a[1]) / math.dist(a, b)
        sin = abs(tx * py - ty * px)
        span = 2 * hg / max(sin, 0.5)
        nx, ny = -ty, tx
        if nx * px + ny * py < 0:
            nx, ny = -nx, -ny                                   # opening axis = boundary normal, pointing outward
        hw, hd_ = span / 2 + ARCH_T, HEDGE_W / 2 + 0.02
        cut.append(Polygon([(x.x + tx * hw + nx * hd_, x.y + ty * hw + ny * hd_), (x.x - tx * hw + nx * hd_, x.y - ty * hw + ny * hd_),
                            (x.x - tx * hw - nx * hd_, x.y - ty * hw - ny * hd_), (x.x + tx * hw - nx * hd_, x.y + ty * hw - ny * hd_)]))
        arches.append({"type": "hedge_arch", "name": f"Arch_Bnd_{name}", "center": _r((x.x, x.y)),
                       "dir_deg": round(math.degrees(math.atan2(ny, nx)), 2), "span": round(span, 3), "thk": ARCH_T,
                       "depth": HEDGE_W, "height": ARCH_H, "confidence": "medium", "evidence": EV})
    solid = solid.difference(unary_union(cut)).buffer(0)
    parts = [q for q in getattr(solid, "geoms", [solid]) if q.area > 0.05]
    parts.sort(key=lambda q: (-q.centroid.y, q.centroid.x))
    for k, q in enumerate(parts):
        q = q.simplify(0.01)
        new.append({"type": "hedge", "name": f"Hedge_Mass_{k}", "ring": [_r(c) for c in q.exterior.coords[:-1]],
                    "holes": [[_r(c) for c in h_.coords[:-1]] for h_ in q.interiors], "height": HEDGE_H, "top": "flat",
                    "confidence": "medium", "evidence": EV})
    new += arches
    # --- scalloped edging: both sides of every path, the gazebo rings and the square, open at every path mouth ---
    edge_keep = inner.buffer(-0.05)
    for name, (a, b, st) in cl.items():
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        nx, ny = -dy / n, dx / n
        others = unary_union([corridor(a2, b2, EDGE_OFF - 0.05, fwd=1.0) for k2, (a2, b2, _) in cl.items() if k2 != name]
                             + [Point(C[g]).buffer(R_EDGE, 96) for g in C] + [sqp(SQ_P - 0.1)])
        for side, sg in (("L", 1), ("R", -1)):
            ln = LineString([(a[0] - dx / n * 3 + sg * nx * EDGE_OFF, a[1] - dy / n * 3 + sg * ny * EDGE_OFF),
                             (b[0] + dx / n * 3 + sg * nx * EDGE_OFF, b[1] + dy / n * 3 + sg * ny * EDGE_OFF)])
            pieces = [q for q in _xy(ln.intersection(edge_keep).difference(others)) if LineString(q).length > 0.3]
            for k, q in enumerate(pieces):
                edging(f"Edging_{name}_{side}" + (f"_{k}" if len(pieces) > 1 else ""), q)

    def loop_pieces(coords, prefix):
        pieces = _xy(LineString(coords).difference(open_e))
        if len(pieces) > 1 and math.dist(pieces[0][0], pieces[-1][-1]) < 1e-6:
            pieces = [pieces[-1] + pieces[0][1:]] + pieces[1:-1]
        for k, q in enumerate(pieces):
            if LineString(q).length > 0.3:
                edging(f"{prefix}_{k}", q)
    for g in C:
        loop_pieces([(C[g][0] + R_EDGE * math.cos(2 * math.pi * k / 96), C[g][1] + R_EDGE * math.sin(2 * math.pi * k / 96))
                     for k in range(97)], f"Edging_{g}_Ring")
    er = SQ_P - 0.05
    loop_pieces([sq(-er, -er), sq(er, -er), sq(er, er), sq(-er, er), sq(-er, -er)], "CentreSquare_Edging")
    # --- centre square: paving, 4 benches (W/E sides, one each side of the link), lamp in the middle ---
    P = SQ_P
    new.append({"type": "path", "name": "CentreSquare_Paving", "line": [_r(sq(-P, 0.0)), _r(sq(P, 0.0))], "width": 2 * P,
                "thk": 0.08, "top": 0.022, "confidence": "medium", "evidence": EV})
    hdg = math.degrees(th)
    bu = (PATH_W / 2 + 0.1 + P) / 2
    blen = round(min(1.5, P - PATH_W / 2 - 0.3), 2)
    for side, nx_ in (("E", 1), ("W", -1)):
        face = hdg + (180.0 if nx_ > 0 else 0.0)
        for k, sgn in enumerate((-1, 1)):
            new.append({"type": "bench", "name": f"CentreSquare_Bench_{side}{k}", "pos": _r(sq(nx_ * (P - 0.4), sgn * bu)),
                        "dir_deg": round(face, 2), "length": blen, "ue_asset": "bench_wrought_iron_slats", "confidence": "medium",
                        "evidence": EV})
    new.append({"type": "lamp_orn", "name": "CentreSquare_Lamp", "pos": _r(SQ_C), "dir_deg": round(hdg, 2), "height": 3.2,
                "cross": True, "arm_span": 0.8, "globe_d": 0.35, "base_box": [0.3, 0.3, 0.6], "confidence": "low",
                "evidence": EV + " | owner: lamp post in the exact middle, 4 lamps (maybe 2)"})

    # --- props that hang on the boundary: east walk lamps, SE arch map board ---
    def outside(p, dist):
        q = outer.exterior.interpolate(outer.exterior.project(Point(p)))
        seg = [c for c in zip(outer.exterior.coords[:-1], outer.exterior.coords[1:]) if LineString(c).distance(q) < 1e-6][0]
        tx, ty = seg[1][0] - seg[0][0], seg[1][1] - seg[0][1]
        tl = math.hypot(tx, ty)
        nx_, ny_ = ty / tl, -tx / tl
        if nx_ * (q.x - outer.centroid.x) + ny_ * (q.y - outer.centroid.y) < 0:
            nx_, ny_ = -nx_, -ny_
        return [round(q.x + nx_ * dist, 3), round(q.y + ny_ * dist, 3)]
    for n in ("Lamp_EastWalk_0", "Lamp_EastWalk_1"):
        if n in by:
            by[n]["pos"] = outside(by[n]["pos"], 0.5)
    if "Signboard_Arch" in by:
        se = next(a_ for a_ in arches if a_["name"] == "Arch_Bnd_G2_SE")
        tx, ty = outer_lines[2][0][0] - vse[0], outer_lines[2][0][1] - vse[1]
        tl = math.hypot(tx, ty)
        by["Signboard_Arch"]["pos"] = outside((se["center"][0] + tx / tl * (se["span"] / 2 + 1.2), se["center"][1] + ty / tl * (se["span"] / 2 + 1.2)), 0.6)
    keep = [e for e in E if e["name"] not in old]
    i = next(k for k, e in enumerate(keep) if e["name"] == "Gazebo_2") + 1
    keep[i:i] = new
    d["elements"] = keep
    d["note"] = re.sub(r" \| boundary v2:.*$", "", d.get("note", "")) + " | boundary v2: measured 7-sided outline " + \
        str([_r(p) for p in ring])
    json.dump(d, open(SPEC, "w"), indent=1, ensure_ascii=False)
    print(f"garden v2: removed {len(old)}, wrote {len(new)}; hedge masses {len(parts)} (holes {sum(len(q.interiors) for q in parts)}); "
          f"arches {len(arches)}; outer area {outer.area:.0f} m2")
    for n, (a, b, st) in cl.items():
        print(f"  {n:12s} {_r(a)} -> {_r(b)}  hd {math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])):7.2f}  len {math.dist(a, b):5.2f}")
    json.dump({"outline": [_r(p) for p in ring], "gazebos": C, "square": [SQ_C, SQ_P, THETA],
               "paths": {n: [_r(a), _r(b)] for n, (a, b, _) in cl.items()}},
              open(os.path.join(os.path.dirname(SPEC), "..", "Audit", "garden_v2_layout.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
