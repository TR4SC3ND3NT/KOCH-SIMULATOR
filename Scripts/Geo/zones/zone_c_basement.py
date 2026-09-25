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
# Placement: the stair descends north along Block C's west wall (plaza photos 012456258-012514370: sunken stair next to
# the brick box, railing parallel to the west facade); frame +x (walking direction) = C +y (north), frame +y = C -x.
TOP_C = np.array([-1.20, 0.40, GRADE - FFL])      # low confidence: +-0.5 m until an exterior photo is matched


def m_to_c(q):
    q = np.asarray(q, float) - TOP_M
    return np.array([TOP_C[0] - q[1], TOP_C[1] + q[0], TOP_C[2] + q[2]])


def c_to_w(xy):
    return (C_ORIGIN + xy[0] * C_X + xy[1] * C_Y).round(3).tolist()


def ring_c(x0, x1, y0, y1):
    return [c_to_w((x0, y0)), c_to_w((x1, y0)), c_to_w((x1, y1)), c_to_w((x0, y1))]


HEADING = math.degrees(math.atan2(C_Y[1], C_Y[0]))   # world bearing of C +y (downhill direction of the stair)

# --- Measured elements (C local, metres; z relative to FFL) --------------------------------------------------------
RISER = 0.138       # SfM tread levels -0.60,-0.89,-1.13,-1.38,-1.61,-1.81,-1.99,-2.22,-2.45 u -> mean 0.231 u
TREAD = 0.36        # nosing breaks every 0.60 u (x -6.45 ... -2.25 u)
N1, N2 = 8, 2       # 8 risers to the mid landing (SfM levels), 2 into the corridor (photo 012543364 bottom)
X_W, X_E = -2.13, -0.28     # stair wall faces (SfM wall peaks y_m +1.05 / -0.80 at x_m -1.5)
LANDING = 1.20      # mid landing depth: SfM gap between the 8th nosing (x_m -1.35) and the next edge; photo ~3 treads
CX_W, CX_E = -2.08, -0.08   # corridor wall faces (SfM y_m +1.00 / -1.00 at x_m 2.25-3.75; east face = C west wall)
CEIL = 0.02         # corridor ceiling ~2.45 m above its floor (SfM ceiling points 0.72-0.84 m vs floor -1.37..-1.80 m)
Y_CORR_END_W = m_to_c([4.47, 0, 0])[1]  # west wall ends (plan slice): opening to the next room / turn
# Grilled window in the corridor west wall, frame-x extent (m); fitted by overlaying frames 41/101/121 (iteration 2):
# it starts ~1 m past the stair foot and ends at the first wardrobe.
WIN_M0, WIN_M1 = 1.5, 3.9


def build():
    y0 = TOP_C[1]
    z_top = TOP_C[2]
    y_land0 = y0 + (N1 - 1) * TREAD
    z_land = z_top - N1 * RISER
    y_land1 = y_land0 + LANDING
    y_corr0 = y_land1 + (N2 - 1) * TREAD + TREAD
    z_corr = z_land - N2 * RISER
    cx = (X_W + X_E) / 2
    ev_sfm = "SfM of video 012547860 (159 frames, global mapper, 0.60 m/unit), gravity frame from wall normals"
    els = [
        {"type": "stairs_run", "name": "Stair_Upper", "top": c_to_w((cx, y0)), "dir_deg": HEADING, "width": X_E - X_W,
         "risers": N1, "riser_h": RISER, "tread": TREAD, "z_top": FFL + z_top, "run_out": LANDING,
         "evidence": ev_sfm + f"; {N1} risers x {RISER} m, treads {TREAD} m, width {X_E - X_W:.2f} m between the tile walls; "
         "granite treads (012543364)", "confidence": "medium"},
        {"type": "stairs_run", "name": "Stair_Lower", "top": c_to_w((cx, y_land1)), "dir_deg": HEADING, "width": X_E - X_W,
         "risers": N2, "riser_h": RISER, "tread": TREAD, "z_top": FFL + z_land, "run_out": 0.5,
         "evidence": "photo 012543364: 2 steps from the mid landing down to the corridor floor; riser as upper flight",
         "confidence": "medium"},
        {"type": "slab", "name": "Corridor_Floor", "ring": ring_c(CX_W, CX_E, y_corr0, Y_CORR_END_W + 2.5),
         "z0": FFL + z_corr - 0.2, "z1": FFL + z_corr,
         "evidence": ev_sfm + f"; floor {z_corr - z_top:.2f} m below the plaza ({N1 + N2} risers); SfM floor at x_m 0.75: "
         f"{-1.80 + 0.36 - 1.05:.2f} rel FFL (model {z_corr:.2f})", "confidence": "medium"},
        {"type": "slab", "name": "Corridor_Ceiling", "ring": ring_c(CX_W, CX_E, y_land0, Y_CORR_END_W + 2.5),
         "z0": FFL + CEIL, "z1": FFL + CEIL + 0.2, "material": "white",
         "evidence": ev_sfm + "; ceiling with downlights ~2.45 m above the corridor floor", "confidence": "medium"},
        {"type": "int_wall", "name": "Stair_Wall_W", "line": [c_to_w((X_W, y0 - 0.3)), c_to_w((X_W, y_corr0))],
         "z0": FFL + z_corr, "z1": FFL + z_top + 0.9, "thk": 0.25, "material": "brick",
         "openings": [{"u0": y_land0 - y0 + 0.3 + 0.15, "u1": y_land0 - y0 + 0.3 + 1.05,
                       "z0": FFL + z_land, "z1": FFL + z_land + 2.0}],
         "evidence": "brick-effect tile wall on the west (left going down) with a brown wooden door at the mid landing "
                     "(012543364, frames 1-10); top = brick box height", "confidence": "medium"},
        {"type": "int_wall", "name": "Stair_Wall_E", "line": [c_to_w((X_E, y_corr0)), c_to_w((X_E, y0 - 0.3))],
         "z0": FFL + z_corr, "z1": FFL + z_top + 0.05, "thk": 0.25, "material": "brick",
         "evidence": "brick-tile retaining wall on the east (right) side under the wrought-iron railing (frames 1-10, 70-80)",
         "confidence": "medium"},
        {"type": "int_wall", "name": "Corridor_Wall_W", "line": [c_to_w((CX_W, y_corr0)), c_to_w((CX_W, Y_CORR_END_W))],
         "z0": FFL + z_corr, "z1": FFL + CEIL, "thk": 0.3, "material": "white",
         "openings": [{"u0": m_to_c([WIN_M0, 0, 0])[1] - y_corr0, "u1": m_to_c([WIN_M1, 0, 0])[1] - y_corr0,
                       "z0": FFL + z_corr + 0.8, "z1": FFL + CEIL - 0.15}],
         "evidence": ev_sfm + "; big window with white hexagon grilles, sill at the grey dado top ~0.8 m, head just under "
                     "the ceiling; extent fitted by overlay on frames 41/101/121", "confidence": "medium"},
        {"type": "int_wall", "name": "Corridor_Wall_E", "line": [c_to_w((CX_E + 0.3, y_corr0)), c_to_w((CX_E + 0.3, Y_CORR_END_W + 2.5))],
         "z0": FFL + z_corr, "z1": FFL + CEIL, "thk": 0.3, "material": "white",
         "evidence": ev_sfm + "; plain wall with a grey tile dado (frames 100-150); coincides with the Block C west wall line",
         "confidence": "medium"},
    ]
    for k, xm in enumerate((4.25, 5.0)):
        c = m_to_c([xm + 0.4, 0, 0])
        els.append({"type": "box", "name": f"Wardrobe_{k}", "center": c_to_w((CX_W + 0.3, c[1])), "dir_deg": HEADING,
                    "size": [0.8, 0.6, 1.85], "z0": FFL + z_corr,
                    "evidence": "orange wooden wardrobes against the west wall; front corner triangulated at x_m 4.2-4.3, "
                                "height 1.85 m (frames 110/120/130)", "confidence": "medium" if k == 0 else "low"})
    return {"id": "INT_C_Basement", "collection": "INT_C_Basement",
            "note": "Block C west basement entry: sunken stair + corridor along the west wall (zone reconstruction 2026-09-25).",
            "elements": els}, dict(z_corr=z_corr, y_corr0=y_corr0)


def alignment(work):
    f = json.load(open(os.path.join(work, "m_frame.json")))
    B, o = np.array(f["B"]), np.array(f["o"])
    M1 = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1.0]])
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
