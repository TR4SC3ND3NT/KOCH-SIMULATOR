# Every tree of the formal garden (R1, SITE_Garden_Trees.json), read by hand off the Google z20 ortho (2026) at 30 px/m
# per bed: crowns + their shadows (sun from the SSE on this ortho, so a trunk stands at the SSE end of its shadow),
# species from the garden videos 081856-082013 (tall pinnate-leaf locusts/acacias over the paths, poplars, spruces, clipped
# thujas along the hedges, young trees on the east lawns). Trunks are pushed onto the lawn >= CLEAR m from any hedge face,
# path or edging; crowns are narrowed so they stay off the gazebo roofs. Replaces the automatic ortho_trees.py garden list.
# Run: uv run --project Scripts python Scripts/Geo/zones/garden_trees.py   (after zone_garden.py)
import json
import math
import os

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

SPECS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs")
CLEAR = 0.45                  # m: trunk to the nearest hedge face / path edge
EV = ("hand-read crown/shadow on Google z20 (2026), 30 px/m, per bed (garden_trees.py); species class from garden "
      "videos 081856-082013")
# kind: (height, crown_d, trunk_d, crown_base, shape)
KIND = {"locust": (13.0, 6.0, 0.35, 4.0, "round"), "broadleaf": (10.0, 4.5, 0.28, 3.0, "round"),
        "poplar": (18.0, 3.2, 0.45, 5.0, "cone"), "spruce": (8.5, 3.2, 0.25, 0.8, "cone"),
        "thuja": (3.2, 1.2, 0.1, 0.2, "cone"), "young": (4.5, 2.0, 0.08, 1.8, "round")}
# (x, y, kind) world m; grouped by bed
TREES = [
    # NW bed (N boundary / G1_N / G1 ring / G1_W / W boundary)
    (101.6, -11.6, "spruce"), (110.8, -12.3, "spruce"), (115.3, -13.4, "thuja"), (106.2, -17.4, "young"),
    (108.6, -16.3, "thuja"), (103.2, -21.6, "broadleaf"), (106.2, -22.2, "spruce"), (108.8, -22.6, "broadleaf"),
    (104.2, -19.4, "thuja"), (112.4, -20.8, "broadleaf"), (101.4, -15.8, "thuja"),
    # W bed (G1_W / G1 ring / G1_SW / SW + W boundary)
    (101.6, -27.2, "locust"), (104.2, -28.2, "spruce"), (107.2, -27.7, "broadleaf"), (109.6, -28.6, "thuja"),
    (104.6, -32.5, "spruce"), (107.0, -31.6, "broadleaf"), (110.4, -31.6, "thuja"), (102.3, -36.5, "spruce"),
    (104.6, -35.9, "thuja"), (100.4, -32.0, "thuja"),
    # SW bed (G1_SW / G1 ring / G1_SSE / S boundary)
    (106.0, -35.6, "thuja"), (103.6, -39.4, "broadleaf"), (107.0, -43.7, "spruce"), (109.8, -44.0, "spruce"),
    (104.8, -44.2, "thuja"), (112.6, -36.6, "young"), (114.2, -39.2, "thuja"), (116.6, -40.6, "thuja"),
    (118.2, -43.8, "spruce"),
    # S-mid W bed (G1_SSE / G1 ring / G1 link / square / Centre_NS_S / S boundary)
    (125.0, -33.2, "locust"), (127.6, -35.6, "broadleaf"), (124.2, -37.6, "spruce"), (126.4, -39.8, "locust"),
    (125.2, -43.6, "spruce"), (127.8, -42.4, "thuja"), (123.4, -30.6, "thuja"),
    # S-mid W, west of G1_SSE (between the path and G1_SW is the SW bed above) -> east side trees of the SSE path
    (120.0, -41.6, "broadleaf"),
    # S-mid E bed (Centre_NS_S / square / G2 link / G2 ring / G2_SSW / S boundary)
    (131.6, -33.2, "locust"), (133.6, -35.4, "spruce"), (132.0, -39.2, "broadleaf"), (135.2, -40.2, "spruce"),
    (131.6, -43.4, "thuja"), (134.6, -44.2, "spruce"), (137.8, -34.0, "locust"), (137.6, -41.6, "broadleaf"),
    (136.2, -31.6, "thuja"),
    # S bed of G2 (G2_SSW / G2 ring / G2_SE / S boundary + SE chamfer): thujas along the south hedge
    (141.6, -45.0, "thuja"), (143.9, -44.8, "thuja"), (146.8, -45.0, "thuja"), (148.9, -45.1, "thuja"),
    (150.2, -45.2, "thuja"), (150.9, -42.6, "thuja"), (143.2, -40.6, "young"), (146.4, -38.8, "young"),
    # E bed (G2_SE / G2 ring / G2_E / E boundary + SE chamfer)
    (153.4, -40.8, "thuja"), (155.4, -39.3, "thuja"), (152.8, -34.6, "young"), (155.4, -32.4, "thuja"),
    (150.8, -31.8, "thuja"),
    # NE bed (Centre_NS_N / square / G2 link / G2 ring / G2_E / E + N boundary)
    (139.5, -14.6, "spruce"), (142.0, -14.4, "spruce"), (144.6, -14.2, "spruce"), (147.2, -14.8, "spruce"),
    (150.2, -15.0, "thuja"), (153.2, -15.2, "thuja"), (155.8, -14.8, "spruce"), (138.2, -17.4, "spruce"),
    (138.6, -20.4, "broadleaf"), (141.2, -22.4, "broadleaf"), (143.2, -18.6, "locust"), (147.4, -20.6, "locust"),
    (149.8, -22.8, "spruce"), (152.4, -25.8, "thuja"), (155.8, -24.4, "thuja"), (153.2, -19.6, "young"),
    (133.8, -22.8, "spruce"), (135.6, -17.6, "broadleaf"), (132.2, -19.4, "locust"), (133.4, -13.8, "spruce"),
    (136.4, -25.6, "thuja"),
    # N-mid bed (G1_N / G1 ring / G1 link / square / Centre_NS_N / N boundary)
    (122.0, -13.2, "spruce"), (125.6, -13.6, "spruce"), (119.6, -16.4, "thuja"), (125.6, -19.6, "locust"),
    (127.6, -22.6, "broadleaf"), (128.0, -17.8, "spruce"), (124.2, -24.6, "thuja"), (121.2, -20.2, "young"),
]


def main():
    g = json.load(open(os.path.join(SPECS, "SITE_Garden.json")))
    lay = json.load(open(os.path.join(SPECS, "..", "Audit", "garden_v2_layout.json")))
    outer = Polygon(lay["outline"])
    block, roofs = [], []
    for e in g["elements"]:
        t = e["type"]
        if t == "hedge" and e.get("ring"):
            block.append(Polygon(e["ring"], e.get("holes", [])).buffer(CLEAR))
        elif t in ("path", "wall") and e.get("line") and len(e["line"]) > 1:
            block.append(LineString(e["line"]).buffer(e.get("width", e.get("thk", 0.2)) / 2 + CLEAR))
        elif t == "hedge_arch":
            block.append(Point(e["center"]).buffer(e["span"] / 2 + 0.8))
        elif t == "gazebo":
            block.append(Point(e["center"]).buffer(e.get("across_flats", 7.7) / 2 + 1.6))
            roofs.append(Point(e["center"]).buffer(e.get("roof_across_flats", 9.15) / 2 + 0.2))
        elif t in ("bench", "lamp_orn", "bin", "sign") and e.get("pos"):
            block.append(Point(e["pos"]).buffer(0.9))
    lawn = outer.buffer(-0.7 - CLEAR).difference(unary_union(block))
    out, moved = [], 0
    for i, (x, y, kind) in enumerate(TREES):
        p = Point(x, y)
        if not lawn.contains(p):
            q = lawn.boundary.interpolate(lawn.boundary.project(p))
            if q.distance(p) > 1.6:
                print("  skip (no lawn within 1.6 m):", x, y, kind)
                continue
            p = Point(q.x + (q.x - x) * 0.05, q.y + (q.y - y) * 0.05) if q.distance(p) > 0 else q
            moved += 1
        h, d, td, cb, shape = KIND[kind]
        room = min((r.exterior.distance(p) if not r.contains(p) else 0.0 for r in roofs), default=99.0)
        if kind in ("locust", "broadleaf", "poplar") and d / 2 > room + 0.6:
            d = max(2.4, 2 * (room + 0.6))              # crown may overhang a roof edge by 0.6 m, not more (it is higher)
        out.append({"type": "tree", "name": f"GT_{i:02d}_{kind}", "pos": [round(p.x, 2), round(p.y, 2)], "height": h,
                    "crown_d": round(d, 1), "trunk_d": td, "crown_base": cb, "shape": shape, "ue_asset": "tree",
                    "species": kind, "evidence": EV, "confidence": "medium" if kind in ("spruce", "thuja") else "low"})
    spec = {"id": "SITE_Garden_Trees", "collection": "04_Garden", "ground": "terrain",
            "note": "Every tree of the formal garden, hand-read per bed (Scripts/Geo/zones/garden_trees.py); regenerate after "
                    "zone_garden.py.", "elements": out}
    json.dump(spec, open(os.path.join(SPECS, "SITE_Garden_Trees.json"), "w"), indent=1, ensure_ascii=False)
    from collections import Counter
    print(f"garden trees: {len(out)} ({dict(Counter(t['species'] for t in out))}), moved onto the lawn: {moved}")


if __name__ == "__main__":
    main()
