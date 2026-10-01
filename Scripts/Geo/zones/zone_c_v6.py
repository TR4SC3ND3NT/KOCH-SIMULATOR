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
C_ORIGIN = np.array([173.264, -3.640])
FFL = 6.40
EAST = math.degrees(math.atan2(C_X[1], C_X[0]))
NORTH = EAST + 90.0

T, PART = 0.45, 0.20
L_OUT = 29.4                                  # = 2 T + 4 STD_L + LOBBY_W + 4 PART (facade fit 29.4)
X_W, X_E = T, L_OUT - T
STD_L, STD_D = 5.80, 6.35                     # reference classroom C105 (clear, wall faces)
COR = 5.00                                    # corridor, clear (C204 014: door 205 711 px vs own door 2362 px)
JOG = 1.3                                     # facade step of the west wing (061621646 fit), mirrored inside
# x lines (partition centres) along the plan
P1 = X_W + STD_L + PART / 2                   # 107|108, 106|105
P2 = P1 + PART / 2 + STD_L + PART / 2         # 108|lobby, 105|WC-W
LOBBY_W = 4.5
P3 = P2 + PART / 2 + LOBBY_W + PART / 2       # lobby|101 = south jog
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
DOOR_H, DOOR_W, WC_DOOR_W = 2.00, 0.90, 0.90  # classroom opening at the wall face (C204 person + tiles, C105 tiles)
RISERS = 11
RISER_H = STOREY / 21.5                       # 21.5 risers per storey (half bottom riser), as before
TREAD, BOTTOM_RISER = 0.332, 0.5 * STOREY / 21.5
LANDING = 1.16
FLIGHT_W, WELL = 1.35, 0.20
STAIR_X = 2 * FLIGHT_W + WELL
FRONT_W, FRONT_E = X_W + STAIR_X, X_E - STAIR_X
SOFFIT = 0.18
F5_Z = 4 * STOREY


def ceil_of(k):
    """Lay-in grid height above the floor of storey k (m)."""
    return 2.90 if k == 1 else 2.80


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
            els.append(slab(f"F{k}_Slab_{nm}_S", x0, x1, y0, yb, z0, zb, t))
            els.append(slab(f"F{k}_Slab_{nm}_N", x0, x1, h1, y1, z0, zb, t))
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
            els.append(slab(f"F{k}_Ceiling_{pn}", x0, x1, a, b, zb + CEIL, zb + CEIL + 0.02, "white",
                            slot="M_Ceiling_Tile_600", **ev(f"600x600 lay-in grid ceiling at {CEIL:.2f} m (reference room)")))
    return els


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
          "bottom_riser_h": round(BOTTOM_RISER, 4), "material": "granite", **ev("U-stair flight 1 (hall photo layout, 3.45 m storey)")}
    if not solid:
        f1["soffit_thk"] = SOFFIT
    els.append(f1)
    xs = sorted([x_wall, x_front])
    els.append(slab(f"{prefix}_Landing", xs[0], xs[1], y_land, h1, zb - 0.1 if solid else top1 - 0.2, top1, "granite",
                    **ev("half-landing against the north hall wall")))
    els.append({"type": "stairs_run", "name": f"{prefix}_Flight2", "top": c_to_w(xb, y_bot), "dir_deg": NORTH,
                "width": FLIGHT_W, "risers": RISERS, "riser_h": round(RISER_H, 4), "tread": TREAD,
                "z_top": z(zb + STOREY), "material": "granite", "soffit_thk": SOFFIT, **ev("U-stair flight 2")})
    rail = {"height": 0.95, "spacing": 0.12, "mid_rails": 0, "material": "white"}
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
DOOR_OFF = PART / 2 + 0.45 + DOOR_W / 2
DOOR_S = {"S1": P1 - DOOR_OFF, "S2": P2 - DOOR_OFF, "S4": P3 + DOOR_OFF, "S5": P4 + DOOR_OFF}   # 107/108 east ends, 101/102 west ends
DOOR_N = {"N1": P1 - DOOR_OFF, "N2": P2 - DOOR_OFF, "N4": P3 + DOOR_OFF, "N5": P4 + DOOR_OFF}   # 106/105 east ends, 104/103 west ends
DOOR_TEACH = (P2 + P3) / 2
WC_DOORS = [(P2 + 0.1 + WC_W / 2, "WC4"), (P_WCM + 0.1 + WC_W / 2, "WC5")]
NUMBERS = {1: {"S1": "107", "S2": "108", "S4": "101", "S5": "102", "N1": "106", "N2": "105", "N4": "104", "N5": "103"}}
for k in (2, 3, 4):
    NUMBERS[k] = {"S1": f"{k}01", "S2": f"{k}02", "S4": f"{k}03", "S5": f"{k}04", "N1": f"{k}08", "N2": f"{k}07",
                  "N4": f"{k}06", "N5": f"{k}05"}


def plan(k, zb, lobby, west_stair):
    P, els, CEIL = f"F{k}_", [], ceil_of(k)
    num = NUMBERS[k]
    # south hall wall: west part (to the lobby's east wall), jog, east part; F1 leaves the lobby front open
    sw = [(DOOR_S["S1"], "S1"), (DOOR_S["S2"], "S2")] + ([] if lobby else [(DOOR_TEACH, "T")])
    se = [(DOOR_S["S4"], "S4"), (DOOR_S["S5"], "S5")]
    segs = [("Hall_S_West", (X_W, HW0 - PART), ((P2 - PART / 2) if lobby else X_JS, HW0 - PART), sw),
            ("Hall_S_East", (X_JS, HE0 - PART), (X_E, HE0 - PART), se)]
    for nm, a, b, dd in segs:
        els.append(wall(P + nm, a, b, zb, doors=[(x - a[0], DOOR_W) for x, _ in dd], **ev("south hall wall")))
        for x, key in dd:
            lab = "teachers' room over the lobby" if key == "T" else f"room {num[key]}"
            els.append(door(f"{P}Door_{key}", a, b, x - a[0], zb, **ev(f"door of {lab}")))
    els.append(wall(P + "Hall_S_Jog", (X_JS, HW0 - PART), (X_JS, HE0 - PART), zb, thk=PART, **ev("south hall wall jog 1.3 m (mirrors the facade step)")))
    # north hall wall: west part to the WC mid wall, jog, east part (east->west so the thickness goes north)
    nw = [(DOOR_N["N1"], "N1", DOOR_W), (DOOR_N["N2"], "N2", DOOR_W), (WC_DOORS[0][0], WC_DOORS[0][1], WC_DOOR_W)]
    ne = [(WC_DOORS[1][0], WC_DOORS[1][1], WC_DOOR_W), (DOOR_N["N4"], "N4", DOOR_W), (DOOR_N["N5"], "N5", DOOR_W)]
    for nm, a, b, dd in (("Hall_N_West", (X_JN, HW1 + PART), (X_W, HW1 + PART), nw), ("Hall_N_East", (X_E, HE1 + PART), (X_JN, HE1 + PART), ne)):
        els.append(wall(P + nm, a, b, zb, doors=[(a[0] - x, w) for x, _, w in dd], **ev("north hall wall; one WC stands forward of the other (owner)")))
        for x, key, w in dd:
            wc = key.startswith("WC")
            els.append(door(f"{P}Door_{key}", a, b, a[0] - x, zb, width=w, leaf="solid" if wc else "glass2",
                            **ev("WC door, solid black leaf" if wc else f"door of room {num[key]}")))
    els.append(wall(P + "Hall_N_Jog", (X_JN, HE1 + PART), (X_JN, HW1 + PART), zb, **ev("north hall wall jog at the WC mid wall (owner)")))
    # partitions
    for x in (P1, P2, P3, P4):
        if lobby or x not in (P2, P3) or True:
            h0 = hall(x - 0.01)[0] if x != P3 else HE0
            els.append(wall(f"{P}Room_S_{x:.2f}", (x, south_in(x)), (x, (HW0 if x < X_JS else HE0) - PART), zb,
                            **ev("room partition, reference 5.80 m rooms / lobby 4.5 m")))
    for x in (P1, P2, P_WCM, P3, P4):
        yh = (HW1 if x < X_JN else HE1) + PART
        els.append(wall(f"{P}Room_N_{x:.2f}", (x, north_in(x + (0.01 if x == P_WCM else 0))), (x, yh), zb,
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
        xb = xf + sg * 4.05
        els.append(slab(f"{P}Hall_Bulkhead_{side}", xb - 0.2, xb + 0.2, h0, h1, zb + CEIL - 0.38, zb + CEIL, "white",
                        **ev("plasterboard bulkhead across the hall in front of the stair zone")))
    for x in (P2, X_JS):
        h0, h1 = hall(x + 0.01)
        els.append(slab(f"{P}Hall_Beam_{x:.1f}", x - 0.2, x + 0.2, min(hall(x - 0.01)[0], h0), max(hall(x - 0.01)[1], h1),
                        zb + CEIL - 0.30, zb + CEIL, "white", **ev("bulkheads crossing the hall at the lobby sides")))
    # blue accent panels at the end-room doors and around the WC doors
    for key, x in (("N1", DOOR_N["N1"]), ("N5", DOOR_N["N5"]), ("S1", DOOR_S["S1"]), ("S5", DOOR_S["S5"])):
        yy = (hall(x)[1] - 0.01) if key[0] == "N" else (hall(x)[0] + 0.01)
        els.append({"type": "box", "name": f"{P}Accent_{key}", "center": c_to_w(x, yy), "dir_deg": EAST,
                    "size": [DOOR_W + 1.2, 0.02, CEIL - 0.1], "z0": z(zb + 0.1), "material": "accent",
                    **ev("periwinkle-blue panel at the end-room door (hall photo)")})
    for x0, x1, yy in ((P2 + 0.1, P_WCM, HW1 - 0.01), (P_WCM, P3 - 0.1, HE1 - 0.01)):
        els.append({"type": "box", "name": f"{P}Accent_WC_{x0:.1f}", "center": c_to_w((x0 + x1) / 2, yy), "dir_deg": EAST,
                    "size": [x1 - x0, 0.02, CEIL - 0.1], "z0": z(zb + 0.1), "material": "accent", **ev("blue accent wall at the WC doors")})
    for n, x in enumerate((FRONT_W + 3.9, FRONT_E - 3.9)):
        els.append({"type": "box", "name": f"{P}Hall_Radiator_{n}", "center": c_to_w(x, hall(x)[1] - 0.06), "dir_deg": EAST,
                    "size": [0.8, 0.08, 0.55], "z0": z(zb + 0.15), "material": "white", **ev("sectional radiator on the north hall wall")})
    for n, x in enumerate(((P1 + P2) / 2, (P3 + P4) / 2)):
        yy = hall(x)[1] - 0.25
        els.append({"type": "bench", "name": f"{P}Hall_Bench_N{n}", "pos": c_to_w(x, yy), "dir_deg": NORTH + 180,
                    "length": 1.8, "depth": 0.40, "seat_h": 0.45, "back": False, "z": z(zb), **ev("hall bench, 1.8 m", "low")})
    return els


# --- reference classroom fit-out (C105, docs/reference/C105_etalon.png). Room frame: u from the back wall to the board
# wall (the board is on the door side), v from the door (corridor) wall to the window wall; L x D = 5.80 x 6.35.
ROOM_X = {"1": (X_W, P1 - PART / 2), "2": (P1 + PART / 2, P2 - PART / 2), "4": (P3 + PART / 2, P4 - PART / 2), "5": (P4 + PART / 2, X_E)}
BOARD_EAST = {"1": True, "2": True, "4": False, "5": False}
WIN_PAIR = (1.65, 4.25)        # window centres from the back wall (C105; facade pairs 2.59 m apart)
CORNER_WIN = {"S1": 3.52, "S5": 25.90, "N1": 3.50, "N5": 25.88}   # one long-facade window in the corner rooms (facade fit)
WC_WIN_N = (P2 + PART / 2 + WC_W / 2, P_WCM + PART / 2 + WC_W / 2)


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
    return sorted(round(to_c(u, 0)[0], 3) for u in WIN_PAIR)


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
        bx("WindowBeam", 0.25, L, D - 0.50, D, C - 0.20, C + 0.01, slot="M_Paint_White", **ref)
        bx("DoorBox", 0.15, L, 0.0, 0.30, C - 0.25, C + 0.01, slot="M_Paint_White", **ref)
        bx("BackBox", 0.0, 0.20, 0.30, D - 0.50, C - 0.25, C + 0.01, slot="M_Paint_White", **ref)
        bx("Pilaster_BackDoor", 0.0, 0.15, 0.0, 0.25, 0.0, C + 0.01, slot="M_Paint_White", **ref)
        bx("Column_BackWin", 0.0, 0.25, D - 0.50, D, 0.0, C + 0.01, slot="M_Paint_White", **ref)
        bx("Pilaster_BoardWin", L - 0.10, L, D - 0.60, D, 0.0, C + 0.01, slot="M_Paint_White", **ref)
        # board wall: 70-inch TV, 1.8 x 1.2 whiteboard, split AC (153)
        bx("TV", L - 0.055, L - 0.005, 4.30 - 0.785, 4.30 + 0.785, 1.06, 1.93, mat="metal", slot="M_Plastic_Black", ue_asset="tv_70in", **ref)
        bx("Whiteboard", L - 0.025, L - 0.005, 1.85 - 0.90, 1.85 + 0.90, 0.75, 1.95, slot="M_Plastic_White", ue_asset="whiteboard_180x120", **ref)
        bx("AC", L - 0.25, L - 0.005, 5.30 - 0.45, 5.30 + 0.45, 2.30, 2.60, slot="M_AC_Casing", ue_asset="ac_split_indoor", **ref)
        # radiators under the long-facade windows
        for n, xw in enumerate(facade_windows(key)):
            uw = (xw - to_c(0, 0)[0]) * su
            bx(f"Radiator_{n}", uw - 0.50, uw + 0.50, D - 0.14, D - 0.06, 0.15, 0.70, slot="M_Paint_White", ue_asset="radiator_sectional", **ref)
        # 3 rows of lab desks (0.80 x 0.60) along the windows from 0.40 m off the back wall, users on the window side of
        # each row (151/152: 5 PCs per row); the window row has 4 so the teacher's corner keeps a 0.6 m passage
        lab = ev("lab layout from C105 151-153: rows of 5/5/4 PCs, users facing the door wall", "medium")
        for r, (vc, n) in enumerate(((0.70, 5), (3.00, 5), (5.30, 4))):
            p = c_to_w(*to_c(0.40 + n * 0.40, vc))
            row = {"pos": p, "dir_deg": d_u, "n": n, "pitch": 0.80, "face": f_v, "z": z(zb), **lab}
            els.append({"type": "desk_row", "name": R + f"Desks_{r}", "depth": 0.60, **row})
            els.append({"type": "monitor_row", "name": R + f"PCs_{r}", **dict(row, z=z(zb + 0.75))})
            els.append({"type": "chair_row", "name": R + f"Chairs_{r}", **dict(row, pos=c_to_w(*to_c(0.40 + n * 0.40, vc + 0.62)))})
        # teacher's desk by the board on the window side, the teacher faces the class (153)
        t = {"dir_deg": d_v, "face": f_u, "n": 1, "z": z(zb), **lab}
        els.append({"type": "desk_row", "name": R + "TeacherDesk", "pos": c_to_w(*to_c(4.50, 5.20)), "pitch": 1.20, "depth": 0.60, **t})
        els.append({"type": "monitor_row", "name": R + "TeacherPC", "pos": c_to_w(*to_c(4.50, 5.20)), "pitch": 1.20, **dict(t, z=z(zb + 0.75))})
        els.append({"type": "chair_row", "name": R + "TeacherChair", "pos": c_to_w(*to_c(5.10, 5.20)), "pitch": 1.20, **t})
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
    return els


def build():
    f1 = floor_slabs(1, 0.0, {}) + ceilings(1, 0.0, {"W": True, "E": True}) + plan(1, 0.0, lobby=True, west_stair=True)
    f1 += fitout(1, 0.0, NUMBERS[1])
    f1 += stair_storey("StairW_F1", X_W, +1, 0.0, solid=True, top_floor=False)
    f1 += stair_storey("StairE_F1", X_E, -1, 0.0, solid=True, top_floor=False)
    # janitor's closets under flight 2 of both F1 stairs (map owner), brown door, north of the east exit door
    evc = ev("janitor's closet under flight 2, ordinary brown door (map owner)")
    for side, xw, sg in (("W", X_W, +1), ("E", X_E, -1)):
        h0, h1 = hall(xw + sg * 1.0)
        y_b = h0 + (COR - LANDING - (RISERS - 1) * TREAD)
        y_c = h0 + 2.97
        y_l = y_b + (RISERS - 1) * TREAD
        soff = lambda y: STOREY - RISER_H - SOFFIT * (TREAD ** 2 + RISER_H ** 2) ** 0.5 / TREAD - (y - y_b) * RISER_H / TREAD
        xo = xw + sg * FLIGHT_W
        xa, xb = (xw, xo) if sg > 0 else (xo, xw)
        f1.append(wall(f"Closet_{side}_Front", (xb, y_c), (xa, y_c), h=soff(y_c) - 0.02, thk=0.12, doors=[(FLIGHT_W / 2, 0.8)], **evc))
        f1.append(door(f"Closet_{side}_Door", (xb, y_c), (xa, y_c), FLIGHT_W / 2, width=0.8, leaf="solid", **dict(evc, wall_thk=0.12, material="wood")))
        f1.append({"type": "roof_plane", "name": f"Closet_{side}_Side", "thk": round(soff(y_c) + 0.1, 3), "material": "white",
                   "ring": [c_to_w(xo - sg * 0.12, y_c), c_to_w(xo, y_c), c_to_w(xo, y_l), c_to_w(xo - sg * 0.12, y_l)],
                   "z": [z(soff(y_c) - 0.02), z(soff(y_c) - 0.02), z(soff(y_l) - 0.02), z(soff(y_l) - 0.02)], **evc})
    up = []
    for k in (2, 3, 4):
        zb = (k - 1) * STOREY
        west = k <= 3
        up += floor_slabs(k, zb, {"W": west, "E": True}) + ceilings(k, zb, {"W": k < 3, "E": True})
        up += plan(k, zb, lobby=False, west_stair=west) + fitout(k, zb, NUMBERS[k])
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
