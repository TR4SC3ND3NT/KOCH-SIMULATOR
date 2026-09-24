# Decisions (one line each: date — decision — why/source)

- 2026-09-24 — UE 5.8.3 for everyone — latest/final UE5, first-party Unreal MCP, Linux Vulkan fix in 5.8.1 — unrealengine.com/news/unreal-engine-5-8-is-now-available
- 2026-09-24 — 1080p ≥60 fps on the 3070 Ti Laptop and the RX 6750 GRE; Lumen SW High + Nanite + VSM + TSR (DLSS/FSR optional), no frame gen — the 3070 Ti Laptop at 150 W ≈ a desktop 3060 Ti
- 2026-09-24 — C++ First Person template; no Lyra, City Sample or GAS — simpler for agents, single-player
- PENDING — LFS host: GitHub + $10 budget cap (≈$3–10/mo) vs Azure DevOps (free, HTTPS-only with LFS) — the GitHub Free LFS quota of 10 GiB is too small
- 2026-09-24 — Greybox pipeline: own Python (uv: pyproj/shapely/rasterio) → JSON in `Art/Blender/Data/` → bmesh builder `Scripts/Blender/build_greybox.py`; no Blender add-ons; `bpypolyskel` (GPL-3) vendored as tool code only, never shipped — reproducible; Blosm/BlenderGIS/Building Tools are broken or unmaintained on 5.2
- 2026-09-24 — World frame: local TM (k=1) at 42.8566 N 74.6790 E; X east, Y north, Z = ASL − 800 m; UE = (x, −y, z) × 100 cm — true north on +Y, sub-mm precision; UTM would be 392 ppm short
- 2026-09-24 — Tracing imagery: Bing ≤2021 (near-nadir) as the footprint base; Esri 2020 roofs lean ≈0.45 m/m west, used only as a leaf-off check; post-2021 changes from Sentinel-2, render, event map, photos — no legally traceable imagery newer than 2021
- 2026-09-24 — Terrain: GLO-30 (commercial OK) masked robust quadratic (−2.4 % N, −1.0 % E, rms 1 m); FABDEM (NC) only as a check; in UE soft ground = Landscape (50 cm quads, baked from Blender), hardscape = Nanite meshes
- PENDING — Export: FBX (io_scene_fbx) → Interchange, one asset per file, parented UCX, pieces ≤ ~15 m for Lumen SW; prefix SM_ (Epic) vs S_ (Allar) needs a team decision
- 2026-09-24 — Facade metrology: single-view rectification (VPs + EXIF/solved focal, `Scripts/Geo/facade_rectify.py`) per wall plane; absolute scale from satellite facade length, cross-checked by eye height/sills/steps; recovered camera poses give photo-matched review renders — no laser survey available yet
- 2026-09-24 — Facade greybox build: per-building spec `Art/Blender/Specs/<BLD>.json` → `build_facades.py`; walls as closed pieces per storey band ≤12 m (Lumen SW), real openings/reveals without booleans, windows/surrounds as shared meshes (linked duplicates → UE instances)
- 2026-09-25 — Greybox specs: one JSON per building/site area in `Art/Blender/Specs/` (every element carries evidence + confidence; confidence low = orange), rebuilt by `Scripts/Blender/build_all.py` with a manifold/name validator — reproducible, reviewable diffs; the .blend is a build artifact
