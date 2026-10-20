# TER_Ground -> 64 m tiles with exact grid-line cuts (ue_prep, inside Blender; used by run.py).
# One bmesh bisect per grid line on the whole terrain, then cut vertices are snapped exactly onto the line, so the
# two tiles of a seam share bit-identical border vertices (same source vertex, float32-exact multiples of 64 m).
# Pivot = tile min corner (x0, y0, 0) in Blender; local coords are then exact in float32 (Sterbenz: v - 64k).
import bmesh
import bpy
import numpy as np
from mathutils import Matrix

from .common import TILE_M, box_uvs, tile_name
from .geom import geo_from_mesh

SNAP = 2e-4   # m; bisect tolerance band snapped onto the grid line


def _lines(lo, hi):
    a = int(np.floor(lo / TILE_M)) + 1
    b = int(np.ceil(hi / TILE_M)) - 1
    return [k * TILE_M for k in range(a, b + 1)]


def _border_set(g, axis, value):
    """Vertices of boundary edges lying on local coordinate `axis` == value, as float32 tuples."""
    lv = g.loop_vert
    nxt = np.arange(len(lv)) + 1
    ends = g.loop_start + g.loop_total
    nxt[ends - 1] = g.loop_start
    a, b = lv, lv[nxt]
    e = np.sort(np.stack([a, b], 1), 1)
    uniq, cnt = np.unique(e, axis=0, return_counts=True)
    bnd = uniq[cnt == 1]
    co = g.co.astype(np.float32)
    on = (co[bnd[:, 0], axis] == np.float32(value)) & (co[bnd[:, 1], axis] == np.float32(value))
    vs = np.unique(bnd[on].ravel())
    other = [i for i in range(3) if i != axis]
    return {tuple(co[v, other].tolist()) for v in vs}


def build_tiles(obj):
    """-> (tiles, seams). tiles: list of dict(name, ij, corner_m, geo (local), uv, tris); seams: verification list."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(Matrix(obj.matrix_world))
    co = np.array([v.co[:] for v in bm.verts])
    lo, hi = co.min(0), co.max(0)
    for axis in (0, 1):
        no = [0.0, 0.0, 0.0]
        no[axis] = 1.0
        for c in _lines(lo[axis], hi[axis]):
            pc = [0.0, 0.0, 0.0]
            pc[axis] = c
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=SNAP * 0.5,
                                   plane_co=pc, plane_no=no)
    me = bpy.data.meshes.new("_ue_prep_terrain")
    bm.to_mesh(me)
    bm.free()
    for i, m in enumerate(obj.data.materials):
        if i < len(me.materials):
            me.materials[i] = m
        else:
            me.materials.append(m)
    g = geo_from_mesh(me)
    bpy.data.meshes.remove(me)
    for axis in (0, 1):   # exact snap of the cut band onto the grid lines
        k = np.rint(g.co[:, axis] / TILE_M)
        near = np.abs(g.co[:, axis] - k * TILE_M) < SNAP
        g.co[near, axis] = k[near] * TILE_M
    lf = g.loop_face()
    cen = np.zeros((g.nfaces, 3))
    np.add.at(cen, lf, g.co[g.loop_vert])
    cen /= g.loop_total[:, None]
    ti = np.floor(cen[:, 0] / TILE_M).astype(int)
    tj = np.floor(cen[:, 1] / TILE_M).astype(int)
    tiles = {}
    for i, j in sorted(set(zip(ti.tolist(), tj.tolist()))):
        faces = np.nonzero((ti == i) & (tj == j))[0]
        corner = np.array([i * TILE_M, j * TILE_M, 0.0])
        sub = g.subset(faces)
        sub.co = sub.co - corner
        n, _ = sub.face_normals()
        uv = box_uvs(sub.co[sub.loop_vert], n, sub.loop_face())   # == world box UVs shifted by whole 64 m
        tiles[(i, j)] = {"name": tile_name(i, j), "ij": [i, j], "corner_m": corner.tolist(), "geo": sub, "uv": uv,
                         "tris": int((sub.loop_total - 2).sum())}
    seams = []
    for (i, j), t in tiles.items():
        for di, dj, axis in ((1, 0, 0), (0, 1, 1)):
            nb = tiles.get((i + di, j + dj))
            if nb is None:
                continue
            a = _border_set(t["geo"], axis, TILE_M)
            b = _border_set(nb["geo"], axis, 0.0)
            seams.append({"a": t["name"], "b": nb["name"], "verts_a": len(a), "verts_b": len(b),
                          "mismatch": len(a ^ b)})
    return [tiles[k] for k in sorted(tiles)], seams
