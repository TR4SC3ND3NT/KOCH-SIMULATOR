# Mesh drop for stream B (R1 handoff section 0b): per zone component with a finished mesh, a world-metre PLY
# decimated to <= --tris triangles (no texture, no colours, no normals), its align.json, the cameras (model.json
# without image paths and without the sparse points) and the zone's route.json from route_profile.py, zipped as
# <drop>/<zone>/ (--pack zone,zone,...: one zip <drop>/koch_meshes_<date>.zip with one folder per zone). Components without an align.json get one from the ground planes + eye height (levelled,
# metric; xy/yaw only a placeholder at the zone prior, flagged in the json). Never commit the output (people in the
# frames' names only, but meshes stay out of git).
# Usage: python mesh_drop.py <zone> [--comps c8,c3] | mesh_drop.py Garden,Sports,C_sw --pack [--work C:/koch/work] [--drop C:/koch/drop] [--tris 3000000]
import argparse
import datetime
import json
import os
import subprocess
import sys
import zipfile

import numpy as np
import open3d as o3d

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import zone_world as zw  # noqa: E402


def level_align(tm, m, job, eye):
    V = np.asarray(tm.vertices); F = np.asarray(tm.triangles)
    sc = o3d.t.geometry.RaycastingScene()
    sc.add_triangles(o3d.core.Tensor(V.astype(np.float32)), o3d.core.Tensor(F.astype(np.uint32)))
    up, h, ng = zw.robust_up(zw.ground_planes(sc, m), m); s = eye / h; R = zw.rot_to_z(up)
    pr = job.get("world_prior", [0, 0, 0])
    C = np.array([s * (R @ np.array(c["center"])) for c in m["cameras"]])
    t = np.array([pr[0], pr[1], zw.terrain_z(pr[0], pr[1]) + eye]) - np.median(C, 0)
    return {"scale": float(s), "R": R.tolist(), "t": t.tolist(), "frame": "levelled placeholder",
            "note": f"mesh_drop.py: up from {ng} ground planes, scale from the {eye} m eye height; xy and yaw are NOT "
                    "registered (placeholder at the zone prior) - levels, sizes and shapes are metric, positions are not"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zone"); ap.add_argument("--comps", help="comma list (default: every component with mesh.done)")
    ap.add_argument("--work", default=r"C:\koch\work"); ap.add_argument("--drop", default=r"C:\koch\drop")
    ap.add_argument("--tris", type=int, default=3_000_000); ap.add_argument("--eye", type=float, default=1.52)
    ap.add_argument("--pack", action="store_true", help="only zip the given zones' drop folders into one koch_meshes_<date>.zip")
    ap.add_argument("--raw", action="store_true", help="no levelling (drone/web clips: no eye height): identity align, RS units")
    ap.add_argument("--name", help="zip name (default koch_meshes_<date>)")
    a = ap.parse_args()
    if a.pack:
        zp = os.path.join(a.drop, (a.name or f"koch_meshes_{datetime.date.today():%Y%m%d}") + ".zip")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for zone in a.zone.split(","):
                d = os.path.join(a.drop, zone)
                for f in sorted(os.listdir(d)):
                    if os.path.isfile(os.path.join(d, f)):
                        z.write(os.path.join(d, f), f"{zone}/{f}")
        print(f"{zp}: {os.path.getsize(zp) / 1e6:.0f} MB")
        return 0
    zdir = os.path.join(a.work, "zones", a.zone); job = json.load(open(os.path.join(zdir, "job.json"), encoding="utf-8-sig"))
    comps = a.comps.split(",") if a.comps else sorted(d for d in os.listdir(zdir) if os.path.exists(os.path.join(zdir, d, "mesh.done")))
    out = os.path.join(a.drop, a.zone); os.makedirs(out, exist_ok=True)
    pairs = []
    for c in comps:
        cd = os.path.join(zdir, c)
        m = json.load(open(os.path.join(cd, "model.json")))
        tm = o3d.io.read_triangle_mesh(os.path.join(cd, "mesh.obj"), enable_post_processing=False)
        aj = os.path.join(cd, "align.json")
        if os.path.exists(aj):
            al = json.load(open(aj))
        elif a.raw:
            al = {"scale": 1.0, "R": np.eye(3).tolist(), "t": [0.0, 0.0, 0.0], "frame": "RealityScan component units",
                  "note": "mesh_drop.py --raw: drone/web clip, no eye height -> NOT levelled, NOT metric, not placed; "
                          "use for shapes and proportions only"}
        else:
            al = level_align(tm, m, job, a.eye)
        n0 = len(tm.triangles)
        tm.vertices = o3d.utility.Vector3dVector(np.asarray(tm.vertices) @ (al["scale"] * np.array(al["R"])).T + np.array(al["t"]))
        # vertex clustering in world metres (quadric decimation of a 20M-triangle mesh needs > 10 GB RAM): voxel from
        # the surface area so that the result lands just under --tris
        me, vox = tm, 0.0
        if n0 > a.tris:
            # bisection on the voxel (log scale) for the finest mesh under --tris; the area estimate alone lands far
            # below the budget on meshes with trees and hole fills
            hi = float(np.sqrt(2.0 * tm.get_surface_area() / a.tris)); lo = hi / 8; me = None
            for _ in range(7):
                v = float(np.sqrt(lo * hi))
                cand = tm.simplify_vertex_clustering(voxel_size=v, contraction=o3d.geometry.SimplificationContraction.Average)
                if len(cand.triangles) <= a.tris:
                    me, vox, hi = cand, v, v
                else:
                    lo = v
                del cand
            if me is None:
                vox = hi; me = tm.simplify_vertex_clustering(voxel_size=hi, contraction=o3d.geometry.SimplificationContraction.Average)
        me.remove_degenerate_triangles(); me.remove_unreferenced_vertices()
        me.vertex_colors = o3d.utility.Vector3dVector(); me.vertex_normals = o3d.utility.Vector3dVector()
        o3d.io.write_triangle_mesh(os.path.join(out, f"mesh_{c}.ply"), me, write_ascii=False, write_vertex_normals=False,
                                   write_vertex_colors=False)
        json.dump(al, open(os.path.join(out, f"align_{c}.json"), "w"), indent=1)
        cams = [{k: v for k, v in cam.items() if k != "image"} for cam in m["cameras"]]
        json.dump({"zone": a.zone, "component": c, "frame": m.get("frame"), "cameras": cams},
                  open(os.path.join(out, f"model_{c}.json"), "w"))
        pairs += ["--zone", os.path.join(cd, "model.json"), os.path.join(out, f"align_{c}.json")]
        print(f"{a.zone}/{c}: {n0} -> {len(me.triangles)} triangles (voxel {vox:.3f} m), {len(cams)} cameras, align {'existing' if os.path.exists(aj) else 'levelled placeholder'}")
        del tm, me
    rdir = os.path.join(out, "route")
    r = subprocess.run([sys.executable, os.path.join(HERE, "route_profile.py"), *pairs, "--out", rdir, "--eye", str(a.eye)],
                       capture_output=True, text=True)
    if os.path.exists(os.path.join(rdir, "route.json")):
        os.replace(os.path.join(rdir, "route.json"), os.path.join(out, "route.json"))
    print("route_profile:", r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-200:])
    json.dump({"zone": a.zone, "components": comps, "date": str(datetime.date.today()),
               "units": "world metres (campus frame, z up)", "note": "decimated RealityScan meshes; align_<c>.json: "
               "world = scale R x + t applied to the model.json cameras; see each align's note for its placement quality"},
              open(os.path.join(out, "README.json"), "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
