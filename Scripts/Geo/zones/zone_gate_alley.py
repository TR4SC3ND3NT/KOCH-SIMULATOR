# Zone "gate + alley" (R1): writes Art/Blender/Specs/SITE_GateAlley.json. Geometry in the Block A local frame
# (x east along A's south face, y north, origin = A anchor), converted to world. Levels from the 2022 drone SfM
# cross-sections (sfm4, scaled by the 13.43 m B-A wall gap): the alley is FLAT at B's level, the planter strip 0.2 m
# below it and the walkway along A 1.35-1.44 m below, constant along the whole B frontage.
# Run: python3 Scripts/Geo/zones/zone_gate_alley.py
import json, math, sys

# phase-1 terrain quadratic (build_greybox fit), only for the gate plaza / south bank that really follow the ground
C = [5.7533, -0.9585, -2.3901, 0.0941, -0.2237, 0.0117]


def gz(x, y):
    X, Y = x / 100, y / 100
    return C[0] + C[1] * X + C[2] * Y + C[3] * X * X + C[4] * X * Y + C[5] * Y * Y

O = (158.84, -92.76)
n = math.hypot(0.999, -0.049)
XD = (0.999 / n, -0.049 / n)
YD = (-XD[1], XD[0])
ANG = math.degrees(math.atan2(XD[1], XD[0]))          # A frame rotation (deg)


def W(x, y):
    return [round(O[0] + XD[0] * x + YD[0] * y, 3), round(O[1] + XD[1] * x + YD[1] * y, 3)]


def ring(pts):
    return [W(*p) for p in pts]


X_WALL, X_CURB, X_RW = 1.28, -3.42, -1.22   # A west face, alley edge (= pavilion front), retaining wall walkway face
PAV_S, PAV_N, PIER = 6.75, 10.75, 0.6      # pavilion pier outer faces (A local y) = BLD_A_S porch u 16.0 / 12.0
S2_S, S2_N, S2_XT = PAV_S + PIER, 11.9, X_CURB + PIER   # pavilion stair: from the south pier to 1.15 m past the north one; top nosing behind the piers
RW_T = 0.3
A_FFL = 5.47          # shared Block A floor (BLD_A_*.json ffl_z)
WALK_Z = 5.35         # walkway along A: 0.12 below the floor (A_W deck edge ~0.1 above it, gallery zone)
DROP = 1.40           # drone SfM: walkway 1.35-1.44 below the alley (profiles Y 6-26)
ALLEY_Z = WALK_Z + DROP   # 6.75: flat alley (drone: +-0.04 over 24 m), ~0.17 below B's floor
B_NE_Y = 38.8         # B's NE corner in A local y (world y -54.0): end of the flat alley, descent steps start here


def zA(y):   # alley level: flat
    return ALLEY_Z


Y0, Y1 = 0.0, B_NE_Y
ZW0, ZW1 = WALK_Z, WALK_Z


def zw(y):   # walkway level: flat (A's floor is flat)
    return WALK_Z


PAD_Z = round(min(zw(Y0), zw(Y1 + 2)) - 0.35, 3)
r3 = lambda v: round(v, 3)

EV_DROP = ("aerial SfM of the 2022 drone shot (sfm4: 21 frames, 14.7k points, scaled by the B east wall - A west wall "
           "spacing 13.43 m): alley plane 0, planter soil -0.2, lower walkway -1.35 constant along the alley; "
           "8 risers on the south stair (7 red-granite + concrete kerb, 012218760) and on the pavilion stair (7 treads, "
           "012227815) -> 0.169 m")

els = []


def slab(name, pts_l, ztop_fn, thk, material, ev, conf, extra=None):
    """sloped solid (roof_plane): top z per vertex from ztop_fn(x_l, y_l)"""
    d = {"type": "roof_plane", "name": name, "ring": ring(pts_l), "z": [r3(ztop_fn(x, y)) for x, y in pts_l],
         "thk": thk, "material": material, "evidence": ev, "confidence": conf}
    if extra:
        d.update(extra)
    els.append(d)


# ---------------------------------------------------------------- south stair (plaza -> A SW corner landing)
t_dir = (0.467, -0.884)        # top nosing direction NNW -> SSE (A frame)
d_dir = (0.884, 0.467)         # downhill (ENE, bearing ~65 deg)
S1_W, S1_N, S1_T = 4.33, 8, 0.34
TNW = (-4.6, 3.6)   # manhole corner; the planter curb angles SW from the pavilion south pier to here
TSE = (TNW[0] + S1_W * t_dir[0], TNW[1] + S1_W * t_dir[1])
TC = ((TNW[0] + TSE[0]) / 2, (TNW[1] + TSE[1]) / 2)
RUN = (S1_N - 1) * S1_T
BNW = (TNW[0] + RUN * d_dir[0], TNW[1] + RUN * d_dir[1])
BSE = (TSE[0] + RUN * d_dir[0], TSE[1] + RUN * d_dir[1])
BC = ((BNW[0] + BSE[0]) / 2, (BNW[1] + BSE[1]) / 2)
zt1 = ALLEY_Z   # 8 measured risers x 0.173 from the walkway land exactly on the flat alley level (plaza = alley)
zb1 = zw(BC[1])
dir_w = math.degrees(math.atan2(XD[1] * d_dir[0] + YD[1] * d_dir[1], XD[0] * d_dir[0] + YD[0] * d_dir[1]))
els.append({"type": "stairs_run", "name": "SouthStair", "top": W(*TC), "dir_deg": r3(dir_w), "risers": S1_N,
            "riser_h": r3((zt1 - zb1) / S1_N), "tread": S1_T, "width": S1_W, "z_top": r3(zt1),
            "evidence": "wide granite flight (grey treads, red-granite risers, concrete kerb as the top riser) from the gate "
                        "plaza down NE to the landing at A's SW corner: 012218760 (8 risers, looking back up SW at the gate), "
                        "012208814 (from the top, looking down-flight at the 'A Block' corner, landing with a drain grate before it), 012258813 (looking S: top nosing runs away from the manhole at the "
                        "lawn-planter corner, both cheeks and the flight run to the east), bearing of 012218760 (view up-flight "
                        "~WSW: gate column left, blue bin right); position: ground rays of 012258813 with the booth-PnP camera "
                        "(f nominal 708 px: manhole/planter curb 1.5 m west of the pavilion front line; f 881: 2 m) and the "
                        "SW-angled curb south of the pavilion in 012251895 -> manhole corner 1.2 m west of the pier line, "
                        "+-1 m, "
                        "drone 2022 frames 26-31 s. " + EV_DROP,
            "confidence": "medium"})

els.append({"type": "path", "name": "Plaza_StairTop", "line": [W(TNW[0] - 0.8 * d_dir[0], TNW[1] - 0.8 * d_dir[1]),
            W(TSE[0] - 0.8 * d_dir[0], TSE[1] - 0.8 * d_dir[1])], "width": 1.6, "thk": 0.08, "surface": "herringbone_200x100",
            "evidence": "gate plaza paving up to the top nosing of the south stair (012258813)", "confidence": "medium"})

# ---------------------------------------------------------------- pavilion stair (alley -> walkway, between the piers)
S2_Y, S2_W, S2_T = (S2_S + S2_N) / 2, S2_N - S2_S, 0.34
zt2 = zA(S2_Y)
els.append({"type": "stairs_run", "name": "PavilionStair", "top": W(S2_XT, S2_Y), "dir_deg": r3(ANG), "risers": 8,
            "riser_h": r3((zt2 - zw(S2_Y)) / 8), "tread": S2_T, "width": S2_W, "z_top": r3(zt2),
            "evidence": "pink granite flight under the A entrance pavilion, from the south pier to ~1.2 m north of the north pier "
                        "(lower treads run further north, staggered, modelled straight), piers on a 0.6 m top landing, deep bottom "
                        "step 0.8 m into the walkway: 012227815 (7 treads + top), 012233382, 012305655 "
                        "(frontal: whole width between the piers drops), 012251895 (door floor ~0.9-1.4 below the pier bases), "
                        "drone 2022 f 29-31 s. " + EV_DROP,
            "confidence": "medium"})

slab("PavilionStair_TopLanding", [(X_CURB, S2_S), (S2_XT, S2_S), (S2_XT, S2_N), (X_CURB, S2_N)], lambda x, y: zA(y) + 0.02, 0.0,
     "stone", "herringbone top landing between the alley and the pavilion stair, the front piers stand on it (012305655)",
     "medium", {"thk": r3(zA(S2_S) - PAD_Z + 0.3)})

# ---------------------------------------------------------------- side stair + steel ramp opening (walkway <-> alley)
# The railed "north stair" of the first pass is not in the drone profiles (Y 18-22: walkway -1.38, planter -0.2).
# The only crossing is at Y ~24-35 (drone Y 30: -0.34 / -0.5 / -1.14 across the strip) = the granite side stair +
# steel grating ramp of 070309303 t28-31, modelled in SITE_Garden (AW_Stairs_Mid, AW_Ramp*): leave the strip open there.
GAP0, GAP1 = 24.2, 35.1          # A local y: stair south edge .. ramp foot north edge
RAMP_XW = -2.65                  # ramp west edge (A local x); planter stays west of it
# ---------------------------------------------------------------- lower walkway + landings (paving solids)
lowtop = lambda x, y: zw(y) + 0.0
slab("Walkway", [(X_RW, BNW[1]), (X_WALL + 0.12, BNW[1] - 0.6), (X_WALL + 0.12, Y1 + 0.5), (X_RW, Y1 + 0.5)], lowtop, 1.3, "stone",
     "herringbone walkway along A_S's west face, 2.5 m from the wall to the planter retaining wall (aerial SfM profile: "
     "walkway 2.0-2.5, planter 1.9, alley edge 4.7 m from the wall = pavilion front); A's west door opens onto it. " + EV_DROP,
     "medium")
slab("Landing_SW", [BNW, BSE, (2.6, BSE[1] + 0.55), (2.6, 3.2), (X_WALL + 0.12, 3.2), (X_WALL + 0.12, BNW[1] - 0.6), (X_RW, BNW[1])],
     lowtop, 1.3, "stone",
     "landing at the foot of the south stair in front of A's SW corner, clover pavers + drain grate (012208814), joins the "
     "walkway", "medium")
slab("Walkway_RampBay", [(RAMP_XW, GAP0 + 2.5), (X_RW, GAP0 + 2.5), (X_RW, GAP1), (RAMP_XW, GAP1)], lowtop, 1.3, "stone",
     "walkway paving under/around the steel ramp and at the foot of the side stair (070309303 t28-32)", "medium")

# ---------------------------------------------------------------- planters (upper level, soil 0.15-0.2 below the curb)
soil = lambda x, y: zA(y) - 0.15
slab("Planter_South", [TNW, BNW, (X_RW - RW_T, BNW[1]), (X_RW - RW_T, PAV_S + PIER), (X_CURB, PAV_S + PIER), (X_CURB, PAV_S)], soil, 0.0, "hedge",
     "raised bed between the south stair and the pavilion stair: lawn + one thuja in the open part (012205046, 012258813), "
     "bare soil under the pavilion (012233382); red granite cheeks with polished coping; the pavilion's south pier stands "
     "on its NW corner", "medium", {"thk": r3(zA(4) - 0.15 - PAD_Z + 0.2)})
slab("Planter_North", [(X_CURB, S2_N), (X_RW - RW_T, S2_N), (X_RW - RW_T, GAP0), (X_CURB, GAP0)], soil, 0.0, "hedge",
     "long lawn/shrub strip between the alley and the lower walkway north of the pavilion (thujas, low shrubs; drone 2022 "
     "shrubs): aerial SfM soil -0.2 m below the alley, 1.9 m wide; its south end is staggered along the pavilion stair "
     "(012227815, modelled straight)", "medium", {"thk": r3(zA(10) - 0.15 - PAD_Z + 0.2)})
slab("Planter_RampW", [(X_CURB, GAP0 + 2.5), (RAMP_XW, GAP0 + 2.5), (RAMP_XW, GAP1), (X_CURB, GAP1)], soil, 0.0, "hedge",
     "narrow lawn strip between the alley and the steel ramp (070309303 t31: red-edged bed left of the grating)", "medium",
     {"thk": r3(zA(30) - 0.15 - PAD_Z + 0.2)})
slab("Planter_NorthEnd", [(X_CURB, GAP1), (X_RW - RW_T, GAP1), (X_RW - RW_T, B_NE_Y), (X_CURB, B_NE_Y)], soil, 0.0, "hedge",
     "planter strip continues along A_W up to B's NE corner (drone Y 26-32, 070309303 t22-27 red-edged lawn with shrubs)",
     "medium", {"thk": r3(zA(36) - 0.15 - PAD_Z + 0.2)})

# retaining walls (walkway face) with polished coping 0.03 proud
cap = lambda x, y: zA(y) + 0.05
for name, y0, y1 in (("RetWall_South", BNW[1], PAV_S + PIER), ("RetWall_North", S2_N, GAP0), ("RetWall_NorthEnd", GAP1, B_NE_Y)):
    slab(name, [(X_RW - RW_T, y0), (X_RW, y0), (X_RW, y1), (X_RW - RW_T, y1)], cap, 0.0, "brick",
         "red rock-face granite block retaining wall (3-4 courses) with a polished pink granite coping between the planter "
         "and the walkway (012227815, 012231007, 012233382); height = alley - walkway", "medium",
         {"thk": r3(zA(y0) + 0.05 - PAD_Z + 0.2)})
    slab(name + "_Coping", [(X_RW - RW_T - 0.03, y0), (X_RW + 0.03, y0), (X_RW + 0.03, y1), (X_RW - RW_T - 0.03, y1)],
         lambda x, y: zA(y) + 0.08, 0.06, "stone", "polished granite coping", "medium")
# alley-edge curbs (red concrete, 0.1 wide, 0.08 proud of the alley); absolute z (the planter strip is inside the pad)
def strip(name, a, b, w, ztop, thk_to, material, ev, conf):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); nx, ny = dy / L * w, -dx / L * w   # right-hand offset
    pts = [a, b, (b[0] + nx, b[1] + ny), (a[0] + nx, a[1] + ny)]
    slab(name, pts, ztop, 0.0, material, ev, conf, {"thk": r3(max(ztop(*p) for p in pts) - thk_to)})
EV_CURB = "red concrete edging along the alley side of the planters (012205046, 012255312, 012251895, drone 2022)"
strip("Curb_PlanterSouth", TNW, (X_CURB, PAV_S), 0.1, lambda x, y: zA(y) + 0.08, PAD_Z - 0.2, "brick",
      EV_CURB + "; angles SW from the pavilion south pier to the manhole corner of the south stair", "medium")
strip("Curb_PlanterNorth", (X_CURB, S2_N), (X_CURB, GAP0), 0.1, lambda x, y: zA(y) + 0.08, PAD_Z - 0.2, "brick", EV_CURB, "medium")
strip("Curb_PlanterNorthEnd", (X_CURB, GAP0 + 2.5), (X_CURB, B_NE_Y), 0.1, lambda x, y: zA(y) + 0.08, PAD_Z - 0.2, "brick",
      EV_CURB, "medium")

# ---------------------------------------------------------------- south bank: raised bed + hedge strip in front of A's south face
up = lambda x, y: gz(*W(x, y))
Z_LAND = zw(3.2)
slab("SouthBed_Cheek", [TSE, BSE, (2.6, BSE[1] + 0.55), (2.6, -3.9), (-1.2, -3.9)],
     lambda x, y: (Z_LAND + 0.3) if (x, y) in (BSE, (2.6, BSE[1] + 0.55)) else up(x, y) + 0.35, 0.0, "hedge",
     "raised bed with conifers SE of the south stair, red-granite cheek wall along the stair (top ~0.35 above the plaza at "
     "the top of the flight, 012258813; ~0.3 above the landing at the foot, 012208814)", "medium",
     {"thk": r3(up(0.5, -1.5) + 0.35 - PAD_Z + 0.3)})
for name, x0, x1 in (("SouthBank_W", 2.6, 14.0), ("SouthBank_E", 14.0, 38.4)):
    slab(name, [(x0, -1.9), (x1, -1.9), (x1, 3.25), (x0, 3.25)],
         lambda x, y: (up(x, -1.9) + 0.35) if y < 0 else (Z_LAND + 0.3), 0.0, "hedge",
         "planted bank (hedge, pines, elms) between the clover path along the gate fence and A_S's south face, falling "
         "from the path parapet to A's lower ground floor (065934318: fluted precast parapet segments stepped along the "
         "path, clipped hedge behind, trees, A's ground-floor windows just above the hedge); slope shape assumed",
         "low", {"thk": r3(up(x0, -1.9) + 0.35 - PAD_Z + 0.3)})

# parapet + hedge along the path (upper level, outside the pad)
PAR = [(2.4, -2.5), (19.5, -2.9)]
els.append({"type": "wall", "name": "PathParapet_S", "line": ring(PAR), "height": 0.45, "thk": 0.2, "material": "stone",
            "evidence": "fluted precast concrete parapet segments (~0.45 m, stepped at joints) on the north edge of the clover "
                        "path from the booth's NE corner east along A_S (065934318 t2-t17); line ~2.3 m north of the gate "
                        "fence, estimated", "confidence": "low"})
els.append({"type": "hedge", "name": "PathHedge_S", "line": ring([(p[0], p[1] + 0.55) for p in PAR]), "width": 0.8,
            "height": 1.1, "top": "flat",
            "evidence": "clipped hedge directly behind the parapet, top ~1.0-1.2 m above the path (065934318)", "confidence": "low"})
for k, (x, y, h, cd, shape) in enumerate([(3.6, -1.5, 9.0, 4.5, "cone"), (8.5, -1.6, 11.0, 6.0, "round"),
                                          (13.8, -1.6, 8.0, 4.0, "cone"), (-0.8, -2.0, 10.0, 6.5, "round")]):
    els.append({"type": "tree", "name": f"BankTree_{k:02d}", "pos": W(x, y), "height": h, "crown_d": cd, "shape": shape,
                "trunk_d": 0.35, "crown_base": 2.2,
                "evidence": "pines and elms on the bank / beside the booth (065934318, 012258813 left, drone 2022 booth frames: "
                            "whitewashed elm trunk at the bench east of the booth)", "confidence": "low"})
for k, x in enumerate((4.0, 13.0)):
    els.append({"type": "lamp", "name": f"PathLamp_{k:02d}", "pos": W(x, -2.95), "height": 4.5, "head": "box",
                "evidence": "grey steel lamp posts standing at the parapet (065934318 t5-t8)", "confidence": "low"})
els.append({"type": "bin", "name": "PathBin", "pos": W(6.0, -3.05), "size": [0.4, 0.4, 0.75],
            "evidence": "ornamental black steel litter bin on scroll legs in front of the parapet (065934318 t5)", "confidence": "low"})

els.append({"type": "path", "name": "PathClover_S", "line": [W(2.4, -3.5), W(19.5, -3.9)], "width": 1.6, "thk": 0.08,
            "surface": "clover_paver_267x218", "evidence": "clover-paver path between the gate fence and the parapet, from "
            "the booth's east side east along A_S (065934318, 070021774 f7 bench)", "confidence": "low"})

# ---------------------------------------------------------------- upper alley paving + B-side shrub bed
bpt_B0, bdir = (147.256, -81.356), (0.04891, 0.9988)
bn = (0.9988, -0.04891)
Bw = lambda u, w: [round(bpt_B0[0] + bdir[0] * u + bn[0] * w, 3), round(bpt_B0[1] + bdir[1] * u + bn[1] * w, 3)]
# alley strip: west edge = B bed curb (1.6 m off B's wall), east edge = A curb line
ys, yn = -93.2, -52.0
def xw_B(y):
    return bpt_B0[0] + bdir[0] * (y - bpt_B0[1]) / bdir[1] + 1.6
def xe_A(y):
    yl = (y - O[1] - XD[1] * X_CURB) / YD[1]
    return W(X_CURB, yl)[0]
mid = lambda y: [(xw_B(y) + xe_A(y)) / 2, y]
YS2 = W(X_CURB, PAV_S + 0.05)[1]
xs2 = W(-4.45, 3.0)[0]
els.append({"type": "path", "name": "Alley_Paving_S", "line": [[r3((xw_B(ys) + xs2) / 2), ys], [r3((xw_B(YS2) + xs2) / 2), r3(YS2)]],
            "width": r3(xs2 - xw_B(-89)), "thk": 0.08, "surface": "herringbone_200x100",
            "evidence": "alley south of the pavilion, west of the angled planter curb (012205046, 012258813)", "confidence": "medium"})
els.append({"type": "path", "name": "Alley_Paving_Curb", "line": [W(TNW[0] - 0.75, TNW[1] - 0.2), W(X_CURB - 0.75, PAV_S + 0.25)],
            "width": 1.5, "thk": 0.08, "surface": "herringbone_200x100",
            "evidence": "alley paving along the angled planter curb", "confidence": "medium"})
ys = YS2
els.append({"type": "path", "name": "Alley_Paving", "line": [[r3(v) for v in mid(ys)], [r3(v) for v in mid(yn)]],
            "width": r3(xe_A(-75) - xw_B(-75)), "thk": 0.08, "surface": "herringbone_200x100 grey (2025 relay; clover pink 2022)",
            "evidence": "level alley from the gate to the square between B's shrub bed and A's planter edge (012249348, 012255312, "
                        "drone 2022 38.5 s); aerial SfM: flat, alley edge 7.9-8.0 m from B's east wall",
            "confidence": "medium"})
B_END_U = 27.2   # B's NE corner along its east face (u from bpt_B0): the tree bed runs to the end of B (map owner)
els.append({"type": "wall", "name": "BBed_Curb", "line": [Bw(6.9, 1.55), Bw(B_END_U, 1.55)], "height": 0.12, "thk": 0.12,
            "material": "stone", "evidence": "yellow/white painted concrete curb of the shrub bed along B's east face north "
                                             "of the porch (drone 2022 38.5 s, 012249348)", "confidence": "medium"})
els.append({"type": "hedge", "name": "BBed_Shrubs", "line": [Bw(7.4, 0.8), Bw(B_END_U - 0.4, 0.8)], "width": 1.1, "height": 1.2,
            "top": "round", "evidence": "rounded clipped shrubs along B's east wall (012249348, 012255312, drone)",
            "confidence": "medium"})
for k, u in enumerate((9.0, 14.8, 20.5, 25.6)):
    els.append({"type": "tree", "name": f"BBed_Thuja_{k:02d}", "pos": Bw(u, 0.8), "height": 3.8, "crown_d": 1.5,
                "shape": "cone", "trunk_d": 0.15, "crown_base": 0.3,
                "evidence": "conical thujas in the B shrub bed (012249348 spruce/thuja beyond the porch, drone 2022)",
                "confidence": "low"})

# ---------------------------------------------------------------- descent at B's NE corner (alley -> north path)
PATH_N_Z = 6.09                  # north path level (SITE_Garden / BLD_A_W pad AW_PathN, gallery zone)
X_PATH_W = -7.63                 # north path west edge (A local x at B's NE corner, world x 153.1)
N_STEPS = 5
els.append({"type": "stairs_run", "name": "Steps_BCorner", "top": W((X_PATH_W + X_CURB) / 2, B_NE_Y), "dir_deg": r3(ANG + 90),
            "risers": N_STEPS, "riser_h": r3((ALLEY_Z - PATH_N_Z) / N_STEPS), "tread": 0.35,
            "width": r3(X_CURB - X_PATH_W), "z_top": r3(ALLEY_Z), "material": "granite",
            "evidence": "map owner (2026-09-25 screenshot marks): a descent across the path right after the end of B; the "
                        "flat alley (drone SfM, B's level) meets the north path of the A_W zone (6.09) -> 0.66 m, 5 risers; "
                        "exact position and riser count to confirm (photo request)", "confidence": "low"})

# ---------------------------------------------------------------- terrain pad (lowered ground under the lower zone)
pad_l = [TNW, TSE, (TSE[0] + 0.33, -1.0), (38.6, -1.0), (38.6, 4.4), (2.5, 4.4), (2.5, Y1), (X_CURB, Y1), (X_CURB, PAV_S)]
# the whole planter strip is lowered and rebuilt as solids; terrain facets dipping at the pad edge stay under the
# alley paving strips (opaque) on the west and under the stair/bed solids elsewhere
spec = {
    "id": "SITE_GateAlley",
    "collection": "03_Site",
    "ground": "pads",
    "note": ("Alley from the gate north between Block B (west, level with the gate) and Block A_S (east). A_S stands "
             f"{DROP} m lower: a lower walkway along its west face, reached by the wide south stair from the gate plaza, the "
             "stair under the entrance pavilion and a railed stair at the planter's north end; planters with granite "
             "retaining walls between. Geometry designed in the A local frame (gen script in the R1 scratch "
             "~/koch_work/zone_gate/gen_alley.py), world XY here. Lower-level solids use absolute z; terrain_pads lower "
             f"TER_Ground under them to {PAD_Z}. REQUIRES A's FFL = {r3(zw(S2_Y) + 0.03)} (walkway at the west door) - see "
             "the note to the lead. Old AlleyParapet_W / AlleyHedge_W removed: that fluted parapet + hedge is along A_S's "
             "south side (path from the booth), not along B."),
    "terrain_pads": [{"ring": ring(pad_l), "z": PAD_Z, "blend": 0.0,
                      "evidence": "lower walkway zone at A_S's west/south side (see note)"},
                     {"name": "Alley_Flat", "ring": [[r3(xw_B(-88.0) - 1.6), -88.0], [r3(xe_A(-88.0)), -88.0],
                                                     [r3(W(X_CURB, B_NE_Y)[0]), r3(W(X_CURB, B_NE_Y)[1])],
                                                     [r3(xw_B(-54.0) - 1.6), -54.0]],
                      "z": r3(ALLEY_Z - 0.08), "blend": 1.5,
                      "evidence": "drone SfM: alley flat (+-0.04 m over 24 m) at B's level from the gate plaza to B's NE "
                                  "corner; paving 0.08 on top"}],
    "elements": els,
}
out = sys.argv[1] if len(sys.argv) > 1 else '/home/faust/KOCH-SIMULATOR/Art/Blender/Specs/SITE_GateAlley.json'
json.dump(spec, open(out, 'w'), indent=1, ensure_ascii=False)
print("wrote", out, len(els), "elements; PAD_Z", PAD_Z, "zw(0..26)", r3(ZW0), r3(ZW1), "A FFL target", r3(zw(S2_Y) + 0.03),
      "zA(S2_Y)", r3(zA(S2_Y)), "S1 top", r3(zt1), "bottom", r3(zb1), "rh", r3((zt1 - zb1) / 8))
