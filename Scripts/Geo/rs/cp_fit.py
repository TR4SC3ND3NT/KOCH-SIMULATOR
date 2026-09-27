# Control-point fit of one zone component to the campus world (R1 pass P0, handoff section 4.2 "control corners"):
# each control point is a pixel in a solved frame of the component where a known world point is seen (a building
# corner at the ground from the BLD specs, a kerb corner from the orthophoto); the pixel ray is cast into the
# component mesh to get the model point. Up and scale come from zone_world.py (ground planes, eye height) unless
# --free (>= 3 points: full similarity). Writes <comp>/align.json and prints the residual per point.
# cps.json: [{"cam": "070647586_f00255", "u": 1234, "v": 2100, "world": [x, y] or [x, y, z], "note": "C SE corner"}]
# Usage: python cp_fit.py <comp_dir> cps.json [--eye 1.52] [--free] [--z-known]
import argparse
import json
import os
import sys

import numpy as np
import open3d as o3d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zone_world as zw  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comp"); ap.add_argument("cps")
    ap.add_argument("--eye", type=float, default=1.52); ap.add_argument("--free", action="store_true")
    a = ap.parse_args()
    m = json.load(open(os.path.join(a.comp, "model.json")))
    tm = o3d.io.read_triangle_mesh(os.path.join(a.comp, "mesh.obj"), enable_post_processing=False)
    V = np.asarray(tm.vertices); F = np.asarray(tm.triangles)
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(V.astype(np.float32)), o3d.core.Tensor(F.astype(np.uint32)))
    gp = zw.ground_planes(sc, m)
    up = np.median([g[0] for g in gp], 0); up /= np.linalg.norm(up); h = float(np.median([g[1] for g in gp])); s = a.eye / h
    Rl = zw.rot_to_z(up)
    cps = json.load(open(a.cps, encoding="utf-8-sig"))
    P, Wd, notes = [], [], []
    for cp in cps:
        c = next(x for x in m["cameras"] if cp["cam"] in x["name"])
        d = np.array(c["R"]).T @ np.array([(cp["u"] - c["cx"]) / c["f"], (cp["v"] - c["cy"]) / c["fy"], 1.0]); d /= np.linalg.norm(d)
        o = np.array(c["center"])
        t = sc.cast_rays(o3d.core.Tensor(np.concatenate([o, d])[None].astype(np.float32)))["t_hit"].numpy()[0]
        if not np.isfinite(t):
            print("miss:", cp.get("note", cp["cam"])); continue
        P.append(o + d * t); Wd.append(cp["world"]); notes.append(cp.get("note", cp["cam"]))
    P = np.array(P); L = s * (P @ Rl.T)
    Wxy = np.array([w[:2] for w in Wd], float)
    if a.free and len(P) >= 3:
        # 2D similarity on xy (Umeyama) after levelling; scale free
        mu_p, mu_w = L[:, :2].mean(0), Wxy.mean(0); A = L[:, :2] - mu_p; B = Wxy - mu_w
        U, S, Vt = np.linalg.svd(B.T @ A); D = np.diag([1, np.sign(np.linalg.det(U @ Vt))])
        R2 = U @ D @ Vt; k = (S * np.diag(D)).sum() / (A ** 2).sum(); s *= k; L *= k
        t2 = mu_w - R2 @ mu_p
    else:
        # rotation + translation only (scale from the eye height)
        mu_p, mu_w = L[:, :2].mean(0), Wxy.mean(0); A = L[:, :2] - mu_p; B = Wxy - mu_w
        th = np.arctan2((A[:, 0] * B[:, 1] - A[:, 1] * B[:, 0]).sum(), (A * B).sum())
        R2 = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]); t2 = mu_w - R2 @ mu_p
    zs = [w[2] - L[i, 2] for i, w in enumerate(Wd) if len(w) > 2]
    tz = float(np.median(zs)) if zs else None
    if tz is None:
        camxy = np.array([(R2 @ (s * (Rl @ np.array(c["center"])))[:2]) + t2 for c in m["cameras"]])
        camz = np.median([s * (Rl @ np.array(c["center"]))[2] for c in m["cameras"]])
        tz = float(np.median([zw.terrain_z(*p) for p in camxy])) + a.eye - float(camz)
    R3 = np.eye(3); R3[:2, :2] = R2; Rw = R3 @ Rl
    res = (L[:, :2] @ R2.T + t2) - Wxy
    for n_, r_ in zip(notes, res):
        print(f"  {n_}: residual {np.hypot(*r_):.2f} m")
    rms = float(np.sqrt((res ** 2).sum(1).mean()))
    json.dump({"scale": float(s), "R": Rw.tolist(), "t": [float(t2[0]), float(t2[1]), tz], "cp_rms_m": rms,
               "n_cps": len(P), "z_from": "control points" if zs else "terrain base",
               "note": "cp_fit.py P0: control points (pixel ray on the component mesh <-> world corner)"},
              open(os.path.join(a.comp, "align.json"), "w"), indent=1)
    print(f"{a.comp}: {len(P)} control points, rms {rms:.2f} m, scale {s:.4f}, yaw {np.degrees(np.arctan2(R2[1, 0], R2[0, 0])):.1f}")


if __name__ == "__main__":
    sys.exit(main())
