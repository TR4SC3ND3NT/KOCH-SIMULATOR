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
SKIRT = 0.5   # m; every open terrain edge gets a vertical skirt this deep (see _add_skirts)
KERB_MIN = 0.04   # m; step walls at least this tall are concrete kerbs (owner playtest 2026-10-28: grass/paint walls)
KERB_SLOT = "M_Concrete_Precast"
GRASS = ("Grass",)
SLIVER_HALF_W, SLIVER_MAX_AREA, SLIVER_DZ = 0.3, 15.0, 0.03   # m, m2, m: see _fill_slivers


def _fill_slivers(bm, grass):
    """Narrow grass leftovers inside paving (owner playtest 2026-10-28: a 0.5 m lawn strip across a plaza, level with
    it) take the paving around them. A grass region (up faces, slots in grass) qualifies if area / boundary length is
    under SLIVER_HALF_W (a strip under ~2x that wide), it is under SLIVER_MAX_AREA, and most of its boundary borders
    non-grass up faces within SLIVER_DZ in height. Returns the number of faces repainted."""
    up = {f for f in bm.faces if f.normal.z > 0.7 and f.material_index in grass}
    seen, done = set(), 0
    for f0 in up:
        if f0 in seen:
            continue
        comp, stack = [], [f0]
        seen.add(f0)
        while stack:
            f = stack.pop()
            comp.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g in up and g not in seen:
                        seen.add(g)
                        stack.append(g)
        area = sum(f.calc_area() for f in comp)
        if area > SLIVER_MAX_AREA:
            continue
        cs = set(comp)
        perim, flat, votes = 0.0, 0.0, {}
        for f in comp:
            for e in f.edges:
                others = [g for g in e.link_faces if g not in cs]
                if len(e.link_faces) == 1 or others:
                    ln = e.calc_length()
                    perim += ln
                    g = others[0] if others else None
                    if g is not None and g.normal.z > 0.7 and g.material_index not in grass and                             abs(g.calc_center_median().z - f.calc_center_median().z) < SLIVER_DZ:
                        flat += ln
                        votes[g.material_index] = votes.get(g.material_index, 0.0) + ln
        if perim == 0.0 or area / perim > SLIVER_HALF_W or flat < 0.6 * perim:
            continue
        slot = max(votes, key=votes.get)
        for f in comp:
            f.material_index = slot
        done += len(comp)
    return done


def _add_skirts(bm, depth=SKIRT):
    """Hang a vertical face below every boundary edge of the terrain. settle.py removes the ground under walk tops and
    leaves level steps (lane vs verge, plaza vs lawn) as two open rims at different heights with nothing between;
    in UE that gap shows the void, read as thin sky-coloured wedges (owner playtest 2026-10-27: 444 such steps, ~150 m,
    measured on TER_Ground; not Nanite: same with r.Nanite 0). A skirt closes every such step with ground-material
    wall, and is hidden under the paving where the rim only frames a covered hole. Winding follows the boundary
    face, so the skirt faces the open side. Returns the number of skirt faces."""
    bottom = {}
    made = 0
    for e in [e for e in bm.edges if e.is_boundary]:
        f = e.link_faces[0]
        loop = next(l for l in f.loops if l.edge == e)
        a, b = loop.vert, loop.link_loop_next.vert
        for v in (a, b):
            if v not in bottom:
                bottom[v] = bm.verts.new((v.co.x, v.co.y, v.co.z - depth))
        try:
            nf = bm.faces.new((b, a, bottom[a], bottom[b]))
        except ValueError:   # face already exists (degenerate double rim)
            continue
        nf.material_index = f.material_index
        made += 1
    return made


def _orient_steps(bm, kerb):
    """Turn every near-vertical terrain face towards its lower side. settle.py's step walls (lane vs verge, 2-10 cm)
    come out wound into the higher ground, so UE culls them from the side they are seen from and the void shows as a
    sky-blue wedge (owner playtest 2026-10-27, east gate lane: normal -X on a step falling to +X). Vote per edge over
    the up-facing neighbours: one on the top edge must be behind the face, one on the bottom edge in front of it.
    A wall at least KERB_MIN tall becomes a concrete kerb (slot index kerb), a lower one takes the material of the
    top it belongs to (settle leaves slot 0, grass, on them). Returns the number of faces flipped."""
    bm.normal_update()
    flip = []
    for f in bm.faces:
        n = f.normal
        if abs(n.z) > 0.3:
            continue
        c = f.calc_center_median()
        score = 0.0
        for e in f.edges:
            top = (e.verts[0].co.z + e.verts[1].co.z) * 0.5 > c.z
            for g in e.link_faces:
                if g is f or g.normal.z < 0.5:
                    continue
                d = g.calc_center_median() - c
                s = n.x * d.x + n.y * d.y
                score += -s if top else s
                if top:
                    f.material_index = g.material_index
        zs = [v.co.z for v in f.verts]
        if max(zs) - min(zs) >= KERB_MIN:
            f.material_index = kerb
        if score < 0:
            flip.append(f)
    bmesh.ops.reverse_faces(bm, faces=flip)
    bm.normal_update()
    return len(flip)


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
    names = [m.name if m else "" for m in obj.data.materials]
    if KERB_SLOT not in names:   # in-memory only: run.py never saves the .blend
        obj.data.materials.append(bpy.data.materials.get(KERB_SLOT) or bpy.data.materials.new(KERB_SLOT))
        names.append(KERB_SLOT)
    grass = {i for i, n in enumerate(names) if any(k in n for k in GRASS)}
    print(f"ue_prep terrain: {_orient_steps(bm, names.index(KERB_SLOT))} step faces turned out, "
          f"{_fill_slivers(bm, grass)} grass sliver faces repainted, {_add_skirts(bm)} skirt faces")
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
