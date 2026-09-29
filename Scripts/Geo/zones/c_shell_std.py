# Block C shell (BLD_C.json) on the owner's standard plan (R1, 2026-09-29): 36.7 m long, west wing 19.75 m / tower +
# east wing 21.05 m deep (1.3 m steps south and north), anchor 5.0 m west of the old SW corner, storey 3.45; windows
# re-laid 2 per standard classroom (plus the end-wall window of each corner room, WC windows, corridor-end windows),
# entrance tower, stairs, canopy, ramps, light wells, pilasters and downpipes moved with their edges; the west shed is
# dropped (the grown west wing stands on its footprint). Uses zone_c_std.py for every plan line.
# Run: uv run --project Scripts python Scripts/Geo/zones/c_shell_std.py
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import zone_c_std as N   # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
P = os.path.join(REPO, "Art", "Blender", "Specs", "BLD_C.json")
EV = "2026-09-29 standard plan (owner): classrooms 7.5 x 6.1, shell grown to 36.7 m (c_shell_std.py)"
T = N.T
XT0, XT1 = N.X_TOWER0, N.X_TOWER1
L, YW, YE, J = N.L_OUT, N.Y_OUT_W, N.Y_OUT_E, N.JOG
XJN = N.X_JN


def rooms_x(x0, x1):
    """2 window centres per standard room (quarter points)."""
    return [round(x0 + (x1 - x0) * 0.25, 2), round(x0 + (x1 - x0) * 0.75, 2)]


def main():
    C = json.load(open(P, encoding="utf-8"))
    old_storey = C["storey_m"]
    dz = lambda k: (k - 1) * (N.STOREY - old_storey)
    C["anchor"]["world_xy"] = [round(v, 3) for v in N.C_ORIGIN.tolist()]
    C["anchor"]["status"] += f" | {EV}: SW corner moved 5.0 m west (the east end keeps 1.4 m to the east road)"
    # ring: edges e0 SW wing, e1 return, e2 tower, e3 SE wing, e4 east, e5 N east part, e6 N step, e7 N west part, e8 west
    C["ring"] = [[0.0, 0.0], [XT0, 0.0], [XT0, J], [XT1, J], [L, J], [L, YE], [XJN, YE], [XJN, YW], [0.0, YW]]
    C["ring_notes"] += f" | {EV}: ring on the standard plan; the north front steps 1.3 m at the WC mid wall like the south one (rooms 6.1 deep on both sides)"
    C["storey_m"] = N.STOREY
    C["rows"] = {f"F{k}": round(1.05 + (k - 1) * N.STOREY, 3) for k in (1, 2, 3, 4)}
    C["eave_z"] = round(C["eave_z"] + 3 * (N.STOREY - old_storey), 3)
    C["cornice"]["z0"] = round(C["cornice"]["z0"] + 3 * (N.STOREY - old_storey), 3)
    C["cornice"]["z1"] = C["eave_z"]
    for p in C["pilasters"]:
        p["z1"] = round(p["z1"] + 3 * (N.STOREY - old_storey), 3)
        if p["edge"] == 3:
            p["u1"] = round(L - XT1, 2); p["u0"] = round(p["u1"] - 1.02, 2)
    rows4 = ["F1", "F2", "F3", "F4"]
    x_s = rooms_x(N.X_W, N.P1 - 0.1) + rooms_x(N.P1 + 0.1, N.P2 - 0.1)            # 107, 108 (edge 0, u = x)
    x_se = rooms_x(N.P3 + 0.1, N.P4 - 0.1) + rooms_x(N.P4 + 0.1, N.X_E)            # 101, 102 (edge 3, u = x - XT1)
    x_n = rooms_x(N.X_W, N.P1 - 0.1) + rooms_x(N.P1 + 0.1, N.P2 - 0.1)             # 106, 105 (edge 7, u = XJN - x)
    x_ne = rooms_x(N.P3 + 0.1, N.P4 - 0.1) + rooms_x(N.P4 + 0.1, N.X_E)            # 104, 103 (edge 5, u = L - x)
    wc_w, wc_e = N.P2 + 0.1 + N.WC_W / 2, N.P_WCM + 0.1 + N.WC_W / 2
    wc_sills = [round(1.55 + (k - 1) * N.STOREY, 3) for k in (1, 2, 3, 4)]
    old = {f["edge"]: f for f in C["facades"]}
    fac = []
    f0 = dict(old[0]); f0["windows"] = [{"type": "W", "u": x_s, "rows": rows4}, {"type": "BW", "u": [2.5] + x_s[1:], "sills": [-2.36],
                                                                                      "evidence": old[0]["windows"][1].get("evidence", "")}]
    fac.append(dict(f0, edge=0, status=EV))
    fac.append(dict(old[1], edge=1))
    f2 = dict(old[2]); f2["windows"] = [dict(old[2]["windows"][0], sills=[round(s + dz(k), 3) for s, k in zip(old[2]["windows"][0]["sills"], (2, 3, 4))])]
    fac.append(dict(f2, edge=2))
    fac.append(dict(old[3], edge=3, windows=[{"type": "W", "u": [round(x - XT1, 2) for x in x_se], "rows": rows4}], status=EV))
    # east front: 102 / 103 end windows, corridor-end window F2-F4, F1 exit door (old: 0.62-2.48 m north of the hall's south face)
    hs, hn = N.hall(N.X_E - 0.5)
    e4 = dict(old[4])
    e4["windows"] = [{"type": "W", "u": [round((N.Y_SE + hs - N.PART) / 2 - J, 2), round((hn + N.PART + N.Y_NE) / 2 - J, 2)], "rows": rows4},
                     {"type": "W", "u": [round((hs + hn) / 2 - J, 2)], "rows": ["F2", "F3", "F4"]}]
    e4["entrance"] = dict(old[4]["entrance"], u0=round(hs + 0.62 - J, 2), u1=round(hs + 2.48 - J, 2))
    e4["status"] = EV + " | " + old[4].get("status", "")
    fac.append(dict(e4, edge=4))
    fac.append({"edge": 5, "name": "north_east", "windows": [{"type": "W", "u": [round(L - x, 2) for x in x_ne], "rows": rows4},
                {"type": "WC", "u": [round(L - wc_e, 2)], "sills": wc_sills}], "status": EV})
    fac.append({"edge": 6, "name": "north_step", "windows": []})
    fac.append({"edge": 7, "name": "north_west", "windows": [{"type": "W", "u": [round(XJN - x, 2) for x in x_n], "rows": rows4},
                {"type": "WC", "u": [round(XJN - wc_w, 2)], "sills": wc_sills}], "status": EV})
    hs_w, hn_w = N.hall(1.0)
    fac.append({"edge": 8, "name": "west", "windows": [{"type": "W", "u": [round(YW - (hn_w + N.PART + N.Y_NW) / 2, 2), round(YW - (N.Y_SW + hs_w - N.PART) / 2, 2)], "rows": rows4},
                {"type": "W", "u": [round(YW - (hs_w + hn_w) / 2, 2)], "rows": rows4}], "status": EV, "confidence": "medium"})
    C["facades"] = fac
    # attachments: edge renumbering (old 4 east -> 4, old 5 north -> 7/5, old 6 west -> 8) and lengths
    att = []
    for a in C["attachments"]:
        a = dict(a)
        e = a.get("edge")
        if a.get("name") == "WestShed":
            continue                                   # the grown west wing stands on the shed's footprint
        if e == 0 and a["type"] == "lightwell":
            a["u1"] = round(N.P2 - 0.3, 2)
            if "parapet" in a:
                a["parapet"] = dict(a["parapet"], spans=[[round(a["u1"] - 5.45, 2), a["u1"]]])
        elif e == 0 and a["type"] == "downpipe":
            a["u"] = [round(XT0 - 0.25, 2)]
        elif e == 3 and a["type"] == "lightwell":
            a["u1"] = round(L - XT1 - 0.3, 2)
        elif e == 5:                                   # north (old u from the NE corner)
            a["edge"] = 7 if a.get("name") == "DP_NW" else 5
            if a.get("name") == "DP_NW":
                a["u"] = [round(XJN - 0.4, 2)]
        elif e == 6:
            a["edge"] = 8
            a["u"] = [round(v * YW / 17.2, 2) for v in a["u"]] if "u" in a else a.get("u")
            if "items" in a:
                a["items"] = [[round(it[0] * YW / 17.2, 2)] + it[1:] for it in a["items"]]
        if "z1" in a and a["type"] == "downpipe":
            a["z1"] = round(a["z1"] + 3 * (N.STOREY - old_storey), 3)
        att.append(a)
    C["attachments"] = att
    # roof dormers: spread over the new edges
    r = C["roof"]
    r["dormers"] = [{"edge": 0, "u": [round(v, 2) for v in (x_s[1], x_s[3])]}, {"edge": 3, "u": [round(x - XT1, 2) for x in x_se[::2]]},
                    {"edge": 5, "u": [round(L - x, 2) for x in x_ne]}, {"edge": 7, "u": [round(XJN - x, 2) for x in x_n]},
                    {"edge": 4, "u": [round(YE * 0.33, 2), round(YE * 0.67, 2)]}]
    json.dump(C, open(P, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("BLD_C: ring", C["ring"], "storey", C["storey_m"], "eave", C["eave_z"], "anchor", C["anchor"]["world_xy"])


if __name__ == "__main__":
    main()
