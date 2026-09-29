# Hall south side (R1, owner 2026-09-29 screenshots 54/56/57): there is NO gallery canopy on the Hall's south face (the
# 061757320 t14-20 "gallery" was the A_W gallery); along the facade runs a paved strip (benches at the wall, garden
# videos 081946180 t0-3) and then one long lawn bed with trees and flowers over almost the whole length, its outer edge
# where the owner drew the second line (~2.2 + 2.6 m out). Removes the Hall gallery, writes HallBed_* into SITE_Garden.
# Run: uv run --project Scripts python Scripts/Geo/zones/hall_bed.py
import json
import math
import os

SP = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs")
EV = "owner 2026-09-29 (screenshots 54/56/57: no canopy on the Hall's south side, a bed with trees along almost the whole length) + 081946180 t0-3 (lawn with thujas/spruces, benches at the wall, no gallery); hall_bed.py"
U0, U1 = 1.0, 59.2              # bed ends along the facade (m from the Hall's SW corner)
W0, W1 = 2.2, 4.8               # bed from 2.2 m to 4.8 m out from the wall (paved strip at the wall)
TREES = [(u, k) for u, k in ((4.1, "thuja"), (9.1, "spruce"), (15.1, "thuja"), (21.1, "spruce"), (27.1, "thuja"), (33.1, "spruce"),
                             (39.1, "thuja"), (45.1, "spruce"), (51.1, "thuja"), (56.8, "spruce"))]
KIND = {"thuja": (3.0, 1.1, 0.1, 0.2, "cone"), "spruce": (7.5, 2.6, 0.22, 0.6, "cone")}


def main():
    hall = json.load(open(os.path.join(SP, "BLD_Hall.json")))
    n0 = len(hall["attachments"])
    hall["attachments"] = [a for a in hall["attachments"] if not (a["type"] == "gallery" and a.get("edge") == 0)]
    for f in hall["facades"]:
        if f["edge"] == 0:
            f["evidence"] = f.get("evidence", "").split(" | 2026-09-29 owner")[0] + " | 2026-09-29 owner: no gallery on this face (hall_bed.py)"
    a = hall["anchor"]
    ox, oy = a["world_xy"]
    dx, dy = a["x_dir"]
    W = lambda u, w: [round(ox + u * dx + w * dy, 3), round(oy + u * dy - w * dx, 3)]   # w > 0 = south, away from the wall
    g = json.load(open(os.path.join(SP, "SITE_Garden.json")))
    E = [e for e in g["elements"] if not e["name"].startswith("HallBed_")]
    ring = [W(U0, W0), W(U1, W0), W(U1, W1), W(U0, W1)]
    new = [{"type": "planter", "name": "HallBed_Kerb", "ring": ring, "curb_h": 0.12, "curb_w": 0.12, "slot": "M_Concrete_Precast",
            "evidence": EV, "confidence": "medium"}]
    wm = (W0 + W1) / 2
    for i, (u, k) in enumerate(TREES):
        h, d, td, cb, sh = KIND[k]
        new.append({"type": "tree", "name": f"HallBed_{k.title()}_{i}", "pos": W(u, wm), "height": h, "crown_d": d, "trunk_d": td,
                    "crown_base": cb, "shape": sh, "species": k, "evidence": EV, "confidence": "low"})
    for i, (a_, b_) in enumerate(zip(TREES[:-1], TREES[1:])):
        um = (a_[0] + b_[0]) / 2
        new.append({"type": "tree", "name": f"HallBed_Flowers_{i}", "pos": W(um - 1.0, wm - 0.5), "height": 0.5, "crown_d": 0.7,
                    "trunk_d": 0.03, "crown_base": 0.05, "shape": "round", "species": "flowers", "evidence": EV, "confidence": "low"})
        new.append({"type": "tree", "name": f"HallBed_Shrub_{i}", "pos": W(um + 1.0, wm + 0.4), "height": 0.9, "crown_d": 1.0,
                    "trunk_d": 0.05, "crown_base": 0.05, "shape": "round", "species": "shrub", "evidence": EV, "confidence": "low"})
    E += new
    g["elements"] = E
    gs = [s for s in g.get("ground_surfaces", []) if not s["name"].startswith("HallBed")]
    gs += [{"name": "HallBed_Strip", "ring": [W(-0.5, 0.0), W(60.7, 0.0), W(60.7, W0), W(-0.5, W0)], "slot": "M_Paver_Herringbone_Grey",
            "evidence": EV + ": paved strip at the wall"},
           {"name": "HallBed_Lawn", "ring": ring, "slot": "M_Ground_Grass", "evidence": EV}]
    g["ground_surfaces"] = gs
    json.dump(g, open(os.path.join(SP, "SITE_Garden.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(hall, open(os.path.join(SP, "BLD_Hall.json"), "w"), indent=1, ensure_ascii=False)
    print(f"Hall: gallery removed ({n0} -> {len(hall['attachments'])} attachments); bed {ring}; plants {len(new) - 1}")


if __name__ == "__main__":
    main()
