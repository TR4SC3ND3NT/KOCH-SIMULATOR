# CPU "render" of the greybox for the R1 photo-vs-model bug hunt: casts one ray per pixel through a pinhole camera
# into the triangles exported by Scripts/Blender/export_tris.py (Open3D RaycastingScene), giving per-pixel class,
# object, material, distance and world xyz, plus a shaded view and the model's edges for overlays on the photo.
# No Blender needed: ~1-3 s per 1000 px frame. Units: metres, world frame (x east, y north, z up).
# Camera: --cam CAM.json (Scripts/Geo/photo_pnp.py output: OpenCV x_cam = R X + t, f/cx/cy in its w x h pixels) or
#   --look PX PY PZ TX TY TZ LENS_MM (36 mm on the long side, like render_view.py). --size W H sets the output size.
# Run: python Scripts/Geo/model_raycast.py MODEL.npz --cam cam.json --size 768 1020 --out PREFIX [--photo P.jpg]
# Writes PREFIX_class.png, PREFIX_shaded.png, PREFIX_ray.npz (oid, cls, mat, dist, xyz as float32), and with --photo
# PREFIX_overlay.jpg (photo with the model's class edges drawn on it) and PREFIX_blend.jpg (50 % blend).
# Import use: from model_raycast import Model; m = Model(npz); r = m.cast(K, Rt, w, h).
import argparse
import json

import numpy as np
import open3d as o3d
from PIL import Image, ImageOps


class Model:
    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.cls, self.oid, self.mat = z["cls"], z["oid"], z["mat"]
        self.names, self.mats, self.classes, self.colours = z["names"], z["mats"], z["classes"], z["colours"]
        self.scene = o3d.t.geometry.RaycastingScene()
        mesh = o3d.t.geometry.TriangleMesh()
        mesh.vertex.positions = o3d.core.Tensor(z["V"].astype(np.float32))
        mesh.triangle.indices = o3d.core.Tensor(z["F"].astype(np.int32))
        self.scene.add_triangles(mesh)

    def cast(self, K, Rt, w, h):
        """K 3x3 pixel intrinsics, Rt 3x4 world->camera (OpenCV). Returns dict of HxW arrays (-1 / nan = sky)."""
        E = np.eye(4)
        E[:3] = Rt
        rays = o3d.t.geometry.RaycastingScene.create_rays_pinhole(
            o3d.core.Tensor(K, dtype=o3d.core.Dtype.Float64), o3d.core.Tensor(E, dtype=o3d.core.Dtype.Float64), w, h)
        ans = self.scene.cast_rays(rays)
        t = ans["t_hit"].numpy()
        prim = ans["primitive_ids"].numpy().astype(np.int64)
        hit = np.isfinite(t)
        prim[~hit] = 0
        r = rays.numpy()
        xyz = r[..., :3] + r[..., 3:] * np.where(hit, t, 0)[..., None]
        nrm = ans["primitive_normals"].numpy()
        return {"hit": hit, "dist": np.where(hit, t * np.linalg.norm(r[..., 3:], axis=-1), np.nan).astype(np.float32),
                "cls": np.where(hit, self.cls[prim].astype(np.int16), -1), "oid": np.where(hit, self.oid[prim], -1),
                "mat": np.where(hit, self.mat[prim].astype(np.int32), -1), "xyz": xyz.astype(np.float32),
                "nrm": nrm.astype(np.float32), "ray_d": r[..., 3:].astype(np.float32)}

    def class_image(self, r):
        img = np.zeros(r["cls"].shape + (3,), np.uint8)
        img[r["hit"]] = self.colours[r["cls"][r["hit"]]]
        return img

    def shaded_image(self, r):
        """Headlight Lambert on the class colours: shows shape without cast shadows (they read as surfaces)."""
        d = r["ray_d"] / np.maximum(np.linalg.norm(r["ray_d"], axis=-1, keepdims=True), 1e-9)
        lam = np.abs((r["nrm"] * d).sum(-1))
        img = self.class_image(r).astype(np.float32) * (0.35 + 0.65 * lam[..., None])
        img[~r["hit"]] = (40, 40, 40)
        return img.clip(0, 255).astype(np.uint8)


def edges(r):
    """Model edge mask: class or object changes between neighbours, and depth jumps > 5 %."""
    e = np.zeros(r["cls"].shape, bool)
    for a in ("cls", "oid"):
        v = r[a]
        e[:, 1:] |= v[:, 1:] != v[:, :-1]
        e[1:, :] |= v[1:, :] != v[:-1, :]
    d = np.nan_to_num(r["dist"], nan=1e4)
    e[:, 1:] |= np.abs(d[:, 1:] - d[:, :-1]) > 0.05 * np.minimum(d[:, 1:], d[:, :-1])
    e[1:, :] |= np.abs(d[1:, :] - d[:-1, :]) > 0.05 * np.minimum(d[1:, :], d[:-1, :])
    return e


def camera_from_args(a):
    """K, Rt, w, h at the output size."""
    if a.cam:
        c = json.load(open(a.cam))["cameras"][0]
        W0, H0 = c["w"], c["h"]
        w, h = a.size or (W0, H0)
        s = w / W0
        K = np.array([[c["f"] * s, 0, c.get("cx", W0 / 2) * s], [0, c.get("fy", c["f"]) * s, c.get("cy", H0 / 2) * s],
                      [0, 0, 1]])
        Rt = np.hstack([np.array(c["R"]), np.array(c["t"]).reshape(3, 1)])
        return K, Rt, w, h
    px, py, pz, tx, ty, tz, lens = a.look
    w, h = a.size or (1400, 1000)
    f = lens / 36.0 * max(w, h)
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]])
    pos, d = np.array([px, py, pz]), np.array([tx - px, ty - py, tz - pz])
    d /= np.linalg.norm(d)
    rgt = np.cross(d, [0, 0, 1.0])
    rgt /= np.linalg.norm(rgt)
    dn = np.cross(d, rgt)
    R = np.vstack([rgt, dn, d])
    return K, np.hstack([R, (-R @ pos).reshape(3, 1)]), w, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--cam")
    ap.add_argument("--look", type=float, nargs=7)
    ap.add_argument("--size", type=int, nargs=2)
    ap.add_argument("--out", required=True)
    ap.add_argument("--photo")
    a = ap.parse_args()
    m = Model(a.model)
    K, Rt, w, h = camera_from_args(a)
    r = m.cast(K, Rt, w, h)
    Image.fromarray(m.class_image(r)).save(a.out + "_class.png")
    Image.fromarray(m.shaded_image(r)).save(a.out + "_shaded.png")
    np.savez_compressed(a.out + "_ray.npz", oid=r["oid"], cls=r["cls"], mat=r["mat"], dist=r["dist"], xyz=r["xyz"],
                        K=K, Rt=Rt)
    if a.photo:
        ph = np.asarray(ImageOps.exif_transpose(Image.open(a.photo)).convert("RGB").resize((w, h), Image.BICUBIC))
        ov = ph.copy()
        e = edges(r)
        ov[e] = (255, 0, 255)
        Image.fromarray(ov).save(a.out + "_overlay.jpg", quality=88)
        Image.fromarray((0.5 * ph + 0.5 * m.class_image(r)).astype(np.uint8)).save(a.out + "_blend.jpg", quality=88)
    print("raycast:", a.out, f"{r['hit'].mean() * 100:.0f}% hit")


if __name__ == "__main__":
    main()
