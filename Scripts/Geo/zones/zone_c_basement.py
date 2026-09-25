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
FFL = 5.53            # world z of the C ground floor (build_facades output, terrain-derived)
GRADE = FFL - 1.05    # plaza at the entrance: 7 risers x 0.15 below FFL (BLD_C plinth evidence)

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
TOP_C = np.array([-4.07, -0.88, GRADE - FFL])


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
CEIL = -0.13        # ceiling 2.30 m above the corridor floor (SfM 2.2-2.6 m); must stay under the sloped covers
X_END = m_to_c([7.0, 0, 0])[0]    # last frames of the segment (corridor continues toward the piano room)
# Grilled basement window in C's south wall, frame-x extent (m), fitted by overlay on frames 41/101/121.
WIN_M0, WIN_M1 = 1.5, 3.9


def build():
    x0 = TOP_C[0]
    z_top = TOP_C[2]
    x_land0 = x0 + (N1 - 1) * TREAD
    z_land = z_top - N1 * RISER
    x_land1 = x_land0 + LANDING
    x_corr0 = x_land1 + N2 * TREAD
    z_corr = z_land - N2 * RISER
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
        {"type": "slab", "name": "Corridor_Ceiling", "ring": ring_c(x_land0, X_END, CY_S, CY_N),
         "z0": FFL + CEIL, "z1": FFL + CEIL + 0.15, "material": "white",
         "evidence": ev_sfm + "; flat ceiling with downlights ~2.3 m above the corridor floor", "confidence": "medium"},
        # north wall of the stair = south face of the Dance Hall box, with the brown door at the mid landing
        {"type": "int_wall", "name": "Stair_Wall_N", "line": [c_to_w((x0 - 0.3, Y_N)), c_to_w((0.0, Y_N))],
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
         "z0": FFL + z_corr, "z1": FFL + CEIL, "thk": 0.3, "material": "white",
         "evidence": ev_sfm + "; plain wall with a grey tile dado (frames 100-150), under the red sloped covers",
         "confidence": "medium"},
    ]
    els.append({"type": "fence", "name": "Stair_Railing_S", "line": [c_to_w((x0 - 0.2, Y_S - 0.12)), c_to_w((x_corr0, Y_S - 0.12))],
                "height": 0.95, "post_spacing": 1.3, "post": 0.05, "panel": "bars",
                "evidence": "wrought-iron railing along the plaza side of the stairwell (map owner photo 10:55, 012507444)",
                "confidence": "medium"})
    for k, xm in enumerate((4.2, 5.0)):
        c = m_to_c([xm + 0.4, 0, 0])
        els.append({"type": "box", "name": f"Wardrobe_{k}", "center": c_to_w((c[0], CY_N - 0.3)), "dir_deg": east,
                    "size": [0.8, 0.6, 1.85], "z0": FFL + z_corr,
                    "evidence": "orange wooden wardrobes against C's south wall; front corner triangulated at x_m 4.2-4.3, "
                                "height 1.85 m (frames 110/120/130)", "confidence": "medium" if k == 0 else "low"})
    win = (m_to_c([WIN_M0, 0, 0])[0], m_to_c([WIN_M1, 0, 0])[0])
    hole = ring_c(x0 - 0.05, x_corr0 + 0.4, Y_S - 0.25, Y_N)   # open stairwell: cut the terrain heightfield here
    return {"id": "INT_C_Basement", "collection": "INT_C_Basement", "terrain_holes": [hole],
            "note": "Block C basement entry: sunken stair from the Dance Hall box, corridor along the south wall "
                    "(zone reconstruction 2026-09-25, direction corrected by the map owner).",
            "elements": els}, dict(z_corr=round(z_corr, 3), x_corr0=round(x_corr0, 3), window_x=[round(w, 2) for w in win],
                                   ceiling=CEIL, x_end=round(X_END, 2))


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
    json.dump(spec, open(out, "w"), indent=1)
    print("wrote", out, info)
    if WORK:
        json.dump(alignment(WORK), open(os.path.join(WORK, "align.json"), "w"), indent=1)
        print("wrote", os.path.join(WORK, "align.json"))
