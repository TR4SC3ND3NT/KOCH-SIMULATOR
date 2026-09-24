# Downloads XYZ satellite tiles and resamples them into a north-up orthophoto in the local campus frame.
# Output is a LOCAL tracing reference only (licensed imagery: never commit, never ship).
# Run: uv run --project Scripts python Scripts/Geo/fetch_ortho.py --source esri --zoom 19
import argparse
import io
import json
import math
import os
import time
import urllib.request

import numpy as np
from PIL import Image

from campus_frame import CAPTURE_DIR, to_lonlat

SOURCES = {
    # Esri World Imagery (current mosaic). Esri permits tracing for OSM; attribution required.
    "esri": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    # Esri Wayback archive: pass --release <id> (list: https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json)
    "wayback": "https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/{release}/{z}/{y}/{x}",
    # Bing aerial (quadkey addressing).
    "bing": "https://ecn.t{s}.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1",
}
TILE = 256
UA = "KochSimulator-greybox/0.1 (local tracing reference)"


def lonlat_to_gpx(lon, lat, z):
    """lon/lat -> global Web Mercator pixel coords at zoom z (float, numpy-friendly)."""
    n = TILE * 2 ** z
    lat_r = np.radians(lat)
    return (lon + 180.0) / 360.0 * n, (1.0 - np.arcsinh(np.tan(lat_r)) / math.pi) / 2.0 * n


def quadkey(x, y, z):
    q = ""
    for i in range(z, 0, -1):
        d, m = 0, 1 << (i - 1)
        d += 1 if x & m else 0
        d += 2 if y & m else 0
        q += str(d)
    return q


def fetch_tile(src, x, y, z, release, cache):
    path = os.path.join(cache, f"{z}_{x}_{y}.img")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    url = SOURCES[src].format(z=z, x=x, y=y, release=release, s=(x + y) % 4, q=quadkey(x, y, z))
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                data = r.read()
            break
        except Exception:  # transient network errors: back off and retry
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    with open(path, "wb") as f:
        f.write(data)
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=SOURCES, default="esri")
    ap.add_argument("--release", default="", help="Wayback release id")
    ap.add_argument("--zoom", type=int, default=19)
    ap.add_argument("--bbox", type=float, nargs=4, default=[-340.0, -150.0, 240.0, 160.0],
                    metavar=("X0", "Y0", "X1", "Y1"), help="local metres")
    ap.add_argument("--res", type=float, default=0.25, help="output metres per pixel")
    ap.add_argument("--out", default=os.path.join(CAPTURE_DIR, "ortho"))
    a = ap.parse_args()

    tag = a.source + (f"_{a.release}" if a.release else "")
    cache = os.path.join(a.out, "tiles", tag)
    os.makedirs(cache, exist_ok=True)

    x0, y0, x1, y1 = a.bbox
    lons, lats = to_lonlat(np.array([x0, x1, x0, x1]), np.array([y0, y0, y1, y1]))
    gx, gy = lonlat_to_gpx(np.asarray(lons), np.asarray(lats), a.zoom)
    tx0, tx1 = int(gx.min() // TILE), int(gx.max() // TILE)
    ty0, ty1 = int(gy.min() // TILE), int(gy.max() // TILE)

    mosaic = np.zeros(((ty1 - ty0 + 1) * TILE, (tx1 - tx0 + 1) * TILE, 3), np.uint8)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            img = Image.open(io.BytesIO(fetch_tile(a.source, tx, ty, a.zoom, a.release, cache))).convert("RGB")
            mosaic[(ty - ty0) * TILE:(ty - ty0 + 1) * TILE, (tx - tx0) * TILE:(tx - tx0 + 1) * TILE] = np.asarray(img)

    # Resample onto the local grid (pixel centres), bilinear.
    w, h = int(round((x1 - x0) / a.res)), int(round((y1 - y0) / a.res))
    xs = x0 + (np.arange(w) + 0.5) * a.res
    ys = y1 - (np.arange(h) + 0.5) * a.res  # row 0 = north
    X, Y = np.meshgrid(xs, ys)
    lon, lat = to_lonlat(X, Y)
    px, py = lonlat_to_gpx(np.asarray(lon), np.asarray(lat), a.zoom)
    px, py = px - tx0 * TILE - 0.5, py - ty0 * TILE - 0.5
    ix, iy = np.clip(np.floor(px).astype(int), 0, mosaic.shape[1] - 2), np.clip(np.floor(py).astype(int), 0, mosaic.shape[0] - 2)
    fx, fy = (px - ix)[..., None], (py - iy)[..., None]
    m = mosaic.astype(np.float32)
    out = (m[iy, ix] * (1 - fx) * (1 - fy) + m[iy, ix + 1] * fx * (1 - fy)
           + m[iy + 1, ix] * (1 - fx) * fy + m[iy + 1, ix + 1] * fx * fy)

    name = f"ortho_{tag}_z{a.zoom}"
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(a.out, name + ".png"))
    meta = {"source": a.source, "release": a.release, "zoom": a.zoom, "extent_local": [x0, y0, x1, y1],
            "m_per_px": a.res, "size_px": [w, h], "fetched": time.strftime("%Y-%m-%d"),
            "note": "local tracing reference only; imagery (c) provider, do not commit or ship"}
    with open(os.path.join(a.out, name + ".json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("wrote", os.path.join(a.out, name + ".png"), w, "x", h)


if __name__ == "__main__":
    main()
