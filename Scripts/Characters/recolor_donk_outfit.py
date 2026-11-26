"""Recolours the Game Animation Sample outfit textures for Donk: orange hoodie -> charcoal, yellow sneaker parts -> off-white.
Usage: python3 recolor_donk_outfit.py <in_dir with T_Torso_BaseColor.png, T_Feet_BaseColor.png> <out_dir>.
Keeps the original shading: new colour = target * (pixel value / median value of the recoloured area)."""
import os
import sys

import numpy as np
from PIL import Image


def recolor(src, dst, target, hue_lo=12.0, hue_hi=62.0):
    rgb = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255.0
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0.0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    d = np.maximum(mx - mn, 1e-4)
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    in_hue = np.clip(1 - np.maximum(hue_lo - hue, hue - hue_hi) / 8.0, 0, 1)  # soft hue window (degrees)
    mask = (in_hue * np.clip((sat - 0.25) / 0.2, 0, 1))[..., None]              # soft saturation gate
    ref = float(np.median(mx[mask[..., 0] > 0.5])) if (mask > 0.5).any() else 1.0
    shade = np.clip(mx / ref, 0, 1.4)[..., None]
    out = rgb * (1 - mask) + np.asarray(target, np.float32) * shade * mask
    Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)).save(dst)


if __name__ == "__main__":
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    recolor(os.path.join(src_dir, "T_Torso_BaseColor.png"), os.path.join(out_dir, "T_Donk_Hoodie_D.png"), (0.055, 0.055, 0.06))
    recolor(os.path.join(src_dir, "T_Feet_BaseColor.png"), os.path.join(out_dir, "T_Donk_Sneakers_D.png"), (0.82, 0.82, 0.8))
