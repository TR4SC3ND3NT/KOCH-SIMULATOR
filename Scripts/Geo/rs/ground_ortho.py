# Metric scale from the paving (R1 photogrammetry, handoff 2.4 "pavers 0.20 x 0.10"): a solved, undistorted frame is
# re-projected onto the local ground plane of the model (plane fitted to the mesh under the frame) as a top view,
# and the paver lattice is read from its 2D FFT: the strongest peaks give the joint spacings in model units, so
# scale (m/unit) = paver module (m) / period (units). Works in the model frame (no world alignment needed).
# Usage: python ground_ortho.py --model model.json --mesh mesh.obj --cam NAME[,NAME2...] [--at u,v[;u,v...]]
#          [--size 0.4] [--px 0.0004] --out dir
# The module is read by a comb search over harmonics 1-4 along the strongest lattice direction and its normal; for
# 90-degree herringbone of L = 2w both directions carry joint lines every w.
#   --size: side of the ground square (model units) centred on the point seen at (0.5, 0.8) of the image height.
import argparse
import json
import os
import sys

import cv2
import numpy as np
import open3d as o3d


def cam_ray(c, uv):
    R, t = np.array(c["R"]), np.array(c["t"])
    d_cam = np.array([(uv[0] - c["cx"]) / c["f"], (uv[1] - c["cy"]) / c["fy"], 1.0])
    d = R.T @ d_cam
    return np.array(c["center"]), d / np.linalg.norm(d)


def project(c, X):
    R, t = np.array(c["R"]), np.array(c["t"])
    Y = X @ R.T + t
    return np.stack([c["f"] * Y[:, 0] / Y[:, 2] + c["cx"], c["fy"] * Y[:, 1] / Y[:, 2] + c["cy"]], 1), Y[:, 2]


def comb_period(Fp, fx, fy, theta, px, kmax=4):
    """Paver module along one lattice direction: comb search over the radial spectrum (harmonics 1..kmax)."""
    pad = Fp.shape[0]
    fr = np.linspace(1.0 / 0.6, 1.0 / 0.03, 3000)
    prof = np.zeros_like(fr)
    for dth in np.radians(np.linspace(-3, 3, 7)):
        t = theta + dth
        X = np.round(fr * np.cos(t) * pad * px + pad / 2).astype(int)
        Y = np.round(fr * np.sin(t) * pad * px + pad / 2).astype(int)
        ok = (X >= 0) & (X < pad) & (Y >= 0) & (Y < pad)
        prof[ok] += Fp[Y[ok], X[ok]]
    best = (0, None)
    for f0 in np.linspace(1.0 / 0.5, 1.0 / 0.06, 4000):
        sc = sum(np.interp(k * f0, fr, prof) for k in range(1, kmax + 1))
        if sc > best[0]:
            best = (sc, f0)
    return 1.0 / best[1]


def one(a, c, Vm, Fm_, scene, tc, fn, at):
    fu, fv = map(float, at.split(","))
    o, d = cam_ray(c, (fu * c["w"], fv * c["h"]))
    th = scene.cast_rays(o3d.core.Tensor(np.concatenate([o, d])[None].astype(np.float32)))["t_hit"].numpy()[0]
    if not np.isfinite(th):
        print(c["name"], "ray misses the mesh")
        return None
    p0 = o + d * th
    # paving plane: up-facing faces within the square and a thin height slab around the hit (steps, kerbs, walls
    # would tilt it and stretch the lattice in one direction)
    near = (np.linalg.norm(tc[:, :2] - p0[:2], axis=1) < a.size / 2) & (np.abs(tc[:, 2] - p0[2]) < a.slab) &            (np.abs(fn[:, 2]) > 0.9)
    Pn = tc[near]
    ctr = Pn.mean(0)
    _, _, vt = np.linalg.svd(Pn - ctr, full_matrices=False)
    nrm = vt[2] if vt[2] @ (o - ctr) > 0 else -vt[2]
    e1 = np.cross(nrm, [0, 0, 1.0]) if abs(nrm[2]) < 0.9 else np.cross(nrm, [1.0, 0, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(nrm, e1)
    rms = float(np.sqrt(np.mean(((Pn - ctr) @ nrm) ** 2)))
    N = int(a.size / a.px)
    us = (np.arange(N) - N / 2) * a.px
    U, V = np.meshgrid(us, us)
    X = p0 + U.reshape(-1, 1) * e1 + V.reshape(-1, 1) * e2
    X = X - np.outer((X - ctr) @ nrm, nrm)          # onto the plane
    uv, depth = project(c, X)
    img = cv2.imread(c["image"], cv2.IMREAD_GRAYSCALE)
    mapx = uv[:, 0].reshape(N, N).astype(np.float32)
    mapy = uv[:, 1].reshape(N, N).astype(np.float32)
    top = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderValue=0)
    valid = ((mapx >= 0) & (mapx < c["w"] - 1) & (mapy >= 0) & (mapy < c["h"] - 1) &
             (depth.reshape(N, N) > 0)).astype(np.float32)
    tag = os.path.basename(c["name"]).rsplit(".", 1)[0]
    cv2.imwrite(os.path.join(a.out, f"ground_{tag}.png"), top)
    # FFT: high-pass (remove shading), smooth taper inside the valid area (the edge of the image footprint would
    # otherwise give a strong streak), zero padding for sub-bin periods
    g = top.astype(np.float32)
    g = g - cv2.GaussianBlur(g, (0, 0), 25)
    taper = cv2.GaussianBlur(cv2.erode(valid, np.ones((41, 41), np.uint8)), (0, 0), 12)
    win = np.outer(np.hanning(N), np.hanning(N)).astype(np.float32) * taper
    pad = 4096
    Fp = np.abs(np.fft.fftshift(np.fft.fft2(g * win, (pad, pad))))
    fy, fx = np.meshgrid((np.arange(pad) - pad / 2) / (pad * a.px), (np.arange(pad) - pad / 2) / (pad * a.px),
                         indexing="ij")
    fr = np.hypot(fx, fy)
    Fq = np.where((fr > 1 / 0.6) & (fr < 1 / 0.03), Fp, 0)
    spec = np.log1p(Fq[pad // 2 - 512:pad // 2 + 512, pad // 2 - 512:pad // 2 + 512])
    cv2.imwrite(os.path.join(a.out, f"fft_{tag}.png"), (spec / spec.max() * 255).astype(np.uint8))
    k = int(np.argmax(Fq))
    y, x = divmod(k, pad)
    theta = float(np.arctan2(fy[y, x], fx[y, x]))
    per = [comb_period(Fp, fx, fy, t, a.px) for t in (theta, theta + np.pi / 2)]
    out = {"camera": c["name"], "plane_rms_units": rms, "px_units": a.px, "size_units": a.size,
           "valid_fraction": float(valid.mean()), "ground_point": p0.tolist(),
           "lattice_angle_deg": float(np.degrees(theta) % 180), "module_units": per}
    json.dump(out, open(os.path.join(a.out, f"ground_{tag}.json"), "w"), indent=1)
    print(f"{c['name']}: plane rms {rms:.5f}, valid {valid.mean():.2f}, lattice {np.degrees(theta) % 180:.1f} deg, "
          f"module {per[0]:.4f} / {per[1]:.4f} units")
    return per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--mesh", required=True)
    ap.add_argument("--cam", required=True, help="camera name substring(s), comma separated")
    ap.add_argument("--at", default="0.5,0.8", help="image point (fractions) the ground square is centred on; "
                    "one per camera separated by ';' or one for all")
    ap.add_argument("--size", type=float, default=0.4)
    ap.add_argument("--px", type=float, default=0.0004)
    ap.add_argument("--slab", type=float, default=0.05, help="height band (units) around the hit for the plane fit")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    m = json.load(open(a.model))
    # Open3D's C++ OBJ reader: minutes instead of the half hour trimesh takes on a 1 GB high-detail export
    tm = o3d.io.read_triangle_mesh(a.mesh, enable_post_processing=False)
    Vm, Fm_ = np.asarray(tm.vertices), np.asarray(tm.triangles)
    scene = o3d.t.geometry.RaycastingScene()   # Embree: fast on multi-million-triangle meshes
    scene.add_triangles(o3d.core.Tensor(Vm.astype(np.float32)), o3d.core.Tensor(Fm_.astype(np.uint32)))
    T = Vm[Fm_]
    tc = T.mean(1)
    fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    del T
    cams = a.cam.split(",")
    ats = a.at.split(";")
    mods = []
    for i, name in enumerate(cams):
        c = next(x for x in m["cameras"] if name in x["name"])
        r = one(a, c, Vm, Fm_, scene, tc, fn, ats[i] if len(ats) > 1 else ats[0])
        if r:
            mods += r
    if mods:
        print(f"module median {np.median(mods):.4f} units over {len(mods)} readings; "
              f"scale for a 0.10 m paver width: {0.10 / np.median(mods):.4f} m/unit")


if __name__ == "__main__":
    sys.exit(main())
