# Door-opening size from a person standing with heels against the threshold (single-view metrology, floor plane).
# Inputs per photo: arris top corners, skirting-foot points left/right, head top, heel-line point, person box, floor y.
import numpy as np, sys, json, cv2
sys.path.insert(0, sys.path[0]); from vp import fit_vp; from metro import Cam
def segs(path):
    g = cv2.imread(path, cv2.IMREAD_GRAYSCALE); L = cv2.createLineSegmentDetector(cv2.LSD_REFINE_ADV).detect(g)[0].reshape(-1, 4)
    return L[np.hypot(L[:,2]-L[:,0], L[:,3]-L[:,1]) > 60]
def run(P, HP=1.85, AX=0.10, SK=0.015, f=2850, verbose=True):
    S = segs(P['img']); ang = np.degrees(np.arctan2(np.abs(S[:,3]-S[:,1]), np.abs(S[:,2]-S[:,0]))); ln = np.hypot(S[:,2]-S[:,0], S[:,3]-S[:,1])
    mx = (S[:,0]+S[:,2])/2; my = (S[:,1]+S[:,3])/2; px0, py0, px1, py1 = P['person']
    inP = (mx > px0) & (mx < px1) & (my > py0) & (my < py1)
    vv, kv, _ = fit_vp(S[(ang > 75) & (ln > 150) & ~inP & (my < P['floor_y'])])
    fl = (ang > 25) & (ang < 89.5) & (ln > 90) & (my > P['floor_y']) & ~inP
    for b in P.get('exclude', []): fl &= ~((mx > b[0]) & (mx < b[2]) & (my > b[1]) & (my < b[3]))
    vz, kz, rz = fit_vp(S[fl], thr=6)
    if 'vz' in P: vz = np.array([*P['vz'], 1.0]); kz = np.ones(1, bool)
    vv = vv/vv[2]; vz = vz/vz[2]
    c0 = np.array([1536., 2040.]) if P.get('portrait', True) else np.array([2040., 1536.])
    fo = np.sqrt(max(-np.dot(vv[:2]-c0, vz[:2]-c0), 0))
    c = Cam(f, (vz[0], c0[1]), vv, vz)           # principal x on the depth VP column (camera faces the wall)
    def foot(top, sk):                          # arris vertical through `top` meets the skirting-foot line
        a = np.cross([*top, 1], vv); b = np.cross([*sk[0], 1], [*sk[1], 1]); p = np.cross(a, b); return p[:2]/p[2]
    BLi = foot(P['TL'], P['sk']); BRi = foot(P['TR'], P['sk'])
    heel = c.floor(P['heel']); s = 1.0
    for _ in range(30):
        B = heel - c.w*AX/s; s = HP / c.height(B, P['head'])
    BL = c.floor(BLi) + c.w*SK/s; BR = c.floor(BRi) + c.w*SK/s
    hl = c.height(BL, P['TL'])*s; hr = c.height(BR, P['TR'])*s
    TL = BL + c.u*hl/s; TR = BR + c.u*hr/s
    r = dict(H_left=hl, H_right=hr, W_top=np.linalg.norm(TR-TL)*s, W_bot=np.linalg.norm(BR-BL)*s,
             camH=s, wall=np.dot(BL, c.w)*s, reveal_cm=np.dot(BL-heel, c.w)*s*100, f_orth=fo, nv=int(kv.sum()), nz=int(kz.sum()))
    r['cam']=c; r['s']=s
    if verbose: print(P['img'].split('/')[-1][:3], {k: round(float(v), 3) for k, v in r.items() if k not in ('cam','s')}, 'BLi', BLi.round(1), 'BRi', BRi.round(1))
    return r
if __name__ == '__main__':
    for P in json.load(open(sys.argv[1])): run(P)
