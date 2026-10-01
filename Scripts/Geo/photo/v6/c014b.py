# Photo 014: door opening, door-wall bulkhead and ceiling-tile pitch in one calibrated view (camera height = 1 unit).
import numpy as np, sys
sys.path.insert(0, sys.argv[1]); from metro import Cam
vv, vz, vx = np.load(sys.argv[1] + '/014_vps.npy')
SK = 0.015; DOOR = float(sys.argv[2]) if len(sys.argv) > 2 else 1.968
def ray_plane(c, px, n, d):        # plane n·X = d
    r = c.Ki @ np.array([px[0], px[1], 1.0]); return r * d / np.dot(n, r)
def vert_foot(top, a, b):
    l1 = np.cross([*top, 1], vv); l2 = np.cross([*a, 1], [*b, 1]); p = np.cross(l1, l2); return p[:2]/p[2]
for f, pp in ((2850, (1637, 2010)), (3060, (1637, 2040)), (2700, (1637, 1990))):
    c = Cam(f, pp, vv, vz)
    ska, skb = (1207, 3774.5), (2401, 3796.4)
    TL, TR = (1148, 1413.8), (2309.5, 1390.8)
    BL = c.floor(vert_foot(TL, ska, skb)); BR = c.floor(vert_foot(TR, ska, skb))
    # wall plane through the wall-face floor line (skirting foot + SK behind it; SK applied after scale is known)
    hl = c.height(BL, TL); hr = c.height(BR, TR); s = DOOR / ((hl + hr) / 2)
    BL += c.w*SK/s; BR += c.w*SK/s; hl = c.height(BL, TL); hr = c.height(BR, TR); s = DOOR / ((hl + hr) / 2)
    dx = c.Ki @ vx; nw = np.cross(c.u, dx); nw /= np.linalg.norm(nw)
    print('  wall-normal from floor line vs vx deg', np.degrees(np.arccos(abs(np.dot(nw, np.cross(BR-BL, c.u)/np.linalg.norm(np.cross(BR-BL, c.u)))))).round(2))
    if np.dot(nw, BL) < 0: nw = -nw
    dw = np.dot(nw, BL)
    wdt = np.linalg.norm(BR - BL) * s
    back = [ray_plane(c, p, nw, dw) for p in [(1160, 570.8), (1440, 565), (2260, 535.2), (2540, 528)]]
    hb = [(np.dot(c.u, X) + 1) * s for X in back]                  # height above floor (floor is u·X = -1)
    hu = np.mean(hb) / s - 1                                          # underside plane u·X = hu
    front = [ray_plane(c, p, c.u, hu) for p in [(1160, 388.7), (1440, 383), (2260, 353.4), (2540, 350.6)]]
    depth = [(dw - np.dot(nw, X)) * s for X in front]
    dB = np.mean(depth) / s
    S1 = ray_plane(c, (1310, 157), nw, dw - dB); S2 = ray_plane(c, (2188, 125), nw, dw - dB)
    pitch = np.linalg.norm(S2 - S1) * s
    hc = [(np.dot(c.u, X) + 1) * s for X in (S1, S2)]
    print(f"f{f} pp{pp}: door W {wdt:.3f} | underside h {np.round(hb,3)} | bulkhead depth {np.round(depth,3)} | ceiling@angle {np.round(hc,3)} | tile pitch {pitch:.3f} | camH {s:.3f} wall dist {dw*s:.2f}")
