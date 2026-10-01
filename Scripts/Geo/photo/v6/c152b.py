# 152 window wall: windows, corner column and beam, using the frame solved in c152.py (run it first with the same f).
import numpy as np, sys
sys.path.insert(0, sys.argv[1]); from metro import Cam
from scipy.optimize import brentq
vv, vz, vx = np.load(sys.argv[1] + '/152_vps.npy'); f = float(sys.argv[2]); B = 0.49; GRID = 2.90
fr = np.load(sys.argv[1] + '/152_frame.npy'); w, ex, s, hc = fr[:3], fr[3:6], fr[6], fr[7]
c = Cam(f, (vz[0], 1536), vv, vz); u = c.u
def rp(px, n, d): r = c.Ki @ np.array([px[0], px[1], 1.0]); return r * d / np.dot(n, r)
Dw = 1.0 + B/s
X = lambda Q: np.dot(ex, Q) * s
H = lambda Q: GRID - (hc - np.dot(u, Q)) * s
# corner column at the back wall: F1/F2 edge (658) and F2/window edge (767) share X; F1 plane depth cy in front of the window wall
xe = X(rp((767, 1100), w, Dw))
cy = brentq(lambda cy: X(rp((658, 1100), w, Dw - cy/s)) - xe, -0.3, 1.5)
x_back = X(rp((508, 1100), w, Dw - cy/s))
print(f"f{f}: column at back corner {xe - x_back:.3f} along x {cy:.3f} deep | (back wall = 0)")
for nm, px in [('win1 L', (1017, 1100)), ('win1 R', (2078, 1100)), ('win2 L', (2420, 1100)), ('win2 R', (3480, 1100)), ('wall end R (board pilaster)', (3700, 1100))]:
    print(f"   {nm:28s} {X(rp(px, w, Dw)) - x_back:6.3f}")
for nm, px in [('win1 top', (1500, 705)), ('win1 bottom', (1500, 1472)), ('win2 top', (3000, 720)), ('win2 bottom', (3000, 1480)), ('beam underside front (568)', (1500, 568))]:
    d = 1.0 if 'beam' in nm else Dw
    print(f"   {nm:28s} h {H(rp(px, w, d)):6.3f}")
bk = rp((1500, 634), u, np.dot(u, rp((1500, 568), w, 1.0))); print('   beam depth if underside back edge at 634:', round((np.dot(w, bk) - 1.0) * s, 3))
bw = X(rp((3700, 1100), w, Dw)) + 0.094          # board wall
for sx, sy in [(791, 424.6), (1158, 431), (1521, 434), (1883, 436), (2242, 440), (2600, 445.6), (2955, 449), (3308, 452), (3660, 454)]:
    q = X(rp((sx, sy), w, 1.0)); print(f"   seam {sx:5d}: from back wall {q - x_back:6.3f}  from board wall {bw - q:6.3f}")
