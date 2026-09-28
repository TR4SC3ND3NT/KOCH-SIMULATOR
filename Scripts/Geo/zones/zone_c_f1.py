# Zone "C floors" (R1): Block C interior, all storeys. F1 (hall, entrance lobby, WC entrances, classrooms, both
# U-stairs, fittings) -> Art/Blender/Specs/INT_C_F1.json; F2-F4 (same plan, a room over the lobby) and F5 inside the
# roof (east stair arrival, ridge corridor, offices under the dormers) -> INT_C_Floors.json. Both built by
# build_site.py. Plan in Block C local metres (x east along the south facade from the SW corner, y north, z above the
# F1 FFL); every constant cites its source. Topology: map owner (docs/reference/campus.md, 2026-09-25).
# Run: uv run --project Scripts python Scripts/Geo/zones/zone_c_f1.py
import json
import math
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
C_ORIGIN = np.array([173.264, -3.640])        # Specs/BLD_C.json anchor
C_X = np.array([0.99920, -0.03985])
C_Y = np.array([-C_X[1], C_X[0]])
FFL = 6.40                                    # C ground floor, world z (BLD_C ffl_z)
EAST = math.degrees(math.atan2(C_X[1], C_X[0]))
NORTH = EAST + 90.0

# --- shell (BLD_C.json ring = outer faces, wall_thk 0.45) -------------------------------------------------------
T = 0.45
X_W, X_E = T, 29.4 - T                        # inner faces of the west / east walls
Y_N = 17.2 - T                                # inner face of the north wall
# 2026-09-26 photo match (061621646 PnP 6 px on 26 window corners, 061428331 eave, drone 2022): the tower face is
# flush with the east wing (y 1.3); only the west wing projects (1.3 m). The older 0.6 m tower recess was wrong.
Y_S_WEST, Y_S_TOWER, Y_S_EAST = 0.0 + T, 1.3 + T, 1.3 + T
X_TOWER0, X_TOWER1 = 12.8, 16.6               # tower (entrance) bay, outer faces

# --- levels -------------------------------------------------------------------------------------------------------
STOREY = 3.30        # facade_fit 061621646: 3.29 m floor-to-floor
SLAB = 0.25          # structural slab (BLD_C basement slab_t)
# Hall photo (map owner, 2026-09-25 21:35; camera from the hall + cross vanishing points, f 945 px checked by their
# orthogonality; metric from the 0.600 m ceiling grid, 4 lines at 0.604/0.600/0.596 m): grid ceiling 1.33 m above the
# camera, floor 1.59 m below it (2.05 m classroom door frames) -> ceiling 2.92 m.
CEIL = 2.92
BEAM_D = 0.38        # bulkhead under the grid ceiling (same photo: underside 2.54 m)
DOOR_H, DOOR_W = 2.05, 0.99   # classroom door outer frame, person-scaled metrology (080420598, campus.md)
WC_DOOR_W = 0.90     # WC doors: solid black leaf, narrower than the glazed classroom doors (F_2.5)

# --- hall (corridor) ------------------------------------------------------------------------------------------------
# Map owner: WCs straight ahead from the entrance, the hall runs left and right to two mirrored stairs. Width from the
# hall photo: door-jamb planes of the two end-room doors at +3.47 / -2.39 m from the camera (5.86 m); the 0.6 m grid
# puts 9.75 tiles across. (The older 5.4 m "9 tiles" reading assumed the LED-panel spacing.)
HALL_W = 5.85
PART = 0.20                                   # partition thickness
HALL_Y0 = Y_S_WEST + (Y_N - Y_S_WEST - HALL_W - 2 * PART) / 2 + PART   # hall south face
HALL_Y1 = HALL_Y0 + HALL_W                                            # hall north face

# --- staircases: U-stairs filling the hall end, flights parallel to the end wall ------------------------------------
# Hall photo, back plane of the stair (left wall -> right wall, looking east): flight 1 is on the hall side, solid with
# a white wall under it, bottom riser 1.45 m from the south wall, rises north over 3.34 m (10 treads) to a 1.07 m
# half-landing against the north wall (the hall wall, not a room); flight 2 returns south along the end wall over
# the exit door to the F2 edge. White balustrade on the hall side of flight 1 and the landing. Bay depth along the hall
# 2.8-2.9 m (front plane 6.36, end wall 9.1-9.2 m from the camera). 11 risers per flight (0.15 m, 22 per 3.30 storey;
# 070704360 t 13-28 s); the photo's landing edge reads +1.80 (one riser more?) -> kept 11 + 11, see photo_requests.
# 2026-09-26 re-read of the hall photo (map owner's corrections, all confirmed there): the rail starts at the SECOND
# riser, the first riser at the hall floor is ~half height, the landing ~0.1 m longer -> 11 risers per flight with a
# half-height bottom riser on flight 1: 21.5 risers per storey, riser 3.30 / 21.5 = 0.1535, tread 0.332, landing 1.16,
# run-in 1.37 (fixC analysis, ~/koch_work/fixC/ovl/hall_before).
RISERS, RISER_H, TREAD = 11, STOREY / 21.5, 0.332
BOTTOM_RISER = 0.5 * RISER_H
LANDING = 1.16
FLIGHT_W, WELL = 1.35, 0.20
STAIR_X = 2 * FLIGHT_W + WELL                 # 2.90 m bay depth along x
RUNIN = HALL_W - LANDING - (RISERS - 1) * TREAD   # hall floor in front of the bottom riser (south side)
SOFFIT = 0.18                                 # waist slab of the flights that need headroom under them
FRONT_W, FRONT_E = X_W + STAIR_X, X_E - STAIR_X   # hall-side face of each stair bay
# End-room doors: in the hall photo both door sets (0.99 m) sit 1.9-2.9 m in front of the stair's front plane, with a
# blue panel on their hall side and a ceiling bulkhead 3.9-4.2 m in front of the stair.
END_DOOR_OFF = 2.40                           # door centre from the stair front (m)
BULK_OFF = 4.05                               # bulkhead centre from the stair front (m)
# Room partitions between facade window bays (BLD_C: south/north columns 3.52 / 8.13 / 10.69 and 18.62 / 21.21 /
# 25.9, openings +-0.925) and clear of the end-room doors.
PART_W, PART_E = 6.70, 22.60
WC0, WC1 = 12.3, 17.1                         # WC block (two rooms, 2.4 m each) centred on the entrance
LOB0, LOB1 = X_TOWER0 - 0.3, X_TOWER1 + 0.3   # F1 lobby opens onto the hall between these lines (tower bay)
# F5 in the roof (BLD_C: eave 13.9, hip pitch 25 deg): floor = top of the F4 ceiling slab 13.2
F5_Z = 4 * STOREY
KNEE, KNEE_Y = 1.20, 2.15                     # knee wall height and its distance in from the eave wall faces (m)
ROOF_TAN = math.tan(math.radians(25))
F5_CORR = 1.80                                # ridge corridor width


# slab/ceiling strips between the stair bays, one per wing (each stops at its own south wall)
# Mid_W stops at the inner face of the west-wing return (x 12.35) south of the tower bay, so its edge face is never
# flush with the return's outer face (the air in front of the tower); the strip behind the return is Mid_WT.
MID = {"Mid_W": (FRONT_W, X_TOWER0 - T, Y_S_WEST), "Mid_WT": (X_TOWER0 - T, X_TOWER0, Y_S_TOWER),
       "Mid_T": (X_TOWER0, X_TOWER1, Y_S_TOWER), "Mid_E": (X_TOWER1, FRONT_E, Y_S_EAST)}


def c_to_w(x, y):
    # 1e-6 m: 1 mm rounding skewed shared slab edges into overlapping slivers (coplanar z-fight)
    return (C_ORIGIN + x * C_X + y * C_Y).round(6).tolist()


def ring(x0, x1, y0, y1):
    return [c_to_w(x0, y0), c_to_w(x1, y0), c_to_w(x1, y1), c_to_w(x0, y1)]


def z(v):
    return round(FFL + v, 3)


def ev(txt, conf="medium"):
    return {"evidence": txt, "confidence": conf}


def wall(name, a, b, zb=0.0, openings=(), thk=PART, h=CEIL, **kw):
    """Partition from C-local a to b at storey base zb (thickness to the LEFT of a->b); openings [(u0, u1, z1_rel)]."""
    L = float(np.hypot(b[0] - a[0], b[1] - a[1]))
    # openings start at the finished floor; the wall base sits inside the slab (an opening flush with the wall base
    # would make wall_piece emit duplicate bottom faces)
    # opening sill 6 cm below the finished floor, inside the slab: flush or 1 cm below still z-fights with the slab top
    ops = [{"u0": round(u0, 3), "u1": round(u1, 3), "z0": z(zb - 0.06), "z1": z(zb + oh)} for u0, u1, oh in openings]
    assert all(0 < o["u0"] < o["u1"] < L for o in ops), (name, L, ops)
    return {"type": "int_wall", "name": name, "line": [c_to_w(*a), c_to_w(*b)], "z0": z(zb - 0.10), "z1": z(zb + h),
            "thk": thk, "openings": ops, "material": "white", **kw}


def door(name, a, b, u_mid, zb=0.0, width=DOOR_W, leaf="glass2", hinge="left", material="metal", **kw):
    """Door set centred at u_mid along the host wall a->b (same line as its int_wall). Map owner 2026-09-26: every C
    door is the same black aluminium glazed door (glass2), only WC doors are solid black; an estimated door keeps that
    look (confidence medium, never the orange 'low' colour) and flags only its position."""
    if kw.get("confidence") == "low":
        kw = dict(kw, confidence="medium", position_confidence="low",
                  evidence=kw.get("evidence", "") + " | position_confidence: low (standard C door, position estimated)")
    return {"type": "door", "name": name, "line": [c_to_w(*a), c_to_w(*b)], "u0": round(u_mid - width / 2, 3),
            "u1": round(u_mid + width / 2, 3), "z0": z(zb), "z1": z(zb + DOOR_H), "wall_thk": PART, "leaf": leaf,
            "mid": 1.0, "hinge": hinge, "material": material, **kw}


def u_ops(doors):
    return [(u - w / 2 - 0.02, u + w / 2 + 0.02, DOOR_H + 0.02) for u, w in doors]


def slab(name, x0, x1, y0, y1, z0, z1, material="stone", **kw):
    return {"type": "slab", "name": name, "ring": ring(x0, x1, y0, y1), "z0": z(z0), "z1": z(z1), "material": material,
            **kw}


def stair_storey(prefix, x_wall, sgn, zb, solid, top_floor):
    """One U-stair storey at a hall end, from floor zb to zb + 3.30. x_wall = inner face of the end wall, sgn = +1
    (west end, bay extends east) / -1. solid: flight 1 + landing solid down to the floor (F1, as in the hall photo)."""
    els = []
    xa = x_wall + sgn * (FLIGHT_W + WELL + FLIGHT_W / 2)   # flight 1 (hall side) centre line
    xb = x_wall + sgn * (FLIGHT_W / 2)                     # flight 2 (end-wall side) centre line
    x_front = x_wall + sgn * STAIR_X                       # hall-side edge of flight 1
    x_in1 = x_wall + sgn * (FLIGHT_W + WELL)               # well-side edge of flight 1
    x_in2 = x_wall + sgn * FLIGHT_W                        # well-side edge of flight 2
    y_bot = HALL_Y0 + RUNIN                                # bottom riser of flight 1 = top nosing of flight 2
    y_land = y_bot + (RISERS - 1) * TREAD                  # landing edge (top nosing of flight 1)
    h1 = zb + BOTTOM_RISER + (RISERS - 1) * RISER_H
    photo = "hall photo 2026-09-25 21:35 (map owner) + frames 070704360 t 13-28 s"
    f1 = {"type": "stairs_run", "name": f"{prefix}_Flight1", "top": c_to_w(xa, y_land), "dir_deg": NORTH + 180,
          "width": FLIGHT_W, "risers": RISERS, "riser_h": round(RISER_H, 4), "tread": TREAD, "z_top": z(h1),
          "bottom_riser_h": round(BOTTOM_RISER, 4), "material": "granite", **ev(f"{photo}: flight 1 on the hall side, rises north across the hall end, "
                                      f"{RISERS} risers, bottom riser {RUNIN:.2f} m from the south wall")}
    if not solid:
        f1["soffit_thk"] = SOFFIT
    els.append(f1)
    xs = sorted([x_wall, x_front])
    els.append(slab(f"{prefix}_Landing", xs[0], xs[1], y_land, HALL_Y1, zb - 0.1 if solid else h1 - 0.2, h1,
                    "granite", **ev(f"{photo}: half-landing {LANDING} m deep against the north hall wall (it meets the "
                                    "wall, not a room); white wall under it on F1")))
    els.append({"type": "stairs_run", "name": f"{prefix}_Flight2", "top": c_to_w(xb, y_bot), "dir_deg": NORTH,
                "width": FLIGHT_W, "risers": RISERS, "riser_h": round(RISER_H, 4), "tread": TREAD,
                "z_top": z(zb + STOREY), "material": "granite", "soffit_thk": SOFFIT,
                **ev(f"{photo}: flight 2 returns south along the end wall to the next floor; sloped soffit with the "
                     "exit door (east) / window + closet door (west, c38) under it")})
    rail = {"height": 0.95, "spacing": 0.12, "mid_rails": 0, "material": "white"}
    rev = ev(f"{photo}: white steel balustrade, vertical bars ~0.12 m, curled handrail end at the bottom")
    # flight 1 + landing: hall side (open to the hall)
    els.append({"type": "rail3d", "name": f"{prefix}_Rail1", **rail, **rev,
                "points": [c_to_w(x_front - sgn * 0.05, y_bot + TREAD) + [z(zb + BOTTOM_RISER + RISER_H)],
                           c_to_w(x_front - sgn * 0.05, y_land) + [z(h1)],
                           c_to_w(x_front - sgn * 0.05, HALL_Y1 - 0.05) + [z(h1)]]})
    # flight 1: well side too (map owner 2026-09-28: the open edge between the flights needs a balustrade)
    els.append({"type": "rail3d", "name": f"{prefix}_Rail1W", **rail, **rev,
                "points": [c_to_w(x_in1 - sgn * 0.05, y_bot + TREAD) + [z(zb + BOTTOM_RISER + RISER_H)],
                           c_to_w(x_in1 - sgn * 0.05, y_land) + [z(h1)]]})
    # flight 2: well side, from the landing up to the next floor; flight 1 well side (upper floors: void next to it)
    els.append({"type": "rail3d", "name": f"{prefix}_Rail2", **rail, **rev,
                "points": [c_to_w(x_in2 + sgn * 0.05, y_land) + [z(h1)],
                           c_to_w(x_in2 + sgn * 0.05, y_bot) + [z(zb + STOREY)],
                           c_to_w(x_in2 + sgn * 0.05, y_bot - 0.30) + [z(zb + STOREY)]]})
    if top_floor:  # guard round the stair opening on the last floor the stair reaches
        zt = zb + STOREY
        els.append({"type": "rail3d", "name": f"{prefix}_TopGuard", **rail, **rev,
                    "points": [c_to_w(x_in2 + sgn * 0.05, y_bot - 0.05) + [z(zt)],
                               c_to_w(x_front - sgn * 0.05, y_bot - 0.05) + [z(zt)],
                               c_to_w(x_front - sgn * 0.05, HALL_Y1 - 0.05) + [z(zt)]]})
    return els


def floor_slabs(k, zb, holes):
    """Slab of floor k (top at zb) over the whole plan minus the stair openings holes = {'W': bool, 'E': bool}."""
    y_bot = HALL_Y0 + RUNIN
    els, name = [], f"F{k}_Slab"
    t = "terrazzo" if k == 1 else "stone"
    z0 = zb - (0.15 if k == 1 else SLAB)
    for nm, (x0, x1, ys) in MID.items():
        els.append(slab(f"{name}_{nm}", x0, x1, ys, Y_N, z0, zb, t))
    for side, x0, x1, ys in (("W", X_W, FRONT_W, Y_S_WEST), ("E", FRONT_E, X_E, Y_S_EAST)):
        if holes.get(side):
            els.append(slab(f"{name}_{side}_S", x0, x1, ys, y_bot, z0, zb, t))
            els.append(slab(f"{name}_{side}_N", x0, x1, HALL_Y1, Y_N, z0, zb, t))
        else:
            els.append(slab(f"{name}_{side}", x0, x1, ys, Y_N, z0, zb, t))
    for e in els:
        e.update(ev("terrazzo floor (hall photo, lobby frames); FFL from BLD_C" if k == 1 else
                    f"F{k} structural slab at {k - 1} x 3.30 m; openings over the stair bays the stair reaches"))
    return els


def ceilings(k, zb, open_bays):
    """600x600 grid ceiling of floor k; none over the stair bays' hall strip where the stair continues up."""
    els = []
    zones = {nm: (x0, x1, ys, Y_N) for nm, (x0, x1, ys) in MID.items()}
    zones.update({"W_S": (X_W, FRONT_W, Y_S_WEST, HALL_Y0), "W_N": (X_W, FRONT_W, HALL_Y1, Y_N),
                  "E_S": (FRONT_E, X_E, Y_S_EAST, HALL_Y0), "E_N": (FRONT_E, X_E, HALL_Y1, Y_N),
                  "W_H": (X_W, FRONT_W, HALL_Y0, HALL_Y1), "E_H": (FRONT_E, X_E, HALL_Y0, HALL_Y1)})
    for nm, (x0, x1, y0, y1) in zones.items():
        if nm[-1] == "H" and open_bays.get(nm[0]):
            continue
        els.append(slab(f"F{k}_Ceiling_{nm}", x0, x1, y0, y1, zb + CEIL, zb + CEIL + 0.02, "white",
                        **ev("600x600 lay-in grid ceiling with 1-tile LED panels, 2.92 m (hall photo)", "medium")))
    return els


def plan(k, zb, lobby, stairs):
    """Hall walls, rooms, doors, WCs, accents of floor k (base zb). lobby: F1 entrance lobby in the tower bay (else a
    room over it). stairs = {'W': bool, 'E': bool}: the stair bay at that end exists on this floor (else offices)."""
    P, els = f"F{k}_", []
    lowev = "room partition between facade window bays (door and layout estimate)"
    # --- south side: rooms west and east of the tower bay ---------------------------------------------------------
    s_doors_w = [(FRONT_W + END_DOOR_OFF, DOOR_W), (LOB0 - 1.0, DOOR_W)]   # end room (by the stair), middle room
    s_doors_e = [(LOB1 + 1.0, DOOR_W), (FRONT_E - END_DOOR_OFF, DOOR_W)]
    a, b = (X_W, HALL_Y0 - PART), (X_E, HALL_Y0 - PART)
    if lobby:
        segs = [("Hall_S_West", (X_W, HALL_Y0 - PART), (LOB0, HALL_Y0 - PART), s_doors_w),
                ("Hall_S_East", (LOB1, HALL_Y0 - PART), (X_E, HALL_Y0 - PART), s_doors_e)]
    else:
        segs = [("Hall_S", a, b, s_doors_w + [((LOB0 + LOB1) / 2, DOOR_W)] + s_doors_e)]
    for nm, p, q, dd in segs:
        els.append(wall(P + nm, p, q, zb, openings=u_ops([(u - p[0], w) for u, w in dd]),
                        **ev("hall wall along the classrooms, full length to the end walls (map owner: the rooms "
                             "continue alongside the stair bays)")))
        for n, (u, w) in enumerate(dd):
            end = abs(u - FRONT_W - END_DOOR_OFF) < 0.01 or abs(u - FRONT_E + END_DOOR_OFF) < 0.01
            els.append(door(f"{P}Door_{nm[5:] or 'S'}{n}", p, q, u - p[0], zb,
                            **ev("black aluminium door, glass leaf with a mid rail, frame 0.99 x 2.05 (080420598); "
                                 + ("end room: 1.9-2.9 m in front of the stair (hall photo)" if end else
                                    "middle room: near its inner end (estimate)"), "medium" if end else "low")))
    els.append(wall(P + "Lobby_W", (LOB0, HALL_Y0 - PART), (LOB0, Y_S_WEST), zb,
                    **ev("tower bay side wall (F1: lobby with vending + coffee machine, 070704360 t 4-6 s)")))
    els.append(wall(P + "Lobby_E", (LOB1, Y_S_EAST), (LOB1, HALL_Y0 - PART), zb, **ev("tower bay side wall")))
    for nm, x in (("S_W12", PART_W), ("S_E12", PART_E)):
        y0 = Y_S_WEST if x < 12.8 else Y_S_EAST
        els.append(wall(f"{P}Room_{nm}", (x, y0), (x, HALL_Y0 - PART), zb, **ev(lowev, "low")))
    # --- north side: WCs straight ahead of the entrance, rooms left and right --------------------------------------
    wc_doors = [(13.4, WC_DOOR_W), (16.0, WC_DOOR_W)]
    n_doors = [(FRONT_W + END_DOOR_OFF, DOOR_W), (WC0 - 0.9, DOOR_W), (WC1 + 0.9, DOOR_W),
               (FRONT_E - END_DOOR_OFF, DOOR_W)] + wc_doors
    a, b = (X_E, HALL_Y1 + PART), (X_W, HALL_Y1 + PART)   # east->west so the thickness goes north
    els.append(wall(P + "Hall_N", a, b, zb, openings=u_ops([(a[0] - u, w) for u, w in n_doors]),
                    **ev("north hall wall, full length; the stair landings meet it (hall photo)")))
    for n, (u, w) in enumerate(n_doors):
        wc = (u, w) in wc_doors
        end = n in (0, 3)
        els.append(door(f"{P}{'Door_WC' if wc else 'Door_N'}{n}", a, b, a[0] - u, zb, width=w,
                        leaf="solid" if wc else "glass2",
                        **ev("WC: solid black leaf with a pictogram, straight ahead of the entrance (map owner, F_2.5)"
                             if wc else ("end room door 1.9-2.9 m in front of the stair (hall photo)" if end else
                                         "middle room door near its inner end (estimate)"),
                             "medium" if wc or end else "low")))
    for nm, x in (("N_W12", PART_W), ("WC_W", WC0), ("WC_Mid", (WC0 + WC1) / 2), ("WC_E", WC1), ("N_E12", PART_E)):
        els.append(wall(f"{P}Room_{nm}", (x, Y_N), (x, HALL_Y1 + PART), zb,
                        **ev("WC block: two narrow rooms (vestibule with 2 pedestal sinks + stalls, 075931189) behind "
                             "the doors straight ahead of the entrance; stacked on every floor" if "WC" in nm else lowev,
                             "low")))
    # --- hall end without a stair (F4 west): two offices across the hall end, one west window each --------------
    if not stairs.get("W", True):
        ym = (HALL_Y0 + HALL_Y1) / 2
        p, q = (FRONT_W, HALL_Y0), (FRONT_W, HALL_Y1)           # thickness to the left (west, inside the offices)
        dd = [(0.9 + DOOR_W / 2, DOOR_W), (HALL_W - 0.9 - DOOR_W / 2, DOOR_W)]
        els.append(wall(f"{P}Office_W_Front", p, q, zb, openings=u_ops(dd),
                        **ev("map owner: on F4 the west hall end holds 1-2 offices with windows instead of the stair; "
                             "front wall on the stair-bay line, two doors (estimate)", "low")))
        for n, (u, w) in enumerate(dd):
            els.append(door(f"{P}Door_Office_W{n}", p, q, u, zb, **ev("office door (estimate)", "low")))
        els.append(wall(f"{P}Office_W_Split", (FRONT_W - PART, ym), (X_W, ym), zb,
                        **ev("split between the two offices, one west window each (BLD_C west F4 y 7.7 / 10.0)", "low")))
    # --- accents, bulkheads, radiators, benches ----------------------------------------------------------------------
    for side, has in stairs.items():
        if not has:
            continue
        sg = 1 if side == "W" else -1
        xf = FRONT_W if side == "W" else FRONT_E
        xb = xf + sg * BULK_OFF
        els.append(slab(f"{P}Hall_Bulkhead_{side}", xb - 0.2, xb + 0.2, HALL_Y0, HALL_Y1, zb + CEIL - BEAM_D,
                        zb + CEIL, "white", **ev("plasterboard bulkhead across the hall in front of the stair zone "
                                                 "(hall photo: 3.9-4.2 m before the stair, underside 2.54 m)")))
        for wy, dy in ((HALL_Y0 + 0.01, "S"), (HALL_Y1 - 0.01, "N")):
            ud = xf + sg * END_DOOR_OFF
            near = ud - sg * (DOOR_W / 2 + 0.02)            # jamb on the hall-middle side
            x0, x1 = sorted([near, near - sg * 1.2])
            els.append({"type": "box", "name": f"{P}Accent_{dy}{side}_Side", "center": c_to_w((x0 + x1) / 2, wy),
                        "dir_deg": EAST, "size": [x1 - x0, 0.02, CEIL - 0.1], "z0": z(zb + 0.1), "material": "accent",
                        **ev("periwinkle-blue panel beside the end-room door, floor to ceiling (hall photo; red fire "
                             "alarm box on the north one)")})
            els.append({"type": "box", "name": f"{P}Accent_{dy}{side}_Head", "center": c_to_w(ud, wy),
                        "dir_deg": EAST, "size": [DOOR_W + 0.04, 0.02, CEIL - DOOR_H - 0.05],
                        "z0": z(zb + DOOR_H + 0.05), "material": "accent", **ev("blue panel above the door (hall photo)")})
        els.append({"type": "box", "name": f"{P}FireAlarm_{side}", "center": c_to_w(near - sg * 0.6, HALL_Y1 - 0.06),
                    "dir_deg": EAST, "size": [0.35, 0.10, 0.45], "z0": z(zb + 1.25), "material": "brick",
                    **ev("red fire-alarm / hose box on the blue panel (hall photo)", "low")})
    els.append({"type": "box", "name": f"{P}Accent_WC", "center": c_to_w((WC0 + WC1) / 2, HALL_Y1 - 0.01),
                "dir_deg": EAST, "size": [WC1 - WC0, 0.02, CEIL - 0.1], "z0": z(zb + 0.1), "material": "accent",
                **ev("blue accent wall around the two WC doors (F_2.5)")})
    for k2, x in enumerate((FRONT_W + 3.9, FRONT_E - 3.9)):
        els.append({"type": "box", "name": f"{P}Hall_Radiator_{k2}", "center": c_to_w(x, HALL_Y1 - 0.06),
                    "dir_deg": EAST, "size": [0.8, 0.08, 0.55], "z0": z(zb + 0.15), "material": "white",
                    **ev("white sectional radiator on the north hall wall 3.5-4.3 m in front of the stair (hall photo overlay)")})
    by = HALL_Y1 - 0.25
    for k2, x in enumerate((9.3, 20.1)):
        els.append({"type": "bench", "name": f"{P}Hall_Bench_N{k2}", "pos": c_to_w(x, by), "dir_deg": NORTH + 180,
                    "length": 1.8, "depth": 0.40, "seat_h": 0.45, "back": False, "z": z(zb),
                    **ev("wooden bench with 3 black cushions, no backrest, ~1.8 m (lobby frames F_8.5, F_12)", "low")})
    return els


def f5(zb):
    """F5 inside the hip roof: east stair arrival, corridor along the ridge, compact offices under the dormers."""
    P, els = "F5_", []
    lo = ev("map owner: F5 = compact teachers' offices inside the roof, low ceilings, lit by the dormers; layout "
            "estimate (not photographed)", "low")
    yc = 17.2 / 2 + 0.0
    y0c, y1c = yc - F5_CORR / 2, yc + F5_CORR / 2
    x0, x1 = X_W + 2.0, FRONT_E
    # corridor walls (with office doors) and knee walls
    doors_s = [(6.0, DOOR_W), (11.0, DOOR_W), (18.5, DOOR_W), (23.5, DOOR_W)]
    doors_n = [(6.0, DOOR_W), (11.0, DOOR_W), (18.5, DOOR_W), (23.5, DOOR_W)]
    els.append(wall(P + "Corr_S", (x0, y0c - PART), (x1, y0c - PART), zb, openings=u_ops([(u - x0, w) for u, w in doors_s]),
                    h=2.40, **lo))
    els.append(wall(P + "Corr_N", (x1, y1c + PART), (x0, y1c + PART), zb, openings=u_ops([(x1 - u, w) for u, w in doors_n]),
                    h=2.40, **lo))
    for side, (p, q) in {"S": (Y_S_WEST + KNEE_Y, None), "N": (Y_N - KNEE_Y, None)}.items():
        y = p
        a, b = ((x0, y - PART), (X_E, y - PART)) if side == "S" else ((X_E, y + PART), (x0, y + PART))
        els.append(wall(f"{P}Knee_{side}", a, b, zb, h=KNEE, **lo))
    for n, (u, w) in enumerate(doors_s):
        els.append(door(f"{P}Door_S{n}", (x0, y0c - PART), (x1, y0c - PART), u - x0, zb, **lo))
    for n, (u, w) in enumerate(doors_n):
        els.append(door(f"{P}Door_N{n}", (x1, y1c + PART), (x0, y1c + PART), x1 - u, zb, **lo))
    for x in (8.5, 14.7, 21.0, x0, x1):
        els.append(wall(f"{P}Office_S_{x:.0f}", (x, Y_S_WEST + KNEE_Y), (x, y0c - PART), zb, h=2.40, **lo))
        els.append(wall(f"{P}Office_N_{x:.0f}", (x, y1c + PART), (x, Y_N - KNEE_Y), zb, h=2.40, **lo))
    # flat corridor/office ceiling at 2.40 and sloped linings from the knee walls up to it
    els.append(slab(P + "Ceiling_Flat", x0, X_E, Y_S_WEST + KNEE_Y + (2.40 - KNEE) / ROOF_TAN,
                    Y_N - KNEE_Y - (2.40 - KNEE) / ROOF_TAN, zb + 2.40, zb + 2.43, "white", **lo))
    ys, yn = Y_S_WEST + KNEE_Y, Y_N - KNEE_Y
    dy = (2.40 - KNEE) / ROOF_TAN
    for side, (ya, yb) in {"S": (ys, ys + dy), "N": (yn, yn - dy)}.items():
        els.append({"type": "roof_plane", "name": f"{P}Ceiling_Slope_{side}", "thk": 0.03, "material": "white",
                    "ring": [c_to_w(x0, ya), c_to_w(X_E, ya), c_to_w(X_E, yb), c_to_w(x0, yb)],
                    "z": [z(zb + KNEE), z(zb + KNEE), z(zb + 2.40), z(zb + 2.40)], **lo})
    return els


def fittings_f1():
    els = []
    # the lobby vending machine, coffee kiosk and water cooler are placed by frames in INT_C_F1.json (F1_Vending,
    # F1_CoffeeKiosk, F1_WaterCooler); the generator's old copies duplicated them (map owner 2026-09-28)
    for nm, (x, y), size in ():
        els.append({"type": "box", "name": nm, "center": c_to_w(x, y), "dir_deg": NORTH, "size": size,
                    "z0": z(0.0), "material": "metal",
                    **ev("vending machine + bean-to-cup coffee machine + water cooler next to the entrance (070704360)",
                         "low")})
    # hall bulkheads at the lobby sides (F_2.5: two cross beams framing the entrance axis)
    for k, xb in enumerate((LOB0, LOB1)):
        # across the hall only (HALL_Y0..HALL_Y1): over the lobby it would enclose the lobby wall head (coplanar tops)
        els.append(slab(f"Hall_Beam_{k}", xb - 0.2, xb + 0.2, HALL_Y0, HALL_Y1, CEIL - 0.30, CEIL, "white",
                        **ev("plasterboard bulkheads crossing the hall at the lobby sides (frames F_2.5, F_8.5)")))
    return els


def build():
    y_bot = HALL_Y0 + RUNIN
    f1 = floor_slabs(1, 0.0, {}) + ceilings(1, 0.0, {"W": True, "E": True})
    f1 += plan(1, 0.0, lobby=True, stairs={"W": True, "E": True})
    f1 += stair_storey("StairW_F1", X_W, +1, 0.0, solid=True, top_floor=False)
    # janitor's closets under flight 2 of BOTH F1 stairs (map owner: "on F1 in both such places there are cleaners'
    # booths with ordinary brown doors"; west one seen in 070704360 t 19-22 s). Under the east flight the brown double
    # exit door sits south of it (BLD_C edge 4 u 5.0-6.86 = y 6.3-8.16), the closet fills the low part north of y 8.65.
    y_c = 8.65
    y_b = HALL_Y0 + RUNIN
    soff = lambda y: STOREY - RISER_H - SOFFIT * (TREAD ** 2 + RISER_H ** 2) ** 0.5 / TREAD - (y - y_b) * RISER_H / TREAD
    y_l = y_b + (RISERS - 1) * TREAD
    evc = ev("janitor's closet under flight 2, ordinary brown door (map owner; west: 070704360 t 19-22 s)", "medium")
    for side, xw, sg in (("W", X_W, +1), ("E", X_E, -1)):
        xo = xw + sg * FLIGHT_W                  # well-side face of the closet
        xa, xb = (xw, xo) if sg > 0 else (xo, xw)
        f1.append(wall(f"Closet_{side}_Front", (xb, y_c), (xa, y_c), h=soff(y_c) - 0.02, thk=0.12,
                       openings=[(FLIGHT_W / 2 - 0.42, FLIGHT_W / 2 + 0.42, DOOR_H + 0.02)], **evc))
        f1.append(door(f"Closet_{side}_Door", (xb, y_c), (xa, y_c), FLIGHT_W / 2, width=0.8, leaf="solid", wall_thk=0.12,
                       material="wood", **evc))
        f1.append({"type": "roof_plane", "name": f"Closet_{side}_Side", "thk": round(soff(y_c) + 0.1, 3), "material": "white",
                   "ring": [c_to_w(xo - sg * 0.12, y_c), c_to_w(xo, y_c), c_to_w(xo, y_l), c_to_w(xo - sg * 0.12, y_l)],
                   "z": [z(soff(y_c) - 0.02), z(soff(y_c) - 0.02), z(soff(y_l) - 0.02), z(soff(y_l) - 0.02)], **evc})
    f1 += stair_storey("StairE_F1", X_E, -1, 0.0, solid=True, top_floor=False)
    f1 += fittings_f1()
    up = []
    for k in (2, 3, 4):
        zb = (k - 1) * STOREY
        west = k <= 3                                     # west stair F1-F3 only (map owner)
        up += floor_slabs(k, zb, {"W": west, "E": True})
        up += ceilings(k, zb, {"W": k < 3, "E": True})
        up += plan(k, zb, lobby=False, stairs={"W": west, "E": True})
        if k < 3:
            up += stair_storey(f"StairW_F{k}", X_W, +1, zb, solid=False, top_floor=(k == 2))
        up += stair_storey(f"StairE_F{k}", X_E, -1, zb, solid=False, top_floor=(k == 4))
    up += floor_slabs(5, F5_Z, {"W": False, "E": True})
    up += f5(F5_Z)
    note = ("Block C interior (zone pass 2026-09-25, stair + hall from the map owner's hall photo). Topology from the "
            "map owner; hall width and stair ratios from the photo metrology; room partitions between window bays and "
            "middle-room doors are estimates (orange).")
    return ({"id": "INT_C_F1", "collection": "INT_C_F1", "note": note, "elements": f1},
            {"id": "INT_C_Floors", "collection": "INT_C_Floors", "note": note + " F2-F4 repeat F1 (room over the "
             "lobby); west stair F1-F3, east stair to F5; F4 west hall end = offices; F5 inside the roof.",
             "elements": up}), dict(hall=(round(HALL_Y0, 2), round(HALL_Y1, 2)), runin=round(RUNIN, 2), y_bot=round(y_bot, 2))


if __name__ == "__main__":
    specs, info = build()
    for spec in specs:
        out = os.path.join(REPO, "Art", "Blender", "Specs", spec["id"] + ".json")
        # since 2026-09-28 the specs carry hand edits "by frames" (fittings, WC layout, F2 lab): never overwrite them
        if os.path.exists(out) and "--force" not in sys.argv:
            out = os.path.join(os.environ.get("TEMP", "/tmp"), spec["id"] + ".gen.json")   # not in Specs: build_all reads every .json there
        json.dump(spec, open(out, "w"), indent=1)
        print(f"{out}: {len(spec['elements'])} elements")
    print(info)
