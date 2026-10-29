# Technical pipeline (Checkpoint 4)

**Engine:** Unreal Engine 5.8.3, C++. Lumen (software RT), Nanite, Virtual Shadow Maps, TSR, World Partition + One File Per Actor.

## Environment
1. Blender 5.2 builds the campus from photos and measurements, 1:1 in metres; every building is a JSON spec (`Art/Blender/Specs/`).
2. `Scripts/Blender/ue_prep/run.py` exports deduplicated FBX meshes with collision and a `manifest.json`.
3. `Scripts/Unreal/import_greybox.py` imports them (Nanite on) and places them in `L_GreyboxTest`.
4. Level-side passes (`fix_site.py`, `apply_facades.py`, `place_vegetation.py`, `place_props.py`, `place_far_ground.py`) fix the greybox and dress it, so the source model stays untouched.

## Gameplay
- C++ classes on the shooter template: rifle with timed reload and ejected cases, companion NPC (AI-possessed, rigged to the UE mannequin skeleton).
- Characters pipeline: phone scan → RealityScan → Mesh to MetaHuman (planned; characters are coming soon).

## Performance (RTX 3070 Laptop, 1080p, whole campus)
54.5 fps measured; 60.6 fps with the skinned wind trees hidden (they cost ~2 ms on the render thread). Target: stable 60 fps, ≤ 7 GB VRAM.

## Source control
Git + LFS for `.uasset`/`.umap`; one branch per task.
