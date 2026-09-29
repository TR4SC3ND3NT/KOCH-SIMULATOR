# Paved vs lawn ground cover of the campus from the Google z20 ortho (R1 greybox): writes the "ground_surfaces" rings of
# Specs/SITE_00_GroundCover.json (paving rings, then lawn islands inside them; the terrain is lawn by default). The file
# sorts before the other SITE_* specs, so their hand-traced surfaces win where they overlap.
# Pixels: vegetation = excess green 2G-R-B > EXG_T; shadows (V < DARK_T), building roofs (footprint swept by the
# ortho's height lean) and modelled tree crowns are unknown and take the class of the nearest known pixel.
# Run: uv run --project Scripts python Scripts/Geo/ground_cover.py [--debug OUT.png]
import argparse
import glob
import json
import math
import os

import cv2
import numpy as np
import rasterio.features
from affine import Affine
from shapely.geometry import Polygon, shape

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SPECS = os.path.join(REPO, "Art", "Blender", "Specs")
ORTHO = os.path.expanduser("~/site-capture/ortho/ortho_google_z20")
OUT = os.path.join(SPECS, "SITE_00_GroundCover.json")
RES = 0.2                  # working resolution, m/px
EXG_T, DARK_T = 5.0, 70.0  # excess-green threshold (0..255 units), shadow brightness threshold
MEDIAN_PX = 7              # label median filter (1.4 m) against speckle between tree shadows and paving joints
LEAN = (0.29, 0.20)        # Google z20 roof displacement per metre of height (x east, y north); docs/reference/campus.md
MIN_LAWN, MIN_PAVE = 4.0, 3.0   # m2: smaller islands are merged into the surrounding class
PAVE_SLOT, LAWN_SLOT = "M_Paver_Clover_Grey", "M_Ground_Grass"
# garden inside its boundary hedge (SITE_Garden: lawns + path/hedge objects; tree shadows make the ortho unreliable)
LAWN_ONLY = [[(104.0, -56.5), (151.5, -58.5), (153.5, -9.0), (104.5, -7.5)],
             # measured 7-sided garden outline (zone_garden.py v2), 0.1 m outside the boundary hedge
             [(100.5, -9.73), (158.39, -13.66), (156.99, -39.03), (153.55, -44.69), (150.4, -46.76), (103.02, -45.08),
              (98.7, -36.9)]]
# construction yard east of Block D (bare earth and rubble on the 2026 ortho): its own dirt ring, not paving
DIRT = [[(1.0, 21.0), (50.0, 23.5), (49.0, 80.0), (0.0, 77.0)]]
DIRT_SLOT = "M_Ground_Dirt"


def world_ring(spec):
    a = spec["anchor"]
    ox, oy = a["world_xy"]
    dx, dy = a["x_dir"]
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    k = float(spec.get("scale", 1.0))
    ring = spec["ring"]
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    pts = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in ring]
    return [(ox + dx * x - dy * y, oy + dy * x + dx * y) for x, y in pts]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--debug")
    args = ap.parse_args()
    meta = json.load(open(ORTHO + ".json"))
    X0, Y0, X1, Y1 = meta["extent_local"]
    img = cv2.imread(ORTHO + ".png")[:, :, ::-1]
    f = meta["m_per_px"] / RES
    img = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_AREA).astype(np.float32)
    H, W = img.shape[:2]
    T = Affine(RES, 0, X0, 0, -RES, Y1)          # pixel -> local metres (row 0 = north edge)

    def burn(geoms, value=1):
        return rasterio.features.rasterize([(g, value) for g in geoms], out_shape=(H, W), transform=T, fill=0,
                                           dtype=np.uint8)

    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    exg = 2 * G - R - B
    V = img.max(axis=2)
    label = np.where(exg > EXG_T, 2, 1).astype(np.uint8)       # 1 paved, 2 lawn, 0 unknown
    label[(V < DARK_T) | ((V < 1.4 * DARK_T) & (B > G))] = 0     # shadows (dark, blue-cast)
    # buildings: footprint + the leaned roof (swept over the building height) hide the ground
    occl = []
    for fn in sorted(glob.glob(os.path.join(SPECS, "BLD_*.json"))):
        s = json.load(open(fn))
        ring = world_ring(s)
        h = s.get("eave_z", 6.0) + 3.0
        fp = Polygon(ring)
        sweep = [fp] + [Polygon([(x + LEAN[0] * h * t, y + LEAN[1] * h * t) for x, y in ring]) for t in (0.25, 0.5, 0.75, 1.0)]
        occl += [g.buffer(0.5) for g in sweep]
    for it in json.load(open(os.path.join(REPO, "Art", "Blender", "Data", "footprints.json")))["items"]:
        r = it.get("ring")
        if r and it.get("group") not in ("Context", "Sport") and len(r) >= 3:
            h = 3.3 * it.get("storeys", 1) + 3.0
            occl += [Polygon([(x + LEAN[0] * h * t, y + LEAN[1] * h * t) for x, y in r]).buffer(0.5) for t in (0, 0.5, 1.0)]
    bmask = burn(occl)
    # modelled tree crowns (their canopy hides what is under them)
    crowns = []
    for fn in glob.glob(os.path.join(SPECS, "SITE_*.json")):
        for e in json.load(open(fn)).get("elements", []):
            if e.get("type") == "tree" and isinstance(e.get("pos"), list) and len(e["pos"]) == 2:
                d = e.get("crown_d", 3.0)
                crowns.append(Polygon([(e["pos"][0] + d / 2 * math.cos(a), e["pos"][1] + d / 2 * math.sin(a))
                                       for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]))
    if crowns:
        label[burn(crowns) > 0] = 0
    label[bmask > 0] = 0
    # unknown pixels take the class of the nearest known pixel
    unknown = (label == 0).astype(np.uint8)
    _, lab = cv2.distanceTransformWithLabels(unknown, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    known_vals = label[label > 0]            # zero pixels of `unknown` in row-major order = label indices 1..n
    label = known_vals[lab - 1].reshape(H, W).astype(np.uint8)
    # clean-up: median, close/open the lawn mask (0.6 m), then merge small islands
    label = cv2.medianBlur(label, MEDIAN_PX)
    lawn = (label == 2).astype(np.uint8)
    lawn[burn([Polygon(r) for r in LAWN_ONLY]) > 0] = 1   # zones modelled as lawn + path objects: no paving rings
    k = np.ones((3, 3), np.uint8)
    lawn = cv2.morphologyEx(cv2.morphologyEx(lawn, cv2.MORPH_CLOSE, k), cv2.MORPH_OPEN, k)
    for val, amin in ((1, MIN_LAWN), (0, MIN_PAVE)):    # small lawn blobs -> paved, small paved blobs -> lawn
        m = (lawn == val).astype(np.uint8)
        n, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
        small = np.isin(cc, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] * RES * RES < amin])
        lawn[small] = 1 - val
    site = json.load(open(os.path.join(REPO, "Art", "Blender", "Data", "site_osm.json")))
    campus = Polygon(site["campus_boundary"])
    inside = burn([campus]) > 0
    paved = ((lawn == 0) & inside).astype(np.uint8)
    rings, islands = [], []
    for geom, v in rasterio.features.shapes(paved, mask=paved > 0, transform=T, connectivity=4):
        poly = shape(geom).simplify(0.3, preserve_topology=True)
        if poly.area < MIN_PAVE:
            continue
        rings.append([[round(x, 2), round(y, 2)] for x, y in list(poly.exterior.coords)[:-1]])
        for hole in poly.interiors:
            hp = Polygon(hole)
            if hp.area >= MIN_LAWN:
                islands.append([[round(x, 2), round(y, 2)] for x, y in list(hole.coords)[:-1]])
    ev = ("Google z20 ortho 2026 classified by excess green (2G-R-B > %.0f), shadows/roofs/tree crowns filled from the "
          "nearest visible ground; generated by Scripts/Geo/ground_cover.py" % EXG_T)
    surfaces = [{"name": f"Paved_{i:03d}", "ring": r, "slot": PAVE_SLOT, "evidence": ev} for i, r in enumerate(rings)]
    surfaces += [{"name": f"Lawn_{i:03d}", "ring": r, "slot": LAWN_SLOT, "evidence": ev} for i, r in enumerate(islands)]
    surfaces += [{"name": f"Dirt_{i:02d}", "ring": [list(p) for p in r], "slot": DIRT_SLOT,
                  "evidence": "construction yard: bare earth and rubble (Google z20 ortho 2026)"} for i, r in enumerate(DIRT)]
    spec = {"id": "SITE_00_GroundCover", "collection": "03_Site", "elements": [],
            "note": "Ground cover only (no objects): paved rings + lawn islands over the default lawn terrain. Generated, do not "
                    "edit by hand; hand-traced ground_surfaces of the other SITE_* specs are applied after these and win.",
            "ground_surfaces": surfaces}
    json.dump(spec, open(OUT, "w"), indent=1)
    pa = sum(Polygon(r).area for r in rings) - sum(Polygon(r).area for r in islands)
    print(f"ground cover: {len(rings)} paved rings, {len(islands)} lawn islands, paved {pa:.0f} m2 of the campus "
          f"{campus.area:.0f} m2 -> {OUT}")
    if args.debug:
        dbg = img.copy()
        dbg[(paved > 0)] = dbg[(paved > 0)] * 0.4 + np.array([255, 60, 60]) * 0.6
        dbg[(lawn > 0) & inside] = dbg[(lawn > 0) & inside] * 0.5 + np.array([40, 255, 40]) * 0.5
        cv2.imwrite(args.debug, dbg[:, :, ::-1].astype(np.uint8))


if __name__ == "__main__":
    main()
