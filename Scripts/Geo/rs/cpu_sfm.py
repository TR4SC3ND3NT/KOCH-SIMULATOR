# CPU structure-from-motion for a small zone on a machine without an NVIDIA GPU (R1 stream B, handoff 0b), with
# pycolmap 4.2 (colmap.github.io/pycolmap, BSD): SIFT per clip folder (one SIMPLE_RADIAL camera per clip), pairs =
# neighbours inside each clip + a sparse all-to-all subset across clips (so separate clips of one place join),
# incremental mapping, undistortion, and a model.json for Scripts/Blender/sfm_overlay.py / pick_cams.py /
# route_profile.py (same fields as rs_to_model.py). Frames contain people: keep <work> outside git.
# Usage: python cpu_sfm.py --images <work>/images --work <work> [--seq 15] [--cross-every 3] [--max-size 1600]
#        python cpu_sfm.py --images ... --work ... --export K     (undistort sub-model K -> model_K.json)
#   <work>/images/<clip>/<clip>_fNNNNN.jpg (select_frames.py naming) -> <work>/sparse/<k>, <work>/undist, model.json
import argparse
import itertools
import json
import os
import sys

import numpy as np
import pycolmap


def pairs_file(images, path, seq, cross_every):
    clips = sorted(d for d in os.listdir(images) if os.path.isdir(os.path.join(images, d)))
    names = {c: sorted(f"{c}/{f}" for f in os.listdir(os.path.join(images, c)) if f.lower().endswith(".jpg"))
             for c in clips}
    pairs = set()
    for c in clips:
        L = names[c]
        for i in range(len(L)):
            for j in range(i + 1, min(len(L), i + 1 + seq)):
                pairs.add((L[i], L[j]))
    sub = [n for c in clips for n in names[c][::cross_every]]
    for a, b in itertools.combinations(sub, 2):
        if a.split("/")[0] != b.split("/")[0]:
            pairs.add((a, b))
    with open(path, "w") as f:
        for a, b in sorted(pairs):
            f.write(f"{a} {b}\n")
    return sum(len(v) for v in names.values()), len(pairs)


def to_model(rec, undist_dir, out, zone):
    cams = []
    for im in rec.images.values():
        if not im.has_pose:
            continue
        cam = rec.cameras[im.camera_id]
        f, cx, cy = cam.params[0], cam.params[-2], cam.params[-1]
        fy = cam.params[1] if cam.model.name == "PINHOLE" else f
        if cam.model.name == "PINHOLE":
            f, fy, cx, cy = cam.params
        T = im.cam_from_world() if callable(im.cam_from_world) else im.cam_from_world
        R, t = T.rotation.matrix(), T.translation
        cams.append({"name": im.name, "image": os.path.join(undist_dir, "images", im.name), "w": cam.width,
                     "h": cam.height, "f": float(f), "fy": float(fy), "cx": float(cx), "cy": float(cy),
                     "R": R.tolist(), "t": t.tolist(), "center": (-R.T @ t).tolist()})
    pts = [[*p.xyz.tolist(), *(p.color / 255.0).tolist()] for p in rec.points3D.values()]
    json.dump({"zone": zone, "frame": "pycolmap model (arbitrary similarity)", "cameras": cams, "points": pts},
              open(out, "w"))
    return len(cams), len(pts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--zone", default="zone")
    ap.add_argument("--seq", type=int, default=15, help="neighbours matched inside a clip")
    ap.add_argument("--cross-every", type=int, default=3, help="every Nth frame of each clip matched across clips")
    ap.add_argument("--max-size", type=int, default=1600)
    ap.add_argument("--features", type=int, default=6000)
    ap.add_argument("--export", type=int, help="only undistort + write model_<k>.json for sub-model k of <work>/sparse")
    a = ap.parse_args()
    if a.export is not None:
        und = os.path.join(a.work, f"undist_{a.export}")
        pycolmap.undistort_images(und, os.path.join(a.work, "sparse", str(a.export)), a.images)
        nc, npt = to_model(pycolmap.Reconstruction(os.path.join(und, "sparse")), und,
                           os.path.join(a.work, f"model_{a.export}.json"), f"{a.zone}_{a.export}")
        print(f"model_{a.export}.json: {nc} cameras, {npt} points")
        return
    os.makedirs(a.work, exist_ok=True)
    db = os.path.join(a.work, "db.db")
    pf = os.path.join(a.work, "pairs.txt")
    if not os.path.exists(db):
        ro = pycolmap.ImageReaderOptions()
        ro.camera_model = "SIMPLE_RADIAL"
        eo = pycolmap.FeatureExtractionOptions()
        eo.max_image_size = a.max_size
        eo.sift.max_num_features = a.features
        pycolmap.extract_features(db, a.images, camera_mode=pycolmap.CameraMode.PER_FOLDER, reader_options=ro,
                                  extraction_options=eo, device=pycolmap.Device.cpu)
        print("features done", flush=True)
        n, p = pairs_file(a.images, pf, a.seq, a.cross_every)
        print(f"{n} images, {p} pairs", flush=True)
        po = pycolmap.ImportedPairingOptions()
        po.match_list_path = pf
        pycolmap.match_image_pairs(db, pairing_options=po, device=pycolmap.Device.cpu)
        print("matching done", flush=True)
    sparse = os.path.join(a.work, "sparse")
    os.makedirs(sparse, exist_ok=True)
    recs = pycolmap.incremental_mapping(db, a.images, sparse)
    if not recs:
        raise SystemExit("no reconstruction")
    k, rec = max(recs.items(), key=lambda kv: kv[1].num_reg_images())
    for i, r in sorted(recs.items()):
        print(f"model {i}: {r.num_reg_images()} images, {r.num_points3D()} points")
    und = os.path.join(a.work, "undist")
    pycolmap.undistort_images(und, os.path.join(sparse, str(k)), a.images)
    rec_u = pycolmap.Reconstruction(os.path.join(und, "sparse"))
    nc, npt = to_model(rec_u, und, os.path.join(a.work, "model.json"), a.zone)
    print(f"model.json: {nc} cameras, {npt} points (largest model {k})")


if __name__ == "__main__":
    sys.exit(main())
