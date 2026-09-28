# Refines an SfM -> world similarity (align.json) by trimmed point-to-surface ICP of the sparse points against the
# greybox triangles (R1 stream B, after sfm_plan_register.py): 4 DoF by default (x, y, z, yaw; scale and tilt stay
# from the levelling / tile scale), optional scale. Only points within --radius of the model are used each round and
# the worst --trim share is dropped, so trees, people and unmodelled clutter do not pull the fit.
# Model triangles: npz with V (n,3) world metres and F (m,3), e.g. exported from the .blend for the zone's box.
# Usage: python sfm_icp_refine.py --sparse gd_sfm/sparse/9 --align reg/align.json --model garden_model.npz
#          --out reg/align_icp.json [--radius 0.6,0.25] [--trim 0.3] [--scale]
import argparse
import json
import math
import sys

import numpy as np
import pycolmap
from scipy.spatial import cKDTree


def sample_surface(V, F, step):
    """Points on every triangle at ~step spacing (barycentric grid), for nearest-point queries."""
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
    n = np.maximum(1, np.ceil(area / (step * step) * 2)).astype(int)
    idx = np.repeat(np.arange(len(F)), n)
    r1, r2 = np.random.default_rng(0).random((2, len(idx)))
    s = np.sqrt(r1)
    P = (1 - s)[:, None] * A[idx] + (s * (1 - r2))[:, None] * B[idx] + (s * r2)[:, None] * C[idx]
    N = np.cross(B - A, C - A)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    return P, N[idx]


def r0_pad(a):
    return 2.0 + float(a.radius.split(",")[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sparse", required=True)
    ap.add_argument("--align", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--radius", default="0.6,0.25", help="m: inlier radius of the first and the last round")
    ap.add_argument("--trim", type=float, default=0.3, help="share of the worst inliers dropped each round")
    ap.add_argument("--rounds", type=int, default=30)
    ap.add_argument("--scale", action="store_true", help="also refine the scale")
    ap.add_argument("--step", type=float, default=0.04, help="m between surface samples")
    ap.add_argument("--above", help="z0: use only points above this world z (drop the ground, which fixes only z)")
    a = ap.parse_args()
    rec = pycolmap.Reconstruction(a.sparse)
    X = np.array([p.xyz for p in rec.points3D.values()])
    al = json.load(open(a.align))
    s, R, t = al["scale"], np.array(al["R"]), np.array(al["t"])
    if a.above:
        X = X[(s * X @ R.T + t)[:, 2] > float(a.above)]
    m = np.load(a.model)
    V, F = m["V"], m["F"]
    P0 = s * X @ R.T + t                       # only triangles near the points (memory: big facades, far objects)
    lo, hi = np.percentile(P0, 2, 0) - r0_pad(a), np.percentile(P0, 98, 0) + r0_pad(a)
    tc = V[F].mean(1)
    F = F[np.all((tc >= lo) & (tc <= hi), 1)]
    S, SN = sample_surface(V, F, a.step)
    print(f"{len(F)} model triangles near the points, {len(S)} surface samples")
    tree = cKDTree(S)
    r0, r1 = map(float, a.radius.split(","))
    # incremental transform in world: p' = k * Rz(dth) @ (p - c) + c + d
    for it in range(a.rounds):
        rad = r0 + (r1 - r0) * min(1.0, it / max(1, a.rounds // 2))
        P = s * X @ R.T + t
        dist, j = tree.query(P, distance_upper_bound=rad)
        ok = np.isfinite(dist)
        if ok.sum() < 30:
            raise SystemExit(f"round {it}: only {ok.sum()} points near the model - registration too far off")
        keep = np.nonzero(ok)[0]
        keep = keep[np.argsort(dist[keep])[: int(len(keep) * (1 - a.trim))]]
        p, q, n = P[keep], S[j[keep]], SN[j[keep]]
        c = p.mean(0)
        # linearised point-to-plane for (dx, dy, dz, dth[, dk]) about the centroid
        pc = p - c
        rows = [n[:, 0], n[:, 1], n[:, 2], n[:, 1] * pc[:, 0] - n[:, 0] * pc[:, 1]]
        if a.scale:
            rows.append((n * pc).sum(1))
        Aq = np.stack(rows, 1)
        bq = ((q - p) * n).sum(1)
        x, *_ = np.linalg.lstsq(Aq, bq, rcond=None)
        dth = x[3]
        dk = x[4] if a.scale else 0.0
        Rz = np.array([[math.cos(dth), -math.sin(dth), 0], [math.sin(dth), math.cos(dth), 0], [0, 0, 1]])
        k = 1.0 + dk
        # compose: P_new = k Rz (P - c) + c + d  with P = s R X + t
        R = Rz @ R
        s = s * k
        t = k * Rz @ (t - c) + c + x[:3]
        if it % 5 == 0 or it == a.rounds - 1:
            res = np.abs(bq)
            print(f"round {it}: radius {rad:.2f}, {len(keep)} pts, median |d| {np.median(dist[keep]):.3f} m, "
                  f"step xyz ({x[0]:+.3f},{x[1]:+.3f},{x[2]:+.3f}) yaw {math.degrees(dth):+.2f} deg"
                  + (f" scale {k:.4f}" if a.scale else ""))
    P = s * X @ R.T + t
    dist, _ = tree.query(P, distance_upper_bound=r1)
    ok = np.isfinite(dist)
    out = {"scale": float(s), "R": R.tolist(), "t": t.tolist(), "rms_m": float(np.sqrt(np.mean(dist[ok] ** 2))),
           "note": al.get("note", "") + f" | sfm_icp_refine.py: {ok.sum()} points within {r1} m, "
                   f"median {np.median(dist[ok]):.3f} m"}
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"{a.out}: {ok.sum()}/{len(P)} points within {r1} m of the model, median {np.median(dist[ok]):.3f} m")


if __name__ == "__main__":
    sys.exit(main())
