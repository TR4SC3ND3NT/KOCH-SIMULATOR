# Real-construction detail kit for the R1 greybox (handoff 4a "detail standard"): parts modelled the way they are
# built, >= ~1 cm relief, closed manifold solids, metres. Used by build_facades.py / build_site.py.
# Local facade frame as in kit.py: u along the facade, w outward from the wall face (w = 0 on the face, negative
# into the wall), z up. Dimensions of stock parts (PVC profiles, gutters, pipes) are typical RU/KG catalogue values
# (Rehau/KBE 70 mm frames, 125/90 mm steel gutter systems); the per-element spec overrides them where measured.
import math
from dataclasses import dataclass, field

from mathutils import Matrix, Vector

from .kit import Opening, box, prism_profile, wall_piece


def _v(bm, frame, u, w, z):
    return bm.verts.new(frame @ Vector((u, w, z)))


# ---------------------------------------------------------------------------------------------------- windows
@dataclass
class PvcWindow:
    """PVC window unit in a wall opening. lights_u / lights_z: split positions (fractions of the frame's inner width /
    height) of the mullions / transoms; sashes: indices (row-major, bottom row first) of the opening lights."""
    reveal: float = 0.16          # wall face -> frame outer face (m)
    frame_face: float = 0.062     # visible frame width (m)
    frame_depth: float = 0.070
    mullion_face: float = 0.084   # visible impost width
    sash_face: float = 0.052      # visible sash width (inside the light)
    sash_depth: float = 0.076
    sash_step: float = 0.006      # sash outer face behind the frame outer face
    clearance: float = 0.002      # gap frame <-> sash (reads as the dark joint line)
    glass_t: float = 0.024        # insulated glass unit
    glass_back: float = 0.022     # glass outer face behind the carrier's outer face (gasket lip + bead)
    glass_bite: float = 0.012     # glass edge set this deep into the frame/sash rebate
    support: float = 0.03         # support profile: frame bottom this far above the masonry opening bottom
    mullions: list = field(default_factory=list)
    transoms: list = field(default_factory=list)
    sashes: list = field(default_factory=list)
    sill_proj: float = 0.045      # exterior steel sill: nose beyond the wall face (m)
    sill_t: float = 0.004         # modelled sheet thickness (real 0.5-0.7 mm; 4 mm keeps it a solid)
    sill_drip: float = 0.02       # bent-down drip nose
    sill_ears: float = 0.03       # sill runs this far into the plaster at each jamb


def _lights(w, h, s):
    """Light rectangles (u0, u1, z0, z1) inside the frame grid, bottom row first, left to right."""
    fw, mw = s.frame_face, s.mullion_face
    iu0, iu1, iz0, iz1 = fw, w - fw, fw, h - fw
    us = [iu0] + [iu0 + (iu1 - iu0) * f for f in s.mullions] + [iu1]
    zs = [iz0] + [iz0 + (iz1 - iz0) * f for f in s.transoms] + [iz1]
    out = []
    for j in range(len(zs) - 1):
        for i in range(len(us) - 1):
            a = us[i] + (mw / 2 if i > 0 else 0.0)
            b = us[i + 1] - (mw / 2 if i < len(us) - 2 else 0.0)
            c = zs[j] + (mw / 2 if j > 0 else 0.0)
            d = zs[j + 1] - (mw / 2 if j < len(zs) - 2 else 0.0)
            out.append((a, b, c, d))
    return out


def pvc_window(parts, frame, o, s):
    """Window in the masonry opening o (u0..u1 x z0..z1 of the wall). parts: dict of bmesh per material slot
    {'frame', 'sash', 'glass', 'sill'}; each part is closed and manifold.
    Frame + mullions are ONE slab with the lights as through-holes (welded PVC grid, no internal faces); it stands on
    a support profile `support` above the opening bottom; the steel sill lies on its mortar bed there."""
    w, h = o.u1 - o.u0, o.z1 - o.z0 - s.support
    fr = frame @ Matrix.Translation((o.u0, -s.reveal, o.z0 + s.support))  # local u 0..w, z 0..h, w = 0 frame face
    lights = _lights(w, h, s)
    wall_piece(parts["frame"], fr, w, 0.0, h, s.frame_depth, [Opening(a, b, c, d) for a, b, c, d in lights],
               cut_start=0.0, cut_end=0.0)
    gb = s.glass_bite
    for k, (a, b, c, d) in enumerate(lights):
        front, depth = 0.0, s.frame_depth
        if k in s.sashes:
            cl, sf = s.clearance, s.sash_face
            sa, sb, sc, sd = a + cl, b - cl, c + cl, d - cl
            sfr = fr @ Matrix.Translation((sa, -s.sash_step, sc))
            wall_piece(parts["sash"], sfr, sb - sa, 0.0, sd - sc, s.sash_depth,
                       [Opening(sf, sb - sa - sf, sf, sd - sc - sf)], cut_start=0.0, cut_end=0.0)
            a, b, c, d = sa + sf, sb - sf, sc + sf, sd - sf
            front, depth = -s.sash_step, s.sash_depth
        g0 = front - s.glass_back
        g1 = max(g0 - s.glass_t, front - depth + 0.005)
        box(parts["glass"], fr, a - gb, b + gb, g1, g0, c - gb, d + gb)  # edges sit in the rebate
    # exterior steel sill: mortar-bed wedge on the reveal floor from under the frame to the wall face, then the
    # sheet overhangs the facade with a bent-down drip nose; ears run into the jamb plaster
    if s.sill_proj > 0:
        t, e, z0 = s.sill_t, s.sill_ears, o.z0
        w_in = -s.reveal - 0.02
        z_in = z0 + s.support - 0.001            # top just under the frame (no coplanar contact)
        slope = (s.support - 0.006) / (s.reveal + 0.02 + s.sill_proj)
        z_face = z_in - slope * (s.reveal + 0.02)
        z_nose = z_in - slope * (s.reveal + 0.02 + s.sill_proj)
        prof = [(w_in, z0), (w_in, z_in), (s.sill_proj, z_nose), (s.sill_proj, z_nose - s.sill_drip),
                (s.sill_proj - t, z_nose - s.sill_drip), (s.sill_proj - t, z_nose - t), (0.0, z_face - t), (0.0, z0)]
        prism_profile(parts["sill"], frame, prof, o.u0 - e, o.u1 + e)


# ---------------------------------------------------------------------------------------------------- storefronts
@dataclass
class AluStorefront:
    """Aluminium entrance screen (stick system, e.g. 50 mm face / 100 mm depth) in a wall opening.
    bays: [[width, 'fixed'|'door'|'door_open'], ...] left to right (rescaled to fill), transom_z: underside of the
    transom bar above the doors (m above the opening bottom), top_bays: split fractions of the transom row."""
    reveal: float = 0.25
    face: float = 0.05
    depth: float = 0.10
    bays: list = field(default_factory=lambda: [[1.0, "door"]])
    transom_z: float = 2.2
    top_splits: list = field(default_factory=list)   # extra mullions in the transom row (fractions of the width)
    leaf_stile: float = 0.09     # door leaf profile face width
    leaf_bottom: float = 0.16    # door bottom rail
    leaf_mid: float = 0.0        # door mid rail centre height (0 = none)
    leaf_depth: float = 0.07
    glass_t: float = 0.024
    threshold: float = 0.02
    handle: str = "bar"          # 'bar': vertical pull tube on the leaf's lock side
    hinge: str = "outer"         # hinge side of each door pair: 'outer' = hinges on the bay edges away from centre


def alu_storefront(parts, frame, o, s):
    """parts {'alu', 'glass', 'steel'} (+ optional 'leaf', 'leaf_glass', 'leaf_steel' for the door leaves). Frame grid (outer frame, bay mullions, transom) is one slab with the panes
    as holes; each door leaf is its own frame slab (hinged part for UE) with its glass; pull bars in 'steel'."""
    w, h = o.u1 - o.u0, o.z1 - o.z0
    fr = frame @ Matrix.Translation((o.u0, -s.reveal, o.z0))
    f = s.face
    total = sum(b[0] for b in s.bays)
    xs, u = [0.0], 0.0
    for b in s.bays:
        u += b[0] * w / total
        xs.append(u)
    holes, leaves = [], []
    zt = s.transom_z
    for i, (b0, b1) in enumerate(zip(xs[:-1], xs[1:])):
        a = b0 + (f if i == 0 else f / 2)
        c = b1 - (f if i == len(xs) - 2 else f / 2)
        kind = s.bays[i][1]
        if kind.startswith("door"):
            holes.append(Opening(a, c, s.threshold, zt))       # door bay: opening down to the threshold
            leaves.append((a, c, kind))
        else:
            holes.append(Opening(a, c, f, zt))
    # transom row panes
    ts = [0.0] + [x * w for x in s.top_splits] + [w]
    if not s.top_splits:
        ts = xs
    for i, (b0, b1) in enumerate(zip(ts[:-1], ts[1:])):
        a = b0 + (f if i == 0 else f / 2)
        c = b1 - (f if i == len(ts) - 2 else f / 2)
        holes.append(Opening(a, c, zt + f, h - f))
    wall_piece(parts["alu"], fr, w, 0.0, h, s.depth, holes, cut_start=0.0, cut_end=0.0)
    gm = -s.depth / 2
    for hl in holes:
        if any(abs(hl.u0 - a) < 1e-6 and abs(hl.u1 - c) < 1e-6 and hl.z1 <= zt + 1e-6 for a, c, _ in leaves):
            continue  # door bays get their glass in the leaf
        box(parts["glass"], fr, hl.u0 - 0.01, hl.u1 + 0.01, gm - s.glass_t / 2, gm + s.glass_t / 2, hl.z0 - 0.01, hl.z1 + 0.01)
    # door leaves: pairs split in the middle of adjacent door bays; each leaf fills its bay with a 3 mm gap
    for k, (a, c, kind) in enumerate(leaves):
        g = 0.003
        la, lc, lz0, lz1 = a + g, c - g, s.threshold + g, zt - g
        st, bt = s.leaf_stile, s.leaf_bottom
        lfr = fr @ Matrix.Translation((la, -0.015, lz0))
        panes = [Opening(st, lc - la - st, bt, lz1 - lz0 - st)]
        if s.leaf_mid > 0:
            zm = s.leaf_mid - lz0
            panes = [Opening(st, lc - la - st, bt, zm - st / 2), Opening(st, lc - la - st, zm + st / 2, lz1 - lz0 - st)]
        wall_piece(parts.get("leaf", parts["alu"]), lfr, lc - la, 0.0, lz1 - lz0, s.leaf_depth, panes, cut_start=0.0,
                   cut_end=0.0)
        for p in panes:
            box(parts.get("leaf_glass", parts["glass"]), lfr, p.u0 - 0.01, p.u1 + 0.01, -s.leaf_depth / 2 - s.glass_t / 2,
                -s.leaf_depth / 2 + s.glass_t / 2, p.z0 - 0.01, p.z1 + 0.01)
        if s.handle == "bar":
            # lock side = towards the pair's meeting stiles (the leaf nearer the screen centre)
            lock_right = (la + lc) / 2 < w / 2
            uh = (lc - la) - st / 2 if lock_right else st / 2
            p0 = lfr @ Vector((uh, 0.06, 0.85))
            p1 = lfr @ Vector((uh, 0.06, 1.65))
            tube(parts.get("leaf_steel", parts["steel"]), [lfr @ Vector((uh, 0.0, 0.85)), p0, p1, lfr @ Vector((uh, 0.0, 1.65))], 0.014, seg=12,
                 bend_r=0.03)


def canopy_box(parts, frame, u0, u1, depth, z_soffit_wall, z_soffit_front, sign_top, sign_frame=0.05, panel=0.6,
               roof_t=0.08, seam=0.012):
    """Entrance canopy cantilevered from the wall: sign box front (u0..u1, full width, from the soffit front edge up
    to sign_top) with a frame border and an inset panel, closed side cheeks, sloped soffit of `panel` cassettes
    (seams as grooves), flat roof deck. parts {'frame', 'panel', 'soffit', 'roof'}."""
    d, zf, zw = depth, z_soffit_front, z_soffit_wall
    ztop = sign_top
    # side cheeks + roof deck + back as one shell: a solid prism (u0..u1) of the canopy body between soffit and roof
    body = [(0.0, zw), (d - 0.08, zf), (d - 0.08, ztop - roof_t), (0.0, ztop - roof_t)]
    prism_profile(parts["frame"], frame, body, u0 + 0.0, u1 - 0.0)
    # roof deck: thin sheet on top with a fall to the wall, drip edge over the sign
    prism_profile(parts["roof"], frame, [(0.0, ztop - roof_t), (d, ztop - roof_t + 0.01), (d, ztop - roof_t + 0.03),
                                         (0.0, ztop - roof_t + 0.06)], u0 - 0.02, u1 + 0.02)
    # sign box front: frame border (white) with the inset panel (content = KOCH branding in UE)
    sf = sign_frame
    fr = frame @ Matrix.Translation((u0, d, zf))
    W, H = u1 - u0, ztop - roof_t - zf
    wall_piece(parts["frame"], fr, W, 0.0, H, 0.08, [Opening(sf, W - sf, sf, H - sf)], cut_start=0.0, cut_end=0.0)
    box(parts["panel"], fr, sf - 0.005, W - sf + 0.005, -0.04, -0.02, sf - 0.005, H - sf + 0.005)
    # soffit cassettes: panels between the wall and the sign, seams `seam` wide, 8 mm proud of the body underside
    nu = max(1, round((u1 - u0) / panel))
    L = math.hypot(d - 0.08, zf - zw)
    nw = max(1, round(L / panel))
    for i in range(nu):
        a = u0 + (u1 - u0) * i / nu + seam / 2
        b = u0 + (u1 - u0) * (i + 1) / nu - seam / 2
        for j in range(nw):
            t0, t1 = j / nw, (j + 1) / nw
            w0 = (d - 0.08) * t0 + (seam / 2 if j else 0.0)
            w1 = (d - 0.08) * t1 - (seam / 2 if j < nw - 1 else 0.0)
            z0 = zw + (zf - zw) * w0 / (d - 0.08)
            z1 = zw + (zf - zw) * w1 / (d - 0.08)
            prism_profile(parts["soffit"], frame, [(w0, z0 - 0.008), (w1, z1 - 0.008), (w1, z1 + 0.002), (w0, z0 + 0.002)], a, b)


# ---------------------------------------------------------------------------------------------------- tubes
def tube(bm, pts, r, seg=16, cap=True, bend_r=0.0):
    """Round tube (downpipe, handrail, post) swept along a world-space polyline of Vectors; mitred at the vertices
    (bend_r > 0 rounds each corner with 3 extra rings on an arc of that radius). Closed manifold with end caps."""
    P = [Vector(p) for p in pts]
    if bend_r > 0 and len(P) > 2:
        Q = [P[0]]
        for a, b, c in zip(P[:-2], P[1:-1], P[2:]):
            d0, d1 = (b - a).normalized(), (c - b).normalized()
            ang = d0.angle(d1, 0.0)
            if ang < 1e-3:
                Q.append(b)
                continue
            k = min(bend_r * math.tan(ang / 2), (b - a).length / 2, (c - b).length / 2)
            p0, p1 = b - d0 * k, b + d1 * k
            for i in range(5):
                t = i / 4
                q = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p1   # quadratic Bezier ~ arc
                Q.append(q)
        Q.append(P[-1])
        P = Q
    P = [p for i, p in enumerate(P) if i == 0 or (p - P[i - 1]).length > 1e-6]
    n = len(P)
    D_ = [(P[i + 1] - P[i]).normalized() for i in range(n - 1)]
    # rotation-minimising (parallel transport) frame: no twist through the bends
    d = D_[0]
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    x = d.cross(ref).normalized()
    circle = []  # ring points of segment i's circle, as offsets in its (x, y) frame
    rings = []
    for i in range(n):
        if i > 0 and i < n - 1:
            a, b = D_[i - 1], D_[i]
            ax = a.cross(b)
            if ax.length > 1e-9:  # transport x from segment i-1 to segment i
                x = Matrix.Rotation(a.angle(b), 3, ax.normalized()) @ x
        di = D_[min(i, n - 2)]
        x = (x - di * x.dot(di)).normalized()
        y = di.cross(x).normalized()
        offs = [x * (r * math.cos(2 * math.pi * k / seg)) + y * (r * math.sin(2 * math.pi * k / seg)) for k in range(seg)]
        if 0 < i < n - 1:
            # exact mitre: slide each point of the incoming segment's circle along that segment onto the bisector plane
            a = D_[i - 1]
            nb = (a + D_[i]).normalized()  # bisector plane normal
            pts_i = [P[i] + o - a * (o.dot(nb) / max(a.dot(nb), 0.2)) for o in circle]
        else:
            pts_i = [P[i] + o for o in offs]
        rings.append([bm.verts.new(p) for p in pts_i])
        circle = offs
    for i in range(n - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(seg):
            j = (k + 1) % seg
            bm.faces.new((A[k], A[j], B[j], B[k]))
    if cap:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])


def ring_clamp(bm, center, axis, r, width=0.025, thick=0.004, seg=16):
    """Pipe clamp band (short tube slightly larger than the pipe) at a point on the pipe axis."""
    a = Vector(axis).normalized()
    c = Vector(center)
    tube(bm, [c - a * width / 2, c + a * width / 2], r + thick, seg=seg)


# ---------------------------------------------------------------------------------------------------- gutters
def half_round_gutter(bm, frame, u0, u1, w_axis, z_top, r=0.0625, t=0.004, bead=0.008, seg=10):
    """Half-round eaves gutter along u (open top, rolled front bead), as a closed thin-walled solid.
    w_axis: gutter centre line (outward offset from the wall face), z_top: rim height. r: radius (125 mm system)."""
    prof = []
    for k in range(seg + 1):                      # outer arc, back rim -> front rim (through the bottom)
        a = math.pi * k / seg
        prof.append((w_axis - r * math.cos(a), z_top - r * math.sin(a)))
    # front bead (a small square roll outward of the front rim)
    fw, fz = prof[-1]
    prof += [(fw + bead, fz), (fw + bead, fz + bead), (fw - t, fz + bead)]
    for k in range(seg, -1, -1):                  # inner arc back
        a = math.pi * k / seg
        prof.append((w_axis - (r - t) * math.cos(a), z_top - (r - t) * math.sin(a)))
    prism_profile(bm, frame, prof[::-1], u0, u1)


def gutter_hangers(bm, frame, u_list, w_axis, z_top, r=0.0625, strap=0.025, t=0.004, back=0.05):
    """Steel gutter brackets: strap under the gutter from the fascia/rafter to the front rim (every ~0.6 m)."""
    for u in u_list:
        seg = 8
        prof = []
        for k in range(seg + 1):
            a = math.pi * k / seg
            prof.append((w_axis - (r + t) * math.cos(a), z_top - (r + t) * math.sin(a)))
        for k in range(seg, -1, -1):
            a = math.pi * k / seg
            prof.append((w_axis - (r + 0.0005) * math.cos(a), z_top - (r + 0.0005) * math.sin(a)))
        prism_profile(bm, frame, prof[::-1], u - strap / 2, u + strap / 2)
        box(bm, frame, u - strap / 2, u + strap / 2, w_axis - r - back, w_axis - r - t, z_top - t, z_top)  # tail


def eave_box(parts, ring, z_soffit, overhang, fascia_h=0.2, board_t=0.025, gutter_r=0.0625, gutter_drop=0.03,
             hanger_pitch=0.6, gutter=True):
    """Boxed eave around a CCW wall ring (world XY, the wall faces): soffit lining from the wall face out to the
    fascia and the fascia board, one closed L-section swept round the ring with mitred corners; a half-round gutter
    hung on the fascia (rim `gutter_drop` below the fascia top) with brackets every hanger_pitch.
    parts {'soffit', 'gutter'} bmesh. Returns the gutter centre-line ring (for downpipe outlets)."""
    from .sweep import sweep_profile  # local import: sweep is shared with build_site
    ov, t, fh = overhang, board_t, fascia_h
    # (across, dz): across > 0 is LEFT of travel = inside a CCW ring, so the eave extends to across = -ov
    prof = [(0.0, 0.0), (0.0, t), (-(ov - t), t), (-(ov - t), fh), (-ov, fh), (-ov, 0.0)]
    sweep_profile(parts["soffit"], [tuple(p) for p in ring], prof[::-1], lambda x, y: z_soffit, closed=True)
    if not gutter:
        return None
    rg = gutter_r
    gring = _offset_closed(ring, ov + rg + 0.005)     # gutter centre line just outside the fascia
    z_rim = z_soffit + fh - gutter_drop
    gprof = []
    seg = 10
    for k in range(seg + 1):
        a = math.pi * k / seg
        gprof.append((rg * math.cos(a), -rg * math.sin(a)))       # outer arc (across, dz) around the centre line
    gprof += [(-rg - 0.008, 0.0), (-rg - 0.008, 0.008), (-rg + 0.004, 0.008)]
    for k in range(seg, -1, -1):
        a = math.pi * k / seg
        gprof.append(((rg - 0.004) * math.cos(a), -(rg - 0.004) * math.sin(a)))
    sweep_profile(parts["gutter"], [tuple(p) for p in gring], gprof, lambda x, y: z_rim, closed=True)
    # brackets: straps under the gutter every hanger_pitch along each edge
    n = len(gring)
    for i in range(n):
        p, q = Vector(gring[i]), Vector(gring[(i + 1) % n])
        L = (q - p).length
        d = (q - p).normalized()
        out = Vector((d.y, -d.x))                          # right of travel = outside for CCW
        m = Matrix.Identity(4)
        m.col[0].xyz = Vector((d.x, d.y, 0))
        m.col[1].xyz = Vector((out.x, out.y, 0))
        m.col[3].xyz = Vector((p.x, p.y, 0))
        us = [0.3 + k * hanger_pitch for k in range(int(max(0.0, L - 0.6) / hanger_pitch) + 1)]
        gutter_hangers(parts["gutter"], m, us, 0.0, z_rim, r=rg, back=0.04)
    return gring


def _offset_closed(ring, d):
    """Outward mitre offset of a CCW ring by d (m)."""
    from .kit import offset_ring
    return offset_ring([tuple(p) for p in ring], -d)


# ---------------------------------------------------------------------------------------------------- sheets
def corrugated_sheet(bm, frame, u0, u1, w0, z0, w1, z1, pitch=0.2, rib_h=0.021, rib_top=0.03, t=0.004):
    """Trapezoid-ribbed steel sheet (C21-type) from (w0, z0) to (w1, z1) in the w-z plane, ribs running down the
    slope, sheet spanning u0..u1. One closed solid (profile across u, extruded along the slope)."""
    L = Vector((w1 - w0, z1 - z0))
    d = L.normalized()
    nrm = Vector((-d.y, d.x))                     # sheet normal in (w, z), pointing up for a falling slope
    if nrm.y < 0:
        nrm = -nrm
    n = max(1, round((u1 - u0) / pitch))
    p = (u1 - u0) / n
    top = []
    for k in range(n):
        a = u0 + k * p
        top += [(a, 0.0), (a + (p - rib_top) / 2 - rib_h * 0.4, 0.0), (a + (p - rib_top) / 2, rib_h),
                (a + (p + rib_top) / 2, rib_h), (a + (p + rib_top) / 2 + rib_h * 0.4, 0.0)]
    top.append((u1, 0.0))
    prof = top + [(u, h - t) for u, h in reversed(top)]   # (u, height above the sheet plane)
    A = [_v(bm, frame, u, w0 + nrm.x * hh, z0 + nrm.y * hh) for u, hh in prof]
    B = [_v(bm, frame, u, w1 + nrm.x * hh, z1 + nrm.y * hh) for u, hh in prof]
    m = len(prof)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((A[i], A[j], B[j], B[i]))
    bm.faces.new(list(reversed(A)))
    bm.faces.new(B)


# ---------------------------------------------------------------------------------------------------- stairs
def stone_stair(bm, frame, u0, u1, risers, riser_h, tread, w_top, z_top, w_back=None, nosing=0.02, chamfer=0.006,
                slab=0.04, bury=0.2):
    """Stair going outward (+w) and down from the landing edge (w_top, z_top), as ONE solid profile prism: every
    nosing is a chamfered stone edge overhanging its riser by `nosing` with the slab thickness `slab` undercut (the
    real granite tread-over-riser detail). risers counts the landing's own riser: total rise = risers * riser_h.
    w_back: back of the landing (default w_top - 1). Returns the w of the bottom riser foot."""
    wb = w_top - 1.0 if w_back is None else w_back
    zg = z_top - risers * riser_h
    prof = [(wb, zg - bury), (wb, z_top)]
    w, z = w_top, z_top
    for k in range(risers):
        # nosing of the surface at height z whose riser line is at w
        prof += [(w + nosing - chamfer, z), (w + nosing, z - chamfer), (w + nosing, z - slab), (w, z - slab)]
        z -= riser_h
        if k < risers - 1:
            prof.append((w, z))
            w += tread
    prof += [(w, zg), (w, zg - bury)]  # bottom riser runs into the paving (buried: never floats on sloped grade)
    prism_profile(bm, frame, _ccw(prof), u0, u1)
    return w


# ---------------------------------------------------------------------------------------------------- railings
def square_tube(bm, p, q, a, b=None, up=None):
    """Rectangular steel section a x b (m) from point p to point q (world Vectors), closed box, square ends.
    up: direction of the section's b side (default world Z, or X for vertical members)."""
    p, q = Vector(p), Vector(q)
    d = (q - p).normalized()
    u = Vector(up) if up is not None else (Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0)))
    x = d.cross(u).normalized()
    y = x.cross(d).normalized()
    b = a if b is None else b
    c = [bm.verts.new(pt + x * sx * a / 2 + y * sy * b / 2) for pt in (p, q) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([c[k] for k in f])


def railing_detailed(bm, pts, height=0.9, post=0.04, post_round=False, rail_r=0.02, spacing=1.2, mid=(0.45,),
                     bars=None, base_plate=0.1, plate_t=0.008, ends="down", wall_ends=False):
    """Steel railing along a world polyline (z = walking surface): posts (square `post` or round) on welded base
    plates, a round top handrail (radius rail_r) ending bent down to the last posts (ends='down') or in wall
    brackets (wall_ends), mid rails at the given heights, optional vertical bars {'pitch', 'r', 'z0', 'z1'}.
    Each member is its own closed solid touching the next (welded joints)."""
    P = [Vector(p) for p in pts]
    posts = []
    for si, (p, q) in enumerate(zip(P[:-1], P[1:])):
        run = (q - p).length
        n = max(1, round(Vector((q.x - p.x, q.y - p.y, 0)).length / spacing))
        for k in range(0 if si == 0 else 1, n + 1):
            posts.append(p + (q - p) * (k / n))
    zt = height - rail_r
    for c in posts:
        box_c = [c.x - base_plate / 2, c.x + base_plate / 2, c.y - base_plate / 2, c.y + base_plate / 2]
        _box_world(bm, box_c[0], box_c[1], box_c[2], box_c[3], c.z, c.z + plate_t)
        top = c + Vector((0, 0, zt - rail_r * 0.3))
        if post_round:
            tube(bm, [c + Vector((0, 0, plate_t)), top], post / 2, seg=12)
        else:
            square_tube(bm, c + Vector((0, 0, plate_t)), top, post, up=Vector((1, 0, 0)))
    # handrail: through the post tops, bent down to the first/last post at mid height
    line = [c + Vector((0, 0, zt)) for c in [P[0]] + P[1:-1] + [P[-1]]]
    if ends == "down" and not wall_ends:
        line = [P[0] + Vector((0, 0, 0.35))] + line + [P[-1] + Vector((0, 0, 0.35))]
    tube(bm, line, rail_r, seg=14, bend_r=0.08)
    for zm in mid:
        tube(bm, [p + Vector((0, 0, zm)) for p in P], rail_r * 0.8, seg=10)
    if bars:
        for p, q in zip(P[:-1], P[1:]):
            L = (q - p).length
            nb = max(1, int(L / bars["pitch"]))
            for k in range(1, nb):
                c = p + (q - p) * (k / nb)
                tube(bm, [c + Vector((0, 0, bars.get("z0", 0.1))), c + Vector((0, 0, bars.get("z1", zt - rail_r)))],
                     bars.get("r", 0.008), seg=8)


def _spiral(cx, cz, r0, r1, turns, a0, sign=1.0, n=28):
    """Archimedean spiral points (u, z) from radius r1 (outer end) in to r0 over `turns` turns, starting at angle a0."""
    out = []
    for k in range(n + 1):
        t = k / n
        a = a0 + sign * 2 * math.pi * turns * t
        r = r1 + (r0 - r1) * t
        out.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return out


def scroll_panel(bm, frame, u0, u1, z0, z1, w=0.0, bar=0.012, rail=(0.04, 0.012), motif="S", rod_r=0.006):
    """Wrought-iron railing infill between u0..u1 and z0..z1 in the frame's u-z plane at offset w: flat-bar top and
    bottom rails, end uprights, and per bay a mirrored pair of scrolls (S = two opposed C-curls joined, C = one curl
    each side) swept as round rods (rod_r). Bays are ~0.35 m wide. Every piece a closed solid."""
    ra, rt = rail
    def P(u, z):
        return frame @ Vector((u, w, z))
    for zz in (z0 + ra / 2, z1 - ra / 2):
        square_tube(bm, P(u0, zz), P(u1, zz), rt, ra, up=frame.to_3x3() @ Vector((0, 0, 1)))
    for uu in (u0 + ra / 2, u1 - ra / 2):
        square_tube(bm, P(uu, z0 + ra), P(uu, z1 - ra), rt, ra, up=frame.to_3x3() @ Vector((1, 0, 0)))
    nb = max(1, round((u1 - u0 - ra) / 0.35))
    bw = (u1 - u0 - ra) / nb
    zi0, zi1 = z0 + ra, z1 - ra
    H = zi1 - zi0
    for k in range(nb):
        a, b = u0 + ra / 2 + k * bw, u0 + ra / 2 + (k + 1) * bw
        if k > 0:
            tube(bm, [P(a, zi0), P(a, zi1)], rod_r, seg=8)          # bay divider bar
        c = (a + b) / 2
        R = min(bw * 0.24, H * 0.2)
        for side in (-1.0, 1.0):                                    # mirrored pair
            cu = c + side * bw * 0.22
            if motif == "S":
                top = _spiral(cu, zi1 - R * 1.05, R * 0.25, R, 1.1, math.pi / 2 if side > 0 else math.pi / 2, sign=side)
                bot = _spiral(cu, zi0 + R * 1.05, R * 0.25, R, 1.1, -math.pi / 2, sign=-side)
                spine = [(cu, zi1 - R * 0.05), (cu - side * R * 0.3, zi0 + H / 2), (cu, zi0 + R * 0.05)]
                for curve in (top, bot):
                    tube(bm, [P(u_, z_) for u_, z_ in curve], rod_r, seg=6)
                tube(bm, [P(u_, z_) for u_, z_ in spine], rod_r, seg=6, bend_r=0.05)
            else:
                curl = _spiral(cu, zi0 + H / 2, R * 0.25, R, 1.25, 0.0 if side > 0 else math.pi, sign=side)
                tube(bm, [P(u_, z_) for u_, z_ in curl], rod_r, seg=6)


def _box_world(bm, x0, x1, y0, y1, z0, z1):
    c = [bm.verts.new((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([c[i] for i in f])


# ---------------------------------------------------------------------------------------------------- ramps
def steel_ramp(parts, frame, u0, u1, w0, w1, z_high, z_low, stringer=(0.12, 0.06), cross_pitch=0.8, deck_t=0.03,
               leg=0.06, leg_pitch=1.5, ground=None):
    """Steel access ramp running along u (high end u0 at z_high, low end u1 at z_low), width w0..w1.
    parts {'frame', 'deck'}: two RHS stringers + cross members + square legs on the ground, and the grating
    deck panel (open grating = UE masked material on this panel). ground(u) -> ground z under the ramp."""
    L = u1 - u0
    sh, sw = stringer
    zf = lambda u: z_high + (z_low - z_high) * (u - u0) / L
    g = ground or (lambda u: z_low - 0.0)
    for w in (w0 + sw / 2, w1 - sw / 2):
        a = frame @ Vector((u0, w, zf(u0) - deck_t - sh / 2))
        b = frame @ Vector((u1, w, zf(u1) - deck_t - sh / 2))
        square_tube(parts["frame"], a, b, sw, sh, up=frame.to_3x3() @ Vector((0, 0, 1)))
    n = max(1, round(L / cross_pitch))
    for k in range(n + 1):
        u = u0 + L * k / n
        uc = min(max(u, u0 + 0.03), u1 - 0.03)
        zc = zf(uc) - deck_t - 0.03
        square_tube(parts["frame"], frame @ Vector((uc, w0 + sw, zc)), frame @ Vector((uc, w1 - sw, zc)), 0.05, 0.05)
    m = max(1, round(L / leg_pitch))
    for k in range(m + 1):
        u = min(max(u0 + L * k / m, u0 + 0.05), u1 - 0.05)
        ztop = zf(u) - deck_t - sh
        zb = g(u)
        if ztop - zb < 0.05:
            continue
        for w in (w0 + sw / 2, w1 - sw / 2):
            square_tube(parts["frame"], frame @ Vector((u, w, zb)), frame @ Vector((u, w, ztop)), leg)
            ctr = frame @ Vector((u, w, zb))
            _box_world(parts["frame"], ctr.x - 0.075, ctr.x + 0.075, ctr.y - 0.075, ctr.y + 0.075, zb, zb + 0.006)
    prof = [(u0, z_high), (u1, z_low), (u1, z_low - deck_t), (u0, z_high - deck_t)]
    a = [_v(parts["deck"], frame, uu, w0, zz) for uu, zz in prof]
    b = [_v(parts["deck"], frame, uu, w1, zz) for uu, zz in prof]
    for i in range(4):
        j = (i + 1) % 4
        parts["deck"].faces.new((a[i], a[j], b[j], b[i]))
    parts["deck"].faces.new(list(reversed(a)))
    parts["deck"].faces.new(b)


# ---------------------------------------------------------------------------------------------------- lamps
def floodlight(bm, frame, u, w, z, size=(0.24, 0.07, 0.2), arm=0.12, tilt_deg=30):
    """LED flood lamp: finned housing box tilted down on a U-bracket, arm back to the mount (canopy/sign top)."""
    sw, sd, shh = size
    # mount plate + arm
    box(bm, frame, u - 0.04, u + 0.04, w - 0.01, w + 0.005, z, z + 0.08)
    box(bm, frame, u - 0.012, u + 0.012, w, w + arm, z + 0.03, z + 0.05)
    t = math.radians(tilt_deg)
    c = Vector((u, w + arm + sd / 2, z + 0.04))
    R = Matrix.Rotation(-t, 3, "X")
    M = frame @ Matrix.Translation(c) @ R.to_4x4()
    box(bm, M, -sw / 2, sw / 2, -sd / 2, sd / 2, -shh / 2, shh / 2)          # housing
    for k in range(5):                                                   # cooling fins on the back
        zz = -shh / 2 + shh * (k + 0.5) / 5
        box(bm, M, -sw / 2 + 0.01, sw / 2 - 0.01, -sd / 2 - 0.012, -sd / 2, zz - 0.004, zz + 0.004)


# ---------------------------------------------------------------------------------------------------- fittings
def ac_unit(parts, frame, u, z, w=0.80, h=0.55, d=0.28, off=0.12):
    """Split-AC outdoor unit on two steel L-brackets: casing box standing `off` off the wall, fan opening on the
    front as a recessed ring with a grille ring, side service cover. parts {'casing', 'steel'}; u = centre, z = base."""
    c = parts["casing"]
    w0, w1 = off, off + d
    box(c, frame, u - w / 2, u + w / 2, w0, w1, z, z + h)
    # fan guard: 12 radial-ish ribs as thin boxes proud of the front + an outer ring
    fu, fz, fr_ = u - w * 0.12, z + h / 2, min(w, h) * 0.38
    seg = 20
    for k in range(seg):
        a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
        prof = [(fu + fr_ * math.cos(a0), fz + fr_ * math.sin(a0)), (fu + fr_ * math.cos(a1), fz + fr_ * math.sin(a1)),
                (fu + (fr_ - 0.012) * math.cos(a1), fz + (fr_ - 0.012) * math.sin(a1)),
                (fu + (fr_ - 0.012) * math.cos(a0), fz + (fr_ - 0.012) * math.sin(a0))]
        a = [_v(c, frame, pu, w1, pz) for pu, pz in prof]
        b = [_v(c, frame, pu, w1 + 0.01, pz) for pu, pz in prof]
        for i in range(4):
            j = (i + 1) % 4
            c.faces.new((a[i], a[j], b[j], b[i]))
        c.faces.new(list(reversed(a)))
        c.faces.new(b)
    for k in range(6):  # grille bars across the fan
        zz = fz - fr_ + 2 * fr_ * (k + 0.5) / 6
        box(c, frame, fu - fr_ * 0.95, fu + fr_ * 0.95, w1 + 0.002, w1 + 0.008, zz - 0.003, zz + 0.003)
    s = parts["steel"]
    for uu in (u - w / 2 + 0.08, u + w / 2 - 0.08):   # L-brackets: arm under the unit + diagonal strut to the wall
        box(s, frame, uu - 0.02, uu + 0.02, 0.0, w1 + 0.03, z - 0.04, z)
        square_tube(s, frame @ Vector((uu, 0.0, z - 0.45)), frame @ Vector((uu, w1 - 0.02, z - 0.03)), 0.03, 0.03)
        box(s, frame, uu - 0.03, uu + 0.03, 0.0, 0.004, z - 0.5, z)          # wall plate


def wall_lamp(parts, frame, u, z, w=0.26, h=0.16, d=0.10):
    """Bulkhead wall lamp: base plate, body, diffuser (separate slot for the emissive UE material)."""
    box(parts["body"], frame, u - w / 2, u + w / 2, 0.0, d * 0.4, z - h / 2, z + h / 2)
    box(parts["diffuser"], frame, u - w / 2 + 0.015, u + w / 2 - 0.015, d * 0.4, d, z - h / 2 + 0.015, z + h / 2 - 0.015)


def vent_grille(parts, frame, u0, u1, z0, z1, slat=0.03, depth=0.03):
    """Louvred vent grille: frame ring set 1 cm proud of the wall and sloped slats (closed solids)."""
    ring = parts["frame"]
    t = 0.02
    for a, b, c, d in ((u0, u1, z0, z0 + t), (u0, u1, z1 - t, z1), (u0, u0 + t, z0 + t, z1 - t), (u1 - t, u1, z0 + t, z1 - t)):
        box(ring, frame, a, b, 0.0, 0.01, c, d)
    n = max(1, int((z1 - z0 - 2 * t) / slat))
    for k in range(n):
        zz = z0 + t + (z1 - z0 - 2 * t) * (k + 0.5) / n
        prism_profile(parts["slats"], frame, [(-depth, zz + slat * 0.35), (0.008, zz - slat * 0.25), (0.008, zz - slat * 0.25 - 0.004),
                                              (-depth, zz + slat * 0.35 - 0.004)], u0 + t, u1 - t)


def sign_plate(parts, frame, u0, u1, z0, z1, t=0.006, standoff=0.012):
    """Flat sign plate on four stand-off pins (content = KOCH branding in UE)."""
    box(parts["plate"], frame, u0, u1, standoff, standoff + t, z0, z1)
    for uu in (u0 + 0.03, u1 - 0.03):
        for zz in (z0 + 0.03, z1 - 0.03):
            tube(parts["pins"], [frame @ Vector((uu, 0.0, zz)), frame @ Vector((uu, standoff, zz))], 0.005, seg=8)


def cctv_camera(parts, frame, u, z, arm=0.18):
    """Bullet CCTV camera on a wall bracket: plate, arm, housing tube with a sun visor."""
    s = parts["body"]
    box(s, frame, u - 0.04, u + 0.04, 0.0, 0.01, z - 0.05, z + 0.05)
    tube(s, [frame @ Vector((u, 0.01, z)), frame @ Vector((u, arm, z))], 0.015, seg=10)
    tube(s, [frame @ Vector((u, arm - 0.05, z - 0.03)), frame @ Vector((u, arm + 0.12, z - 0.07))], 0.035, seg=14)
    box(s, frame, u - 0.045, u + 0.045, arm - 0.06, arm + 0.14, z + 0.0, z + 0.006)


def _ccw(prof):
    a = sum(prof[i - 1][0] * prof[i][1] - prof[i][0] * prof[i - 1][1] for i in range(len(prof)))
    return prof if a > 0 else prof[::-1]
