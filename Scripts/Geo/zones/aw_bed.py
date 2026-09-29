# Lawn bed along the A_W gallery (R1, owner 2026-09-29 + video 070309303 t33-37): between the herringbone walk that
# runs along the garden's east hedge and the lower walkway at the gallery deck there is one long lawn bed with a red
# brick kerb, clipped thujas, shrubs and flowers. Plan from Google z20: garden lawn edge x 157.5, paving to 160.5, the
# thuja row (dark crowns + shadows) at x 161.5-162.5 from y -27 to -46, gallery eave 163.5 (roof lean ~0.9 m east).
# Writes AWBed_* elements into SITE_Garden.json and re-lays the AW_PathN / AW_LawnN terrain pads of BLD_A_W.json onto
# the walk and the bed (they sat 3-4 m west, inside the garden). The old square "pits" of the 4 thujas were this bed.
# Run: uv run --project Scripts python Scripts/Geo/zones/aw_bed.py
import json
import os

SP = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs")
EV = "owner 2026-09-29 (screenshot 54: bed along almost the whole gallery) + video 070309303 t33-37 (red brick kerb, thujas, shrubs, flowers) + Google z20 plan (thuja row x 161.5-162.5); aw_bed.py"
Y_S, Y_N = -48.0, -24.0          # bed ends (south: past the wide stair head; north: short of the north steps/ramp)
X_WALK0 = 157.55                 # walk west edge = garden hedge outer face (at y -30; follows the gallery line)
WALK_W, BED_W = 3.0, 2.4         # walk (herringbone, ~10 brick courses in t34.5) and bed widths (m)
DX_DY = (166.9 - 164.45) / (72.95 - 22.75)   # gallery line drift in x per metre of y (A_W west face)


def x_at(y, x30):
    return x30 + (y + 30.0) * DX_DY


def main():
    g = json.load(open(os.path.join(SP, "SITE_Garden.json")))
    aw = json.load(open(os.path.join(SP, "BLD_A_W.json")))
    E = [e for e in g["elements"] if not e["name"].startswith("AWBed_") and not e["name"].startswith("AW_Pit_")]
    xb0 = X_WALK0 + WALK_W                                   # bed west kerb
    r = lambda v: round(v, 3)
    bed = [[r(x_at(Y_S, xb0)), Y_S], [r(x_at(Y_S, xb0 + BED_W)), Y_S], [r(x_at(Y_N, xb0 + BED_W)), Y_N], [r(x_at(Y_N, xb0)), Y_N]]
    new = [{"type": "planter", "name": "AWBed_Kerb", "ring": bed, "curb_h": 0.12, "curb_w": 0.12, "slot": "M_Tile_Brick_Red",
            "evidence": EV, "confidence": "medium"}]
    # plants: thujas every ~4.4 m on the bed axis (the 4 known ones kept), shrubs and flower clumps between them
    xc = xb0 + BED_W * 0.55
    thuja_y = [-46.0, -43.35, -38.86, -34.41, -29.97, -25.6]
    for k, y in enumerate(thuja_y):
        new.append({"type": "tree", "name": f"AWBed_Thuja_{k}", "pos": [r(x_at(y, xc)), y], "height": 2.6, "crown_d": 0.9,
                    "trunk_d": 0.08, "crown_base": 0.2, "shape": "cone", "species": "thuja", "evidence": EV, "confidence": "medium"})
    for k, (a, b) in enumerate(zip(thuja_y[:-1], thuja_y[1:])):
        ym = (a + b) / 2
        new.append({"type": "tree", "name": f"AWBed_Shrub_{k}", "pos": [r(x_at(ym, xb0 + 0.9)), round(ym, 2)], "height": 0.8,
                    "crown_d": 0.9, "trunk_d": 0.05, "crown_base": 0.05, "shape": "round", "species": "shrub", "evidence": EV,
                    "confidence": "low"})
        new.append({"type": "tree", "name": f"AWBed_Flowers_{k}", "pos": [r(x_at(ym + 1.1, xb0 + 1.7)), round(ym + 1.1, 2)],
                    "height": 0.45, "crown_d": 0.6, "trunk_d": 0.03, "crown_base": 0.05, "shape": "round", "species": "flowers",
                    "evidence": EV, "confidence": "low"})
    for e in E:                                              # the wheelie bin stood in the bed: onto the lower walkway
        if e["name"] == "AW_Bin_0":
            e["pos"] = [r(x_at(e["pos"][1], xb0 + BED_W + 0.55)), e["pos"][1]]
    old_pit_trees = {f"AW_PitThuja_{k}" for k in range(4)}
    E = [e for e in E if e["name"] not in old_pit_trees]
    i = next(k for k, e in enumerate(E) if e["name"].startswith("AW_"))
    E[i:i] = new
    g["elements"] = E
    g.setdefault("ground_surfaces", [])
    g["ground_surfaces"] = [s for s in g["ground_surfaces"] if not s.get("name", "").startswith("AWBed")] + [
        {"name": "AWBed_Lawn", "ring": bed, "slot": "M_Ground_Grass", "evidence": EV},
        {"name": "AWBed_Walk", "ring": [[r(x_at(Y_S - 4, X_WALK0)), Y_S - 4], [r(x_at(Y_S - 4, xb0)), Y_S - 4], [r(x_at(-14.0, xb0)), -14.0],
                                        [r(x_at(-14.0, X_WALK0)), -14.0]], "slot": "M_Paver_Herringbone_Grey",
         "evidence": EV + ": herringbone walk between the garden hedge and the bed"},
        {"name": "AWBed_LowerWalk", "ring": [[r(x_at(Y_S - 4, xb0 + BED_W)), Y_S - 4], [r(x_at(Y_S - 4, xb0 + BED_W + 3.5)), Y_S - 4],
                                             [r(x_at(-14.0, xb0 + BED_W + 3.5)), -14.0], [r(x_at(-14.0, xb0 + BED_W)), -14.0]],
         "slot": "M_Paver_Herringbone_Grey", "evidence": EV + ": lower walkway between the bed and the gallery deck (under the deck too)"}]
    g["ground_surfaces"] = [s for s in g["ground_surfaces"] if s["name"] != "AWBed_Lawn"] + [s for s in g["ground_surfaces"] if s["name"] == "AWBed_Lawn"]
    for p in aw["terrain_pads"]:
        if p["name"] == "AW_PathN":
            p["ring"] = [[r(x_at(-52.6, X_WALK0)), -52.6], [r(x_at(-52.6, xb0)), -52.6], [r(x_at(-25.9, xb0)), -25.9], [r(x_at(-25.9, X_WALK0)), -25.9]]
            p["evidence"] += " | 2026-09-29 aw_bed.py: moved onto the walk east of the measured garden hedge (x 157.55)"
        if p["name"] == "AW_LawnN":
            p["ring"] = [[r(x_at(-52.6, xb0)), -52.6], [r(x_at(-52.6, xb0 + BED_W)), -52.6], [r(x_at(-25.9, xb0 + BED_W)), -25.9], [r(x_at(-25.9, xb0)), -25.9]]
            p["evidence"] += " | 2026-09-29 aw_bed.py: = the kerbed lawn bed along the gallery"
    json.dump(g, open(os.path.join(SP, "SITE_Garden.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(aw, open(os.path.join(SP, "BLD_A_W.json"), "w"), indent=1, ensure_ascii=False)
    print("AW bed", bed, "plants", len(new) - 1)


if __name__ == "__main__":
    main()
