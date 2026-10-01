# Carries the hand-placed Block C fittings (WC fit-out, lobby machines, hall ceiling panels, heat pipes, CCTV, fire
# hoses, plants, stair-landing items) from the 7.5 m plan (zone_c_std.py, origin 5 m west) onto plan v6 (zone_c_v6.py)
# (R1, 2026-10-01): piecewise-linear remap of C-local x per side through the matching plan lines, y per band (south
# rooms / hall / north rooms; wall-mounted items keep their offset from their wall), storey 3.45 -> 3.30 and
# ceiling-mounted items follow the 3.05 -> 2.90/2.80 grid. The hand-placed F2 lab (Lab_*) is dropped: every standard
# room now gets the generated reference fit-out. Generated structure comes from the v6 .std.json files.
# Run: uv run --project Scripts python Scripts/Geo/zones/remap_c_v6.py V6_DIR
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import zone_c_std as S   # noqa: E402   source plan (what the current specs are on)
import zone_c_v6 as N    # noqa: E402   target plan

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KN_S = ["X_W", "FRONT_W", "P1", "P2", "P3", "P4", "FRONT_E", "X_E"]
KN_N = ["X_W", "FRONT_W", "P1", "P2", "P_WCM", "P3", "P4", "FRONT_E", "X_E"]
XK_S = ([getattr(S, k) for k in KN_S], [getattr(N, k) for k in KN_S])
XK_N = ([getattr(S, k) for k in KN_N], [getattr(N, k) for k in KN_N])
DROP = re.compile(r"^(F\d_)?(Lab_|Accent_Recess_|WC\d_)")   # old F2 lab; old F1 WC recess accents; old WC fit-out (v6 wc_fitout)


def s_local(p):
    d = np.asarray(p[:2], float) - S.C_ORIGIN
    return float(d @ S.C_X), float(d @ S.C_Y)


def remap_xy(xo, yo):
    hs_o, hn_o = S.hall(xo)
    side = "S" if yo < (hs_o + hn_o) / 2 else "N"
    xn = float(np.interp(xo, *(XK_S if side == "S" else XK_N)))
    hs, hn = N.hall(xn)
    if yo < hs_o - S.PART:                                    # south rooms
        yn = float(np.interp(yo, [S.south_in(xo), hs_o - S.PART], [N.south_in(xn), hs - N.PART]))
    elif yo <= hn_o + S.PART and yo >= hs_o - S.PART:          # hall (and its walls): wall-mounted items keep their offset
        if yo - hs_o < 0.7:
            yn = hs + (yo - hs_o)
        elif hn_o - yo < 0.7:
            yn = hn - (hn_o - yo)
        else:
            yn = float(np.interp(yo, [hs_o, hn_o], [hs, hn]))
    else:                                                     # north rooms
        yn = float(np.interp(yo, [hn_o + S.PART, S.north_in(xo)], [hn + N.PART, N.north_in(xn)]))
    return xn, yn


def floor_of(name):
    m = re.match(r"^F(\d)_", name)
    return int(m.group(1)) if m else 1


def remap_z(zw, k):
    rel = zw - S.FFL - (k - 1) * S.STOREY
    if 2.4 < rel < S.STOREY and k <= 4:
        rel += N.ceil_of(k) - S.CEIL
    return round(N.FFL + (k - 1) * N.STOREY + rel, 3)


def remap_el(e):
    k = floor_of(e.get("name", ""))
    e = json.loads(json.dumps(e))

    def P(p):
        w = N.c_to_w(*remap_xy(*s_local(p)))
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
    e["evidence"] = (e.get("evidence", "") + " | " if e.get("evidence") else "") + "2026-10-01 remapped onto plan v6 (remap_c_v6.py)"
    return e


def main(v6_dir):
    std_specs, _ = S.build()
    std_gen = {sp["id"]: {x["name"] for x in sp["elements"]} for sp in std_specs}
    for sid in ("INT_C_F1", "INT_C_Floors"):
        spec_p = os.path.join(REPO, "Art", "Blender", "Specs", sid + ".json")
        old = json.load(open(spec_p, encoding="utf-8"))
        new = json.load(open(os.path.join(v6_dir, sid + ".std.json")))
        gen_names = {x["name"] for x in new["elements"]}
        kept, dropped = [], []
        for e in old["elements"]:
            nm = e.get("name", "")
            if nm in std_gen[sid] or nm in gen_names or DROP.match(nm):
                dropped.append(nm)
                continue
            kept.append(remap_el(e))
        new["elements"] += kept
        json.dump(new, open(spec_p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"{sid}: generated {len(gen_names)}, carried over {len(kept)}, dropped {len(dropped)} (old generated / lab)")


if __name__ == "__main__":
    main(sys.argv[1])
