# Draws site_osm.json (and optional traced footprints) over a local orthophoto, with a 10 m grid, for visual cross-checks.
# Run: uv run --project Scripts python Scripts/Geo/overlay_check.py <ortho.png> <out.jpg> [--crop X0 Y0 X1 Y1] [--extra traced.json]
import argparse
import json
import os

from PIL import Image, ImageDraw

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COLORS = {"building": (255, 230, 0), "highway": (0, 230, 255), "leisure": (0, 255, 0), "barrier": (255, 0, 255)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ortho")
    ap.add_argument("out")
    ap.add_argument("--crop", type=float, nargs=4)
    ap.add_argument("--extra", help="JSON with {'items'|'footprints': [{'id','ring'}]} drawn in red")
    ap.add_argument("--grid", type=float, default=10.0)
    a = ap.parse_args()

    meta = json.load(open(os.path.splitext(a.ortho)[0] + ".json"))
    x0, y0, x1, y1 = meta["extent_local"]
    res = meta["m_per_px"]
    img = Image.open(a.ortho).convert("RGB")
    d = ImageDraw.Draw(img)
    px = lambda x, y: ((x - x0) / res, (y1 - y) / res)

    g = a.grid
    for gx in range(int(x0 // g), int(x1 // g) + 1):
        c = (255, 255, 255) if gx % 10 == 0 else (90, 90, 90)
        d.line([px(gx * g, y0), px(gx * g, y1)], fill=c, width=1)
    for gy in range(int(y0 // g), int(y1 // g) + 1):
        c = (255, 255, 255) if gy % 10 == 0 else (90, 90, 90)
        d.line([px(x0, gy * g), px(x1, gy * g)], fill=c, width=1)

    site = json.load(open(os.path.join(REPO, "Art", "Blender", "Data", "site_osm.json"), encoding="utf-8"))
    d.line([px(*c) for c in site["campus_boundary"]], fill=(255, 0, 0), width=3)
    for f in site["features"]:
        col = COLORS.get(f["kind"], (200, 200, 200))
        if "ring" in f:
            d.line([px(*c) for c in f["ring"] + f["ring"][:1]], fill=col, width=2)
        else:
            d.line([px(*c) for c in f["line"]], fill=col, width=1)
    if a.extra:
        data = json.load(open(a.extra))
        for fp in data.get("items", data.get("footprints", [])):
            d.line([px(*c) for c in fp["ring"] + fp["ring"][:1]], fill=(255, 40, 40), width=2)
            d.text(px(*fp["ring"][0]), fp["id"], fill=(255, 40, 40))
    if a.crop:
        cx0, cy0, cx1, cy1 = a.crop
        l, t = px(cx0, cy1)
        r, b = px(cx1, cy0)
        img = img.crop((int(l), int(t), int(r), int(b)))
    img.save(a.out, quality=90)
    print("wrote", a.out, img.size)


if __name__ == "__main__":
    main()
