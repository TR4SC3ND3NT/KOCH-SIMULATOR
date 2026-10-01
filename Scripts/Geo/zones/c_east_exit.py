# Block C east exit (owner 2026-09-29: "да ставь ступеньки"): landing in front of the F1 east door + a flight down
# along the east wall to the sidewalk (the kerb of the east road is only ~1.4 m out, so the flight cannot run outward).
# Writes/replaces the CEast_* elements in SITE_CPlaza.json. Run: uv run --project Scripts python Scripts/Geo/zones/c_east_exit.py
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import zone_c_v6 as N   # noqa: E402   plan v6 (2026-10-01)

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
P = os.path.join(REPO, "Art", "Blender", "Specs", "SITE_CPlaza.json")
Z_GROUND = 4.90          # ground at the foot east of the v6 east face (check_stairs on the v6 build: 4.86-4.90)
RISERS, TREAD = 9, 0.30  # 9 x 0.167 = 1.50 = FFL 6.40 - 4.90 (owner: "about 9 steps"); 2R+T 0.63
W_FLIGHT, LAND_D = 1.2, 1.25
EV = "owner 2026-09-29: landing + steps down at the C east exit door (door 1.86 m, u 7.37-9.23 of the east face); " \
     "flight along the wall because the east road kerb is ~1.4 m from the wall; sizes by rule (riser 0.17, tread 0.30), not measured"


def main():
    rh = round((N.FFL - Z_GROUND) / RISERS, 4)
    hs, _ = N.hall(N.X_E - 0.5)
    y_d0, y_d1 = hs + 0.62, hs + 2.48                     # door jambs (C-local y)
    y_l0, y_l1 = y_d0 - 0.27, y_d1 + 0.27                 # landing 0.27 past each jamb
    x0, x1 = N.L_OUT, N.L_OUT + LAND_D
    w = lambda x, y: [round(v, 3) for v in N.c_to_w(x, y)]
    run = (RISERS - 1) * TREAD
    xc = x1 - W_FLIGHT / 2
    dir_s = (N.C_X[0] * 0 - N.C_Y[0], -N.C_Y[1])          # downhill = C-local -y (south)
    import math
    dir_deg = round(math.degrees(math.atan2(dir_s[1], dir_s[0])), 3)
    els = [
        {"type": "slab", "name": "CEast_Landing", "ring": [w(x0 - 0.05, y_l0), w(x1, y_l0), w(x1, y_l1), w(x0 - 0.05, y_l1)],
         "z0": round(Z_GROUND - 0.2, 3), "z1": N.FFL, "material": "stone", "slot": "M_Concrete_Precast", "evidence": EV, "confidence": "medium"},
        {"type": "stairs_run", "name": "CEast_Stair", "top": w(xc, y_l0), "dir_deg": dir_deg, "width": W_FLIGHT, "risers": RISERS,
         "riser_h": rh, "tread": TREAD, "z_top": N.FFL, "top_flush": True, "material": "stone", "slot": "M_Concrete_Precast",
         "evidence": EV, "confidence": "medium"},
        {"type": "rail3d", "name": "CEast_Rail", "unique_posts": True, "height": 0.9, "spacing": 1.2, "mid_rails": 1, "material": "metal",
         "points": [w(x0 + 0.05, y_l1 - 0.04) + [N.FFL], w(x1 - 0.04, y_l1 - 0.04) + [N.FFL], w(x1 - 0.04, y_l0) + [N.FFL],
                    w(x1 - 0.04, y_l0 - run) + [round(N.FFL - (RISERS - 1) * rh, 3)]],
         "evidence": EV + "; rail on the open sides (north edge of the landing, road side of landing + flight)", "confidence": "medium"},
    ]
    d = json.load(open(P, encoding="utf-8"))
    d["elements"] = [e for e in d["elements"] if not e.get("name", "").startswith("CEast_")] + els
    json.dump(d, open(P, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("C east exit: risers", RISERS, "x", rh, "tread", TREAD, "dir", dir_deg, "foot local y", round(y_l0 - run, 2))


if __name__ == "__main__":
    main()
