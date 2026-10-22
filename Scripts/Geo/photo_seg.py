# Batch semantic segmentation of owner photos for the R1 photo-vs-model bug hunt: two Mask2Former checkpoints on CPU,
# fused into the class set of Scripts/Blender/render_semantic.py, so photo and model class maps compare pixel by pixel.
# Mapillary Vistas gives the ground classes (curb, sidewalk / pedestrian area, road, terrain); ADE20K adds what Vistas
# lacks (stairs, railing, roof, window, door). Research 2026-10-22: ~20 s + ~10 s per photo on 6 threads.
# Checkpoints: facebook/mask2former-swin-large-mapillary-vistas-semantic, facebook/mask2former-swin-large-ade-semantic
# (local QA only, never shipped). Run (needs torch-cpu + transformers):
#   python Scripts/Geo/photo_seg.py LIST.txt OUT_DIR      (LIST: one photo path per line; done photos are skipped)
# Writes OUT_DIR/<basename>_cls.png (palette PNG: index = CLASS_LIST order), _vis.jpg (photo | overlay) and appends
# OUT_DIR/index.jsonl {photo, cls, size, seconds}. The fused map is at SHORT px on the short side.
import json
import os
import sys
import time

import numpy as np
import torch
from PIL import Image, ImageOps
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation

SHORT = int(os.environ.get("KOCH_SEG_SHORT", "1024"))   # 768: ~1.7x faster, kerbs still resolved
# same names/colours as render_semantic.CLASSES, plus photo-only classes (masked out of the diff)
CLASS_LIST = ["unknown", "grass", "soil", "paving", "road", "kerb", "stairs", "wall", "roof", "window", "door",
              "vegetation", "metal", "sign", "water", "other", "sky", "person", "vehicle"]
COLOURS = {"unknown": (0, 0, 0), "grass": (60, 180, 75), "soil": (140, 90, 40), "paving": (200, 200, 200),
           "road": (70, 70, 80), "kerb": (255, 225, 25), "stairs": (245, 130, 48), "wall": (230, 25, 75),
           "roof": (145, 30, 180), "window": (70, 240, 240), "door": (240, 50, 230), "vegetation": (0, 100, 0),
           "metal": (0, 0, 128), "sign": (255, 250, 200), "water": (0, 130, 200), "other": (128, 128, 0),
           "sky": (135, 206, 235), "person": (255, 0, 0), "vehicle": (255, 128, 128)}
VISTAS = {  # Mapillary Vistas v1.2 label -> our class (unlisted -> other)
    "Curb": "kerb", "Curb Cut": "kerb", "Sidewalk": "paving", "Pedestrian Area": "paving", "Crosswalk - Plain": "road",
    "Lane Marking - Crosswalk": "road", "Lane Marking - General": "road", "Road": "road", "Parking": "road",
    "Service Lane": "road", "Bike Lane": "road", "Rail Track": "road", "Terrain": "grass", "Vegetation": "vegetation",
    "Building": "wall", "Wall": "wall", "Bridge": "wall", "Tunnel": "wall", "Fence": "metal", "Guard Rail": "metal",
    "Barrier": "metal", "Pole": "metal", "Utility Pole": "metal", "Street Light": "metal", "Traffic Light": "metal",
    "Traffic Sign Frame": "metal", "Sky": "sky", "Person": "person", "Bicyclist": "person", "Motorcyclist": "person",
    "Other Rider": "person", "Car": "vehicle", "Truck": "vehicle", "Bus": "vehicle", "Bicycle": "vehicle",
    "Motorcycle": "vehicle", "Other Vehicle": "vehicle", "Trailer": "vehicle", "Caravan": "vehicle",
    "On Rails": "vehicle", "Boat": "vehicle", "Wheeled Slow": "vehicle", "Car Mount": "vehicle", "Ego Vehicle": "vehicle",
    "Water": "water", "Sand": "soil", "Snow": "unknown", "Mountain": "unknown", "Billboard": "sign", "Banner": "sign",
    "Traffic Sign (Front)": "sign", "Traffic Sign (Back)": "sign", "Signage": "sign",
}
ADE_OVER = {  # ADE20K label -> our class, applied where it adds what Vistas cannot say
    "stairs": "stairs", "stairway": "stairs", "step": "stairs", "railing": "metal", "bannister": "metal",
    "roof": "roof", "windowpane": "window", "window": "window", "door": "door", "screen door": "door",
    "grass": "grass", "column": "wall", "awning": "roof", "canopy": "roof",
}
ADE_WHERE = {"stairs": {"wall", "paving", "road", "kerb", "other"}, "metal": {"wall", "paving", "other", "vegetation"},
             "roof": {"wall", "other", "sky"}, "window": {"wall", "other"}, "door": {"wall", "other"},
             "grass": {"soil", "paving", "other"}, "wall": {"other"}}   # ADE only overrides these Vistas classes (keeps curb/sidewalk)


def load(ckpt):
    return AutoImageProcessor.from_pretrained(ckpt), Mask2FormerForUniversalSegmentation.from_pretrained(ckpt).eval()


def run(proc, model, im):
    inp = proc(images=im, return_tensors="pt", do_resize=False)
    with torch.inference_mode():
        o = model(**inp)
    return proc.post_process_semantic_segmentation(o, target_sizes=[im.size[::-1]])[0].numpy()


def main():
    torch.set_num_threads(int(os.environ.get("KOCH_SEG_THREADS", "6")))
    photos = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    vp, vm = load("facebook/mask2former-swin-large-mapillary-vistas-semantic")
    ap, am = load("facebook/mask2former-swin-large-ade-semantic")
    vl = {k: VISTAS.get(v, "other") for k, v in vm.config.id2label.items()}
    al = {k: ADE_OVER.get(v) for k, v in am.config.id2label.items()}
    ci = {c: i for i, c in enumerate(CLASS_LIST)}
    pal = np.zeros((256, 3), np.uint8)
    for c, i in ci.items():
        pal[i] = COLOURS[c]
    vlut = np.array([ci[vl[k]] for k in range(len(vl))], np.uint8)
    for p in photos:
        base = os.path.splitext(os.path.basename(p))[0]
        dst = os.path.join(out, base + "_cls.png")
        if os.path.exists(dst):
            continue
        t = time.time()
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        s = SHORT / min(im.size)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.BICUBIC)
        cls = vlut[run(vp, vm, im)]
        ade = run(ap, am, im.resize((round(im.width * 0.75), round(im.height * 0.75)), Image.BICUBIC))
        ade = np.asarray(Image.fromarray(ade.astype(np.int32)).resize(im.size, Image.NEAREST))
        for k, c in al.items():
            if c is None:
                continue
            m = ade == k
            if m.any():
                allowed = np.isin(cls, [ci[x] for x in ADE_WHERE[c]])
                cls[m & allowed] = ci[c]
        img = Image.fromarray(cls, "P")
        img.putpalette(pal.ravel().tolist())
        img.save(dst)
        ov = (0.5 * np.asarray(im) + 0.5 * pal[cls]).astype(np.uint8)
        Image.fromarray(np.concatenate([np.asarray(im), ov], 1)).resize((im.width, im.height // 2)).save(
            os.path.join(out, base + "_vis.jpg"), quality=85)
        with open(os.path.join(out, "index.jsonl"), "a") as f:
            f.write(json.dumps({"photo": p, "cls": dst, "size": im.size, "seconds": round(time.time() - t, 1)}) + "\n")
        print(base, round(time.time() - t, 1), "s", flush=True)


main()
