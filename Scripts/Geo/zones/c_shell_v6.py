# Block C shell (BLD_C.json) v6 on the reference classroom plan (R1, 2026-10-01): starts from the facade-measured spec
# before the 7.5 m plan (git 9bfe6ac^, 29.4 m, storey 3.30) and only (1) deepens it to the interior (19.0 m west part /
# 20.3 m east part, the north front steps 1.3 m at the WC mid wall like the south one), (2) renumbers the edges for
# the stepped north front and (3) lays the windows from zone_c_v6 (the facade-measured pairs already sit on the
# reference window layout within 0.1 m). Items on the west/north fronts keep their world position.
# Run: uv run --project Scripts python Scripts/Geo/zones/c_shell_v6.py PRESTD_BLD_C.json
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import zone_c_v6 as N   # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
P = os.path.join(REPO, "Art", "Blender", "Specs", "BLD_C.json")
EV = "2026-10-01 plan v6 (c_shell_v6.py): reference classrooms 5.80 x 6.35, corridor 5.0"
L, YW, YE, J = N.L_OUT, N.Y_OUT_W, N.Y_OUT_E, N.JOG
XJN = N.X_JN - N.PART / 2 - N.T  # north front step: its wall stands west of the WC mid wall, so WC-E keeps its corner
OLD_W = 17.2                      # pre-v6 north front y (straight)
WC_SILLS = [round(N.WC_WIN_SILL + k * N.STOREY, 3) for k in range(4)]   # WC end windows, F1-F4 (029: sill 1.45)


def north_u(u_old):
    """Old north edge (from the NE corner, x = L - u) -> (new edge, u): 5 = east part from (L,YE), 7 = west part from (XJN,YW)."""
    x = L - u_old
    return (5, round(L - x, 3)) if x > XJN else (7, round(XJN - x, 3))


def main(src):
    C = json.load(open(src, encoding="utf-8"))
    assert abs(C["storey_m"] - N.STOREY) < 1e-6 and C["ring"][4] == [L, J], "expects the 29.4 m / 3.30 m facade spec"
    C["ring"] = [[round(a, 3), round(b, 3)] for a, b in ([0.0, 0.0], [N.X_TOWER0, 0.0], [N.X_TOWER0, J], [N.X_TOWER1, J], [L, J], [L, YE], [XJN, YE], [XJN, YW], [0.0, YW])]
    C["ring_notes"] += f" | {EV}: depth 19.0 / 20.3 m from the interior (2 x 6.35 rooms + 5.0 corridor + walls); the north front steps 1.3 m at the WC mid wall (rooms 6.35 deep on both sides). The west facade read 5.22 storeys (17.2 m); the interior wins (owner 2026-09-29: interior sizes over satellite/facade)"
    old = {f["edge"]: f for f in C["facades"]}
    win = lambda u, rows=("F1", "F2", "F3", "F4"): {"type": "W", "u": [round(v, 3) for v in u], "rows": list(rows)}
    xs = N.facade_windows
    hs, hn = N.hall(N.X_E - 0.5)
    s5_c = (N.Y_SE + hs - N.PART) / 2
    n5_c = (hn + N.PART + N.Y_NE) / 2
    door_u0, door_u1 = round(hs + 0.62 - J, 2), round(hs + 2.48 - J, 2)
    hsw, hnw = N.hall(1.0)
    cw = (hsw + hnw) / 2
    fac = [dict(old[0], windows=[win(xs("S1") + xs("S2")), dict(old[0]["windows"][1])], status=EV),
           dict(old[1]), dict(old[2]),
           dict(old[3], windows=[win([x - N.X_TOWER1 for x in xs("S4") + xs("S5")])], status=EV),
           dict(old[4], windows=[win([s5_c - J, n5_c - J, (door_u0 + door_u1) / 2 + 2.4]),       # rooms 102/103 + corridor window 2.4 m north of the door axis
                                 win([(door_u0 + door_u1) / 2], ("F2", "F3", "F4"))],                    # over the F1 exit door
                # 138: brown timber double door, 3-light transom (not the aluminium storefront of the main entrance)
                entrance=dict(old[4]["entrance"], u0=door_u0, u1=door_u1, leaf="solid", transom_lights=3, slot="M_Wood_Stained"),
                status=EV + " | " + old[4].get("status", "")),
           {"edge": 5, "name": "north_east", "status": EV,
            "windows": [win([L - x for x in xs("N4") + xs("N5")]), {"type": "WC", "u": [round(L - N.WC_WIN_N[1], 3)], "sills": WC_SILLS}]},
           {"edge": 6, "name": "north_step", "windows": []},
           {"edge": 7, "name": "north_west", "status": EV,
            "windows": [win(sorted(XJN - x for x in xs("N1") + xs("N2"))), {"type": "WC", "u": [round(XJN - N.WC_WIN_N[0], 3)], "sills": WC_SILLS}]},
           {"edge": 8, "name": "west", "status": EV, "confidence": "medium",
            "windows": [win([YW - (hnw + N.PART + N.Y_NW) / 2, YW - (cw - 0.9), YW - (N.Y_SW + hsw - N.PART) / 2]),
                        win([YW - (cw + 1.4)], ("F3", "F4"))]}]
    C["facades"] = fac
    C["window_types"]["WC"].update(w=N.WC_WIN_W, h=N.WC_WIN_H, evidence=C["window_types"]["WC"]["evidence"] +
                                   " | 2026-10-01 WC photos 029/030 (tile metrology): opening 0.52-0.55 x 1.10, sill 1.45, axis 0.775 m off the aisle wall")
    for p in C["pilasters"]:
        if p["edge"] == 6:
            p.update(edge=8, u0=round(p["u0"] + YW - OLD_W, 3), u1=round(p["u1"] + YW - OLD_W, 3))
    att = []
    for a in C["attachments"]:
        a = dict(a)
        if a.get("type") == "canopy" and a.get("edge") == 2:          # main entrance sign box (photos 158/159)
            a["sign"] = dict(a.get("sign", {}), slot="M_Sign_KOCH",
                             ue_note="blue sign box: KOCH emblem + 'KOCH' lettering only (the real sign's text/logo never in game)")
        if a.get("edge") == 6:                                          # west front: keep world y
            a["edge"] = 8
            if a.get("name") == "WestShed":                             # runs from the NW corner (owner) to its old south end
                a["u1"] = round(a["u1"] + YW - OLD_W, 3)
                # 2026-09-30 photos 181/182/188 (+013/014): brick-tile wall under a dark split-stone band, grey profiled
                # roof with a brass-coloured edge flashing; the south end is hidden by the basement-stair brick pier
                a.update(body_slot="M_Tile_Brick_Red", roof_slot="M_Sheet_Grey", trim_slot="M_Brass_Trim", band_ends=["u1"],
                         bands=[{"z0": -2.10, "z1": -0.58, "slot": "M_Tile_Brick_Red", "proj": 0.02},
                                {"z0": -0.58, "z1": -0.15, "slot": "M_Stone_Rubble_Dark", "proj": 0.04}],
                         bands_evidence="2026-09-30 photos 181/182/188: ~0.45 m dark split-stone band under the roof edge over "
                                        "brick-effect tile (shares of the 0.9 m front wall by eye, +-5 cm)")
            if "u" in a:
                a["u"] = [round(v + YW - OLD_W, 3) for v in a["u"]]
            if "items" in a:
                a["items"] = [[round(it[0] + YW - OLD_W, 3)] + it[1:] for it in a["items"]]
        elif a.get("edge") == 5:                                        # north front: split at the step
            if "u" in a:
                e, _ = north_u(a["u"][0])
                a["edge"], a["u"] = e, [north_u(v)[1] for v in a["u"]]
            if "items" in a:
                e, _ = north_u(a["items"][0][0])
                a["edge"], a["items"] = e, [[north_u(it[0])[1]] + it[1:] for it in a["items"]]
        if a.get("type") == "ramp" and a.get("name") == "Top" and "rail_ends" not in a:
            a["rail_ends"] = ["u1"]                                     # walk QA 2026-10-02: open outer end 1.05 m over the plaza
        att.append(a)
    C["attachments"] = att
    dorm = []
    for d in C["roof"]["dormers"]:
        if d["edge"] == 5:
            for e in (5, 7):
                us = [north_u(v)[1] for v in d["u"] if north_u(v)[0] == e]
                if us:
                    dorm.append({"edge": e, "u": us})
        elif d["edge"] == 4:
            dorm.append({"edge": 4, "u": [round(v * (YE - J) / (OLD_W - J), 2) for v in d["u"]]})
        else:
            dorm.append(d)
    C["roof"]["dormers"] = dorm
    C["note"] += f" | {EV}"
    json.dump(C, open(P, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("BLD_C v6: ring", C["ring"], "storey", C["storey_m"], "anchor", C["anchor"]["world_xy"])
    for f in fac:
        print("  edge", f["edge"], [(w["type"], w["u"]) for w in f.get("windows", [])], f.get("entrance", {}).get("u0", ""))


if __name__ == "__main__":
    main(sys.argv[1])
