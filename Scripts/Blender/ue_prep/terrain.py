# TER_Ground -> 64 m tiles with exact grid-line cuts (ue_prep, inside Blender; used by run.py).
# One bmesh bisect per grid line on the whole terrain, then cut vertices are snapped exactly onto the line, so the
# two tiles of a seam share bit-identical border vertices (same source vertex, float32-exact multiples of 64 m).
# Pivot = tile min corner (x0, y0, 0) in Blender; local coords are then exact in float32 (Sterbenz: v - 64k).
import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

from .common import TILE_M, box_uvs, tile_name
from .geom import geo_from_mesh

SNAP = 2e-4   # m; bisect tolerance band snapped onto the grid line
SKIRT = 0.5   # m; every open terrain edge gets a vertical skirt this deep (see _add_skirts)
KERB_MIN = 0.04   # m; step walls at least this tall are concrete kerbs (owner playtest 2026-10-28: grass/paint walls)
KERB_SLOT = "M_Concrete_Precast"
GRASS = ("Grass",)
SLIVER_HALF_W, SLIVER_MAX_AREA, SLIVER_DZ = 0.3, 15.0, 0.03   # m, m2, m: see _fill_slivers
# Owner corrections to the ground ("it is flat there, no step, no ramp"), see _flatten. UE cm rect (x0, x1, y0, y1),
# floor z (cm): ground within FLOOR_TOL of it is the reference plaza; grade: max rise per metre away from it;
# fade (m): the cut fades out over this distance inside the rect edge so no new step appears there.
OWNER_FLATTEN = [
    # 2026-10-28: herringbone path / lawn terrace west and south of the hex plaza by the north wall stood 0.6 m above
    # the plaza (x 95.5 m) with a concrete step across the path
    # (rect past the wall, so the cut does not fade out along it; east edge = end of LowerYard_Retain_West)
    {"rect_cm": (5000.0, 11600.0, -9700.0, -7000.0), "floor_cm": 218.0, "grade": 0.04, "fade_m": 5.0},
    # 2026-10-28 (2): footpath north along the lower-yard terraces east of the booth (x 217 m): the 0.17 m terrace
    # step at y -81 m becomes a 5 % slope down to the 1.72 m end
    {"rect_cm": (21620.0, 21900.0, -8420.0, -7700.0), "floor_cm": 172.0, "grade": 0.05, "fade_m": 0.6},
    # 2026-10-28 (2): two terrain vertices spiked to 3.2 m behind the north-bed kerb (x 139.3..140.0 m, y -77.2 m;
    # ground 2.33 m) stood as a dark 0.9 m "box" in the lawn: cut to their neighbours
    {"rect_cm": (13890.0, 14020.0, -7730.0, -7705.0), "floor_cm": 233.0, "grade": 0.6, "fade_m": 0.05},
]
FLOOR_TOL = 0.03   # m
# non-terrain meshes lying on the cut ground that follow it (carry_flatten, called by run.py before export)
OWNER_FLATTEN_CARRY = ("GBS_Sports_NorthTreeLawn",)
# stairs the ground pokes through (owner playtest 2026-10-28: pale paving triangles in the red treads)
OWNER_SINK = ("GBS_GateAlley_Steps_BCorner_Upper", "GBS_GateAlley_Steps_BCorner_Lower")
SINK_R, SINK_EDGE = 0.35, 0.3   # m
# UE cm rects (x0, x1, y0, y1[, slot]): grass that juts into a walkway takes the paving it borders, or the slot given
# (owner marks 2026-10-28)
OWNER_REPAINT = [(13895.0, 13990.0, -8120.0, -7930.0),
                 # 2026-10-28 (2): lawn notch by the north-lawn bench, strip between the bin yard paving and the tree
                 # bed, the lawn island east of the pavilion, the pavilion plaza lawns, the path to the back wicket
                 (13450.0, 14060.0, -8235.0, -8065.0), (19950.0, 21350.0, -7975.0, -7850.0),
                 (9180.0, 10600.0, -8150.0, -6880.0), (7050.0, 9300.0, -6600.0, -1300.0),
                 (21680.0, 21840.0, -8400.0, -7760.0, "M_Paver_Clover_Grey")]


def _fields(verts):
    """Per OWNER_FLATTEN entry: (rect in Blender m, KD-tree of the plaza vertices, entry) from world (x, y, z) m."""
    out = []
    for fl in OWNER_FLATTEN:
        x0, x1, y0, y1 = (v / 100.0 for v in fl["rect_cm"])
        rect = (x0, x1, -y1, -y0)
        floor = fl["floor_cm"] / 100.0
        plaza = [c for c in verts if rect[0] <= c[0] <= rect[1] and rect[2] <= c[1] <= rect[3]
                 and abs(c[2] - floor) <= FLOOR_TOL]
        if not plaza:
            continue
        kd = KDTree(len(plaza))
        for i, c in enumerate(plaza):
            kd.insert((c[0], c[1], 0.0), i)
        kd.balance()
        out.append((rect, kd, fl))
    return out


def _cut(fields, x, y, z):
    """z after OWNER_FLATTEN: min(z, floor + grade * distance to the plaza), blended to z over fade_m inside the rect
    edge. Blender coords (x = UE x / 100, y = -UE y / 100), metres."""
    for (x0, x1, y0, y1), kd, fl in fields:
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue
        target = fl["floor_cm"] / 100.0 + fl["grade"] * kd.find((x, y, 0.0))[2]
        if z > target:
            w = min(1.0, min(x - x0, x1 - x, y - y0, y1 - y) / fl["fade_m"])
            z -= w * (z - target)
    return z


def _flatten(bm):
    """OWNER_FLATTEN on the terrain: cut steps collapse to flat or sloped ground (runs before the step pass).
    Returns the number of vertices moved."""
    fields = _fields([v.co[:] for v in bm.verts])
    moved = 0
    for v in bm.verts:
        z = _cut(fields, v.co.x, v.co.y, v.co.z)
        if z < v.co.z:
            v.co.z = z
            moved += 1
    bm.normal_update()
    return moved


def carry_flatten(terrain, objs):
    """Objects in OWNER_FLATTEN_CARRY (kerbed lawn strips lying on the cut ground) follow it: each vertex drops by
    the cut of the original ground under it. Edits the in-memory mesh before run.py hashes/exports it. -> count."""
    bm = bmesh.new()
    bm.from_mesh(terrain.data)
    bm.transform(Matrix(terrain.matrix_world))
    fields = _fields([v.co[:] for v in bm.verts])
    tree = BVHTree.FromBMesh(bm)
    n = 0
    for ob in objs:
        if ob.name not in OWNER_FLATTEN_CARRY:
            continue
        inv = ob.matrix_world.inverted()
        for v in ob.data.vertices:
            w = ob.matrix_world @ v.co
            hit = tree.ray_cast(Vector((w.x, w.y, 1000.0)), Vector((0.0, 0.0, -1.0)))
            if hit[0] is None:
                continue
            dz = hit[0].z - _cut(fields, w.x, w.y, hit[0].z)
            if dz > 0.0:
                v.co = inv @ Vector((w.x, w.y, w.z - dz))
                n += 1
        ob.data.update()
    bm.free()
    return n


def _sink(bm):
    """OWNER_SINK: ground under these stairs drops 3 cm below the stair surface right above it (ray cast on the stair
    mesh), so no slope pokes through the treads; ground beside the stair is untouched (a bound-box cut left a pit
    next to it, owner playtest 2026-10-28). -> number of vertices moved."""
    moved = 0
    for name in OWNER_SINK:
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        sb = bmesh.new()
        sb.from_mesh(ob.data)
        sb.transform(Matrix(ob.matrix_world))
        tree = BVHTree.FromBMesh(sb)
        xs = [v.co.x for v in sb.verts]
        ys = [v.co.y for v in sb.verts]
        zmin = min(v.co.z for v in sb.verts)
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        sb.free()

        def near():
            return [f for f in bm.faces if any(x0 - 1 <= v.co.x <= x1 + 1 and y0 - 1 <= v.co.y <= y1 + 1 for v in f.verts)]
        # cut the ground along the stair outline and densify it underneath: big triangles reaching past the stair
        # otherwise keep vertices outside and their middle pokes through the treads (the second owner mark)
        for co, no in (((x0, 0, 0), (1, 0, 0)), ((x1, 0, 0), (1, 0, 0)), ((0, y0, 0), (0, 1, 0)), ((0, y1, 0), (0, 1, 0))):
            fs = near()
            geom = list({v for f in fs for v in f.verts}) + list({e for f in fs for e in f.edges}) + fs
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-4)
        for _ in range(8):   # split long edges under the stair until none is over SINK_EDGE (uniform cuts exploded)
            long = [e for e in bm.edges if e.calc_length() > SINK_EDGE and all(
                x0 - 1e-3 <= v.co.x <= x1 + 1e-3 and y0 - 1e-3 <= v.co.y <= y1 + 1e-3 for v in e.verts)]
            if not long:
                break
            bmesh.ops.subdivide_edges(bm, edges=long, cuts=1)
            bmesh.ops.triangulate(bm, faces=[f for f in near() if len(f.verts) > 3])
        for v in bm.verts:
            if not (x0 - 1e-3 <= v.co.x <= x1 + 1e-3 and y0 - 1e-3 <= v.co.y <= y1 + 1e-3) or v.co.z < zmin:
                continue
            # lowest stair surface within SINK_R: a straight ground edge between two such points stays under the
            # treads it spans (a riser is ~15 cm, tread ~30 cm)
            low = None
            for dx, dy in ((0, 0), (SINK_R, 0), (-SINK_R, 0), (0, SINK_R), (0, -SINK_R)):
                hit = tree.ray_cast(Vector((v.co.x + dx, v.co.y + dy, v.co.z + 5.0)), Vector((0.0, 0.0, -1.0)))
                if hit[0] is None and dx == dy == 0:
                    break   # not under the stair itself (its bound box is wider than its steps)
                if hit[0] is not None:
                    low = hit[0].z if low is None else min(low, hit[0].z)
            if low is not None and v.co.z > low - 0.03:
                v.co.z = low - 0.03
                moved += 1
    bm.normal_update()
    return moved


def _repaint(bm, grass, names):
    """OWNER_REPAINT: grass up faces with their centre in the rect take the paving they border (majority by edge
    length). -> number of faces repainted."""
    done = 0
    for x0, x1, y0, y1, *target in OWNER_REPAINT:
        bx0, bx1, by0, by1 = x0 / 100.0, x1 / 100.0, -y1 / 100.0, -y0 / 100.0
        if target:   # a laid path: cut the ground along its edges first, or big triangles leave saw-tooth borders
            for co, no in (((bx0, 0, 0), (1, 0, 0)), ((bx1, 0, 0), (1, 0, 0)), ((0, by0, 0), (0, 1, 0)),
                           ((0, by1, 0), (0, 1, 0))):
                fs = [f for f in bm.faces if any(bx0 - 1 <= v.co.x <= bx1 + 1 and by0 - 1 <= v.co.y <= by1 + 1
                                                 for v in f.verts)]
                geom = list({v for f in fs for v in f.verts}) + list({e for f in fs for e in f.edges}) + fs
                bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-4)
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
            bm.normal_update()
        sel = [f for f in bm.faces if f.normal.z > 0.7 and f.material_index in grass
               and bx0 <= f.calc_center_median().x <= bx1 and by0 <= f.calc_center_median().y <= by1]
        cs, votes = set(sel), {}
        for f in sel:
            for e in f.edges:
                for g in e.link_faces:
                    if g not in cs and g.normal.z > 0.7 and g.material_index not in grass:
                        votes[g.material_index] = votes.get(g.material_index, 0.0) + e.calc_length()
        if target:   # explicit slot (a path laid across a lawn borders no paving to vote)
            votes = {names.index(target[0]): 1.0} if target[0] in names else {}
        if votes:
            slot = max(votes, key=votes.get)
            for f in sel:
                f.material_index = slot
            done += len(sel)
    return done


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


def _orient_steps(bm, kerb, grass):
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
        low_grass = False
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
                elif g.material_index in grass:
                    low_grass = True
        zs = [v.co.z for v in f.verts]
        if max(zs) - min(zs) >= KERB_MIN and not (low_grass and f.material_index in grass):
            f.material_index = kerb   # a step inside a lawn stays lawn (a concrete patch in a bank read as a box)
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
    print(f"ue_prep terrain: {_flatten(bm)} vertices lowered (owner flatten), {_sink(bm)} sunk under stairs")
    print(f"ue_prep terrain: {_orient_steps(bm, names.index(KERB_SLOT), grass)} step faces turned out, "
          f"{_fill_slivers(bm, grass)} grass sliver faces repainted, {_repaint(bm, grass, names)} owner repaints, "
          f"{_add_skirts(bm)} skirt faces")
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
