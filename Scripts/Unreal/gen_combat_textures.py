# Generates the decal source textures for combat (R3): blood splatters, blood pool, entry wound, bullet hole.
# Procedural and seeded, so the PNGs are reproducible and carry no third-party licence. Imported by setup_combat.py.
# Each decal is two files: <name>_M.png (R = thickness/darkness, G = dust ring (bullet hole only), A = opacity) and
# <name>_N.png (tangent-space normal, DirectX green).
# Run (any Python with numpy, e.g. Blender's): python gen_combat_textures.py <output dir>
import os
import struct
import sys
import zlib

import numpy as np

TAU = 2.0 * np.pi


def write_png(path, rgba):
    """rgba: uint8 array H x W x 4."""
    h, w, _ = rgba.shape
    raw = b"".join(b"\x00" + rgba[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def fbm(n, rng, octaves=5, base=4):
    """Value noise in 0..1, n x n."""
    out = np.zeros((n, n), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        g = base * 2 ** o
        r = rng.random((g + 1, g + 1), dtype=np.float32)
        xs = np.linspace(0, g, n, endpoint=False)
        xi = xs.astype(int)
        xf = (xs - xi).astype(np.float32)
        xf = xf * xf * (3.0 - 2.0 * xf)
        fx, fy = xf[None, :], xf[:, None]
        a, b = r[np.ix_(xi, xi)], r[np.ix_(xi, xi + 1)]
        c, d = r[np.ix_(xi + 1, xi)], r[np.ix_(xi + 1, xi + 1)]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
        total += amp
        amp *= 0.5
    return out / total


def stamp(field, cx, cy, rx, ry, angle, strength):
    """Adds an elongated Gaussian blob (radii rx along angle, ry across) to field."""
    n = field.shape[0]
    reach = int(3 * max(rx, ry)) + 2
    x0, x1 = max(0, int(cx) - reach), min(n, int(cx) + reach + 1)
    y0, y1 = max(0, int(cy) - reach), min(n, int(cy) + reach + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    c, s = np.cos(angle), np.sin(angle)
    u, v = (dx * c + dy * s) / rx, (-dx * s + dy * c) / ry
    field[y0:y1, x0:x1] += strength * np.exp(-(u * u + v * v))


def radial(n):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = xx - n / 2 + 0.5, yy - n / 2 + 0.5
    return np.sqrt(dx * dx + dy * dy) / (n / 2), np.arctan2(dy, dx)


def border_fade(n):
    """0 at the texture edge, so the decal box never shows a cut."""
    dist, _ = radial(n)
    return 1.0 - smoothstep(0.90, 0.99, dist)


def normal_from_height(height, strength):
    gy, gx = np.gradient(height.astype(np.float32))
    nx, ny, nz = -gx * strength, gy * strength, np.ones_like(height, np.float32)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    rgb = np.stack([nx / length, ny / length, nz / length], -1) * 0.5 + 0.5
    return np.concatenate([rgb, np.ones(height.shape + (1,), np.float32)], -1)


def save(out_dir, name, mask_rgba, height, normal_strength):
    to8 = lambda a: (np.clip(a, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    write_png(os.path.join(out_dir, f"{name}_M.png"), to8(mask_rgba))
    write_png(os.path.join(out_dir, f"{name}_N.png"), to8(normal_from_height(height, normal_strength)))
    print("wrote", name)


def blood_splat(n, seed, core=1.0, spray=1.0):
    """Impact splatter: a wet core, rays of stretched droplets, fine mist. core/spray scale the two parts."""
    rng = np.random.default_rng(seed)
    f = np.zeros((n, n), np.float32)
    c = n / 2
    for _ in range(int(rng.integers(5, 9) * core) + 1):
        a, d = rng.uniform(0, TAU), rng.uniform(0, 0.09) * n * core
        stamp(f, c + np.cos(a) * d, c + np.sin(a) * d, rng.uniform(0.045, 0.10) * n * core, rng.uniform(0.045, 0.10) * n * core,
              rng.uniform(0, np.pi), rng.uniform(0.8, 1.4))
    for _ in range(int(rng.integers(14, 26) * spray)):
        a, length, count = rng.uniform(0, TAU), rng.uniform(0.15, 0.44) * n, rng.integers(3, 9)
        for j in range(count):
            t = (j + 1) / count
            d = length * t * rng.uniform(0.85, 1.1)
            r = n * rng.uniform(0.006, 0.02) * (1.15 - t)
            stamp(f, c + np.cos(a) * d, c + np.sin(a) * d, r * rng.uniform(1.5, 3.5), r, a, rng.uniform(0.9, 1.6))
    for _ in range(int(260 * spray)):
        a, d, r = rng.uniform(0, TAU), abs(rng.normal(0, 0.19)) * n, n * rng.uniform(0.002, 0.007)
        stamp(f, c + np.cos(a) * d, c + np.sin(a) * d, r, r, 0.0, rng.uniform(0.7, 1.5))

    edge = f + (fbm(n, rng, 5, 6) - 0.5) * 0.35
    alpha = smoothstep(0.42, 0.60, edge) * border_fade(n)
    thick = smoothstep(0.6, 1.7, f)
    return np.stack([thick, np.zeros_like(f), np.zeros_like(f), alpha], -1), np.minimum(f, 2.0) * alpha


def blood_pool(n, seed):
    """Pool under a body: one irregular lobe-edged puddle, thick in the middle."""
    rng = np.random.default_rng(seed)
    dist, angle = radial(n)
    lobes = sum(rng.uniform(0.02, 0.07) * np.cos(angle * k + rng.uniform(0, TAU)) for k in (2, 3, 5, 8))
    v = 0.74 + lobes - dist + (fbm(n, rng, 4, 3) - 0.5) * 0.30
    alpha = smoothstep(0.0, 0.035, v) * border_fade(n)
    thick = smoothstep(0.0, 0.45, v)
    return np.stack([thick, np.zeros_like(v), np.zeros_like(v), alpha], -1), smoothstep(0.0, 0.08, v)


def bullet_hole(n, seed):
    """Hole in masonry: dark irregular core, a chipped ring of pale dust, a few hairline cracks."""
    rng = np.random.default_rng(seed)
    dist, angle = radial(n)
    core = 1.0 - smoothstep(0.13, 0.19, dist + (fbm(n, rng, 4, 8) - 0.5) * 0.14)
    ring = 1.0 - smoothstep(0.30, 0.44, dist + (fbm(n, rng, 5, 5) - 0.5) * 0.45)
    cracks = np.zeros_like(dist)
    for _ in range(rng.integers(3, 6)):
        a, length = rng.uniform(0, TAU), rng.uniform(0.35, 0.8)
        delta = np.abs(np.arctan2(np.sin(angle - a), np.cos(angle - a))) * dist
        cracks = np.maximum(cracks, np.exp(-(delta / 0.012) ** 2) * (1.0 - smoothstep(length * 0.6, length, dist)))
    alpha = np.maximum(np.maximum(core, ring * 0.9), cracks * 0.7) * border_fade(n)
    dark = np.maximum(core, cracks * 0.8)
    height = -(core * 1.0 + ring * 0.25 + cracks * 0.3)
    return np.stack([dark, ring * (1.0 - core), np.zeros_like(dist), alpha], -1), height


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for i, seed in enumerate((11, 23, 37, 58), 1):
        save(out_dir, f"T_BloodSplat_{i:02d}", *blood_splat(512, seed), 6.0)
    for i, seed in enumerate((5, 19), 1):
        save(out_dir, f"T_BloodPool_{i:02d}", *blood_pool(512, seed), 10.0)
    save(out_dir, "T_BloodWound_01", *blood_splat(128, 71, core=1.6, spray=0.25), 4.0)
    for i, seed in enumerate((3, 14, 29), 1):
        save(out_dir, f"T_BulletHole_{i:02d}", *bullet_hole(256, seed), 8.0)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "combat_textures")
