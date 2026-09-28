# Closed-solid sweeps for site greybox elements (walls, hedges, curbs, planter edging). Used by build_site.py (R1).
# A cross-section (across, z) is placed at every polyline vertex with mitred joints; z follows the ground per vertex.
import math

from mathutils import Vector


def _dirs(pts, closed):
    n = len(pts)
    segs = []
    for i in range(n if closed else n - 1):
        a, b = pts[i], pts[(i + 1) % n]
        d = Vector((b[0] - a[0], b[1] - a[1]))
        segs.append(d.normalized() if d.length > 1e-9 else Vector((1, 0)))
    return segs


def _subdivide(pts, closed, max_seg):
    """Insert points so no segment is longer than max_seg (m): the sweep then follows the ground between vertices."""
    out = []
    n = len(pts)
    for i in range(n if closed else n - 1):
        a, b = pts[i], pts[(i + 1) % n]
        k = max(1, math.ceil(math.dist(a, b) / max_seg))
        out += [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k) for j in range(k)]
    if not closed:
        out.append(tuple(pts[-1]))
    return out


def _refine_steps(pts, closed, ground, dz=0.05, min_len=0.02):
    """Bisect segments whose ground z changes by more than dz (a curb or pad edge between two samples) down to
    min_len, so the element steps where the ground steps instead of ramping through it (a path crossing a
    dropped kerb sank 7 cm under the curb top on a 0.5 m sample)."""
    P = [Vector(p) for p in pts]
    z = [ground(p.x, p.y) for p in P]
    out = [P[0]]
    pairs = list(zip(range(len(P)), list(range(1, len(P))) + ([0] if closed else [])))
    for i, j in pairs:
        stack = [(P[i], z[i], P[j], z[j])]
        seg = []
        while stack:
            a, za, b, zb = stack.pop()
            if abs(za - zb) > dz and (b - a).length > min_len:
                m = (a + b) / 2
                zm = ground(m.x, m.y)
                stack.append((m, zm, b, zb)); stack.append((a, za, m, zm))
            else:
                seg.append(b)
        if j != 0 or not closed:
            out += seg
        else:
            out += seg[:-1]
    return [(p.x, p.y) for p in out]


def sweep_profile(bm, pts, profile, ground, closed=False, max_seg=None, cut0=None, cut1=None):
    """Sweep a closed CCW profile [(across, dz)] along pts [(x, y)]; ground(x, y) -> z of the base at that point.

    across > 0 is to the LEFT of the travel direction. dz is added to the ground z at each vertex.
    max_seg (m): subdivide longer segments so z follows the ground in between (paths over pad edges / blends).
    cut0 / cut1: world heading (deg) of the start / end cap line for open lines (mitred joint against another
    element, e.g. a path meeting a landing at an angle); default = square to the line.
    Returns nothing; adds one closed manifold solid to bm (end caps for open lines).
    """
    if max_seg:
        pts = _subdivide(pts, closed, max_seg)
        pts = _refine_steps(pts, closed, ground)
    n = len(pts)
    segs = _dirs(pts, closed)
    loops = []
    for i in range(n):
        if closed:
            d0, d1 = segs[i - 1], segs[i % len(segs)]
        else:
            d0 = segs[max(i - 1, 0)]
            d1 = segs[min(i, len(segs) - 1)]
        t = (d0 + d1)
        t = t.normalized() if t.length > 1e-9 else d1
        left = Vector((-t.y, t.x))
        cos_half = max(0.2, left.dot(Vector((-d1.y, d1.x))))  # mitre stretch, clamped for very sharp turns
        cut = None if closed else (cut0 if i == 0 else cut1 if i == n - 1 else None)
        if cut is not None:  # cap along the given heading; 'across' stays the perpendicular distance
            c = Vector((math.cos(math.radians(cut)), math.sin(math.radians(cut))))
            nrm = Vector((-d1.y, d1.x))
            if c.dot(nrm) < 0:
                c = -c
            left, cos_half = c, max(0.2, c.dot(nrm))
        x, y = pts[i]
        zg = ground(x, y)
        loops.append([bm.verts.new((x + left.x * a / cos_half, y + left.y * a / cos_half, zg + dz)) for a, dz in profile])
    m = len(profile)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        A, B = loops[i], loops[(i + 1) % n]
        for k in range(m):
            j = (k + 1) % m
            bm.faces.new((A[k], B[k], B[j], A[j]))
    if not closed:
        bm.faces.new(list(reversed(loops[0])))
        bm.faces.new(loops[-1])


def rect_profile(w, h, bury=0.3, centered=True):
    """Across-section of a box wall of width w, from bury below ground to h above it (CCW in (across, z))."""
    a0, a1 = (-w / 2, w / 2) if centered else (0.0, w)
    return [(a1, -bury), (a1, h), (a0, h), (a0, -bury)]


def hedge_profile(w, h, round_top=True, bury=0.3):
    """Clipped hedge: slight batter (base wider) and a rounded or flat top."""
    b = w / 2
    t = b * 0.92
    if not round_top:
        return [(b, -bury), (t, h), (-t, h), (-b, -bury)]
    r = min(t, 0.25)
    pts = [(b, -bury), (t, h - r)]
    for k in range(1, 4):
        a = math.pi / 2 * k / 4
        pts.append((t - r + r * math.cos(a), h - r + r * math.sin(a)))
    pts += [(t - r, h), (-(t - r), h)]
    for k in range(1, 4):
        a = math.pi / 2 + math.pi / 2 * k / 4
        pts.append((-(t - r) + r * math.cos(a), h - r + r * math.sin(a)))
    pts += [(-t, h - r), (-b, -bury)]
    return pts
