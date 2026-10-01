# 151: positions along the C105 door wall (metres from the board-wall corner), tile layout and pilaster.
import numpy as np, sys
sys.path.insert(0, sys.argv[1]); from metro import Cam
vv, vz, vx = np.load(sys.argv[1] + '/151_vps.npy'); f = float(sys.argv[2]) if len(sys.argv) > 2 else 2894
def rp(c, px, n, d): r = c.Ki @ np.array([px[0], px[1], 1.0]); return r * d / np.dot(n, r)
c = Cam(f, (vz[0], 1536), vv, vz); u = c.u
dx = c.Ki @ vx; w = np.cross(u, dx); w /= np.linalg.norm(w); w = w if w[2] > 0 else -w
ex = np.cross(w, u); ex = ex if np.dot(ex, dx) * np.sign(vx[0]) >= 0 else -ex   # along the wall, image-right
ex = ex if (c.K @ (np.array([0,0,5.]) + ex))[0] / (c.K @ (np.array([0,0,5.]) + ex))[2] > (c.K @ [0,0,5.])[0] / 5 else -ex
seams = [(600, 254), (955, 254), (1302, 254), (1645, 254), (1985, 254), (2325, 254), (2662, 254), (3000, 254), (3365, 254)]
S = [rp(c, p, w, 1.0) for p in seams]
s = 0.6 / np.mean([np.linalg.norm(S[i+1]-S[i]) for i in range(1, 7)])     # well-visible seams only
hf = np.mean([np.dot(u, rp(c, p, w, 1.0)) for p in [(1500, 387.6), (3000, 385.5)]])
Dw = np.mean([np.dot(w, rp(c, p, u, hf)) for p in [(1500, 421.2), (3000, 419.7)]])
FL = rp(c, (715, 1831.8), w, Dw); hfl = np.dot(u, FL)
X = lambda P: np.dot(ex, P) * s
x0 = X(rp(c, (400, 420), w, Dw))                                 # board-wall corner at wall level
pts = {'corner board (wall, y420)': rp(c, (400, 420), w, Dw), 'corner board (wall, y998)': rp(c, (450, 998), w, Dw),
       'bulkhead face L end': rp(c, (300, 300), w, 1.0), 'door arris L': rp(c, (677.5, 805.8), w, Dw), 'door arris R': rp(c, (1171.8, 807.5), w, Dw),
       'pilaster edge 3401': rp(c, (3401, 600), w, Dw), 'pilaster 3477': rp(c, (3477, 600), w, Dw), 'pilaster 3557': rp(c, (3557, 600), w, Dw),
       'bulkhead face R end': rp(c, (3480, 300), w, 1.0)}
for k, P in pts.items(): print(f"{k:28s} x {X(P)-x0:7.3f}")
for p, P in zip(seams, S): print(f"seam {p[0]:5d} x {X(P)-x0:7.3f}")
hg = np.dot(u, S[1])
cross = rp(c, (2900, 131), u, hg); print('cut row next to the bulkhead (face -> first cross seam)', round((1.0 - np.dot(w, cross)) * s, 3))
cross2 = rp(c, (320, 122), u, hg); print('same, left end', round((1.0 - np.dot(w, cross2)) * s, 3))
print('scale m/unit', round(s, 4), 'bulkhead depth', round((Dw-1)*s, 3), 'grid h', round((hg-hfl)*s, 3), 'underside', round((hf-hfl)*s, 3))
# corner pilaster: edge 3401 on the wall plane (x = L - px); edge 3477 same x on its front face (depth pw); edge 3557 = back wall
xA = X(rp(c, (3401, 600), w, Dw))
from scipy.optimize import brentq
g = lambda pw: X(rp(c, (3477, 600), w, Dw - pw/s)) - xA
pw = brentq(g, -0.5, 1.0)
L = X(rp(c, (3557, 600), w, Dw - pw/s)) - x0
print('pilaster: front face depth from door wall', round(pw, 3), '| back wall at x', round(L, 3), '| pilaster width along wall', round(L - (xA - x0), 3))
for xi in (3401, 3477, 3557):
    for dep in (0.0, 0.15, 0.28, 0.40):
        print(f"   edge {xi} on plane {dep:.2f} in front of door wall: x {X(rp(c, (xi, 600), w, Dw - dep/s)) - x0:6.3f}")
