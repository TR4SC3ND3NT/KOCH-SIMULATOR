# Trees of the formal garden (R1 greybox) from the Google z20 ortho: crowns = the dark canopy/shadow masses inside the
# garden's boundary hedge, split into single crowns by distance-transform peaks (trunk ~ mass centre); trees on paths/hedges/gazebos/the pergola are moved onto the nearest lawn or dropped.
# Writes Specs/SITE_Garden_Trees.json (tree elements only; SITE_Garden keeps paths, hedges, furniture).
# Run: uv run --project Scripts python Scripts/Geo/garden_trees.py [--debug OUT.png]
import argparse
import json
import math
import os

import cv2
import numpy as np
import rasterio.features
from affine import Affine
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SPECS = os.path.join(REPO, "Art", "Blender", "Specs")
ORTHO = os.path.expanduser("~/site-capture/ortho/ortho_google_z20")
OUT = os.path.join(SPECS, "SITE_Garden_Trees.json")
RES = 0.1                                  # native ortho resolution, m/px
LEAN = (0.29, 0.20)                        # Google z20 displacement per metre of height (docs/reference/campus.md)
# inside the boundary hedge, north of the pergola (the strip south of it is in Block B's shadow on the ortho)
GARDEN = [(104.3, -48.3), (151.8, -50.6), (153.3, -9.0), (104.5, -7.8)]
MIN_R, MIN_SEP = 1.1, 3.2                  # m: smallest crown radius, closest crown centres
DARK = 72.0                                # blurred brightness below which a pixel is canopy/shadow
CLEAR = 0.9                                # m: trunk clearance from path/hedge/wall centre lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--debug")
    args = ap.parse_args()
    meta = json.load(open(ORTHO + ".json"))
    X0, Y0, X1, Y1 = meta["extent_local"]
    gx0, gy0 = min(p[0] for p in GARDEN) - 5, min(p[1] for p in GARDEN) - 5
    gx1, gy1 = max(p[0] for p in GARDEN) + 5, max(p[1] for p in GARDEN) + 5
    c0, r0 = int((gx0 - X0) / RES), int((Y1 - gy1) / RES)
    c1, r1 = int((gx1 - X0) / RES), int((Y1 - gy0) / RES)
    img = cv2.imread(ORTHO + ".png")[r0:r1, c0:c1, ::-1].astype(np.float32)
    H, W = img.shape[:2]
    T = Affine(RES, 0, gx0, 0, -RES, gy1)
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    V = img.max(axis=2)
    # canopy: the dark masses (crown + its own shadow; the lawn and paving are brighter). The crown leans east/north
    # with height on this ortho while its morning shadow falls west/north-west, so the mass centre ~ the trunk.
    canopy = (cv2.GaussianBlur(V, (0, 0), 3) < DARK).astype(np.uint8)
    canopy = cv2.morphologyEx(canopy, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    canopy = cv2.morphologyEx(canopy, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    inside = rasterio.features.rasterize([(Polygon(GARDEN), 1)], out_shape=(H, W), transform=T, dtype=np.uint8)
    canopy &= inside
    dist = cv2.distanceTransform(canopy, cv2.DIST_L2, 5) * RES           # m to the crown edge
    k = int(MIN_SEP / RES) | 1
    peaks = (dist == cv2.dilate(dist, np.ones((k, k), np.float32))) & (dist >= MIN_R)
    ys, xs = np.nonzero(peaks)
    order = np.argsort(-dist[ys, xs])
    spec_g = json.load(open(os.path.join(SPECS, "SITE_Garden.json")))
    lines, blocks, roofs = [], [], []   # roofs: structures a crown must not grow through
    for e in spec_g["elements"]:
        if e["type"] in ("path", "hedge", "wall") and e.get("line"):
            lines.append(LineString(e["line"]).buffer(CLEAR + e.get("width", 0.3) / 2))
        elif e["type"] == "gazebo":
            blocks.append(Point(e["center"]).buffer(e.get("across_flats", 7.7) / 2 + 1.0))
            roofs.append(Point(e["center"]).buffer(e.get("across_flats", 7.7) / 2 + e.get("overhang", 0.8)))
        elif e["type"] == "pergola":
            blocks.append(LineString(e["line"]).buffer(e.get("width", 2.0) / 2 + 0.6))
            roofs.append(LineString(e["line"]).buffer(e.get("width", 2.0) / 2 + 0.2))
    busy = unary_union(lines + blocks)
    lawn = Polygon(GARDEN).buffer(-0.8).difference(busy)
    trees = []
    for i in order:
        r = float(dist[ys[i], xs[i]])
        cx, cy = T * (xs[i] + 0.5, ys[i] + 0.5)
        d = min(10.0, 2.0 * r)                           # crown diameter (crown + shadow mass: an upper bound)
        conifer = d < 3.4
        h = (1.8 * d + 1.0) if conifer else min(17.0, 1.2 * d + 5.0)
        tx, ty = cx, cy                                  # lean and shadow offsets roughly cancel (see above)
        p = Point(tx, ty)
        if not lawn.contains(p):
            q = lawn.boundary.interpolate(lawn.boundary.project(p)) if not lawn.is_empty else None
            if q is None or q.distance(p) > 1.5:
                continue
            tx, ty = q.x, q.y
        if any(math.hypot(tx - t["pos"][0], ty - t["pos"][1]) < MIN_SEP for t in trees):
            continue
        room = min((rf.distance(Point(tx, ty)) for rf in roofs), default=99.0)
        if d / 2 > room:          # crown would pierce a gazebo/pergola roof: narrower crown (min 2 m) or no tree
            if room < 1.0:
                continue
            d = 2.0 * room
            conifer = d < 3.4
            h = (1.8 * d + 1.0) if conifer else min(17.0, 1.2 * d + 5.0)
        trees.append({"type": "tree", "name": f"GT_{len(trees):02d}_{'conifer' if conifer else 'broadleaf'}",
                      "pos": [round(tx, 2), round(ty, 2)], "height": round(h, 1), "crown_d": round(d, 1),
                      "trunk_d": 0.18 if conifer else 0.3, "crown_base": round(0.15 * h if conifer else 0.35 * h, 1),
                      "shape": "cone" if conifer else "round", "ue_asset": "tree",
                      "evidence": "crown on the Google z20 ortho 2026 (dark green blob r %.1f m), trunk = crown centre minus "
                                  "the height lean; species class by crown size (garden videos 081856-082013: thujas, "
                                  "pines, acacias, poplars)" % r, "confidence": "low"})
    spec = {"id": "SITE_Garden_Trees", "collection": "04_Garden", "ground": "terrain",
            "note": "Trees of the formal garden (the garden spec had none inside the boundary hedge). Generated by "
                    "Scripts/Geo/garden_trees.py; regenerate after path/hedge changes.",
            "elements": trees}
    json.dump(spec, open(OUT, "w"), indent=1)
    print(f"garden trees: {len(trees)} ({sum(t['shape'] == 'cone' for t in trees)} conifers) -> {OUT}")
    if args.debug:
        dbg = img.copy()
        dbg[canopy > 0] = dbg[canopy > 0] * 0.5 + np.array([255, 255, 0]) * 0.5
        inv = ~T
        for t in trees:
            px, py = inv * tuple(t["pos"])
            cv2.circle(dbg, (int(px), int(py)), int(t["crown_d"] / 2 / RES), (255, 0, 0), 2)
        cv2.imwrite(args.debug, dbg[:, :, ::-1].astype(np.uint8))


if __name__ == "__main__":
    main()
