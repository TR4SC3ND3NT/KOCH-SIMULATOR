# Lists touching terrain pads whose flat levels differ by a few cm (0 < dz < MAX_DZ): on a paved yard such a step is
# never intended (real steps are >= 0.10 m risers), it only shows up as a seam/ledge. Used by R1 to unify pad levels.
# Run: python3 Scripts/Geo/pad_steps.py [--fix]
import glob
import json
import os
import sys

from shapely.geometry import Polygon

SPECS = os.path.join(os.path.dirname(__file__), "..", "..", "Art", "Blender", "Specs")
MAX_DZ = 0.075


def pads():
    for fn in sorted(glob.glob(os.path.join(SPECS, "*.json"))):
        d = json.load(open(fn, encoding="utf-8"))
        for key in ("terrain_pads",):
            for p in d.get(key) or []:
                if isinstance(p.get("z"), (int, float)) and "grad" not in p and "ref" not in p and len(p.get("ring", [])) >= 3 \
                        and p.get("field", True) is not False:
                    yield fn, p


def main(fix):
    P = [(fn, p, Polygon(p["ring"]).buffer(0)) for fn, p in pads()]
    pairs = []
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            (fa, a, ga), (fb, b, gb) = P[i], P[j]
            dz = abs(a["z"] - b["z"])
            if 1e-4 < dz < MAX_DZ and ga.distance(gb) < 0.3:
                pairs.append((dz, os.path.basename(fa), a.get("name"), a["z"], os.path.basename(fb), b.get("name"), b["z"]))
    for r in sorted(pairs, reverse=True):
        print("STEP %.3f  %s:%s z %.3f | %s:%s z %.3f" % r)
    print("pairs:", len(pairs))


if __name__ == "__main__":
    main("--fix" in sys.argv)
