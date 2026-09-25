# Zone "C ground floor" (R1): Block C F1 interior (hall, entrance lobby, both staircases, WC entrances, room
# partitions, doors, fittings) written as Art/Blender/Specs/INT_C_F1.json for build_site.py. Plan in Block C local
# metres (x east along the south facade from the SW corner, y north, z above FFL); every constant cites its source.
# Layout topology from the map owner (docs/reference/campus.md, 2026-09-25); sizes from footage metrology.
# Run: uv run --project Scripts python Scripts/Geo/zones/zone_c_f1.py
import json
import math
import os

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
C_ORIGIN = np.array([173.264, -3.640])        # Specs/BLD_C.json anchor
C_X = np.array([0.99920, -0.03985])
C_Y = np.array([-C_X[1], C_X[0]])
FFL = 6.40                                    # C ground floor, world z (build_facades output)
EAST = math.degrees(math.atan2(C_X[1], C_X[0]))
NORTH = EAST + 90.0

# --- shell (BLD_C.json ring = outer faces, wall_thk 0.45) -------------------------------------------------------
T = 0.45
X_W, X_E = T, 29.4 - T                        # inner faces of the west / east walls
Y_N = 17.2 - T                                # inner face of the north wall
Y_S_WEST, Y_S_TOWER, Y_S_EAST = 0.0 + T, 1.9 + T, 1.3 + T
X_TOWER0, X_TOWER1 = 12.8, 16.6               # tower (entrance) bay, outer faces

# --- levels -------------------------------------------------------------------------------------------------------
STOREY = 3.30        # facade_fit 061621646: 3.29 m floor-to-floor
SLAB = 0.25          # structural slab (BLD_C basement slab_t)
CEIL = 3.00          # grid ceiling underside above FFL: 600x600 lay-in grid in the hall; corridor ceiling request open
BEAM_D = 0.30        # hall bulkheads under the grid ceiling (lobby frames F_2.5 / F_8.5: two cross beams)
DOOR_H, DOOR_W = 2.05, 0.99   # classroom door outer frame, person-scaled metrology (080420598, campus.md)
WC_DOOR_W = 0.90     # WC doors: solid black leaf, narrower than the glazed classroom doors (F_2.5)

# --- hall (corridor) ------------------------------------------------------------------------------------------------
# Map owner: WCs straight ahead from the entrance, the hall runs left and right to two mirrored stairs.
# Width 5.4 m = 9 ceiling tiles: the two LED panels of one row sit 3 tiles (1.8 m) apart on the hall axis (ceiling
# homography on frame F_2.5, 3.6 cm residual) and the hall reads as 3 panel pitches wide in F_8.5. Rooms on both sides
# then get ~5.2 m clear depth in the west wing, matching the 3-window bays of the facade.
HALL_W = 5.4
PART = 0.20                                   # partition thickness
HALL_Y0 = Y_S_WEST + (Y_N - Y_S_WEST - HALL_W - 2 * PART) / 2 + PART   # hall south face
HALL_Y1 = HALL_Y0 + HALL_W                                            # hall north face

# --- staircases: U-stairs at both hall ends, flights parallel to the end wall -----------------------------------------
# Frames 070704360 t 13-28 s: first flight rises across the hall end (to the right = north when facing west),
# half-landing at the far side, second flight returns along the end wall; 11 + 11 risers counted (0.150 m, 3.30 m),
# granite treads 0.30 m, white steel balustrade. Mirrored at the east end (map owner).
RISERS, RISER_H, TREAD = 11, STOREY / 22, 0.30
FLIGHT_W, WELL = 1.40, 0.20
STAIR_X = 2 * FLIGHT_W + WELL                 # bay depth along x
LANDING = HALL_W - (RISERS - 1) * TREAD - 0.35  # half-landing depth along y (0.35 m run-in at the bottom)


def c_to_w(x, y):
    return (C_ORIGIN + x * C_X + y * C_Y).round(3).tolist()


def ring(x0, x1, y0, y1):
    return [c_to_w(x0, y0), c_to_w(x1, y0), c_to_w(x1, y1), c_to_w(x0, y1)]


def z(v):
    return round(FFL + v, 3)


def ev(txt, conf="medium"):
    return {"evidence": txt, "confidence": conf}


def wall(name, a, b, openings=(), thk=PART, z1=CEIL, **kw):
    """Partition from C-local a to b (thickness to the LEFT of a->b); openings [(u0, u1, z1_rel)] along a->b."""
    L = float(np.hypot(b[0] - a[0], b[1] - a[1]))
    # openings start at the finished floor; the wall base sits inside the slab (an opening flush with the wall base
    # would make wall_piece emit duplicate bottom faces)
    ops = [{"u0": round(u0, 3), "u1": round(u1, 3), "z0": z(0.0), "z1": z(h)} for u0, u1, h in openings]
    assert all(0 < o["u0"] < o["u1"] < L for o in ops), (name, L, ops)
    return {"type": "int_wall", "name": name, "line": [c_to_w(*a), c_to_w(*b)], "z0": z(-0.10), "z1": z(z1),
            "thk": thk, "openings": ops, "material": "white", **kw}


def door(name, a, b, u_mid, width=DOOR_W, leaf="glass2", hinge="left", material="metal", **kw):
    """Door set centred at u_mid along the host wall a->b (same line as its int_wall)."""
    return {"type": "door", "name": name, "line": [c_to_w(*a), c_to_w(*b)], "u0": round(u_mid - width / 2, 3),
            "u1": round(u_mid + width / 2, 3), "z0": z(0.0), "z1": z(DOOR_H), "wall_thk": PART, "leaf": leaf,
            "mid": 1.0, "hinge": hinge, "material": material, **kw}


def u_ops(doors):
    return [(u - w / 2 - 0.02, u + w / 2 + 0.02, DOOR_H + 0.02) for u, w in doors]


def stair(prefix, x_wall, sgn):
    """U-stair at a hall end. x_wall = inner face of the end wall, sgn = +1 (west end, stair extends east) / -1."""
    els = []
    xa = x_wall + sgn * (FLIGHT_W + WELL + FLIGHT_W / 2)   # lower flight (hall side) centre line
    xb = x_wall + sgn * (FLIGHT_W / 2)                     # upper flight (end-wall side) centre line
    y_bot = HALL_Y0 + 0.35                                 # first nosing
    y_top1 = y_bot + (RISERS - 1) * TREAD                  # last nosing of flight 1 = landing edge
    h1 = RISERS * RISER_H
    # flight 1 rises north: 'top' is the top nosing line centre, dir = downhill (south)
    els.append({"type": "stairs_run", "name": f"{prefix}_Flight1", "top": c_to_w(xa, y_top1), "dir_deg": NORTH + 180,
                "width": FLIGHT_W, "risers": RISERS, "riser_h": round(RISER_H, 4), "tread": TREAD, "z_top": z(h1),
                "material": "granite", **ev("frames 070704360 t 15-22 s: 11 risers to the half-landing, granite treads")})
    y_l0, y_l1 = y_top1, HALL_Y1
    xs = sorted([x_wall, x_wall + sgn * STAIR_X])
    els.append({"type": "slab", "name": f"{prefix}_Landing", "ring": ring(xs[0], xs[1], y_l0, y_l1),
                "z0": z(h1 - 0.2), "z1": z(h1), "material": "granite",
                **ev("half-landing across both flights at the far side of the hall end (frames t 19-22 s)")})
    # flight 2 returns south along the end wall up to F2
    els.append({"type": "stairs_run", "name": f"{prefix}_Flight2", "top": c_to_w(xb, y_bot), "dir_deg": NORTH,
                "width": FLIGHT_W, "risers": RISERS, "riser_h": round(RISER_H, 4), "tread": TREAD,
                "z_top": z(STOREY), "material": "granite",
                **ev("frames t 23-28 s: second flight returns along the end wall, 11 risers to F2")})
    # balustrades: open side of flight 1 (towards the well) and the landing edge
    x_in = x_wall + sgn * (FLIGHT_W + WELL)
    els.append({"type": "rail3d", "name": f"{prefix}_Balustrade1",
                "points": [c_to_w(x_in, y_bot - 0.3) + [z(0.0)], c_to_w(x_in, y_bot) + [z(RISER_H)],
                           c_to_w(x_in, y_top1) + [z(h1)]],
                "height": 0.95, "spacing": 0.12, "mid_rails": 0, "material": "white",
                **ev("white steel balustrade, vertical bars ~0.12 m, rounded top rail (frames t 16-18 s)")})
    return els


def build():
    els = []
    # floor + ceiling + F2 slab (stair bays open above F1)
    els.append({"type": "slab", "name": "F1_Floor", "ring": ring(X_W, X_E, Y_S_WEST, Y_N), "z0": z(-0.15),
                "z1": z(0.0), "material": "terrazzo", **ev("terrazzo floor (lobby frames); FFL from BLD_C")})
    xw1, xe0 = X_W + STAIR_X, X_E - STAIR_X
    for nm, (x0, x1, y0, y1) in {"Mid": (xw1, xe0, Y_S_WEST, Y_N), "W_S": (X_W, xw1, Y_S_WEST, HALL_Y0 - PART),
                                 "W_N": (X_W, xw1, HALL_Y1 + PART, Y_N), "E_S": (xe0, X_E, Y_S_EAST, HALL_Y0 - PART),
                                 "E_N": (xe0, X_E, HALL_Y1 + PART, Y_N)}.items():
        els.append({"type": "slab", "name": f"F2_Slab_{nm}", "ring": ring(x0, x1, y0, y1), "z0": z(STOREY - SLAB),
                    "z1": z(STOREY), "material": "stone", **ev("F2 structural slab, 3.30 m storey")})
        els.append({"type": "slab", "name": f"F1_Ceiling_{nm}", "ring": ring(x0, x1, y0, y1), "z0": z(CEIL),
                    "z1": z(CEIL + 0.02), "material": "white",
                    **ev("600x600 lay-in grid ceiling with 1-tile LED panels; height to be taped (photo request)", "low")})
    # hall bulkheads at the lobby edges (F_2.5: two cross beams framing the entrance axis)
    for k, xb in enumerate((X_TOWER0 - 0.3, X_TOWER1 + 0.3)):
        els.append({"type": "slab", "name": f"Hall_Beam_{k}", "ring": ring(xb - 0.2, xb + 0.2, Y_S_TOWER, HALL_Y1),
                    "z0": z(CEIL - BEAM_D), "z1": z(CEIL), "material": "white",
                    **ev("plasterboard bulkheads crossing the hall at the lobby sides (frames F_2.5, F_8.5)")})

    # --- south side: entrance lobby in the tower bay, rooms west and east -----------------------------------------
    lob0, lob1 = X_TOWER0 - 0.3, X_TOWER1 + 0.3            # lobby opens onto the hall between the bulkheads
    # hall south wall, west part (rooms S1, S2), door centres near each room's east end
    s_doors_w = [(4.9, DOOR_W), (11.3, DOOR_W)]
    els.append(wall("Hall_S_West", (X_W + STAIR_X, HALL_Y0 - PART), (lob0, HALL_Y0 - PART),
                    openings=u_ops([(u - (X_W + STAIR_X), w) for u, w in s_doors_w])))
    for n, (u, w) in enumerate(s_doors_w):
        els.append(door(f"Door_S_W{n}", (X_W + STAIR_X, HALL_Y0 - PART), (lob0, HALL_Y0 - PART), u - (X_W + STAIR_X),
                        **ev("black aluminium door, two glass panes, frame 0.99 x 2.05 (080420598); blue accent panel "
                             "above (lobby frames); position within the room assumed", "low")))
    s_doors_e = [(18.1, DOOR_W), (24.5, DOOR_W)]
    els.append(wall("Hall_S_East", (lob1, HALL_Y0 - PART), (X_E - STAIR_X, HALL_Y0 - PART),
                    openings=u_ops([(u - lob1, w) for u, w in s_doors_e])))
    for n, (u, w) in enumerate(s_doors_e):
        els.append(door(f"Door_S_E{n}", (lob1, HALL_Y0 - PART), (X_E - STAIR_X, HALL_Y0 - PART), u - lob1,
                        **ev("as Door_S_W: glazed black aluminium classroom door; position assumed", "low")))
    # lobby side walls (tower bay) from the facade to the hall
    els.append(wall("Lobby_W", (lob0, HALL_Y0 - PART), (lob0, Y_S_WEST), thk=PART,
                    **ev("lobby = entrance tower bay; vending + coffee machine against its side (070704360 t 4-6 s)")))
    els.append(wall("Lobby_E", (lob1, Y_S_EAST), (lob1, HALL_Y0 - PART), thk=PART,
                    **ev("lobby east wall, mirror of Lobby_W")))
    # south room partitions (between window bays: S facade columns 3.52 / 8.13 / 10.69 and 18.62 / 21.21 / 25.9)
    for nm, x in (("S_W12", 6.0), ("S_E12", 23.0)):
        y0 = Y_S_WEST if x < 12.8 else Y_S_EAST
        els.append(wall(f"Room_{nm}", (x, y0), (x, HALL_Y0 - PART),
                        **ev("room partition between facade window bays (BLD_C south columns)", "low")))
    for nm, x0, x1 in (("S_WStair", X_W, X_W + STAIR_X), ("S_EStair", X_E - STAIR_X, X_E)):
        y0 = Y_S_WEST if x0 < 12.8 else Y_S_EAST
        els.append(wall(f"Room_{nm}_End", (x1 if x0 < 12.8 else x0, y0), (x1 if x0 < 12.8 else x0, HALL_Y0 - PART),
                        **ev("room beside the stair bay, same line as the stair edge", "low")))

    # --- north side: WCs straight ahead of the entrance, rooms left and right --------------------------------------
    wc0, wc1 = 12.3, 17.1                              # WC block (two rooms, 2.4 m each) centred on the entrance
    wc_doors = [(13.4, WC_DOOR_W), (16.0, WC_DOOR_W)]
    n_doors = [(5.8, DOOR_W), (10.9, DOOR_W), (18.6, DOOR_W), (23.7, DOOR_W)] + wc_doors
    a, b = (X_E - STAIR_X, HALL_Y1 + PART), (X_W + STAIR_X, HALL_Y1 + PART)   # east->west so thickness goes north
    L = b[0] - a[0]
    els.append(wall("Hall_N", a, b, openings=u_ops([(a[0] - u, w) for u, w in n_doors])))
    for n, (u, w) in enumerate(n_doors):
        wc = (u, w) in wc_doors
        els.append(door(("Door_WC" if wc else "Door_N") + str(n), a, b, a[0] - u, width=w,
                        leaf="solid" if wc else "glass2",
                        **ev("WC: solid black leaf with a pictogram, straight ahead of the entrance (map owner, F_2.5)"
                             if wc else "glazed black aluminium classroom door; position assumed", "medium" if wc else "low")))
    for nm, x in (("N_W12", 6.8), ("WC_W", wc0), ("WC_Mid", (wc0 + wc1) / 2), ("WC_E", wc1), ("N_E12", 22.6)):
        els.append(wall(f"Room_{nm}", (x, Y_N), (x, HALL_Y1 + PART),
                        **ev("WC block: two narrow rooms (vestibule with 2 pedestal sinks + stalls, 075931189) "
                             "behind the doors straight ahead of the entrance" if "WC" in nm else
                             "room partition between window bays (north facade assumed)", "low")))
    for x in (X_W + STAIR_X, X_E - STAIR_X):
        els.append(wall(f"Room_N_Stair_{'W' if x < 15 else 'E'}", (x, Y_N), (x, HALL_Y1 + PART),
                        **ev("room beside the stair bay", "low")))

    # --- staircases -------------------------------------------------------------------------------------------------
    els += stair("StairW", X_W, +1)
    els += stair("StairE", X_E, -1)

    # --- fittings -----------------------------------------------------------------------------------------------------
    by = HALL_Y1 - 0.25                                 # benches against the hall walls (backless, black cushions)
    for k, x in enumerate((8.3, 20.9)):
        els.append({"type": "bench", "name": f"Hall_Bench_N{k}", "pos": c_to_w(x, by), "dir_deg": NORTH + 180,
                    "length": 1.8, "depth": 0.40, "seat_h": 0.45, "back": False, "z": z(0.0),
                    **ev("wooden bench with 3 black cushions, no backrest, ~1.8 m (lobby frames F_8.5, F_12)")})
    for k, x in enumerate((8.3, 20.9)):
        els.append({"type": "bench", "name": f"Hall_Bench_S{k}", "pos": c_to_w(x, HALL_Y0 + 0.25), "dir_deg": NORTH,
                    "length": 1.8, "depth": 0.40, "seat_h": 0.45, "back": False, "z": z(0.0), **ev("as Hall_Bench_N", "low")})
    # vending + coffee machines on the lobby west wall, water cooler opposite (070704360 t 1-6 s)
    for nm, (x, y), size in (("Vending", (lob0 + 0.45, 3.4), [0.90, 0.85, 1.83]),
                             ("Coffee", (lob0 + 0.40, 4.5), [0.75, 0.70, 1.90]),
                             ("WaterCooler", (lob1 - 0.25, 3.0), [0.32, 0.32, 1.10])):
        els.append({"type": "box", "name": nm, "center": c_to_w(x, y), "dir_deg": NORTH, "size": size,
                    "z0": z(0.0), "material": "metal",
                    **ev("vending machine + bean-to-cup coffee machine + water cooler next to the entrance (070704360)",
                         "low")})
    # radiators under the hall wall lamps (steel panel radiators, F_12)
    for k, x in enumerate((9.8, 19.4)):
        els.append({"type": "box", "name": f"Hall_Radiator_{k}", "center": c_to_w(x, HALL_Y1 - 0.06), "dir_deg": EAST,
                    "size": [0.8, 0.08, 0.55], "z0": z(0.15), "material": "white",
                    **ev("white sectional radiator on the hall wall (F_12)", "low")})
    # blue accent panels over the doors (from the door head to the ceiling, 1.2 m wide)
    for u, w in [(u, w) for u, w in n_doors if (u, w) not in wc_doors]:
        els.append({"type": "box", "name": f"Accent_N_{u:.0f}", "center": c_to_w(u, HALL_Y1 - 0.01), "dir_deg": EAST,
                    "size": [1.2, 0.02, CEIL - DOOR_H - 0.05], "z0": z(DOOR_H + 0.05), "material": "accent",
                    **ev("periwinkle-blue accent panel above each classroom door (lobby frames)", "low")})
    els.append({"type": "box", "name": "Accent_WC", "center": c_to_w((wc0 + wc1) / 2, HALL_Y1 - 0.01), "dir_deg": EAST,
                "size": [wc1 - wc0, 0.02, CEIL - 0.1], "z0": z(0.0), "material": "accent",
                **ev("blue accent wall around the two WC doors (F_2.5)")})

    return {"id": "INT_C_F1", "collection": "INT_C_F1",
            "note": "Block C ground floor interior (zone pass 2026-09-25). Topology from the map owner; hall width from "
                    "the ceiling grid; stairs from riser counts; doors from person-scaled metrology. Room partitions "
                    "and door positions along the hall are estimates (orange) until the evacuation plan photo arrives.",
            "elements": els}


if __name__ == "__main__":
    spec = build()
    out = os.path.join(REPO, "Art", "Blender", "Specs", "INT_C_F1.json")
    json.dump(spec, open(out, "w"), indent=1)
    print(f"{out}: {len(spec['elements'])} elements; hall y {HALL_Y0:.2f}-{HALL_Y1:.2f}, landing {LANDING:.2f} m")
