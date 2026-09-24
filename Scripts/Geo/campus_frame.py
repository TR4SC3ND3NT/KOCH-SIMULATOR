# Shared local metric frame for all geo tools (and, through the JSON they write, Blender and UE).
# X = east, Y = north, Z = up, metres. 1 Blender unit = 1 m; UE imports at 100 uu per m.
import os

from pyproj import Transformer

# Local site data (never committed: licensed imagery, captures with people). Expected: osm.json, cop.tif, ortho/.
CAPTURE_DIR = os.environ.get("KOCH_CAPTURE_DIR", os.path.expanduser("~/site-capture"))

ORIGIN_LAT = 42.8566  # site origin near the campus bbox centre; UE world (0,0) maps here
ORIGIN_LON = 74.6790
Z_DATUM_ASL = 800.0   # Blender Z = height above sea level minus this (campus ground is ~801-811 m ASL)

# Transverse Mercator on the origin meridian, k=1: scale error < 2e-9 over the ~0.6 km site.
LOCAL_PROJ = (f"+proj=tmerc +lat_0={ORIGIN_LAT} +lon_0={ORIGIN_LON} +k=1 +x_0=0 +y_0=0 "
              "+ellps=WGS84 +units=m +no_defs")

_fwd = Transformer.from_crs("EPSG:4326", LOCAL_PROJ, always_xy=True)
_inv = Transformer.from_crs(LOCAL_PROJ, "EPSG:4326", always_xy=True)


def to_local(lon, lat):
    """lon/lat (deg, WGS84) -> local x/y (m). Accepts scalars or numpy arrays."""
    return _fwd.transform(lon, lat)


def to_lonlat(x, y):
    """local x/y (m) -> lon/lat (deg)."""
    return _inv.transform(x, y)
