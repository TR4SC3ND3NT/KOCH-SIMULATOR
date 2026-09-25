# Sparse SfM for one greybox zone (R1): frames from video segments + stills -> pycolmap (CPU) -> JSON for Blender.
# Frames and the COLMAP workspace stay in a scratch dir (captures contain people: never commit them).
# Run (pycolmap wheels need Python <= 3.12, so not the Scripts/ uv env):
#   uv run --python 3.12 --with pycolmap==4.2.0 --with numpy --with pillow python Scripts/Geo/sfm_zone.py zone.json
# zone.json: {"name": "C_basement", "work": "/abs/scratch/dir",
#   "videos": [{"file": "PXL_...mp4", "t0": 0, "t1": 20, "fps": 3}], "photos": ["PXL_....jpg"],
#   "max_side": 1600, "matcher": "sequential"|"exhaustive", "camera_model": "SIMPLE_RADIAL"|"OPENCV", "mapper": "incremental"|"global"}
# Output: <work>/undist (PINHOLE model + images, SBCV-importable) and <work>/model.json {cameras:[{name, image, f, cx, cy, w, h, R(world->cam), t, center}], points:[[x,y,z,r,g,b,err,track]]}
import json
import os
import subprocess
import sys

import numpy as np
import pycolmap
from PIL import Image, ImageOps

RAW = os.path.expanduser(os.environ.get("KOCH_CAPTURE_DIR", "~/site-capture")) + "/raw"
DIAG_35MM = 43.27  # 35 mm-equivalent focal is defined on the 36x24 mm diagonal


def extract(zone, img_dir):
    """Write frames/stills as <group>/<name>.jpg; returns {group: f35_mm or None}."""
    groups = {}
    ms = zone.get("max_side", 1600)
    for k, v in enumerate(zone.get("videos", [])):
        g = f"v{k:02d}_{os.path.splitext(v['file'])[0][-9:]}"
        d = os.path.join(img_dir, g)
        os.makedirs(d, exist_ok=True)
        if not os.listdir(d):
            vf = f"fps={v.get('fps', 3)},scale='if(gt(iw,ih),{ms},-2)':'if(gt(iw,ih),-2,{ms})'"
            cmd = ["ffmpeg", "-v", "error", "-ss", str(v.get("t0", 0))]
            if "t1" in v:
                cmd += ["-to", str(v["t1"])]
            cmd += ["-i", os.path.join(RAW, v["file"]), "-vf", vf, "-q:v", "2", os.path.join(d, "%04d.jpg")]
            subprocess.run(cmd, check=True)
        groups[g] = v.get("f35")  # video: EIS crop changes intrinsics; let COLMAP refine from a prior
    for p in zone.get("photos", []):
        src = p if os.path.isabs(p) else os.path.join(RAW, p)  # absolute paths: photos sent outside the capture set
        im = Image.open(src)
        f35 = float(im.getexif().get_ifd(0x8769).get(41989) or 0) or zone.get("default_f35", {}).get(p)
        g = f"p{int(f35 or 0):02d}mm"
        d = os.path.join(img_dir, g)
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, os.path.splitext(p)[0][-9:] + ".jpg")
        if not os.path.exists(out):
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((ms, ms))
            im.save(out, quality=95)
        groups[g] = f35
    return groups


def drop_outlier_cameras(out, k=6.0):
    """Global mapping can register a few frames far away (bad pairs); drop cameras beyond k x the robust spread."""
    C = np.array([c["center"] for c in out["cameras"]])
    med = np.median(C, 0)
    d = np.linalg.norm(C - med, axis=1)
    lim = k * np.median(d) + 1e-9
    bad = [c["name"] for c, di in zip(out["cameras"], d) if di > lim]
    out["cameras"] = [c for c, di in zip(out["cameras"], d) if di <= lim]
    if bad:
        print("dropped outlier cameras:", bad)


def main():
    zone = json.load(open(sys.argv[1]))
    work = zone["work"]
    img_dir, db, sparse = os.path.join(work, "images"), os.path.join(work, "db.db"), os.path.join(work, "sparse")
    os.makedirs(sparse, exist_ok=True)
    groups = extract(zone, img_dir)
    if os.path.exists(db):
        os.remove(db)
    ro = pycolmap.ImageReaderOptions()
    ro.camera_model = zone.get("camera_model", "SIMPLE_RADIAL")
    eo = pycolmap.FeatureExtractionOptions()
    eo.sift.max_num_features = zone.get("max_features", 8000)
    pycolmap.extract_features(db, img_dir, camera_mode=pycolmap.CameraMode.PER_FOLDER, reader_options=ro,
                              extraction_options=eo, device=pycolmap.Device.cpu)
    # Focal priors from EXIF 35 mm-eq (stills) or a per-video guess (Pixel 9 4K EIS ~26 mm-eq main lens).
    with pycolmap.Database.open(db) as d:
        cams = {c.camera_id: c for c in d.read_all_cameras()}
        for im in d.read_all_images():
            c = cams[im.camera_id]
            f35 = groups.get(im.name.split("/")[0]) or 26.0  # p00mm/p27mm groups: EXIF-less photos use their prior
            f = f35 * np.hypot(c.width, c.height) / DIAG_35MM
            p = list(c.params)
            if c.model.name in ("SIMPLE_RADIAL", "SIMPLE_PINHOLE", "RADIAL"):
                p[:3] = [f, c.width / 2, c.height / 2]
            else:  # PINHOLE / OPENCV...: fx, fy, cx, cy first
                p[:4] = [f, f, c.width / 2, c.height / 2]
            c.params = p
            c.has_prior_focal_length = True
            d.update_camera(c)
    if zone.get("matcher", "sequential") == "sequential" and not zone.get("photos"):
        po = pycolmap.SequentialPairingOptions()
        po.overlap = zone.get("overlap", 12)
        po.quadratic_overlap = True
        pycolmap.match_sequential(db, pairing_options=po, device=pycolmap.Device.cpu)
    else:
        pycolmap.match_exhaustive(db, device=pycolmap.Device.cpu)
    if zone.get("mapper") == "global":  # GLOMAP (merged into COLMAP 4): less drift on long sequences
        maps = pycolmap.global_mapping(db, img_dir, sparse)
    else:
        maps = pycolmap.incremental_mapping(db, img_dir, sparse)
    if not maps:
        sys.exit("no reconstruction")
    bid, best = max(maps.items(), key=lambda kv: kv[1].num_reg_images())
    print(best.summary())
    # Undistort to PINHOLE (the Blender importer and our overlays ignore radial terms); writes undist/{images,sparse}.
    und = os.path.join(work, "undist")
    pycolmap.undistort_images(und, os.path.join(sparse, str(bid)), img_dir)
    best = pycolmap.Reconstruction(os.path.join(und, "sparse"))
    out = {"zone": zone["name"], "cameras": [], "points": []}
    for im in best.images.values():
        cam = best.cameras[im.camera_id]
        cfw = im.cam_from_world() if callable(im.cam_from_world) else im.cam_from_world
        R, t = cfw.rotation.matrix(), cfw.translation
        fx, fy, cx, cy = cam.params  # PINHOLE after undistortion
        out["cameras"].append({"name": im.name, "image": os.path.join(und, "images", im.name), "w": cam.width, "h": cam.height,
                               "f": float(fx), "fy": float(fy), "cx": float(cx), "cy": float(cy),
                               "R": R.tolist(), "t": t.tolist(), "center": (-R.T @ t).tolist()})
    for pt in best.points3D.values():
        if pt.error < 2.0 and len(pt.track.elements) >= 3:
            out["points"].append([*map(float, pt.xyz), *map(int, pt.color), round(float(pt.error), 3), len(pt.track.elements)])
    drop_outlier_cameras(out)
    json.dump(out, open(os.path.join(work, "model.json"), "w"))
    print(f"model.json: {len(out['cameras'])} cameras, {len(out['points'])} points (of {len(zone.get('videos', []))} videos, "
          f"{len(zone.get('photos', []))} photos)")


if __name__ == "__main__":
    main()
