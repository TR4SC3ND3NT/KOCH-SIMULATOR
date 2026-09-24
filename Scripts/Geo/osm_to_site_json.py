# Converts the local OSM extract (Overpass JSON) into metric site data for the Blender greybox builder.
# Output: Art/Blender/Data/site_osm.json (local frame from campus_frame.py). Real names/addresses are dropped.
# Run: uv run --project Scripts python Scripts/Geo/osm_to_site_json.py
# Map data (c) OpenStreetMap contributors, ODbL.
import json
import os

import numpy as np
from shapely.geometry import LineString, Polygon, box, mapping
from shapely.validation import make_valid

from campus_frame import CAPTURE_DIR, LOCAL_PROJ, ORIGIN_LAT, ORIGIN_LON, Z_DATUM_ASL, to_local

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(CAPTURE_DIR, "osm.json")  # Overpass JSON with geometry
OUT = os.path.join(REPO, "Art", "Blender", "Data", "site_osm.json")
EXTENT = (-340.0, -150.0, 240.0, 160.0)  # local metres: campus + street + one block of surroundings
CAMPUS_WAY = 341105734  # the campus boundary polygon

KEEP_TAGS = {"building", "building:levels", "building:levels:underground", "roof:shape", "roof:levels", "height",
             "layer", "highway", "lanes", "width", "surface", "oneway", "service", "footway", "crossing",
             "leisure", "sport", "barrier", "landuse", "natural", "amenity", "man_made", "area", "access"}


def kind(tags):
    for k in ("building", "highway", "barrier", "leisure", "landuse", "natural", "amenity", "man_made"):
        if k in tags:
            return k
    return None


def main():
    els = json.load(open(SRC, encoding="utf-8"))["elements"]
    clip = box(*EXTENT)
    feats = []
    campus = None
    for e in els:
        if e["type"] != "way" or "geometry" not in e:
            continue
        tags = e.get("tags", {})
        k = kind(tags)
        if not k and e["id"] != CAMPUS_WAY:
            continue
        lon = np.array([p["lon"] for p in e["geometry"]])
        lat = np.array([p["lat"] for p in e["geometry"]])
        x, y = to_local(lon, lat)
        pts = list(zip(np.round(x, 3), np.round(y, 3)))
        closed = e["nodes"][0] == e["nodes"][-1] and len(pts) >= 4
        is_area = closed and (k in ("building", "leisure", "landuse", "natural", "amenity", "man_made")
                              or tags.get("area") == "yes" or e["id"] == CAMPUS_WAY)
        geom = make_valid(Polygon(pts)) if is_area else LineString(pts)
        if not geom.intersects(clip):
            continue
        if e["id"] == CAMPUS_WAY:
            campus = geom
            continue
        feats.append({"osm": f"way/{e['id']}", "kind": k, "geom": geom,
                      "tags": {t: v for t, v in tags.items() if t in KEEP_TAGS}})

    out = {"frame": {"proj": LOCAL_PROJ, "origin_lat": ORIGIN_LAT, "origin_lon": ORIGIN_LON,
                     "z_datum_asl": Z_DATUM_ASL, "units": "m", "axes": "X east, Y north, Z up"},
           "attribution": "(c) OpenStreetMap contributors, ODbL",
           "extent": EXTENT,
           "campus_boundary": [list(c) for c in campus.exterior.coords],
           "features": []}
    for f in feats:
        g = f["geom"]
        rec = {"osm": f["osm"], "kind": f["kind"], "tags": f["tags"],
               "in_campus": bool(g.representative_point().within(campus)) if g.geom_type != "LineString"
               else bool(g.intersection(campus).length > 0.5 * g.length)}
        if g.geom_type == "LineString":
            rec["line"] = [list(c) for c in g.coords]
        else:
            poly = max(getattr(g, "geoms", [g]), key=lambda p: p.area) if g.geom_type != "Polygon" else g
            if poly.exterior.is_ccw is False:  # normalise winding: CCW outer ring (Blender face normal up)
                poly = Polygon(list(poly.exterior.coords)[::-1], [list(r.coords) for r in poly.interiors])
            rec["ring"] = [list(c) for c in poly.exterior.coords][:-1]
            rec["holes"] = [[list(c) for c in r.coords][:-1] for r in poly.interiors]
            rec["area_m2"] = round(poly.area, 1)
        out["features"].append(rec)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=0)
    n = sum(1 for f in out["features"] if f["kind"] == "building")
    print(f"wrote {OUT}: {len(out['features'])} features, {n} buildings, "
          f"{sum(1 for f in out['features'] if f['kind'] == 'building' and f['in_campus'])} in campus")


if __name__ == "__main__":
    main()
