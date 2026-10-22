# Photo-vs-model disagreement candidates for the R1 bug hunt: compares the photo's semantic map (photo_seg.py) with
# the greybox class map from the solved camera (model_raycast.py) and returns connected blobs where they disagree,
# each with its world xy (median of the hit points), the model objects under it and numbered review tiles
# (Set-of-Mark style: numbered outlines on the photo, plus photo | model crops per blob; SoM, arXiv 2310.11441).
# False positives are expected (segmentation errors, residual pose error, occluders): every blob is only a CANDIDATE
# that a reviewer confirms or rejects. Construction-progress-monitoring practice (Golparvar-Fard et al. 2011):
# mask occluders, ignore a band around boundaries, and trust blobs that several photos agree on.
# Run: python Scripts/Geo/diff_blobs.py MODEL.npz PHOTO.jpg SEG_cls.png CAM.json --out PREFIX [--max-dist 40]
# Writes PREFIX_blobs.json, PREFIX_marks.jpg and PREFIX_blob_<k>.jpg.
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_raycast import Model, edges   # noqa: E402

PHOTO_CLASSES = ["unknown", "grass", "soil", "paving", "road", "kerb", "stairs", "wall", "roof", "window", "door",
                 "vegetation", "metal", "sign", "water", "other", "sky", "person", "vehicle"]
# comparable labels; window/door/sign fold into wall (the segmenters split facades unreliably)
FOLD = {"window": "wall", "door": "wall", "sign": "wall"}
CMP = ["grass", "soil", "paving", "road", "kerb", "stairs", "wall", "roof", "vegetation", "sky"]
PHOTO_IGNORE = {"unknown", "metal", "water", "other", "person", "vehicle"}
MODEL_IGNORE = {"metal", "other", "terrain_other"}
EQUIV = [{"grass", "soil"}]   # the segmenters confuse these; a lawn bed's soil is still "not paving"


def label_maps(m, r, seg):
    ci = {c: i for i, c in enumerate(CMP)}
    pl = np.full(seg.shape, -1, np.int16)
    for i, c in enumerate(PHOTO_CLASSES):
        c2 = FOLD.get(c, c)
        if c2 in ci and c not in PHOTO_IGNORE:
            pl[seg == i] = ci[c2]
    ml = np.full(seg.shape, -1, np.int16)
    for i, c in enumerate(m.classes):
        c2 = FOLD.get(str(c), str(c))
        if c2 in ci and c2 not in MODEL_IGNORE:
            ml[r["cls"] == i] = ci[c2]
    ml[~r["hit"]] = ci["sky"]
    for s in EQUIV:
        ids = [ci[c] for c in s]
        pl[np.isin(pl, ids)] = ids[0]
        ml[np.isin(ml, ids)] = ids[0]
    return pl, ml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("photo")
    ap.add_argument("seg")
    ap.add_argument("cam")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=768)
    ap.add_argument("--max-dist", type=float, default=40.0)
    ap.add_argument("--band", type=int, default=6, help="px ignored around model and photo class boundaries")
    ap.add_argument("--min-frac", type=float, default=0.0015, help="min blob area as a fraction of the image")
    a = ap.parse_args()
    m = Model(a.model)
    c = json.load(open(a.cam))["cameras"][0]
    W0, H0 = c["w"], c["h"]
    w = a.width
    h = round(w * H0 / W0)
    s = w / W0
    K = np.array([[c["f"] * s, 0, c.get("cx", W0 / 2) * s], [0, c.get("fy", c["f"]) * s, c.get("cy", H0 / 2) * s], [0, 0, 1]])
    Rt = np.hstack([np.array(c["R"]), np.array(c["t"]).reshape(3, 1)])
    r = m.cast(K, Rt, w, h)
    seg = np.asarray(Image.open(a.seg).resize((w, h), Image.NEAREST))
    pl, ml = label_maps(m, r, seg)
    ph = np.asarray(ImageOps.exif_transpose(Image.open(a.photo)).convert("RGB").resize((w, h), Image.BICUBIC))
    valid = (pl >= 0) & (ml >= 0)
    valid &= ~(r["hit"] & (np.nan_to_num(r["dist"], nan=0) > a.max_dist))
    # occluders: photo vegetation in front of model ground/wall is a tree, not a surface bug (its size is checked apart)
    veg = CMP.index("vegetation")
    valid &= ~((pl == veg) & (ml != veg) & (ml != CMP.index("sky")))
    band = ndimage.binary_dilation(edges(r), iterations=a.band)
    pb = np.zeros_like(band)
    pb[:, 1:] |= pl[:, 1:] != pl[:, :-1]
    pb[1:, :] |= pl[1:, :] != pl[:-1, :]
    band |= ndimage.binary_dilation(pb, iterations=max(1, a.band // 2))
    dis = valid & (pl != ml) & ~band
    dis = ndimage.binary_opening(dis, iterations=2)
    lab, n = ndimage.label(dis)
    blobs = []
    for k in range(1, n + 1):
        mk = lab == k
        area = int(mk.sum())
        if area < a.min_frac * w * h:
            continue
        ys, xs = np.nonzero(mk)
        pc = np.bincount(pl[mk], minlength=len(CMP))
        mc = np.bincount(ml[mk], minlength=len(CMP))
        hit = mk & r["hit"]
        xyz = np.median(r["xyz"][hit], 0).round(2).tolist() if hit.any() else None
        oids, cnt = np.unique(r["oid"][hit], return_counts=True) if hit.any() else ([], [])
        objs = [(str(m.names[o]), int(n_)) for o, n_ in sorted(zip(oids, cnt), key=lambda t: -t[1])[:4] if o >= 0]
        note = ""
        if not hit.any() and CMP[int(pc.argmax())] == "wall":
            note = "background building beyond the model (context ring): usually out of scope"
        blobs.append({"k": len(blobs) + 1, "note": note, "photo_class": CMP[int(pc.argmax())], "model_class": CMP[int(mc.argmax())],
                      "px_bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], "area_px": area,
                      "area_frac": round(area / (w * h), 4), "world_xyz": xyz,
                      "dist_m": float(np.nanmedian(r["dist"][hit])) if hit.any() else None, "objects": objs,
                      "_mask": mk})
    blobs.sort(key=lambda b: -b["area_px"])
    for i, b in enumerate(blobs, 1):
        b["k"] = i
    # marks image: photo with numbered outlines
    mk_img = Image.fromarray(ph.copy())
    d = ImageDraw.Draw(mk_img)
    ov = np.asarray(mk_img).copy()
    for b in blobs:
        ov[ndimage.binary_dilation(b["_mask"], iterations=1) & ~b["_mask"]] = (255, 0, 255)
    mk_img = Image.fromarray(ov)
    d = ImageDraw.Draw(mk_img)
    for b in blobs:
        x0, y0, x1, y1 = b["px_bbox"]
        d.rectangle([x0 - 2, y0 - 2, x0 + 26, y0 + 14], fill=(0, 0, 0))
        d.text((x0 + 1, y0), str(b["k"]), fill=(255, 255, 0))
    mk_img.save(a.out + "_marks.jpg", quality=88)
    mcol = m.class_image(r)
    for b in blobs:
        x0, y0, x1, y1 = b["px_bbox"]
        pad = max(24, (x1 - x0) // 2, (y1 - y0) // 2)
        X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
        ring = ndimage.binary_dilation(b["_mask"], iterations=1) & ~b["_mask"]
        a1, a2 = ph.copy(), mcol.copy()
        a1[ring] = a2[ring] = (255, 0, 255)
        tile = np.concatenate([a1[Y0:Y1, X0:X1], a2[Y0:Y1, X0:X1]], 1)
        im = Image.fromarray(tile)
        sc = min(1000 / im.width, 700 / im.height, 4.0)
        im.resize((round(im.width * sc), round(im.height * sc)), Image.NEAREST).save(f"{a.out}_blob_{b['k']}.jpg", quality=90)
        del b["_mask"]
    ious = {}
    for i, cname in enumerate(CMP):
        A, B = (pl == i) & valid, (ml == i) & valid
        if A.sum() > 50 or B.sum() > 50:
            ious[cname] = round(float((A & B).sum() / max((A | B).sum(), 1)), 3)
    json.dump({"photo": a.photo, "cam": a.cam, "size": [w, h], "iou": ious, "blobs": blobs}, open(a.out + "_blobs.json", "w"),
              indent=1)
    print("diff:", len(blobs), "blobs; IoU", ious)


if __name__ == "__main__":
    main()
