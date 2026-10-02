# Hall south side (R1, owner 2026-09-29 screenshots 54/56/57/59/60/61 + footage): no gallery canopy on the Hall's south
# face; along it, measured on Google z20 (shadows of raised walls fall NNW) and the garden videos:
#   - a raised red-brick box with a light coping against the wall at the west end (x 88.6-98, 4.4 m out) and one at
#     x 113-118.8 (5.3 m out; 082013462 t22: brick wall ~0.9 m with a white coping behind the G1 north hedge),
#     like the light-well box along Block B (owner 61);
#   - the lawn bed right against the wall at the east end (x 134 - Hall east end, 6.8 m out, owner 60) with two rows
#     of spruces (ortho crowns at w 2.1 / 5.6 m: x 137.5, 142.5, 147 and 137.5, 142, 147, 150.8);
#   - paving everywhere else, and benches on the walk with their backs to the garden's north hedge (owner 59; video
#     081946180 t0-2.4: wrought-iron benches just north of the hedge).
# Removes the Hall gallery; writes HallBed_* into SITE_Garden. Run: uv run --project Scripts python Scripts/Geo/zones/hall_bed.py
import json
import math
import os

SP = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs")
EV = ("owner 2026-09-29 (screenshots 54/56/57/59-61) + Google z20 wall shadows / crowns + videos 081946180 t0-2.4, "
      "082013462 t22 (hall_bed.py)")
Z_G = 5.35                                      # ground level of the walk (LowerTerrace)
BOXES = [("W", 88.6, 98.0, 4.4), ("E", 113.0, 118.8, 5.3)]     # x0, x1 (world), depth out from the wall (m)
BOX_H, BOX_T = 0.85, 0.3
BED = (134.0, None, 6.8)                        # x0 world, x1 = Hall east end, depth out from the wall
SPRUCES = [(137.5, 2.1), (142.5, 2.1), (147.0, 2.1), (137.5, 5.6), (142.0, 5.6), (147.0, 5.6), (150.8, 5.4)]
BENCH_X = [104.0, 110.0, 123.5, 137.0, 143.0, 149.0, 154.5]    # along the garden's north hedge (arches at x 117.6, 130.8)


def main():
    hall = json.load(open(os.path.join(SP, "BLD_Hall.json")))
    hall["attachments"] = [a for a in hall["attachments"] if not (a["type"] == "gallery" and a.get("edge") == 0)]
    a = hall["anchor"]
    ox, oy = a["world_xy"]
    dx, dy = a["x_dir"]
    L = hall["ring"][1][0]
    W = lambda u, w: [round(ox + u * dx + w * dy, 3), round(oy + u * dy - w * dx, 3)]   # w > 0 = south, away from the wall
    u_of = lambda x: (x - ox) / dx                                                        # world x -> u (small angle)
    g = json.load(open(os.path.join(SP, "SITE_Garden.json")))
    E = [e for e in g["elements"] if not e["name"].startswith("HallBed_")]
    new, gs = [], [s for s in g.get("ground_surfaces", []) if not s["name"].startswith("HallBed")]
    for nm, x0, x1, dep in BOXES:
        u0, u1 = max(0.0, u_of(x0)), min(L, u_of(x1))
        ring = [W(u0, 0.0), W(u1, 0.0), W(u1, dep), W(u0, dep)]
        # 3 brick walls as one mitred run (the 4th side is the Hall wall; separate pieces overlapped at the corners and
        # left a notch outside them) + the raised soil inside
        new.append({"type": "wall", "name": f"HallBed_Box{nm}_Wall", "line": [W(u0, 0.05), W(u0, dep), W(u1, dep), W(u1, 0.05)],
                    "height": BOX_H, "thk": BOX_T, "cap_proj": 0.03, "material": "brick", "slot": "M_Tile_Brick_Red", "evidence": EV,
                    "confidence": "low"})
        new.append({"type": "slab", "name": f"HallBed_Box{nm}_Soil", "ring": [W(u0 + BOX_T / 2, 0.05), W(u1 - BOX_T / 2, 0.05),
                    W(u1 - BOX_T / 2, dep - BOX_T / 2), W(u0 + BOX_T / 2, dep - BOX_T / 2)], "z0": Z_G - 0.1,
                    "z1": round(Z_G + BOX_H - 0.1, 3), "material": "stone", "slot": "M_Ground_Grass", "evidence": EV,
                    "confidence": "low"})
        n = max(2, int((u1 - u0) / 2.5))
        for k in range(n):                          # roses / shrubs on the raised soil
            u = u0 + (u1 - u0) * (k + 0.5) / n
            p = W(u, dep * (0.35 if k % 2 else 0.65))
            new.append({"type": "tree", "name": f"HallBed_Box{nm}_Shrub_{k}", "pos": p, "z": round(Z_G + BOX_H - 0.1, 3),
                        "height": 1.0, "crown_d": 0.9, "trunk_d": 0.05, "crown_base": 0.1, "shape": "round", "species": "rose",
                        "evidence": EV, "confidence": "low"})
    x0, _, dep = BED
    u0, u1 = u_of(x0), L
    ring = [W(u0, 1.25), W(u1, 1.25), W(u1, dep), W(u0, dep)]   # wall side behind the hall's 1.2 m light-well covers
    new.append({"type": "planter", "name": "HallBed_Kerb", "ring": ring, "curb_h": 0.12, "curb_w": 0.12, "slot": "M_Concrete_Precast",
                "evidence": EV, "confidence": "medium"})
    gs.append({"name": "HallBed_Lawn", "ring": ring, "slot": "M_Ground_Grass", "evidence": EV})
    for k, (x, w) in enumerate(SPRUCES):
        new.append({"type": "tree", "name": f"HallBed_Spruce_{k}", "pos": W(u_of(x), w), "height": 8.0, "crown_d": 3.0, "trunk_d": 0.25,
                    "crown_base": 0.6, "shape": "cone", "species": "spruce", "evidence": EV, "confidence": "medium"})
    for k, x in enumerate((139.8, 144.8, 149.2)):
        new.append({"type": "tree", "name": f"HallBed_Rose_{k}", "pos": W(u_of(x), 3.9), "height": 0.9, "crown_d": 0.9, "trunk_d": 0.04,
                    "crown_base": 0.1, "shape": "round", "species": "rose", "evidence": EV, "confidence": "low"})
    # paving: the whole strip between the Hall and the garden's north hedge (minus the bed / boxes, which come after)
    gs.insert(0, {"name": "HallBed_Paving", "ring": [W(-1.0, 0.0), W(L + 2.0, 0.0), [158.2, -13.4], [100.4, -9.5]],
                  "slot": "M_Paver_Herringbone_Grey", "evidence": EV + ": paved walk between the Hall and the garden"})
    # benches with their backs to the garden's north hedge (outer face: the garden outline's north edge)
    lay = json.load(open(os.path.join(SP, "..", "Audit", "garden_v2_layout.json")))
    (ax, ay), (bx, by_) = lay["outline"][0], lay["outline"][1]
    tl = math.hypot(bx - ax, by_ - ay)
    tx, ty = (bx - ax) / tl, (by_ - ay) / tl
    nx, ny = -ty, tx                                                  # north (away from the garden)
    face = math.degrees(math.atan2(ny, nx))
    for k, x in enumerate(BENCH_X):
        t = (x - ax) / tx
        p = [round(ax + tx * t + nx * 0.45, 3), round(ay + ty * t + ny * 0.45, 3)]
        new.append({"type": "bench", "name": f"HallBed_Bench_{k}", "pos": p, "dir_deg": round(face, 2), "length": 2.2, "depth": 0.55,
                    "seat_h": 0.45, "back_h": 0.85, "ue_asset": "bench_slats_steel_frame",
                    "evidence": EV + " | 2026-10-02 garden photo diff: slatted benches on a black steel frame, ~2.2 m (front "
                                "feet 1.91 m apart by the tile rows, A015/A013)",
                    "confidence": "low"})
    E += new
    g["elements"] = E
    g["ground_surfaces"] = gs
    json.dump(g, open(os.path.join(SP, "SITE_Garden.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(hall, open(os.path.join(SP, "BLD_Hall.json"), "w"), indent=1, ensure_ascii=False)
    print(f"Hall south: boxes {len(BOXES)}, bed {ring}, spruces {len(SPRUCES)}, benches {len(BENCH_X)}")


if __name__ == "__main__":
    main()
