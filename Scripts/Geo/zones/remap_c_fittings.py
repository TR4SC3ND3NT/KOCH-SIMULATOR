# Carries the hand-placed Block C fittings (WC fit-out, lobby machines, hall ceiling panels, radiators, heat pipes,
# benches, CCTV, stair-landing items, the F2 computer lab) from the old 29.4 m plan into the standard plan of
# zone_c_std.py (R1, 2026-09-29): piecewise-linear remap of C-local x (per side: south with the lobby, north with the
# WCs; stair bays unscaled) and y (per band: south rooms / hall / north rooms, wall-mounted items keep their offset from
# their wall), storey 3.30 -> 3.45, ceiling-mounted items follow the 2.92 -> 3.05 ceiling. Generated structure comes from
# the .std.json files; the old generated elements and the superseded hand walls are dropped.
# Run: uv run --project Scripts python Scripts/Geo/zones/remap_c_fittings.py STD_DIR
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import zone_c_std as N   # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OLD_ORIGIN = np.array([173.264, -3.640])
CX, CY = N.C_X, N.C_Y
OLD_STOREY, OLD_CEIL = 3.30, 2.92
XK_S = ([0.45, 3.35, 6.7, 12.5, 16.9, 22.6, 26.05, 28.95], [0.45, 3.35, N.P1, N.P2, N.P3, N.P4, N.FRONT_E, N.X_E])
XK_N = ([0.45, 3.35, 6.7, 12.3, 14.7, 17.1, 22.6, 26.05, 28.95], [0.45, 3.35, N.P1, N.P2, N.P_WCM, N.P3, N.P4, N.FRONT_E, N.X_E])
O_HS, O_HN, O_HN_REC = 5.675, 11.525, 12.725      # old hall faces (south, north; F1 east of x 14.9: recess)
DROP = re.compile(r"^(F1_Hall_N_Recess|F1_Hall_N_W|F\d_Accent_Recess_\d+|F\d_Accent_WC(_\d+)?)$")


def old_local(p):
    d = np.asarray(p[:2], float) - OLD_ORIGIN
    return float(d @ CX), float(d @ CY)


def remap_xy(xo, yo, k, wall_hint=None):
    o_hn = O_HN_REC if (k == 1 and xo > 14.9) else O_HN
    side = "S" if yo < (O_HS + o_hn) / 2 else "N"
    xn = float(np.interp(xo, *(XK_S if side == "S" else XK_N)))
    hs, hn = N.hall(xn)
    if yo < O_HS - 0.2:                                   # south rooms
        s_old = 0.45 if xo < 12.8 else 1.75
        yn = float(np.interp(yo, [s_old, O_HS - 0.2], [N.south_in(xn), hs - N.PART]))
    elif yo <= o_hn:                                      # hall: wall-mounted items keep their offset
        if yo - O_HS < 0.7:
            yn = hs + (yo - O_HS)
        elif o_hn - yo < 0.7:
            yn = hn - (o_hn - yo)
        else:
            yn = float(np.interp(yo, [O_HS, o_hn], [hs, hn]))
    else:                                                 # north rooms
        yn = float(np.interp(yo, [o_hn + 0.2, 16.75], [hn + N.PART, N.north_in(xn)]))
    return xn, yn


def remap_z(zw, k):
    rel = zw - N.FFL - (k - 1) * OLD_STOREY
    if rel > 2.4 and rel < 3.3:
        rel += N.CEIL - OLD_CEIL
    return round(N.FFL + (k - 1) * N.STOREY + rel, 3)


def floor_of(name):
    m = re.match(r"^F(\d)_", name)
    return int(m.group(1)) if m else 1


def remap_el(e):
    k = floor_of(e.get("name", ""))
    e = json.loads(json.dumps(e))

    def P(p):
        xn, yn = remap_xy(*old_local(p), k)
        w = N.c_to_w(xn, yn)
        return w + ([remap_z(p[2], k)] if len(p) > 2 else [])
    for f in ("center", "pos", "top"):
        if f in e:
            e[f] = P(e[f])
    for f in ("line", "ring", "points"):
        if f in e:
            e[f] = [P(p) for p in e[f]]
    for f in ("z0", "z1", "z_top"):
        if f in e and isinstance(e[f], (int, float)):
            e[f] = remap_z(e[f], k)
    if "z" in e:
        e["z"] = [remap_z(v, k) for v in e["z"]] if isinstance(e["z"], list) else remap_z(e["z"], k)
    if "openings" in e:
        for o in e["openings"]:
            o["z0"], o["z1"] = remap_z(o["z0"], k), remap_z(o["z1"], k)
    e["evidence"] = (e.get("evidence", "") + " | " if e.get("evidence") else "") + "2026-09-29 remapped onto the standard plan (remap_c_fittings.py)"
    return e


def main(std_dir):
    old_gen = {}
    for sid in ("INT_C_F1", "INT_C_Floors"):
        path = os.path.join(std_dir, sid + ".gen.json")
        old_gen[sid] = {x["name"] for x in json.load(open(path))["elements"]} if os.path.exists(path) else set()
    for sid in ("INT_C_F1", "INT_C_Floors"):
        spec_p = os.path.join(REPO, "Art", "Blender", "Specs", sid + ".json")
        old = json.load(open(spec_p, encoding="utf-8"))
        new = json.load(open(os.path.join(std_dir, sid + ".std.json")))
        gen_names = {x["name"] for x in new["elements"]}
        kept, dropped = [], []
        for e in old["elements"]:
            nm = e.get("name", "")
            if nm in old_gen[sid] or nm in gen_names or DROP.match(nm):
                dropped.append(nm); continue
            kept.append(remap_el(e))
        new["elements"] += kept
        json.dump(new, open(spec_p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"{sid}: generated {len(gen_names)}, carried over {len(kept)}, dropped {len(dropped)} old generated/superseded")


if __name__ == "__main__":
    main(sys.argv[1])
