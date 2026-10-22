# Automatic photo camera refine for the R1 photo-vs-model bug hunt: render-and-compare of the greybox class map
# (Scripts/Geo/model_raycast.py) against the photo's semantic map (Scripts/Geo/photo_seg.py), maximising the mean IoU
# of coarse groups (sky / building / vegetation / grass / ground) over pose + focal, coarse to fine.
# Idea: silhouette / semantic alignment as in LoD-Loc v2 (arXiv 2507.00659; idea only, its code has no licence) and
# MeshLoc's finding that raw greybox renders are poor for feature matching (ECCV 2022) - so we align regions, not features.
# The camera height is kept 1.1-2.0 m above the model ground under it (hand-held phone).
# Run: python Scripts/Geo/camera_refine.py MODEL.npz PHOTO.jpg SEG_cls.png --look PX PY PZ TX TY TZ [--f35 24]
#        --out PREFIX            (or --cam start.json)
# Writes PREFIX_cam.json (photo_pnp.py format at the photo's full resolution, + "miou") and PREFIX_overlay.jpg.
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageOps
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_raycast import Model, edges   # noqa: E402

PHOTO_CLASSES = ["unknown", "grass", "soil", "paving", "road", "kerb", "stairs", "wall", "roof", "window", "door",
                 "vegetation", "metal", "sign", "water", "other", "sky", "person", "vehicle"]   # photo_seg.CLASS_LIST
GROUP = {"sky": 0, "wall": 1, "window": 1, "door": 1, "roof": 1, "sign": 1, "vegetation": 2, "grass": 3, "soil": 3,
         "paving": 4, "road": 4, "kerb": 4, "stairs": 4}   # others: ignored (people, cars, metal, props, unknown)
NG = 5
DIAG_35MM = 43.27


def rot(yaw, pitch, roll):
    """World->camera R (OpenCV) for a camera looking along yaw (deg from +x, CCW), pitch (deg up), roll (deg)."""
    y, p, r = map(math.radians, (yaw, pitch, roll))
    d = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)])
    rgt = np.cross(d, [0, 0, 1.0])
    rgt /= np.linalg.norm(rgt)
    dn = np.cross(d, rgt)
    c, s = math.cos(r), math.sin(r)
    rgt, dn = c * rgt + s * dn, -s * rgt + c * dn
    return np.vstack([rgt, dn, d])


class Refiner:
    def __init__(self, model, seg_path, photo_size):
        self.m = model
        seg = np.asarray(Image.open(seg_path))
        lut = np.full(256, -1, np.int16)
        for i, c in enumerate(PHOTO_CLASSES):
            lut[i] = GROUP.get(c, -1)
        self.seg_full = lut[seg]
        self.W, self.H = photo_size
        mcls = list(model.classes)
        self.mlut = np.array([GROUP.get(c, -1) for c in mcls] + [0], np.int16)   # index -1 (no hit) -> sky

    def seg_at(self, w, h):
        return np.asarray(Image.fromarray(self.seg_full.astype(np.int16) + 1).resize((w, h), Image.NEAREST),
                          np.int16) - 1

    def score(self, x, w, h, seg):
        px, py, pz, yaw, pitch, roll, f = x
        K = np.array([[f * w, 0, w / 2], [0, f * w, h / 2], [0, 0, 1]])   # f in units of image width
        R = rot(yaw, pitch, roll)
        Rt = np.hstack([R, (-R @ np.array([px, py, pz])).reshape(3, 1)])
        r = self.m.cast(K, Rt, w, h)
        mg = self.mlut[r["cls"]]
        mg[~r["hit"]] = 0
        valid = seg >= 0
        ious = []
        for g in range(NG):
            a, b = (seg == g) & valid, (mg == g) & valid
            u = (a | b).sum()
            if a.sum() > 0.002 * valid.sum():   # groups the photo actually shows
                ious.append((a & b).sum() / max(u, 1))
        return float(np.mean(ious)) if ious else 0.0, r


def ground_z(m, x, y, z_from):
    """Walkable model surface under (x, y), cast down from z_from (just above the phone): hits on rails, crowns, roofs
    and props are stepped through (a handrail under the rough xy once put the camera 1.5 m too high)."""
    K = np.array([[1, 0, 0.5], [0, 1, 0.5], [0, 0, 1.0]])
    R = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1.0]])   # looking straight down
    walk = {i for i, c in enumerate(m.classes) if str(c) in ("grass", "soil", "paving", "road", "kerb", "stairs", "terrain_other")}
    z = z_from
    for _ in range(8):
        Rt = np.hstack([R, (-R @ np.array([x, y, z])).reshape(3, 1)])
        r = m.cast(K, Rt, 1, 1)
        if not r["hit"][0, 0]:
            return None
        if int(r["cls"][0, 0]) in walk:
            return float(r["xyz"][0, 0, 2])
        z = float(r["xyz"][0, 0, 2]) - 0.01
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("photo")
    ap.add_argument("seg")
    ap.add_argument("--look", type=float, nargs=6)
    ap.add_argument("--cam")
    ap.add_argument("--f35", type=float, default=24.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--search", type=float, default=1.0, help="scale of the coarse multi-start (1 = +-2.5 m, +-12 deg)")
    a = ap.parse_args()
    ph = ImageOps.exif_transpose(Image.open(a.photo)).convert("RGB")
    W, H = ph.size
    m = Model(a.model)
    ref = Refiner(m, a.seg, (W, H))
    f0 = a.f35 * math.hypot(W, H) / DIAG_35MM / W
    if a.cam:
        c = json.load(open(a.cam))["cameras"][0]
        R = np.array(c["R"])
        C = np.array(c["center"])
        d = R[2]
        yaw, pitch = math.degrees(math.atan2(d[1], d[0])), math.degrees(math.asin(np.clip(d[2], -1, 1)))
        x0 = [*C, yaw, pitch, 0.0, c["f"] / c["w"]]
    else:
        px, py, pz, tx, ty, tz = a.look
        d = np.array([tx - px, ty - py, tz - pz])
        x0 = [px, py, pz, math.degrees(math.atan2(d[1], d[0])), math.degrees(math.atan2(d[2], math.hypot(d[0], d[1]))),
              0.0, f0]
    gz = ground_z(m, x0[0], x0[1], x0[2] + 1.0)
    if gz is not None:
        x0[2] = min(max(x0[2], gz + 1.1), gz + 2.0)
    zlo, zhi = (gz + 1.1, gz + 2.0) if gz is not None else (x0[2] - 1, x0[2] + 1)
    # 1. coarse multi-start at 96 px wide
    w, h = 96, round(96 * H / W)
    seg = ref.seg_at(w, h)
    s = a.search
    best = (ref.score(x0, w, h, seg)[0], list(x0))
    for dx in (-2.5 * s, 0, 2.5 * s):
        for dy in (-2.5 * s, 0, 2.5 * s):
            for dyaw in (-12 * s, -6 * s, 0, 6 * s, 12 * s):
                for dp in (-4.0, 0.0, 4.0):
                    x = [x0[0] + dx, x0[1] + dy, x0[2], x0[3] + dyaw, x0[4] + dp, 0.0, x0[6]]
                    sc = ref.score(x, w, h, seg)[0]
                    if sc > best[0]:
                        best = (sc, x)
    x = best[1]
    # 2. Powell refine, coarse to fine
    bounds = [(x0[0] - 6 * s, x0[0] + 6 * s), (x0[1] - 6 * s, x0[1] + 6 * s), (zlo, zhi), (x0[3] - 30 * s, x0[3] + 30 * s),
              (-35, 35), (-8, 8), (0.6 * f0, 1.4 * f0)]
    for w in (128, 256, 448):
        h = round(w * H / W)
        seg = ref.seg_at(w, h)
        res = minimize(lambda v: -ref.score(v, w, h, seg)[0], x, method="Powell", bounds=bounds,
                       options={"xtol": 1e-3, "ftol": 1e-4, "maxfev": 600})
        x = list(res.x)
    w, h = 768, round(768 * H / W)
    sc, r = ref.score(x, w, h, ref.seg_at(w, h))
    px, py, pz, yaw, pitch, roll, f = x
    R = rot(yaw, pitch, roll)
    C = np.array([px, py, pz])
    cam = {"name": os.path.basename(a.photo), "image": a.photo, "w": W, "h": H, "f": f * W, "fy": f * W,
           "cx": W / 2, "cy": H / 2, "R": R.tolist(), "t": (-R @ C).tolist(), "center": C.tolist(), "miou": sc,
           "yaw_pitch_roll": [yaw, pitch, roll], "f35": f * W * DIAG_35MM / math.hypot(W, H),
           "ground_z": gz, "method": "camera_refine semantic mIoU"}
    json.dump({"zone": cam["name"], "cameras": [cam], "points": []}, open(a.out + "_cam.json", "w"), indent=1)
    small = np.asarray(ph.resize((w, h), Image.BICUBIC)).copy()
    small[edges(r)] = (255, 0, 255)
    Image.fromarray(small).save(a.out + "_overlay.jpg", quality=88)
    print(f"refine: miou {best[0]:.3f} (coarse) -> {sc:.3f}; camera {C.round(2)} yaw {yaw:.1f} pitch {pitch:.1f} "
          f"roll {roll:.1f} f35 {cam['f35']:.1f}")


if __name__ == "__main__":
    main()
