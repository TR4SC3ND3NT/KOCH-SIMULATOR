# Garden layout generator (R1 stream B, SITE_Garden.json): the hedged path network between the two gazebos, laid out
# in one garden frame (u along the pergola walk, v north) and MIRROR-symmetric about the centre axis between the
# gazebos: per gazebo a north path, an outer side path, a link to the centre bench square (4 benches) and a straight
# south path; a north-south spine through the square (owner 2026-09-28: no diagonal paths); boundary hedges on
# one rectangle (west/east/north hedge lines + the row along the pergola walk) with gaps where paths cross; ring hedges
# and edging around each gazebo apron with gaps at the paths; hedge arches inside the rectangle. Everything is clipped
# to the rectangle. Rewrites only the elements it owns (listed in OWN); run it after moving a gazebo or the walk.
# Usage: python Scripts/Geo/zones/zone_garden.py
import json
import math
import os
import re

SPEC = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs", "SITE_Garden.json")
OWN = re.compile(r"^(G[12]_(N|W|E|S|D|Link)|Centre_NS(_[NS])?|(Hedge|Edging)_(G[12]_.*|Centre_NS_.*|North_\d+|South_\d+|East_\d+|West_\d+|Bnd_.*)|"
                 r"Arch_G[12]_.*|G[12]_(SSE|SSW|W_Link|E_Link)|Hedge_G[12]_Ring_\d+|Edging_G[12]_Ring_\d+|CentreSquare_.*)$")
PATH_W, EDGE_OFF, HEDGE_OFF, HEDGE_W = 1.2, 0.65, 1.05, 0.7
R_APRON, R_EDGE, R_HEDGE = 5.3, 5.75, 6.35       # path start (under the apron), ring edging, ring hedge centre (m)
SQ_P = 4.0       # centre bench square: paving half size (m); 4 benches on its W/E sides
EV = "[B] zone_garden.py 2026-09-28: mirror-symmetric garden layout on one rectangle (owner: same paths at both gazebos, diagonals to the centre, nothing outside the garden boundary)"


def main():
    d = json.load(open(SPEC))
    E = d["elements"]
    by = {e["name"]: e for e in E}
    walk = by["PergolaWalk_South"]
    (wx0, wy0), (wx1, wy1) = walk["line"]
    L = math.hypot(wx1 - wx0, wy1 - wy0)
    T = ((wx1 - wx0) / L, (wy1 - wy0) / L)
    N = (-T[1], T[0])
    g1, g2 = by["Gazebo_1"], by["Gazebo_2"]
    O = ((g1["center"][0] + g2["center"][0]) / 2, (g1["center"][1] + g2["center"][1]) / 2)
    uv = lambda p: ((p[0] - O[0]) * T[0] + (p[1] - O[1]) * T[1], (p[0] - O[0]) * N[0] + (p[1] - O[1]) * N[1])
    W = lambda u, v: [round(O[0] + u * T[0] + v * N[0], 3), round(O[1] + u * T[1] + v * N[1], 3)]
    ug = abs(uv(g2["center"])[0] - uv(g1["center"])[0]) / 2
    # boundary from the current outer hedges (their centre lines) and the walk
    def mean_u(names): return sum(uv(p)[0] for n in names for p in by[n]["line"]) / sum(len(by[n]["line"]) for n in names)
    def mean_v(names): return sum(uv(p)[1] for n in names for p in by[n]["line"]) / sum(len(by[n]["line"]) for n in names)
    old = {n for n in by if OWN.match(n)}
    bw = [n for n in by if n.startswith("Hedge_West_")] or [n for n in by if n.startswith("Hedge_Bnd_W")]
    be = [n for n in by if n.startswith("Hedge_East_")] or [n for n in by if n.startswith("Hedge_Bnd_E")]
    bn = [n for n in by if n.startswith("Hedge_North_")] or [n for n in by if n.startswith("Hedge_Bnd_N")]
    u_w, u_e, v_n = mean_u(bw), mean_u(be), mean_v(bn)
    v_walk = uv(walk["line"][0])[1]
    v_s = v_walk + walk["width"] / 2                          # walk north edge
    v_sh = v_s + 0.4                                          # south hedge row centre (along the walk)
    # gazebos on the axis pair, same height, same (mirror-invariant) rotation
    for g, s in ((g1, -1), (g2, 1)):
        g["center"] = W(s * ug, 0.0)
        g["rot_deg"] = g1["rot_deg"]
        g["evidence"] = g.get("evidence", "") + " | " + EV
    rot = math.radians(g1["rot_deg"])
    sq = SQ_P + 0.35 + 0.35                                   # centre square half size to the outside of its hedge
    new = []
    paths = []                                                # (name, [(u, v), ...], start_r, end_kind)

    def ang(a):
        return (math.cos(a), math.sin(a))
    # face normals of the gazebo octagon that open to the south (owner photos: two south openings per gazebo)
    down = math.atan2(-1, 0)                                  # -v direction in the garden frame
    for g, s in ((g1, -1), (g2, 1)):
        c = (s * ug, 0.0)
        nm = "G1" if s < 0 else "G2"
        paths.append((f"{nm}_N", [(c[0], c[1] + R_APRON), (c[0], v_n - 0.35)], "bnd"))
        paths.append((f"{nm}_W" if s < 0 else f"{nm}_E", [(c[0] + s * R_APRON, c[1]), (u_w + 0.35 if s < 0 else u_e - 0.35, c[1])], "bnd"))
        paths.append((f"{nm}_Link", [(c[0] - s * R_APRON, c[1]), (s * sq, c[1])], "sq"))   # ends at the square's near side
        a_out = down + s * math.radians(22.5)                 # outer south face (away from the centre)
        p0 = (c[0] + R_APRON * math.cos(a_out), c[1] + R_APRON * math.sin(a_out))
        p1 = (p0[0] + 1.6 * math.cos(a_out), p0[1] + 1.6 * math.sin(a_out))
        paths.append((f"{nm}_S", [p0, p1, (p1[0], v_s)], "walk"))
    paths.append(("Centre_NS_N", [(0.0, SQ_P), (0.0, v_n - 0.35)], "bnd"))     # from the square paving edge
    paths.append(("Centre_NS_S", [(0.0, -SQ_P), (0.0, v_s)], "walk"))

    def offset(pts, d):
        """Offset polyline (u, v) by d to the left, mitred at the bends."""
        out = []
        segs = list(zip(pts[:-1], pts[1:]))
        nrm = []
        for a, b in segs:
            l = math.hypot(b[0] - a[0], b[1] - a[1])
            nrm.append((-(b[1] - a[1]) / l, (b[0] - a[0]) / l))
        for i, p in enumerate(pts):
            if i == 0:
                n = nrm[0]
                out.append((p[0] + n[0] * d, p[1] + n[1] * d))
            elif i == len(pts) - 1:
                n = nrm[-1]
                out.append((p[0] + n[0] * d, p[1] + n[1] * d))
            else:
                n0, n1 = nrm[i - 1], nrm[i]
                m = (n0[0] + n1[0], n0[1] + n1[1])
                ml = math.hypot(*m)
                m = (m[0] / ml, m[1] / ml)
                k = d / max(0.3, m[0] * n1[0] + m[1] * n1[1])
                out.append((p[0] + m[0] * k, p[1] + m[1] * k))
        return out

    def trim_start(pts, c, r):
        """Move the first point along the first segment to radius r from c (hedges start at the ring hedge)."""
        (ax, ay), (bx, by_) = pts[0], pts[1]
        dx, dy = bx - ax, by_ - ay
        fx, fy = ax - c[0], ay - c[1]
        A = dx * dx + dy * dy
        B = 2 * (fx * dx + fy * dy)
        C = fx * fx + fy * fy - r * r
        disc = B * B - 4 * A * C
        if disc < 0:
            return pts
        t = (-B + math.sqrt(disc)) / (2 * A)
        t = max(0.0, min(0.95, t))
        return [(ax + dx * t, ay + dy * t)] + pts[1:]

    def clip_end(pts, kind, inner):
        """Last point onto the boundary line the path ends at (inner face of the boundary hedge / walk edge / square)."""
        (ax, ay), (bx, by_) = pts[-2], pts[-1]
        if kind == "walk":
            v_t = v_s + (0.0 if not inner else 0.75)
            t = (v_t - ay) / (by_ - ay) if abs(by_ - ay) > 1e-9 else 1.0
        elif kind == "sq":
            u_t = math.copysign(sq if inner else sq - 0.7, bx)          # path butts onto the square paving
            t = (u_t - ax) / (bx - ax) if abs(bx - ax) > 1e-9 else 1.0
        else:
            if abs(bx - ax) > abs(by_ - ay):
                u_t = (u_w + (0.35 if inner else 0.0)) if bx < ax else (u_e - (0.35 if inner else 0.0))
                t = (u_t - ax) / (bx - ax)
            else:
                v_t = v_n - (0.35 if inner else 0.0)
                t = (v_t - ay) / (by_ - ay)
        return pts[:-1] + [(ax + (bx - ax) * t, ay + (by_ - ay) * t)]

    def centre_of(name):
        if name.startswith("G1"):
            return (-ug, 0.0)
        if name.startswith("G2"):
            return (ug, 0.0)
        return None

    gaps_bnd = {"N": [], "S": [], "W": [], "E": []}
    ring_gaps = {"G1": [], "G2": []}
    for name, pts, kind in paths:
        c = centre_of(name)
        cl = clip_end(pts, kind, False)
        new.append({"type": "path", "name": name, "line": [W(*p) for p in cl], "width": PATH_W, "thk": 0.08,
                    "top": 0.016, "confidence": "medium", "evidence": EV})
        for side, dd in (("L", 1), ("R", -1)):
            h = offset(pts, dd * HEDGE_OFF)
            ed = offset(pts, dd * EDGE_OFF)
            if c:
                h = trim_start(h, c, R_HEDGE + HEDGE_W / 2 - 0.1)   # butts onto the ring hedge's outer face (no doubled block)
                ed = trim_start(ed, c, R_EDGE)
            elif kind in ("bnd", "walk"):
                h = [(h[0][0], math.copysign(sq, h[0][1]))] + h[1:]
                ed = [(ed[0][0], math.copysign(sq - 0.35 - 0.06, ed[0][1]))] + ed[1:]
            h = clip_end(h, kind, True)
            ed = clip_end(ed, kind, True)
            new.append({"type": "hedge", "name": f"Hedge_{name}_{side}", "line": [W(*p) for p in h], "width": HEDGE_W,
                        "height": 1.05, "top": "flat", "confidence": "medium", "evidence": EV})
            new.append({"type": "wall", "name": f"Edging_{name}_{side}", "line": [W(*p) for p in ed], "height": 0.22,
                        "thk": 0.1, "cap_proj": 0.0, "material": "stone", "kind": "scalloped_edging", "confidence": "medium",
                        "evidence": EV})
        # boundary gap where the path meets it
        e0 = cl[-1]
        if kind == "walk":
            gaps_bnd["S"].append(e0[0])
        elif kind == "bnd":
            # north paths end on the boundary centre line (clip_end, not inner): test both, else they fell to W/E (no N gaps)
            key = "N" if min(abs(e0[1] - v_n), abs(e0[1] - (v_n - 0.35))) < 0.01 else ("W" if e0[0] < 0 else "E")
            gaps_bnd[key].append(e0[1] if key in "WE" else e0[0])
        if c:
            a = math.atan2(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0])
            ring_gaps[name[:2]].append(a)
    # boundary hedges with gaps (half gap = hedge offset - half hedge width so the path hedges butt onto them)
    hg = HEDGE_OFF - HEDGE_W / 2 + 0.02

    def hedge_line(name, a, b, along_u, gaps, fixed):
        lo, hi = (a, b) if a < b else (b, a)
        cuts = sorted(g for g in gaps if lo < g < hi)
        spans, cur = [], lo
        for g in cuts:
            spans.append((cur, g - hg))
            cur = g + hg
        spans.append((cur, hi))
        for k, (x0, x1) in enumerate(spans):
            if x1 - x0 < 0.2:
                continue
            p0, p1 = ((x0, fixed), (x1, fixed)) if along_u else ((fixed, x0), (fixed, x1))
            new.append({"type": "hedge", "name": f"Hedge_Bnd_{name}{k}", "line": [W(*p0), W(*p1)], "width": HEDGE_W,
                        "height": 1.04, "top": "flat", "confidence": "medium", "evidence": EV})
    hedge_line("N", u_w, u_e, True, gaps_bnd["N"], v_n)
    hedge_line("S", u_w, u_e, True, gaps_bnd["S"], v_sh)
    hedge_line("W", v_sh + 0.35, v_n - 0.35, False, gaps_bnd["W"], u_w)
    hedge_line("E", v_sh + 0.35, v_n - 0.35, False, gaps_bnd["E"], u_e)
    # gazebo ring hedge + edging (24-gon) with gaps at the paths
    for gname, s in (("G1", -1), ("G2", 1)):
        c = (s * ug, 0.0)
        for kind, r, half in (("Hedge", R_HEDGE, math.asin((HEDGE_OFF - HEDGE_W / 2) / R_HEDGE)),
                              ("Edging", R_EDGE, math.asin((EDGE_OFF - 0.05) / R_EDGE))):
            gaps = sorted((a % (2 * math.pi)) for a in ring_gaps[gname])
            n = 48
            arcs, cur = [], None
            for k in range(n + 1):
                a = 2 * math.pi * k / n
                inside = any(min(abs(a - g), 2 * math.pi - abs(a - g)) < half for g in gaps)
                if inside:
                    if cur:
                        arcs.append(cur)
                    cur = None
                else:
                    cur = (cur or []) + [a]
            if cur:
                if arcs and arcs[0][0] == 0.0:
                    arcs[0] = cur + arcs[0][1:]
                else:
                    arcs.append(cur)
            for k, arc in enumerate(arcs):
                if len(arc) < 2:
                    continue
                pts = [W(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in arc]
                if kind == "Hedge":
                    new.append({"type": "hedge", "name": f"Hedge_{gname}_Ring_{k}", "line": pts, "width": HEDGE_W,
                                "height": 1.06, "top": "flat", "confidence": "medium", "evidence": EV})
                else:
                    new.append({"type": "wall", "name": f"Edging_{gname}_Ring_{k}", "line": pts, "height": 0.22, "thk": 0.1,
                                "cap_proj": 0.0, "material": "stone", "kind": "scalloped_edging", "confidence": "medium",
                                "evidence": EV})
    # hedge arches (topiary): on the north paths, the links and the diagonals, all inside the rectangle
    def arch(name, p, a):
        new.append({"type": "hedge_arch", "name": name, "center": W(*p),
                    "dir_deg": round(math.degrees(a + math.atan2(T[1], T[0])), 2), "span": 1.3, "height": 2.25,
                    "confidence": "medium", "evidence": EV})
    for gname, s in (("G1", -1), ("G2", 1)):
        arch(f"Arch_{gname}_N", (s * ug, v_n - 0.35 - 1.2), math.pi / 2)
        arch(f"Arch_{gname}_Link", (s * (sq + 0.9), 0.0), 0.0)
    # centre bench square (owner 2026-09-28): paving 2*SQ_P, hedge + scalloped edging on 4 sides with the 4 entrances
    # (gap = path width), 4 benches on the W/E sides (one each side of the link entrance) facing the middle, drain
    # grate (owner 2026-09-28: 4 benches, none on the N/S sides; the 8 m size stays)
    P, gh = SQ_P, PATH_W / 2
    hd = math.degrees(math.atan2(T[1], T[0]))                 # world heading of +u
    new.append({"type": "path", "name": "CentreSquare_Paving", "line": [W(-P, 0.0), W(P, 0.0)], "width": 2 * P,
                "thk": 0.08, "top": 0.022, "confidence": "medium", "evidence": EV})
    for side, (nx, ny) in (("N", (0, 1)), ("S", (0, -1)), ("E", (1, 0)), ("W", (-1, 0))):
        along = (ny != 0)                                     # N/S sides run along u and own the corners
        hr, er = P + 0.35, P - 0.05                           # hedge / edging centre lines
        hl, el_ = (sq if along else P), (P if along else P - 0.1)
        for k, (a0, a1) in enumerate(((-hl, -gh), (gh, hl))):
            pts = [(a0, ny * hr), (a1, ny * hr)] if along else [(nx * hr, a0), (nx * hr, a1)]
            new.append({"type": "hedge", "name": f"CentreSquare_Hedge_{side}{k}", "line": [W(*q) for q in pts],
                        "width": HEDGE_W, "height": 1.05, "top": "flat", "confidence": "medium", "evidence": EV})
        for k, (a0, a1) in enumerate(((-el_, -gh), (gh, el_))):
            pts = [(a0, ny * er), (a1, ny * er)] if along else [(nx * er, a0), (nx * er, a1)]
            new.append({"type": "wall", "name": f"CentreSquare_Edging_{side}{k}", "line": [W(*q) for q in pts],
                        "height": 0.22, "thk": 0.1, "cap_proj": 0.0, "material": "stone", "kind": "scalloped_edging",
                        "confidence": "medium", "evidence": EV})
        bu = (gh + 0.1 + P) / 2                               # bench centre along the side (mid of each half)
        face = math.degrees(math.atan2(-ny, -nx)) + hd        # sitter faces the middle of the square
        for k, sgn in enumerate((-1, 1) if not along else ()):
            q = (sgn * bu, ny * (P - 0.4)) if along else (nx * (P - 0.4), sgn * bu)
            new.append({"type": "bench", "name": f"CentreSquare_Bench_{side}{k}", "pos": W(*q), "dir_deg": round(face, 2),
                        "length": 1.5, "ue_asset": "bench_wrought_iron_slats", "confidence": "medium", "evidence": EV})
    new.append({"type": "lamp_orn", "name": "CentreSquare_Lamp", "pos": W(0.0, 0.0), "dir_deg": round(hd, 2), "height": 3.2,
                "cross": True, "arm_span": 0.8, "globe_d": 0.35, "confidence": "low",
                "evidence": EV + " | owner: lamp post in the exact middle, 4 lamps (maybe 2)"})
    new.append({"type": "box", "name": "CentreSquare_Drain", "center": W(1.2, -1.0), "dir_deg": round(hd, 2),
                "size": [0.5, 0.5, 0.03], "z_rel": 0.0, "material": "metal", "slot": "M_Steel_Grating", "confidence": "low",
                "evidence": EV})
    keep = [e for e in E if e["name"] not in old]
    i = next(k for k, e in enumerate(keep) if e["name"] == "Gazebo_2") + 1
    keep[i:i] = new
    d["elements"] = keep
    json.dump(d, open(SPEC, "w"), indent=1, ensure_ascii=False)
    print(f"garden: removed {len(old)}, wrote {len(new)}; rectangle u {u_w:.2f}..{u_e:.2f} v {v_s:.2f}..{v_n:.2f}, gazebos at +-{ug:.2f}")


if __name__ == "__main__":
    main()
