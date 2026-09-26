# Zone "gate + alley" (R1): writes Art/Blender/Specs/SITE_GateAlley.json. Geometry in the Block A local frame
# (x east along A's south face, y north, origin = A anchor), converted to world.
# 2026-09-26 photo-match of 070309303 (all 76 frames at 2 fps): two-lens COLMAP SfM (zoom switch f38/f39 -> two
# cameras, 151 frames, 0.80 px), aligned to the A_S/A_W walls (ICP + picks + gravity from vertical lines), dense
# plane-sweep ground heights of every frame -> levels and plan positions below (A-local, m). The 2022 drone numbers
# were scaled by the model's B-A gap (13.43), which the SfM measures at ~12.6 (B's east wall ~0.8 m further east).
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


EV_SFM = ("070309303 photo-match 2026-09-26 (two-lens SfM aligned to the A walls, dense plane-sweep heights of all 76 "
          "frames, per-frame overlays)")
X_WALL = 1.28          # A_S west face
X_DECK = 2.05          # A_W facade line: loggia deck edge (posts x 2.3), door bay front 2.2 (BLD_A_W)
Y_AW = 22.75           # A_S / A_W junction
X_PAV = -4.15          # pavilion front piers' outer face = alley edge at the pavilion (SfM face points -4.10..-4.26)
PAV_S, PAV_N, PIER = 6.6, 9.6, 0.5    # pavilion pier outer faces (A local y) = BLD_A_S porch piers_u 15.9 / 13.4
S2_S, S2_N, S2_XT = PAV_S + PIER, PAV_N + 1.15, X_PAV + PIER   # pavilion stair: south pier -> 1.15 m past the north one
X_CURB = -3.3          # red curb (alley side) of the lawn strip at y 15, face; curb 0.1 wide
# the curb is NOT parallel to A: red-curb sweep points (all frames, z 6.4-6.5) at x -3.35 (y 13-18), -3.05 (y 20-22),
# -2.55 (y 28), -2.45 (y 33-34), -2.25 (y 37) -> the lawn strip narrows northwards
xc = lambda y: X_CURB - 0.05 + 0.0458 * (y - 13.0)
X_SC = -3.85           # red curb of the south bed, from the pavilion's south pier down to the manhole (f04 ground rays)
X_BT, X_BB = -0.6, 0.15   # bank top / bank foot = walkway curb (0.12 wide) north of the pavilion
X_RW, RW_T = -1.45, 0.3   # south bed retaining wall walkway face (coping rays f04/f05: -1.45..-1.9)
A_FFL = 5.47           # shared Block A floor (BLD_A_*.json ffl_z)
WALK_Z = 5.35          # walkway along A: 0.12 below the floor; deck/walkway continuous in the sweep
ALLEY_S, ALLEY_N = 6.75, 6.63   # alley south of y 10 (pavilion, gate plaza) / north of y 15 (lawn strip, B frontage)
# sweep: path along the lawn strip 1.26 +-0.05 above the walkway/deck (y 12-40 flat within +-0.05), the alley at the
# pavilion and the gate plaza 0.12-0.2 higher; drone 1.35-1.44 x 0.94 (true B-A gap) = 1.27-1.35
Y_STAIR_N = 40.45      # top nosing of the wide stair north of the alley (f74 ground rays, pink granite band)


def zA(y):   # alley level
    if y <= 10.0:
        return ALLEY_S
    if y >= 15.0:
        return ALLEY_N
    return ALLEY_S + (ALLEY_N - ALLEY_S) * (y - 10.0) / 5.0


def zw(y):   # walkway level: flat (A's floor is flat)
    return WALK_Z


Y0, Y1 = 0.0, Y_STAIR_N
PAD_Z = round(WALK_Z - 0.35, 3)
r3 = lambda v: round(v, 3)

EV_DROP = ("levels: " + EV_SFM + ": walkway/deck 1.26 below the path along the lawn strip, alley 0.12-0.2 higher at the "
           "pavilion/gate plaza; 8 risers on the south stair (012218760) and on the pavilion stair (012227815)")

els = []


def slab(name, pts_l, ztop_fn, thk, material, ev, conf, extra=None):
    """sloped solid (roof_plane): top z per vertex from ztop_fn(x_l, y_l)"""
    d = {"type": "roof_plane", "name": name, "ring": ring(pts_l), "z": [r3(ztop_fn(x, y)) for x, y in pts_l],
         "thk": thk, "material": material, "evidence": ev, "confidence": conf}
    if extra:
        d.update(extra)
    els.append(d)


def strip(name, a, b, w, ztop, thk_to, material, ev, conf):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); nx, ny = dy / L * w, -dx / L * w   # right-hand offset
    pts = [a, b, (b[0] + nx, b[1] + ny), (a[0] + nx, a[1] + ny)]
    slab(name, pts, ztop, 0.0, material, ev, conf, {"thk": r3(max(ztop(*p) for p in pts) - thk_to)})


# ---------------------------------------------------------------- south stair (plaza -> A SW corner landing)
t_dir = (0.467, -0.884)        # top nosing direction NNW -> SSE (A frame)
d_dir = (0.884, 0.467)         # downhill (ENE, bearing ~65 deg)
S1_W, S1_N, S1_T = 4.33, 8, 0.34
# manhole corner: the south-bed curb runs straight from the pavilion's south pier to the manhole (f04 ground rays at
# the plaza level: curb x -3.91..-4.01 for y 0.9-3.7, manhole ~(-3.9, 0.4)); the bed's SE coping corner at (-1.7, 1.5)
# (f05 rays) -> the stair's north cheek starts here, 2.6 m further south than the first-pass estimate (-4.6, 3.6)
TNW = (-4.0, 1.0)
TSE = (TNW[0] + S1_W * t_dir[0], TNW[1] + S1_W * t_dir[1])
TC = ((TNW[0] + TSE[0]) / 2, (TNW[1] + TSE[1]) / 2)
RUN = (S1_N - 1) * S1_T
BNW = (TNW[0] + RUN * d_dir[0], TNW[1] + RUN * d_dir[1])
BSE = (TSE[0] + RUN * d_dir[0], TSE[1] + RUN * d_dir[1])
BC = ((BNW[0] + BSE[0]) / 2, (BNW[1] + BSE[1]) / 2)
zt1 = zA(TC[1])
zb1 = zw(BC[1])
dir_w = math.degrees(math.atan2(XD[1] * d_dir[0] + YD[1] * d_dir[1], XD[0] * d_dir[0] + YD[0] * d_dir[1]))
els.append({"type": "stairs_run", "name": "SouthStair", "top": W(*TC), "dir_deg": r3(dir_w), "risers": S1_N,
            "riser_h": r3((zt1 - zb1) / S1_N), "tread": S1_T, "width": S1_W, "z_top": r3(zt1),
            "evidence": "wide granite flight (grey treads, red-granite risers, concrete kerb as the top riser) from the gate "
                        "plaza down NE to the landing at A's SW corner: 012218760 (8 risers), 012208814, 012258813; "
                        "070309303 f05 (lower treads beyond the bed coping, drain grate on the landing). Position: NW top "
                        "corner at the manhole, " + EV_SFM + ". NOTE: SfM heights of the landing (f03-f09, rotation-only "
                        "frames, short tracks) read ~0.6 m below the door walkway - not adopted (photo request)",
            "confidence": "medium"})

els.append({"type": "path", "name": "Plaza_StairTop", "line": [W(TNW[0] - 0.8 * d_dir[0], TNW[1] - 0.8 * d_dir[1]),
            W(TSE[0] - 0.8 * d_dir[0], TSE[1] - 0.8 * d_dir[1])], "width": 1.6, "thk": 0.08, "surface": "herringbone_200x100",
            "evidence": "gate plaza paving up to the top nosing of the south stair (012258813)", "confidence": "medium"})

# ---------------------------------------------------------------- pavilion stair (alley -> walkway, between the piers)
S2_Y, S2_W, S2_T = (S2_S + S2_N) / 2, S2_N - S2_S, 0.34
zt2 = zA(S2_Y)
S2_FOOT = S2_XT + 7 * S2_T + S2_T            # walkway side of the bottom tread
els.append({"type": "stairs_run", "name": "PavilionStair", "top": W(S2_XT, S2_Y), "dir_deg": r3(ANG), "risers": 8,
            "riser_h": r3((zt2 - zw(S2_Y)) / 8), "tread": S2_T, "width": S2_W, "z_top": r3(zt2),
            "evidence": "pink granite flight under the A entrance pavilion, from the south pier to ~1.15 m past the north "
                        "pier (lower treads run further north, staggered, modelled straight): 012227815 (7 treads + top), "
                        "012233382, 012305655; 070309303 f04/f09 (flight down to the east between the piers); piers moved "
                        "with the pavilion (" + EV_SFM + ")", "confidence": "medium"})

slab("PavilionStair_TopLanding", [(X_PAV, S2_S - PIER), (S2_XT, S2_S - PIER), (S2_XT, S2_N), (X_PAV, S2_N)],
     lambda x, y: zA(y) + 0.02, 0.0, "stone",
     "herringbone top landing between the alley and the pavilion stair, the front piers stand on it (012305655)",
     "medium", {"thk": r3(zA(S2_S) - PAD_Z + 0.3)})

# ---------------------------------------------------------------- lower walkway + landings (paving solids)
lowtop = lambda x, y: zw(y) + 0.0
Y_WS = min(BNW[1], 2.0)
slab("Walkway_South", [(X_RW, Y_WS), (X_WALL + 0.12, Y_WS - 0.6), (X_WALL + 0.12, S2_N), (S2_FOOT, S2_N), (S2_FOOT, S2_S),
                       (X_RW, S2_S)], lowtop, 1.3, "stone",
     "walkway along A_S's west face from the south landing to the pavilion stair foot, A's west door opens onto it "
     "(070309303 f05/f06). " + EV_DROP, "medium")
slab("Landing_SW", [BNW, BSE, (2.6, BSE[1] + 0.55), (2.6, 3.2), (X_WALL + 0.12, 3.2), (X_WALL + 0.12, Y_WS - 0.6), (X_RW, Y_WS)],
     lowtop, 1.3, "stone",
     "landing at the foot of the south stair in front of A's SW corner, clover pavers + drain grate (012208814, 070309303 "
     "f05: grate at A-local (0.7, 2.85) just south of the corner), joins the walkway", "medium")
X_WC = X_BB + 0.12     # walkway (lower) edge behind the curb
slab("Walkway_North", [(X_WC, S2_N), (X_WALL + 0.12, S2_N), (X_WALL + 0.12, Y_AW), (X_DECK + 0.05, Y_AW),
                       (X_DECK + 0.05, Y1 + 0.5), (X_WC, Y1 + 0.5)], lowtop, 1.3, "stone",
     "lower walkway: 1.0 m wide along A_S (curb x 0.15-0.27 .. wall 1.28), ~1.8 m along the A_W loggia up to its deck "
     "edge (x 2.05); sweep: walkway and deck at one level, 1.26 below the path; " + EV_SFM, "medium")

# ---------------------------------------------------------------- south bed (between the south stair and the pavilion)
soilS = lambda x, y: (zA(y) - 0.25) + ((zw(y) + 0.45) - (zA(y) - 0.25)) * (x - X_SC) / ((X_RW - RW_T) - X_SC)
slab("Planter_South", [TNW, BNW, (X_RW - RW_T, BNW[1]), (X_RW - RW_T, S2_S), (X_SC, S2_S), (X_SC, TNW[1])], soilS, 0.0, "hedge",
     "raised bed between the south stair and the pavilion stair: lawn, one thuja, hydrangeas (070309303 f04-f06); soil "
     "slopes from the curb (~0.25 below the plaza) down to the pink coping ~0.5 above the walkway (f04/f05, sweep 5.6-6.4 "
     "across it); " + EV_SFM, "medium", {"thk": r3(zA(4) - PAD_Z + 0.2)})
els.append({"type": "tree", "name": "SouthBed_Thuja", "pos": W(-2.75, 4.9), "z": r3(soilS(-2.75, 4.9)), "height": 1.6,
            "crown_d": 0.9, "shape": "cone", "trunk_d": 0.08, "crown_base": 0.15,
            "evidence": "conical thuja in the south bed (070309303 f04: centre of the bed, ~1.6 m)", "confidence": "low"})
cap = lambda x, y: zw(y) + 0.47
slab("RetWall_South", [(X_RW - RW_T, BNW[1]), (X_RW, BNW[1]), (X_RW, S2_S), (X_RW - RW_T, S2_S)], cap, 0.0, "brick",
     "red rock-face granite retaining wall of the south bed along the walkway, ~0.5 m (people's knee height, 070309303 "
     "f04-f06), pink polished coping", "medium", {"thk": r3(zw(3) + 0.47 - PAD_Z + 0.2)})
slab("RetWall_South_Coping", [(X_RW - RW_T - 0.03, BNW[1]), (X_RW + 0.03, BNW[1]), (X_RW + 0.03, S2_S), (X_RW - RW_T - 0.03, S2_S)],
     lambda x, y: zw(y) + 0.52, 0.06, "stone", "polished pink granite coping (070309303 f04/f05)", "medium")
strip("Curb_PlanterSouth", TNW, (X_SC, S2_S - PIER), 0.1, lambda x, y: zA(y) + 0.08, PAD_Z - 0.2, "brick",
      "red concrete edging of the south bed, straight from the manhole to the pavilion's south pier (070309303 f04)", "medium")

# ---------------------------------------------------------------- lawn strip north of the pavilion (A side)
# sweep profiles (y 12-40): path, red curb at x -3.3, lawn falling ~0.3 from the curb to the bank top at x -0.6 (cloud
# 6.48 -> 6.17), pink coping 0.3 wide along the bank top (070309303 f55/f56 south of the side stair, f71 north of it),
# then a steep grass bank down to the low pink curb at x 0.15. The side stair + steel ramp cut the strip at y 29.3-32.64.
PATH_T = lambda y: zA(y) - 0.06   # walkable top of the alley paving (pad zA-0.08 + 'path' 0.02)
X_CP = X_BT - 0.3                 # bank-top coping, west face (coping x -0.9 .. -0.6)
Y_LN = Y_STAIR_N - 0.3            # lawn strip north end (coping)
lawn = lambda x, y: PATH_T(y) - 0.30 * (x - xc(y)) / (X_BT - xc(y))
bank = lambda x, y: lawn(X_BT, y) if x <= X_BT + 1e-6 else (zw(y) + 0.12)

# ---------------------------------------------------------------- side stair + steel ramp (070309303 f55-f68)
# All A-local, measured on the two-lens SfM of 070309303 (plane-sweep tread heights of all frames + triangulated rail
# posts / coping corners on the undistorted frames, 0.2-5 px): 7 granite risers of 0.171 (sweep treads 6.46 6.28 6.09
# 5.94 5.76 5.59 5.44 -> walkway 5.26, cloud z), nosings x -2.27 -1.75 -1.33 -0.92 -0.50 -0.12 0.25 (0.42 treads).
# Flight between the pink copings of the two lawn beds: south coping y 28.95-29.30 (NE corner (-0.58, 29.03)), north
# coping y 32.64-32.94 (corners (-2.28, 32.73) and (-0.64, 32.64)). Steel grating ramp laid over the north part of the
# flight: run 1 east from the path (x -2.27) to a landing x -0.55..0.55 (top rail 0.9 above: posts (-0.41..0.51, 31.7)
# z 6.93-6.97 cloud), then run 2 north over the bank line to the walkway (east rail end post (0.56, 36.2), rail
# 0.9 above the walkway; west rail end (-0.3, 36.1)); both runs ~1:4.3. Model levels: path top PATH_T, walkway zw.
SS_S, SS_N = 29.30, 32.64                         # flight side faces (coping faces)
SS_XT, SS_NR, SS_T = -2.27, 7, 0.42               # top nosing x, risers, tread
SS_XB = SS_XT + (SS_NR - 1) * SS_T                # bottom nosing 0.25
CPS0, CPN1 = 28.95, 32.94                         # outer faces of the south / north stair copings
ZT_SS = PATH_T(30.0)
RH_SS = (ZT_SS - zw(30.0)) / SS_NR
RP_Y0, RP_Y1 = 31.65, 32.62                       # ramp run 1 grating (north edge on the north coping face)
RP_X1, RP_XE = -0.55, 0.55                        # landing / run 2 grating x
RP_Y2 = 36.2                                      # run 2 foot (walkway level)
RP_ZL = ZT_SS - 0.39                              # landing (cloud: path 6.46, landing 6.07)
RP_ZF = zw(36.2) + 0.02
Y_RB1 = RP_Y2 + 1.0                               # walkway-level bay under/after run 2: bank cut y 32.94..37.2
EV_SS = ("070309303 two-lens SfM (a1): plane-sweep tread heights + triangulated rail posts/coping corners on f55-f68, "
         "012327726 t8-t31 views of the ramp")
els.append({"type": "stairs_run", "name": "SideStair", "top": W(SS_XT, (SS_S + SS_N) / 2), "dir_deg": r3(ANG),
            "risers": SS_NR, "riser_h": r3(RH_SS), "tread": SS_T, "width": r3(SS_N - SS_S), "z_top": r3(ZT_SS),
            "run_out": r3(X_WC - SS_XB), "material": "granite",
            "evidence": "pink granite side stair from the path down east to the walkway: 7 risers x 0.171 (sweep), treads "
                        "0.42, nosings x -2.27..0.25, between the two lawn-bed copings (y 29.30-32.64); " + EV_SS,
            "confidence": "medium"})
slab("SideStair_TopLanding", [(xc(SS_S) - 0.1, SS_S), (SS_XT, SS_S), (SS_XT, SS_N), (xc(SS_N) - 0.1, SS_N)], lambda x, y: PATH_T(y), 0.0,
     "stone", "grey concrete kerb strip between the path and the top nosing (070309303 f58, 012327726 t30.5)", "medium",
     {"thk": r3(ZT_SS - PAD_Z + 0.2)})
# copings of the two lawn beds along the flight: flat part follows the lawn to the bank top (x -0.6), then a sloped
# cheek down the bank end to the walkway beside the lowest treads (f57/f58: pink slab sweeping down to the stair foot)
cp_top = lambda x, y: lawn(x, y) + 0.05
for nm, y0, y1 in (("StairCoping_S", CPS0, SS_S), ("StairCoping_N", SS_N, CPN1)):
    slab(nm, [(xc(y0), y0), (X_BT, y0), (X_BT, y1), (xc(y1), y1)], cp_top, 0.0, "stone",
         "pink granite coping of the lawn bed beside the side stair, top 0.05 above the lawn (corners triangulated: "
         "(-0.58, 29.03) z 6.14 / (-2.28, 32.73) z 6.54 / (-0.64, 32.64) z 6.29 cloud); " + EV_SS, "medium",
         {"thk": r3(ZT_SS + 0.1 - PAD_Z + 0.2)})
    slab(nm + "Cheek", [(X_BT, y0), (X_WC, y0), (X_WC, y1), (X_BT, y1)],
         lambda x, y: cp_top(X_BT, y) + (zw(y) + 0.14 - cp_top(X_BT, y)) * (x - X_BT) / (X_WC - X_BT), 0.0, "stone",
         "sloped pink cheek down the bank end beside the lowest treads to the walkway (070309303 f57/f58)", "medium",
         {"thk": r3(cp_top(X_BT, 30) - PAD_Z + 0.2)})

for sfx, y0, y1 in (("S", S2_N, CPS0), ("N", CPN1, Y_LN)):
    yc0 = Y_RB1 if sfx == "N" else y0      # RampBay_Wall carries the coping along the ramp bay
    slab("Lawn_" + sfx, [(xc(y0), y0), (X_CP, y0), (X_CP, y1), (xc(y1), y1)], lawn, 0.0, "hedge",
         "lawn strip between the path and the lower walkway, falling ~0.3 from the path curb to the bank top (sweep/cloud "
         "6.48 -> 6.17); thujas, saplings on stakes, hydrangeas (070309303 f19-f45, f64-f73); " + EV_SFM, "medium",
         {"thk": r3(zA(y0) - PAD_Z + 0.2)})
    slab("LawnCoping_" + sfx, [(X_CP, yc0), (X_BT, yc0), (X_BT, y1), (X_CP, y1)], cp_top, 0.0, "stone",
         "pink granite coping along the bank top (070309303 f55/f56, f71; 012327726 t22-23)", "medium",
         {"thk": r3(zA(y0) - PAD_Z + 0.2)})
    strip("Curb_Path_" + sfx, (xc(y1), y1), (xc(y0), y0), 0.1, lambda x, y: PATH_T(y) + 0.07, PAD_Z - 0.2, "brick",
          "red concrete edging along the path side of the lawn strip (070309303 f19-f75; sweep path/lawn step at x -3.3)",
          "medium")
# grass bank + walkway curb, cut by the walkway-level bay under ramp run 2 (y 32.94 .. 37.2)
for sfx, y0, y1 in (("S", S2_N, CPS0), ("N", Y_RB1, Y_LN)):
    slab("Bank_" + sfx, [(X_BT, y0), (X_BB, y0), (X_BB, y1), (X_BT, y1)], bank, 0.0, "hedge",
         "steep grass bank from the bank-top coping down to the walkway curb (sweep: ~0.85 m over 0.75 m; 070309303 "
         "f24-f44)", "medium", {"thk": r3(zA(y0) - PAD_Z + 0.2)})
    strip("Curb_Walkway_" + sfx, (X_BB, y0), (X_BB, y1), 0.12, lambda x, y: zw(y) + 0.12, PAD_Z - 0.2, "brick",
          "low pink concrete curb at the foot of the bank along the walkway (070309303 f24-f44, f40 ground rays x 0.0-0.4)",
          "medium")
slab("RampBay_Wall", [(X_CP, CPN1), (X_BT, CPN1), (X_BT, Y_RB1), (X_CP, Y_RB1)], cp_top, 0.0, "stone",
     "lawn edge retained by a wall with the pink coping where ramp run 2 replaces the bank (070309303 f66/f67: grating "
     "directly below the coping edge); foot bay length to the bank restart assumed 1.0 m", "medium",
     {"thk": r3(cp_top(X_BT, 34) - PAD_Z + 0.2)})
slab("RampBay_Paving", [(X_BT, CPN1), (X_WC, CPN1), (X_WC, Y_RB1), (X_BT, Y_RB1)], lowtop, 1.3, "stone",
     "walkway-level paving under ramp run 2 and at its foot (bank cut); foot bay extent low confidence", "low")
# steel ramp (dark grating on a steel frame, 3-bar railings, legs down to the treads / walkway)
tread_z = lambda x: ZT_SS if x < SS_XT else (ZT_SS - RH_SS * min(SS_NR, 1 + int((x - SS_XT) / SS_T)) if x < SS_XB else zw(30))
r1z = lambda x: ZT_SS + (RP_ZL - ZT_SS) * (x - SS_XT) / (RP_X1 - SS_XT)
els.append({"type": "roof_plane", "name": "Ramp_Run1", "ring": ring([(SS_XT, RP_Y0), (RP_X1, RP_Y0), (RP_X1, RP_Y1), (SS_XT, RP_Y1)]),
            "z": [r3(ZT_SS + 0.005), r3(RP_ZL), r3(RP_ZL), r3(ZT_SS + 0.005)], "thk": 0.06, "material": "metal",
            "evidence": "grating run 1 over the north part of the flight, from the path kerb down east to the landing "
                        "(sweep: 6.45 at x -2.2, 6.36 at -1.77, 6.29 at -1.4, 6.22 at -0.93 cloud); " + EV_SS,
            "confidence": "medium"})
els.append({"type": "slab", "name": "Ramp_Landing", "ring": ring([(RP_X1, RP_Y0), (RP_XE, RP_Y0), (RP_XE, RP_Y1), (RP_X1, RP_Y1)]),
            "z0": r3(RP_ZL - 0.06), "z1": r3(RP_ZL), "material": "metal",
            "evidence": "flat grating landing over the lowest treads, top rail level 0.9 above it on 3 posts; " + EV_SS,
            "confidence": "medium"})
els.append({"type": "roof_plane", "name": "Ramp_Run2", "ring": ring([(RP_X1, RP_Y1), (RP_XE, RP_Y1), (RP_XE, RP_Y2), (RP_X1, RP_Y2)]),
            "z": [r3(RP_ZL), r3(RP_ZL), r3(RP_ZF), r3(RP_ZF)], "thk": 0.06, "material": "metal",
            "evidence": "grating run 2 north along the bank line down to the walkway (east rail end post (0.56, 36.2) "
                        "0.9 above the walkway, f66/f67 rays; 012327726 t21-23 long rails over the walkway); " + EV_SS,
            "confidence": "medium"})
RY_S, RY_N, RX_W, RX_E = RP_Y0 + 0.03, RP_Y1 - 0.03, RP_X1 + 0.03, RP_XE - 0.03


def ramp_z(x, y):   # grating top at an A-local point of the ramp
    if y <= RP_Y1:
        return r1z(x) if x < RP_X1 else RP_ZL
    return RP_ZL + (RP_ZF - RP_ZL) * (y - RP_Y1) / (RP_Y2 - RP_Y1)


# rail polylines, broken at the grade changes (run 1 -> landing at x RP_X1, landing -> run 2 at y RP_Y1)
for nm, pts in (("RampRail_S", [(SS_XT + 0.03, RY_S), (RP_X1, RY_S), (RX_E, RY_S), (RX_E, RP_Y1), (RX_E, RP_Y2 - 0.03)]),
                ("RampRail_N", [(SS_XT + 0.03, RY_N), (RX_W, RY_N), (RX_W, RP_Y2 - 0.03)])):
    els.append({"type": "rail3d", "name": nm, "points": [W(x, y) + [r3(ramp_z(x, y))] for x, y in pts],
                "height": 0.9, "spacing": 1.0, "mid_rails": 2, "post": 0.05, "rail": 0.05, "material": "metal",
                "unique_posts": True, "evidence": "dark grey square-tube railing, top rail + 2 bars (f55-f64); " + EV_SS,
                "confidence": "medium"})
# legs under the grating frame (posts continue down to the treads / walkway, f55-f60)
for k, (x, y) in enumerate([(-1.1, RY_S), (-1.1, RY_N), (RX_W, RY_S), (RX_E, RY_S), (RX_E, RY_N), (RX_W, 34.4), (RX_E, 34.4)]):
    ztop = ramp_z(x, y)
    zg = tread_z(x) if y < SS_N else zw(y)
    els.append({"type": "box", "name": f"Ramp_Leg_{k}", "center": W(x, y), "size": [0.05, 0.05, r3(ztop - 0.06 - zg + 0.05)],
                "dir_deg": r3(ANG), "z0": r3(zg - 0.05), "material": "metal",
                "evidence": "grating frame leg (070309303 f55-f60)", "confidence": "medium"})
slab("LawnEnd_Coping", [(xc(Y_LN), Y_LN), (X_BB, Y_LN), (X_BB, Y_STAIR_N), (xc(Y_STAIR_N), Y_STAIR_N)], lambda x, y: zA(y) + 0.05, 0.0,
     "stone", "pink granite coping closing the lawn strip at the wide stair (070309303 f73/f74)", "medium",
     {"thk": r3(zA(40) - PAD_Z + 0.2)})

# ---------------------------------------------------------------- terrain pad (lowered ground under the lower zone)
pad_l = [TNW, TSE, (BSE[0] + 0.05, BSE[1] - 0.05), (2.65, BSE[1] + 0.5), (2.65, -1.0), (38.6, -1.0), (38.6, 4.4), (2.5, 4.4), (2.5, Y1), (xc(Y1), Y1), (xc(S2_N), S2_N),
         (X_PAV, S2_N), (X_PAV, PAV_S), (X_SC, PAV_S)]

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
# B's east wall: model ring at A-local x -12.13; the SfM puts it at -11.35 (upper-storey wall points z 11-15, peak
# -11.4..-11.3) -> BLD_B owner. The bed elements below are placed at their measured A-local positions.
X_BW = -11.35          # B east wall (measured)
X_BC = -7.8            # B bed curb face (alley side): f48/f49/f52 ground rays -7.35..-8.2, SfM shrub fronts -7.8..-8.0
Y_BB0, Y_BB1 = 17.8, 38.2   # bed from the porch's north end to B's NE corner trees
ys, yn = -93.2, -52.0
def xw_B(y):
    return W(X_BC, (y - O[1] - XD[1] * X_BC) / YD[1])[0]
def xe_A(y):
    yl = (y - O[1] - XD[1] * X_CURB) / YD[1]
    return W(xc(yl), yl)[0]
mid = lambda y: [(xw_B(y) + xe_A(y)) / 2, y]
YS2 = W(X_PAV, PAV_S + 0.05)[1]
xs2 = W(-4.45, 3.0)[0]
# south of the pavilion the plaza follows the ground: a densified line (1 m) so the slab tracks the pads/terrain
_n = max(2, int(abs(YS2 - ys)) + 1)
els.append({"type": "path", "name": "Alley_Paving_S",
            "line": [[r3((xw_B(ys + (YS2 - ys) * i / (_n - 1)) + xs2) / 2), r3(ys + (YS2 - ys) * i / (_n - 1))] for i in range(_n)],
            "width": r3(xs2 - xw_B(-89)), "thk": 0.08, "surface": "herringbone_200x100",
            "evidence": "alley south of the pavilion, west of the south-bed curb (012205046, 012258813, 070309303 f00-f10)",
            "confidence": "medium"})
# alley paving from the pavilion to the wide stair: explicit planar slabs between B's bed curb (x -7.8) and the red
# curb of the lawn strip (face xc(y) - 0.1), top 0.02 above the Alley_* pads (a 2-point 'path' sloped between its
# end grounds and let the pads poke through)
PV_E = X_PAV
ptop = lambda x, y: PATH_T(y)
slab("Alley_Paving", [(X_BC, PAV_S + 0.05), (PV_E, PAV_S + 0.05), (PV_E, 10.0), (X_BC, 10.0)], ptop, 0.12, "stone",
     "alley at the pavilion (flat, sweep 0.12-0.2 above the lawn-strip path); " + EV_SFM, "medium",
     {"surface": "herringbone_200x100"})
slab("Alley_Paving_Fall", [(X_BC, 10.0), (PV_E, 10.0), (PV_E, S2_N), (xc(S2_N) - 0.1, S2_N), (xc(15.0) - 0.1, 15.0), (X_BC, 15.0)],
     ptop, 0.12, "stone", "alley falls 0.12 m between A-local y 10 and 15 (sweep)", "medium", {"surface": "herringbone_200x100"})
slab("Alley_Paving_N", [(X_BC, 15.0), (xc(15.0) - 0.1, 15.0), (xc(Y_STAIR_N) - 0.1, Y_STAIR_N), (X_BC, Y_STAIR_N)], ptop, 0.12,
     "stone", "alley from the pavilion to the wide stair between B's shrub bed curb (x -7.8) and the lawn-strip curb "
     "(x -3.35 at y 13 .. -2.25 at y 37), flat within +-0.05 (sweep); " + EV_SFM, "medium",
     {"surface": "herringbone_200x100 grey (2025 relay; clover pink 2022)"})
els.append({"type": "wall", "name": "BBed_Curb", "line": [W(X_BC - 0.06, Y_BB0), W(X_BC - 0.06, Y_BB1)], "height": 0.12, "thk": 0.12,
            "material": "stone", "evidence": "yellow/white painted concrete curb of the shrub bed along B's east face north "
                                             "of the porch (070309303 f47-f52 ground rays, SfM crescents of the shrubs)",
            "confidence": "medium"})
for k, y in enumerate((21.3, 24.0, 26.8, 29.5)):
    els.append({"type": "tree", "name": f"BBed_Shrub_{k:02d}", "pos": W(-8.65, y), "height": 1.6, "crown_d": 1.6,
                "shape": "round", "trunk_d": 0.1, "crown_base": 0.05,
                "evidence": "round clipped shrubs ~1.6 m in B's bed, fronts at x -7.8..-8.0 (SfM crescents y 23-30.5; "
                            "070309303 f45-f53 frontal views, ~2.7 m pitch)", "confidence": "medium" if 23 < y < 31 else "low"})
for k, y in enumerate((22.5, 28.3)):
    els.append({"type": "lamp_orn", "name": f"BBed_Lamp_{k:02d}", "pos": W(-8.5, y), "height": 3.2, "arm_span": 0.7,
                "globes": 2, "globe_d": 0.28, "dir_deg": r3(ANG),
                "evidence": "black cast lamp post with two lanterns between the shrubs (070309303 f48, f49, f51, f52 base "
                            "rays: (-8.7, 22.5), (-8.35, 28.3))", "confidence": "medium"})
for k, (x, y, h, cd) in enumerate([(-8.8, 33.9, 9.0, 3.6), (-8.3, 37.4, 8.0, 3.2)]):
    els.append({"type": "tree", "name": f"BBed_Conifer_{k:02d}", "pos": W(x, y), "height": h, "crown_d": cd, "shape": "cone",
                "trunk_d": 0.3, "crown_base": 1.0,
                "evidence": "tall conifers at B's NE end of the bed (070309303 f44-f53, trunk rays in f51)", "confidence": "low"})

# ---------------------------------------------------------------- lawn strip planting (A side)
# conical thujas from the SfM crowns (plan blobs z 0.3-1.5 above the lawn) and frames f30-f45
for k, (x, y, h) in enumerate([(-2.7, 13.7, 1.5), (-2.05, 18.25, 1.6), (-2.4, 20.3, 1.2), (-2.2, 22.8, 1.2)]):
    els.append({"type": "tree", "name": f"LawnThuja_{k:02d}", "pos": W(x, y), "z": r3(lawn(x, y)), "height": h, "crown_d": 0.8,
                "shape": "cone", "trunk_d": 0.06, "crown_base": 0.15,
                "evidence": "conical thujas on the lawn strip: SfM crown blobs at A-local (%.1f, %.1f) (070309303 f28-f45)"
                            % (x, y), "confidence": "medium"})

# ---------------------------------------------------------------- wide stair north of the alley (-> lower terrace)
# 012404116 t0-3.5 s (2 fps, frames ~/koch_work/ws): 6 pink granite steps + a grey concrete kerb as the top riser =
# 7 risers down to the lower terrace. The upper 4 risers run between two raised beds: east = the end of the lawn strip
# (rubble-stone wall with a pink granite coping, stepped down along the flight), west = the rose bed at B's corner
# (rubble-stone retaining wall). The lower 3 steps run past both bed walls (t0.5 / t2.0 frames).
PATH_N_Z = 5.35                  # lower terrace (path, garden, gazebos, C plaza)
N_STEPS, N_UP = 7, 4
RH = (ALLEY_N - PATH_N_Z) / N_STEPS
TR = 0.35
X_UP_W, X_UP_E = -7.63, -2.3     # upper flight between the bed walls (B bed curb line / lawn-strip end, f74 band)
X_LO_W, X_LO_E = -8.4, -1.5      # lower steps run ~0.8 m past both walls
EV_WS = ("012404116 t0-3.5 s (6 granite steps + grey kerb = 7 risers, bed walls on both sides, lower steps running past "
         "them), 070309303 f71-f75 (top nosing band y 40.35-40.53)")
els.append({"type": "stairs_run", "name": "Steps_BCorner_Upper", "top": W((X_UP_W + X_UP_E) / 2, Y_STAIR_N),
            "dir_deg": r3(ANG + 90), "risers": N_UP, "riser_h": r3(RH), "tread": TR, "width": r3(X_UP_E - X_UP_W),
            "z_top": r3(ALLEY_N), "material": "granite", "evidence": EV_WS, "confidence": "medium"})
Y_LO = Y_STAIR_N + N_UP * TR     # nosing of the first lower step
els.append({"type": "stairs_run", "name": "Steps_BCorner_Lower", "top": W((X_LO_W + X_LO_E) / 2, Y_LO),
            "dir_deg": r3(ANG + 90), "risers": N_STEPS - N_UP, "riser_h": r3(RH), "tread": TR,
            "width": r3(X_LO_E - X_LO_W), "z_top": r3(ALLEY_N - N_UP * RH), "material": "granite",
            "evidence": EV_WS, "confidence": "medium"})
# bed walls beside the upper flight (rubble stone + pink coping), top = upper level + 0.3 (bed soil + coping)
for nm, x0, x1 in (("WS_BedWall_E", X_UP_E, X_UP_E + 0.35), ("WS_BedWall_W", X_UP_W - 0.35, X_UP_W)):
    slab(nm, [(x0, Y_STAIR_N - 0.3), (x1, Y_STAIR_N - 0.3), (x1, Y_LO), (x0, Y_LO)], lambda x, y: ALLEY_N + 0.3, 0.0,
         "stone", "rubble-stone bed wall with pink granite coping beside the upper flight (" + EV_WS + ")", "medium",
         {"thk": r3(ALLEY_N + 0.3 - PAD_Z + 0.2)})
# the raised beds behind the walls continue alongside the upper flight at the upper level (012404116 t0.5 / t2.0)
for nm, x0, x1 in (("WS_Bed_E", X_UP_E + 0.35, X_BB), ("WS_Bed_W", X_UP_W - 1.8, X_UP_W - 0.35)):
    slab(nm, [(x0, Y_STAIR_N - 0.3), (x1, Y_STAIR_N - 0.3), (x1, Y_LO), (x0, Y_LO)], lambda x, y: ALLEY_N + 0.15, 0.0,
         "hedge", "raised bed (lawn / roses) beside the upper flight, soil just below the coping (" + EV_WS + ")", "medium",
         {"thk": r3(ALLEY_N + 0.15 - PAD_Z + 0.2)})
    xf = x0 if nm.endswith("E") else x1
    slab(nm + "_Front", [(x0, Y_LO), (x1, Y_LO), (x1, Y_LO + 0.3), (x0, Y_LO + 0.3)], lambda x, y: ALLEY_N + 0.3, 0.0,
         "stone", "rubble-stone front wall of the raised bed facing the lower plaza (" + EV_WS + ")", "medium",
         {"thk": r3(ALLEY_N + 0.3 - PAD_Z + 0.2)})

spec = {
    "id": "SITE_GateAlley",
    "collection": "03_Site",
    "ground": "pads",
    "note": ("Alley from the gate north between Block B (west) and Block A_S/A_W (east). A stands ~1.3 m lower: a lower "
             "walkway along its west face, reached by the wide south stair from the gate plaza, the stair under the "
             "entrance pavilion and the side stair + steel ramp opposite the A_W lettering (SITE_Garden AW_*). North of "
             "the pavilion a sloping lawn strip with a steep grass bank separates the path from the walkway; south of it "
             "a raised bed with a low retaining wall. Geometry designed in the A local frame (Scripts/Geo/zones/"
             "zone_gate_alley.py), world XY here. Lower-level solids use absolute z; terrain_pads lower TER_Ground under "
             f"them to {PAD_Z}. 2026-09-26: re-measured from the 070309303 SfM photo-match (see the generator header)."),
    "terrain_pads": [{"ring": ring(pad_l), "z": PAD_Z, "blend": 0.0,
                      "evidence": "lower walkway zone at A_S's west/south side (see note)"},
                     {"name": "Alley_Flat_S", "ring": [[r3(xw_B(-89.0) - 3.0), -89.0], [r3(xe_A(-89.0) - 0.8), -89.0],
                                                       W(X_PAV, 10.0), [r3(xw_B(-82.3) - 3.0), -82.3]],
                      "z": r3(ALLEY_S - 0.08), "blend": 1.5,
                      "evidence": "alley at the pavilion and the gate plaza (sweep 0.12-0.2 above the lawn-strip path)"},
                     {"name": "Alley_Fall", "ring": [[r3(xw_B(-82.3) - 3.0), -82.3], W(X_PAV, 10.0), W(xc(15.0), 15.0),
                                                     [r3(xw_B(-77.3) - 3.0), -77.3]],
                      "z": r3(ALLEY_S - 0.08), "grad": [r3(-(ALLEY_S - ALLEY_N) / 5.0 * 0.049), r3(-(ALLEY_S - ALLEY_N) / 5.0 * 0.9988)],
                      "ref": [r3(xw_B(-82.3)), -82.3], "blend": 0.5,
                      "evidence": "alley falls 0.12 m between A-local y 10 and 15 (sweep)"},
                     {"name": "Alley_Flat_N", "ring": [[r3(xw_B(-77.3) - 3.0), -77.3], W(xc(15.0), 15.0),
                                                       W(xc(Y_STAIR_N), Y_STAIR_N), [r3(xw_B(-52.3) - 3.5), -52.3]],
                      "z": r3(ALLEY_N - 0.08), "blend": 1.0,
                      "evidence": "sweep: path flat within +-0.05 from y 12 to the wide stair, 1.26 above the walkway"}],
    "elements": els,
}
out = sys.argv[1] if len(sys.argv) > 1 else '/home/faust/KOCH-SIMULATOR/Art/Blender/Specs/SITE_GateAlley.json'
json.dump(spec, open(out, 'w'), indent=1, ensure_ascii=False)
print("wrote", out, len(els), "elements; PAD_Z", PAD_Z, "alley", ALLEY_S, ALLEY_N, "S1 top", r3(zt1), "bottom", r3(zb1),
      "rh", r3((zt1 - zb1) / 8), "TNW", TNW, "BNW", tuple(round(v, 2) for v in BNW))
