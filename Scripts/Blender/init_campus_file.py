# Creates/updates Art/Blender/KOCH_Campus_Greybox.blend: metric units, collection layout, MCP auto-start.
# Idempotent. Run: blender -b -P Scripts/Blender/init_campus_file.py
import os
import bpy

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "Art", "Blender", "KOCH_Campus_Greybox.blend")

# Collection tree. "00_*" is reference only, never exported to UE.
LAYOUT = {
    "00_Reference": ["REF_Satellite", "REF_Plans"],
    "01_Terrain": [],
    "02_Buildings": ["BLD_A", "BLD_B", "BLD_C", "BLD_D", "BLD_Gallery", "BLD_Other"],
    "03_Site": ["SITE_Paving", "SITE_Curbs", "SITE_StairsRamps", "SITE_FenceGate", "SITE_Checkpoint", "SITE_Sport"],
    "04_Garden": ["GRD_Hedges", "GRD_Arch", "GRD_Gazebos", "GRD_Furniture"],
    "05_Street": ["STR_Road", "STR_Crossing", "STR_BusStop"],
    "06_Vegetation": ["VEG_Trees", "VEG_Shrubs"],
    "07_BlockC_Interior": ["INT_C_Basement", "INT_C_F1", "INT_C_F2", "INT_C_F3", "INT_C_F4", "INT_C_F5"],
    "08_Context": ["CTX_Buildings"],  # neighbour massing, backdrop only
}


def ensure_collection(name, parent):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in parent.children:
        parent.children.link(col)
    return col


def main():
    if os.path.exists(OUT):
        bpy.ops.wm.open_mainfile(filepath=OUT)
    else:
        bpy.ops.wm.read_homefile(use_empty=True)

    scene = bpy.context.scene
    us = scene.unit_settings
    us.system, us.scale_length, us.length_unit = "METRIC", 1.0, "METERS"  # 1 BU = 1 m; FBX export converts to UE cm

    root = scene.collection
    for top, subs in LAYOUT.items():
        parent = ensure_collection(top, root)
        for sub in subs:
            ensure_collection(sub, parent)

    # Campus is ~430 m wide: widen clipping so the whole site is visible in the viewport.
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.clip_start, space.clip_end = 0.01, 3000.0

    if hasattr(scene, "blendermcp_auto_start_server"):
        scene.blendermcp_auto_start_server = True  # Claude connects on port 9876 as soon as the file opens

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    print("SAVED", OUT)


main()
