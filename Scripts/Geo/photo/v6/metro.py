# Calibrated single-view metrology on the floor plane (Criminisi-style): camera height = 1 unit, scale from a person.
import numpy as np
def h(p): return np.array([p[0], p[1], 1.0])
class Cam:
    def __init__(s, f, c, vv, vz):
        s.K = np.array([[f,0,c[0]],[0,f,c[1]],[0,0,1.]]); s.Ki = np.linalg.inv(s.K)
        u = s.Ki @ vv; u /= np.linalg.norm(u)
        if u[1] > 0: u = -u          # up = toward image top
        s.u = u
        w = s.Ki @ vz; w /= np.linalg.norm(w); w -= u*np.dot(w,u); w /= np.linalg.norm(w)
        if w[2] < 0: w = -w          # floor direction away from camera (toward the wall)
        s.w = w
    def floor(s, p):                 # image point -> 3D floor point (camera height 1)
        r = s.Ki @ h(p); return r * (-1.0/np.dot(s.u, r))
    def height(s, B, t):             # height above 3D base B of the vertical through image point t
        T = h(t); a = np.cross(s.K @ B, T); b = np.cross(s.K @ s.u, T)
        return -np.dot(a, b)/np.dot(b, b)
    def proj(s, X): x = s.K @ X; return x[:2]/x[2]
