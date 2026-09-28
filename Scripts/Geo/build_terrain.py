# Fits the bare-earth base surface of the site from Copernicus GLO-30 (buildings/trees masked) and writes the
# terrain + street spec for the Blender greybox builder: Art/Blender/Data/terrain.json (local frame, metres).
# Run: uv run --project Scripts python Scripts/Geo/build_terrain.py
# GLO-30 (c) DLR/Airbus, Copernicus programme; free incl. commercial use with attribution.
# FABDEM is only an optional cross-check (CC BY-NC-SA): pass --fabdem <tif> to print its fit next to ours.
import argparse
import json
import os

import numpy as np
import rasterio
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep

from campus_frame import CAPTURE_DIR, LOCAL_PROJ, Z_DATUM_ASL, to_local, to_lonlat

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(REPO, "Art", "Blender", "Data")
DEM = os.path.join(CAPTURE_DIR, "cop.tif")
FIT_EXTENT = (-420.0, -230.0, 320.0, 240.0)  # wider than the build grid so the quadratic is not edge-driven
GRID = {"extent": [-340.0, -150.0, 240.0, 160.0], "spacing_m": 1.0}
MASK_BUFFER_M = 18.0  # 30 m posts average ~30x30 m: drop posts whose cell touches a building or wood

# Carriageway widths (m) per OSM class/lanes: 3.5 m lanes + 0.5 m gutters (SP 42.13330 Table 11.2a).
LANE_W, GUTTER_W = 3.5, 0.5
SERVICE_W = {"service": 5.0, "residential": 6.0, "tertiary": 8.0}
CURB_REVEAL_M = 0.15
PAD_INFLUENCE_M = 30.0   # terrain_field screening: pad corrections fade back to the DEM over ~30 m (2026-09-28)
# Measured corrections per OSM street: (dx, dy) shift of the centreline (m) and carriageway width (m).
STREET_FIX = {
    # Curbs at the zebra in front of the gate: north y=-110.8, south y=-125.6 at x=153 (Google z20, 2026-09-24)
    # -> centre -118.2 vs OSM -119.15, width 14.8 m.
    "way/187959018": {"shift": (0.0, 0.95), "width_m": 14.8},
}


def carriageway_rings(streets, extent, inset=0.02):
    """Union of the carriageways (centreline buffered by half the width, round caps = the builders' distance test)
    clipped to the grid: [{"ring": [[x, y], ...], "hole": bool}]. TER_Ground conforms to these rings so every curb
    is a vertical 0.15 m breakline instead of a reveal smeared over one grid cell (2026-09-28 terrain audit)."""
    geo = unary_union([LineString(s["centerline"]).buffer(s["width_m"] / 2, quad_segs=8) for s in streets])
    x0, y0, x1, y1 = extent
    geo = geo.intersection(box(x0 + inset, y0 + inset, x1 - inset, y1 - inset)).simplify(0.02)
    polys = [geo] if geo.geom_type == "Polygon" else [g for g in getattr(geo, "geoms", []) if g.geom_type == "Polygon"]
    out = []
    for pg in polys:
        out.append({"ring": [[round(x, 3), round(y, 3)] for x, y in list(pg.exterior.coords)[:-1]], "hole": False})
        for h in pg.interiors:
            out.append({"ring": [[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]], "hole": True})
    return out


def dem_posts(path, extent):
    """All DEM post centres inside the local extent -> (x, y, z_local)."""
    with rasterio.open(path) as r:
        x0, y0, x1, y1 = extent
        lons, lats = to_lonlat(np.array([x0, x1, x0, x1]), np.array([y0, y0, y1, y1]))
        win = rasterio.windows.from_bounds(min(lons), min(lats), max(lons), max(lats), r.transform).round_offsets().round_lengths()
        z = r.read(1, window=win).astype(np.float64)
        tr = r.window_transform(win)
    rows, cols = np.mgrid[0:z.shape[0], 0:z.shape[1]]
    lon, lat = rasterio.transform.xy(tr, rows.ravel(), cols.ravel(), offset="center")
    x, y = to_local(np.asarray(lon), np.asarray(lat))
    keep = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
    return x[keep], y[keep], z.ravel()[keep] - Z_DATUM_ASL


def robust_quadratic(x, y, z, iters=12, c=2.5):
    """Tukey-biweight IRLS fit of z = c0 + cx x + cy y + cxx x^2 + cxy xy + cyy y^2 (x, y in hectometres)."""
    X, Y = x / 100.0, y / 100.0
    A = np.column_stack([np.ones_like(X), X, Y, X * X, X * Y, Y * Y])
    w = np.ones_like(z)
    for _ in range(iters):
        coef, *_ = np.linalg.lstsq(A * w[:, None], z * w, rcond=None)
        res = z - A @ coef
        s = 1.4826 * np.median(np.abs(res)) + 1e-6
        u = res / (c * s)
        w = np.where(np.abs(u) < 1, (1 - u * u) ** 2, 0.0)
    rms = float(np.sqrt(np.sum(w * res * res) / max(np.sum(w), 1)))
    return coef, rms, int(np.sum(w > 0))


def road_width(tags):
    hw = tags.get("highway")
    if hw in ("primary", "secondary", "primary_link", "trunk"):
        lanes = int(tags.get("lanes", "2"))
        return lanes * LANE_W + 2 * GUTTER_W
    return SERVICE_W.get(hw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fabdem", help="optional FABDEM tile for a cross-check fit (non-commercial licence)")
    ap.add_argument("--rings-only", action="store_true", help="only recompute carriageway_rings of terrain.json")
    a = ap.parse_args()
    if a.rings_only:
        path = os.path.join(DATA, "terrain.json")
        t = json.load(open(path))
        t["carriageway_rings"] = carriageway_rings(t["streets"], t["grid"]["extent"])
        json.dump(t, open(path, "w"), indent=1)
        print("carriageway_rings:", len(t["carriageway_rings"]), "rings,", sum(len(r["ring"]) for r in t["carriageway_rings"]), "vertices")
        return

    site = json.load(open(os.path.join(DATA, "site_osm.json"), encoding="utf-8"))
    fp_path = os.path.join(DATA, "footprints.json")
    rings = [f["ring"] for f in site["features"] if f["kind"] == "building" and "ring" in f]
    if os.path.exists(fp_path):
        rings += [it["ring"] for it in json.load(open(fp_path))["items"]]
    rings += [f["ring"] for f in site["features"] if f["kind"] == "natural" and "ring" in f]
    mask = prep(unary_union([Polygon(r).buffer(MASK_BUFFER_M) for r in rings if len(r) >= 3]))

    def fit(path):
        x, y, z = dem_posts(path, FIT_EXTENT)
        free = np.array([not mask.contains(Point(px, py)) for px, py in zip(x, y)])
        coef, rms, n = robust_quadratic(x[free], y[free], z[free])
        return coef, rms, n, int(free.sum()), len(x)

    coef, rms, n_in, n_free, n_all = fit(DEM)
    print(f"GLO-30: posts {n_all}, unmasked {n_free}, inliers {n_in}, rms {rms:.2f} m")
    print("  z0 %.2f m (ASL %.2f), slope east %.2f %%, north %.2f %%" % (coef[0], coef[0] + Z_DATUM_ASL, coef[1], coef[2]))
    if a.fabdem:
        fc, frms, fn, _, _ = fit(a.fabdem)
        print("FABDEM check: z0 %.2f, east %.2f %%, north %.2f %%, rms %.2f" % (fc[0], fc[1], fc[2], frms))

    streets = []
    for f in site["features"]:
        if f["kind"] != "highway" or "line" not in f:
            continue
        w = road_width(f["tags"])
        if not w:
            continue
        line = f["line"]
        fix = STREET_FIX.get(f["osm"])
        if fix:
            dx, dy = fix["shift"]
            line = [[round(x + dx, 3), round(y + dy, 3)] for x, y in line]
            w = fix.get("width_m", w)
        streets.append({"osm": f["osm"], "class": f["tags"]["highway"], "lanes": f["tags"].get("lanes"),
                        "width_m": w, "centerline": line, "corrected": bool(fix)})

    out = {"frame": {"proj": LOCAL_PROJ, "z_datum_asl": Z_DATUM_ASL},
           "source": "Copernicus GLO-30 DSM, posts within %.0f m of buildings/wood masked, Tukey IRLS quadratic" % MASK_BUFFER_M,
           "base": {"model": "quadratic_hm", "note": "z = c0 + cx*X + cy*Y + cxx*X^2 + cxy*X*Y + cyy*Y^2, X/Y in hectometres",
                    "coef": [round(float(c), 4) for c in coef], "rms_m": round(rms, 2), "inliers": n_in},
           "grid": GRID,
           "curb_reveal_m": CURB_REVEAL_M,
           "pad_influence_m": PAD_INFLUENCE_M,
           "streets": streets,
           "carriageway_rings": carriageway_rings(streets, GRID["extent"])}
    with open(os.path.join(DATA, "terrain.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote terrain.json,", len(streets), "street centrelines")


if __name__ == "__main__":
    main()
