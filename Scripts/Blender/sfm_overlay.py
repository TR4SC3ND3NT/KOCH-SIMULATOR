# Zone verification for R1: renders the greybox through aligned SfM cameras and blends each render over its
# undistorted frame (writes <out>/ovl_<frame>.jpg). Optionally links the aligned sparse cloud as a reference mesh.
# Run headless (does NOT save the .blend unless KOCH_SFM_SAVE=1):
#   KOCH_SFM_MODEL=model.json KOCH_SFM_ALIGN=align.json KOCH_SFM_OUT=/scratch/ovl KOCH_SFM_CAMS=every:10 \
#   blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/sfm_overlay.py
# KOCH_SFM_CAMS: "every:N" or comma list of frame names; KOCH_SFM_CLOUD=1 links REF_SfM_<zone> (00_Reference).
# KOCH_SFM_SHOW=GBF_BLD_C_Win,GBS_...: render only objects with these name prefixes. Writes <out>/manifest.json.
import json
import os
import shutil
import subprocess

import bpy
import numpy as np
from mathutils import Matrix


def world_pose(cam, al):
    """Blender camera matrix_world from a COLMAP camera (x_cam = R X + t, +Z forward, +Y down) and model->world sim."""
    s, Rw, tw = al["scale"], np.array(al["R"]), np.array(al["t"])
    R = np.array(cam["R"])
    C = np.array(cam["center"])
    rot = Rw @ R.T @ np.diag([1.0, -1.0, -1.0])     # COLMAP cam axes -> Blender cam axes (-Z forward, +Y up)
    pos = s * Rw @ C + tw
    m = Matrix.Identity(4)
    for i in range(3):
        for j in range(3):
            m[i][j] = rot[i, j]
        m[i][3] = pos[i]
    return m


def setup_camera(cam, al):
    ob = bpy.data.objects.get("TMP_SfMCam") or bpy.data.objects.new("TMP_SfMCam", bpy.data.cameras.new("TMP_SfMCam"))
    if ob.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(ob)
    w, h = cam["w"], cam["h"]
    big = max(w, h)
    cd = ob.data
    cd.sensor_fit = "HORIZONTAL" if w >= h else "VERTICAL"
    cd.sensor_width = cd.sensor_height = 36.0
    cd.lens = cam["f"] * 36.0 / big
    cd.shift_x = (w / 2 - cam["cx"]) / big
    cd.shift_y = (cam["cy"] - h / 2) / big
    cd.clip_start, cd.clip_end = 0.05, 2000
    ob.matrix_world = world_pose(cam, al)
    sc = bpy.context.scene
    sc.camera = ob
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    return ob


def link_cloud(model, al):
    s, Rw, tw = al["scale"], np.array(al["R"]), np.array(al["t"])
    P = np.array([p[:3] for p in model["points"]])
    W = (s * (Rw @ P.T)).T + tw
    name = "REF_SfM_" + model["zone"]
    me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    me.clear_geometry()
    me.from_pydata(W.tolist(), [], [])
    col = me.color_attributes.get("rgb") or me.color_attributes.new("rgb", "BYTE_COLOR", "POINT")
    col.data.foreach_set("color", (np.array([p[3:6] + [255] for p in model["points"]], float) / 255.0).ravel())
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, me)
    ref = bpy.data.collections.get("00_Reference")
    if ob.name not in ref.objects:
        ref.objects.link(ob)
    ob.hide_render = True
    ob["koch_notes"] = "aligned sparse SfM cloud (reference only, never export); rms %.3f m" % al.get("rms_m", -1)


def main():
    model = json.load(open(os.environ["KOCH_SFM_MODEL"]))
    al = json.load(open(os.environ["KOCH_SFM_ALIGN"]))
    out = os.environ["KOCH_SFM_OUT"]
    os.makedirs(out, exist_ok=True)
    sel = os.environ.get("KOCH_SFM_CAMS", "every:10")
    cams = sorted(model["cameras"], key=lambda c: c["name"])
    if sel.startswith("every:"):
        cams = cams[::int(sel.split(":")[1])]
    else:
        want = set(sel.split(","))
        cams = [c for c in cams if c["name"] in want]
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    # MATERIAL: detail-kit meshes carry several material slots (frame / glass / sill); every older part has a
    # review slot in its object colour (greybox/materials.py)
    sh.light, sh.color_type, sh.show_cavity, sh.show_object_outline = "STUDIO", "MATERIAL", True, True
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    # terrain heightfield and references would occlude interiors/basements seen from below grade
    for ob in bpy.data.objects:
        if ob.name.startswith(tuple(os.environ.get("KOCH_SFM_HIDE", "TER_,REF_").split(","))):
            ob.hide_render = True
    if os.environ.get("KOCH_SFM_CLOUD"):
        link_cloud(model, al)
    # KOCH_SFM_SHOW: only objects whose name starts with one of these prefixes are rendered (one element at a time)
    show = tuple(p for p in os.environ.get("KOCH_SFM_SHOW", "").split(",") if p)
    if show:
        for ob in bpy.data.objects:
            if ob.type == "MESH" and not ob.name.startswith(show):
                ob.hide_render = True
    magick = shutil.which("magick")
    manifest = []
    for c in cams:
        setup_camera(c, al)
        tag = c["name"].replace("/", "_").rsplit(".", 1)[0]
        png = os.path.join(out, f"r_{tag}.png")
        sc.render.filepath = png
        bpy.ops.render.render(write_still=True)
        manifest.append({"name": c["name"], "image": c["image"], "render": png})
        if not magick:  # no ImageMagick (Windows): Scripts/Geo/rs/overlay_compose.py makes the triptychs + metrics
            print("render", png)
            continue
        jpg = os.path.join(out, f"ovl_{tag}.jpg")
        # left: frame, middle: 55 % blend, right: render alone
        subprocess.run([magick, c["image"], "(", png, "-channel", "A", "-evaluate", "multiply", "0.55", "+channel", ")",
                        "-compose", "over", "-composite", jpg], check=True)
        subprocess.run([magick, c["image"], jpg, "(", png, "-background", "#303030", "-flatten", ")", "+append",
                        "-resize", "x900", jpg], check=True)
        print("overlay", jpg)
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    tmp = bpy.data.objects.get("TMP_SfMCam")
    if tmp:
        bpy.data.objects.remove(tmp, do_unlink=True)
    if bpy.app.background and os.environ.get("KOCH_SFM_SAVE"):
        bpy.ops.wm.save_mainfile(compress=True)


main()
