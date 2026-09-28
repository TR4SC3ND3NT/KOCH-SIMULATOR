# Smooth campus ground (R1): DEM quadratic + a harmonic correction r that meets every terrain pad exactly.
# Replaces the old per-pad linear blends, whose overlaps left creases, ridges and bumps. Laplace's equation has no
# interior extrema, so outside the pads the ground has no bumps or pits and runs as an even slope between levels.
#   - pad interiors (the last pad containing a node wins, as before): r fixed to plane - DEM
#   - hard pads (blend 0): graph edges across their rings are cut, so the step stays vertical and the ground outside
#     is not pulled toward the pad level (Neumann side)
#   - soft pads (blend > 0): connected, the harmonic solve is the transition. Nodes of an EARLIER pad inside a later
#     soft pad's blend band are released, so the later pad can still ramp into it (the old sequential-blend intent)
#   - grid border: r = 0 (DEM topography); 'pad_influence_m' in terrain.json screens r back to 0 away from the pads
#   - carriageways are not special here (callers subtract the curb reveal)
# Used by common.Terrain (base/ground) for TER_Ground, building walls and every site element's ground z.
import json
import os

import numpy as np

SPECS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs"))


def all_pads(specs=SPECS):
    """terrain_pads of every spec in file-name order (the order they have always been applied in)."""
    pads = []
    for fn in sorted(os.listdir(specs)) if os.path.isdir(specs) else []:
        if fn.endswith(".json"):
            try:
                pads += json.load(open(os.path.join(specs, fn), encoding="utf-8")).get("terrain_pads", [])
            except ValueError:   # a half-written spec of another zone: skipped, as everywhere else
                pass
    return pads


def pad_plane_z(pad, x, y):
    """Flat 'z', or the sloped plane 'grad' [dz/dx, dz/dy] about 'ref' [x, y] (ramps, sloping paths, lawn banks)."""
    if "grad" not in pad:
        return pad["z"] + 0.0 * np.asarray(x, float)
    (gx, gy), (x0, y0) = pad["grad"], pad["ref"]
    return pad["z"] + gx * (np.asarray(x, float) - x0) + gy * (np.asarray(y, float) - y0)


def in_ring(ring, x, y):
    """Even-odd point-in-polygon, numpy arrays or scalars."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    inside = np.zeros(np.shape(x), bool)
    n = len(ring)
    for i in range(n):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % n]
        cross = (y1 > y) != (y2 > y)
        xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1 if y2 != y1 else 1e-12)
        inside ^= cross & (x < xi)
    return inside


def ring_dist(ring, x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    d = np.full(np.shape(x), np.inf)
    n = len(ring)
    for i in range(n):
        a, b = np.array(ring[i], float), np.array(ring[(i + 1) % n], float)
        ab = b - a
        t = np.clip(((x - a[0]) * ab[0] + (y - a[1]) * ab[1]) / max(ab @ ab, 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(x - (a[0] + t * ab[0]), y - (a[1] + t * ab[1])))
    return d


class TerrainField:
    def __init__(self, dem, grid, pads, screen_m=None, tol=1e-7, max_iter=20000):
        x0, y0, x1, y1 = grid["extent"]
        s = float(grid["spacing_m"])
        self.x0, self.y0, self.s = x0, y0, s
        xs, ys = np.arange(x0, x1 + s / 2, s), np.arange(y0, y1 + s / 2, s)
        self.nx, self.ny = len(xs), len(ys)
        X, Y = np.meshgrid(xs, ys)
        D = dem(X, Y)
        self.pads = pads
        self.hard_idx = [k for k, p in enumerate(pads) if float(p.get("blend", 0.0)) <= 0.0]
        ins = [in_ring(np.array(p["ring"], float), X, Y) for p in pads]
        owner = np.full(X.shape, -1)
        for k, m in enumerate(ins):
            owner[m] = k
        # side label: which hard rings contain the node (edges between different labels are cut)
        side = np.zeros(X.shape, np.int64)
        for bit, k in enumerate(self.hard_idx):
            side |= ins[k].astype(np.int64) << bit
        # a later soft pad's blend band releases the nodes of earlier pads (soft or hard) on its own side of the
        # hard edges: the old sequential blends ramped banks into earlier pads (e.g. the alley's lawn banks down
        # onto the hard lower walkway), and site elements stand on those banks. Only nodes within 'blend' of the
        # part the later pad really holds are released (a pad fully covered by later pads has no level to ramp to:
        # releasing would only let the ground sag toward the DEM)
        fixed = owner >= 0
        released = np.zeros(X.shape, bool)
        for q, p in enumerate(pads):
            b = float(p.get("blend", 0.0))
            own_q = ins[q] & (owner == q)
            if b <= 0 or not own_q.any():
                continue
            lab = int(np.bincount(side[own_q]).argmax())
            near = own_q.copy()
            for _ in range(int(np.ceil(b / s))):   # Chebyshev dilation by the blend width
                g = near.copy()
                g[1:] |= near[:-1]; g[:-1] |= near[1:]
                near = g.copy()
                near[:, 1:] |= g[:, :-1]; near[:, :-1] |= g[:, 1:]
            rel = near & ~ins[q] & (owner >= 0) & (owner < q) & (side == lab)
            fixed &= ~rel
            released |= rel
        self.released = released
        target = np.zeros(X.shape)
        for k, p in enumerate(pads):
            m = fixed & (owner == k)
            target[m] = pad_plane_z(p, X[m], Y[m]) - D[m]
        border = np.zeros(X.shape, bool)
        border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
        fixed |= border & (owner < 0)
        wE = (side[:, :-1] == side[:, 1:]).astype(float)   # edge (j, i)-(j, i+1)
        wN = (side[:-1, :] == side[1:, :]).astype(float)   # edge (j, i)-(j+1, i)
        free = ~fixed
        r = np.where(fixed, target, 0.0)
        # Laplace on the free nodes: deg*r - sum(w*r_nb) = 0, fixed neighbours go to the right-hand side
        deg = np.zeros(X.shape)
        deg[:, :-1] += wE; deg[:, 1:] += wE; deg[:-1, :] += wN; deg[1:, :] += wN
        # screening: (L + 1/lambda^2) r = 0 lets the pad correction fade back to the DEM over ~lambda m (unmeasured
        # ground keeps its DEM height) while r keeps the maximum principle (no bumps or pits of its own)
        eps = 1.0 / screen_m ** 2 if screen_m else 1e-6

        def nb_sum(v):
            out = np.zeros_like(v)
            out[:, :-1] += wE * v[:, 1:]; out[:, 1:] += wE * v[:, :-1]
            out[:-1, :] += wN * v[1:, :]; out[1:, :] += wN * v[:-1, :]
            return out

        def A(v):   # v is zero on fixed nodes
            return np.where(free, (deg + eps) * v - nb_sum(v), 0.0)

        b = np.where(free, nb_sum(np.where(fixed, r, 0.0)), 0.0)
        Minv = np.where(free, 1.0 / (deg + eps), 0.0)
        u = np.zeros(X.shape)
        res = b - A(u)
        z = Minv * res
        p = z.copy()
        rz = float((res * z).sum())
        bn = float(np.sqrt((b * b).sum())) or 1.0
        it = 0
        for it in range(max_iter):
            Ap = A(p)
            alpha = rz / float((p * Ap).sum())
            u += alpha * p
            res -= alpha * Ap
            if np.sqrt(float((res * res).sum())) / bn < tol:
                break
            z = Minv * res
            rz_new = float((res * z).sum())
            p = z + (rz_new / rz) * p
            rz = rz_new
        self.iterations = it + 1
        r = np.where(free, u, r)
        self.node_side = side
        self.r = r
        # outside view of hard-pad interiors: extrapolate from the outside neighbours, so bilinear sampling next to
        # a hard edge never mixes in the other side's level (the step)
        ghost = side != 0
        ro = r.copy()
        known = ~ghost
        for _ in range(3):
            acc = np.zeros_like(ro); cnt = np.zeros_like(ro)
            for sl_a, sl_b in (((slice(None), slice(None, -1)), (slice(None), slice(1, None))),
                               ((slice(None, -1), slice(None)), (slice(1, None), slice(None)))):
                for a, b2 in ((sl_a, sl_b), (sl_b, sl_a)):
                    kn = known[b2]
                    acc[a] += np.where(kn, ro[b2], 0.0); cnt[a] += kn
            grow = ~known & (cnt > 0)
            ro[grow] = acc[grow] / cnt[grow]
            known = known | grow
        self.r_out = ro

    def residual(self, x, y, side=None):
        """DEM correction at (x, y), bilinear over the cell nodes on the point's own side of the hard edges (a cell
        straddling a step never mixes the two levels). side = hard-ring bitmask of the point (default: ring test;
        mesh vertex copies on a ring pass theirs). No same-side node in the cell: the outside view r_out."""
        x, y = np.asarray(x, float), np.asarray(y, float)
        side = self.side(x, y) if side is None else np.asarray(side, np.int64)
        fx = np.clip((x - self.x0) / self.s, 0, self.nx - 1.000001)
        fy = np.clip((y - self.y0) / self.s, 0, self.ny - 1.000001)
        i, j = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - i, fy - j
        acc = np.zeros(np.shape(x)); wsum = np.zeros(np.shape(x)); fall = np.zeros(np.shape(x))
        for dj, di, w in ((0, 0, (1 - tx) * (1 - ty)), (0, 1, tx * (1 - ty)), (1, 0, (1 - tx) * ty), (1, 1, tx * ty)):
            same = self.node_side[j + dj, i + di] == side
            acc += np.where(same, w * self.r[j + dj, i + di], 0.0)
            wsum += np.where(same, w, 0.0)
            fall += w * self.r_out[j + dj, i + di]
        return np.where(wsum > 1e-9, acc / np.maximum(wsum, 1e-9), fall)

    def owner(self, x, y):
        """Index of the last pad containing (x, y), else -1."""
        x, y = np.asarray(x, float), np.asarray(y, float)
        own = np.full(np.shape(x), -1)
        for k, p in enumerate(self.pads):
            own[in_ring(np.array(p["ring"], float), x, y)] = k
        return own

    def side(self, x, y):
        """Bitmask of the hard rings containing (x, y) (the step side), as in the solve."""
        x, y = np.asarray(x, float), np.asarray(y, float)
        sd = np.zeros(np.shape(x), np.int64)
        for bit, k in enumerate(self.hard_idx):
            sd |= in_ring(np.array(self.pads[k]["ring"], float), x, y).astype(np.int64) << bit
        return sd

    def plane_owner(self, own, x, y, side):
        """own (last containing pad per point) with the points a later soft pad's band released set to -1: the
        field, not the pad plane, holds them (nearest grid node, same side). side = hard-ring bitmask per point."""
        own = np.array(own, copy=True)
        x, y = np.asarray(x, float), np.asarray(y, float)
        i = np.clip(np.round((x - self.x0) / self.s).astype(int), 0, self.nx - 1)
        j = np.clip(np.round((y - self.y0) / self.s).astype(int), 0, self.ny - 1)
        rel = self.released[j, i] & (self.node_side[j, i] == np.asarray(side, np.int64)) & (own >= 0)
        own[rel] = -1
        return own

    def hard_owner(self, x, y):
        """Index of the hard pad whose plane holds (x, y) (last containing pad, not released), else -1."""
        own = self.plane_owner(self.owner(x, y), x, y, self.side(x, y))
        return np.where(np.isin(own, self.hard_idx), own, -1)
