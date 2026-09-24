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


def sweep_profile(bm, pts, profile, ground, closed=False):
    """Sweep a closed CCW profile [(across, dz)] along pts [(x, y)]; ground(x, y) -> z of the base at that point.

    across > 0 is to the LEFT of the travel direction. dz is added to the ground z at each vertex.
    Returns nothing; adds one closed manifold solid to bm (end caps for open lines).
    """
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
