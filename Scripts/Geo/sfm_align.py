# Aligns a zone SfM model (sfm_zone.py model.json) to the campus frame, for R1 zone reconstruction.
# Correspondences: a feature picked in >= 2 undistorted frames (pixels) is triangulated in the model and paired with its
# world position (from the existing greybox / measurements). A similarity (scale, rotation, translation) is fitted
# (Umeyama 1991, "Least-squares estimation of transformation parameters between two point patterns").
# Run: uv run --project Scripts python Scripts/Geo/sfm_align.py model.json pairs.json align.json
# pairs.json: {"pairs": [{"name": "C_SW_corner_base", "obs": [["v00_x/0012.jpg", u, v], ...], "world": [x, y, z]}, ...],
#              "fix_up": true}   # fix_up: keep world Z vertical by solving rotation about Z only (needs >= 2 pairs + gravity)
import json
import sys

import numpy as np


def proj_matrix(c):
    K = np.array([[c["f"], 0, c["cx"]], [0, c.get("fy", c["f"]), c["cy"]], [0, 0, 1.0]])
    return K @ np.column_stack([np.array(c["R"]), np.array(c["t"])])


def triangulate(cams, obs):
    """Linear (DLT) triangulation of one point from [(cam_name, u, v), ...]; returns (X, mean reprojection px)."""
    rows = []
    for name, u, v in obs:
        P = proj_matrix(cams[name])
        rows += [u * P[2] - P[0], v * P[2] - P[1]]
    X = np.linalg.svd(np.array(rows))[2][-1]
    X = X[:3] / X[3]
    err = []
    for name, u, v in obs:
        x = proj_matrix(cams[name]) @ np.append(X, 1)
        err.append(np.hypot(x[0] / x[2] - u, x[1] / x[2] - v))
    return X, float(np.mean(err))


def umeyama(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    S, D = src - mu_s, dst - mu_d
    U, sig, Vt = np.linalg.svd(D.T @ S / len(src))
    E = np.eye(3)
    if np.linalg.det(U @ Vt) < 0:
        E[2, 2] = -1
    R = U @ E @ Vt
    s = np.trace(np.diag(sig) @ E) / (S ** 2).sum(1).mean()
    return s, R, mu_d - s * R @ mu_s


def gravity(model):
    """Model 'up' from camera y axes (hand-held frames are near level): mean of -row1 of R."""
    ups = np.array([-np.array(c["R"])[1] for c in model["cameras"]])
    u = ups.mean(0)
    return u / np.linalg.norm(u)


def main():
    model = json.load(open(sys.argv[1]))
    cams = {c["name"]: c for c in model["cameras"]}
    spec = json.load(open(sys.argv[2]))
    src, dst = [], []
    for p in spec["pairs"]:
        X, e = triangulate(cams, p["obs"])
        print(f"{p['name']:24s} model {np.round(X, 3)}  reproj {e:.1f} px")
        src.append(X)
        dst.append(p["world"])
    src, dst = np.array(src), np.array(dst, float)
    if spec.get("fix_up") or len(src) < 3:
        # Rotate model 'up' onto world +Z first, then fit scale + yaw + translation in the horizontal plane.
        g = gravity(model)
        z = np.array([0, 0, 1.0])
        v, c = np.cross(g, z), g @ z
        Vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R0 = np.eye(3) + Vx + Vx @ Vx / (1 + c)
        s2 = (R0 @ src.T).T
        a, b = s2[:, :2] - s2[:, :2].mean(0), dst[:, :2] - dst[:, :2].mean(0)
        H = a.T @ b
        yaw = np.arctan2(H[0, 1] - H[1, 0], H[0, 0] + H[1, 1])
        Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
        R = Rz @ R0
        r = (R @ src.T).T
        s = np.sqrt(((dst - dst.mean(0)) ** 2).sum() / ((r - r.mean(0)) ** 2).sum()) if len(src) > 1 else 1.0
        t = dst.mean(0) - s * r.mean(0)
    else:
        s, R, t = umeyama(src, dst)
    res = np.linalg.norm((s * (R @ src.T)).T + t - dst, axis=1)
    for p, e in zip(spec["pairs"], res):
        print(f"  residual {p['name']:24s} {e:.3f} m")
    json.dump({"scale": float(s), "R": R.tolist(), "t": t.tolist(), "rms_m": float(np.sqrt((res ** 2).mean())),
               "pairs": [p["name"] for p in spec["pairs"]]}, open(sys.argv[3], "w"), indent=1)
    print(f"scale {s:.4f} m/unit, rms {np.sqrt((res ** 2).mean()):.3f} m -> {sys.argv[3]}")


if __name__ == "__main__":
    main()
