# Round-trip proof of the ue_prep transform convention (R1, inside Blender, read-only): re-reads the exported FBX
# files, maps asset vertices into UE space the way UE's FBX importer does (node Lcl transform -> cm, file axes ==
# UE's target frame, then Y mirror), applies the manifest UE transform, maps back to Blender and compares with the
# source objects' world vertices (both directions, nearest vertex) and the terrain surface. Prints the max error.
# Run: blender -b IN.blend -P Scripts/Blender/ue_prep/roundtrip.py -- OUT_DIR [--n 300] [--seed 0]
import argparse
import json
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ue_prep.common import S_FLIP, TERRAIN, ue_matrix_from_rotator   # noqa: E402
from ue_prep.fbxread import read                                     # noqa: E402

EXPECT_AXES = {"UpAxis": 2, "UpAxisSign": 1, "FrontAxis": 1, "FrontAxisSign": -1, "CoordAxis": 0, "CoordAxisSign": 1}


def file_cm(model):
    """FBX node vertices -> file units (cm, Blender axes): v * Lcl Scaling + Lcl Translation (rotation is 0)."""
    v = np.array(model["verts"], np.float64)
    if any(abs(r) > 1e-9 for r in model["lcl_r"]):
        raise SystemExit("roundtrip: unexpected node rotation")
    return v * np.array(model["lcl_s"]) + np.array(model["lcl_t"])


def ue_world_to_blender(v_file_cm, inst):
    v_ue = v_file_cm @ S_FLIP.T                       # UE FBX import: Y mirror (asset space, cm)
    r = ue_matrix_from_rotator(*inst["rot"]) @ np.diag(inst["scale"])
    w_ue = v_ue @ r.T + np.array(inst["loc"])
    return w_ue @ S_FLIP.T / 100.0                     # back to Blender metres


def world_verts(ob):
    me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    m = np.array(ob.matrix_world)
    return co.reshape(-1, 3).astype(np.float64) @ m[:3, :3].T + m[:3, 3]


def nearest_max(a, b):
    kd = KDTree(len(b))
    for i, p in enumerate(b):
        kd.insert(p.tolist(), i)
    kd.balance()
    return max(kd.find(p.tolist())[2] for p in a)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    bpy.context.view_layer.update()
    with open(os.path.join(a.out, "manifest.json")) as fh:
        man = json.load(fh)
    meshes = man["meshes"]
    pool = [e for e in man["instances"] if e["role"] != "ground" and e["name"] in bpy.data.objects]
    rnd = random.Random(a.seed)
    mirrored = [e for e in pool if e.get("mirrored_src")]
    sample = rnd.sample(pool, min(a.n, len(pool)))
    sample += [e for e in rnd.sample(mirrored, min(50, len(mirrored))) if e not in sample]
    cache, hdr_bad = {}, 0
    err_fwd = err_bwd = err_bb = err_col = 0.0
    worst, worst_col = ("", 0.0), ("", 0.0)
    for e in sample:
        m = meshes[e["mesh"]]
        if e["mesh"] not in cache:
            f = read(os.path.join(a.out, m["file"]))
            hdr_bad += any(f["axes"].get(k) != v for k, v in EXPECT_AXES.items()) or f["unit"] != 1.0
            cache[e["mesh"]] = f
        f = cache[e["mesh"]]
        rec = ue_world_to_blender(file_cm(f["models"][e["mesh"]]), e)
        src = world_verts(bpy.data.objects[e["name"]])
        fwd, bwd = nearest_max(rec, src), nearest_max(src, rec)
        bb = float(np.abs(np.r_[rec.min(0) - src.min(0), rec.max(0) - src.max(0)]).max())
        lo, hi = src.min(0) - 2e-3, src.max(0) + 2e-3
        for k, mod in f["models"].items():
            if k.startswith(("UBX_", "UCX_")):
                c = ue_world_to_blender(file_cm(mod), e)
                d = float(np.maximum(lo - c, c - hi).max())
                if d > worst_col[1]:
                    worst_col = (k, d)
                err_col = max(err_col, d)
        err_fwd, err_bwd, err_bb = max(err_fwd, fwd), max(err_bwd, bwd), max(err_bb, bb)
        if max(fwd, bwd) > worst[1]:
            worst = (e["name"], max(fwd, bwd))
    # cross-check the stdlib FBX reader against Blender's own FBX importer on a few files
    err_imp, sc = 0.0, bpy.data.scenes.new("_ue_prep_rt")
    for name in sorted(cache)[:20]:
        with bpy.context.temp_override(scene=sc, view_layer=sc.view_layers[0]):
            bpy.ops.import_scene.fbx(filepath=os.path.join(a.out, meshes[name]["file"]))
        sc.view_layers[0].update()
        ob = next(o for o in sc.objects if o.name.startswith(name))
        co = np.empty(len(ob.data.vertices) * 3, np.float32)
        ob.data.vertices.foreach_get("co", co)
        mw = np.array(ob.matrix_world)
        imp = co.reshape(-1, 3).astype(np.float64) @ mw[:3, :3].T + mw[:3, 3]
        mine = file_cm(cache[name]["models"][name]) / 100.0
        err_imp = max(err_imp, float(np.abs(np.sort(imp, 0) - np.sort(mine, 0)).max()))
        for o in list(sc.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.scenes.remove(sc)
    # terrain tiles: every exported vertex must lie on the source terrain surface
    ter = bpy.data.objects.get(TERRAIN)
    err_ter, nt, ter_at = 0.0, 0, None
    if ter is not None:
        tv = world_verts(ter)
        bvh = BVHTree.FromPolygons([Vector(p) for p in tv], [tuple(p.vertices) for p in ter.data.polygons])
        for e in man["instances"]:
            if e["role"] != "ground":
                continue
            f = read(os.path.join(a.out, meshes[e["mesh"]]["file"]))
            rec = ue_world_to_blender(file_cm(f["models"][e["mesh"]]), e)
            d = [bvh.find_nearest(Vector(p))[3] for p in rec]
            i = int(np.argmax(d))
            if d[i] > err_ter:
                err_ter, ter_at = d[i], rec[i].round(4).tolist()
            nt += 1
    ex = next((e for e in sample if abs(((np.degrees(bpy.data.objects[e["name"]].matrix_world.to_euler().z) + 45) % 90)
                                         - 45) > 1), sample[0])   # an object with a non-90-degree yaw
    ob = bpy.data.objects[ex["name"]]
    print(f"roundtrip: example {ex['name']}: blender loc {tuple(round(x, 3) for x in ob.matrix_world.translation)} "
          f"yaw {np.degrees(ob.matrix_world.to_euler().z):.3f} -> UE loc {ex['loc']} rot {ex['rot']}")
    res = {"objects": len(sample), "mirrored_in_sample": sum(1 for e in sample if e.get("mirrored_src")),
           "max_err_mm_rec_to_src": round(err_fwd * 1000, 3), "max_err_mm_src_to_rec": round(err_bwd * 1000, 3),
           "max_bbox_err_mm": round(err_bb * 1000, 3), "max_collision_outside_bbox_mm": round(max(err_col, 0) * 1000, 3),
           "tiles": nt, "max_tile_off_surface_mm": round(err_ter * 1000, 3), "tile_worst_at": ter_at, "bad_headers": int(hdr_bad), "reader_vs_blender_import_mm": round(err_imp * 1000, 4),
           "worst": worst[0], "worst_collision": worst_col[0]}
    print("roundtrip: " + json.dumps(res))


main()
