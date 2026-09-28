# Zone "sports" (R1): writes Art/Blender/Specs/SITE_Sports.json (pitch cage, courts, bench strip, decorated alley, round
# bed, north strip) and SITE_HallCPassage.json (terrace -> stair -> lower path between the hall and Block C). Measurements
# live in the local sports frame (origin world (114,45), u along -2.2 deg = campus grid, v 'local north').
# Run: python3 Scripts/Geo/zones/zone_sports.py
import json, math
import numpy as np

O = np.array([114.0, 45.0]); A = np.radians(-2.2)
DU = np.array([np.cos(A), np.sin(A)]); DV = np.array([-np.sin(A), np.cos(A)])
def w(u, v): return O + DU * u + DV * v

ROT = -2.2                      # frame rotation (deg): u axis in world
DEG_N = 90 + ROT                # "local north" (v axis) as a world heading
R3 = lambda p: [round(float(p[0]), 3), round(float(p[1]), 3)]
W = lambda u, v: R3(w(u, v))
def rect(u0, u1, v0, v1): return [W(u0, v0), W(u1, v0), W(u1, v1), W(u0, v1)]
def poly(pts): return [W(u, v) for u, v in pts]

# ---------------------------------------------------------------- levels (absolute z, Z = ASL - 800)
Z_PLAZA = 3.45   # walkway / courts platform / plaza strip along the pitch (terrain pad)
Z_PITCH = 3.80   # turf top: plinth 0.35 above the walkway at the SE gate (070410255 t=60 s, 2 steps)
Z_NORTH = 3.75   # north path + lawn terrace: flush with the pitch edge (drone 2022 d_07/d_19), steps at the walkway end
Z_COURT = 3.50   # courts: flush with the walkway + a 5 cm curb (070410255 t=52/60 s)
Z_LOW = Z_PLAZA - 0.60   # lower yard behind the courts (owner 2026-09-28: lower, reached by steps; 0.6 m assumed)

# ---------------------------------------------------------------- measured outlines (local u, v)
P_U0, P_U1, P_V0, P_V1 = -0.10, 44.35, 0.15, 25.40     # pitch plinth = fence line
P_IN = 0.30                                            # red rubber border inside the fence (drone d_07/d_19)
# courts block = fence line. 2026-09-28 owner: the courts fence is flush with the pitch fence on both long sides (S and N);
# the ortho read S v 1.7 / N v 28.0 (Google 28.6 incl. the lean band): the band beyond v 25.4 is the workout area
# behind the basketball court (WORKOUT below), not courts surface
C_U0, C_U1, C_V0, C_V1 = 50.90, 97.00, P_V0, P_V1
DIV1, DIV2 = 68.90, 84.35                              # division fences bb|vb, vb|third court
BB = (52.90, 67.40, 0.90, 24.66)                       # basketball green field: measured 23.76 m long, re-centred in the flush block
VB = (72.40, 81.10, 3.95, 21.60)                       # volleyball green inner court (8.7 x 17.65 measured), re-centred

EV_ORTHO = ("Google z20 (2026, 0.1 m/px) georeferenced in the world frame; edges by luminance-step profiles in the "
            "rotated sports frame (origin 114,45, -2.2 deg), cross-checked on Bing 2021 (+1.2/+0.5 m registration)")
els = []
def add(**e): els.append(e); return e

# ================================================================= PITCH (mini-football cage)
pc_v = (P_V0 + P_IN + P_V1 - P_IN) / 2
TURF = rect(P_U0 + P_IN, P_U1 - P_IN, P_V0 + P_IN, P_V1 - P_IN)
# plinth = red border frame around the turf (hole): a full plinth top 1 cm under the turf top would z-fight through it
add(type="slab", name="Pitch_Plinth", ring=rect(P_U0, P_U1, P_V0, P_V1), holes=[TURF], z0=3.1, z1=Z_PITCH - 0.01, material="brick",
    evidence=EV_ORTHO + ": turf/fence line W u -0.1 (Google -0.11..-0.05, Bing -0.02..-0.19), E u 44.35 (Bing 44.27..44.42; "
             "Google 44.0-44.6 blurred by the E fence shadow), S v 0.15 (Google 0.12..0.26), N v 25.4 (Google 25.42, Bing 25.35..25.45)"
             " -> 44.45 x 25.25 m. Red brick-tile plinth ~0.35 m above the walkway at the SE gate (070410255 t=60 s) and along "
             "the W end (drone 2022 f 0:14)", confidence="medium")
add(type="slab", name="Pitch_Turf", ring=TURF, z0=3.1, z1=Z_PITCH, material="hedge",
    evidence="green artificial turf inside a ~0.3 m red border strip (drone 2022 d_07/d_19); level surface", confidence="medium")
tu0, tu1, tv0, tv1 = P_U0 + P_IN + 0.05, P_U1 - P_IN - 0.05, P_V0 + P_IN + 0.05, P_V1 - P_IN - 0.05
um = (tu0 + tu1) / 2
lines = [poly([(tu0, tv0), (tu1, tv0), (tu1, tv1), (tu0, tv1), (tu0, tv0)]), poly([(um, tv0), (um, tv1)])]
arcs = [dict(c=W(um, pc_v), r=3.0, a0=0, a1=360), dict(c=W(um, pc_v), r=0.12, a0=0, a1=360)]
for side, u_g, s in (("W", tu0, 1), ("E", tu1, -1)):   # futsal penalty areas: quarter circles r 6 m from the posts + 3 m line
    a_base = ROT if s > 0 else ROT + 180
    arcs.append(dict(c=W(u_g, pc_v + 1.5), r=6.0, a0=a_base, a1=a_base + 90 * s))
    arcs.append(dict(c=W(u_g, pc_v - 1.5), r=6.0, a0=a_base, a1=a_base - 90 * s))
    lines.append(poly([(u_g + 6.0 * s, pc_v - 1.5), (u_g + 6.0 * s, pc_v + 1.5)]))
    arcs.append(dict(c=W(u_g + 6.0 * s, pc_v), r=0.1, a0=0, a1=360))
add(type="paint", name="Pitch_Lines", lines=lines, arcs=arcs, width=0.08, z=Z_PITCH,
    evidence="drone 2022 d_07/d_19 + Google 2026: white outline, halfway line, centre circle, futsal-style D areas "
             "(r ~6 m arcs from the goal posts); radii from the Google image (centre circle ~3 m)", confidence="medium")
for side, u_g, s in (("W", tu0, 1), ("E", tu1, -1)):
    for k, vv in enumerate((pc_v - 1.5, pc_v + 1.5)):
        add(type="box", name=f"Goal_{side}_Post{k}", center=W(u_g - 0.04 * s, vv), size=[0.08, 0.08, 2.0], dir_deg=ROT,
            z0=Z_PITCH, material="white", evidence="white 3 x 2 m futsal goals centred on both ends (Google 2026: white "
            "frames at u 0.2 and 43.9, v 10.9..14.4; drone 2022)", confidence="medium")
    add(type="box", name=f"Goal_{side}_Bar", center=W(u_g - 0.04 * s, pc_v), size=[0.08, 3.08, 0.08], dir_deg=ROT,
        z0=Z_PITCH + 2.0, material="white", evidence="goal crossbar 2.0 m", confidence="medium")
    add(type="box", name=f"Goal_{side}_Back", center=W(u_g - 1.0 * s, pc_v), size=[0.05, 3.0, 0.05], dir_deg=ROT,
        z0=Z_PITCH, material="white", evidence="goal ground frame ~1 m deep (drone 2022 d_19)", confidence="low")

# fence: 8.2 m cage on the plinth; S gate near the SE corner (photo-matched camera on 070410255 t=52 s, see ovl/)
H_P = 8.2
ev_pf = ("PnP camera on 070410255 t=52 s (5 ground points, rms 2 px; checks: wheelie bin 1.09 m, courts gate 2.0 m, person "
         "1.86 m): S fence top rail level at z 11.85-11.92 = 8.2-8.3 m above the plinth top, mid rail z 7.47 = 3.8 m; posts "
         "~3 m (15 bays x 2.96 m on the S side, drone 2022 d_19); rope-net roof (drone d_19, 2GIS night photo 2025)")
fence_common = dict(height=H_P, post_spacing=3.0, post=0.1, rail=0.06, rails=[0.1, 3.8, H_P - 0.03], z_base=Z_PITCH - 0.01)
g_u0, g_u1 = 43.05, 44.15
add(type="cage_fence", name="PitchFence_Main", line=poly([(g_u0, P_V0), (P_U0, P_V0), (P_U0, P_V1), (P_U1, P_V1), (P_U1, P_V0)]),
    evidence=ev_pf, confidence="medium", **fence_common)
add(type="cage_fence", name="PitchFence_S_Corner", line=poly([(P_U1, P_V0), (g_u1, P_V0)]), evidence=ev_pf,
    confidence="medium", **dict(fence_common, post_spacing=9.0))
add(type="cage_fence", name="PitchGate_S", line=poly([(g_u0 + 0.04, P_V0), (g_u1 - 0.04, P_V0)]), height=1.95,
    post_spacing=9.0, post=0.05, rail=0.04, rails=[0.05, 1.0, 1.93], z_base=Z_PITCH - 0.01,
    evidence="white barred door in the S fence next to the SE corner: back-projected u 43.57..44.09 (door ajar), steps "
             "u 42.86..44.3; door ~1.9 m (070410255 t=39/52 s)", confidence="medium")
add(type="steps", name="PitchGate_S_Steps", pos=W((g_u0 + g_u1) / 2, P_V0 - 0.33), dir_deg=DEG_N, width=1.45,
    risers=2, riser_h=0.17, tread=0.3, top_landing=0.02,
    evidence="two dark steps in front of the S gate (070410255 t=52/60 s): 2 x 0.17 = the 0.35 plinth", confidence="medium")
add(type="net_roof", name="Pitch_NetRoof", ring=rect(P_U0, P_U1, P_V0, P_V1), z=Z_PITCH - 0.01 + H_P + 0.03, spacing=2.0,  # ropes ON the top rail
    rope=0.03, evidence="rope net over the whole cage, ~2 m grid (drone 2022 d_19; night photo 2GIS 2025-01)",
    confidence="medium")
for nm, (u, v, d) in dict(SE=(40.7, P_V0, 90 + ROT), SW=(P_U0 + P_U1 - 40.7, P_V0, 90 + ROT),
                          NE=(40.7, P_V1, -90 + ROT), NW=(P_U0 + P_U1 - 40.7, P_V1, -90 + ROT)).items():
    add(type="floodlight", name=f"PitchFlood_{nm}", pos=W(u, v), z_base=Z_PITCH - 0.01, height=8.6, heads=2, dir_deg=d,
        evidence=("mast on the S fence at u 40.7 (back-projected, 070410255 t=52 s), 2 lamp heads at z 12.2-12.7 = 8.6-9.0 m "
                  "above the plinth, ladder rungs on it") if nm == "SE" else
                 "assumed mirror/opposite of the measured SE mast (drone 2022 d_07/d_19 show masts on both long sides)",
        confidence="medium" if nm == "SE" else "low")

# ================================================================= COURTS (basketball | volleyball | hard court)
HARD = (DIV2 + 0.05, C_U1 - 0.05, C_V0 + 0.05, C_V1 - 0.05)
# fields sit flush in holes of the courts slab (stacked coplanar-ish tops z-fight); paint lines 5 mm proud of them
add(type="slab", name="Courts_Slab", ring=rect(C_U0, C_U1, C_V0, C_V1), holes=[rect(*BB), rect(*VB), rect(*HARD)], z0=3.1,
    z1=Z_COURT, material="brick",
    evidence=EV_ORTHO + ": courts W u 50.9 (Google 50.87..50.89), E u 97.0 (Google 96.9..97.0, Bing 96.8..96.9), S v 1.7 "
             "(Google 1.4..1.7, Bing 1.75..1.86), N v 28.0 (visual; Google 28.6 incl. the N fence lean band, Bing 27.4..27.9) "
             "-> 46.1 x 26.3 m; 2026-09-28 owner: S and N fences flush with the pitch -> v 0.15..25.40 (46.1 x 25.25 m); red acrylic "
             "surface, flush with the walkway + 5 cm curb", confidence="medium")
add(type="slab", name="Court_Basket_Field", ring=rect(*BB), z0=3.1, z1=Z_COURT, material="hedge",
    evidence="green basketball field u 52.9..67.4, 23.76 m long (Google profiles v 3.04..26.8, rms 0.03-0.06 m; N edge 26.4..27.3 "
             "blurred); re-centred in the courts block made flush with the pitch (owner 2026-09-28)",
    confidence="medium")
add(type="slab", name="Court_Volley_Field", ring=rect(*VB), z0=3.1, z1=Z_COURT, material="hedge",
    evidence="green volleyball court u 72.4..81.1, v 5.75..23.4 = 8.7 x 17.65 (9 x 18 lines) (Google profiles, rms <= 0.06)",
    confidence="medium")
add(type="slab", name="Court_Hard_Field", ring=rect(*HARD), z0=3.1, z1=Z_COURT, material="brick", evidence="third court: red surface with white tennis lines, net (Google 2026, drone 2022 "
    "d_23; in 2022 its margin was green)", confidence="medium")
# basketball markings (FIBA-like, fitted to a 14.5 x 23.76 field)
b_u0, b_u1, b_v0, b_v1 = BB
bu, bv = (b_u0 + b_u1) / 2, (b_v0 + b_v1) / 2
bl = [poly([(b_u0, b_v0), (b_u1, b_v0), (b_u1, b_v1), (b_u0, b_v1), (b_u0, b_v0)]), poly([(b_u0, bv), (b_u1, bv)])]
ba = [dict(c=W(bu, bv), r=1.8, a0=0, a1=360)]
for vb0, s in ((b_v0, 1), (b_v1, -1)):
    hoop = vb0 + 1.575 * s
    bl.append(poly([(bu - 2.45, vb0), (bu - 2.45, vb0 + 5.8 * s), (bu + 2.45, vb0 + 5.8 * s), (bu + 2.45, vb0)]))
    ba.append(dict(c=W(bu, vb0 + 5.8 * s), r=1.8, a0=ROT if s > 0 else ROT + 180, a1=ROT + 180 if s > 0 else ROT + 360))
    half = math.degrees(math.acos(6.6 / 6.75))   # 3-pt arc between the straight corner lines at 6.6 m
    a_c = ROT + 90 * s
    ba.append(dict(c=W(bu, hoop), r=6.75, a0=a_c - (90 - half), a1=a_c + (90 - half)))
    yc = hoop + s * 6.75 * math.sin(math.radians(half))
    bl.append(poly([(bu - 6.6, vb0), (bu - 6.6, yc)])); bl.append(poly([(bu + 6.6, vb0), (bu + 6.6, yc)]))
add(type="paint", name="Court_Basket_Lines", lines=bl, arcs=ba, width=0.05, z=Z_COURT,
    evidence="Google 2026: centre circle ~r 1.8 at v 14.9, 3-pt arcs and keys at both N/S ends; FIBA dimensions fitted to the "
             "measured field", confidence="medium")
for s, vb0 in ((1, b_v0), (-1, b_v1)):   # poles 0.55 m behind the end line (inside the flush fence)
    nm = "S" if s > 0 else "N"
    add(type="box", name=f"Hoop_{nm}_Pole", center=W(bu, vb0 - 0.55 * s), size=[0.16, 0.16, 3.35], dir_deg=ROT, z0=Z_COURT,
        material="metal", evidence="hoop stands behind both baselines (Google 2026 backboard images at v 4.4 / 25.8 incl. lean; "
        "drone 2022)", confidence="medium")
    add(type="box", name=f"Hoop_{nm}_Arm", center=W(bu, vb0 + 0.325 * s), size=[1.75, 0.1, 0.1], dir_deg=ROT + 90,
        z0=Z_COURT + 3.2, material="metal", evidence="arm to the board", confidence="low")
    add(type="box", name=f"Hoop_{nm}_Board", center=W(bu, vb0 + 1.2 * s), size=[1.8, 0.05, 1.05], dir_deg=ROT,
        z0=Z_COURT + 2.9, material="white", evidence="1.8 x 1.05 board, rim 3.05 m (standard)", confidence="low")
    add(type="box", name=f"Hoop_{nm}_Rim", center=W(bu, vb0 + 1.575 * s), size=[0.45, 0.45, 0.02], dir_deg=ROT,
        z0=Z_COURT + 3.04, material="metal", evidence="rim 0.45 m at 3.05 m", confidence="low")
# volleyball
v_u0, v_u1, v_v0, v_v1 = VB
vv_c = (v_v0 + v_v1) / 2
add(type="paint", name="Court_Volley_Lines", width=0.05, z=Z_COURT,
    lines=[poly([(v_u0, v_v0), (v_u1, v_v0), (v_u1, v_v1), (v_u0, v_v1), (v_u0, v_v0)]), poly([(v_u0, vv_c), (v_u1, vv_c)]),
           poly([(v_u0, vv_c - 3), (v_u1, vv_c - 3)]), poly([(v_u0, vv_c + 3), (v_u1, vv_c + 3)])],
    evidence="white lines on the green inner court; net line across the long axis (drone d_23)", confidence="medium")
for k, u in enumerate((v_u0 - 0.6, v_u1 + 0.6)):
    add(type="box", name=f"VolleyNetPost_{k}", center=W(u, vv_c), size=[0.1, 0.1, 2.55], dir_deg=ROT, z0=Z_COURT,
        material="white", evidence="white net posts outside the sidelines (drone 2022 d_23)", confidence="medium")
add(type="box", name="VolleyNet", center=W((v_u0 + v_u1) / 2, vv_c), size=[v_u1 - v_u0 + 1.1, 0.02, 1.0], dir_deg=ROT,
    z0=Z_COURT + 1.43, material="white", evidence="net top 2.43 m (standard); drone d_23", confidence="low")
# tennis-lined hard court (doubles 10.97 x 23.77 centred)
t_uc, t_vc = (DIV2 + C_U1) / 2, (C_V0 + C_V1) / 2
T = lambda du, dv: (t_uc + du, t_vc + dv)
tl = [poly([T(-5.485, -11.885), T(5.485, -11.885), T(5.485, 11.885), T(-5.485, 11.885), T(-5.485, -11.885)]),
      poly([T(-4.115, -11.885), T(-4.115, 11.885)]), poly([T(4.115, -11.885), T(4.115, 11.885)]),
      poly([T(-4.115, -6.4), T(4.115, -6.4)]), poly([T(-4.115, 6.4), T(4.115, 6.4)]), poly([T(0, -6.4), T(0, 6.4)])]
add(type="paint", name="Court_Hard_Lines", lines=tl, width=0.05, z=Z_COURT,
    evidence="Google 2026: centre service line u ~90.1 (standard 90.68), service lines v ~7.8/21.8 (std 8.45/21.25): standard "
             "doubles court assumed centred", confidence="low")
for k, du in enumerate((-6.0, 6.0)):
    add(type="box", name=f"HardNetPost_{k}", center=W(*T(du, 0)), size=[0.08, 0.08, 1.07], dir_deg=ROT, z0=Z_COURT,
        material="metal", evidence="net across the court (drone 2022 d_23)", confidence="low")
add(type="box", name="HardNet", center=W(*T(0, 0)), size=[12.0, 0.02, 0.9], dir_deg=ROT, z0=Z_COURT + 0.05, material="white",
    evidence="tennis net 0.91 m", confidence="low")
# courts fences 4.9 m, rails at mid + top, W gate at the SW corner
H_C = 4.9
ev_cf = ("height 4.9 m: 070410255 t=52 s, post 250 px vs a 1.75 m person at the fence (90 px); same height on the division "
         "fences (drone 2022 d_23); mid rail at the 2.1 m gate top; posts ~3 m (Google post dots)")
cf = dict(height=H_C, post_spacing=3.0, post=0.08, rail=0.05, rails=[0.08, 2.1, H_C - 0.025], z_base=Z_COURT)
# 2026-09-28 owner: no door in the W fence; each court has its own door in the S fence near its W end (basketball next to
# the SW corner, the others "about the same"); the 4.9 m mesh continues above the 2.1 m doors
GATES = [("Basket", 52.30, 53.40), ("Volley", 69.60, 70.70), ("Hard", 85.00, 86.10)]
ev_g = "owner 2026-09-28 (screenshot notes): entrance to each court from the south side, W-fence door removed; door u by eye"
add(type="cage_fence", name="CourtsFence_Perimeter", line=poly([(GATES[0][1], C_V0), (C_U0, C_V0), (C_U0, C_V1), (C_U1, C_V1),
                                                                  (C_U1, C_V0), (GATES[2][2], C_V0)]),
    evidence=ev_cf + "; " + ev_g, confidence="medium", **cf)
for k, (a, b) in enumerate(((GATES[2][1], GATES[1][2]), (GATES[1][1], GATES[0][2]))):
    add(type="cage_fence", name=f"CourtsFence_S{k}", line=poly([(a, C_V0), (b, C_V0)]), evidence=ev_cf, confidence="medium", **cf)
for nm, g0, g1 in GATES:
    add(type="gate_leaf", name=f"CourtsGate_{nm}", line=poly([(g0 + 0.08, C_V0), (g1 - 0.08, C_V0)]), height=2.1, panel="bars",
        z_base=Z_COURT, evidence="white barred door as filmed on the old W door (070410255 t=52/60 s); " + ev_g, confidence="low")
    add(type="cage_fence", name=f"CourtsGate_{nm}_Head", line=poly([(g0 + 0.09, C_V0), (g1 - 0.09, C_V0)]),   # posts clear of the fence end posts evidence=ev_g, confidence="low",
        **dict(cf, height=H_C - 2.15, z_base=Z_COURT + 2.15, rails=[0.03, H_C - 2.15 - 0.025]))
for nm, u in (("Div1", DIV1), ("Div2", DIV2)):
    add(type="cage_fence", name=f"CourtsFence_{nm}", line=poly([(u, C_V0), (u, C_V1)]),
        evidence=ev_cf + f"; division fence at u {u} (Google profile rms 0.14-0.34)", confidence="medium", **cf)

# ---------------------------------------------------------------- LOWER YARD north of the courts (owner 2026-09-28)
# the ground behind the courts falls toward the back (boundary) fence: a yard 0.6 m below the courts/walkway, held by a
# retaining wall under the courts' N fence and one along the E edge of the north terrace (pitch side, 0.9 m); reached by a
# gentle stair (4 risers x 0.15, treads 0.45) at the N end of the walkway between the pitch and the courts
ev_ly = ("owner 2026-09-28 (screenshots + sketch): the workout zone is lower than the courts, the drop is not abrupt, steps "
         "down from the walkway; toward the back fence the ground is lower, the tree bed behind the pitch is higher than the "
         "path; drop 0.6 m = 4 risers assumed (not measured)")
ST_U0, ST_U1 = 44.45, 50.90                   # stair over the full walkway width, pitch NE corner -> courts NW corner (owner)
ST_N, ST_RH, ST_TR = 4, 0.15, 0.45
LANE_V0 = 33.30                                # S edge of the low lane behind the pitch (N curb of the tree bed)
NB_RAISE = 0.40   # owner 2026-09-28: the tree bed behind the pitch stands higher than the path (raised bed, 0.4 assumed)
add(type="stairs_run", name="LowerYard_Stair", top=W((ST_U0 + ST_U1) / 2, C_V1), dir_deg=DEG_N, width=ST_U1 - ST_U0 - 0.02,
    risers=ST_N, riser_h=ST_RH, tread=ST_TR, z_top=Z_PLAZA, material="stone", slot="M_Concrete_Precast", evidence=ev_ly,
    confidence="low")
ST_V1 = C_V1 + ST_N * ST_TR


def wall_box(nm, u0, u1, v0, v1, z0, z1, slot="M_Concrete_Precast"):
    add(type="box", name=nm, center=W((u0 + u1) / 2, (v0 + v1) / 2), dir_deg=ROT, size=[u1 - u0, v1 - v0, z1 - z0], z0=z0,
        material="stone", slot=slot, evidence=ev_ly, confidence="low")


RW_TOP = 0.8   # owner 2026-09-28: concrete strip between the courts fence and the lower yard a bit wider (was 0.3)
wall_box("LowerYard_Retain_Courts", ST_U1, 101.0, C_V1, C_V1 + RW_TOP, Z_LOW - 0.3, Z_COURT)             # under the N fence, to the E fence
wall_box("LowerYard_Retain_Terrace", ST_U0 - 0.4, ST_U0 - 0.1, C_V1, LANE_V0 + 0.3, Z_LOW - 0.3, Z_NORTH + 0.05)  # pitch side
# the lane behind the pitch is low too (owner 2026-09-28): retaining wall along the N side of the raised bed / west terrace
wall_box("LowerYard_Retain_Bed", 0.0, ST_U0 - 0.4, LANE_V0, LANE_V0 + 0.3, Z_LOW - 0.3, Z_NORTH + NB_RAISE + 0.1)
wall_box("LowerYard_Retain_West", -20.0, 0.0, LANE_V0, LANE_V0 + 0.3, Z_LOW - 0.3, Z_NORTH + 0.05)
wall_box("LowerYard_Stair_CheekE", ST_U1, ST_U1 + 0.3, C_V1 + RW_TOP, ST_V1, Z_LOW - 0.3, Z_PLAZA)       # stair E cheek

# ---------------------------------------------------------------- WORKOUT area behind the basketball court (owner 2026-09-28)
# between the basketball court's N fence (v 25.40) and the lane; owner 2026-09-28: only parallel bars and 4 pull-up bars, the
# pull-ups in two rows of two (sketch); steel tube placeholders (UE swaps kits via koch_ue_asset)
EV_WO = ("owner 2026-09-28: a workout area with pull-up bars behind the basketball court, between it and the lane (the ortho "
         "band v 25.4..28.6 that was read as courts); set per the owner (parallel bars + 4 pull-up bars, 2 rows x 2), positions from the owner sketch, heights assumed")
WO_V = 29.8                                   # strip centre in the lower yard (moved off the fence, owner sketch)
Z_WO = Z_LOW                                  # lower yard level


def tube(nm, u0, v0, u1, v1, z0, z1, d=0.05, ue=None):
    """straight steel tube as a thin box: along u, along v or vertical (z0 != z1 with u0 == u1, v0 == v1)"""
    if abs(z1 - z0) > 1e-6:
        e = add(type="box", name=nm, center=W(u0, v0), size=[d, d, z1 - z0], dir_deg=ROT, z0=z0, material="metal")
    elif abs(v1 - v0) < 1e-6:
        e = add(type="box", name=nm, center=W((u0 + u1) / 2, v0), size=[abs(u1 - u0), d, d], dir_deg=ROT, z0=z0, material="metal")
    else:
        e = add(type="box", name=nm, center=W(u0, (v0 + v1) / 2), size=[abs(v1 - v0), d, d], dir_deg=DEG_N, z0=z0, material="metal")
    e.update(slot="M_Steel_Paint_Dark", evidence=EV_WO, confidence="low")
    if ue:
        e["ue_asset"] = ue
    return e


# owner sketches 2026-09-28: parallel bars just east of the stair foot (clear of the way down), the 4 pull-up bars behind them
# in two rows of two with a short gap, all bars along v (the stair's direction); wall bars (3 bays) against the retaining
# wall under the courts' N fence, east of the pull-ups
pv0, pv1, ph, pu = C_V1 + ST_N * ST_TR + 0.9, C_V1 + ST_N * ST_TR + 2.9, 1.25, ST_U1 + 1.4   # parallel (dip) bars
for su, u in (("W", pu - 0.28), ("E", pu + 0.28)):
    for sv, v in (("S", pv0 + 0.1), ("N", pv1 - 0.1)):
        tube(f"Workout_Dip_Post{su}{sv}", u, v, u, v, Z_WO, Z_WO + ph, d=0.07, ue="workout_parallel_bars" if su + sv == "WS" else None)
    tube(f"Workout_Dip_Bar{su}", u, pv0, u, pv1, Z_WO + ph - 0.02, Z_WO + ph - 0.02, d=0.045)
# owner 2026-09-28: the pull-ups are two welded units, each a high bar and a low bar on one frame of 3 posts (along v)
PU_V0, PU_L, PU_H = C_V1 + RW_TOP + 0.6, 1.2, (2.5, 2.2)
for k, uc in enumerate((pu + 1.9, pu + 3.7)):
    vs = [PU_V0 + PU_L * j for j in range(3)]
    for j, v in enumerate(vs):
        tube(f"Workout_PullUp{k}_Post{j}", uc, v, uc, v, Z_WO, Z_WO + max(PU_H[max(0, j - 1)], PU_H[min(1, j)]), d=0.08,
             ue="workout_pullup_bar_double" if j == 0 else None)
    for j, h in enumerate(PU_H):
        tube(f"Workout_PullUp{k}_Bar{j}", uc, vs[j], uc, vs[j + 1], Z_WO + h - 0.04, Z_WO + h - 0.04, d=0.035)
# owner 2026-09-28: two wall-bar units, bigger (3 bays of 0.9 m, 3.0 m high, rungs every 0.25 m), 12 cm off the wall
wb, wh, wv = 0.9, 3.0, C_V1 + RW_TOP + 0.12
for n, wu0 in enumerate((pu + 5.6, pu + 5.6 + 3 * wb + 0.4)):
    for j in range(4):
        u = wu0 + wb * j
        tube(f"Workout_WallBars{n}_Post{j}", u, wv, u, wv, Z_WO, Z_WO + wh, d=0.07, ue="workout_wall_bars" if j == 0 else None)
    for k in range(11):
        z = Z_WO + 0.3 + 0.25 * k
        tube(f"Workout_WallBars{n}_Rung{k}", wu0, wv, wu0 + 3 * wb, wv, z, z, d=0.03)

# ================================================================= PLAZA strip south of the pitch and courts
bench_u = [7.0, 10.25, 13.1, 16.0, 19.0, 23.5, 26.5, 30.05, 33.9, 37.1]   # u 40.0 (Google) absent in 070410255 t=52 s
for k, u in enumerate(bench_u):
    add(type="bench", name=f"PitchBench_{k:02d}", pos=W(u, -0.85), dir_deg=DEG_N, length=2.0, depth=0.55, seat_h=0.45,
        back_h=0.85, evidence=f"Google 2026: grey 2.0 x 0.55 m bench tops at v -0.6..-1.1, local u {bench_u}; "
        "dark steel frame benches facing the pitch (070541257 t=8-9.5 s, winter photo 2014)", confidence="medium")
for k, u in enumerate([59.7, 65.8, 71.6, 76.8, 81.9, 87.8, 93.6]):   # none at u 53.8 (070410255 t=52 s)
    add(type="planter", name=f"CourtsThujaPot_{k}", ring=rect(u - 0.4, u + 0.4, C_V0 - 2.3, C_V0 - 1.5), curb_w=0.08, curb_h=0.35,
        evidence="small square concrete planters with a thuja along the S side of the courts (drone 2022 d_23; Google dots "
                 "v -0.3..0.0, ~5.9 m spacing); not visible in the blurred 2026-09 frame 070410255 t=39 s: may be gone", confidence="low")
    add(type="tree", name=f"CourtsThuja_{k}", pos=W(u, C_V0 - 1.9), height=2.4, crown_d=0.8, crown_base=0.4, trunk_d=0.08,
        evidence="thuja ~2.4 m (drone d_23, vs the 4.9 m fence)", confidence="low")

# alley beds: 2 rows of elongated hexagonal beds, yellow/white curbs, 2 thujas + a double globe lamp each
ev_bed = ("Google 2026 bed outlines ~5.8 x 3.2 m (rows at v -8.1 and -15.0; row N: u -14.0, 1.4, 9.4, 25.7, 34.0; row S: "
          "u -14.1, 1.5, 9.6, 17.6, 25.5, 33.7); pointed-end hexagon curbs painted yellow/white, lawn, roses (070541257, "
          "070410255 t=54-58 s)")
beds = [(-14.0, -8.1), (1.4, -8.1), (9.4, -8.1), (25.7, -8.1), (34.0, -8.1),
        (-14.1, -15.0), (1.5, -15.0), (9.6, -15.0), (17.6, -15.0), (25.5, -15.0), (33.7, -15.0)]
for k, (u, v) in enumerate(beds):
    tag = f"{'N' if v > -10 else 'S'}{k if v > -10 else k - 5}"
    add(type="planter", name=f"AlleyBed_{tag}", ring=poly([(u - 2.95, v), (u - 2.0, v - 1.6), (u + 2.0, v - 1.6), (u + 2.95, v),
                                                           (u + 2.0, v + 1.6), (u - 2.0, v + 1.6)]),
        curb_w=0.12, curb_h=0.12, evidence=ev_bed, confidence="medium")
    for j, du in enumerate((-1.8, 1.8)):
        add(type="tree", name=f"AlleyThuja_{tag}_{j}", pos=W(u + du, v), height=4.6, crown_d=1.3, crown_base=0.3,
            trunk_d=0.12, evidence="two tall thujas per bed (dark crown pairs in Google at +-1.8 m); ~2.6 x a 1.75 m walker "
            "(070541257 t=3.5 s)", confidence="medium")
    add(type="lamp_orn", name=f"AlleyLamp_{tag}", pos=W(u, v), height=3.6, arm_span=0.95, globes=2, globe_d=0.3,
        dir_deg=DEG_N, evidence="black ornamental cast post with two scroll arms and white globes in the bed between the thujas "
                                "(070541257 t=8/9.5 s); height est. vs the thujas", confidence="low")
# festoon strings along the alley (between the thujas of each row) and across it (N bed -> S bed)
rowN = [(u, v) for u, v in beds if v > -10]
rowS = [(u, v) for u, v in beds if v < -10]
for nm, row in (("N", rowN), ("S", rowS)):
    ends = []
    for u, v in row:
        ends += [[*W(u - 1.8, v), 3.6], [*W(u + 1.8, v), 3.6]]
    add(type="string_lights", name=f"AlleyFestoon_{nm}", ends=ends, sag=0.35, spacing=0.9, bulb_d=0.08,
        evidence="warm bulbs on wires strung between the thujas along the alley at ~3-3.6 m (070541257 t=0-5 s)",
        confidence="low")
for (un, vn) in rowN:
    s = min(rowS, key=lambda b: abs(b[0] - un))
    add(type="string_lights", name=f"AlleyFestoonX_{un:+.0f}".replace("+", "p").replace("-", "m").replace(".", "_"),
        ends=[[*W(un, vn - 1.0), 3.5], [*W(s[0], s[1] + 1.0), 3.5]], sag=0.4, spacing=0.9, bulb_d=0.08,
        evidence="cross strings over the alley (070541257 t=0-5 s)", confidence="low")

# round bed with the ornamental lamp in front of the canteen W gable
rb_c, rb_r = (60.2, -11.6), 2.6
add(type="planter", name="RoundBed", ring=[W(rb_c[0] + rb_r * math.cos(a), rb_c[1] + rb_r * math.sin(a))
                                           for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)],
    curb_w=0.12, curb_h=0.12, evidence="Google 2026 disc: fitted ellipse centre local (60.22,-11.62), axes 5.14/5.20 m, area 21.7 m2; yellow/white curb, soil, "
    "two young trees and a plaque (070410255 t=44-46/65.5 s)", confidence="medium")
add(type="lamp_orn", name="RoundBed_Lamp", pos=W(*rb_c), height=3.6, arm_span=0.95, globes=2, dir_deg=DEG_N,
    evidence="same ornamental double-globe post in the bed centre (070410255 t=65.5 s; 2GIS 2019)", confidence="medium")
for k, (du, dv) in enumerate(((-1.2, 0.8), (1.1, -0.9))):
    add(type="tree", name=f"RoundBed_Tree_{k}", pos=W(rb_c[0] + du, rb_c[1] + dv), height=2.2, crown_d=1.0, crown_base=0.9,
        trunk_d=0.06, shape="round", evidence="two young deciduous trees (070410255 t=65.5 s); positions approximate",
        confidence="low")
# young trees along the hall's north side
for k, u in enumerate([-21.2, -15.0, -9.5, -3.9, 3.45, 9.1, 14.6, 19.9]):
    add(type="tree", name=f"HallRowTree_{k}", pos=W(u - 0.3, -24.25), height=3.5, crown_d=1.6, crown_base=0.6,
        evidence="Google 2026 dark crowns on a 5.5 m pitch at v -24 (lean-corrected -0.3/-0.2 m); spruces in front of the hall "
        "(drone 2022 row f 0:15-0:18)", confidence="low")

# ================================================================= NORTH strip (path, lawn bed, lane, tree lawn, boundary)
add(type="planter", name="NorthBed", ring=rect(0.0, 43.9, 27.0, 33.3), curb_w=0.15, curb_h=NB_RAISE + 0.1,
    evidence="Google 2026 lawn bed u 0..44.4, v 27.0..33.3 behind a 1.6 m paved path along the N fence (drone 2022 d_07/d_19: "
    "grey path, lawn with two rows of young blue spruces)", confidence="medium")
for k, (u, v) in enumerate([(0.8, 28.9), (5.35, 28.9), (10.75, 28.9), (15.85, 28.9), (20.55, 28.9), (25.45, 28.9),
                            (30.6, 28.9), (34.5, 28.9), (39.4, 28.9), (3.65, 30.65), (8.3, 30.65), (13.7, 30.65),
                            (18.7, 30.65), (23.1, 30.65), (28.25, 30.65), (32.85, 30.65), (37.45, 30.65), (40.7, 32.1)]):
    add(type="tree", name=f"NorthBedSpruce_{k:02d}", pos=W(u, v), height=2.6, crown_d=1.4, crown_base=0.2, trunk_d=0.08,
        evidence="Google 2026 dark crowns 1.0-1.8 m (lean-corrected ~-0.35/-0.2 m), two staggered rows ~4.9 m apart; young "
        "blue spruces ~2.5 m (drone d_07)", confidence="medium")
add(type="tree", name="NorthBedTree_Big", pos=W(43.2, 29.5), height=9.0, crown_d=5.0, crown_base=2.5, shape="round",
    evidence="large crown u 41..46, v 27..32 (Google 2026)", confidence="low")
add(type="planter", name="NorthTreeLawn", ring=rect(-40.0, 97.0, 38.3, 41.5), curb_w=0.12, curb_h=0.12,
    evidence="Google 2026 lawn strip v 38.3..41.5 along the boundary with a row of trees", confidence="medium")
for k, u in enumerate([-35.6, -23.3, -17.5, -12.3, -6.9, -1.7, 4.1, 9.2, 15.0, 20.5, 25.1, 32.6, 37.8, 43.1, 70.3, 75.7, 92.4]):
    big = u in (9.2, 15.0, 25.1, 37.8, 43.1, 70.3, 75.7, 92.4)
    add(type="tree", name=f"NorthLawnTree_{k:02d}", pos=W(u - 0.6, 39.4), height=7.0 if big else 4.5,
        crown_d=3.2 if big else 2.0, crown_base=1.5 if big else 0.4, shape="cone",
        evidence="Google 2026 crowns 2-5 m along v 39.2-40.1 (lean-corrected); blue spruces along the boundary (drone d_07)",
        confidence="low")
add(type="path", name="NorthLane_Path_W", line=poly([(-20.0, 36.0), (-112.0, 36.0)]), width=3.0, slot="M_Paving_Generic",
    evidence="owner 2026-09-28 (overview sketch): the low path along the back fence runs from the courts to Block D; west "
    "of the pitch it follows the natural ground (DEM 2.9 at u -30 rising to 3.7 at u -112); width 3.0 assumed", confidence="low")
# N boundary (owner 2026-09-28): red block pillars with pale-yellow cast sand-concrete panels between them, no openings;
# E boundary along the neighbour's wall: black steel bar fence (see-through, not cast)
NB_LINE = [(-112.0, 42.2), (93.0, 42.2), (100.5, 40.0)]
EV_NB = ("campus N boundary: dark line v 41.8-42.3 on Google 2026 (shadow of the wall), cars parked beyond; owner 2026-09-28: "
         "a solid fence of red block pillars with pale-yellow cast sand-concrete panels between them (replaces the bar fence + "
         "brick piers read from drone 2022 d_07); pillar pitch 3.0 m and heights assumed")
add(type="wall", name="NorthBoundary_Wall", line=poly(NB_LINE), height=2.2, thk=0.2, material="stone", slot="M_Block_PaleYellow",
    evidence=EV_NB, confidence="medium")
_k = 0
for (ua, va), (ub, vb) in zip(NB_LINE[:-1], NB_LINE[1:]):
    L = float(np.hypot(ub - ua, vb - va)); hd = ROT + float(np.degrees(np.arctan2(vb - va, ub - ua)))
    n = max(1, int(round(L / 3.0)))
    for j in range(n + (1 if (ub, vb) == NB_LINE[-1] else 0)):
        f = j / n; u, v = ua + (ub - ua) * f, va + (vb - va) * f
        add(type="box", name=f"NorthBoundary_Pillar_{_k:03d}", center=W(u, v), size=[0.45, 0.45, 2.5], dir_deg=hd,
            material="brick", slot="M_Tile_Brick_Red", evidence=EV_NB, confidence="low")
        add(type="box", name=f"NorthBoundary_PillarCap_{_k:03d}", center=W(u, v), size=[0.55, 0.55, 0.08], dir_deg=hd,
            z_rel=2.5, material="brick", slot="M_Tile_Brick_Red", evidence=EV_NB, confidence="low")
        _k += 1
add(type="fence", name="EastBoundary_Fence", line=poly([(100.5, 40.0), (100.5, -35.0)]), height=2.0, post_spacing=2.5,
    post=0.06, panel="bars", slot="M_Steel_Paint_Dark",
    evidence="owner 2026-09-28 (overview sketch): black steel bar fence along the east edge from the N boundary corner south "
    "to the level of Block C, beside the neighbour's west wall (x ~215.6); height 2.0 assumed", confidence="low")
# west of the pitch
add(type="slab", name="WestRedSquare", ring=rect(-16.5, -5.5, 17.5, 23.9), z0=Z_PLAZA - 0.05, z1=Z_PLAZA + 0.03,
    material="brick", evidence="Google 2026: mauve-red 11.0 x 6.4 m surface (not in Bing 2021/Esri 2020, which show a round "
    "bed at u ~-10, v 13); use unknown (rubber mat / stage?)", confidence="low")
add(type="tree", name="WestBigSpruce", pos=W(-18.0, 31.0), height=12.0, crown_d=8.0, crown_base=0.5,
    evidence="large blue spruce clump u -24..-12, v 25..38 (Google 2026, drone 2022)", confidence="low")

# ---------------------------------------------------------------- terrain pads
pads = [
    dict(name="SportsPlatform", ring=poly([(-20.0, -2.2), (101.0, -2.2), (101.0, 25.4), (44.35, 25.4), (44.35, 26.9),
                                           (-20.0, 26.9)]), z=Z_PLAZA, blend=10.0,
         evidence="bench strip, walkway, courts and the lane north of the courts read level in 070410255 t=52/60 s and drone "
                  "2022 d_23; level anchored to the DEM value at the middle of the pitch south edge (3.44; the DEM gives "
                  "3.3-3.6 along it, rms 1 m) so the 10 m blend into the alley/canteen stays within 0.1-0.4 m", confidence="low"),
    dict(name="NorthTerrace", ring=rect(-20.0, 44.35, 26.9, LANE_V0), z=Z_NORTH, blend=3.0,
         evidence="north path/lawn flush with the pitch plinth top (drone 2022 d_07/d_19); the walkway rises to it at its north "
                  "end (plinth tapers, step with pipe handrails in 070410255 t=60 s; modelled as the 3 m pad blend)",
         confidence="low"),
]
pads += [
    dict(name="LowerYard", ring=poly([(ST_U0 - 0.1, C_V1), (ST_U1, C_V1), (ST_U1, C_V1 + RW_TOP), (101.0, C_V1 + RW_TOP), (101.0, 44.0),
                                      (-20.0, 44.0), (-20.0, LANE_V0 + 0.3), (ST_U0 - 0.1, LANE_V0 + 0.3)]), z=Z_LOW, blend=0.0,
         evidence=ev_ly + "; the lane behind the pitch included (owner overview sketch)", confidence="low"),
    dict(name="NorthBedRaised", ring=rect(0.15, 43.75, 27.15, 33.15), z=Z_NORTH + NB_RAISE, blend=0.0,
         evidence="raised bed inside its curb (owner 2026-09-28)", confidence="low"),
]
for e in els:   # "ground" z0 marker -> resolved by the builder? (box needs absolute z0): use the pad z
    if e.get("z0") == "ground":
        e["z0"] = Z_NORTH - 0.3

spec = {
    "id": "SITE_Sports",
    "collection": "SITE_Sport",
    "ground": "pads",
    "replaces": ["GB_SITE_FootballPitch", "GB_SITE_Courts"],
    "note": ("Sports area north of the hall and Block C: a roofed 44.45 x 25.25 m mini-football cage (7 m mesh fence on a "
             "0.35 m brick plinth) and, 6.5 m east across a paved walkway, a 46.1 x 26.3 m block of three fenced courts "
             "(basketball | volleyball | tennis-lined hard court, 4.9 m fences). South of them the bench strip and the "
             "decorated alley (2 rows of hexagonal thuja beds with double-globe lamps and festoon lights), the round bed at the "
             "canteen gable; north the path, a spruce lawn bed, a lane, a tree lawn and the boundary wall. Sports frame: origin "
             "(114,45), u along -2.2 deg (world), v 'local north'; the spec generator keeps all measurements in that frame. "
             "Levels (relative from photos, absolute anchored to the DEM +-1 m): pads at z 3.45 (platform) / 3.75 (north terrace); pitch turf 3.80, courts 3.50. Geometry is placed on the "
             "padded ground ('ground': 'pads')."),
    "georef": ("user satellite screenshot (Google, 540x795) -> Google z20 ortho by SIFT + RANSAC affine: 1619 inliers, rms 0.19 m "
               "(0.8 screenshot px), scale 0.2299/0.2289 m/px, rotation -0.07 deg"),
    "terrain_pads": pads,
    "elements": els,
}
import os
SPECS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "Art", "Blender", "Specs")
out = os.path.join(SPECS, "SITE_Sports.json")
json.dump(spec, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("wrote", out, len(els), "elements")

# ================================================================= PASSAGE hall <-> Block C (the second descent)
# Local passage frame: origin = bottom riser centre of the stair (world 157.4, 9.2), x/y along the campus grid (DU/DV).
# Levels: terrace 5.35 (SITE_Garden) -> 5 risers x 0.175 -> 4.475 lower path (flat to y ~21) -> clover plaza falls ~4.8 %
# north to the pitch walkway (3.45, SITE_Sports). Drop measured in the SfM of 070410255 t=12-34 s, scale 2.0 m/unit from
# 0.2 x 0.1 m pavers and 1.0 m curb stones in its ortho (camera then 1.36 m above the paving).
Z_UP, Z_LOW, RISERS = 5.35, 4.475, 5
P0 = np.array([157.4, 9.2])
def pw(x, y): return R3(P0 + DU * x + DV * y)
def prect(x0, x1, y0, y1): return [pw(x0, y0), pw(x1, y0), pw(x1, y1), pw(x0, y1)]
TREAD = 0.33
SX0, SX1, S_RUN = -0.1, 2.1, (RISERS - 1) * TREAD + 0.40     # stair 2.2 m wide (x 157.3-159.5), run incl. top landing
RX0 = -1.1                                                     # grey grating ramp W of the stair (x 156.3-157.3)
RY0, RY1 = -2.0, 1.4                                           # ramp top / foot (world y 7.2 / 10.6)
EV_RAMP = ("070410255 t=33.5-34.5 s (fixG/hc/f4k/t30_15..19, st/t30_17c.jpg): grey steel mesh-grating ramp with square-"
           "tube rails (top + mid + bottom stringer) on the W side of the stair, same type as the other campus ramps; plan "
           "from Google z20: rails ~1.0 m apart at x 156.3-157.3, y 7.2-10.6 (fixG/st/ortho_stair.jpg, g_up.jpg)")
SHED_X = 10.45                                                 # Block C west shed front at the return arm (x 167.9)
pe = []
def padd(**e): pe.append(e); return e

EV_STAIR = ("070410255 t=26-33 s (2 fps a_053..a_067 + 10 fps crops): herringbone path between the hall E end and the lawn "
            "ends in a full-width granite stair descending north; granite cheek on its E side turns E at the bottom as the "
            "coping of the lawn's retaining edge, lower paved strip N of it running to the C shed front (a_062). Plan from "
            "Google z20 (return-arm coping shadow y 9.0-9.2, lower lawn W edge x 160.5, strip y 9.2-10.8, dirt bed y 0-9). 5 risers counted from the top "
            "landing (4K frame t=29.5 s: nosings at 1640/1450/1335/1235/1170 px); drop 0.44 SfM units x 2.0 m/unit = 0.88 m "
            "(SfM of t=12-34 s, 80 frames, pavement-normal up; scale from 0.2 x 0.1 m pavers and 1.0 m curbs) -> 5 x 0.175")
padd(type="steps", name="Passage_Stair", pos=pw((SX0 + SX1) / 2, 0.02), dir_deg=-92.2, width=SX1 - SX0, risers=RISERS,
     riser_h=round((Z_UP - Z_LOW) / RISERS, 3), tread=TREAD, top_landing=0.40, evidence=EV_STAIR, confidence="medium")
padd(type="slab", name="Passage_Cheek_E", ring=prect(SX1, SX1 + 0.3, -S_RUN, 0.0), z0=Z_LOW - 0.3, z1=Z_UP + 0.05,
     material="granite", evidence="pink granite cheek/coping along the E side of the flight, ~0.3 m wide, top ~5 cm above "
     "the upper lawn (a_059..a_061, 10 fps crops t=28-30 s)", confidence="medium")
padd(type="slab", name="Passage_Cheek_Return", ring=prect(SX1, SHED_X, -0.3, 0.0), z0=Z_LOW - 0.3, z1=Z_UP + 0.05,
     material="granite", evidence="the cheek turns E at the stair foot and runs to the C shed front as the coping of the "
     "upper lawn's retaining edge; lower paved strip with a manhole N of it (a_062, Google z20 shadow line y 9.0-9.2)",
     confidence="medium")
RZ = lambda y: Z_UP + (Z_LOW - Z_UP) * (y - RY0) / (RY1 - RY0)
padd(type="roof_plane", name="Passage_Ramp_Base", ring=prect(RX0, SX0, RY0, RY1), z=[Z_UP - 0.06, Z_UP - 0.06, Z_LOW - 0.06, Z_LOW - 0.06],
     thk=round(Z_UP - Z_LOW + 0.3, 3), material="stone", evidence=EV_RAMP + "; solid infill under the grating", confidence="medium")
padd(type="roof_plane", name="Passage_Ramp", ring=prect(RX0, SX0, RY0, RY1), z=[Z_UP, Z_UP, Z_LOW, Z_LOW], thk=0.06,
     material="metal", evidence=EV_RAMP, confidence="medium")
for nm, x in (("W", RX0 + 0.03), ("E", SX0 - 0.03)):
    padd(type="rail3d", name=f"Passage_RampRail_{nm}", points=[[*pw(x, RY0), Z_UP], [*pw(x, RY1), Z_LOW]], height=0.9,
         spacing=1.2, mid_rails=1, material="metal", unique_posts=True, evidence=EV_RAMP, confidence="medium")
padd(type="rail3d", name="Passage_LandingRail", points=[[*pw(-3.2, -1.35), Z_UP], [*pw(RX0, -1.35), Z_UP]],
     height=0.8, post=0.03, rail=0.04, spacing=0.12, mid_rails=0, material="metal", unique_posts=True,
     evidence="low black bar fence on the upper landing W of the ramp, dense verticals (~0.12 m), E-W at y 7.85, "
              "x 154.2-156.3 (070410255 frames 0030-0033, fixG/st/land.jpg; map owner: lower and denser than modelled)",
     confidence="medium")
padd(type="box", name="Passage_Bench", center=pw(-3.6, -4.9), dir_deg=round(float(np.degrees(np.arctan2(DV[1], DV[0]))), 2),
     size=[6.4, 0.8, 0.42], z0=Z_UP, material="brick",
     evidence="low maroon bench/ledge along the hall's E wall on the upper landing, x 153.4-154.2 (070410255 f55 overlay, "
              "fixG/st/ortho_stair.jpg); length estimated", confidence="low")
padd(type="planter", name="Passage_Lawn_Upper", ring=[pw(SX1, -8.8), pw(SHED_X - 0.2, -8.8), pw(SHED_X - 0.2, -0.3),
                                                      pw(SX1 + 0.3, -0.3), pw(SX1 + 0.3, -S_RUN), pw(SX1, -S_RUN)],
     curb_w=0.12, curb_h=0.12, evidence="upper lawn E of the path with yellow/white painted curbs and three blue spruces "
     "(a_038..a_061); Google z20 bed x 159.5..167.5, y 0..9 (dirt inside the cheek L at its N end)", confidence="medium")
padd(type="planter", name="Passage_Lawn_Lower", ring=prect(3.1, SHED_X, 2.5, 10.7), curb_w=0.12, curb_h=0.12,
     evidence="lower lawn with roses, blue spruces and a deciduous tree between the path and the C shed, yellow/white "
     "curbs on its W side (a_065..a_078); Google z20 x 160.5..167.8, y 11..19.5", confidence="medium")
for nm, (x, y), h, cd in (("Spruce_UpperSW", (161.2, 1.2), 11.0, 6.0), ("Spruce_UpperNW", (163.4, 6.6), 8.0, 4.0),
                          ("Spruce_UpperNE", (166.0, 6.8), 6.0, 3.5), ("Spruce_Lower", (164.5, 16.4), 6.0, 3.8),
                          ("Spruce_LowerSmall", (161.4, 17.8), 3.5, 2.0)):
    padd(type="tree", name=f"Passage_{nm}", pos=[x, y], height=h, crown_d=cd, crown_base=0.3, trunk_d=0.3,
         evidence="blue spruce: Google z20 dark crown, height vs the hall gable / C storeys (a_040, a_059, a_065)",
         confidence="medium" if nm.startswith("Spruce_Upper") else "low")
padd(type="tree", name="Passage_Tree_Lower", pos=[166.8, 12.0], height=7.0, crown_d=4.0, crown_base=2.0, shape="round",
     evidence="deciduous tree behind the lower spruce next to the shed (a_062..a_065)", confidence="low")
padd(type="wall", name="Passage_Curb_North", line=[[153.5, 24.5], [161.0, 24.2]], height=0.1, thk=0.15, material="stone",
     evidence="yellow-painted curb where the herringbone path meets the clover-paver plaza, ~0.1 m reveal (a_083..a_087)",
     confidence="low")
pass_pads = [
    dict(name="PassageUpper", z=Z_UP, blend=0.0,
         ring=[pw(-8.2, -10.0), pw(SHED_X - 0.1, -10.0), pw(SHED_X - 0.1, 0.0), pw(SX1, 0.0), pw(SX1, -S_RUN),
               pw(SX0, -S_RUN), pw(SX0, RY0), pw(RX0, RY0), pw(RX0, 0.0), pw(-8.2, 0.0)],
         evidence="the lower-terrace level continues N between the hall E gable and the upper lawn to the stair top "
                  "(flat camera track t=13-30 s in the SfM, no steps in a_026..a_061)", confidence="medium"),
    dict(name="PassageLower", z=Z_LOW, blend=0.0,
         ring=[pw(RX0, RY0), pw(SX0, RY0), pw(SX0, -S_RUN), pw(SX1, -S_RUN), pw(SX1, 0.0), pw(SHED_X + 0.4, 0.0),
               pw(SHED_X + 0.8, 12.7), pw(-5.0, 12.9), pw(-8.2, 3.0), pw(-8.2, 0.0), pw(RX0, 0.0)],
         evidence="stair foot and the herringbone path N along the hall wing, flat (a_062..a_078); PnP-free check at t=39 s: "
                  "camera (156.5,20.6) from the pitch/courts door sizes (22.9/26.1 m), horizon from the walkway-edge "
                  "vanishing point 2.55 m above the pitch walkway -> ground there = walkway + 1.2 = 4.6", confidence="medium"),
    dict(name="PlazaSlope", z=Z_LOW, grad=[0.0, round(-(Z_LOW - 3.45) / 21.0, 4)], ref=[157.4, 22.0], blend=1.0,
         ring=[[150.9, 22.0], [171.0, 21.2], [171.9, 42.3], [151.8, 43.1]],
         evidence="clover-paver plaza between the hall wing and the canteen falls ~1.0 m from the path end (y 22, 4.475) to "
                  "the pitch walkway (3.45): t=39 s horizon (above) and PnP at t=52 s at f 1740 px (camera 1.86 above the "
                  "walkway at y 28.3 -> ground there ~3.95 +-0.25, slope model 4.13); no steps seen (a_079..a_110)",
         confidence="low"),
]
pspec = {
    "id": "SITE_HallCPassage", "collection": "SITE_Sport", "ground": "pads",
    "note": ("Passage between the sports hall E gable / wing and Block C's west shed: the lower-terrace path runs N to a "
             "full-width granite stair (5 risers x 0.175, 5.35 -> 4.475) with a granite cheek that returns E as the coping of the "
             "upper lawn; below it a paved strip to the shed front and the herringbone path N along the hall wing to the "
             "clover plaza of the sports area (curb at y 24.5). Generated by Scripts/Geo/zones/zone_sports.py."),
    "terrain_pads": pass_pads, "elements": pe,
}
out = os.path.join(SPECS, "SITE_HallCPassage.json")
json.dump(pspec, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("wrote", out, len(pe), "elements")
