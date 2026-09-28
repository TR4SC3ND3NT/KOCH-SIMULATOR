# Zone "C basement entry" (R1): measured geometry of the west basement stair + corridor of Block C, written as
# Art/Blender/Specs/INT_C_Basement.json (built by build_site.py) and the SfM->world alignment used by sfm_overlay.py.
# Measurements come from the pycolmap model of video PXL_20260925_012547860 (t 0-32 s, 159 frames, global mapper) in
# its gravity frame at 0.60 m/unit; every constant below cites how it was read. Run:
#   uv run --project Scripts python Scripts/Geo/zones/zone_c_basement.py <sfm_work_dir>
import json
import math
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK = sys.argv[1] if len(sys.argv) > 1 else None

# --- Block C local frame (Specs/BLD_C.json anchor) and levels -------------------------------------------------------
C_ORIGIN = np.array([173.264, -3.640])
C_X = np.array([0.99920, -0.03985])
C_Y = np.array([-C_X[1], C_X[0]])
FFL = 6.40            # world z of the C ground floor (build_facades output, terrain-derived)
# Ground at the SW corner / basement entry: 1.78 m below the C ground floor (0.73 m lower than the main entrance
# plaza). From the map owner's photo 10:55 (camera solved by PnP on 10 C window centres, 5 px rms): with this grade the
# stair railing reads 1.0 m and the roof post 2.2 m; the entry roof then meets C's west wall just under the F1 sills,
# as in the photo. Also consistent with the earlier note that the ground west of C is lower than the entrance plaza.
GW = -1.78
GRADE = FFL + GW
# Stair head / landing = the south plaza level (FFL - 7 risers x 0.15), NOT the lower west grade GW. 2026-09-25 photo
# match of video 070629483 (frames a06-a08, window PnP cameras): the brick-box corner base, both canopy-post bases and
# the stair-head railing base triangulate/ray-cast to -0.9..-1.17 below FFL; stills 012507444/012536150/061624280 and
# frame a10 show the granite landing one kerb above the paving that runs flat east to the entrance plaza (people's
# feet vs the horizon agree), and the model terrain there is already the 5.35 lower terrace. GW stays for the ground
# west of the shed (sloping paving north of the box, 012456258).
PLAZA = -1.05

# --- SfM metric frame (sfm_views --scale 0.60) -> C local -----------------------------------------------------------
# Scale 0.60 m/unit: stair profile tread 0.60 u / riser 0.231 u + Blondel 2h+b = 0.63 m -> 0.593; hand-held camera
# 2.5 u above the corridor floor -> 1.48 m; wardrobe (triangulated, 3 frames) 1.85 m tall. All three agree within 5 %.
SCALE = 0.60
# Top nosing of the stair (metric frame) = where the video starts at plaza level (photo 012543364 from the same spot).
TOP_M = np.array([-3.87, 0.12, -0.36])
# Placement (photos 012507444/012511910/012543364, map owner): from the granite landing in front of the "Dance Hall"
# brick box at the SW corner the stair descends EAST, parallel to C's south facade; the corridor below runs east along
# the south wall under the red sloped covers, its left (north) wall is C's south wall with the grilled basement window,
# the plaza with the planters is on the right. Frame +x (walking) = C +x (east), frame +y (left) = C +y (north).
# y: corridor north face (frame y_m +1.00) = C south wall face (y 0); x: the brick box ends / white C wall starts at
# frame x_m ~0.2 (frame 41: brick wall -> column -> white wall) = C SW corner (x 0).
TOP_C = np.array([-4.07, -0.88, PLAZA])


def m_to_c(q):
    q = np.asarray(q, float) - TOP_M
    return np.array([TOP_C[0] + q[0], TOP_C[1] + q[1], TOP_C[2] + q[2]])


def c_to_w(xy):
    return (C_ORIGIN + xy[0] * C_X + xy[1] * C_Y).round(3).tolist()


def ring_c(x0, x1, y0, y1):
    return [c_to_w((x0, y0)), c_to_w((x1, y0)), c_to_w((x1, y1)), c_to_w((x0, y1))]


HEADING = math.degrees(math.atan2(C_Y[1], C_Y[0]))   # world bearing of C +y (downhill direction of the stair)

# --- Measured elements (C local, metres; z relative to FFL) --------------------------------------------------------
RISER = 0.138       # SfM tread levels -0.60,-0.89,-1.13,-1.38,-1.61,-1.81,-1.99,-2.22,-2.45 u -> mean 0.231 u
TREAD = 0.36        # nosing breaks every 0.60 u (x -6.45 ... -2.25 u)
N1, N2 = 8, 2       # 8 risers to the mid landing (SfM levels), 2 into the corridor (photo 012543364 bottom)
Y_N, Y_S = m_to_c([0, 1.05, 0])[1], m_to_c([0, -0.80, 0])[1]   # stair wall faces (SfM wall peaks at x_m -1.5)
LANDING = 1.20      # mid landing depth: SfM gap between the 8th nosing (x_m -1.35) and the next edge; photo ~3 treads
CY_N, CY_S = 0.0, m_to_c([0, -1.00, 0])[1]   # corridor: C south wall face / retaining wall (SfM y_m +-1.00)
CEIL_H = 2.30       # corridor clear height (SfM 2.2-2.6 m); must stay under the sloped covers
# Sloped red covers over the corridor = BLD_C lightwell edge 0 (keep in sync): top at C's wall / at the outer edge (z rel
# FFL) and depth (m). 2026-09-25 frame b12 of 070647586 (PnP 11 px): the covers start right under the maroon plinth band
# and fall to a low fascia ~0.35 m above the paving (also 012526070, 061624280).
COVER_WALL, COVER_EDGE, COVER_DEPTH, COVER_T = -0.10, -0.70, 2.30, 0.06
X_END = m_to_c([7.0, 0, 0])[0]    # last frames of the segment (corridor continues toward the piano room)
# Grilled basement window in C's south wall, frame-x extent (m), fitted by overlay on frames 41/101/121.
WIN_M0, WIN_M1 = 1.5, 3.9


def cover_under(y):
    """Underside of the sloped covers at C-local y (<= 0, south of C's wall), z rel FFL."""
    return COVER_WALL + (COVER_EDGE - COVER_WALL) * min(-y, COVER_DEPTH) / COVER_DEPTH - COVER_T


def build():
    x0 = TOP_C[0]
    z_top = TOP_C[2]
    x_land0 = x0 + (N1 - 1) * TREAD
    z_land = z_top - N1 * RISER
    x_land1 = x_land0 + LANDING
    x_corr0 = x_land1 + N2 * TREAD
    z_corr = z_land - N2 * RISER
    CEIL = z_corr + CEIL_H
    cy = (Y_N + Y_S) / 2
    east = math.degrees(math.atan2(C_X[1], C_X[0]))
    ev_sfm = "SfM of video 012547860 (159 frames, global mapper, 0.60 m/unit), gravity frame from wall normals"
    ev_dir = "direction: stair descends east along C's south facade from the landing at the Dance Hall box (012507444/012511910)"
    els = [
        {"type": "stairs_run", "name": "Stair_Upper", "top": c_to_w((x0, cy)), "dir_deg": east, "width": Y_N - Y_S,
         "risers": N1, "riser_h": RISER, "tread": TREAD, "z_top": FFL + z_top, "run_out": LANDING,
         "evidence": ev_sfm + f"; {N1} risers x {RISER} m, treads {TREAD} m, width {Y_N - Y_S:.2f} m between the tile walls; "
         "granite treads (012543364); " + ev_dir, "confidence": "medium"},
        {"type": "stairs_run", "name": "Stair_Lower", "top": c_to_w((x_land1, cy)), "dir_deg": east, "width": Y_N - Y_S,
         "risers": N2, "riser_h": RISER, "tread": TREAD, "z_top": FFL + z_land, "run_out": 0.5,
         "evidence": "photo 012543364: 2 steps from the mid landing down to the corridor floor; riser as upper flight",
         "confidence": "medium"},
        {"type": "slab", "name": "Corridor_Floor", "ring": ring_c(x_corr0, X_END, CY_S, CY_N),
         "z0": FFL + z_corr - 0.2, "z1": FFL + z_corr,
         "evidence": ev_sfm + f"; floor {z_corr - z_top:.2f} m below the plaza ({N1 + N2} risers)", "confidence": "medium"},
        # ceiling lining directly under the sloped covers (the covers are the corridor roof since the stair head moved up
        # to the plaza level; the SfM 'flat 2.2-2.6 m' ceiling would pierce them): 2.2 m clear at C's wall, ~1.6 m at the
        # south wall
        {"type": "roof_plane", "name": "Corridor_Ceiling", "thk": 0.05, "material": "white",
         "ring": ring_c(x_corr0, X_END, CY_S, CY_N),
         "z": [FFL + cover_under(CY_S), FFL + cover_under(CY_S), FFL + cover_under(CY_N), FFL + cover_under(CY_N)],
         "evidence": ev_sfm + "; lining under the sloped covers (downlights), height from the covers (frame b12)",
         "confidence": "low"},
        # north wall of the stair = south face of the Dance Hall box, with the brown door at the mid landing
        # line 8 cm inside the Dance Hall wall (BLD_C DanceHallEntry, 0.4 m): its face is hidden inside the box above the
        # box base and continues the wall face below it; no coplanar / 1 cm layered faces with the box (z-fight)
        {"type": "int_wall", "name": "Stair_Wall_N", "line": [c_to_w((x0 - 0.3, Y_N + 0.08)), c_to_w((0.0, Y_N + 0.08))],
         "z0": FFL + z_corr, "z1": FFL + z_top + 0.9, "thk": 0.25, "material": "brick",
         "openings": [{"u0": x_land0 - x0 + 0.3 + 0.15, "u1": x_land0 - x0 + 0.3 + 1.05,
                       "z0": FFL + z_land, "z1": FFL + z_land + 2.0}],
         "evidence": "brick-effect tile wall on the left going down with a brown wooden door at the mid landing "
                     "(012543364, frames 1-10) = the Dance Hall box", "confidence": "medium"},
        # south side: tile retaining wall under the railing (stair), then the plain corridor wall with a grey dado
        {"type": "int_wall", "name": "Stair_Wall_S", "line": [c_to_w((x_corr0, Y_S)), c_to_w((x0 - 0.3, Y_S))],
         "z0": FFL + z_corr, "z1": FFL + z_top + 0.05, "thk": 0.25, "material": "brick",
         "evidence": "brick-tile retaining wall on the right side under the wrought-iron railing (frames 1-10, 70-80)",
         "confidence": "medium"},
        {"type": "int_wall", "name": "Corridor_Wall_S", "line": [c_to_w((X_END, CY_S)), c_to_w((x_corr0, CY_S))],
         "z0": FFL + z_corr, "z1": FFL + cover_under(CY_S), "thk": 0.3, "material": "brick",
         "evidence": ev_sfm + "; plain wall with a grey tile dado inside (frames 100-150); outside it is the low red-tile "
                     "parapet under the sloped covers (map owner photo 10:55)",
         "confidence": "medium"},
    ]
    du0 = x_land0 + 0.15
    els.append({"type": "box", "name": "DanceHall_Door", "center": c_to_w((du0 + 0.45, Y_N - 0.02)), "dir_deg": east,
                "size": [0.9, 0.04, 2.0], "z0": FFL + z_land, "material": "wood",
                "evidence": "brown wooden door at the mid landing in the Dance Hall wall (012543364, frames 1-10); leaf on the "
                            "wall face (the BLD_C box has no opening yet)", "confidence": "medium"})
    els.append({"type": "fence", "name": "Stair_Railing_S", "line": [c_to_w((x0 - 0.2, Y_S - 0.12)), c_to_w((x_corr0, Y_S - 0.12))],
                "height": 0.95, "post_spacing": 1.3, "post": 0.05, "panel": "bars",
                "evidence": "wrought-iron railing along the plaza side of the stairwell (map owner photo 10:55, 012507444)",
                "confidence": "medium"})
    # Entry roof: grey profiled-sheet canopy with a white soffit over the landing, the box and the stair head (frames
    # a05-a10 of 070629483, stills 012507444/012520140/012536150): near-flat, a little higher over the box; fascia 0.2 m;
    # front beam on two steel posts along the plaza side of the stairwell; east end ~0.3 m past C's SW corner line.
    # Heights from the a06-a08 cameras: post tops (beam underside) +0.87..+0.91, front top +1.17, top over the box
    # +1.28..+1.43; its north edge stays south of the F1 window of C's west wall (sill +1.05 from y 2.675, seen above it).
    R_W, R_E, R_S, R_N = -6.05, 0.30, Y_S - 0.35, 2.20
    Z_N, Z_S, R_T = 1.35, 1.12, 0.20
    zr = lambda y: Z_S + (Z_N - Z_S) * (y - R_S) / (R_N - R_S)
    ev_roof = ("frames a06-a08 of 070629483 (window-PnP cameras, 3-view triangulation): post tops +0.87..+0.91, front "
               "edge top +1.17, west verge over the box +1.28; flat grey sheet, white soffit (012507444, 012520140)")
    els.append({"type": "roof_plane", "name": "EntryRoof", "thk": R_T, "material": "metal",
                "ring": [c_to_w((R_W, R_S)), c_to_w((0.0, R_S)), c_to_w((0.0, R_N)), c_to_w((R_W, R_N))],
                "z": [FFL + Z_S, FFL + Z_S, FFL + Z_N, FFL + Z_N], "evidence": ev_roof, "confidence": "medium"})
    # east end past C's corner line only south of the south facade (y < 0)
    els.append({"type": "roof_plane", "name": "EntryRoof_E", "thk": R_T, "material": "metal",
                "ring": [c_to_w((0.0, R_S)), c_to_w((R_E, R_S)), c_to_w((R_E, -0.05)), c_to_w((0.0, -0.05))],
                "z": [FFL + Z_S, FFL + Z_S, FFL + zr(-0.05), FFL + zr(-0.05)], "evidence": ev_roof, "confidence": "low"})
    els.append({"type": "slab", "name": "Entry_Landing", "ring": ring_c(-5.8, x0 + 0.05, Y_S - 1.2, Y_N),
                "z0": FFL + PLAZA - 0.2, "z1": FFL + PLAZA + 0.05,
                "evidence": "pink granite landing in front of the Dance Hall box's south face, at the stair head, one kerb "
                            "above the plaza paving (012507444, frame a10 of 070629483)", "confidence": "medium"})
    # two steel posts under the front beam; spacing 2.9 m from the a06/a08 triangulation (post 1 -> post 2)
    for k, xp in enumerate((x0 - 0.1, x0 - 0.1 + 2.9)):
        els.append({"type": "box", "name": f"EntryRoof_Post{k}", "center": c_to_w((xp, Y_S - 0.2)), "dir_deg": east,
                    "size": [0.1, 0.1, Z_S - R_T - PLAZA + 0.3], "z0": FFL + PLAZA - 0.3, "material": "metal",
                    "evidence": "steel posts at the front of the entry roof: one by the stair head, one further east "
                                "(frames a06-a08 of 070629483, 012507444, 012536150)", "confidence": "medium"})
    for k, xm in enumerate((4.2, 5.0)):
        c = m_to_c([xm + 0.4, 0, 0])
        els.append({"type": "box", "name": f"Wardrobe_{k}", "center": c_to_w((c[0], CY_N - 0.3)), "dir_deg": east,
                    "size": [0.8, 0.6, 1.85], "z0": FFL + z_corr,
                    "evidence": "orange wooden wardrobes against C's south wall; front corner triangulated at x_m 4.2-4.3, "
                                "height 1.85 m (frames 110/120/130)", "confidence": "medium" if k == 0 else "low"})
    win = (m_to_c([WIN_M0, 0, 0])[0], m_to_c([WIN_M1, 0, 0])[0])
    hole = ring_c(x0 - 0.05, x_corr0 + 0.4, Y_S - 0.25, Y_N)   # open stairwell: cut the terrain heightfield here
    # lower ground west/south-west of C (see GW); blends back to the DEM surface over 8 m
    # 2026-09-26: the ground west / south-west of C is the plaza terrace (5.35 = FFL - 1.05), the same level as the
    # passage by the sports hall (SITE_HallCPassage) and the south plaza; the old 'GW' pad (4.62) made the landing float
    pad = {"ring": ring_c(-12.0, 1.0, -6.0, 12.5), "z": round(FFL + PLAZA - 0.02, 3), "blend": 1.0}
    # "ground": "pads" -> the plaza-side railing stands on the padded terrain (5.35 terrace), not the raw DEM
    return {"id": "INT_C_Basement", "collection": "INT_C_Basement", "ground": "pads", "terrain_holes": [hole], "terrain_pads": [pad],
            "note": "Block C basement entry: sunken stair from the Dance Hall box, corridor along the south wall "
                    "(zone reconstruction 2026-09-25, direction corrected by the map owner).",
            "elements": els}, dict(z_corr=round(z_corr, 3), x_corr0=round(x_corr0, 3), window_x=[round(w, 2) for w in win],
                                   ceiling=round(CEIL, 2), x_end=round(X_END, 2))


def alignment(work):
    f = json.load(open(os.path.join(work, "m_frame.json")))
    B, o = np.array(f["B"]), np.array(f["o"])
    M1 = np.eye(3)  # frame axes coincide with C local axes (x east, y north, z up)
    M2 = np.array([[C_X[0], C_Y[0], 0], [C_X[1], C_Y[1], 0], [0, 0, 1.0]])
    R = M2 @ M1 @ B
    t = M2 @ (M1 @ (-SCALE * B @ o - TOP_M) + TOP_C) + np.array([C_ORIGIN[0], C_ORIGIN[1], FFL])
    return {"scale": SCALE, "R": R.tolist(), "t": t.tolist(), "rms_m": -1,
            "note": "model units -> world; gravity from walls, yaw = corridor axis, origin = stair top nosing"}


if __name__ == "__main__":
    spec, info = build()
    out = os.path.join(REPO, "Art", "Blender", "Specs", "INT_C_Basement.json")
    if os.path.exists(out) and "--force" not in sys.argv:   # the spec carries hand edits "by frames" since 2026-09-28
        out = os.path.join(os.environ.get("TEMP", "/tmp"), "INT_C_Basement.gen.json")   # not in Specs: build_all reads every .json there
    json.dump(spec, open(out, "w"), indent=1)
    print("wrote", out, info)
    if WORK:
        json.dump(alignment(WORK), open(os.path.join(WORK, "align.json"), "w"), indent=1)
        print("wrote", os.path.join(WORK, "align.json"))
