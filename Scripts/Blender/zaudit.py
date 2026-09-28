# Z-fight audit (R1): coplanar (|offset| <= TOL) overlapping faces of different objects, exact triangle-clip overlap
# area, same/opposite normal, and a visibility test (point just off the face inside another closed solid / under terrain).
# "exact" (offset < 2 mm) = real flicker; "layered" (2-15 mm) = check at distance. Read-only.
# Run: blender -b file.blend -P Scripts/Blender/zaudit.py -- out.json   (prints the pairs sorted by visible area)
import bpy, numpy as np, json, sys, math
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOL = 0.015
out = sys.argv[sys.argv.index('--') + 1]
objs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith(('REF_', 'CAM_')) and not o.hide_render]
gen = {o.name: o.get('koch_gen', '') for o in objs}
F = []   # (obj, n, c, tri2d-ready world tris, area)
geo = {}
for o in objs:
    me = o.data
    mw = np.array(o.matrix_world)
    co = np.empty(len(me.vertices) * 3, np.float64); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    W = co @ mw[:3, :3].T + mw[:3, 3]
    flip = np.linalg.det(mw[:3, :3]) < 0   # mirrored instance (facade frames are left-handed): winding flips
    me.calc_loop_triangles()
    tv = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('vertices', tv); tv = tv.reshape(-1, 3)
    tp = np.empty(len(me.loop_triangles), np.int32); me.loop_triangles.foreach_get('polygon_index', tp)
    geo[o.name] = (W, [list(p.vertices) for p in me.polygons])
    bytri = defaultdict(list)
    for t, p in zip(tv, tp):
        bytri[p].append(t)
    for p in me.polygons:
        tris = bytri.get(p.index)
        if not tris:
            continue
        T = W[np.array(tris)]
        cr = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        a = 0.5 * np.linalg.norm(cr, axis=1).sum()
        if a < 0.01:
            continue
        n = cr.sum(0); n /= np.linalg.norm(n)
        if flip:
            n = -n
        F.append((o.name, n, T.reshape(-1, 3).mean(0), T, a))
print('objects', len(objs), 'faces', len(F))


def canon(n):
    return n if (n[2] > 1e-6 or (abs(n[2]) < 1e-6 and (n[1] > 1e-6 or (abs(n[1]) < 1e-6 and n[0] > 0)))) else -n


B = defaultdict(list)
for i, f in enumerate(F):
    nn = canon(f[1]); d = nn @ f[2]
    B[(round(nn[0], 2), round(nn[1], 2), round(nn[2], 2), math.floor(d / 0.02))].append(i)


def clip(subj, clipp):
    """Sutherland-Hodgman: convex subject polygon clipped by convex CCW clip polygon (2D lists)."""
    outp = subj
    for i in range(len(clipp)):
        if not outp:
            break
        a, b = clipp[i - 1], clipp[i]
        inp, outp = outp, []
        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-12
        def inter(p, q):
            x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            den = (x2 - x1) * dy - (y2 - y1) * dx
            t = ((a[0] - x1) * dy - (a[1] - y1) * dx) / den if abs(den) > 1e-15 else 0
            return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
        s = inp[-1]
        for e in inp:
            if inside(e):
                if not inside(s):
                    outp.append(inter(s, e))
                outp.append(e)
            elif inside(s):
                outp.append(inter(s, e))
            s = e
    return outp


def parea(p):
    return 0.5 * sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))


def ccw2(t):
    return t if parea(t) > 0 else t[::-1]


def overlap(fa, fb):
    n = fa[1]
    ax = int(np.argmax(np.abs(n))); idx = [k for k in range(3) if k != ax]
    ta = [ccw2([(float(v[idx[0]]), float(v[idx[1]])) for v in t]) for t in fa[3]]
    tb = [ccw2([(float(v[idx[0]]), float(v[idx[1]])) for v in t]) for t in fb[3]]
    pieces = []
    for A in ta:
        amin, amax = np.min(A, 0), np.max(A, 0)
        for Bt in tb:
            bmin, bmax = np.min(Bt, 0), np.max(Bt, 0)
            if (amin > bmax).any() or (bmin > amax).any():
                continue
            P = clip(A, Bt)
            if len(P) >= 3:
                ar = abs(parea(P))
                if ar > 1e-4:
                    c2 = np.mean(P, 0)
                    # lift the centroid onto face a's plane
                    p3 = np.zeros(3); p3[idx[0]], p3[idx[1]] = c2
                    p3[ax] = (n @ fa[3][0][0] - n[idx[0]] * c2[0] - n[idx[1]] * c2[1]) / n[ax]
                    pieces.append((ar, p3))
    return pieces


# closed solids for the visibility test
solid = []
for o in objs:
    if o.name.startswith('TER_'):
        continue
    W, polys = geo[o.name]
    if not polys:
        continue
    solid.append(o.name)
aabb = np.array([[*geo[s][0].min(0), *geo[s][0].max(0)] for s in solid])
bvh = {}


def tree(s):
    if s not in bvh:
        W, polys = geo[s]
        bvh[s] = BVHTree.FromPolygons([Vector(v) for v in W], polys, all_triangles=False)
    return bvh[s]


ter = None
if 'TER_Ground' in geo:
    W, polys = geo['TER_Ground']
    ter = BVHTree.FromPolygons([Vector(v) for v in W], polys)
DIRS = [Vector((0.1234, 0.2711, 0.9546)).normalized(), Vector((-0.8123, 0.3311, -0.4801)).normalized(), Vector((0.3517, -0.9013, 0.2531)).normalized()]


def inside_any(p):
    m = np.all((aabb[:, :3] - 1e-4 <= p) & (p <= aabb[:, 3:] + 1e-4), axis=1)
    P = Vector(p)
    for k in np.nonzero(m)[0]:
        t = tree(solid[k]); votes = 0
        for D in DIRS:
            cnt, o_ = 0, P.copy()
            for _ in range(200):
                hit = t.ray_cast(o_, D)
                if hit[0] is None:
                    break
                cnt += 1; o_ = hit[0] + D * 1e-5
            votes += cnt & 1
        if votes >= 2:
            return solid[k]
    return None


def under_ter(p):
    if ter is None:
        return False
    h = ter.ray_cast(Vector(p), Vector((0, 0, 1)))
    return h[0] is not None and h[0].z - p[2] > 0.005


pairs = defaultdict(lambda: {'area': 0.0, 'exact': 0.0, 'layered': 0.0, 'touch': 0.0, 'hidden': 0.0, 'off': 9.0, 'pts': []})
fobj = np.array([f[0] for f in F])
for key in list(B.keys()):
    ids = np.array(B[key] + B.get((key[0], key[1], key[2], key[3] + 1), []))
    nb = len(B[key])
    if len(set(fobj[ids])) < 2:
        continue
    bb = np.array([[*F[i][3].reshape(-1, 3).min(0), *F[i][3].reshape(-1, 3).max(0)] for i in ids])
    names = fobj[ids]
    for a in range(nb):
        fa = F[ids[a]]
        m = np.all(bb[:, :3] <= bb[a, 3:] + TOL + 1e-6, axis=1) & np.all(bb[:, 3:] >= bb[a, :3] - TOL - 1e-6, axis=1) & (names != fa[0])
        m[:a + 1] = False
        for b in np.nonzero(m)[0]:
            fb = F[ids[b]]
            dot = float(fa[1] @ fb[1])
            if abs(dot) < 0.999:
                continue
            off = float(fa[1] @ (fb[2] - fa[2]))
            if abs(off) > TOL:
                continue
            pcs = overlap(fa, fb)
            ar = sum(p[0] for p in pcs)
            if ar < 0.01:
                continue
            k = tuple(sorted((fa[0], fb[0])))
            r = pairs[k]
            r['area'] += ar; r['off'] = min(r['off'], abs(off))
            if dot < 0:
                r['touch'] += ar
                continue
            pcs.sort(key=lambda p: -p[0])
            last = None
            for i_, (pa, p3) in enumerate(pcs):
                if i_ < 6:
                    q = p3 + fa[1] * (max(off, 0.0) + 0.002)   # just above the upper face
                    if inside_any(q) or under_ter(q):
                        last = 'hidden'
                    else:
                        last = 'exact' if abs(off) < 0.002 else 'layered'
                        if len(r['pts']) < 3:
                            r['pts'].append([round(float(x), 2) for x in p3])
                r[last] += pa
res = []
for (a, b), r in pairs.items():
    res.append({'a': a, 'b': b, 'ga': gen.get(a, ''), 'gb': gen.get(b, ''), 'area': round(r['area'], 3),
                'exact': round(r['exact'], 3), 'layered': round(r['layered'], 3), 'touch': round(r['touch'], 3),
                'hidden': round(r['hidden'], 3), 'vis': round(r['exact'] + r['layered'], 3), 'off': round(r['off'], 4),
                'pts': r['pts']})
res.sort(key=lambda r: -r['vis'])
json.dump(res, open(out, 'w'), indent=0)
nv = sum(1 for r in res if r['vis'] > 0.01)
print('pairs', len(res), 'visible', nv, 'vis_area', round(sum(r['vis'] for r in res), 1))
for r in res[:40]:
    print(r['exact'], r['layered'], r['area'], r['off'], r['a'], '|', r['b'], r['pts'][:1])
