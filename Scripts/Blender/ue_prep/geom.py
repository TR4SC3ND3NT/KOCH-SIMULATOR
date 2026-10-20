# Mesh data as numpy arrays + rigid canonicalisation/hashing for dedup (ue_prep, run inside Blender by run.py).
# A Geo is face-loop topology (loop_start/loop_total/loop_vert) with per-face slot names and smooth flags, so it can
# be transformed, hashed and rebuilt as a Blender mesh without bmesh round trips.
import hashlib
import zlib

import numpy as np

from .common import MM, rot_z90

PACK_OFF = 1 << 20   # packed vertex key: 21 bits per axis in mm -> |coord| < 1048 m (local meshes only)


class Geo:
    __slots__ = ("co", "loop_start", "loop_total", "loop_vert", "face_slot", "smooth", "slots")

    def __init__(self, co, loop_start, loop_total, loop_vert, face_slot, smooth, slots):
        self.co = co                  # (V,3) float64, metres
        self.loop_start = loop_start  # (F,) int64
        self.loop_total = loop_total  # (F,) int64
        self.loop_vert = loop_vert    # (L,) int64
        self.face_slot = face_slot    # (F,) int64 index into slots
        self.smooth = smooth          # (F,) bool
        self.slots = slots            # list[str] material slot names

    @property
    def nfaces(self):
        return len(self.loop_start)

    def loop_face(self):
        return np.repeat(np.arange(self.nfaces), self.loop_total)

    def tris(self):
        """Fan triangulation (T,3) vertex ids + (T,) face ids. Exact for convex faces; for concave planar faces the
        signed volume/area sums stay exact (used for volumes, hull inputs and tri counts, never for rendering)."""
        n = self.loop_total
        k = n - 2
        f = np.repeat(np.arange(self.nfaces), k)
        j = np.arange(k.sum()) - np.repeat(np.cumsum(k) - k, k)
        s = self.loop_start[f]
        lv = self.loop_vert
        return np.stack([lv[s], lv[s + j + 1], lv[s + j + 2]], 1), f

    def face_normals(self):
        t, f = self.tris()
        c = self.co
        cr = np.cross(c[t[:, 1]] - c[t[:, 0]], c[t[:, 2]] - c[t[:, 0]])
        n = np.zeros((self.nfaces, 3))
        np.add.at(n, f, cr)
        ln = np.linalg.norm(n, axis=1)
        return n / np.where(ln > 0, ln, 1)[:, None], ln * 0.5   # unit normals, areas

    def volume(self):
        t, _ = self.tris()
        c = self.co
        return float(np.einsum("ij,ij->i", c[t[:, 0]], np.cross(c[t[:, 1]], c[t[:, 2]])).sum() / 6.0)

    def transformed(self, a3, t3=None):
        """Apply x -> a3 x + t3; mirrors (det < 0) reverse the winding so faces stay outward."""
        co = self.co @ a3.T
        if t3 is not None:
            co = co + t3
        lv = self.loop_vert
        if np.linalg.det(a3) < 0:
            lv = self.loop_vert.copy()
            for n in np.unique(self.loop_total):
                idx = self.loop_start[self.loop_total == n][:, None] + np.arange(n)
                lv[idx] = self.loop_vert[idx[:, ::-1]]
        return Geo(co, self.loop_start, self.loop_total, lv, self.face_slot, self.smooth, self.slots)

    def subset(self, faces):
        """Faces (index array) as a compact Geo (unused vertices dropped)."""
        faces = np.asarray(faces)
        tot = self.loop_total[faces]
        offs = np.cumsum(tot) - tot
        idx = np.repeat(self.loop_start[faces] - offs, tot) + np.arange(int(tot.sum()))
        lv = self.loop_vert[idx]
        used, inv = np.unique(lv, return_inverse=True)
        ls = np.concatenate([[0], np.cumsum(tot)[:-1]]).astype(np.int64)
        return Geo(self.co[used], ls, tot.astype(np.int64), inv.astype(np.int64), self.face_slot[faces],
                   self.smooth[faces], self.slots)


def geo_from_mesh(me):
    nv, nf, nl = len(me.vertices), len(me.polygons), len(me.loops)
    co = np.empty(nv * 3, np.float32)
    me.vertices.foreach_get("co", co)
    ls = np.empty(nf, np.int32)
    lt = np.empty(nf, np.int32)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nl, np.int32)
    me.loops.foreach_get("vertex_index", lv)
    mi = np.empty(nf, np.int32)
    me.polygons.foreach_get("material_index", mi)
    sm = np.empty(nf, bool)
    me.polygons.foreach_get("use_smooth", sm)
    slots = [m.name if m else "None" for m in me.materials] or ["None"]
    mi = np.clip(mi, 0, len(slots) - 1)
    return Geo(co.reshape(-1, 3).astype(np.float64), ls.astype(np.int64), lt.astype(np.int64), lv.astype(np.int64),
               mi.astype(np.int64), sm, slots)


def decompose(m4):
    """World matrix -> (rigid 4x4, local scale (3,), ok). Mirrors are folded into scale y (as finalize.py does);
    ok=False if the 3x3 is sheared (caller bakes the whole 3x3 instead)."""
    a = np.asarray(m4, dtype=np.float64)[:3, :3]
    s = np.linalg.norm(a, axis=0)
    r = a / np.where(s > 0, s, 1)
    if np.linalg.det(r) < 0:
        r[:, 1] *= -1
        s[1] *= -1
    ok = np.abs(r.T @ r - np.eye(3)).max() < 1e-5
    rig = np.eye(4)
    rig[:3, :3] = r
    rig[:3, 3] = np.asarray(m4)[:3, 3]
    return rig, s, ok


def _pivot(co):
    lo, hi = co.min(0), co.max(0)
    return np.array([(lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5, lo[2]])


def shape_key(g, co):
    """Order-independent geometry hash: faces as (slot-name crc, cyclically rotated packed mm vertices), sorted."""
    q = np.rint(co * MM).astype(np.int64) + PACK_OFF
    if q.min() < 0 or q.max() >= (1 << 21):
        return None   # too large for the packed key: never deduplicated
    packed = (q[:, 0] << 42) | (q[:, 1] << 21) | q[:, 2]
    lv = packed[g.loop_vert]
    crc = np.array([zlib.crc32(s.encode()) for s in g.slots], np.int64)[g.face_slot]
    h = hashlib.sha1()
    for n in np.unique(g.loop_total):
        sel = np.nonzero(g.loop_total == n)[0]
        rows = lv[g.loop_start[sel][:, None] + np.arange(n)]
        roll = (rows.argmin(1)[:, None] + np.arange(n)) % n
        rows = np.take_along_axis(rows, roll, 1)
        keys = np.column_stack([crc[sel], rows])
        keys = keys[np.lexsort(keys.T[::-1])]
        h.update(int(n).to_bytes(4, "little"))
        h.update(keys.tobytes())
    return h.hexdigest()


def canonical(g):
    """Best of the 4 yaw-90 orientations (smallest hash, ties -> smallest k), pivot = bottom-centre of the rotated
    local bbox (UE placement pivot: the actor sits on its footprint centre). Returns (key, k, pivot, mirror_key);
    mirror_key = same for the X-mirrored shape, used only to flag mirror twins (they stay separate assets)."""
    best = None
    mkey = None
    mir = np.diag([-1.0, 1.0, 1.0])
    gm = g.transformed(mir)
    for k in range(4):
        r = rot_z90(k)
        c = g.co @ r.T
        p = _pivot(c)
        key = shape_key(g, c - p)
        if key is None:
            return None, 0, _pivot(g.co), None
        if best is None or key < best[0]:
            best = (key, k, p)
        cm = gm.co @ r.T
        km = shape_key(gm, cm - _pivot(cm))
        if mkey is None or km < mkey:
            mkey = km
    return best[0], best[1], best[2], mkey
