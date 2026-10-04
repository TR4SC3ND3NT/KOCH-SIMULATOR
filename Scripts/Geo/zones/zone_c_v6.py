# Zone "C floors" v6 (R1, 2026-10-01): Block C on the measured reference classroom (C105, docs/reference/C105_etalon.png):
# rooms 5.80 m along the windows x 6.35 m deep, corridor 5.0 m (C204 photo 014: door 205 seen across it), lobby 4.5 m,
# WCs 2.15 m, storey 3.30 (facade fit), lay-in grid 2.90 (F1) / 2.80 (F2+), door openings 0.90 x 2.00. The shell returns
# to the 29.4 m satellite/facade length (4 x 5.80 + lobby + walls); the facade-measured windows (2.59 m pairs) land on
# the reference window layout. Writes the structural elements (slabs, ceilings, walls, doors, stairs, bulkheads,
# accents) and the classroom fit-out (window beam, door/back bulkheads, pilasters, lab desks, monitors, chairs,
# teacher's desk, TV, whiteboard, AC, radiators) of INT_C_F1 / INT_C_Floors; hand-placed fittings are carried over by
# remap_c_v6.py. C-local metres: x east along the south front from the SW outer corner, y north, z above the F1 FFL.
# Run: uv run --project Scripts python Scripts/Geo/zones/zone_c_v6.py OUT_DIR
import json
import math
import os
import sys

import numpy as np

# --- frame: the BLD_C anchor (SW outer corner of the west wing, satellite/facade fit)
C_X = np.array([0.99920, -0.03985])
C_Y = np.array([-C_X[1], C_X[0]])
C_ORIGIN = np.array([176.364, -0.140])   # BLD_C anchor (2026-10-04 D1: +3.10/+3.50)
FFL = 6.40
EAST = math.degrees(math.atan2(C_X[1], C_X[0]))
NORTH = EAST + 90.0

T, PART = 0.45, 0.20
L_OUT = 29.4                                  # = 2 T + 4 STD_L + LOBBY_W + 4 PART (facade fit 29.4)
X_W, X_E = T, L_OUT - T
STD_L, STD_D = 5.80, 6.35                     # reference classroom C105 (clear, wall faces)
COR = 5.80                                    # corridor, clear (2026-09-30_C_interior 003: 5.67-5.87 between the facing door
                                              # openings, scaled by their 2.00 m height; the C204 014 read of 5.0 was the weaker one)
JOG = 1.3                                     # facade step of the west wing (061621646 fit), mirrored inside
# x lines (partition centres) along the plan
P1 = X_W + STD_L + PART / 2                   # 107|108, 106|105
P2 = P1 + PART / 2 + STD_L + PART / 2         # 108|lobby, 105|WC-W
LOBBY_W = 4.5
P3 = P2 + PART / 2 + LOBBY_W + PART / 2       # lobby|101 = south jog
LOBBY_X0, LOBBY_X1 = 12.82, 16.58             # F1 lobby clear faces = storefront frame / tower edges: 3.76 clear, the side
                                              # walls 0.57 thick (lined on the lobby side), rooms 108/101 unchanged (D2 X0-05)
WC_W = 2.15
P_WCM = P2 + PART / 2 + WC_W + PART / 2       # WC mid wall = north jog
P4 = P3 + PART / 2 + STD_L + PART / 2         # 101|102, 104|103
X_TOWER0, X_TOWER1 = 12.8, 16.6               # entrance tower (outer faces, facade fit), inside the lobby span
X_JS, X_JN = P3, P_WCM
# y levels: west part / east part (+JOG)
Y_SW, Y_SE = T, JOG + T                       # south inner faces (west wing / tower + east wing)
HW0, HW1 = Y_SW + STD_D + PART, Y_SW + STD_D + PART + COR     # hall faces, west part
HE0, HE1 = HW0 + JOG, HW1 + JOG                               # hall faces, east part
Y_NW, Y_NE = HW1 + PART + STD_D, HE1 + PART + STD_D           # north inner faces
Y_OUT_W, Y_OUT_E = Y_NW + T, Y_NE + T

STOREY = 3.30        # facade fit (061621646 PnP: 29.4 m : 3.29 m), BLD_C storey_m
SLAB = 0.25
CEIL = 2.90          # F1 lay-in grid (C105 150/151/153); F2+ 2.80 (C204 014), see ceil_of()
DOOR_H, DOOR_W, WC_DOOR_W = 2.05, 0.99, 0.90  # classroom door frame (outer): campus.md metrology 2.05 x 0.99, re-checked
                                                # 2026-10-02 on C204 (1.87 m person in the doorway: 2.02-2.04 x ~1.0)
RISERS, RISERS2 = 11, 10                       # flight 1 (half bottom riser + 10) / flight 2 (riser count, 2026-10-04 D2)
RISER_H = STOREY / 20.5                       # 20.5 risers per storey
TREAD, BOTTOM_RISER = 0.31, 0.5 * STOREY / 20.5
LANDING = 1.24
FLIGHT_W, WELL = 1.275, 0.20                  # stair bay 2.75: 103 frame 1.46 m off the stair-front corner (Q3-24 / D2)
STAIR_X = 2 * FLIGHT_W + WELL
FRONT_W, FRONT_E = X_W + STAIR_X, X_E - STAIR_X
SOFFIT = 0.08          # flight soffit slab: 0.18 cut the F1 E exit-door frame / W window head (2026-10-04 X0-01)
F5_Z = 4 * STOREY


def ceil_of(k):
    """Lay-in grid height above the floor of storey k (m)."""
    return 2.90 if k == 1 else 2.80


def cor_ceil_of(k):
    """Corridor lay-in grid height (m): higher than the rooms (owner; 003 reads 3.10 at the wall, capped at storey 3.30
    - slab 0.25 - 0.05 plenum); the cross bulkheads hang to 2.66 (003)."""
    return 3.00


COR_BEAM_Z = 2.66


def c_to_w(x, y):
    return (C_ORIGIN + x * C_X + y * C_Y).round(6).tolist()


def ring(x0, x1, y0, y1):
    return [c_to_w(x0, y0), c_to_w(x1, y0), c_to_w(x1, y1), c_to_w(x0, y1)]


def z(v):
    return round(FFL + v, 3)


def ev(txt, conf="medium"):
    return {"evidence": "2026-10-01 reference classroom plan v6: " + txt, "confidence": conf}


def hall(x):
    """(south face, north face) of the hall at x: south wall jogs at the lobby's east wall, north at the WC mid wall."""
    return (HW0 if x < X_JS else HE0), (HW1 if x < X_JN else HE1)


def south_in(x):
    return Y_SW if x < X_TOWER0 else Y_SE


def north_in(x):
    return Y_NW if x < X_JN else Y_NE


def wall(name, a, b, zb=0.0, doors=(), thk=PART, h=None, **kw):
    """Partition a->b (C-local), thickness to the LEFT; doors = [(x_or_y_abs_along, width)] measured along a->b."""
    L = float(np.hypot(b[0] - a[0], b[1] - a[1]))
    if h is None:
        h = ceil_of(1 + int(round(zb / STOREY)))
    ops = [{"u0": round(u - w / 2 - 0.02, 3), "u1": round(u + w / 2 + 0.02, 3), "z0": z(zb - 0.06), "z1": z(zb + DOOR_H + 0.02)}
           for u, w in doors]
    assert all(0 < o["u0"] < o["u1"] < L for o in ops), (name, L, ops)
    return {"type": "int_wall", "name": name, "line": [c_to_w(*a), c_to_w(*b)], "z0": z(zb - 0.10), "z1": z(zb + h),
            "thk": thk, "openings": ops, "material": "white", **kw}


def door(name, a, b, u, zb=0.0, width=DOOR_W, leaf="glass2", **kw):
    d = {"type": "door", "name": name, "line": [c_to_w(*a), c_to_w(*b)], "u0": round(u - width / 2, 3),
         "u1": round(u + width / 2, 3), "z0": z(zb), "z1": z(zb + DOOR_H), "wall_thk": PART, "leaf": leaf,
         "mid": 1.0, "hinge": "left", "material": "metal"}
    d.update(kw)
    return d


def slab(name, x0, x1, y0, y1, z0, z1, material="stone", **kw):
    return {"type": "slab", "name": name, "ring": ring(x0, x1, y0, y1), "z0": z(z0), "z1": z(z1), "material": material, **kw}


# x bands where the south/north inner faces are constant (for slabs and ceilings)
BANDS = [("W", X_W, FRONT_W), ("M1", FRONT_W, X_TOWER0 - T), ("M2", X_TOWER0 - T, X_JN), ("M3", X_JN, FRONT_E), ("E", FRONT_E, X_E)]


def band_y(x0, x1):
    xm = (x0 + x1) / 2
    y0 = Y_SW if x1 <= X_TOWER0 - T + 1e-6 else Y_SE
    return y0, north_in(xm)


def floor_slabs(k, zb, holes):
    els, t = [], "terrazzo" if k == 1 else "stone"
    z0 = zb - (0.15 if k == 1 else SLAB)
    for nm, x0, x1 in BANDS:
        y0, y1 = band_y(x0, x1)
        side = nm if nm in ("W", "E") else None
        if side and holes.get(side):
            h0, h1 = hall((x0 + x1) / 2)
            yb = h0 + (COR - LANDING - (RISERS - 1) * TREAD)
            els.append(slab(f"F{k}_Slab_{nm}_S", x0, x1, y0, yb + 0.02, z0, zb, t))
            els.append(slab(f"F{k}_Slab_{nm}_N", x0, x1, h1 + 0.02, y1, z0, zb, t))
        else:
            els.append(slab(f"F{k}_Slab_{nm}", x0, x1, y0, y1, z0, zb, t))
    for e in els:
        e.update(ev(f"F{k} floor slab over the grown plan; openings over the stair bays the stair reaches"))
    return els


def ceilings(k, zb, open_bays):
    els, CEIL = [], ceil_of(k)
    for nm, x0, x1 in BANDS:
        y0, y1 = band_y(x0, x1)
        h0, h1 = hall((x0 + x1) / 2)
        if nm in ("W", "E") and open_bays.get(nm):
            parts = [(f"{nm}_S", y0, h0), (f"{nm}_N", h1, y1)]
        else:
            parts = [(nm, y0, y1)]
        for pn, a, b in parts:
            # the hall strip gets its own, higher grid; split the band where the hall faces jog (X_JS / X_JN)
            cuts = sorted({x0, x1} | {c for c in (X_JS, X_JN) if x0 < c < x1})
            for i, (c0, c1) in enumerate(zip(cuts, cuts[1:])):
                h0, h1 = hall((c0 + c1) / 2)
                sub = f"{pn}{'' if len(cuts) == 2 else '_' + str(i)}"
                for nm, ya, yb, zc in ((sub + "_S", a, min(b, h0 - PART), CEIL), (sub + "_Hall", max(a, h0), min(b, h1), cor_ceil_of(k)),
                                       (sub + "_N", max(a, h1 + PART), b, CEIL)):
                    if yb - ya > 0.01:
                        els.append(slab(f"F{k}_Ceiling_{nm}", c0, c1, ya, yb, zb + zc, zb + zc + 0.02, "white", slot="M_Ceiling_Tile_600",
                                        **ev(f"600x600 lay-in grid ceiling at {zc:.2f} m ({'corridor' if 'Hall' in nm else 'reference room'})")))
    return els


STAIR_FINISH = {"slot": "M_Granite_Pink", "side_slot": "M_Paint_White"}   # pinkish granite treads, white painted strings (003/138, X0-08)


def stair_storey(prefix, x_wall, sgn, zb, solid, top_floor):
    """U-stair storey at a hall end (x_wall = inner face of the end wall, sgn +1 west end / -1 east end)."""
    h0, h1 = hall(x_wall + sgn * 1.0)
    runin = COR - LANDING - (RISERS - 1) * TREAD
    els = []
    xa = x_wall + sgn * (FLIGHT_W + WELL + FLIGHT_W / 2)
    xb = x_wall + sgn * (FLIGHT_W / 2)
    x_front = x_wall + sgn * STAIR_X
    x_in1 = x_wall + sgn * (FLIGHT_W + WELL)
    x_in2 = x_wall + sgn * FLIGHT_W
    y_bot = h0 + runin
    y_land = y_bot + (RISERS - 1) * TREAD
    top1 = zb + BOTTOM_RISER + (RISERS - 1) * RISER_H
    f1 = {"type": "stairs_run", "name": f"{prefix}_Flight1", "top": c_to_w(xa, y_land), "dir_deg": NORTH + 180,
          "width": FLIGHT_W, "risers": RISERS, "riser_h": round(RISER_H, 4), "tread": TREAD, "z_top": z(top1),
          "bottom_riser_h": round(BOTTOM_RISER, 4), "material": "granite", **STAIR_FINISH, **ev("U-stair flight 1 (hall photo layout, 3.45 m storey)")}
    if not solid:
        f1["soffit_thk"] = SOFFIT
    else:   # ground-floor flight and landing stand on the slab top (sunk into it their faces lay on the slab edges)
        f1["z_base"] = z(zb)
    els.append(f1)
    xs = sorted([x_wall, x_front])
    # half-landing: white plastered body, beige granite top like the treads (138: the landing side under the flight is
    # white, not stone)
    els.append(slab(f"{prefix}_Landing", xs[0], xs[1], y_land, h1, zb if solid else top1 - 0.2, top1 - 0.03, "white",
                    slot="M_Paint_White", **ev("half-landing against the north hall wall")))
    els.append(slab(f"{prefix}_LandingTop", xs[0], xs[1], y_land, h1, top1 - 0.03, top1, "granite", slot="M_Terrazzo_Grey_Tile",
                    **ev("terrazzo half-landing top, granite treads (video 080011086, 2026-10-04 X0-08)")))
    # flight 2 has one riser less (10, D2): its foot is one tread short of the landing, which runs on under it
    els.append(slab(f"{prefix}_LandingExt", *sorted([x_wall, x_in2]), y_land - TREAD, y_land, zb if solid else top1 - 0.2, top1,
                    "granite", slot="M_Terrazzo_Grey_Tile", **ev("half-landing under the foot of flight 2 (10 risers, D2)")))
    els.append({"type": "stairs_run", "name": f"{prefix}_Flight2", "top": c_to_w(xb, y_bot), "dir_deg": NORTH,
                "width": FLIGHT_W, "risers": RISERS2, "riser_h": round(RISER_H, 4), "tread": TREAD,
                "z_top": z(zb + STOREY), "material": "granite", **STAIR_FINISH, "soffit_thk": SOFFIT, **ev("U-stair flight 2")})
    # white steel balustrade (138): 40 mm posts at the ends / joints, round-ish 40 mm handrail, a bottom rail 0.10 over
    # the nosing line and 20 mm bars at ~0.20 m standing on it
    rail = {"height": 0.95, "spacing": 0.20, "mid_rails": 0, "post": 0.04, "bar": 0.02, "rail": 0.04, "bottom_rail": 0.10,
            "material": "white"}
    rev = ev("white steel balustrade")
    els.append({"type": "rail3d", "name": f"{prefix}_Rail1", **rail, **rev,
                "points": [c_to_w(x_front - sgn * 0.05, y_bot + TREAD) + [z(zb + BOTTOM_RISER + RISER_H)],
                           c_to_w(x_front - sgn * 0.05, y_land) + [z(top1)], c_to_w(x_front - sgn * 0.05, h1 - 0.05) + [z(top1)]]})
    els.append({"type": "rail3d", "name": f"{prefix}_Rail1W", **rail, **rev,
                "points": [c_to_w(x_in1 - sgn * 0.05, y_bot + TREAD) + [z(zb + BOTTOM_RISER + RISER_H)],
                           c_to_w(x_in1 - sgn * 0.05, y_land) + [z(top1)], c_to_w(x_in2 + sgn * 0.05, y_land) + [z(top1)],
                           c_to_w(x_in2 + sgn * 0.05, y_bot) + [z(zb + STOREY)], c_to_w(x_in2 + sgn * 0.05, y_bot - 0.30) + [z(zb + STOREY)]]})
    if top_floor:
        zt = zb + STOREY
        els.append({"type": "rail3d", "name": f"{prefix}_TopGuard", **rail, **rev,
                    "points": [c_to_w(x_in2 + sgn * 0.05, y_bot - 0.05) + [z(zt)], c_to_w(x_front - sgn * 0.05, y_bot - 0.05) + [z(zt)],
                               c_to_w(x_front - sgn * 0.05, h1 - 0.05) + [z(zt)]]})
    return els


# rooms: (south, north) numbers per floor, door x per room (owner 2026-09-29: 105/106 doors at their east end, 101 at
# its west end by the lobby; end rooms next to the stairs as before)
# door centre 0.45 + 0.45 m from the board-side partition face (C105: opening 0.45 m from the board-wall corner)
DOOR_OFF = PART / 2 + 0.60 + DOOR_W / 2         # frame 0.60 off the board wall = 0.45 off the 0.15 pilaster (2026-10-04 D2 X0-05)
DOOR_S = {"S1": P1 - DOOR_OFF, "S2": P2 - DOOR_OFF, "S4": P3 + DOOR_OFF, "S5": P4 + DOOR_OFF}   # 107/108 east ends, 101/102 west ends
DOOR_N = {"N1": P1 - DOOR_OFF, "N2": P2 - DOOR_OFF, "N4": P3 + DOOR_OFF, "N5": P4 + DOOR_OFF}   # 106/105 east ends, 104/103 west ends
DOOR_TEACH = (P2 + P3) / 2
# leaf hinge side along the wall line (CI001/CI003/CK018, 2026-10-04 X0-04): the leaf hangs on the jamb away from the board
# corner; "left" puts S doors on the W jamb and N doors (lines run E->W) on the E jamb
HINGE = {"S4": "right", "S5": "right", "N1": "right", "N2": "right"}
WC_DOORS = [(P2 + 0.1 + WC_W / 2, "WC4"), (P_WCM + 0.1 + WC_W / 2, "WC5")]
NUMBERS = {1: {"S1": "107", "S2": "108", "S4": "101", "S5": "102", "N1": "106", "N2": "105", "N4": "104", "N5": "103"}}
for k in (2, 3, 4):
    NUMBERS[k] = {"S1": f"{k}01", "S2": f"{k}02", "S4": f"{k}03", "S5": f"{k}04", "N1": f"{k}08", "N2": f"{k}07",
                  "N4": f"{k}06", "N5": f"{k}05"}


def plan(k, zb, lobby, west_stair):
    P, els, CEIL = f"F{k}_", [], ceil_of(k)
    CC = cor_ceil_of(k)                       # hall walls run 3 cm into the (higher) corridor grid slab (its top is +0.02)
    num = NUMBERS[k]
    # south hall wall: west part (to the lobby's east wall), jog, east part; F1 leaves the lobby front open
    sw = [(DOOR_S["S1"], "S1"), (DOOR_S["S2"], "S2")] + ([] if lobby else [(DOOR_TEACH, "T")])
    se = [(DOOR_S["S4"], "S4"), (DOOR_S["S5"], "S5")]
    # the jogs are centred on X_JS / X_JN: each straight part ends on the jog's face where it would run into the jog,
    # and runs over the jog's width where it closes the outer corner (no overlaps, no notch)
    segs = [("Hall_S_West", (X_W, HW0 - PART), ((P2 + PART / 2) if lobby else X_JS - PART / 2, HW0 - PART), sw),   # F1: to the partition face (the lining closes the corner, Y0-g)
            ("Hall_S_East", (X_JS - PART / 2, HE0 - PART), (X_E, HE0 - PART), se)]
    for nm, a, b, dd in segs:
        els.append(wall(P + nm, a, b, zb, doors=[(x - a[0], DOOR_W) for x, _ in dd], h=CC + 0.03, **ev("south hall wall")))
        for x, key in dd:
            lab = "teachers' room over the lobby" if key == "T" else f"room {num[key]}"
            els.append(door(f"{P}Door_{key}", a, b, x - a[0], zb, hinge=HINGE.get(key, "left"), **ev(f"door of {lab}")))
    # int_wall lines are a FACE with the thickness to their left: partitions/jogs are offset by PART / 2 so they sit
    # centred on their plan lines (the room / WC frames and the asserts assume centred walls)
    if lobby:   # lobby side linings: lobby 3.76 clear between the storefront edges (D2 X0-05)
        evl = ev("lobby side wall lining to the 3.76 m clear width (2026-10-04 D2 X0-05)", "medium")
        els.append(wall(P + "Lobby_Lining_W", (LOBBY_X0, Y_SW), (LOBBY_X0, HW0), zb, thk=LOBBY_X0 - P2 - PART / 2, h=CC + 0.03, **evl))
        els.append(wall(P + "Lobby_Lining_E", (P3 - PART / 2, Y_SE), (P3 - PART / 2, HE0), zb, thk=P3 - PART / 2 - LOBBY_X1, h=CC + 0.03, **evl))
    els.append(wall(P + "Hall_S_Jog", (X_JS + PART / 2, HW0 - PART), (X_JS + PART / 2, HE0 - PART), zb, thk=PART, h=CC + 0.03, **ev("south hall wall jog 1.3 m (mirrors the facade step)")))
    # north hall wall: west part to the WC mid wall, jog, east part (east->west so the thickness goes north)
    nw = [(DOOR_N["N1"], "N1", DOOR_W), (DOOR_N["N2"], "N2", DOOR_W), (WC_DOORS[0][0], WC_DOORS[0][1], WC_DOOR_W)]
    ne = [(WC_DOORS[1][0], WC_DOORS[1][1], WC_DOOR_W), (DOOR_N["N4"], "N4", DOOR_W), (DOOR_N["N5"], "N5", DOOR_W)]
    for nm, a, b, dd in (("Hall_N_West", (X_JN + PART / 2, HW1 + PART), (X_W, HW1 + PART), nw), ("Hall_N_East", (X_E, HE1 + PART), (X_JN + PART / 2, HE1 + PART), ne)):
        els.append(wall(P + nm, a, b, zb, doors=[(a[0] - x, w) for x, _, w in dd], h=CC + 0.03, **ev("north hall wall; one WC stands forward of the other (owner)")))
        for x, key, w in dd:
            wc = key.startswith("WC")
            els.append(door(f"{P}Door_{key}", a, b, a[0] - x, zb, width=w, leaf="solid" if wc else "glass2", hinge=HINGE.get(key, "left"),
                            **ev("WC door, solid black leaf" if wc else f"door of room {num[key]}")))
    els.append(wall(P + "Hall_N_Jog", (X_JN - PART / 2, HE1 + PART), (X_JN - PART / 2, HW1 + PART), zb, h=CC + 0.03, **ev("north hall wall jog at the WC mid wall (owner)")))
    # partitions
    for x in (P1, P2, P3, P4):
        if lobby or x not in (P2, P3) or True:
            h0 = hall(x - 0.01)[0] if x != P3 else HE0
            els.append(wall(f"{P}Room_S_{x:.2f}", (x + PART / 2, south_in(x)), (x + PART / 2, HW0 - PART if x <= X_JS else HE0 - PART), zb,
                            **ev("room partition, reference 5.80 m rooms / lobby 4.5 m")))
    for x in (P1, P2, P_WCM, P3, P4):
        yh = (HW1 if x < X_JN else HE1) + PART
        els.append(wall(f"{P}Room_N_{x:.2f}", (x - PART / 2, north_in(x + (0.01 if x == P_WCM else 0))), (x - PART / 2, yh), zb,
                        **ev("room / WC partition")))
    # F4: west hall end holds a teachers' room with 2 end-wall windows instead of the stair (owner)
    if not west_stair:
        xf = FRONT_W + 0.4
        p, q = (xf, HW0), (xf, HW1)
        els.append(wall(f"{P}Teach_W_Front", p, q, zb, doors=[(COR / 2, DOOR_W)], **ev("F4: teachers' room at the west hall end, 2 windows (owner)")))
        els.append(door(f"{P}Door_Teach_W", p, q, COR / 2, zb, **ev("F4 teachers' room door")))
    # perimeter bulkhead along the corridor walls is not modelled here (rooms only); hall bulkheads at the stair zones
    for side, xf, sg in (("W", FRONT_W, 1), ("E", FRONT_E, -1)):
        if side == "W" and not west_stair:
            continue
        h0, h1 = hall(xf + sg * 4.0)
        # E: over the P4 line, 0.59 wide, underside 2.72 (CC010 PnP, 2026-10-04 Y0-b); W as measured in round 1 (CI003)
        xb, hw, zu = (xf + 4.05, 0.2, COR_BEAM_Z) if side == "W" else (FRONT_E - 3.07, 0.295, 2.72)
        els.append(slab(f"{P}Hall_Bulkhead_{side}", xb - hw, xb + hw, h0, h1, zb + zu, zb + CC, "white",
                        **ev("plasterboard bulkhead across the hall in front of the stair zone")))
    for x in (P2, X_JS):
        h0, h1 = hall(x + 0.01)
        els.append(slab(f"{P}Hall_Beam_{x:.1f}", x - 0.2, x + 0.2, min(hall(x - 0.01)[0], h0), max(hall(x - 0.01)[1], h1),
                        zb + COR_BEAM_Z, zb + CC, "white", **ev("bulkheads crossing the hall at the lobby sides, underside 2.66 (003)")))
    # blue accent paint (2026-10-03 Q3-17 F1 CI/CK + Q0-06 F3 B026-B040, supersedes the end-room L/R panels): a frame-wide
    # panel over every classroom door from the head to the ceiling; on F1 room 103 (N5) the blue also runs from its east
    # jamb to the stair-front corner, where the fire-hose cabinet hangs. Around the WC doors the wall is blue (owner).
    hall_doors = [(key, DOOR_S[key], False) for key in ("S1", "S2", "S4", "S5")] + \
                 [(key, DOOR_N[key], True) for key in ("N1", "N2", "N4", "N5")] + ([] if lobby else [("T", DOOR_TEACH, False)])
    blue = [(P2 + 0.1, P_WCM, True), (X_JN + PART / 2, P3 - 0.1, True)]   # full-height blue ranges (x0, x1, north) for skins
    if k == 1:                                                          # F1 WC zone as photographed (Q2-10, below)
        blue = [(X_JN + PART / 2, DOOR_N["N4"] + DOOR_W / 2 + 0.06, True)]
    evq = ev("periwinkle-blue panel over the classroom door, head to ceiling (2026-10-03 Q3-17 / Q0-06)",
             "high" if k in (1, 3) else "low")
    zt = DOOR_H + 0.02
    for key, x, north in hall_doors:
        yy = (hall(x)[1] - 0.01) if north else (hall(x)[0] + 0.01)
        parts = [("T", x - DOOR_W / 2, x + DOOR_W / 2, zt, CC - 0.02)]
        if k == 1 and key == "N5":
            parts.append(("R", x + DOOR_W / 2 + 0.02, FRONT_E, 0.1, CC - 0.02))
            blue.append((x + DOOR_W / 2 + 0.02, FRONT_E, True))
        for nm, u0, u1, z0_, z1_ in parts:
            els.append({"type": "box", "name": f"{P}Accent_{key}_{nm}", "center": c_to_w((u0 + u1) / 2, yy), "dir_deg": EAST,
                        "size": [round(u1 - u0, 3), 0.02, round(z1_ - z0_, 3)], "z0": z(zb + z0_), "material": "accent", **evq})

    def on_blue(xa, xb, north):
        return any(n == north and xa < b1 and xb > b0 for b0, b1, n in blue)
    # black room plate (KOCH number) on the frame side of every classroom door at FFL+1.70 (Q0-06; side assumed: +x)
    for key, x, north in hall_doors:
        xp = x + DOOR_W / 2 + 0.02 + 0.10
        off = 0.02 if on_blue(xp - 0.06, xp + 0.06, north) else 0.0     # in front of the blue paint skin
        yy = (hall(x)[1] - off - 0.005) if north else (hall(x)[0] + off + 0.005)
        rn = num.get(key, f"{k}09")
        els.append({"type": "box", "name": f"{P}RoomPlate_{key}", "center": c_to_w(xp, yy),
                    "dir_deg": EAST, "size": [0.12, 0.01, 0.16], "z0": z(zb + 1.62), "material": "metal",
                    "slot": "M_Plastic_Black", "ue_asset": "room_plate", "content": f"KOCH {rn}",
                    **ev("black room plate beside the classroom door at ~1.7 m (2026-10-03 Q0-06)", "low")})
    # F1: black linear wall lamps at 2.45, one per classroom door, 1.12 m east of the frame (Q3-19; count unsure)
    if k == 1:
        for key, x, north in hall_doors:
            if key in ("S1", "N2", "N5", "S5"):        # photographed without a lamp (CC010/CC011/CI003, 2026-10-04 Y0-k)
                continue
            xl = x + DOOR_W / 2 + 1.12 + 0.175
            off = 0.02 if on_blue(xl - 0.175, xl + 0.175, north) else 0.0
            yy = (hall(x)[1] - off - 0.04) if north else (hall(x)[0] + off + 0.04)
            els.append({"type": "box", "name": f"{P}Hall_WallLamp_{key}", "center": c_to_w(xl, yy), "dir_deg": EAST,
                        "size": [0.35, 0.08, 0.06], "z0": z(zb + 2.45), "material": "metal", "slot": "M_Steel_Paint_Dark",
                        "ue_asset": "wall_light_linear_black", **ev("black linear wall lamp at ~2.45 (2026-10-03 Q3-19)", "low")})
    # WC accent walls: same paint-round-the-opening rule (a full panel hid both WC doors, owner 2026-10-03). F1 as
    # photographed (Q2-10 CC/CI): WC4 only a 1.10 panel over its door; the WC5 recess blue full height from the jog face
    # to the 104 (N4) door frame and 0.22 past it; F2+ (not photographed) keep the paint-round rule.
    wcs = ((P2 + 0.1, P_WCM, HW1 - 0.01), (X_JN + PART / 2, P3 - 0.1, HE1 - 0.01))
    if k == 1:
        evw = ev("F1 WC zone blue as photographed (2026-10-03 Q2-10)", "medium")
        xd4, xd5, x4 = WC_DOORS[0][0], WC_DOORS[1][0], DOOR_N["N4"]
        o0, o1 = xd5 - WC_DOOR_W / 2 - 0.02, xd5 + WC_DOOR_W / 2 + 0.02
        for nm, u0, u1, z0_, z1_, yy in (("WC4_T", xd4 - 0.45, xd4 + 0.45, zt, CC - 0.1, HW1 - 0.01),
                                         ("WC5_L", X_JN + PART / 2, o0, 0.1, CC - 0.1, HE1 - 0.01),
                                         ("WC5_T", o0, o1, zt, CC - 0.1, HE1 - 0.01),
                                         ("WC5_R", o1, x4 - DOOR_W / 2, 0.1, CC - 0.1, HE1 - 0.01),
                                         ("N4_R", x4 + DOOR_W / 2, x4 + DOOR_W / 2 + 0.06, 0.1, CC - 0.1, HE1 - 0.01)):
            els.append({"type": "box", "name": f"{P}Accent_{nm}", "center": c_to_w((u0 + u1) / 2, yy), "dir_deg": EAST,
                        "size": [round(u1 - u0, 3), 0.02, round(z1_ - z0_, 3)], "z0": z(zb + z0_), "material": "accent", **evw})
        els.append({"type": "box", "name": f"{P}Accent_Jog", "center": c_to_w(X_JN + PART / 2 + 0.01, (HW1 + HE1) / 2),
                    "dir_deg": NORTH, "size": [round(HE1 - HW1, 3), 0.02, round(CC - 0.2, 3)], "z0": z(zb + 0.1),
                    "material": "accent", **evw})
    else:
        for (x0, x1, yy), (xd, _wc) in zip(wcs, WC_DOORS):
            o0, o1 = xd - WC_DOOR_W / 2 - 0.02, xd + WC_DOOR_W / 2 + 0.02
            for nm, u0, u1, z0_, z1_ in (("L", x0, o0, 0.1, CC - 0.1), ("R", o1, x1, 0.1, CC - 0.1), ("T", o0, o1, zt, CC - 0.1)):
                if u1 - u0 < 0.02:
                    continue
                els.append({"type": "box", "name": f"{P}Accent_WC_{x0:.1f}_{nm}", "center": c_to_w((u0 + u1) / 2, yy),
                            "dir_deg": EAST, "size": [round(u1 - u0, 3), 0.02, round(z1_ - z0_, 3)], "z0": z(zb + z0_),
                            "material": "accent", **ev("blue accent wall at the WC doors, painted round the door opening")})
    for n, x in enumerate((FRONT_W + 3.9, FRONT_E - 3.9)):
        els.append({"type": "box", "name": f"{P}Hall_Radiator_{n}", "center": c_to_w(x, hall(x)[1] - 0.06), "dir_deg": EAST,
                    "size": [0.8, 0.08, 0.55], "z0": z(zb + 0.15), "material": "white", **ev("sectional radiator on the north hall wall")})
    for n, x in enumerate(((P1 + P2) / 2, (P3 + P4) / 2)):
        yy = hall(x)[1] - 0.25
        els.append({"type": "bench", "name": f"{P}Hall_Bench_N{n}", "pos": c_to_w(x, yy), "dir_deg": NORTH + 180,
                    "length": 1.8, "depth": 0.40, "seat_h": 0.45, "back": False, "z": z(zb + (HALL_FIN if k > 1 else 0.0)), "slot": "M_Wood_Oak_Light",
                    "ue_asset": "bench_box_upholstered", **ev("hall bench: oak-orange wooden box base + black upholstered pad "
                                                              "(video V3-07); length 1.8 kept (>= 2.4 per V3-07, unsure)", "low")})
    els += hall_finish(k, zb, west_stair, lobby, [(x, DOOR_W, north) for _, x, north in hall_doors] +
                       [(xd, WC_DOOR_W, True) for xd, _ in WC_DOORS], blue)
    return els


HALL_FIN = 0.010     # F2+ corridor terrazzo tile on the slab (m)


def hall_finish(k, zb, west_stair, lobby, doors, blue):
    """Corridor finishes between the stair halls. F2-F4: light-grey terrazzo tiles wall face to wall face (Q0-07, F3
    B026-B033). All floors: grey terrazzo skirting 0.08 on both long walls, broken at the openings (Q0-07 / Q3-08). F1:
    two-tone walls, light greige up to 2.10 and white above, except where the wall is blue (Q3-18 CI; F2+ not seen, white).
    Pieces split at the jogs: the north face steps at X_JN + PART/2, the south face at X_JS - PART/2; F1 leaves the lobby
    front open. doors = [(x, width, north)], blue = [(x0, x1, north)] full-height accent ranges."""
    P, ev7 = f"F{k}_", ev("terrazzo tile floor + terrazzo skirting in the corridors (2026-10-03 Q0-07 / Q3-08)", "medium")
    fin = HALL_FIN if k > 1 else 0.0
    x0 = FRONT_W if west_stair else FRONT_W + 0.4
    xs = [x0, X_JN + PART / 2, LOBBY_X1 if lobby else X_JS - PART / 2, FRONT_E]
    ys = [(HW0, HW1), (HW0, HE1), (HE0, HE1)]
    floor, skirt, greige = [], [], []

    def it(xa, xb, ya, yb, za, zb_):
        cx, cy = c_to_w((xa + xb) / 2, (ya + yb) / 2)
        return [cx, cy, EAST, round(xb - xa, 4), round(yb - ya, 4), round(zb_ - za, 4), z(zb + za)]

    def runs(xa, xb, gaps):
        """[xa, xb] minus the gap intervals, pieces > 2 cm."""
        out, a = [], xa
        for g0, g1 in sorted(gaps) + [(xb, xb)]:
            if min(g0, xb) - a > 0.02:
                out.append((a, min(g0, xb)))
            a = max(a, g1)
        return out
    for (xa, xb), (ya, yb) in zip(zip(xs[:-1], xs[1:]), ys):
        if k > 1:
            floor.append(it(xa, xb, ya, yb, 0.0, HALL_FIN))
        for yf, north in ((ya, False), (yb, True)):
            ops = [(x - w / 2 - 0.02, x + w / 2 + 0.02) for x, w, n in doors if n == north]
            if lobby and not north:
                ops.append((LOBBY_X0, LOBBY_X1))                            # F1 lobby front: no wall
            sgn = -1 if north else 1
            for a, b in runs(xa, xb, ops):
                skirt.append(it(a, b, *sorted((yf, yf + sgn * 0.012)), fin, fin + 0.08))
            if k == 1:
                for a, b in runs(xa, xb, ops + [(b0, b1) for b0, b1, n in blue if n == north]):
                    greige.append(it(a, b, *sorted((yf, yf + sgn * 0.006)), 0.08, 2.10))
    out = [{"type": "boxes", "name": P + "Hall_Skirting", "items": skirt, "material": "white", "slot": "M_Terrazzo_Grey", **ev7}]
    if floor:
        out.append({"type": "boxes", "name": P + "Hall_Floor", "items": floor, "material": "white", "slot": "M_Terrazzo_Grey_Tile",
                    "ue_note": "tile module not measured (count tiles across the 5.8 m corridor)", **ev7})
    if greige:
        out.append({"type": "boxes", "name": P + "Hall_Dado_Paint", "items": greige, "material": "white", "slot": "M_Paint_Greige",
                    **ev("two-tone hall walls: light greige to 2.10, white above (2026-10-03 Q3-18 / Q2-09)", "medium")})
    return out


# --- reference classroom fit-out (C105, docs/reference/C105_etalon.png). Room frame: u from the back wall to the board
# wall (the board is on the door side), v from the door (corridor) wall to the window wall; L x D = 5.80 x 6.35.
ROOM_X = {"1": (X_W, P1 - PART / 2), "2": (P1 + PART / 2, P2 - PART / 2), "4": (P3 + PART / 2, P4 - PART / 2), "5": (P4 + PART / 2, X_E)}
BOARD_EAST = {"1": True, "2": True, "4": False, "5": False}
WIN_PAIR = (1.65, 4.25)        # window centres from the back wall (C105; facade pairs 2.59 m apart)
WIN_PAIR_KEY = {"N2": (1.65, 4.11)}   # R105 (and the rooms over it): 0.60 m gap to the east pier, not 0.74 (Q0-04 TG005/TG011)
WIN_W, WIN_SILL, WIN_H = 1.85, 1.15, 1.40   # facade window opening (BLD_C window type W, row F1 1.05 above the FFL)
LAM = 0.010      # laminate floor finish on the slab (m): wall skins and furniture stand on it, not in it
# room use (owner 2026-10-01, the timetable room list): PC labs 103 105 201 204 205; 207 vice principal; 307 405 408
# teachers' offices; 409 director (over the lobby); every other room is a plain classroom (24 pupils + teacher)
LABS = {1: ("N5", "N2"), 2: ("S1", "S5", "N5")}
OFFICES = {2: {"N2": "vice"}, 3: {"N2": "teachers"}, 4: {"N5": "teachers", "N1": "teachers"}}


def room_kind(k, key):
    if key in LABS.get(k, ()):
        return "lab"
    return OFFICES.get(k, {}).get(key, "class")
CORNER_WIN = {"S1": 3.52, "S5": 25.90, "N1": 3.50, "N5": 25.88}   # one long-facade window in the corner rooms (facade fit)


def room_frame(key):
    """(to_c(u, v) -> C-local xy, su, sv): back wall / door wall of standard room key ('S1'..'N5')."""
    xa, xb = ROOM_X[key[1]]
    su = 1 if BOARD_EAST[key[1]] else -1
    x_back = xa if su > 0 else xb
    xm = (xa + xb) / 2
    if key[0] == "S":
        y_door, sv = (HW0 if xm < X_JS else HE0) - PART, -1
    else:
        y_door, sv = (HW1 if xm < X_JN else HE1) + PART, 1
    return (lambda u, v: (x_back + su * u, y_door + sv * v)), su, sv


for _k in ("S1", "S2", "S4", "S5", "N1", "N2", "N4", "N5"):      # every standard room is the reference room
    _xa, _xb = ROOM_X[_k[1]]
    _xm = (_xa + _xb) / 2
    _d = ((HW0 if _xm < X_JS else HE0) - PART - south_in(_xm)) if _k[0] == "S" else (north_in(_xm) - (HW1 if _xm < X_JN else HE1) - PART)
    assert abs(_xb - _xa - STD_L) < 1e-6 and abs(_d - STD_D) < 1e-6, (_k, _xb - _xa, _d)
assert abs(HW1 - HW0 - COR) < 1e-6 and abs(HE1 - HE0 - COR) < 1e-6


def facade_windows(key):
    """C-local x centres of the long-facade windows of room key."""
    if key in CORNER_WIN:
        return [CORNER_WIN[key]]
    to_c, su, _ = room_frame(key)
    return sorted(round(to_c(u, 0)[0], 3) for u in WIN_PAIR_KEY.get(key, WIN_PAIR))


def fitout(k, zb, num):
    els, C, L, D = [], ceil_of(k), STD_L, STD_D
    for key in ("S1", "S2", "S4", "S5", "N1", "N2", "N4", "N5"):
        to_c, su, sv = room_frame(key)
        R = f"F{k}_R{num[key]}_"
        d_u = EAST if su > 0 else EAST + 180
        d_v = NORTH if sv > 0 else NORTH + 180
        f_v, f_u = su * sv, -su * sv            # row "face" values for the +v / +u side (see b_desk_row)

        def bx(nm, u0, u1, v0, v1, z0, z1, mat="white", **kw):
            cx, cy = to_c((u0 + u1) / 2, (v0 + v1) / 2)
            els.append({"type": "box", "name": R + nm, "center": c_to_w(cx, cy), "dir_deg": EAST,
                        "size": [round(abs(u1 - u0), 3), round(abs(v1 - v0), 3), round(z1 - z0, 3)], "z0": z(zb + z0),
                        "material": mat, **kw})
        ref = ev("reference classroom C105 (150-153, plan v6)")
        PK = 0.006                                    # paint skin on the back / window walls (below): bulkheads sit on it
        # bulkheads and pilasters meet face to face (no overlaps, no gap at the back-door corner): the window beam ends on
        # the board-side pilaster, the back-door pilaster is as deep as the door-wall box (0.30)
        bx("WindowBeam", 0.25, L - 0.10, D - 0.50, D - PK, C - 0.20, C + 0.01, slot="M_Paint_White", **ref)
        bx("DoorBox", 0.15, L - 0.15, 0.0, 0.30, C - 0.25, C + 0.01, slot="M_Paint_White", **ref)
        # pilaster in the board/door corner, mirroring the back-door one (CI019 / CR013, 2026-10-04 Y0-i)
        bx("Pilaster_BoardDoor", L - 0.15, L, 0.0, 0.30, 0.0, C + 0.01, slot="M_Paint_White",
           **ev("pilaster in the board/door corner (102 / 204, Y0-i)", "medium"))
        bx("BackBox", PK, 0.20, 0.30, D - 0.50, C - 0.25, C + 0.01, slot="M_Paint_White", **ref)
        r105 = k == 1 and key == "N2"
        kind = room_kind(k, key)
        x0 = to_c(0, 0)[0]
        ud = ((DOOR_N if key[0] == "N" else DOOR_S)[key] - x0) * su            # door axis along u
        ud0, ud1 = ud - DOOR_W / 2 - 0.02, ud + DOOR_W / 2 + 0.02              # wall opening
        # the sage back wall wraps the back pilaster and the corner column in R105 (Q3-05 CK)
        bx("Pilaster_BackDoor", PK, 0.15, 0.0, 0.30, 0.0, C + 0.01, slot="M_Paint_Sage" if r105 else "M_Paint_White", **ref)
        bx("Column_BackWin", PK, 0.25, D - 0.50, D - PK, 0.0, C + 0.01, slot="M_Paint_Sage" if r105 else "M_Paint_White", **ref)
        # board wall (Q3-12, classroom 102 / lab 204): sage from v 1.54 to the window pilaster (sage too), white strip by the
        # door corner; R105's board wall is white (CK021). Other rooms assumed like 102 / 204.
        board_sage = not r105
        bx("Pilaster_BoardWin", L - 0.10, L, D - 0.60, D - PK, 0.0, C + 0.01, slot="M_Paint_Sage" if board_sage else "M_Paint_White", **ref)
        # lay-in ceiling (C105 tile metrology): T-grid on the measured seams - along u back box 0.20 + cut 0.28 + 8 x 0.60
        # + cut 0.52, along v door box 0.30 + cut 0.15 + 9 x 0.60 + window beam 0.50 - plus the wall angle on the box/beam
        # faces; 4 LED panels 600 x 600 in tiles u #1/#6 x v #2/#6 (153: front pair at u 4.08-4.68, v 1.65-2.25 / 4.05-4.65)
        LG = L - 0.20 if board_sage else L                   # the board-wall top box (Q3-12b) ends the grid
        us = [0.48 + 0.60 * i for i in range(9)] + [0.20, LG]
        vs = [0.45 + 0.60 * j for j in range(9)] + [0.30, D - 0.50]
        seg = [[c_to_w(*to_c(u, 0.30)), c_to_w(*to_c(u, D - 0.50))] for u in us] + \
              [[c_to_w(*to_c(0.20, v)), c_to_w(*to_c(LG, v))] for v in vs]
        els.append({"type": "rails", "name": R + "CeilingGrid", "segments": seg, "width": 0.024, "height": 0.012,
                    "z0": z(zb + C - 0.012), **ev("600 mm lay-in T-grid on the C105 seam layout")})
        for i, u0 in enumerate((1.08, 4.08)):
            for j, v0 in enumerate((1.65, 4.05)):
                bx(f"LED_{i}{j}", u0 + 0.012, u0 + 0.588, v0 + 0.012, v0 + 0.588, C - 0.015, C, mat="white",
                   slot="M_LED_Panel_600", ue_asset="led_panel_600", **ev("600 x 600 LED panel in a grid cell (C105 153/034-037)"))
        # board wall (2026-10-03 Q3-07, measured R105 CK / classroom 102 CL; Q0-08 superseded): labs a 1.63 m display high,
        # whiteboard 1.81 x 1.25, AC 0.99 wide; plain rooms a 75-inch interactive panel hung low. Fixed on the paint skin.
        LB = L - PK
        evt = ev("board-wall fittings measured in R105 / 102 (2026-10-03 Q3-07)", "high" if r105 else "medium")
        if kind == "lab":
            bx("TV", LB - 0.06, LB, 3.84 - 0.815, 3.84 + 0.815, 1.15, 2.05, mat="metal", slot="M_Plastic_Black", ue_asset="tv_75in", **evt)
            bx("Whiteboard", LB - 0.02, LB, 1.57 - 0.905, 1.57 + 0.905, 0.80, 2.05, slot="M_Plastic_White", ue_asset="whiteboard_180x120", **evt)
            if r105:   # split AC only in R105; none in 102 / 204 / the other rooms (2026-10-04 X0-06)
                bx("AC", LB - 0.245, LB, 5.20 - 0.495, 5.20 + 0.495, 2.40, 2.72, slot="M_AC_Casing", ue_asset="ac_split_indoor", **evt)
            bx("Socket_TV", LB - 0.02, LB, 3.78 - 0.08, 3.78 + 0.08, 0.88, 0.93, slot="M_Plastic_White", **evt)
        else:
            bx("TV", LB - 0.08, LB, 3.94 - 0.835, 3.94 + 0.835, 0.82, 1.83, mat="metal", slot="M_Plastic_Black",
               ue_asset="interactive_panel_75", **evt)
            bx("Whiteboard", LB - 0.02, LB, 1.79 - 0.905, 1.79 + 0.905, 0.74, 1.93, slot="M_Plastic_White", ue_asset="whiteboard_180x120", **evt)
        evs = ev("CCTV dome under the back box at the window-wall corner, 2 smoke detectors (2026-10-03 Q0-02 / Q3-03: R105, "
                 "102, 204; detector positions by tile count; other rooms assumed)", "medium" if r105 else "low")
        for n, uc in enumerate((1.98, 4.38)):                              # lay-in cell centres clear of the LED panels
            bx(f"Smoke_{n}", uc - 0.05, uc + 0.05, 3.10, 3.20, C - 0.05, C - 0.012, slot="M_Plastic_White", ue_asset="smoke_detector", **evs)
        bx("CCTV", 0.09, 0.21, D - 0.63, D - 0.51, C - 0.35, C - 0.25, slot="M_Plastic_White", ue_asset="cctv_dome", **evs)
        # radiators under the long-facade windows: 1.20 wide (~15 sections), top 0.87 (Q3-10)
        for n, xw in enumerate(facade_windows(key)):
            uw = (xw - x0) * su
            bx(f"Radiator_{n}", uw - 0.60, uw + 0.60, D - 0.14, D - 0.06, 0.30, 0.87, slot="M_Paint_White", ue_asset="radiator_sectional",
               **ev("sectional radiator 1.20 wide, top ~0.87 (2026-10-03 Q3-10)", "medium"))
        # interior finish of the outer walls (the shell's inner face carries the facade render and the maroon reveals):
        # window wall white with white reveals and PVC window boards, back wall sage green (C105 150/152, labs
        # 2026-10-01); the back wall of the end rooms is the outer end wall with one window at its middle
        sk, rv = [], round(X_W - 0.16 - 0.07, 3)

        def itm(u0, u1, v0, v1, z0, z1):
            cx, cy = to_c((u0 + u1) / 2, (v0 + v1) / 2)
            return [*c_to_w(cx, cy), EAST, round(abs(u1 - u0), 4), round(abs(v1 - v0), 4), round(z1 - z0, 4), z(zb + z0)]

        def face_skin(along, at, depth_dir, lo, hi, ops):
            """Skin boxes on a wall face: along = 'u' (face v = at) or 'v' (face u = at); depth_dir = +1/-1 into the room;
            ops = [(a0, a1)] window openings along the face (sill WIN_SILL, head WIN_SILL + WIN_H). Returns paint + trim."""
            paint, trim = [], []
            w0, w1 = sorted((at, at + depth_dir * 0.006))
            r0, r1 = sorted((at, at - depth_dir * rv))            # reveal, into the wall
            box_ = (lambda a0, a1, q0, q1, z0, z1: itm(a0, a1, q0, q1, z0, z1)) if along == "u" else \
                   (lambda a0, a1, q0, q1, z0, z1: itm(q0, q1, a0, a1, z0, z1))
            zt, zs, zh = C + 0.01, WIN_SILL, WIN_SILL + WIN_H
            a = lo
            for o0, o1 in sorted(ops) + [(hi, hi)]:
                if o0 - a > 0.005:
                    paint.append(box_(a, o0, w0, w1, LAM, zt))
                if o1 > o0:
                    paint += [box_(o0, o1, w0, w1, LAM, zs), box_(o0, o1, w0, w1, zh, zt)]
                    # lining inside the opening (on the shell's reveal faces, never coplanar with them), board on the sill
                    trim += [box_(o0, o0 + 0.006, r0, r1, zs + 0.02, zh), box_(o1 - 0.006, o1, r0, r1, zs + 0.02, zh),
                             box_(o0 + 0.006, o1 - 0.006, r0, r1, zh - 0.006, zh),
                             box_(o0, o1, *sorted((at + depth_dir * 0.04, at - depth_dir * rv)), zs, zs + 0.02)]
                a = max(a, o1)
            return paint, trim
        wops = [((xw - x0) * su - WIN_W / 2, (xw - x0) * su + WIN_W / 2) for xw in facade_windows(key)]
        p_w, t_w = face_skin("u", D, -1, 0.0, L, wops)
        end_room = key[1] in "15"
        p_b, t_b = face_skin("v", 0.0, 1, 0.0, D, [(D / 2 - WIN_W / 2, D / 2 + WIN_W / 2)] if end_room else [])
        # corner PC labs: the facade window wall is sage and the end (back) wall white (video 006 lab pan, 2026-10-03 V3-01);
        # the C105 reference (white window wall, sage back wall) holds for the other rooms
        # 2026-10-03 Q3-27: lab 204 (F2 SE) follows the C105 rule, so the swap stays only on the unidentified corner labs
        swap = kind == "lab" and end_room and not (k == 2 and key == "S5")
        for e_ in reversed(els):            # the back-wall top box takes the back wall's paint (2026-10-04 Y0-h)
            if e_["name"] == R + "BackBox":
                e_["slot"] = "M_Paint_White" if swap else "M_Paint_Sage"
                break
        if end_room:   # radiator under the end-wall window, toward the window wall (102 / 204, Y0-i)
            bx("Radiator_End", 0.06, 0.14, D / 2 + 0.20 - 0.40, D / 2 + 0.20 + 0.40, 0.30, 0.87, slot="M_Paint_White",
               ue_asset="radiator_sectional", **ev("radiator under the end-wall window (CI017 / CR004, Y0-i)", "medium"))
        els.append({"type": "boxes", "name": R + "WindowWall_Paint", "items": p_w, "material": "white",
                    "slot": "M_Paint_Sage" if swap else "M_Paint_White", **ref})
        els.append({"type": "boxes", "name": R + "BackWall_Paint", "items": p_b, "material": "white",
                    "slot": "M_Paint_White" if swap else "M_Paint_Sage", **ref})
        els.append({"type": "boxes", "name": R + "Window_Trim", "items": t_w + t_b, "material": "white", "slot": "M_PVC_White",
                    **ev("white reveals and PVC window boards (C105 152, labs 2026-10-01)")})
        # laminate floor (C105 152/153, C204, desk room 140-149)
        bx("Floor_Laminate", 0.0, L, 0.0, D, 0.0, LAM, slot="M_Laminate_Oak_Grey", **ref)
        SK, ST = LAM + 0.045, 0.012                         # laminate skirting top / depth (Q3-08)
        if board_sage:
            evbb = ev("bulkhead box along the top of the board wall, painted like the wall behind (2026-10-04 D2 Q3-12b)", "medium")
            bx("BoardBox_White", L - 0.20, L, 0.30, 1.54, C - 0.19, C + 0.01, slot="M_Paint_White", **evbb)
            bx("BoardBox_Sage", L - 0.20, L, 1.54, D - 0.60, C - 0.19, C + 0.01, slot="M_Paint_Sage", **evbb)
            els.append({"type": "boxes", "name": R + "BoardWall_Paint", "items": [itm(LB, L, 1.54, D - 0.60, SK, C - 0.19)],
                        "material": "white", "slot": "M_Paint_Sage",
                        **ev("board wall sage from v 1.54 to the window pilaster, white strip by the door (Q3-12)", "medium")})
        sk_items = [itm(0.15, ud0, 0.0, ST, LAM, SK), itm(ud1, L - 0.15, 0.0, ST, LAM, SK),    # door wall
                    itm(L - 0.15 - ST, L - 0.15, ST, 0.30, LAM, SK), itm(L - 0.15 - ST, LB, 0.30, 0.30 + ST, LAM, SK),   # board pilaster
                    itm(0.15, 0.15 + ST, ST, 0.30, LAM, SK), itm(PK, 0.15 + ST, 0.30, 0.30 + ST, LAM, SK),   # back-door pilaster
                    itm(PK, PK + ST, 0.30 + ST, D - 0.50 - ST, LAM, SK),                       # back wall
                    itm(PK, 0.25 + ST, D - 0.50 - ST, D - 0.50, LAM, SK), itm(0.25, 0.25 + ST, D - 0.50, D - PK - ST, LAM, SK),
                    itm(0.25 + ST, L - 0.10 - ST, D - PK - ST, D - PK, LAM, SK),                # window wall
                    itm(L - 0.10 - ST, L - 0.10, D - 0.60 - ST, D - PK - ST, LAM, SK), itm(L - 0.10 - ST, LB, D - 0.60 - ST, D - 0.60, LAM, SK),
                    itm(LB - ST, LB, 0.30 + ST, D - 0.60 - ST, LAM, SK)]                        # board wall
        els.append({"type": "boxes", "name": R + "Skirting", "items": sk_items, "material": "white", "slot": "M_Laminate_Oak_Grey",
                    **ev("laminate skirting 45 mm round the room, broken at the door (2026-10-03 Q3-08)", "medium")})
        # low white heating pipe along the board wall and the door wall's board end, 0.04 off the faces (Q3-15)
        els.append({"type": "boxes", "name": R + "HeatPipe", "items": [itm(LB - 0.07, LB - 0.04, 0.30, D - 0.60, 0.21, 0.24),
                                                                       itm(ud1, L - 0.15, 0.04, 0.07, 0.21, 0.24)],
                    "material": "white", "slot": "M_PVC_White", **ev("white heating pipe at ~0.21 (2026-10-03 Q3-15)", "medium")})
        evbin = ev("waste-paper basket in the board/door corner, light switch beside the door (2026-10-03 Q3-11)", "medium")
        els.append({"type": "disc", "name": R + "Bin", "pos": c_to_w(*to_c(L - 0.23, 0.45)), "r": 0.14, "z0": z(zb + LAM),
                    "z1": z(zb + LAM + 0.30), "seg": 16, "material": "white", "slot": "M_Plastic_Green", "ue_asset": "waste_bin_round", **evbin})
        bx("LightSwitch", L - 0.25, L - 0.17, 0.0, 0.02, 0.83, 0.91, slot="M_Plastic_White", ue_asset="light_switch_double", **evbin)
        door_left = su * sv < 0          # facing the board (+u) the door wall (v = 0) is on the left
        if kind == "class":
            # plain classroom (2026-09-30_C_interior 140-149; owner: 24 pupils + teacher): single desks 0.60 x 0.45 (orange
            # beech top, grey tube frame, wire shelf) in pairs, 3 pairs across x 4 rows, facing the board; separate chairs.
            # Teacher's desk 1.20 x 0.60 (oak, black steel frame) at the board on the window side; owner: door on the left
            # -> the teacher sits with his back to the board facing the class, otherwise with his back to the windows.
            dk = ev("plain classroom (photos 140-149, owner 2026-10-01): 4 rows x 3 pairs of single desks = 24 seats", "medium")
            for r, uc in enumerate((1.00, 1.95, 2.90, 3.85)):
                for c, vc in enumerate((1.25, 3.15, 5.05)):
                    row = {"dir_deg": d_v, "n": 2, "pitch": 0.60, "face": -f_u, "z": z(zb + LAM), **dk}
                    els.append({"type": "desk_row", "name": R + f"Desk_{r}{c}", "pos": c_to_w(*to_c(uc, vc)), "depth": 0.45, "height": 0.76,
                                "slot": "M_Laminate_Beech_Orange", "ue_asset": "school_desk_single_600", **row})
                    els.append({"type": "chair_row", "name": R + f"Chair_{r}{c}", "pos": c_to_w(*to_c(uc - 0.42, vc)),
                                "slot": "M_Plastic_Orange", "ue_asset": "school_chair_beech_tube", **row})
            if door_left:
                t = {"dir_deg": d_v, "face": f_u, "n": 1, "pitch": 1.20, "z": z(zb + LAM), **dk}
                tp, cp = to_c(L - 1.00, D - 1.15), to_c(L - 0.45, D - 1.15)
            else:
                t = {"dir_deg": d_u, "face": f_v, "n": 1, "pitch": 1.20, "z": z(zb + LAM), **dk}
                tp, cp = to_c(L - 1.00, D - 1.05), to_c(L - 1.00, D - 0.43)
            els.append({"type": "desk_row", "name": R + "TeacherDesk", "pos": c_to_w(*tp), "depth": 0.60,
                        "slot": "M_Wood_Oak_Light", "ue_asset": "teacher_desk_oak_steel_1200", **t})
            els.append({"type": "chair_row", "name": R + "TeacherChair", "pos": c_to_w(*cp), "ue_asset": "office_chair_iso_black", **t})
            # curtains (Q3-14 CL / 102): 2 near floor-length panels 0.60 wide per window on a white rail under the beam, also
            # at the end-wall window of the end rooms (under the back box)
            evc = ev("curtains 2 x 0.60 per window, ~floor length, white rail (2026-10-03 Q3-14)", "medium")
            for n, xw in enumerate(facade_windows(key)):
                uw = (xw - x0) * su
                bx(f"CurtainRail_{n}", max(0.26, uw - WIN_W / 2 - 0.30), min(L - 0.11, uw + WIN_W / 2 + 0.30), D - 0.16, D - 0.10,
                   C - 0.25, C - 0.20, slot="M_PVC_White", **evc)
                for sd in (-1, 1):
                    uc_ = uw + sd * WIN_W / 2
                    bx(f"Curtain_{n}{'LR'[sd > 0]}", uc_ - 0.30, uc_ + 0.30, D - 0.16, D - 0.10, 0.05, C - 0.25,
                       slot="M_Fabric_Curtain_Brown", ue_asset="curtain_panel_blackout", **evc)
            if end_room:
                bx("CurtainRail_End", 0.10, 0.16, D / 2 - WIN_W / 2 - 0.30, D / 2 + WIN_W / 2 + 0.30, C - 0.30, C - 0.25,
                   slot="M_PVC_White", **evc)
                for sd in (-1, 1):
                    vc_ = D / 2 + sd * WIN_W / 2
                    bx(f"Curtain_End{'LR'[sd > 0]}", 0.10, 0.16, vc_ - 0.30, vc_ + 0.30, 0.05, C - 0.30,
                       slot="M_Fabric_Curtain_Brown", ue_asset="curtain_panel_blackout", **evc)
        elif kind in ("teachers", "vice"):
            # staff office (owner: 207 vice principal, 307 / 405 / 408 teachers' offices; layout not photographed): desks
            # 1.40 x 0.70 with PCs along the back and window walls, cabinets along the door wall, a meeting table
            of = ev(f"{'vice principal' if kind == 'vice' else 'teachers'} office (owner room list 2026-10-01); layout assumed", "low")
            if kind == "teachers":
                desks = [("Desk_Back", (0.40, 2.30), d_v, f_u, 2), ("Desk_Win", (2.70, D - 0.40), d_u, -f_v, 2)]
            else:
                desks = [("Desk_Head", (L - 1.20, D - 1.40), d_v, f_u, 1)]
            for nm, (uu, vv), dd, fc, n in desks:
                o = {"dir_deg": dd, "n": n, "pitch": 1.40 if kind == "teachers" else 1.80, "face": fc, "z": z(zb + LAM), **of}
                els.append({"type": "desk_row", "name": R + nm, "pos": c_to_w(*to_c(uu, vv)), "depth": 0.70 if kind == "teachers" else 0.85,
                            "slot": "M_Wood_Oak_Light", "ue_asset": "office_desk_1400", **o})
                els.append({"type": "monitor_row", "name": R + nm + "_PC", "pos": c_to_w(*to_c(uu, vv)), **dict(o, z=z(zb + LAM + 0.75))})
                off = 0.62
                cp_ = (uu + off, vv) if dd == d_v else (uu, vv - off)
                els.append({"type": "chair_row", "name": R + nm + "_Chair", "pos": c_to_w(*to_c(*cp_)), "ue_asset": "office_chair_swivel", **o})
            bx("Cabinets", 0.40, 3.20, 0.04, 0.49, LAM, 1.95, slot="M_Laminate_White", ue_asset="office_cabinet_row", **of)
            mt = {"dir_deg": d_u, "n": 1, "pitch": 1.80, "face": f_v, "z": z(zb + LAM), **of}
            els.append({"type": "desk_row", "name": R + "MeetingTable", "pos": c_to_w(*to_c(2.60, 3.30)), "depth": 0.90,
                        "slot": "M_Wood_Oak_Light", "ue_asset": "meeting_table_1800", **mt})
            for sd in (-1, 1):
                els.append({"type": "chair_row", "name": R + f"MeetingChairs_{'AB'[sd > 0]}", "pos": c_to_w(*to_c(2.60, 3.30 + sd * 0.70)),
                            **dict(mt, n=3, pitch=0.60, face=sd * f_v), "ue_asset": "chair_visitor_black"})
        else:   # kind == "lab"
            # pleated blinds in top cassettes, one per light (type W lights 0.35 / 0.30 / 0.35 of the opening), on the sashes
            # just inside the frame (rv into the wall), also at the end-wall window (Q0-01 TG, Q3-04 CK, R201 Q2-08)
            evb = ev("white-cream pleated blinds per light in top cassettes, no curtains (2026-10-03 Q0-01 / Q3-04)", "high")
            LIGHTS = (("L", -0.885, -0.30), ("M", -0.255, 0.255), ("R", 0.30, 0.885))
            zb0, zb1 = WIN_SILL + 0.05, WIN_SILL + WIN_H - 0.08
            for n, xw in enumerate(facade_windows(key)):
                uw = (xw - x0) * su
                for nm, a0, a1 in LIGHTS:
                    bx(f"Blind_{n}_{nm}", uw + a0, uw + a1, D + rv - 0.04, D + rv - 0.02, zb0, zb1,
                       slot="M_Fabric_Pleated_Cream", ue_asset="pleated_blind", **evb)
                    bx(f"BlindBox_{n}_{nm}", uw + a0, uw + a1, D + rv - 0.045, D + rv - 0.015, zb1, zb1 + 0.04, slot="M_PVC_White", **evb)
            if end_room:
                for nm, a0, a1 in LIGHTS:
                    bx(f"Blind_End_{nm}", -rv + 0.02, -rv + 0.04, D / 2 + a0, D / 2 + a1, zb0, zb1,
                       slot="M_Fabric_Pleated_Cream", ue_asset="pleated_blind", **evb)
                    bx(f"BlindBox_End_{nm}", -rv + 0.015, -rv + 0.045, D / 2 + a0, D / 2 + a1, zb1, zb1 + 0.04, slot="M_PVC_White", **evb)
            if r105:
                # corridor wall (Q3-01 CK, supersedes Q0-05): from the back pilaster sage, then a white band 0.12 and an orange
                # stripe 0.105 rising towards the door (axis u 2.17 at the floor -> 4.59 under the door box, ~42 deg); white
                # from the stripe to the board corner. Both start above the skirting.
                ub, ut, z0s, zt_ = 2.17, 4.59, SK, C - 0.25
                tilt = math.degrees(math.atan2(ut - ub, zt_ - LAM))
                c_ = math.cos(math.radians(tilt))
                dw = (0.105 / 2 + 0.12 / 2) / c_                                   # white band axis, horizontally (-u)
                paint = []
                for i in range(20):                                      # sage up to the white band axis, steps hidden by it
                    za, zb_ = z0s + (zt_ - z0s) * i / 20, z0s + (zt_ - z0s) * (i + 1) / 20
                    ue = ub - dw + (ut - ub) * ((za + zb_) / 2 - LAM) / (zt_ - LAM)
                    paint.append(itm(0.15, ue, 0.0, PK, za, zb_))
                els.append({"type": "boxes", "name": R + "DoorWall_Paint", "items": paint, "material": "white",
                            "slot": "M_Paint_Sage", **ev("R105 corridor wall sage (Q3-01 / Q0-05)", "high")})
                ln = (zt_ - z0s) / c_ - 0.08                                       # ends inside the wall height
                zm = (z0s + zt_) / 2
                um = ub + (ut - ub) * (zm - LAM) / (zt_ - LAM)
                for nm, du, w, sl in (("Orange", 0.0, 0.105, "M_Paint_Orange"), ("White", -dw, 0.12, "M_Paint_White")):
                    bx(f"DoorWallStripe_{nm}", um + du - w / 2, um + du + w / 2, PK, PK + 0.004, zm - ln / 2, zm + ln / 2,
                       slot=sl, tilt_deg=round(su * tilt, 2),
                       **ev("orange stripe + white band on the corridor wall (2026-10-03 Q3-01 CK, Q0-05 B016)", "medium"))
            # black wall network cabinet with a glass door, white DB panel under it and a conduit, on the end (back) wall by
            # the corridor-corner pilaster (V3-03; heights Q3-02 R105: cabinet 1.60-2.05, panel 1.18-1.60)
            evn = ev("network cabinet 1.60-2.05 + DB panel 1.18-1.60 + conduit (2026-10-03 Q3-02; V3-03 read ~2.0)", "medium")
            bx("NetCabinet", PK, 0.45, 0.35, 0.95, 1.60, 2.05, slot="M_Steel_Paint_Dark", ue_asset="network_cabinet_wall_9u", **evn)
            bx("NetPanel", PK, 0.10, 0.50, 0.80, 1.18, 1.60, slot="M_Plastic_White", ue_asset="db_panel_meter", **evn)
            bx("NetConduit", PK, PK + 0.03, 0.60, 0.64, 0.90, 1.18, slot="M_PVC_White", **evn)
            # white PVC trunking along the door wall behind the wall row (Q3-06)
            bx("Trunking_Door", 0.20, 4.18, PK + 0.004, PK + 0.054, 0.78, 0.88, slot="M_PVC_White",
               **ev("PVC trunking at desk height behind the wall row (2026-10-03 Q3-06)", "low"))
            # 25 PCs (owner 2026-10-01, C105 150-153): one row of 5 against the door wall (users face the wall) + two
            # islands of 2 rows back to back (users on the outer sides); desks 0.80 x 0.60 from 0.40 m off the back wall.
            # Island axes 2.50 / 4.95 m from the door wall: ~0.62 m between back-to-back chair rows, 1.1 m to the window wall.
            lab = ev("lab layout C105 (owner 2026-10-01): wall row + 2 back-to-back islands, 5 x 5 PCs, desks 0.80 x 0.60", "medium")
            rows = [(0.32, f_v)] + [(c + d, f_v if d > 0 else -f_v) for c in (2.50, 4.95) for d in (-0.30, 0.30)]
            for r, (vc, face) in enumerate(rows):
                # the wall row starts 0.25 off the back wall (on the back-door pilaster): from 0.40 its 5th desk ran 0.14 m
                # into the door opening (door_qa 2026-10-03; door 0.45 m off the board-wall corner, C105)
                p = c_to_w(*to_c((0.20 if r == 0 else 0.40) + 5 * 0.40, vc))
                row = {"pos": p, "dir_deg": d_u, "n": 5, "pitch": 0.80, "face": face, "z": z(zb + LAM), **lab}
                els.append({"type": "desk_row", "name": R + f"Desks_{r}", "depth": 0.60, **row})
                els.append({"type": "monitor_row", "name": R + f"PCs_{r}", **dict(row, z=z(zb + LAM + 0.75))})
                sv_off = 0.62 if face == f_v else -0.62
                els.append({"type": "chair_row", "name": R + f"Chairs_{r}",
                            **dict(row, pos=c_to_w(*to_c((0.20 if r == 0 else 0.40) + 2.0, vc + sv_off)))})
            # teacher's desk (owner 2026-10-01): longer (1.40 x 0.60), it continues the window-side row of the second island
            # up to the board wall (end against the wall); the teacher sits with his back to the windows, PC in front
            tv = 4.95 + 0.30
            t = {"dir_deg": d_u, "face": f_v, "n": 1, "pitch": 1.40, "z": z(zb + LAM), **lab}
            tu = L - 0.79                                   # end 0.09 off the board wall: clear of its heating pipe (Q3-15)
            els.append({"type": "desk_row", "name": R + "TeacherDesk", "pos": c_to_w(*to_c(tu, tv)), "depth": 0.60, **t})
            els.append({"type": "monitor_row", "name": R + "TeacherPC", "pos": c_to_w(*to_c(tu, tv)), **dict(t, z=z(zb + LAM + 0.75))})
            els.append({"type": "chair_row", "name": R + "TeacherChair", "pos": c_to_w(*to_c(tu, tv + 0.62)), **t})
    return els


# --- WC fit-out (photos docs/reference/photos/2026-10-01_WC 029-045; single-view metrology on the 600 x 600 floor tiles,
# camera height 1.51 m, f 2850 px checked by VP orthogonality 89.2-89.8 deg). Frame per WC: a from the shared mid wall
# (wet wall: cubicles + sinks on it, back to back) towards its outer partition, b from the hall wall face to the north
# wall. Measured: aisle 1.04 (tile 0.60 from the outer wall + 0.455 cut), 3 cubicles to the north wall at a 1.10 m
# pitch (door frames 0.66-0.68 x ~2.0, outward, handle south / hinges north), wall tiles 600 x 600 (bottom row cut 0.35,
# band top 1.55, up to the sill under the window), white PVC strip ceiling 2.60 with a cornice, end window 0.52 x 1.10
# (sill 1.45, 0.80 m from the aisle wall to its axis), 7-section radiator 0.49 x 0.60 centred on the aisle, two pedestal
# basins in a 1.20 m alcove (031/040), mirror 1.10 x 0.60 at 1.21, inner door 0.76 frame (045) 0.55 m off the wet wall.
# Cubicle depth = what the 2.15 m WC leaves (1.00 m, outward doors): not visible in the photos.
WC_PASS, WC_FRONT_T, WC_PT = 1.05, 0.10, 0.10
WC_CUB_D = round(WC_W - WC_PASS - WC_FRONT_T, 3)
WC_CUBS = (1.05, 1.05, 1.00)            # clear widths from the alcove to the north wall (b ascending)
WC_ALCOVE, WC_ANTE = 1.20, 1.65         # sink alcove clear width; anteroom (lock) depth from the hall wall
WC_CEIL, WC_BAND, WC_TILE_T = 2.60, 1.56, 0.01
WC_ROWS = (0.36, 0.96, 2.16)      # wall tile seams above the floor (bottom row cut 0.35; 029 end wall 0.355 / 0.96 / 1.56; 2.16 in the cubicles)
WC_TILE, WC_GROUT, WC_FLOOR_CUT = 0.60, 0.003, 0.34   # tile, joint (m); floor row at the north wall cut to 0.34 (029)
WC_WIN_W, WC_WIN_SILL, WC_WIN_H = 0.50, 1.42, 1.13   # opening at the wall face (0.50: CW002-008, 2026-10-04 X0-07); head 2.55
WC_WIN_A = WC_CUB_D + WC_FRONT_T + WC_WIN_W / 2    # window axis: its jamb on the cubicle front line (0.775 off the aisle wall)
WC_CUB_DOOR, WC_IN_DOOR, WC_IN_DOOR_A0 = 0.70, 0.78, 0.55
WC_HALL_DOOR_A = WC_W / 2
WC_FLOOR_T = 0.012
WC_WIN_N = (P_WCM - PART / 2 - WC_WIN_A, P_WCM + PART / 2 + WC_WIN_A)   # C-local x of the WC4 / WC5 end windows


def wc_frame(i):
    """(pt(a, b) -> C-local xy, sa): WC i (0 = west / WC4, 1 = east / WC5)."""
    sa = -1 if i == 0 else 1
    xm = P_WCM + sa * PART / 2
    yh = (HW1 if i == 0 else HE1) + PART
    assert abs((Y_NW if i == 0 else Y_NE) - yh - STD_D) < 1e-6
    return (lambda a, b: (xm + sa * a, yh + b)), sa


def wc_fitout(k, zb):
    els = []
    D, C = STD_D, WC_CEIL
    b_alc0 = WC_ANTE + WC_PT
    b_blk = b_alc0 + WC_ALCOVE                          # block end wall south face
    cub = []                                            # (b0, b1) clear spans
    b = b_blk + WC_PT
    for n, w in enumerate(WC_CUBS):
        cub.append((b, b + w))
        b += w + (WC_PT if n < len(WC_CUBS) - 1 else 0.0)
    assert abs(b - D) < 1e-6 and WC_CUB_D > 0.95, (b, WC_CUB_D)
    a_fr = WC_CUB_D                                     # front wall: a_fr .. a_fr + WC_FRONT_T
    a_ps = a_fr + WC_FRONT_T                            # aisle starts
    wev = lambda t, c="medium": ev("WC (2026-10-01_WC photos): " + t, c)
    for i in (0, 1):
        pt, sa = wc_frame(i)
        W = lambda a, b_: c_to_w(*pt(a, b_))
        R = f"F{k}_WC{'WE'[i]}_"
        d_a = EAST if sa > 0 else EAST + 180

        def wall_ab(nm, p, q, side, h=C + 0.02, doors=(), thk=WC_PT, **kw):
            """Wall p->q (a, b), thickness towards +a/+b (side = (da, db) unit); doors [(centre along p->q from p, width)]."""
            A, B = np.array(pt(*p)), np.array(pt(*q))
            dvec = (B - A) / np.linalg.norm(B - A)
            want = np.array(pt(p[0] + side[0], p[1] + side[1])) - A
            left = np.array([-dvec[1], dvec[0]])
            L = float(np.linalg.norm(B - A))
            dd = list(doors)
            if left @ want < 0:                          # thickness must go to the left of the line: reverse it
                A, B, dd = B, A, [(L - u, w) for u, w in dd]
            line = (tuple(A), tuple(B))
            els.append(wall(R + nm, line[0], line[1], zb, doors=dd, thk=thk, h=h, **kw))
            return line, dd

        def bx(nm, a0, a1, b0, b1, z0, z1, slot, **kw):
            cx, cy = pt((a0 + a1) / 2, (b0 + b1) / 2)
            els.append({"type": "box", "name": R + nm, "center": c_to_w(cx, cy), "dir_deg": EAST,
                        "size": [round(abs(a1 - a0), 4), round(abs(b1 - b0), 4), round(z1 - z0, 4)], "z0": z(zb + z0),
                        "material": "white", "slot": slot, **kw})
        it = lambda a0, a1, b0, b1, z0, z1: [*c_to_w(*pt((a0 + a1) / 2, (b0 + b1) / 2)), EAST, round(abs(a1 - a0), 4),
                                                round(abs(b1 - b0), 4), round(z1 - z0, 4), z(zb + z0)]
        def lamp(nm, a_, b_, r, ue):
            els.append({"type": "disc", "name": R + nm, "pos": W(a_, b_), "r": r, "z0": z(zb + C - 0.065), "z1": z(zb + C), "seg": 64,
                        "slot": "M_Plastic_White", "ue_asset": ue, **wev(f"round LED ceiling lamp {2 * r:.2f} (029/032)")})
            els.append({"type": "disc", "name": R + nm + "_Diffuser", "pos": W(a_, b_), "r": r - 0.012, "z0": z(zb + C - 0.068),
                        "z1": z(zb + C - 0.02), "seg": 64, "slot": "M_Lamp_Diffuser", **wev("opal diffuser")})
        # floor tiles, PVC ceiling
        xa, xb = sorted((pt(0, 0)[0], pt(WC_W, 0)[0]))
        y0, y1 = pt(0, 0)[1], pt(0, D)[1]
        G = WC_GROUT / 2
        els.append(slab(R + "Floor_Grout", xa, xb, y0, y1, zb + 0.002, zb + WC_FLOOR_T - 0.006, "white", slot="M_Tile_Grout",
                        **wev("tile adhesive / grout bed under the floor tiles")))
        fl = []
        a_seams = sorted({WC_W} | {round(WC_W - WC_TILE * n, 4) for n in range(1, 5) if WC_W - WC_TILE * n > 0} | {0.0})
        b_seams = sorted({0.0, D} | {round(D - WC_FLOOR_CUT - WC_TILE * n, 4) for n in range(11) if D - WC_FLOOR_CUT - WC_TILE * n > 0})
        for a0, a1 in zip(a_seams, a_seams[1:]):
            for b0, b1 in zip(b_seams, b_seams[1:]):
                fl.append(it(a0 + G, a1 - G, b0 + G, b1 - G, WC_FLOOR_T - 0.006, WC_FLOOR_T))
        els.append({"type": "boxes", "name": R + "Floor_Tile", "items": fl, "material": "white", "slot": "M_Tile_Floor_600",
                    **wev("porcelain floor tiles 600 x 600, 3 mm joints, grid from the aisle wall, 0.34 cut row at the north wall (029)")})
        els.append(slab(R + "Ceiling_PVC", xa, xb, y0, y1, zb + C, zb + C + 0.01, "white", slot="M_PVC_Ceiling_Panel",
                        **wev("white PVC strip ceiling at 2.60, strips along the aisle (029/032)")))
        # walls: inner (lock) partition with its door, block end wall, cubicle front with 3 doors, cubicle partitions
        evw = wev("masonry partition, tiled to 1.55, painted above")
        in_u = WC_IN_DOOR_A0 + WC_IN_DOOR / 2
        ln_in, dd_in = wall_ab("Lock_Wall", (0, WC_ANTE), (WC_W, WC_ANTE), (0, 1), doors=[(in_u, WC_IN_DOOR)], **evw)
        wall_ab("Block_End", (0, b_blk), (a_ps, b_blk), (0, 1), **evw)
        cub_c = [(b0 + b1) / 2 for b0, b1 in cub]
        ln_fr, dd_fr = wall_ab("Cubicle_Front", (a_fr, b_blk + WC_PT), (a_fr, D), (1, 0),
                               doors=[(c - b_blk - WC_PT, WC_CUB_DOOR) for c in cub_c], thk=WC_FRONT_T, **evw)
        for n in range(len(cub) - 1):
            wall_ab(f"Cubicle_Part_{n}", (0, cub[n][1]), (a_fr, cub[n][1]), (0, 1), **evw)
        for n, (u, w) in enumerate(dd_fr):
            hinge = "left" if ln_fr[0][1] > ln_fr[1][1] else "right"         # hinges on the north jamb (029/037)
            els.append(door(f"{R}Cubicle_Door_{n}", ln_fr[0], ln_fr[1], u, zb, width=w, leaf="solid", hinge=hinge,
                            wall_thk=WC_FRONT_T, slot="M_PVC_Anthracite", frame_w=0.05,
                            **wev("anthracite PVC door, frame 0.70 x 2.00, opens out into the aisle (029/037/039)")))
        u, w = dd_in[0]
        els.append(door(f"{R}Lock_Door", ln_in[0], ln_in[1], u, zb, width=w, leaf="solid", slot="M_PVC_Anthracite",
                        wall_thk=WC_PT, **wev("anthracite PVC door, frame 0.76-0.78 (045), 0.55 m off the wet wall (040)")))
        # wall faces (a or b constant), room side, span, tile openings (along the span), under-window band
        T = WC_TILE_T
        o_hall = [(WC_HALL_DOOR_A - WC_DOOR_W / 2 - 0.02, WC_HALL_DOOR_A + WC_DOOR_W / 2 + 0.02)]
        o_in = [(WC_IN_DOOR_A0 - 0.02, WC_IN_DOOR_A0 + WC_IN_DOOR + 0.02)]
        o_fr = [(c - WC_CUB_DOOR / 2 - 0.02, c + WC_CUB_DOOR / 2 + 0.02) for c in cub_c]
        win = (WC_WIN_A - WC_WIN_W / 2, WC_WIN_A + WC_WIN_W / 2)
        faces = [("a", WC_W, -1, 0.0, WC_ANTE, []), ("a", WC_W, -1, b_alc0, D, []),          # aisle (outer) wall
                 ("a", 0.0, 1, 0.0, WC_ANTE, []), ("a", 0.0, 1, b_alc0, b_blk, []),           # wet wall
                 ("b", 0.0, 1, 0.0, WC_W, o_hall),                                            # hall wall
                 ("b", WC_ANTE, -1, 0.0, WC_W, o_in), ("b", b_alc0, 1, 0.0, WC_W, o_in),      # lock wall
                 ("b", b_blk, -1, 0.0, a_ps, []),                                             # block end (alcove side)
                 ("a", a_ps, 1, b_blk, D, o_fr),                                              # cubicle fronts, aisle side
                 ("b", D, -1, a_ps, WC_W, [])]                                                # north wall, aisle
        for (b0, b1), c in zip(cub, cub_c):                       # cubicle interiors: tiled to the cornice (video V2-05)
            faces += [("a", 0.0, 1, b0, b1, [], C - 0.05), ("a", a_fr, -1, b0, b1, [(c - WC_CUB_DOOR / 2 - 0.02, c + WC_CUB_DOOR / 2 + 0.02)], C - 0.05),
                      ("b", b0, 1, 0.0, a_fr, [], C - 0.05), ("b", b1, -1, 0.0, a_fr, [], C - 0.05)]
        tiles, grout, corn = [], [], []
        z_rows = [WC_FLOOR_T, *WC_ROWS, WC_BAND]
        for ax, pos, sd, lo, hi, ops, *top_ in faces:
            band = top_[0] if top_ else WC_BAND
            span = lambda u0, u1, w0, w1, z0, z1: it(w0, w1, u0, u1, z0, z1) if ax == "a" else it(u0, u1, w0, w1, z0, z1)
            g0, g1 = sorted((pos, pos + sd * 0.004))                 # grout / adhesive layer
            t0, t1 = sorted((pos + sd * 0.004, pos + sd * T))       # tile body
            c0, c1 = sorted((pos, pos + sd * 0.05))
            corn.append(span(lo, hi, c0, c1, C - 0.05, C))
            # columns: from the north wall along b, from the aisle wall along a (029 end wall: aligned with the floor)
            if ax == "a":
                cols = sorted({lo, hi} | {round(D - WC_TILE * n, 4) for n in range(12) if lo < D - WC_TILE * n < hi})
            else:
                cols = sorted({lo, hi} | {round(WC_W - WC_TILE * n, 4) for n in range(5) if lo < WC_W - WC_TILE * n < hi})
            pieces, u = [], lo
            for o0, o1 in sorted(o for o in ops if o[1] > lo and o[0] < hi) + [(hi, hi)]:
                if o0 - u > 0.005:
                    if ax == "b" and pos == D and u < win[1] and o0 > win[0]:                 # under the window: to the sill
                        pieces += [(s0, s1, zt) for s0, s1, zt in ((u, win[0], WC_BAND), (win[0], win[1], WC_WIN_SILL), (win[1], o0, WC_BAND)) if s1 - s0 > 0.005]
                    else:
                        pieces.append((u, o0, band))
                u = max(u, o1)
            for p0, p1, zt in pieces:
                grout.append(span(p0, p1, g0, g1, WC_FLOOR_T, zt))
                cc = sorted({p0, p1} | {c for c in cols if p0 < c < p1})
                zz = sorted({WC_FLOOR_T, zt} | {r for r in z_rows if WC_FLOOR_T < r < zt})
                for u0, u1 in zip(cc, cc[1:]):
                    for z0_, z1_ in zip(zz, zz[1:]):
                        if u1 - u0 > 0.01 and z1_ - z0_ > 0.01:
                            tiles.append(span(u0 + G, u1 - G, t0, t1, z0_ + G, z1_ - G))
        els.append({"type": "boxes", "name": R + "Wall_Tile", "items": tiles, "material": "white", "slot": "M_Tile_Wall_Grey",
                    **wev("porcelain wall tiles 600 x 600, 3 mm joints, rows 0.35 (cut) / 0.60 / 0.60 to 1.56 (029 end wall)")})
        els.append({"type": "boxes", "name": R + "Wall_Grout", "items": grout, "material": "white", "slot": "M_Tile_Grout",
                    **wev("tile adhesive / grout behind the wall tiles")})
        # north (outer) wall above the band: white paint skin and the window reveal lining (the shell's inner face is facade render)
        hd = WC_WIN_SILL + WC_WIN_H
        rv = round(X_W - 0.16 - 0.07, 3)                        # inner reveal depth (outer wall X_W = 0.45, frame at 0.16 + 0.07)
        pw = [it(win[1], WC_W, D - 0.006, D, WC_BAND, C), it(win[0], win[1], D - 0.006, D, hd, C),   # cubicle part (a < win[0]) is tiled
              it(win[0], win[0] + 0.006, D, D + rv, WC_WIN_SILL + 0.02, hd), it(win[1] - 0.006, win[1], D, D + rv, WC_WIN_SILL + 0.02, hd),
              it(win[0] + 0.006, win[1] - 0.006, D, D + rv, hd - 0.006, hd)]
        els.append({"type": "boxes", "name": R + "North_Paint", "items": pw, "material": "white", "slot": "M_Paint_White",
                    **wev("white paint above the tiles and in the window reveal (029)")})
        bx("Window_Sill", win[0], win[1], D - 0.03, D + rv, WC_WIN_SILL, WC_WIN_SILL + 0.02, "M_PVC_White",
           **wev("white PVC window board at the sill (029)"))
        els.append({"type": "boxes", "name": R + "Cornice", "items": corn, "material": "white", "slot": "M_PVC_White",
                    **wev("PVC ceiling cornice 50 x 50 (029/032)")})
        # sink alcove: 2 pedestal basins, taps, mirror, soap dispenser, bin, floor drain (031/040/043)
        bc = (b_alc0 + b_blk) / 2
        for n, db in enumerate((-0.29, 0.29)):
            els.append({"type": "sink", "name": f"{R}Sink_{n}", "pos": W(T + 0.235, bc + db), "dir_deg": d_a, "width": 0.52,
                        "depth": 0.45, "height": 0.85, "z": z(zb + WC_FLOOR_T), "ue_asset": "washbasin_pedestal_520",
                        **wev("pedestal basin 0.52 wide, rim 0.85 (031)")})
            els.append({"type": "disc", "name": f"{R}Tap_{n}", "pos": W(T + 0.07, bc + db), "r": 0.022, "z0": z(zb + 0.85), "z1": z(zb + 0.99),
                        "seg": 32, "slot": "M_Chrome", "ue_asset": "tap_monolever", **wev("monolever basin tap (031)")})
            bx(f"TapSpout_{n}", T + 0.07, T + 0.16, bc + db - 0.012, bc + db + 0.012, 0.955, 0.975, "M_Chrome", **wev("tap spout"))
            bx(f"TapLever_{n}", T + 0.05, T + 0.14, bc + db - 0.008, bc + db + 0.008, 1.00, 1.015, "M_Chrome", **wev("tap lever"))
        bx("Mirror", T, T + 0.006, bc - 0.55, bc + 0.55, 1.21, 1.81, "M_Mirror", **wev("frameless mirror 1.10 x 0.60, bottom 1.21 (031)"))
        bx("Soap", T, T + 0.10, bc - 0.05, bc + 0.05, 0.95, 1.20, "M_Plastic_White", ue_asset="soap_dispenser_wall", **wev("wall soap dispenser between the basins (031)"))
        bx("Bin", T + 0.06, T + 0.40, bc - 0.16, bc + 0.16, WC_FLOOR_T, 0.50, "M_Plastic_Black", ue_asset="bin_bag_black", **wev("bin with a black bag between the pedestals (031/040)"))
        bx("Drain", T + 0.04, T + 0.19, bc + 0.12, bc + 0.27, WC_FLOOR_T, WC_FLOOR_T + 0.003, "M_Steel_Galv", **wev("floor drain grate by the right pedestal (040)"))
        bx("Socket", WC_W - T - 0.02, WC_W - T, bc - 0.04, bc + 0.04, 1.58, 1.66, "M_Plastic_White", **wev("socket above the tile band opposite the basins (031/033)"))
        # cubicles (video pass 2026-10-03 V2-05): white squat pan set flush in the floor tiles, outlet to the back (wet) wall,
        # high-level plastic cistern on the back wall with a flush pipe down to the pan, tiled pipe box in the back corner,
        # jumbo roll dispenser, bin in the back corner (clear of the door), light switch outside by the handle
        PAN_A0, PAN_L, PAN_W = T + 0.12, 0.58, 0.44
        for n, ((b0, b1), c) in enumerate(zip(cub, cub_c)):
            bx(f"SquatPan_{n}", PAN_A0, PAN_A0 + PAN_L, c - PAN_W / 2, c + PAN_W / 2, WC_FLOOR_T - 0.004, WC_FLOOR_T + 0.004,
               "M_Ceramic_White", ue_asset="squat_pan_ceramic", **wev("squat pan flush in the floor, outlet to the back wall (video V2-05)"))
            for sg in (-1, 1):   # raised footrests either side of the bowl
                bx(f"SquatPan_{n}_Foot{'LR'[sg > 0]}", PAN_A0 + PAN_L - 0.28, PAN_A0 + PAN_L - 0.04, c + sg * 0.13 - 0.05,
                   c + sg * 0.13 + 0.05, WC_FLOOR_T + 0.004, WC_FLOOR_T + 0.016, "M_Ceramic_White", **wev("pan footrest"))
            bx(f"Cistern_{n}", T, T + 0.14, c - 0.20, c + 0.20, 1.85, 2.15, "M_Plastic_White", ue_asset="cistern_high_level",
               **wev("high-level plastic cistern on the back wall (height unsure, V2-05)", "low"))
            bx(f"FlushPipe_{n}", T + 0.02, T + 0.05, c - 0.015, c + 0.015, WC_FLOOR_T + 0.016, 1.85, "M_Plastic_White",
               **wev("flush pipe from the cistern down to the pan back (V2-05)", "low"))
            bx(f"PipeBox_{n}", T, T + 0.16, b1 - T - 0.16, b1 - T, WC_FLOOR_T, 1.20, "M_Tile_Wall_Grey",
               **wev("small tiled pipe box in the back corner (V2-05)", "low"))
            bx(f"PaperHolder_{n}", 0.62, 0.74, b1 - T - 0.27, b1 - T, 0.80, 1.07, "M_Plastic_White", ue_asset="jumbo_roll_dispenser",
               **wev("jumbo toilet-roll dispenser on the side wall (V2-05)", "low"))
            bx(f"CubBin_{n}", T + 0.02, T + 0.24, b0 + T + 0.03, b0 + T + 0.25, WC_FLOOR_T, 0.32, "M_Plastic_Grey",
               **wev("small bin in the back corner (039; V2-05)", "low"))
            bx(f"Switch_{n}", a_ps + T, a_ps + T + 0.015, c - WC_CUB_DOOR / 2 - 0.16, c - WC_CUB_DOOR / 2 - 0.08, 1.00, 1.08,
               "M_Plastic_White", **wev("light switch beside each cubicle door, handle side (029)"))
            lamp(f"CubLamp_{n}", a_fr / 2, c, 0.11, "ceiling_lamp_round_led_220")
        # lamps: aisle, alcove (+ air diffuser), lock; window radiator with pipes
        for nm, a_, b_, r in (("Lamp_Aisle", a_ps + WC_PASS / 2, (cub[1][0] + cub[2][1]) / 2, 0.165), ("Lamp_Alcove", 1.20, bc, 0.165),
                              ("Lamp_Lock", WC_W / 2, WC_ANTE / 2, 0.165)):
            lamp(nm, a_, b_, r, "ceiling_lamp_round_led_330")
        els.append({"type": "disc", "name": R + "Diffuser", "pos": W(0.60, bc), "r": 0.08, "z0": z(zb + C - 0.025), "z1": z(zb + C),
                    "slot": "M_Plastic_White", **wev("round extract air diffuser 0.16 (032)")})
        a_rad = a_ps + WC_PASS / 2
        els.append({"type": "radiator", "name": R + "Radiator", "pos": W(a_rad, D - T), "dir_deg": NORTH + 180, "n": 7, "pitch": 0.07,
                    "height": 0.58, "depth": 0.08, "gap": 0.04, "z0": z(zb + 0.16), **wev("7-section radiator 0.49 x 0.58, bottom 0.16, centred on the aisle (029)")})
        pipes = [it(a_rad - 0.29, WC_W - T, D - T - 0.09, D - T - 0.07, zz, zz + 0.02) for zz in (0.06, 0.10)] + \
                [it(a_rad + sg * 0.27, a_rad + sg * 0.25, D - T - 0.09, D - T - 0.07, 0.06, 0.24 if sg < 0 else 0.68) for sg in (-1, 1)]
        els.append({"type": "boxes", "name": R + "Radiator_Pipes", "items": pipes, "material": "white", "slot": "M_PVC_White",
                    **wev("radiator flow/return pipes along the end wall from the aisle wall (029)")})
    return els


def extra_rooms(k, zb):
    """Fit-out of the rooms outside the 8 standard ones (owner room list 2026-10-01): F2/F3 room over the lobby =
    209 / 309 classrooms, F4 = 409 director; F4 west-end room = 410 classroom. Same furniture as the standard rooms."""
    if k == 1:
        return []
    els = []
    dk = ev("owner room list 2026-10-01; layout assumed (not photographed)", "low")

    def frame(x0, y0, du, dv):
        return lambda u, v: (x0 + du[0] * u + dv[0] * v, y0 + du[1] * u + dv[1] * v)

    def ang(dx, dy):
        return math.degrees(math.atan2(dx * C_X[1] + dy * C_Y[1], dx * C_X[0] + dy * C_Y[0]))
    rooms = []
    cw = (HW0 + HW1) / 2
    # over the lobby: u east from the P2 partition face, v south from the door (hall) wall face; board on the east wall
    rooms.append((f"{k}09", frame(P2 + PART / 2, HW0 - PART, (1, 0), (0, -1)), (1, 0), (0, -1), LOBBY_W, HW0 - PART - Y_SE, "director" if k == 4 else "class"))
    if k == 4:   # west-end room: u north from the south hall wall, v west from its front wall; board on the north wall
        rooms.append(("410", frame(FRONT_W + 0.4 - PART, HW0, (0, 1), (-1, 0)), (0, 1), (-1, 0), COR, FRONT_W + 0.4 - PART - X_W, "class"))
    # door centre along u on the v = 0 (door) wall: x09 = the teachers' door on the south hall wall, 410 = mid front wall
    door_u = {f"{k}09": DOOR_TEACH - (P2 + PART / 2), "410": COR / 2}
    for num, to_c, du, dv, L, D, kind in rooms:
        R = f"F{k}_R{num}_"
        d_u, d_v = ang(*du), ang(*dv)
        # desk_row "face" = +1 when the user sits on the LEFT of the row direction
        left_of = lambda d, o: d[0] * o[1] - d[1] * o[0] > 0          # is o to the left of d (C-local, right-handed)
        f_u = 1 if left_of(dv, du) else -1        # face value for the +u side of a row running along v
        f_v = 1 if left_of(du, dv) else -1        # face value for the +v side of a row running along u
        W = lambda u, v: c_to_w(*to_c(u, v))
        els.append({"type": "box", "name": R + "Floor_Laminate", "center": W(L / 2, D / 2), "dir_deg": ang(*du), "size": [L, D, 0.01],
                    "z0": z(zb), "material": "white", "slot": "M_Laminate_Oak_Grey", **dk})
        # outer wall (v = D) finish: white paint with the facade window openings, white reveals + boards; 600 lay-in grid
        # with 2 LED panels (as the standard rooms). Windows: tower landing windows T 1.0 x 1.4 (BLD_C edge 2, sills
        # 4.2 / 7.5 / 10.75 above the F1 FFL) over the lobby; west-end room: facade type W 1.85 x 1.40 at row F4 (1.05)
        C = ceil_of(k)
        if num == "410":
            wins, ww, wsill, wh = [(cw - 1.35) - HW0, (cw + 1.4) - HW0], WIN_W, WIN_SILL, WIN_H   # cw - 1.35: photo pass R0-05
        else:
            wins, ww, wsill, wh = [X_TOWER0 + 0.92 - P2 - PART / 2, X_TOWER0 + 2.86 - P2 - PART / 2], 1.0, (4.2, 7.5, 10.75)[k - 2] - (k - 1) * STOREY, 1.40
        rv = round(X_W - 0.16 - 0.07, 3)
        it_ = lambda u0, u1, v0, v1, z0, z1: [*W((u0 + u1) / 2, (v0 + v1) / 2), d_u, round(u1 - u0, 4), round(abs(v1 - v0), 4), round(z1 - z0, 4), z(zb + z0)]
        paint, trim, a_ = [], [], 0.0      # the shell wall face at v = D runs the full width (the tower wall's corner fills the west 0.35 m)
        for wc in sorted(wins) + [None]:
            o0, o1 = (L, L) if wc is None else (wc - ww / 2, wc + ww / 2)
            if o0 - a_ > 0.005:
                paint.append(it_(a_, o0, D - 0.006, D, LAM, C + 0.01))
            if wc is not None:
                paint += [it_(o0, o1, D - 0.006, D, LAM, wsill), it_(o0, o1, D - 0.006, D, wsill + wh, C + 0.01)]
                trim += [it_(o0, o0 + 0.006, D, D + rv, wsill + 0.02, wsill + wh), it_(o1 - 0.006, o1, D, D + rv, wsill + 0.02, wsill + wh),
                         it_(o0 + 0.006, o1 - 0.006, D, D + rv, wsill + wh - 0.006, wsill + wh), it_(o0, o1, D - 0.04, D + rv, wsill, wsill + 0.02)]
            a_ = o1
        els.append({"type": "boxes", "name": R + "OuterWall_Paint", "items": paint, "material": "white", "slot": "M_Paint_White", **dk})
        els.append({"type": "boxes", "name": R + "Window_Trim", "items": trim, "material": "white", "slot": "M_PVC_White", **dk})
        us = [0.30 + 0.60 * i for i in range(int((L - 0.3) / 0.6) + 1)]
        vs = [0.30 + 0.60 * j for j in range(int((D - 0.3) / 0.6) + 1)]
        seg = [[W(u, 0.0), W(u, D)] for u in us] + [[W(0.0, v), W(L, v)] for v in vs]
        els.append({"type": "rails", "name": R + "CeilingGrid", "segments": seg, "width": 0.024, "height": 0.012, "z0": z(zb + C - 0.012), **dk})
        for i, uc in enumerate((us[1] + 0.3, us[-3] + 0.3)):
            vc = vs[len(vs) // 2 - 1] + 0.3
            els.append({"type": "box", "name": R + f"LED_{i}", "center": W(uc, vc), "dir_deg": d_u, "size": [0.576, 0.576, 0.015],
                        "z0": z(zb + C - 0.015), "material": "white", "slot": "M_LED_Panel_600", "ue_asset": "led_panel_600", **dk})
        if kind == "class":
            cols = [D * 0.27, D * 0.73] if D < 5.5 else [1.25, 3.15, 5.05]
            for r, uc in enumerate([1.00, 1.95, 2.90, 3.85][: max(2, int((L - 1.6) / 0.95))]):
                for c, vc in enumerate(cols):
                    # keep the walk-in zone free (door_qa 2026-10-03: R410 desks stood 0.24 m in front of its door): no
                    # desk pair (desk u +-0.23, chair 0.42 behind it) nearer than 0.6 m to the door wall within 0.15 m of
                    # the door edges
                    du_ = door_u[num]
                    if vc - 0.6 < 0.6 and uc + 0.23 > du_ - DOOR_W / 2 - 0.15 and uc - 0.64 < du_ + DOOR_W / 2 + 0.15:
                        continue
                    row = {"dir_deg": d_v, "n": 2, "pitch": 0.60, "face": -f_u, "z": z(zb + LAM), **dk}
                    els.append({"type": "desk_row", "name": R + f"Desk_{r}{c}", "pos": W(uc, vc), "depth": 0.45, "height": 0.76,
                                "slot": "M_Laminate_Beech_Orange", "ue_asset": "school_desk_single_600", **row})
                    els.append({"type": "chair_row", "name": R + f"Chair_{r}{c}", "pos": W(uc - 0.42, vc),
                                "slot": "M_Plastic_Orange", "ue_asset": "school_chair_beech_tube", **row})
            door_left = left_of(du, (-dv[0], -dv[1]))  # facing the board (+u), is the door wall (-v side) on the left?
            if door_left:
                t = {"dir_deg": d_v, "face": f_u, "n": 1, "pitch": 1.20, "z": z(zb + LAM), **dk}
                tp, cp = W(L - 1.00, D - 1.10), W(L - 0.45, D - 1.10)
            else:
                t = {"dir_deg": d_u, "face": f_v, "n": 1, "pitch": 1.20, "z": z(zb + LAM), **dk}
                tp, cp = W(L - 1.00, D - 0.95), W(L - 1.00, D - 0.35)
            els.append({"type": "desk_row", "name": R + "TeacherDesk", "pos": tp, "depth": 0.60, "slot": "M_Wood_Oak_Light",
                        "ue_asset": "teacher_desk_oak_steel_1200", **t})
            els.append({"type": "chair_row", "name": R + "TeacherChair", "pos": cp, "ue_asset": "office_chair_iso_black", **t})
        else:   # director: executive desk facing the door, meeting table, cabinets on the door wall
            t = {"dir_deg": d_v, "face": f_u, "n": 1, "pitch": 1.80, "z": z(zb + LAM), **dk}
            els.append({"type": "desk_row", "name": R + "DirectorDesk", "pos": W(L - 1.20, D * 0.62), "depth": 0.85,
                        "slot": "M_Wood_Oak_Light", "ue_asset": "executive_desk_1800", **t})
            els.append({"type": "monitor_row", "name": R + "DirectorPC", "pos": W(L - 1.20, D * 0.62), **dict(t, z=z(zb + LAM + 0.75))})
            els.append({"type": "chair_row", "name": R + "DirectorChair", "pos": W(L - 0.55, D * 0.62), "ue_asset": "office_chair_executive", **t})
            mt = {"dir_deg": d_u, "n": 1, "pitch": 2.40, "face": f_v, "z": z(zb + LAM), **dk}
            els.append({"type": "desk_row", "name": R + "MeetingTable", "pos": W(1.45, D * 0.45), "depth": 1.00,
                        "slot": "M_Wood_Oak_Light", "ue_asset": "meeting_table_2400", **mt})
            for sd in (-1, 1):
                els.append({"type": "chair_row", "name": R + f"MeetingChairs_{'AB'[sd > 0]}", "pos": W(1.45, D * 0.45 + sd * 0.75),
                            **dict(mt, n=3, pitch=0.70, face=sd * f_v), "ue_asset": "chair_visitor_black"})
            c0, c1 = sorted((to_c(0.05, 0.04), to_c(1.60, 0.49)))
            els.append({"type": "box", "name": R + "Cabinets", "center": W(0.825, 0.265), "dir_deg": ang(*du), "size": [1.55, 0.45, 1.95],
                        "z0": z(zb + LAM), "material": "white", "slot": "M_Laminate_White", "ue_asset": "office_cabinet_row", **dk})
    return els


def f5(zb):
    P, els = "F5_", []
    lo = ev("F5 offices inside the roof, layout estimate", "low")
    yc = (Y_SE + Y_NW) / 2
    y0c, y1c = yc - 0.9, yc + 0.9
    x0, x1 = X_W + 2.0, FRONT_E
    doors = [(x0 + (x1 - x0) * f, DOOR_W) for f in (0.15, 0.38, 0.62, 0.85)]
    els.append(wall(P + "Corr_S", (x0, y0c - PART), (x1, y0c - PART), zb, doors=[(u - x0, w) for u, w in doors], h=2.40, **lo))
    els.append(wall(P + "Corr_N", (x1, y1c + PART), (x0, y1c + PART), zb, doors=[(x1 - u, w) for u, w in doors], h=2.40, **lo))
    for n, (u, w) in enumerate(doors):
        els.append(door(f"{P}Door_S{n}", (x0, y0c - PART), (x1, y0c - PART), u - x0, zb, **lo))
        els.append(door(f"{P}Door_N{n}", (x1, y1c + PART), (x0, y1c + PART), x1 - u, zb, **lo))
    els.append(slab(P + "Ceiling_Flat", x0, X_E, y0c - 2.0, y1c + 2.0, zb + 2.40, zb + 2.43, "white", **lo))
    for e in els:   # the storey is inside the hip roof: build_site cuts all of it to the roof shell's underside
        e["clip_roof"] = "BLD_C"
    return els


def build():
    f1 = floor_slabs(1, 0.0, {}) + ceilings(1, 0.0, {"W": True, "E": True}) + plan(1, 0.0, lobby=True, west_stair=True)
    f1 += fitout(1, 0.0, NUMBERS[1]) + wc_fitout(1, 0.0)
    # lobby: free-standing power-bank kiosk next to the coffee kiosk on the west wall (002; brand-neutral in game)
    f1.append({"type": "box", "name": "F1_ChargeKiosk", "center": c_to_w(LOBBY_X0 + 0.25, HW0 - 0.75), "dir_deg": EAST,
               "size": [0.40, 0.40, 1.45], "z0": z(0.0), "material": "white", "slot": "M_Plastic_White", "ue_asset": "powerbank_kiosk",
               **ev("power-bank rental kiosk by the coffee kiosk (002)")})
    # lobby radiators on both side walls near the entrance + a wall terminal on the east wall (2026-10-03 Q3-22 CI)
    evl = ev("lobby radiators on both side walls by the entrance + wall terminal (2026-10-03 Q3-22; positions +-0.4)", "low")
    for nm, xr in (("W", LOBBY_X0 + 0.06), ("E", LOBBY_X1 - 0.06)):
        f1.append({"type": "box", "name": f"F1_Lobby_Radiator_{nm}", "center": c_to_w(xr, 2.70), "dir_deg": NORTH,
                   "size": [0.85, 0.08, 0.55], "z0": z(0.17), "material": "white", "slot": "M_Paint_White",
                   "ue_asset": "radiator_sectional", **evl})
    f1.append({"type": "box", "name": "F1_Lobby_Terminal", "center": c_to_w(LOBBY_X1 - 0.04, 4.30), "dir_deg": NORTH,
               "size": [0.15, 0.08, 0.25], "z0": z(1.55), "material": "white", "slot": "M_Plastic_Grey", "ue_asset": "wall_terminal", **evl})
    evf = ev("lobby W wall fittings: fire-alarm panel, breaker box, clear box, 4-gang socket (2026-10-03 Q2-12; wall unsure)", "low")
    for nm, y0_, y1_, d_, z0_, z1_, sl in (("FireAlarmPanel", 2.40, 2.80, 0.10, 1.50, 1.80, "M_Plastic_White"),
                                           ("BreakerBox", 2.85, 3.15, 0.10, 1.50, 1.90, "M_Plastic_Grey"),
                                           ("ClearBox", 2.15, 2.35, 0.08, 1.65, 1.90, "M_Plastic_White"),
                                           ("Socket4", 1.90, 2.20, 0.03, 0.30, 0.38, "M_Plastic_White")):
        f1.append({"type": "box", "name": f"F1_Lobby_{nm}", "center": c_to_w(LOBBY_X0 + d_ / 2, (y0_ + y1_) / 2),
                   "dir_deg": NORTH, "size": [round(y1_ - y0_, 3), d_, round(z1_ - z0_, 3)], "z0": z(z0_), "material": "white",
                   "slot": sl, **evf})
    evx = ev("F1 E stair hall: full-height fin on the S wall, lintel over the exit bay, low wall + radiator in front of the "
             "N exit leaf (CC010 / CI013-015, 2026-10-04 Y0-d/e)", "medium")
    for nm, x0_, x1_, y0_, y1_, z0_, z1_, sl in (("SFin", 28.10, X_E, HE0, HE0 + 0.21, 0.0, 3.05, "M_Paint_White"),
                                                  ("ExitLintel", 28.70, X_E, HE0 + 0.21, 10.80, 2.70, 3.05, "M_Paint_White"),
                                                  ("ExitParapet", 28.70, X_E, 10.01, 10.73, 0.0, 1.11, "M_Paint_White"),
                                                  ("ExitRadiator", 28.62, 28.70, 10.05, 10.70, 0.36, 0.85, "M_Paint_White")):
        f1.append({"type": "box", "name": f"F1_StairE_{nm}", "center": c_to_w((x0_ + x1_) / 2, (y0_ + y1_) / 2), "dir_deg": EAST,
                   "size": [round(x1_ - x0_, 3), round(y1_ - y0_, 3), round(z1_ - z0_, 3)], "z0": z(z0_), "material": "white",
                   "slot": sl, **evx})
    f1.append({"type": "box", "name": "F1_CCTV_StairE", "center": c_to_w(27.70, HE0 + 0.07), "dir_deg": EAST, "size": [0.12, 0.12, 0.10],
               "z0": z(2.95), "material": "white", "slot": "M_Plastic_White", "ue_asset": "cctv_dome",
               **ev("CCTV dome on the S hall wall by the E end wall (2026-10-03 Q3-26)", "medium")})
    f1 += stair_storey("StairW_F1", X_W, +1, 0.0, solid=True, top_floor=False)
    f1 += stair_storey("StairE_F1", X_E, -1, 0.0, solid=True, top_floor=False)
    # east stair hall (138): the end wall steps back at the F2 floor over flight 2 - a white ledge with a row of potted
    # plants (clay / grey / pink pots, succulents); it ends where flight 2 climbs to within ~1 m of it
    h0e, h1e = hall(X_E - 1.0)
    y_lnd = h0e + (COR - LANDING - (RISERS - 1) * TREAD) + (RISERS - 1) * TREAD
    top1 = BOTTOM_RISER + (RISERS - 1) * RISER_H
    y_end = y_lnd - ((STOREY - 1.0) - top1) / RISER_H * TREAD
    evp = ev("ledge with potted plants on the east end wall over flight 2 (138)", "medium")
    f1.append(slab("F1_StairE_PlantLedge", X_E - 0.22, X_E, y_end, h1e, STOREY - 0.12, STOREY, "white", slot="M_Paint_White", **evp))
    pots = [(0.30, 0.24, "M_Clay_Pot"), (0.16, 0.14, "M_Plastic_Grey"), (0.30, 0.22, "M_Clay_Pot"), (0.18, 0.16, "M_Plastic_Pot_Pink"),
            (0.26, 0.22, "M_Clay_Pot"), (0.16, 0.14, "M_Plastic_Grey")]
    n_p = len(pots)
    for i, (d_, h_, sl) in enumerate(pots):
        yp = h1e - 0.35 - i * (h1e - 0.35 - y_end - 0.25) / (n_p - 1)
        pw = c_to_w(X_E - 0.11, yp)
        f1.append({"type": "disc", "name": f"F1_StairE_Pot_{i}", "pos": pw, "r": round(d_ / 2, 3), "z0": z(STOREY),
                   "z1": z(STOREY + h_), "seg": 20, "material": "white", "slot": sl, "ue_asset": "flower_pot", **evp})
        f1.append({"type": "disc", "name": f"F1_StairE_PotPlant_{i}", "pos": pw, "r": round(d_ / 2 * 0.8, 3), "z0": z(STOREY + h_),
                   "z1": z(STOREY + h_ + 0.18), "seg": 12, "material": "white", "slot": "M_Hedge_Foliage", "ue_asset": "houseplant_small", **evp})
    # janitor's closets under flight 2 of both F1 stairs (map owner), brown door, north of the east exit door
    evc = ev("janitor's closet under flight 2, ordinary brown door (map owner)")
    for side, xw, sg in (("W", X_W, +1), ("E", X_E, -1)):
        h0, h1 = hall(xw + sg * 1.0)
        y_b = h0 + (COR - LANDING - (RISERS - 1) * TREAD)
        y_c = y_b + 1.30                          # closet front 1.3 m up the flight: clear of the exit-door frame (X0-11)
        y_l = y_b + (RISERS - 1) * TREAD
        soff = lambda y: STOREY - RISER_H - SOFFIT * (TREAD ** 2 + RISER_H ** 2) ** 0.5 / TREAD - (y - y_b) * RISER_H / TREAD
        xo = xw + sg * FLIGHT_W
        xa, xb = (xw, xo) if sg > 0 else (xo, xw)
        ud_c = FLIGHT_W / 2 + (0.125 if side == "E" else 0.0)   # E: clear of the exit-door radiator (door_qa, Y0-e)
        f1.append(wall(f"Closet_{side}_Front", (xb, y_c), (xa, y_c), h=soff(y_c) - 0.02, thk=0.12, doors=[(ud_c, 0.8)], **evc))
        f1.append(door(f"Closet_{side}_Door", (xb, y_c), (xa, y_c), ud_c, width=0.8, leaf="solid", **dict(evc, wall_thk=0.12, material="metal")))   # black metal (X0-03)
        # side wall: a straight wall up to the low end of the flight + a wedge on it following the soffit (a single sloped
        # slab hung below the F1 slab into the basement hall, 2026-10-04 Y0-a)
        xl_ = xo if sg > 0 else xo + 0.12                       # wall() thickness goes to the left of the line (-x)
        f1.append(wall(f"Closet_{side}_Side", (xl_, y_c), (xl_, y_l), h=soff(y_l) - 0.02, thk=0.12, **evc))
        f1.append({"type": "roof_plane", "name": f"Closet_{side}_SideTop", "thk": round(soff(y_c) - soff(y_l) + 0.02, 3), "material": "white",
                   "ring": [c_to_w(xo - sg * 0.12, y_c), c_to_w(xo, y_c), c_to_w(xo, y_l), c_to_w(xo - sg * 0.12, y_l)],
                   "z": [z(soff(y_c) - 0.02), z(soff(y_c) - 0.02), z(soff(y_l) - 0.02), z(soff(y_l) - 0.02)], **evc})
    up = []
    for k in (2, 3, 4):
        zb = (k - 1) * STOREY
        west = k <= 3
        up += floor_slabs(k, zb, {"W": west, "E": True}) + ceilings(k, zb, {"W": k < 3, "E": True})
        up += plan(k, zb, lobby=False, west_stair=west) + fitout(k, zb, NUMBERS[k]) + wc_fitout(k, zb) + extra_rooms(k, zb)
        if k == 3:   # potted floor plants in front of the W stair guard at F3, none at F1 (video 052716931, 2026-10-04 X0-02)
            for i, yp in enumerate((8.8, 9.7, 10.6)):
                up.append({"type": "box", "name": f"F3_Plant_{i}", "center": c_to_w(FRONT_W + 0.30, yp), "dir_deg": 0,
                           "size": [0.35, 0.35, 0.7], "z0": z(zb + HALL_FIN), "material": "hedge", "slot": "M_Hedge_Foliage",
                           "ue_asset": "potted_plant_floor", **ev("potted plants at the F3 W stair guard (X0-02; y +-0.5)", "medium")})
        if k < 3:
            up += stair_storey(f"StairW_F{k}", X_W, +1, zb, solid=False, top_floor=(k == 2))
        up += stair_storey(f"StairE_F{k}", X_E, -1, zb, solid=False, top_floor=(k == 4))
    up += floor_slabs(5, F5_Z, {"W": False, "E": True}) + f5(F5_Z)
    note = ("Block C interior v6 (2026-10-01): reference classrooms 5.80 x 6.35 m (C105), corridor 5.0 m with a 1.3 m jog, "
            "shell 29.4 m, storey 3.30; generated by Scripts/Geo/zones/zone_c_v6.py, fittings carried over by remap_c_v6.py")
    info = dict(P1=P1, P2=P2, P3=P3, P4=P4, P_WCM=P_WCM, tower=(X_TOWER0, X_TOWER1), hallW=(HW0, HW1), hallE=(HE0, HE1),
                north=(Y_NW, Y_NE), outer=(L_OUT, Y_OUT_W, Y_OUT_E), origin=C_ORIGIN.round(3).tolist())
    return ({"id": "INT_C_F1", "collection": "INT_C_F1", "note": note, "elements": f1},
            {"id": "INT_C_Floors", "collection": "INT_C_Floors", "note": note, "elements": up}), info


if __name__ == "__main__":
    specs, info = build()
    out_dir = sys.argv[1]
    for spec in specs:
        json.dump(spec, open(os.path.join(out_dir, spec["id"] + ".std.json"), "w"), indent=1)
        print(spec["id"], len(spec["elements"]))
    print({k: (np.round(v, 3).tolist() if not isinstance(v, list) else v) for k, v in info.items()})
