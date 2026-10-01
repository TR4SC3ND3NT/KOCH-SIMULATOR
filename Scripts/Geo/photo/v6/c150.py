# 150 (C105 door wall, 2nd view): same chain as c151b; positions from the door's left arris.
import numpy as np, sys
sys.path.insert(0, sys.argv[1]); from metro import Cam
from scipy.optimize import brentq
vv, vz, vx = np.load(sys.argv[1] + '/150_vps.npy'); f = float(sys.argv[2])
def rp(c, px, n, d): r = c.Ki @ np.array([px[0], px[1], 1.0]); return r * d / np.dot(n, r)
def rot(v, k, t): return v*np.cos(t) + np.cross(k, v)*np.sin(t) + k*np.dot(k, v)*(1-np.cos(t))
c = Cam(f, (vz[0], 1536), vv, vz); u = c.u
dx = c.Ki @ vx; w = np.cross(u, dx); w /= np.linalg.norm(w); w = w if w[2] > 0 else -w
seams = [(862, 400), (1213, 407), (1555, 413), (1890, 420), (2220, 423), (2548, 427), (2872, 432)]
def spread(t):
    ww = rot(w, u, t); Q = [rp(c, p, ww, 1.0) for p in seams]; dd = np.array([np.linalg.norm(Q[i+1]-Q[i]) for i in range(len(Q)-1)])
    return np.polyfit(np.arange(len(dd)), dd/dd.mean(), 1)[0]
t = brentq(spread, -0.2, 0.2); w = rot(w, u, t)
ex = np.cross(u, w)
if (c.K @ (np.array([0,0,5.]) + ex))[0] < (c.K @ [0,0,5.])[0]: ex = -ex
P = [rp(c, p, w, 1.0) for p in seams]; d = [np.linalg.norm(P[i+1]-P[i]) for i in range(len(P)-1)]; s = 0.6/np.mean(d)
hf = np.mean([np.dot(u, rp(c, p, w, 1.0)) for p in [(1500, 539), (2800, 555)]])
Dw = np.mean([np.dot(w, rp(c, p, u, hf)) for p in [(1500, 569.6), (2800, 584)]])
FL = rp(c, (590, 1972.7), w, Dw); hfl = np.dot(u, FL)
X = lambda Q: np.dot(ex, Q) * s
x0 = X(rp(c, (573.3, 939.3), w, Dw))
xA = X(rp(c, (3250, 800), w, Dw))
pw = brentq(lambda pw: X(rp(c, (3310, 800), w, Dw - pw/s)) - xA, -0.5, 1.0)
L = X(rp(c, (3390, 800), w, Dw - pw/s))
print(f"f{f} yaw {np.degrees(t):.2f}: pitch {np.round(np.array(d)*s,3)} bulkhead {(Dw-1)*s:.3f} grid {(np.dot(u,P[0])-hfl)*s:.3f} underside {(hf-hfl)*s:.3f}")
print(f"   door W {X(rp(c, (1071.3, 945.5), w, Dw)) - x0:.3f} H {(np.dot(u, rp(c,(573.3,939.3),w,Dw)) - hfl)*s:.3f} | from door-L: seam862 {X(P[0])-x0:.3f} | bulkhead R end {X(rp(c,(3321,550),w,1.0))-x0:.3f} | E1 {xA-x0:.3f} pilaster depth {pw:.3f} back wall {L-x0:.3f}")
