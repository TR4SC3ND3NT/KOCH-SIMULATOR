# Plan check of the greybox against the satellite orthophoto (R1 pass P0/P1 plan test): renders a top-down orthographic
# Workbench view of a world box (object colours, transparent background) and blends it over the matching crop of the
# local ortho (alatoo-capture/data/ortho/*.png + .json: extent_local, m_per_px), with the model's silhouette edges in
# magenta and a 5 m grid. Read-only (never saves the .blend). Ortho imagery is a local tracing reference: never commit
# the output images.
# Usage: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/plan_overlay.py -- \
#          --box x0,y0,x1,y1 --ortho ~/alatoo-capture/data/ortho/ortho_google_z20 --out plan.png [--px 0.05]
#          [--zmax 30] [--hide REF_,CTX_,TER_]
import argparse
import json
import os
import re
import sys

import bpy
import numpy as np


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--box", required=True)
    ap.add_argument("--ortho", required=True, help="ortho basename without extension (.png + .json)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--px", type=float, default=0.05, help="m per output pixel")
    ap.add_argument("--zmax", type=float, default=40.0, help="camera height (m, world z); objects above are clipped")
    ap.add_argument("--hide", default="REF_,CTX_,TER_", help="name prefixes left out of the render")
    ap.add_argument("--only", help="regex: render only objects whose name matches (e.g. the walkable paths)")
    ap.add_argument("--zband", help="z0,z1 world metres: render only geometry between these heights (a horizontal "
                    "slab section) and also write <out>.mask.png + .json for Scripts/Geo/rs/sfm_plan_register.py")
    a = ap.parse_args(argv)
    x0, y0, x1, y1 = map(float, a.box.split(","))
    W, H = int(round((x1 - x0) / a.px)), int(round((y1 - y0) / a.px))

    sc = bpy.context.scene
    hide = tuple(p for p in a.hide.split(",") if p)
    only = re.compile(a.only) if a.only else None
    for ob in sc.objects:
        if ob.name.startswith(hide) or (only and not only.search(ob.name)):
            ob.hide_render = True
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sh = sc.display.shading
    sh.light, sh.color_type, sh.show_shadows, sh.show_cavity = "FLAT", "OBJECT", False, False
    cam = bpy.data.objects.new("TMP_PlanCam", bpy.data.cameras.new("TMP_PlanCam"))
    sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(x1 - x0, y1 - y0)
    cam.data.sensor_fit = "HORIZONTAL" if W >= H else "VERTICAL"
    if a.zband:
        zb0, zb1 = map(float, a.zband.split(","))
        cam.data.clip_start, cam.data.clip_end = 0.001, zb1 - zb0
        cam.location = ((x0 + x1) / 2, (y0 + y1) / 2, zb1)
    else:
        cam.data.clip_start, cam.data.clip_end = 0.1, a.zmax + 50.0
        cam.location = ((x0 + x1) / 2, (y0 + y1) / 2, a.zmax)
    cam.rotation_euler = (0.0, 0.0, 0.0)          # looking straight down, +Y up in the image
    sc.camera = cam
    tmp = a.out + ".model.png"
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)

    if a.zband:
        mask = (load_rgba(tmp)[:, :, 3] > 0.5).astype(np.float32)
        save_rgb(np.repeat(mask[:, :, None], 3, 2), a.out + ".mask.png")
        json.dump({"box": [x0, y0, x1, y1], "px": a.px, "zband": a.zband}, open(a.out + ".mask.json", "w"))
    meta = json.load(open(a.ortho + ".json"))
    ex, mpp = meta["extent_local"], meta["m_per_px"]
    mod = load_rgba(tmp)                                   # (H, W, 4), top row first
    ortho = load_rgba(a.ortho + ".png")
    # nearest-neighbour resample of the ortho crop onto the output grid
    xs = x0 + (np.arange(W) + 0.5) * a.px
    ys = y1 - (np.arange(H) + 0.5) * a.px
    ci = np.clip(((xs - ex[0]) / mpp).astype(int), 0, ortho.shape[1] - 1)
    ri = np.clip(((ex[3] - ys) / mpp).astype(int), 0, ortho.shape[0] - 1)
    crop = ortho[ri][:, ci, :3]
    al = mod[:, :, 3:4] * 0.45
    out = crop * (1 - al) + mod[:, :, :3] * al
    m = mod[:, :, 3] > 0.5
    lum = mod[:, :, :3].mean(2)
    e = np.zeros_like(m)
    e[1:, :] |= m[1:, :] != m[:-1, :]
    e[:, 1:] |= m[:, 1:] != m[:, :-1]
    e[1:, :] |= m[1:, :] & m[:-1, :] & (np.abs(lum[1:, :] - lum[:-1, :]) > 0.06)
    e[:, 1:] |= m[:, 1:] & m[:, :-1] & (np.abs(lum[:, 1:] - lum[:, :-1]) > 0.06)
    out[e] = (1.0, 0.0, 1.0)
    for gx in np.arange(np.ceil(x0 / 5) * 5, x1, 5):     # 5 m grid, 10 m lines brighter
        c = int((gx - x0) / a.px)
        if not 0 <= c < W:
            continue
        out[:, c] = out[:, c] * 0.4 + (0.6 if gx % 10 == 0 else 0.3)
    for gy in np.arange(np.ceil(y0 / 5) * 5, y1, 5):
        r = int((y1 - gy) / a.px)
        if not 0 <= r < H:
            continue
        out[r, :] = out[r, :] * 0.4 + (0.6 if gy % 10 == 0 else 0.3)
    save_rgb(out, a.out)
    os.remove(tmp)
    print(f"{a.out}: {W}x{H} px, {a.px} m/px, box {a.box}; grid 5 m (bright = multiples of 10 m), "
          f"top-left = ({x0}, {y1})")


def load_rgba(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[::-1]          # Blender stores the bottom row first


def save_rgb(rgb, path):
    h, w = rgb.shape[:2]
    img = bpy.data.images.new("TMP_PlanOut", w, h, alpha=False)
    buf = np.ones((h, w, 4), np.float32)
    buf[:, :, :3] = np.clip(rgb, 0, 1)
    img.pixels.foreach_set(buf[::-1].ravel())
    img.filepath_raw, img.file_format = path, "PNG"
    img.save()
    bpy.data.images.remove(img)

main()
