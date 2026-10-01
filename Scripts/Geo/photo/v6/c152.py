# 152 (C105 window wall): tile pitch on the beam face sets the scale; beam depth, first cut row, windows, corners.
import numpy as np, sys
sys.path.insert(0, sys.argv[1]); from metro import Cam
from scipy.optimize import brentq
vv, vz, vx = np.load(sys.argv[1] + '/152_vps.npy'); f = float(sys.argv[2])
def rp(c, px, n, d): r = c.Ki @ np.array([px[0], px[1], 1.0]); return r * d / np.dot(n, r)
def rot(v, k, t): return v*np.cos(t) + np.cross(k, v)*np.sin(t) + k*np.dot(k, v)*(1-np.cos(t))
c = Cam(f, (vz[0], 1536), vv, vz); u = c.u
dx = c.Ki @ vx; w = np.cross(u, dx); w /= np.linalg.norm(w); w = w if w[2] > 0 else -w
seams = [(791, 424.6), (1158, 431), (1521, 434), (1883, 436), (2242, 440), (2600, 445.6), (2955, 449)]
def spread(t):
    ww = rot(w, u, t); Q = [rp(c, p, ww, 1.0) for p in seams]; dd = np.array([np.linalg.norm(Q[i+1]-Q[i]) for i in range(len(Q)-1)])
    return np.polyfit(np.arange(len(dd)), dd/dd.mean(), 1)[0]
t = brentq(spread, -0.2, 0.2); w = rot(w, u, t)
ex = np.cross(u, w)
if (c.K @ (np.array([0,0,5.]) + ex))[0] < (c.K @ [0,0,5.])[0]: ex = -ex
P = [rp(c, p, w, 1.0) for p in seams]; d = [np.linalg.norm(P[i+1]-P[i]) for i in range(len(P)-1)]; s = 0.6/np.mean(d)
hc = np.mean([np.dot(u, Q) for Q in P])
cr = rp(c, (2240, 331), u, hc); cut = (np.dot(w, cr) - 1.0) * s * -1
res = {}
for x in (1500, 3000):
    yf, yb = {1500: (568, 610.3), 3000: (578.5, 621)}[x]
    hu = np.dot(u, rp(c, (x, yf), w, 1.0)); Bk = rp(c, (x, yb), u, hu); res[x] = ((np.dot(w, Bk) - 1.0) * s, (hc - hu) * s)
print(f"f{f} yaw {np.degrees(t):.2f}: pitch {np.round(np.array(d)*s,3)} | first row beam-face->cross seam {cut:.3f} | beam depth/drop {[(round(a,3), round(b,3)) for a,b in res.values()]} | dist {s:.2f}")
np.save(sys.argv[1] + '/152_frame.npy', np.r_[w, ex, s, hc])
for xs in (1700, 2240, 2900):
    ys = {1700: (437.5, 323.5, 168), 2240: (440, 328, 174), 2900: (448.5, 334, 183)}[xs]
    pts = [rp(c, (xs, y), u, hc) for y in ys]
    print('   x', xs, 'rows from beam face:', [round((np.dot(w, pts[0]) - np.dot(w, q)) * s, 3) for q in pts[1:]])
