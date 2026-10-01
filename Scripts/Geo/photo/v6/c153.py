# 153 (C105 board wall, straight on): positions along the board wall from the window side, tile layout across the room.
import numpy as np, sys
sys.path.insert(0, sys.argv[1]); from metro import Cam
vv, vz, vx = np.load(sys.argv[1] + '/153_vps.npy'); f = float(sys.argv[2])
def rp(c, px, n, d): r = c.Ki @ np.array([px[0], px[1], 1.0]); return r * d / np.dot(n, r)
c = Cam(f, (vz[0], 1536), vv, vz); u = c.u
dx = c.Ki @ vx; w = np.cross(u, dx); w /= np.linalg.norm(w); w = w if w[2] > 0 else -w
seams0 = [(892, 491), (1248, 495), (1600, 494), (1950, 494), (2297, 497), (2642, 497), (2985, 499.4), (3324, 500)]
def rot(v, k, t): return v*np.cos(t) + np.cross(k, v)*np.sin(t) + k*np.dot(k, v)*(1-np.cos(t))
def spread(t):
    ww = rot(w, u, t); Q = [rp(c, p, ww, 1.0) for p in seams0]; dd = np.array([np.linalg.norm(Q[i+1]-Q[i]) for i in range(len(Q)-1)])
    return np.polyfit(np.arange(len(dd)), dd/dd.mean(), 1)[0]
from scipy.optimize import brentq
t = brentq(spread, -0.2, 0.2); w = rot(w, u, t); print('yaw correction deg', round(np.degrees(t), 2))
ex = np.cross(u, w); 
if (c.K @ (np.array([0,0,5.]) + ex))[0] < (c.K @ [0,0,5.])[0]: ex = -ex
seams = [(892, 491), (1248, 495), (1600, 494), (1950, 494), (2297, 497), (2642, 497), (2985, 499.4), (3324, 500), (3666, 500)]
P = [rp(c, p, w, 1.0) for p in seams]; d = [np.linalg.norm(P[i+1]-P[i]) for i in range(len(P)-1)]
s = 0.6 / np.mean(d[:-1])                     # last seam is faint
X = lambda Q: np.dot(ex, Q) * s
Pc = rp(c, (586, 487), w, 1.0); hc = np.dot(u, Pc)
Pp = rp(c, (559, 471), u, hc); p = (1.0 - np.dot(w, Pp)) * s     # pilaster face in front of the board wall
win = rp(c, (245, 1200), w, 1.0 - p/s)                             # window-wall corner on the pilaster face
xw = X(win)
items = {'pilaster side edge (586)': Pc, 'pilaster front edge (559, ceiling)': Pp, 'door-wall bulkhead face (3746)': rp(c, (3746, 560), w, 1.0),
         'door-wall corner (3899)': rp(c, (3899, 700), w, 1.0)}
print(f"f{f}: pitch {np.round(np.array(d)*s,3)}  pilaster depth {p:.3f}  wall dist {s:.2f}")
for k, Q in items.items(): print(f"   {k:36s} {X(Q)-xw:7.3f}")
for sp, Q in zip(seams, P): print(f"   seam {sp[0]:5d} {X(Q)-xw:7.3f}")
for nm, px in [('beam bottom-front corner (514,640)', (514, 640)), ('pilaster edge at y640 (563.5)', (563.5, 640)), ('beam top kink (555,471)', (555, 471))]:
    print(f"   {nm:36s} {X(rp(c, px, w, 1.0 - p/s)) - xw:7.3f}")
hb = np.dot(u, rp(c, (514, 640), w, 1.0 - p/s))
print('   beam drop below ceiling junction', round((hb - hc) * -s * -1, 3) if False else round((hc - hb) * s * -1, 3))
for xq, yc, yf in [(1950, 494, 2143), (1500, 492, 2150)]:
    Cc = rp(c, (xq, yc), w, 1.0); Ff = rp(c, (xq, yf), w, 1.0)
    print(f"   x{xq}: grid at board wall above floor {np.dot(u, Cc - Ff) * s:.3f}")
TV = [rp(c, q, w, 1.0 - 0.04/s) for q in [(1188.5, 974.3), (2103, 975), (1202.8, 1481), (2106, 1475)]]
print(f"   TV W {np.linalg.norm(TV[1]-TV[0])*s:.3f} {np.linalg.norm(TV[3]-TV[2])*s:.3f}  H {np.linalg.norm(TV[2]-TV[0])*s:.3f} {np.linalg.norm(TV[3]-TV[1])*s:.3f}")
