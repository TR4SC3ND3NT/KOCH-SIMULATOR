# Transforms an OpenMVS dense point cloud (binary PLY, SfM frame) into the campus world frame with a similarity
# (align JSON: world = scale * R @ x + t) and writes: a cropped world-frame PLY (for Blender reference import) and
# plan / section rasters in Block C local coordinates (2 cm cells) for measuring. Used by R1 zone reconstruction.
# Run: uv run --project Scripts python Scripts/Geo/dense_to_world.py dense.ply align.json out_prefix \
#        --box X0 X1 Y0 Y1 Z0 Z1   (C local metres, z rel C FFL)
import argparse
import json

import numpy as np
from PIL import Image, ImageDraw

C_ORIGIN = np.array([173.264, -3.640, 5.53])      # Block C local origin (SW corner, FFL), Specs/BLD_C.json
C_X = np.array([0.99920, -0.03985, 0.0])
C_Y = np.array([0.03985, 0.99920, 0.0])
PLY_TYPES = {"float": "f4", "float32": "f4", "double": "f8", "uchar": "u1", "uint8": "u1", "int": "i4", "uint": "u4", "uint32": "u4", "int32": "i4"}


def read_ply(path):
    """Binary little-endian PLY vertices (x, y, z, optional red/green/blue). Handles per-vertex list properties
    (OpenMVS writes view_indices / view_weights lists) with a sequential offset scan."""
    with open(path, "rb") as f:
        props, n = [], 0
        while True:
            line = f.readline().decode("ascii", "ignore").strip()
            if line.startswith("element vertex"):
                n = int(line.split()[2])
            elif line.startswith("element"):
                pass  # faces etc. after the vertices are ignored
            elif line.startswith("property") and n:
                parts = line.split()
                if parts[1] == "list":
                    props.append((parts[4], ("list", "<" + PLY_TYPES[parts[2]], "<" + PLY_TYPES[parts[3]])))
                else:
                    props.append((parts[2], "<" + PLY_TYPES[parts[1]]))
            if line == "end_header":
                break
        raw = f.read()
    if not any(isinstance(t, tuple) for _, t in props):
        data = np.frombuffer(raw, dtype=np.dtype(props), count=n)
        cols = {k: data[k] for k, _ in props}
    else:
        fixed = []
        for k, t in props:
            if isinstance(t, tuple):
                break
            fixed.append((k, t))
        fdt = np.dtype(fixed)
        lists = [t for _, t in props[len(fixed):]]
        buf = np.frombuffer(raw, np.uint8)
        offs = np.empty(n, np.int64)
        o = 0
        csz = [np.dtype(c).itemsize for _, c, _ in lists]
        isz = [np.dtype(i).itemsize for _, _, i in lists]
        for k in range(n):  # records are variable length: walk the counts
            offs[k] = o
            o += fdt.itemsize
            for cs, it in zip(csz, isz):
                cnt = int(buf[o]) if cs == 1 else int.from_bytes(buf[o:o + cs].tobytes(), "little")
                o += cs + cnt * it
        idx = offs[:, None] + np.arange(fdt.itemsize)[None, :]
        data = buf[idx].copy().view(fdt).ravel()
        cols = {k: data[k] for k, _ in fixed}
    xyz = np.stack([cols["x"], cols["y"], cols["z"]], 1).astype(np.float64)
    rgb = np.stack([cols[k] for k in ("red", "green", "blue")], 1) if "red" in cols else np.full((n, 3), 200)
    return xyz, rgb


def write_ply(path, xyz, rgb):
    hdr = ("ply\nformat binary_little_endian 1.0\nelement vertex %d\nproperty float x\nproperty float y\nproperty float z\n"
           "property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n" % len(xyz))
    arr = np.zeros(len(xyz), dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("r", "u1"), ("g", "u1"), ("b", "u1")])
    arr["x"], arr["y"], arr["z"] = xyz.T
    arr["r"], arr["g"], arr["b"] = rgb.T.astype(np.uint8)
    with open(path, "wb") as f:
        f.write(hdr.encode())
        arr.tofile(f)


def raster(q, rgb, ax, ranges, res, color_by_depth, grid):
    (a0, a1), (b0, b1) = ranges
    W, H = int((a1 - a0) / res) + 1, int((b1 - b0) / res) + 1
    img = np.full((H, W, 3), 15, np.uint8)
    u = ((q[:, ax[0]] - a0) / res).astype(int)
    v = ((b1 - q[:, ax[1]]) / res).astype(int)
    ok = (u >= 0) & (u < W) & (v >= 0) & (v < H)
    d = q[:, 3 - ax[0] - ax[1]]
    order = np.argsort(d if color_by_depth == "max" else -d)  # draw so the requested extreme ends on top
    for i in order[ok[order]]:
        img[v[i], u[i]] = rgb[i]
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    for g in np.arange(np.ceil(a0 / grid) * grid, a1, grid):
        x = (g - a0) / res
        dr.line([(x, 0), (x, H)], fill=(255, 255, 0) if abs(g % 1) < 1e-6 else (70, 70, 70))
        if abs(g % 1) < 1e-6:
            dr.text((x + 2, 2), f"{g:g}", fill=(255, 255, 0))
    for g in np.arange(np.ceil(b0 / grid) * grid, b1, grid):
        y = (b1 - g) / res
        dr.line([(0, y), (W, y)], fill=(255, 255, 0) if abs(g % 1) < 1e-6 else (70, 70, 70))
        if abs(g % 1) < 1e-6:
            dr.text((2, y + 2), f"{g:g}", fill=(255, 255, 0))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ply")
    ap.add_argument("align")
    ap.add_argument("out")
    ap.add_argument("--box", type=float, nargs=6, default=[-10, 6, -6, 8, -4, 3])
    ap.add_argument("--res", type=float, default=0.02)
    a = ap.parse_args()
    al = json.load(open(a.align))
    xyz, rgb = read_ply(a.ply)
    w = (al["scale"] * (np.array(al["R"]) @ xyz.T)).T + np.array(al["t"])
    rel = w - C_ORIGIN
    q = np.stack([rel @ C_X, rel @ C_Y, rel[:, 2]], 1)
    x0, x1, y0, y1, z0, z1 = a.box
    sel = (q[:, 0] > x0) & (q[:, 0] < x1) & (q[:, 1] > y0) & (q[:, 1] < y1) & (q[:, 2] > z0) & (q[:, 2] < z1)
    q, w, rgb = q[sel], w[sel], rgb[sel]
    write_ply(a.out + "_world.ply", w, rgb)
    # plan coloured by height (top-most point wins), plus true-colour plan and two sections
    t = np.clip((q[:, 2] - z0) / (z1 - z0), 0, 1)
    hc = np.stack([255 * t, 255 * (1 - np.abs(2 * t - 1)), 255 * (1 - t)], 1).astype(np.uint8)
    raster(q, hc, (0, 1), ((x0, x1), (y0, y1)), a.res, "max", 0.5).save(a.out + "_plan_height.png")
    raster(q, rgb, (0, 1), ((x0, x1), (y0, y1)), a.res, "max", 0.5).save(a.out + "_plan_rgb.png")
    raster(q, rgb, (0, 2), ((x0, x1), (z0, z1)), a.res, "min", 0.5).save(a.out + "_sec_from_south.png")
    raster(q, rgb, (1, 2), ((y0, y1), (z0, z1)), a.res, "max", 0.5).save(a.out + "_sec_from_west.png")
    print(f"{sel.sum()} points in the box -> {a.out}_world.ply and rasters")


if __name__ == "__main__":
    main()
