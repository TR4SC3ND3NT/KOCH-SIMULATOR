# People/vehicle masks for the RealityScan site mesh (R1 photogrammetry): writes <image>.mask.png next to each JPEG
# (RealityScan image-layer naming: white = used, black = ignored). Instance segmentation with Ultralytics YOLO-seg
# (AGPL-3.0, offline tool only, never shipped; docs.ultralytics.com/tasks/segment), masks dilated so edges and
# shadows at the feet do not leak features. Usage:
#   python mask_people.py --model yolo11x-seg.pt C:/koch/work/frames C:/koch/work/photos
import argparse
import os
import shutil
import sys

import cv2
import numpy as np
from ultralytics import YOLO

# COCO ids: person, bicycle, car, motorcycle, bus, truck, dog, backpack, umbrella, handbag, suitcase
MOVERS = {0, 1, 3, 5, 7, 16, 24, 25, 26, 28}
CARS = {2}  # parked cars are static scene; masked only with --cars (street clips with traffic)


def images(roots):
    for r in roots:
        for dp, _, fs in os.walk(r):
            if "_tmp" in dp:  # select_frames.py staging folder
                continue
            for f in sorted(fs):
                if f.lower().endswith((".jpg", ".jpeg")) and ".mask" not in f:
                    yield os.path.join(dp, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+")
    ap.add_argument("--model", default="yolo11x-seg.pt")
    ap.add_argument("--imgsz", type=int, default=1280)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--dilate", type=float, default=0.012, help="dilation radius as a fraction of the long side")
    ap.add_argument("--cars", action="store_true")
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--reuse", help="folder tree with masks from an earlier frame set: same-named masks are copied")
    a = ap.parse_args()
    classes = sorted(MOVERS | (CARS if a.cars else set()))
    if a.reuse:
        old = {}
        for dp, _, fs in os.walk(a.reuse):
            for f in fs:
                if f.endswith(".mask.png"):
                    old[f] = os.path.join(dp, f)
        n = 0
        for p in images(a.roots):
            m = os.path.basename(p) + ".mask.png"
            if m in old and not os.path.exists(p + ".mask.png"):
                shutil.copyfile(old[m], p + ".mask.png")
                n += 1
        print(f"reused {n} masks from {a.reuse}", flush=True)
    model = YOLO(a.model)
    todo = [p for p in images(a.roots) if a.redo or not os.path.exists(p + ".mask.png")]
    print(f"{len(todo)} images to mask", flush=True)
    masked = 0
    for i, path in enumerate(todo):
        img = cv2.imread(path)
        h, w = img.shape[:2]
        keep = np.full((h, w), 255, np.uint8)
        r = model.predict(img, imgsz=a.imgsz, conf=a.conf, classes=classes, retina_masks=True, half=True,
                          verbose=False)[0]
        if r.masks is not None and len(r.masks):
            m = (r.masks.data.cpu().numpy().max(0) > 0.5).astype(np.uint8)
            if m.shape != (h, w):
                m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
            k = max(3, int(a.dilate * max(h, w)) | 1)
            m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
            keep[m > 0] = 0
            masked += 1
        cv2.imwrite(path + ".mask.png", keep)
        if i % 100 == 0:
            print(f"{i}/{len(todo)} ({masked} with detections)", flush=True)
    print(f"done: {len(todo)} masks, {masked} with detections")


if __name__ == "__main__":
    sys.exit(main())
