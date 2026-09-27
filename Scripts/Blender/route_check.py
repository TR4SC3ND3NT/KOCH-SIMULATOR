# Level check of the greybox along the owner's walking routes (R1 pass exit test for levels, handoff section 0):
# for every camera sample of Scripts/Geo/rs/route_profile.py (route.json) it casts a ray down through the built model
# and compares the model's walking surface with the measured ground (mesh ground under the camera if it agrees with
# camera z - eye, else camera z - eye). Clips whose eye height is the default (no mesh) are also scored with their
# median offset removed, so an eye-height error is not read as a wrong level. Railings, lamps, trees, benches etc.
# are left out of the ray test (--skip regex). Prints one line per clip and the worst runs, writes <out>/route_check.json.
# Read-only (never saves the .blend). Usage:
#   blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/route_check.py -- \
#       --route C:/koch/work/route/route.json --out C:/koch/work/route [--tol 0.07] [--clips a,b]
import argparse
import json
import os
import re
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SKIP = r"(?i)^REF_|rail|balust|fence|lamp|tree|thuja|spruce|hedge|bench|bin_|bin$|sign|bollard|flood|net|bike|flag|festoon|garland"


def build_bvh(lo, hi, skip):
    """One BVH of the evaluated, world-space triangles of every mesh object whose bounds touch the route box."""
    dg = bpy.context.evaluated_depsgraph_get()
    rx = re.compile(skip)
    verts, tris, owners, names, base = [], [], [], [], 0
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or rx.search(ob.name):
            continue
        bb = np.array([ob.matrix_world @ Vector(c) for c in ob.bound_box])
        if (bb[:, 0].max() < lo[0] or bb[:, 0].min() > hi[0] or bb[:, 1].max() < lo[1] or bb[:, 1].min() > hi[1]):
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        nv, nt = len(me.vertices), len(me.loop_triangles)
        if nt:
            co = np.empty(nv * 3)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            M = np.array(ob.matrix_world)
            verts.append(co @ M[:3, :3].T + M[:3, 3])
            t = np.empty(nt * 3, np.int64)
            me.loop_triangles.foreach_get("vertices", t)
            tris.append(t.reshape(-1, 3) + base)
            owners.append(np.full(nt, len(names)))
            names.append(ob.name)
            base += nv
        ev.to_mesh_clear()
    if not tris:
        raise SystemExit("no model geometry under the routes: wrong .blend or route frame?")
    V, T = np.concatenate(verts), np.concatenate(tris)
    return BVHTree.FromPolygons(V.tolist(), T.tolist()), np.concatenate(owners), names


def runs(bad, xs):
    """Index ranges [a, b] of consecutive True values."""
    out, a = [], None
    for i, b in enumerate(bad):
        if b and a is None:
            a = i
        if not b and a is not None:
            out.append((a, i - 1))
            a = None
    if a is not None:
        out.append((a, len(bad) - 1))
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tol", type=float, default=0.07, help="m; pass exit tolerance (P0 0.30, P1 0.07, P2 0.04)")
    ap.add_argument("--clips")
    ap.add_argument("--skip", default=SKIP, help="regex of object names left out of the ground test")
    a = ap.parse_args(argv)
    route = json.load(open(a.route))
    want = set(a.clips.split(",")) if a.clips else None
    clips = {k: v for k, v in route["clips"].items() if not want or k in want}
    allxy = np.array([[q[1], q[2]] for c in clips.values() for q in c["samples"]])
    bvh, owner, names = build_bvh(allxy.min(0) - 2, allxy.max(0) + 2, a.skip)

    report, worst = {"tol": a.tol, "clips": {}}, []
    for clip, c in sorted(clips.items()):
        S = c["samples"]            # [frame, x, y, z_cam, ground_cam, ground_mesh]
        g = np.array([q[5] if q[5] is not None and abs(q[5] - q[4]) < 0.35 else q[4] for q in S])
        zm, ob = np.full(len(S), np.nan), [""] * len(S)
        for i, q in enumerate(S):
            # start 0.3 m above the camera: under canopies/galleries the soffit is higher than that
            loc, _, idx, _ = bvh.ray_cast(Vector((q[1], q[2], q[3] + 0.3)), Vector((0, 0, -1)), 6.0)
            if loc is not None:
                zm[i], ob[i] = loc.z, names[owner[idx]]
        res = zm - g
        hit = np.isfinite(res)
        rel = c.get("eye_src") != "mesh"
        bias = float(np.median(res[hit])) if hit.any() else 0.0
        r = res - bias if rel else res
        within = float(np.mean(np.abs(r[hit]) <= a.tol)) if hit.any() else 0.0
        p90 = float(np.percentile(np.abs(r[hit]), 90)) if hit.any() else float("nan")
        bad = ~hit | (np.abs(np.nan_to_num(r, nan=9.0)) > a.tol)
        xy = np.array([[q[1], q[2]] for q in S])
        s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))])
        cr = []
        for i, j in runs(bad, s):
            seg = r[i:j + 1]
            if i == j and np.isfinite(seg[0]) and abs(seg[0]) < 2 * a.tol:
                continue            # one sample just over the tolerance: hand shake, not a wrong level
            objs = sorted({o for o in ob[i:j + 1] if o}, key=lambda o: -ob[i:j + 1].count(o))[:2]
            e = {"clip": clip, "s": [round(float(s[i]), 1), round(float(s[j]), 1)],
                 "xy": [round(float(xy[i, 0]), 2), round(float(xy[i, 1]), 2), round(float(xy[j, 0]), 2),
                        round(float(xy[j, 1]), 2)],
                 "res": None if not np.isfinite(seg).any() else round(float(np.nanmedian(seg)), 3),
                 "objects": objs, "frames": [S[i][0], S[j][0]], "len": float(s[j] - s[i]) + 0.3}
            cr.append(e)
            worst.append(e)
        report["clips"][clip] = {"n": len(S), "hit": int(hit.sum()), "bias": bias, "relative": rel,
                                 "within_tol": within, "p90": p90, "runs": cr}
        print(f"{clip}: {int(hit.sum())}/{len(S)} hits, {'relative (bias %+.2f)' % bias if rel else 'absolute'}, "
              f"{within * 100:.0f}% within {a.tol:.2f} m, p90 {p90:.2f} m, {len(cr)} bad runs")
    worst.sort(key=lambda e: -(abs(e["res"]) if e["res"] is not None else 9.0) * e["len"])
    for e in worst[:20]:
        res = "no ground" if e["res"] is None else f"{e['res']:+.2f} m"
        print(f"  {e['clip']} s {e['s'][0]}-{e['s'][1]} ({e['xy'][0]},{e['xy'][1]})->({e['xy'][2]},{e['xy'][3]}) "
              f"{res} {','.join(e['objects'])}  {os.path.basename(e['frames'][0])}")
    total = sum(v["hit"] for v in report["clips"].values())
    ok = sum(v["within_tol"] * v["hit"] for v in report["clips"].values())
    report["within_tol"] = ok / total if total else 0.0
    print(f"ALL: {report['within_tol'] * 100:.1f}% of {total} route samples within {a.tol:.2f} m")
    os.makedirs(a.out, exist_ok=True)
    json.dump(report, open(os.path.join(a.out, "route_check.json"), "w"), indent=1)


main()
