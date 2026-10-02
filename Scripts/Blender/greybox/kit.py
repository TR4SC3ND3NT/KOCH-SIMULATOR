# Parametric greybox kit for building facades (bmesh, metres). Used by build_facades.py (R1).
# Every generator emits closed, manifold solids in a local facade frame: u along the facade (0 = start corner),
# w outward from the exterior wall face (w = 0 on the face, negative into the wall), z up (0 = local base).
# No booleans: walls are split into cells around openings, like Building Tools' facade split (MIT,
# github.com/ranjian0/building_tools, btools/building/*: face subdivision + reveal extrusion).
from dataclasses import dataclass, field

from mathutils import Matrix, Vector


@dataclass
class Opening:
    """Rectangular hole through a wall piece (local u/z, metres)."""
    u0: float
    u1: float
    z0: float
    z1: float


@dataclass
class WindowSpec:
    """Window unit placed in an opening. lights_u/lights_z: split positions as fractions (0..1) of the frame."""
    reveal: float = 0.18          # outer face -> frame outer plane (m)
    frame_w: float = 0.065        # frame face width (m)
    frame_d: float = 0.07         # frame depth (m)
    mullions: list = field(default_factory=list)   # u fractions of vertical bars
    transoms: list = field(default_factory=list)   # z fractions of horizontal bars
    bar_w: float = 0.08
    glass_t: float = 0.024
    sill_proj: float = 0.05       # exterior sill projection beyond the wall face (m)
    sill_t: float = 0.03


def _v(bm, frame, u, w, z):
    return bm.verts.new(frame @ Vector((u, w, z)))


def facade_frame(p0, p1, z_base):
    """Matrix mapping local (u, w, z) to world: u along p0->p1, w = outward normal of a CCW ring, z up."""
    d = (Vector(p1) - Vector(p0)).to_3d()
    d.z = 0
    d.normalize()
    n = Vector((d.y, -d.x, 0.0))  # right of the edge direction = outside for CCW rings
    m = Matrix.Identity(4)
    m.col[0].xyz = d
    m.col[1].xyz = n
    m.col[2].xyz = Vector((0, 0, 1))
    m.col[3].xyz = Vector((p0[0], p0[1], z_base))
    return m


def box(bm, frame, u0, u1, w0, w1, z0, z1):
    """Closed axis-aligned box in facade space."""
    c = [_v(bm, frame, u, w, z) for z in (z0, z1) for w in (w0, w1) for u in (u0, u1)]
    # index = z*4 + w*2 + u
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([c[i] for i in f])


def ring_box(bm, frame, u0, u1, z0, z1, width, w0, w1):
    """Rectangular ring (window surround / frame) around the rectangle u0..u1 x z0..z1, band width `width`."""
    box(bm, frame, u0 - width, u1 + width, w0, w1, z0 - width, z0)          # bottom
    box(bm, frame, u0 - width, u1 + width, w0, w1, z1, z1 + width)          # top
    box(bm, frame, u0 - width, u0, w0, w1, z0, z1)                          # left
    box(bm, frame, u1, u1 + width, w0, w1, z0, z1)                          # right


def wall_piece(bm, frame, length, z0, z1, thk, openings, cut_start=None, cut_end=None, reveal_faces=None):
    """Wall slab from u=0..length (outer face) with through-openings and mitred ends.

    cut_start / cut_end: inner-face inset at each end (m); defaults to thk (90-degree convex corner).
    Openings must lie inside [cut_start, length - cut_end] x [z0, z1]. Result is one closed manifold.
    reveal_faces: optional list; the opening reveal faces are appended (e.g. to give them a painted material slot).
    """
    a = thk if cut_start is None else cut_start
    b = thk if cut_end is None else cut_end
    us = sorted({o.u0 for o in openings} | {o.u1 for o in openings})
    zs = sorted({z0, z1} | {o.z0 for o in openings} | {o.z1 for o in openings})
    uo = [0.0] + us + [length]            # outer face u lines
    ui = [a] + us + [length - b]          # inner face u lines (same interior lines)

    def is_hole(uc, zc):
        return any(o.u0 < uc < o.u1 and o.z0 < zc < o.z1 for o in openings)

    V = {}

    def vert(side, i, j):
        key = (side, i, j)
        if key not in V:
            u = (uo if side == "o" else ui)[i]
            V[key] = _v(bm, frame, u, 0.0 if side == "o" else -thk, zs[j])
        return V[key]

    nu, nz = len(uo), len(zs)
    for i in range(nu - 1):
        for j in range(nz - 1):
            uc = (uo[i] + uo[i + 1]) / 2 if 0 < i < nu - 2 else None
            zc = (zs[j] + zs[j + 1]) / 2
            if uc is not None and is_hole(uc, zc):
                continue
            bm.faces.new((vert("o", i, j), vert("o", i + 1, j), vert("o", i + 1, j + 1), vert("o", i, j + 1)))
            bm.faces.new((vert("i", i, j + 1), vert("i", i + 1, j + 1), vert("i", i + 1, j), vert("i", i, j)))
    # Mitred end caps (every z line, so the caps share vertices with both faces).
    for j in range(nz - 1):
        bm.faces.new((vert("o", 0, j + 1), vert("i", 0, j + 1), vert("i", 0, j), vert("o", 0, j)))
        e = nu - 1
        bm.faces.new((vert("o", e, j), vert("i", e, j), vert("i", e, j + 1), vert("o", e, j + 1)))
    # Bottom / top caps per u segment.
    top = nz - 1
    for i in range(nu - 1):
        bm.faces.new((vert("o", i, 0), vert("i", i, 0), vert("i", i + 1, 0), vert("o", i + 1, 0)))
        bm.faces.new((vert("o", i + 1, top), vert("i", i + 1, top), vert("i", i, top), vert("o", i, top)))
    # Reveals: the four sides of every opening, outer loop to inner loop.
    rf = reveal_faces if reveal_faces is not None else []
    for o in openings:
        i0, i1 = uo.index(o.u0), uo.index(o.u1)
        j0, j1 = zs.index(o.z0), zs.index(o.z1)
        for j in range(j0, j1):          # left and right jambs
            rf.append(bm.faces.new((vert("o", i0, j), vert("o", i0, j + 1), vert("i", i0, j + 1), vert("i", i0, j))))
            rf.append(bm.faces.new((vert("o", i1, j + 1), vert("o", i1, j), vert("i", i1, j), vert("i", i1, j + 1))))
        for i in range(i0, i1):          # sill and head
            rf.append(bm.faces.new((vert("o", i + 1, j0), vert("o", i, j0), vert("i", i, j0), vert("i", i + 1, j0))))
            rf.append(bm.faces.new((vert("o", i, j1), vert("o", i + 1, j1), vert("i", i + 1, j1), vert("i", i, j1))))


def window_unit(bm, frame, o, spec):
    """Frame + bars + glass + exterior sill inside opening o, frame outer plane at w = -spec.reveal."""
    w1 = -spec.reveal
    w0 = w1 - spec.frame_d
    fw = spec.frame_w
    ring_box(bm, frame, o.u0 + fw, o.u1 - fw, o.z0 + fw, o.z1 - fw, fw, w0, w1)
    iu0, iu1, iz0, iz1 = o.u0 + fw, o.u1 - fw, o.z0 + fw, o.z1 - fw
    hb = spec.bar_w / 2
    for f in spec.mullions:
        u = iu0 + (iu1 - iu0) * f
        box(bm, frame, u - hb, u + hb, w0, w1, iz0, iz1)
    for f in spec.transoms:
        z = iz0 + (iz1 - iz0) * f
        box(bm, frame, iu0, iu1, w0, w1, z - hb, z + hb)
    gm = (w0 + w1) / 2
    box(bm, frame, iu0, iu1, gm - spec.glass_t / 2, gm + spec.glass_t / 2, iz0, iz1)
    if spec.sill_proj > 0:  # metal sill from the frame to beyond the wall face (thin closed box) lying ON the reveal
        # floor (z0..z0 + sill_t): flush with it, its top would be coplanar with the wall's sill face (z-fight)
        box(bm, frame, o.u0 - 0.03, o.u1 + 0.03, w1, spec.sill_proj, o.z0, o.z0 + spec.sill_t)


def prism_profile(bm, frame, profile_wz, u0, u1):
    """Extrude a simple closed (w, z) profile polygon along u0..u1 (stairs, ramps, cornices)."""
    a = [_v(bm, frame, u0, w, z) for w, z in profile_wz]
    b = [_v(bm, frame, u1, w, z) for w, z in profile_wz]
    n = len(profile_wz)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)


def stair_flight(bm, frame, u0, u1, risers, riser_h, tread, landing, w_start=0.0, z_base=0.0):
    """Solid external stair against the wall face: landing (depth `landing`) at the top, steps going outward (+w).

    risers counts the landing's own rise; total rise = risers * riser_h (m) above z_base.
    """
    H = risers * riser_h
    prof = [(w_start, z_base - 0.2), (w_start, z_base + H), (w_start + landing, z_base + H)]
    w = w_start + landing
    for k in range(1, risers):
        z = z_base + H - k * riser_h
        prof += [(w, z), (w + tread, z)]
        w += tread
    prof += [(w, z_base), (w, z_base - 0.2)]  # buried 20 cm so the stair never floats on sloped grade
    prism_profile(bm, frame, prof, u0, u1)


def ramp(bm, frame, u0, u1, w0, w1, z_low, z_high, thk=0.25):
    """Wedge ramp along +w (w0 at z_high, w1 at z_low); u0..u1 is its width."""
    prism_profile(bm, frame, [(w0, z_high), (w1, z_low), (w1, z_low - thk), (w0, z_low - thk)], u0, u1)


def railing(bm, points, height=0.9, post=0.05, rail=0.05, spacing=1.2, mid_rails=1, bottom_rail=None, bar=None):
    """Posts + top rail + mid rails along a world-space polyline of Vector (z = walking surface).
    bottom_rail (m over the surface): balustrade style - a rail parallel to the pitch, the in-between bars (section
    bar, default post) stand on it; only the end/joint posts run down to the surface."""
    for si, (p, q) in enumerate(zip(points[:-1], points[1:])):
        seg = q - p
        d = seg.normalized()
        flat = Vector((d.x, d.y, 0)).normalized()
        side = Vector((-flat.y, flat.x, 0))
        m = Matrix.Identity(4)
        m.col[0].xyz, m.col[1].xyz, m.col[2].xyz, m.col[3].xyz = flat, side, Vector((0, 0, 1)), p
        run = Vector((seg.x, seg.y, 0)).length
        slope = seg.z / run if run > 1e-6 else 0.0
        n = max(1, round(run / spacing))
        for k in range(0 if si == 0 else 1, n + 1):  # joint post once (the previous segment placed it)
            u = run * k / n
            z = slope * u
            end = k in (0, n)
            if bottom_rail is None or end:
                box(bm, m, u - post / 2, u + post / 2, -post / 2, post / 2, z, z + height)
            else:
                b = bar or post
                box(bm, m, u - b / 2, u + b / 2, -b / 2, b / 2, z + bottom_rail, z + height)   # ends welded into the rails
        zs = [height] + [height * (i + 1) / (mid_rails + 1) for i in range(mid_rails)]
        for zr in zs + ([bottom_rail] if bottom_rail is not None else []):
            _sloped_bar(bm, m, run, slope, zr, rail)


def _sloped_bar(bm, m, run, slope, z, s):
    h = s / 2
    c = []
    for u in (0.0, run):
        for w in (-h, h):
            for dz in (-h, h):
                c.append(_v(bm, m, u, w, z + slope * u + dz))
    # index = u*4 + w*2 + dz
    for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        bm.faces.new([c[i] for i in f])


def offset_ring(ring, d):
    """Mitre offset of a CCW ring (list of (x, y)); d > 0 moves edges inward. d may be a list (one value per edge i,
    edge i = ring[i] -> ring[i+1]), e.g. a roof overhang that is 0 on an edge shared with a taller neighbour."""
    n = len(ring)
    ds = list(d) if isinstance(d, (list, tuple)) else [d] * n
    lines = []
    for i in range(n):
        p, q = Vector(ring[i]), Vector(ring[(i + 1) % n])
        t = (q - p).normalized()
        lines.append((p + Vector((-t.y, t.x)) * ds[i], t))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1.x * d2.y - d1.y * d2.x
        if abs(den) < 1e-9:
            out.append((p2.x, p2.y))
            continue
        s = ((p2.x - p1.x) * d2.y - (p2.y - p1.y) * d2.x) / den
        out.append((p1.x + d1.x * s, p1.y + d1.y * s))
    return out
