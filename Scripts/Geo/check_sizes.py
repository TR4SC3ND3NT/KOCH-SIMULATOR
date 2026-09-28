# Size sanity scan over all specs (R1 zone loop): flags elements outside the normal range of real-world sizes
# (stairs, ramps, railings, benches, doors, curbs). Run: python3 Scripts/Geo/check_sizes.py
import json
import math
import os

SPECS = os.path.join(os.path.dirname(__file__), "..", "..", "Art", "Blender", "Specs")
RULES = {   # type -> [(field, lo, hi, what)]
    "stairs_run": [("riser_h", 0.12, 0.20, "подступенок"), ("tread", 0.26, 0.80, "проступь"), ("width", 0.9, 12.0, "ширина марша")],
    "steps": [("riser_h", 0.10, 0.20, "подступенок"), ("tread", 0.26, 0.80, "проступь")],
    "bench": [("seat_h", 0.40, 0.50, "высота сиденья"), ("length", 0.9, 6.5, "длина")],
    "rail3d": [("height", 0.8, 1.25, "высота перил")],
    "fence": [("height", 0.6, 5.5, "высота ограды")],
    "door": [],
}
rows = []
for fn in sorted(os.listdir(SPECS)):
    if not fn.endswith(".json") or fn.startswith("INT_C_Basement"):
        continue
    for el in json.load(open(os.path.join(SPECS, fn))).get("elements", []):
        t = el.get("type")
        for f, lo, hi, what in RULES.get(t, []):
            if f in el and not (lo <= el[f] <= hi):
                rows.append((fn[:-5], el.get("name"), what, el[f], f"{lo}-{hi}"))
        if t == "door" and "z0" in el and "z1" in el:
            h = el["z1"] - el["z0"]; w = el["u1"] - el["u0"]
            if not (1.95 <= h <= 2.6) or not (0.75 <= w <= 2.2):
                rows.append((fn[:-5], el.get("name"), "дверь h x w", f"{h:.2f} x {w:.2f}", "1.95-2.6 x 0.75-2.2"))
        if t == "roof_plane" and "Ramp" in el.get("name", "") and len(el.get("z", [])) >= 4:
            r = el["ring"]; z = el["z"]
            best = 0.0
            for i in range(len(r)):
                for j in range(i + 1, len(r)):
                    dxy = math.dist(r[i], r[j])
                    if dxy > 0.5:
                        best = max(best, abs(z[i] - z[j]) / dxy)
            if best > 0.125:
                rows.append((fn[:-5], el.get("name"), "уклон пандуса", f"{best * 100:.1f}%", "<= 12.5%"))
print("SIZES flagged:", len(rows))
for r in rows:
    print("SIZE", *r)
