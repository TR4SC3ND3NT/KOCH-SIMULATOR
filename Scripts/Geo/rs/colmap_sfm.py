# Fallback / video-aware SfM for the site (R1 photogrammetry; docs/decisions.md 2026-09-26 fallback): COLMAP 4.2 CUDA
# (colmap.github.io) with per-clip cameras, people masks, sequential matching (neighbour frames + vocab-tree loop
# closure) plus vocab-tree matching across clips, then the global mapper (GLOMAP). The result can be loaded into
# RealityScan (-loadColmap) for GPU meshing, or converted for sfm_overlay.py.
# Layout it builds under <work>: images/<clip>/<frame>.jpg (directory junctions to the frame folders; stills are
# grouped per lens+size so each group is one camera), masks/<clip>/<frame>.jpg.png (hard links to *.mask.png).
# Usage: python colmap_sfm.py --work C:/koch/work/sfm --frames C:/koch/work/frames_a --photos C:/koch/work/photos \
#          --colmap C:/koch/work/tools/colmap/bin/colmap.exe --vocab C:/koch/work/tools/vocab_tree_faiss_flickr100K_words256K.bin
import argparse
import os
import shutil
import subprocess
import sys

from PIL import Image


def run(cmd, log):
    print(" ".join(cmd[:2]), flush=True)
    with open(log, "a") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode:
        raise SystemExit(f"{cmd[1]} failed ({r.returncode}), see {log}")


def junction(src, dst):
    if not os.path.exists(dst):
        subprocess.run(["cmd", "/c", "mklink", "/J", dst, src], check=True, stdout=subprocess.DEVNULL)


def layout(a):
    img, msk = os.path.join(a.work, "images"), os.path.join(a.work, "masks")
    os.makedirs(img, exist_ok=True)
    os.makedirs(msk, exist_ok=True)
    for clip in sorted(os.listdir(a.frames)):
        src = os.path.join(a.frames, clip)
        if not os.path.isdir(src):
            continue
        junction(src, os.path.join(img, clip))
        os.makedirs(os.path.join(msk, clip), exist_ok=True)
        for f in os.listdir(src):
            if f.endswith(".mask.png"):
                dst = os.path.join(msk, clip, f.replace(".mask.png", ".png"))  # x.jpg.mask.png -> x.jpg.png
                if not os.path.exists(dst):
                    os.link(os.path.join(src, f), dst)
    if a.photos:
        for dp, _, fs in os.walk(a.photos):
            for f in fs:
                if not f.lower().endswith(".jpg") or ".mask" in f:
                    continue
                p = os.path.join(dp, f)
                im = Image.open(p)
                f35 = int(float(im.getexif().get_ifd(0x8769).get(41989) or 0))
                w, h = im.size
                if im.getexif().get(0x0112, 1) in (6, 8):
                    w, h = h, w
                g = f"photo_{f35:02d}mm_{w}x{h}"
                os.makedirs(os.path.join(img, g), exist_ok=True)
                os.makedirs(os.path.join(msk, g), exist_ok=True)
                d = os.path.join(img, g, f)
                if not os.path.exists(d):
                    os.link(p, d)
                m = p + ".mask.png"
                if os.path.exists(m) and not os.path.exists(os.path.join(msk, g, f + ".png")):
                    os.link(m, os.path.join(msk, g, f + ".png"))
    return img, msk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--photos")
    ap.add_argument("--colmap", required=True)
    ap.add_argument("--vocab", required=True)
    ap.add_argument("--max-size", type=int, default=3200)
    ap.add_argument("--features", type=int, default=12000)
    ap.add_argument("--overlap", type=int, default=20)
    ap.add_argument("--stage", default="all", choices=["all", "extract", "match", "map"])
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    img, msk = layout(a)
    db, log = os.path.join(a.work, "db.db"), os.path.join(a.work, "colmap.log")
    C = a.colmap
    if a.stage in ("all", "extract"):
        run([C, "feature_extractor", "--database_path", db, "--image_path", img, "--ImageReader.mask_path", msk,
             "--ImageReader.camera_model", "OPENCV", "--ImageReader.single_camera_per_folder", "1",
             "--FeatureExtraction.use_gpu", "1", "--FeatureExtraction.max_image_size", str(a.max_size),
             "--SiftExtraction.max_num_features", str(a.features)], log)
    if a.stage in ("all", "match"):
        run([C, "sequential_matcher", "--database_path", db, "--SequentialMatching.overlap", str(a.overlap),
             "--SequentialMatching.quadratic_overlap", "1", "--SequentialMatching.loop_detection", "1",
             "--SequentialMatching.vocab_tree_path", a.vocab, "--FeatureMatching.use_gpu", "1"], log)
        run([C, "vocab_tree_matcher", "--database_path", db, "--VocabTreeMatching.vocab_tree_path", a.vocab,
             "--VocabTreeMatching.num_images", "50", "--FeatureMatching.use_gpu", "1"], log)
    if a.stage in ("all", "map"):
        out = os.path.join(a.work, "sparse")
        if os.path.isdir(out):
            shutil.rmtree(out)
        os.makedirs(out)
        run([C, "global_mapper", "--database_path", db, "--image_path", img, "--output_path", out], log)
        for d in sorted(os.listdir(out)):
            run([C, "model_analyzer", "--path", os.path.join(out, d)], os.path.join(a.work, f"analyze_{d}.log"))
            print(d, open(os.path.join(a.work, f"analyze_{d}.log")).read()[-600:])


if __name__ == "__main__":
    sys.exit(main())
