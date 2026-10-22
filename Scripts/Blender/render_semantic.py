# Photo-vs-model diff renders for R1 bug hunts: from one camera, writes a flat class map (grass, paving, kerb, road,
# wall, roof, vegetation, ...), an object-ID map and a shaded view, plus legend.json (colour -> class, id -> object).
# A disagreement blob in the class map is traced back to its object (and spec element) through the ID map.
# Run (does not save the .blend):
#   blender -b model.blend -P Scripts/Blender/render_semantic.py -- --cam CAM.json | --look PX PY PZ TX TY TZ LENS
#       --size W H --out OUT_PREFIX
# CAM.json: Scripts/Geo/photo_pnp.py output (COLMAP-style R, t, f, w, h; world frame), first camera used.
# Outputs OUT_PREFIX_class.png, _id.png, _shaded.png (RGBA, sky transparent), _legend.json. Units: metres.
import argparse
import json
import math
import re
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

# class -> sRGB colour (8-bit). Kept far apart so 8-bit PNG round-trips exactly (no AA, flat light, Standard view).
CLASSES = {
    "grass": (60, 180, 75), "soil": (140, 90, 40), "paving": (200, 200, 200), "road": (70, 70, 80),
    "kerb": (255, 225, 25), "stairs": (245, 130, 48), "wall": (230, 25, 75), "roof": (145, 30, 180),
    "window": (70, 240, 240), "door": (240, 50, 230), "vegetation": (0, 100, 0), "metal": (0, 0, 128),
    "sign": (255, 250, 200), "water": (0, 130, 200), "other": (128, 128, 0), "terrain_other": (170, 255, 195),
}
# object-name overrides first (the element decides: a precast kerb and a precast coping share a material)
# tested on "_<element part>_" (spec/building prefix stripped: SITE_Gate's own prefix is not a gate); a word starts at
# "_" or at a CamelCase capital ("PavilionStair", "RampRail"). Order matters: the first match wins.
B = r"(?:_|(?<=[a-z0-9]))"
NAME_RULES = [
    (B + r"(Wall|Cheek|Parapet|Plinth|Pier|Column|Pilaster)(?=[A-Z_0-9])", "wall"),
    (B + r"(Stair|Steps|Step|Flight|Riser|Tread|Landing)(?!Rail)", "stairs"),
    (B + r"(Kerb|Curb|Edging|Coping|Border)|_Paint(Yellow|White)_|NosePaint", "kerb"),
    (B + r"(Roof|Canopy|Awning)", "roof"),
    (B + r"(Rail|Handrail|Fence(?!Plinth)|Bollard|Barrier|Cage|Net|Turnstile|Gate)(?=[A-Z_0-9])", "metal"),
    (B + r"(Door|Leaf)", "door"),
    (B + r"(Win|Window|Glazing|Glass)(?=[A-Z_0-9])", "window"),
    (B + r"(Sign|Poster|Plaque)", "sign"),
]
MAT_RULES = [
    (r"Grass|Lawn", "grass"), (r"Soil|Mulch|Dirt|Sand", "soil"), (r"Asphalt|Road_Paint", "road"),
    (r"Paver|Paving|Gravel|Terrazzo|Granite", "paving"), (r"Kerb", "kerb"), (r"Tree|Hedge|Foliage", "vegetation"),
    (r"Sheet|Shingle|Roof_Membrane", "roof"), (r"Glass|Mirror", "window"),
    (r"Render|Brick|Block|Context_Facade|Fascia|Tile_Wall|Paint_Maroon", "wall"),
    (r"Steel|Alu|Chrome|Fence", "metal"), (r"Sign", "sign"), (r"Concrete", "paving"),
]
OUT = {}


def element_part(name):
    """GBS_<spec>_<element...> -> _<element...>_ ; GBF_BLD_<bld>_<part...> -> _<part...>_ (rules see only these)."""
    t = name.split("_")
    k = 3 if name.startswith("GBF_BLD_") else 2 if name.startswith(("GBS_", "GBF_", "GB_")) else 0
    return "_" + "_".join(t[k:]) + "_"


def classify(ob, mat):
    n = ob.name
    el = element_part(n)
    for pat, c in NAME_RULES:
        if re.search(pat, el):
            return c
    m = mat.name if mat else ""
    for pat, c in MAT_RULES:
        if re.search(pat, m):
            return "terrain_other" if (n.startswith("TER_") and c not in ("grass", "soil", "paving", "road")) else c
    return "other"


def srgb_to_lin(c8):
    c = c8 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def flat_scene(w, h, mode):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.film_transparent = True
    sc.render.dither_intensity = 0.0
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure, sc.view_settings.gamma = 0.0, 1.0
    sc.display.render_aa = "OFF"   # exact colours: every pixel is one class / one object
    sh = sc.display.shading
    sh.light, sh.color_type = "FLAT", mode
    sh.show_shadows = sh.show_cavity = sh.show_specular_highlight = sh.show_object_outline = False
    sh.show_xray = False


def shaded_scene():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.render_aa = "8"
    sc.view_settings.view_transform = "Standard"
    sh = sc.display.shading
    sh.light, sh.color_type = "STUDIO", "MATERIAL"
    sh.show_shadows, sh.show_cavity = False, True   # no cast shadows: they read as surface changes (2026-10-22)


def set_camera(args):
    cam = bpy.data.objects.new("TMP_SemCam", bpy.data.cameras.new("TMP_SemCam"))
    bpy.context.scene.collection.objects.link(cam)
    cd = cam.data
    cd.clip_start, cd.clip_end = 0.05, 3000
    if args.cam:
        c = json.load(open(args.cam))["cameras"][0]
        w, h = int(c["w"]), int(c["h"])
        big = max(w, h)
        cd.sensor_fit = "HORIZONTAL" if w >= h else "VERTICAL"
        cd.sensor_width = cd.sensor_height = 36.0
        cd.lens = c["f"] * 36.0 / big
        cd.shift_x = (w / 2 - c.get("cx", w / 2)) / big
        cd.shift_y = (c.get("cy", h / 2) - h / 2) / big
        R = np.array(c["R"])
        rot = R.T @ np.diag([1.0, -1.0, -1.0])   # COLMAP camera axes (+Z forward, +Y down) -> Blender (-Z forward, +Y up)
        m = Matrix.Identity(4)
        for i in range(3):
            for j in range(3):
                m[i][j] = rot[i, j]
            m[i][3] = c["center"][i]
        cam.matrix_world = m
        if args.size:
            w, h = args.size
    else:
        px, py, pz, tx, ty, tz, lens = args.look
        pos, tgt = Vector((px, py, pz)), Vector((tx, ty, tz))
        cam.location = pos
        cam.rotation_euler = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
        cd.lens, cd.sensor_width = lens, 36.0
        w, h = args.size or (1400, 1000)
    bpy.context.scene.camera = cam
    return w, h


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam")
    ap.add_argument("--look", type=float, nargs=7)
    ap.add_argument("--size", type=int, nargs=2)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render]
    for o in bpy.data.objects:
        if o.name.startswith(("REF_", "CAM_")) and o.type == "MESH":
            o.hide_render = True
    w, h = set_camera(args)
    shaded_scene()
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = w, h
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.film_transparent = True
    render(args.out + "_shaded.png")
    # object-ID pass: id k (1-based) -> sRGB (k // 256, k % 256, 77); B is a fixed tag so id 0 = sky stays distinct
    flat_scene(w, h, "OBJECT")
    ids = {}
    for k, o in enumerate(sorted((o for o in meshes if not o.name.startswith(("REF_", "CAM_"))), key=lambda o: o.name), 1):
        ids[k] = o.name
        o.color = (srgb_to_lin(k // 256), srgb_to_lin(k % 256), srgb_to_lin(77), 1.0)
    render(args.out + "_id.png")
    # class pass: each slot gets its class material (temporary; the file is never saved)
    flat_scene(w, h, "MATERIAL")
    cls_mat = {}
    for name, rgb in CLASSES.items():
        m = bpy.data.materials.new("CLS_" + name)
        m.diffuse_color = tuple(srgb_to_lin(v) for v in rgb) + (1.0,)
        cls_mat[name] = m
    per_obj = {}
    for o in meshes:
        if o.name.startswith(("REF_", "CAM_")):
            continue
        cs = []
        if not o.material_slots:
            o.data.materials.append(cls_mat[classify(o, None)])
            cs.append(classify(o, None))
        for s in o.material_slots:
            c = classify(o, s.material)
            cs.append(c)
            s.link = "OBJECT"   # per object: shared meshes keep their own class
            s.material = cls_mat[c]
        per_obj[o.name] = sorted(set(cs))
    render(args.out + "_class.png")
    json.dump({"size": [w, h], "classes": CLASSES, "ids": ids, "object_classes": per_obj,
               "id_decode": "id = R*256 + G where B == 77; alpha 0 = sky/no model"},
              open(args.out + "_legend.json", "w"), indent=0)
    print("semantic renders:", args.out)


if __name__ == "__main__":
    main()
