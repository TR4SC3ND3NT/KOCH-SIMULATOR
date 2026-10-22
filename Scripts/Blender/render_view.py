# Headless Workbench review render of the greybox from an arbitrary camera (R1 photo comparisons). Does not save.
# Run: blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/render_view.py -- \
#        CAM_X CAM_Y CAM_Z TGT_X TGT_Y TGT_Z LENS_MM OUT.png [W H]     (world metres, campus frame)
import os
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
px, py, pz, tx, ty, tz, lens = map(float, argv[:7])
out = argv[7]
w, h = (int(argv[8]), int(argv[9])) if len(argv) > 9 else (1400, 1000)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light, sh.color_type, sh.show_shadows, sh.show_cavity = "STUDIO", os.environ.get("KOCH_COLOR", "OBJECT"), True, True   # KOCH_COLOR=MATERIAL: slot colours
cam = bpy.data.objects.new("TMP_ViewCam", bpy.data.cameras.new("TMP_ViewCam"))
sc.collection.objects.link(cam)
cam.data.lens, cam.data.clip_start, cam.data.clip_end = lens, 0.05, 3000
pos, tgt = Vector((px, py, pz)), Vector((tx, ty, tz))
f = (tgt - pos).normalized()
r = f.cross(Vector((0, 0, 1))).normalized()
u = r.cross(f)
cam.matrix_world = Matrix.Translation(pos) @ Matrix((r, u, -f)).transposed().to_4x4()
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
