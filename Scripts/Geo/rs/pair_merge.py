# Pairwise zone merge (R1 pass P0, handoff section 4.2 "divide and merge, never one whole-site solve"): the frames of
# two zones (all clips of both job.json files) are cut out of the matched COLMAP database (sfm/db.db, sequential +
# loop matches already computed) into a small pair database, solved with COLMAP global_mapper (minutes, a few GB),
# and every RealityScan component of both zones is fitted to the pair model on its shared frames: rotation from the
# camera orientations (chordal mean), then scale and translation from the camera centres (robust). The residual of
# the camera centres in metres is the pair REG (limit 0.30 m for P0). Metres: from a component that has a world
# align.json (its scale), else from the eye height over the pair model's own ground (not done here: pass --scale).
# Output: <work>/pairs/<A>_<B>/ (sub.db, sparse/, pair.json) and <zone>/c<N>/align_pair.json (component -> pair frame).
# Chain several pairs with --base <previous pair dir>: the new pair is expressed in the previous pair's frame through
# the components they share.
# Usage: python pair_merge.py Street Gate [--work C:/koch/work] [--colmap tools/colmap/bin/colmap.exe] [--reuse]
import argparse
import glob
import json
import os
import sqlite3
import subprocess
import sys

import numpy as np

P = 2147483647


def clip_of(name):
    b = os.path.basename(name)
    return b.rsplit("_f", 1)[0] if "_f" in b else b


def sub_db(src, dst, clips):
    if os.path.exists(dst):
        os.remove(dst)
    s = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    ids = [i for i, n in s.execute("select image_id, name from images") if clip_of(n) in clips]
    s.close()
    d = sqlite3.connect(dst, uri=True)
    d.execute(f"attach database 'file:{src.replace(os.sep, '/')}?mode=ro' as s")
    for (sql,) in d.execute("select sql from s.sqlite_master where type='table' and name!='sqlite_sequence'").fetchall():
        d.execute(sql)
    d.execute("create temp table keep(id integer primary key)")
    d.executemany("insert into keep values (?)", [(i,) for i in ids])
    for t in ("rigs", "rig_sensors", "cameras"):
        d.execute(f"insert into {t} select * from s.{t}")
    d.execute("insert into images select * from s.images where image_id in (select id from keep)")
    d.execute("insert into frame_data select * from s.frame_data where data_id in (select id from keep)")
    d.execute("insert into frames select * from s.frames where frame_id in (select frame_id from frame_data)")
    d.execute("insert into pose_priors select * from s.pose_priors where corr_data_id in (select id from keep)")
    for t in ("keypoints", "descriptors"):
        d.execute(f"insert into {t} select * from s.{t} where image_id in (select id from keep)")
    for t in ("matches", "two_view_geometries"):
        d.execute(f"insert into {t} select * from s.{t} where pair_id / {P} in (select id from keep) and pair_id % {P} in (select id from keep)")
    d.commit(); d.close()
    return len(ids)


def read_images_txt(path):
    out, lines = {}, [l for l in open(path, encoding="utf-8") if not l.startswith("#")]
    for l in lines[::2]:
        e = l.split()
        if len(e) < 10:
            continue
        q = np.array(e[1:5], float); t = np.array(e[5:8], float)
        w, x, y, z = q / np.linalg.norm(q)
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                      [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                      [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])
        out[os.path.basename(e[9])] = (R, -R.T @ t)
    return out


def fit(Ra, Ca, Rb, Cb):
    """x_b = s R x_a + t from world-to-camera rotations and centres of the same frames in model a and b."""
    M = sum(rb.T @ ra for ra, rb in zip(Ra, Rb))                  # R_a = R_b R  ->  R = R_b^T R_a
    U, _, Vt = np.linalg.svd(M); R = U @ np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))]) @ Vt
    A = Ca @ R.T; keep = np.ones(len(A), bool)
    for _ in range(3):                                            # robust: drop centres > 3 x median residual
        ma, mb = A[keep].mean(0), Cb[keep].mean(0)
        s = ((A[keep] - ma) * (Cb[keep] - mb)).sum() / ((A[keep] - ma) ** 2).sum()
        t = mb - s * ma; r = np.linalg.norm(s * A + t - Cb, axis=1)
        keep = r <= max(3 * np.median(r), 1e-9)
    ang = np.degrees([np.arccos(np.clip((np.trace(rb.T @ ra @ R.T) - 1) / 2, -1, 1)) for ra, rb in zip(Ra, Rb)])
    return s, R, t, r, keep, np.median(ang)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--work", default=r"C:\koch\work"); ap.add_argument("--colmap", default=r"C:\koch\work\tools\colmap\bin\colmap.exe")
    ap.add_argument("--reuse", action="store_true", help="keep an existing pair solve"); ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--tracks", type=int, default=150000, help="cap on tracks: global positioning time and RAM (<= 10 GB rule)")
    ap.add_argument("--eye", type=float, default=1.52)
    ap.add_argument("--scale", type=float, help="metres per pair-model unit (else from a component with align.json)")
    a = ap.parse_args()
    out = os.path.join(a.work, "pairs", f"{a.a}_{a.b}"); os.makedirs(out, exist_ok=True)
    zones = {z: json.load(open(os.path.join(a.work, "zones", z, "job.json"), encoding="utf-8-sig")) for z in (a.a, a.b)}
    clips = {c for j in zones.values() for c in j.get("clips", [])}
    sp = os.path.join(out, "sparse")
    if not (a.reuse and glob.glob(os.path.join(sp, "*", "images.txt"))):
        n = sub_db(os.path.join(a.work, "sfm", "db.db"), os.path.join(out, "sub.db"), clips)
        os.makedirs(sp, exist_ok=True)
        with open(os.path.join(out, "mapper.log"), "w") as f:
            rc = subprocess.run([a.colmap, "global_mapper", "--database_path", os.path.join(out, "sub.db"),
                                 "--image_path", os.path.join(a.work, "sfm", "images"), "--output_path", sp,
                                 "--GlobalMapper.num_threads", str(a.threads),
                                 "--GlobalMapper.keep_max_num_tracks", str(a.tracks)], stdout=f, stderr=subprocess.STDOUT).returncode
        print(f"pair {a.a}+{a.b}: {len(clips)} clips, {n} frames, global_mapper exit {rc}")
        for m in glob.glob(os.path.join(sp, "*", "")):
            subprocess.run([a.colmap, "model_converter", "--input_path", m, "--output_path", m, "--output_type", "TXT"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    models = sorted(((read_images_txt(f), os.path.basename(os.path.dirname(f))) for f in glob.glob(os.path.join(sp, "*", "images.txt"))),
                    key=lambda m: -len(m[0]))
    if not models:
        print("no pair model"); return 1
    print("pair models (frames):", ", ".join(f"{k}:{len(m)}" for m, k in models[:5]))
    img, key = models[0]
    comps = []
    for z in (a.a, a.b):
        for mj in sorted(glob.glob(os.path.join(a.work, "zones", z, "c*", "model.json"))):
            cams = json.load(open(mj))["cameras"]
            sh = [c for c in cams if os.path.basename(c["name"]) in img]
            if len(sh) < 5:
                comps.append((z, mj, len(cams), len(sh), None)); continue
            Ra = [np.array(c["R"]) for c in sh]; Ca = np.array([c["center"] for c in sh])
            Rb = [img[os.path.basename(c["name"])][0] for c in sh]; Cb = np.array([img[os.path.basename(c["name"])][1] for c in sh])
            comps.append((z, mj, len(cams), len(sh), fit(Ra, Ca, Rb, Cb)))
    # metres per pair unit: eye height over the mesh of well-fitted components (zone_world.py ground planes), else a
    # component with a world align.json, else --scale
    mpu = a.scale
    if mpu is None:
        est = []
        for z, mj, _, _, f in comps:
            d = os.path.dirname(mj)
            if f is None or f[0] <= 0 or f[5] > 2 or not os.path.exists(os.path.join(d, "mesh.obj")):
                continue
            import open3d as o3d
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import zone_world as zw
            tm = o3d.io.read_triangle_mesh(os.path.join(d, "mesh.obj"), enable_post_processing=False)
            sc = o3d.t.geometry.RaycastingScene()
            sc.add_triangles(o3d.core.Tensor(np.asarray(tm.vertices).astype(np.float32)), o3d.core.Tensor(np.asarray(tm.triangles).astype(np.uint32)))
            m = json.load(open(mj)); _, h, ng = zw.robust_up(zw.ground_planes(sc, m), m); del tm, sc
            est.append(a.eye / h / f[0]); print(f"metres from the eye height in {os.path.relpath(d, a.work)}: {est[-1]:.4f} m/unit ({ng} ground planes)")
        if est:
            mpu = float(np.median(est))
        else:
            for z, mj, _, _, f in comps:
                aj = os.path.join(os.path.dirname(mj), "align.json")
                if f is not None and f[0] > 0 and os.path.exists(aj):
                    mpu = json.load(open(aj))["scale"] / f[0]; print(f"metres from {os.path.relpath(aj, a.work)}: {mpu:.4f} m/unit"); break
    mpu = mpu or float("nan")
    res = {"pair": [a.a, a.b], "model": key, "frames": len(img), "m_per_unit": mpu, "components": []}
    for z, mj, n, ns, f in comps:
        c = os.path.relpath(os.path.dirname(mj), os.path.join(a.work, "zones"))
        if f is None:
            print(f"  {c}: {ns}/{n} frames in the pair model - not joined"); res["components"].append({"comp": c, "joined": False}); continue
        s, R, t, r, keep, ang = f
        reg = float(np.sqrt((r[keep] ** 2).mean()) * mpu)
        print(f"  {c}: {ns}/{n} frames, REG {reg:.2f} m ({keep.sum()} inliers), rot {ang:.1f} deg {'ok' if reg <= 0.30 and ang < 2 and s > 0 else 'FAIL'}")
        json.dump({"scale": float(s), "R": R.tolist(), "t": t.tolist(), "frame": f"pair {a.a}_{a.b}/{key}", "reg_m": reg,
                   "note": "pair_merge.py: component -> pair model (shared frames)"}, open(os.path.join(os.path.dirname(mj), "align_pair.json"), "w"), indent=1)
        res["components"].append({"comp": c, "joined": True, "shared": ns, "reg_m": reg, "rot_deg": float(ang), "ok": bool(reg <= 0.30 and ang < 2 and s > 0)})
    json.dump(res, open(os.path.join(out, "pair.json"), "w"), indent=1)
    ok = [c for c in res["components"] if c.get("ok")]
    zj = {z: any(c["comp"].startswith(z) for c in ok) for z in (a.a, a.b)}
    print(f"{a.a}+{a.b}: {len(ok)}/{len(comps)} components within REG 0.30 m, both zones {'yes' if all(zj.values()) else 'NO'}"
          f"; not joined or FAIL: {', '.join(c['comp'] for c in res['components'] if not c.get('ok')) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
