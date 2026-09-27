# R1 handoff: rebuild the campus greybox from a photogrammetry mesh (Windows + RTX 3070 Ti)

For the teammate's PC and its Claude Code. It continues the R1 greybox (`Art/Blender/KOCH_Campus_Greybox.blend`) where the map owner's laptop stopped: that laptop has no NVIDIA GPU, so levels, stairs and platforms were estimated from single frames and are often wrong. **Goal:** one metric mesh of the site from the footage, then every element traced on it.

## 0. Strategy: the whole map coarse to fine, in passes (map owner, 2026-09-27; overrides everything below)
**Scope:** the complete game map as geometry in Blender (Unreal, materials, lighting and physics come later):
1. **The whole campus:** every object in the owner's footage or the web media (buildings with every facade element,
   filmed interiors incl. the C basement, stairs, single steps, ramps, terraces, kerbs, planters, trees, hedges, the
   garden with arches and gazebos, alleys, the gate, fences, fields, benches, lamps, bins, signs, AC units, ...).
2. **The surroundings within ~500 m** (section 6).

**Why passes.** Polishing one object to centimetres while its neighbours are 2-4 m off wastes the work: when the
frame or a level moves, the polished object moves with it. On 2026-09-27 the C entrance was fitted to the centimetre
while the gazebos, the gate→C path, the first steps after the gate, the planters and the street were off by 2-4 m.
So the map is refined like a progressive render: every zone reaches pass N before any zone starts pass N+1.

### The object list
Built from the footage, never from a fixed list (the lists in this file are hints): walk through the owner's clips
(ROUTE.md), the web media and the satellite/mesh orthophoto, and keep every object in `docs/reference/r1_progress.md`
by zone. Add new objects whenever they turn up.

### Passes, tolerances and exit tests
Each pass has two checks, and a zone passes only when both pass: the **scripted numeric test** below, and **your own
look** at the footage vs the model (section 3a "Your own review"). Scripts find and measure; you confirm. Neither
replaces the other: numbers catch what the eye misses, the eye catches what the scripts miss (a wrong object, a
missing step, a mis-registered camera that scores well).

| Pass | What exists | Tolerance | Sources used | Exit test |
|---|---|---|---|---|
| P0 frame | one world frame for all zones; every object as a box/massing at its place; every terrace level and level change from the routes (0a); the ring as OSM footprints × floors | campus ±0.30 m, ring ±2 m | satellite/mesh orthophoto, OSM, web drone/aerials, all walking clips (camera paths) | REG ≤ 0.30 m between zones (route_profile.py), control corners ≤ 0.30 m (rs_world.py fit), route_check `--tol 0.30` ≥ 95 %, every list object present |
| P1 blockout | true outlines, heights and roof masses; every stair with its riser count, every single step, ramp and kerb > 0.10 m; gazebos (plan, post count, heights), hedge blocks, planters; interiors as rooms + stairs; ring: ready-made models fitted to footprint and floor count | levels ±0.07 m (< half a riser), plan ±0.15 m | mesh sections (mesh_section.py plan/profile), wide solved cameras (`pick_cams --dist 8,80`), route event frames | route_check `--tol 0.07` ≥ 95 %; riser counts = event frames; overlay_compose median ≤ 8 px on 2 cameras per object |
| P2 greybox (last pass in Blender) | every feature ≥ 0.10 m: doors and windows (mesh_section facade), reveals, cheek walls, rails, kerb sections, interior doors, radiators, stair balustrades; the **unique modules** with their real sections (section 4a); generic props as placeholders; a material slot on every surface (4a); ring near: facades, entrances, balconies | ±0.04 m | medium cameras (`--dist 2,15`), web photos of the object | route_check `--tol 0.04` on mesh-eye clips; overlay median ≤ 3 px, p90 ≤ 8 px on ≥ 2 cameras; counts (posts, bars, windows, steps) match |
| P3 detail (**in Unreal**, not in this job) | surface relief from materials (Nanite displacement: brick, joints, render, pavers, corrugation), decals (dirt, cracks, stains), Fab/Megascans props swapped in for the placeholders, colours sampled from the photos per material slot | ~0.01 m look | close cameras, owner screenshots | UE screenshot vs photo from the same solved camera; 60 fps budget (AGENTS.md) |

**Depth cap in Blender** (owner, 2026-09-27): P2 for the whole campus, Block D/E and the ring ≤ 150 m; P1 for the
ring > 150 m. **P3 is done in Unreal** with materials, decals and ready-made assets: it is faster there and looks more
real than hand-modelling every centimetre (Nanite displacement tessellates only where the screen needs it). So this
Blender job is finished at P2; do not model sub-10 cm relief that a material or decal gives.

**Order inside a pass:** the player's route first, then outward: street + bus stop + crossing → gate + booth →
alley B–A → A_W gallery → C plaza → C exterior → C interior → **C basement** → hall–C passage → garden → sports →
hall, canteen, B, A → west campus → ring near → ring far. The C basement is still poor (owner, 2026-09-27): it goes
through every pass like the rest, never skipped as "done".

**Every photo and video is used in every pass, at the depth of that pass:** P0 wide views and camera paths, P1 wide
cameras and sections, P2 medium cameras, P3 close ones. `pick_cams.py --dist` picks them per object; web photos that do
not align are camera-matched to the model (known sizes: storey 3.30, door 0.99 × 2.05, pavers 0.20 × 0.10).

### Progress file and done rules
- `r1_progress.md` has a grid zone × pass at the top. Each object line carries the highest pass it passed and the
  commit, e.g. `P1✓ 1a2b3c4`; `[x]` only at its depth cap.
- "approx.", "in the model" and "estimated" never count as a pass.
- A blocker is written next to the item as `BLOCKED: <reason>`, stays open, and gets a Russian photo request in
  `docs/reference/photo_requests.md`. Blocked items do not stop the pass for the rest of the zone.
- **Finished** = every zone at its cap and no open item except BLOCKED ones with photo requests.

### Loop (each iteration)
**Model every iteration; never wait for the world frame (owner, 2026-09-27: "a whole day, zero progress").** Each
zone's own mesh is metric inside the zone: take levels, step counts and sizes from it now and place the zone on the map
by the satellite ortho (±0.5 m) until the stitching is done; then only shift whole zones. Every iteration changes the
.blend and is committed; stitching and GPU jobs run in the background.
1. Read the grid → the lowest open pass → the first zone in route order that has not passed it.
2. Run the zone's checks (one command, short summary) and do your own review of the frames and overlays → fix what
   fails in the specs/generators → rebuild → re-check both.
3. Commit + push when the zone passes; update the grid and the item lines; one log line.
4. While RealityScan runs a queue job, work on another zone; never wait idle, never poll with sleep loops.

## 0a. Levels from the owner's walks (P0/P1)
The phone was carried at a near-constant height, so the solved camera centres of a walking clip trace the ground the
owner walked on. `Scripts/Geo/rs/route_profile.py` turns every walking clip into a level profile: flat levels, every
step, stair and ramp (with the time and frame names), a riser hint, and the zone-to-zone registration error from frames
solved in two zones. `Scripts/Blender/route_check.py` casts rays down through the model along the same samples and lists
where the model's walking surface is off (with the object under it).
- Run route_profile over **all** zones at once so clips that cross zones chain the levels (gate → alley → C).
- Give it `--mesh` (world mesh) where there is one: the eye height then comes from the mesh; without it only level
  *differences* are trusted (route_check scores those clips relative).
- Look only at the event frames: count risers, see single steps and kerbs (e.g. the single steps every ~2 m after
  the sports hall), then write the levels into the terrain pads and stair specs.
- Pose accuracy depends on the frames per second: re-extract walking clips at `--fps 6` if steps closer than ~1.5 m
  merge. Hand shake is about ±5-10 cm, so single-step heights come from the mesh profile (mesh_section.py profile)
  and the event frames, not from the camera path alone.

## 0b. Two work streams, no conflicts (map owner, 2026-09-27)
Two agents work on the map at the same time, each on its own zones and files:
- **Stream A:** the RTX PC (this job). It computes every mesh, owns the `.blend`, and takes the route from its start.
- **Stream B:** the map owner's laptop agent (no GPU, no Unreal). It takes the route from its end, works from the
  meshes stream A exports, and commits spec/generator changes only, never the `.blend`.

| | Stream A (RTX PC) | Stream B (owner laptop) |
|---|---|---|
| Zones | Street, bus stop, crossing; Gate + booth + yard; Alley B–A; A_W gallery + plaza; C plaza + exterior; C interior F1-F5; C basement; Blocks A and B; ring (CTX) | Garden (gazebos, hedges, arches, pergola, retaining walls); Hall–C passage; Sports fields; Sports hall + wing + east end; Canteen and the small buildings north of C; West campus (D frontage, E) |
| Spec files | SITE_StreetFront, SITE_Gate, BLD_GateBooth, SITE_GateAlley (+ zone_gate_alley.py), BLD_A_S/A_N/A_E/A_W, BLD_B, SITE_CPlaza, BLD_C, INT_C_* (+ zone_c_f1.py, zone_c_basement.py), footprints.json, ctx_osm.json | SITE_Garden, SITE_HallCPassage, SITE_Sports (+ zone_sports.py), BLD_Hall, BLD_HallEast, BLD_HallWing, BLD_Canteen, SITE_WestFront |
| `.blend` | rebuilds and commits it (holds the LFS lock) | never commits it; builds a local scratch copy for its checks |

Rules:
- Each stream edits only its own spec files and its own sections/grid rows of `r1_progress.md`; log lines start with
  `[A]` or `[B]`. Terrain pads live in the zone's own spec, so they follow the zone.
- Shared code (`Scripts/Blender/*`, `greybox/*`, `Scripts/Geo/*`): small separate commits, `git pull --rebase` right
  before every commit; never reformat or move code you did not change.
- Stream A pulls at the start of every iteration and rebuilds the `.blend` when stream B's specs changed.
- A seam object that touches both (e.g. the passage stair at C's west side, the garden edge at the alley): the owner of
  the object's spec file decides; the other stream writes a one-line request in the log instead of editing.

**Mesh drops for stream B** (stream A, as soon as a zone's mesh is ready: Garden, Sports, C_sw, WEB_drone, then any
later zone that covers stream B's area):
- `<zone>/mesh.ply`: world metres (`rs_world.py apply`), decimated to ≤ 3M triangles, no texture, no vertex colours;
- `<zone>/align.json`, `<zone>/model.json` (cameras only, no images: the owner has the raw footage and re-extracts the
  frames by name), and the zone's `route.json` from route_profile.py;
- zipped per zone (`<zone>_<date>.zip`) into the Google Drive folder `koch_meshes`, shared with the map owner only
  (never "anyone with the link"), then one log line `[A] mesh drop <zone>`. Never commit meshes.

## 1. Get the data (never commit it: people in the frames)
- **Repo:**
  - branch `feat/r1/greybox-zones`; `git lfs pull` for the `.blend`;
  - `git lfs locks` before editing the `.blend`, then lock it (AGENTS.md → Git).
- **Footage from the map owner** (drive/USB, not git):
  - `alatoo-capture/raw` (7.4 GB, 145 files: Pixel 9 photos + 4K60 videos) → `C:\koch\raw`.
  - `alatoo-capture/data` (91 MB: satellite orthos, plans) → `C:\koch\data`.
- **Notes:**
  - `alatoo-capture/ROUTE.md` lists what each file shows.
  - Web media (YouTube drone clips, 2GIS photos) is in the owner's `~/koch_work/web` if needed.

## 2. Build the mesh in RealityScan 2.2
RealityScan is free for students and under $1M revenue: realityscan.com, Epic account, Windows, NVIDIA GPU. Its CLI is the RealityCapture command set (help: rshelp.capturingreality.com). Check each flag there before scripting; don't guess.

1. **Frames.** Photos go in as they are (EXIF focal). Videos: extract frames with ffmpeg at 2–3 fps into one folder per clip:
   ```
   ffmpeg -i raw\PXL_x.mp4 -vf fps=3 -q:v 2 frames\PXL_x\%04d.jpg
   ```
   Most clips are the 0.5x ultrawide with EIS: stabilisation changes the crop per frame.
   - Give each video folder its own lens group.
   - Drop clips that won't align or that degrade the model.
2. **Masks.** Mask people: RealityScan AI masking, or SAM 2 batch masks.
3. **Align** everything in one project. Where components don't connect, add 3+ control points on the same kerb or window corners in both.
4. **Scale and frame.** Set these as control points / distances; the world frame is in section 3.
   - Known distances (m):
     - Block C storey 3.30 (window rows).
     - C classroom door frame 0.99 × 2.05.
     - C entrance stair: 7 risers × 0.15.
     - C east-wing facade 12.8 wall-to-wall.
     - Gap between B's east wall and A's west wall ≈ 13.4 (drone SfM gave 12.6; the mesh decides).
     - Pavers 0.20 × 0.10.
   - Control points (world X east, Y north, metres; Z only where the floor level is known). These are wall-face corners at ground/plinth level:

     | Point | X | Y |
     |---|---|---|
     | C SW corner (west wing) | 173.264 | −3.640 |
     | C SE corner | 202.692 | −3.513 |
     | C NE corner | 203.326 | 12.375 |
     | C NW corner | 173.949 | 13.546 |
     | A_S NW corner | 161.233 | −70.100 |
     | A_S SW corner | 160.275 | −89.627 |
     | B NE corner | 148.453 | −56.926 |
     | B SE corner | 147.256 | −81.356 |

     The C floor (FFL) is Z 6.40; the plaza south of C is Z 5.35 (= FFL − 7 × 0.15).
     These corners come from the current specs: good to ~0.3–1 m in plan. Use them for position and rotation. Take the scale from the tape-like distances above, not from these corners.
5. **Build.** Normal-detail mesh + texture. Export OBJ (+ PLY point cloud) in that local frame.
   - Put the mesh in `Art/Blender/Reference/` locally. It is big and shows people/texture: **never commit it**; add the path to `.gitignore` if needed.

## 3. Frames and conventions
- **World frame:** local TM (k = 1) at 42.8566 N 74.6790 E; X east, Y north, Z = ASL − 800 (docs/decisions.md). UE = (x, −y, z) × 100.
- **Block C local frame** (used by its specs): origin = C SW corner (173.264, −3.640), x along (0.99920, −0.03985), y north, z above FFL 6.40.
- **Block A local frame** (A_S/A_N/A_W/A_E + the alley generator): origin (158.84, −92.76), x along (0.999, −0.049).
- **The pipeline:**
  - The geometry comes from specs `Art/Blender/Specs/*.json`, built by `Scripts/Blender/build_all.py` (terrain + BLD_* + SITE_*/INT_*); the build validates manifold meshes and unique names.
  - Zones with generators (edit the generator, then run it):
    - `Scripts/Geo/zones/zone_gate_alley.py` (alley B–A);
    - `zone_c_f1.py` (C interiors, all floors);
    - `zone_c_basement.py` (C basement entry);
    - `zone_sports.py` (sports area + hall–C passage).
  - Ground levels are `terrain_pads` in the specs; pads with blend 0 are hard edges.
- **Run:**
  ```
  blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_all.py
  ```
  or in a live Blender through MCP:
  ```
  runpy.run_path(".../build_all.py", run_name="__main__")
  ```
  then save.
- **Checks:** a coplanar-overlap audit and a terrain-poke check exist on the owner's machine (`~/koch_work/fixG/zaudit.py`, `poke.py`). Copy them if useful.

## 4. How to rebuild on the mesh
1. **Import.** Import the mesh into the `.blend` as `REF_Photogrammetry` in the `00_Reference` collection. Lock it; it is never exported (the builders skip `REF_*`).
2. **One world frame first (P0).** All zone models must agree before anything is measured on them.
   **Rule (map owner, 2026-09-27): divide and merge, never one whole-site solve.** The zone models are the chunks;
   join them pairwise in route order (Street → Gate → Alley → AW → C → ...), one pair per step, each step minutes.
   Whole-site runs (COLMAP/GLOMAP on all ~3900 frames) are not allowed: a 2026-09-27 run needed hours and 13 GB RAM,
   GLOMAP is known to run out of memory late on thousands of images (github.com/colmap/glomap/issues/78), and an
   earlier global COLMAP model false-merged on the herringbone paving and repeating windows. This is the standard
   large-scene method (COLMAP FAQ: overlapping sub-models, then merge; RealityScan: component workflow). No job over
   10 GB RAM. For each pair:
   - shared frames first: a walking clip that crosses both zones;
   - else 4-6 control points on corners seen in both zones, plus satellite corners;
   - check the pair (route_profile REG ≤ 0.30 m) before the next pair; one bundle adjustment at the end.

   Ways to do the merge:
   - Preferred: merge the zones in RealityScan through control points (at least 4 CPs per component, each seen in
     several images; 6 shared CPs between two components; rshelp "Merging Components Using Control Points"): kerb
     corners, building corners and paving joints that are visible from both zones.
   - Else: fit every zone to the world with `rs_world.py fit` on shared corners (the control corners of section 2 +
     corners picked on the satellite orthophoto) and check each pair of zones with the REG lines of route_profile.py.
   - Take plan outlines (planters, gazebos, hedges, paths, kerbs, tree pits) from the mesh orthophoto
     (`rs_world.py level` → plan_rgb.png) or the satellite orthophoto, never from single oblique frames.
3. **Then the passes of section 0**, zone by zone in route order. For each zone and pass: levels from 0a, outlines
   and heights from mesh_section.py (plan/profile/facade), written into the specs/generators with evidence strings
   ("mesh profile", "route event f00123"); rebuild; run the pass test.
4. **Owner's rules:**
   - **Every item.** Number every screenshot and bug the owner sends, close each one, and report each as done or blocked with a reason.
   - **Verify before "done".** Check from the same viewpoint as the owner's screenshot and the real photo before saying done.
   - **The owner can be wrong** (it happened twice). Verify their claims against the footage and show proof when it disagrees.
   - **Shared machine resources.** Heavy jobs go under a memory cap. Replies to the owner are short and in Russian.
   - **Lore.** No real names or logos anywhere in the game (KOCH only). Never commit the raw footage.

## 3a. Agent and token budget for this job (map owner, 2026-09-27; stricter than AGENTS.md)
- Work solo by default. At most **2 subagents** at a time, only when they really save time; never more.
- **No workflows, no Verify / review / adversarial phases, no "second opinion" agents.** Verification means a build plus
  the scripted pass test, done by you.
- The run on 2026-09-27 wasted most of a session limit on a 20-agent review workflow (1.5M tokens) that changed nothing on the map.
- High effort for hard problems (registration, alignment, a test that keeps failing); routine spec edits are quick.

### Token economy (same quality, fewer tokens)
- **Scripts do the work, you read summaries.** Every command prints at most ~20 lines: send logs to files
  (`> log.txt 2>&1`) and print `tail`/summary lines only. Never dump JSON, CSV, specs or logs whole into the context.
- **One command per check:** write once a `pass_check` script (zone + pass → build, route_check, pick_cams, sfm_overlay,
  overlay_compose, a 10-line verdict) and use it every iteration instead of re-typing chains of commands.
- **Images, targeted:** open the images the review below needs, ≤ 1280 px, composites from overlay_compose; never
  open raw 4K frames or whole folders. Contact sheets for triage.
- **Read little:** `grep` the spec field you change instead of reading whole specs; from this file read section 0/0a
  and the part you need; from r1_progress.md read the grid and the current zone only. After a context compaction,
  re-read just those.
- **GPU waits:** RealityScan jobs run in the queue (gpu_queue.ps1); meanwhile work on another zone or pass. When
  nothing else is left, schedule a long wake-up (≥ 20 min) instead of polling.
- **Chat:** at most 3 short Russian lines per iteration, e.g. `P1 · Gate · G.7 ступени 5→6, route ±0.04 ✓ 1a2b3c4 · дальше G.8`.
  No tables, no recaps, no plans in chat. Details go into the progress log (one line per zone-pass).
- **Your own review (required, every zone-pass):** look at the footage yourself and judge it as a modeller:
  - every route event (step, stair, ramp): the frames around it; count the risers and see what the edge is;
  - every object group in the zone: one overlay composite from 2 cameras at the pass distance; check shape, count and
    position against the photo, not only the metric;
  - anything the scripts flag, plus one look at the zone overall (a wide camera) for missing or extra objects;
  - where you disagree with a script, trust the footage, find why the script was wrong and fix it or its input;
  - write what you saw in the log line (e.g. `looked: 6 events, 9 overlays; H.2 ramp side wrong → fixed`).
- **Keep going on your own** until "Finished" (section 0). Stop only for a real blocker on every remaining item; then
  write the photo requests and say so in 2 lines.

## 4a. Detail standard in Blender (P2): real structure for the unique parts, slots for the rest
Blender delivers the true shape, size and position of everything, and real modelled sections for the parts that no
ready-made asset can match. Surface relief and generic props come in Unreal (P3, section 0).

### Model as real geometry (unique to this campus)
- **Walls:** real thickness, window and door reveals; plinth bands and cornices with their true profiles; pilasters,
  expansion joints, parapets and copings.
- **Windows and doors:** frames, sashes, mullions, leaves with stiles and rails, glass set back, sills with their slope,
  surrounds, thresholds, transoms (as a modular kit: one mesh + instances per type).
- **Stairs and ramps:** each step (tread, riser, nosing), cheek walls with caps, handrails and balustrades with posts,
  rails, bars and brackets; ramp decks, frames, rails.
- **Ground:** every kerb with its section, planter and tree-pit rims, retaining walls with copings, paving level
  changes, bank slopes.
- **Roofs:** hips, ridges, eaves, fascia boards, gutters and downpipes, dormers with their own roofs.
- **Canopies, galleries, gazebos, pergolas, arches, the gate canopy, the booth, fences with their real bays.**
- **Interiors (Block C):** walls, openings, door frames, stairs with balustrades, ceiling steps and bulkheads, fixed
  fittings (radiators, WC stalls, sinks) as simple true-size shapes.

### Leave to Unreal (P3)
- **Surface relief and texture:** brick-tile pattern, mortar joints, render roughness, paver pattern, stone grain,
  corrugation ribs, dirt, stains, cracks: materials with Nanite displacement and decals.
- **Generic props:** bins, generic lamps, AC units, CCTV, floodlights, sign posts, bike racks, benches of a common
  type, vegetation. In Blender they are simple placeholders at the true position, size and orientation, with a custom
  property `koch_ue_asset = "<type>"` (e.g. `bin_wrought_iron`, `street_lamp_curved`, `ac_unit`) so UE swaps them for
  Fab/Megascans assets. Props that are unique to the campus (the decorative bicycle, the gazebo lanterns) are modelled.

### Material slots (every surface, from P2)
- Every face gets a material slot from `Scripts/Blender/greybox/materials.py` (`M_<Material>_<Finish>`, e.g.
  `M_Render_Beige`, `M_Tile_Brick_Red`, `M_Granite_Red`, `M_Sheet_Red`). Add new names to its PALETTE when a real
  material is missing; one name per real material, used everywhere it occurs. The site/zone builders must use these
  slots too (not only build_facades.py); no plain colour materials in the delivered file.
- Choose the slot from the footage while modelling (what the surface really is). UE maps each slot to a PBR material
  and samples its base colour from the photos through the solved cameras.

### Rules for the geometry
- True-scale metres, with the real construction logic: parts join as they do in reality, with no floating and no interpenetrating slabs.
- One surface per real surface (no coplanar overlaps).
- Manifold meshes.
- Repeated parts (windows, doors, lamps, posts, railing bays, benches) as one mesh plus linked instances, i.e. a modular kit.
- Nanite handles dense meshes in UE, so detail is fine. Still, no hidden or internal faces, and no micro-geometry where a material works.
- Put everything through the spec/generator pipeline, extending the builders with new element types and profiles, so it rebuilds. Hand-modelled one-offs are acceptable only for unique pieces; keep them in their own collection with a note.

### Per-element loop for the unique modules (P2)
1. Collect the close cameras and stills that show the element (`pick_cams.py --dist 0,5`, ROUTE.md, web photos).
2. Measure on the mesh (mesh_section.py) and check against known sizes: storey 3.30, door 0.99 × 2.05, risers, pavers.
3. Model it at the detail standard above, with its material slots.
4. Check: sfm_overlay.py + overlay_compose.py through ≥ 2 real cameras (median ≤ 3 px), and look at the composites
   yourself: edges, heights and counts (steps, posts, bars, windows). Fix and repeat until both agree.
5. Also check from the owner's screenshot viewpoint if they marked that spot. Commit.

## 5. Open items the mesh must settle (from the owner's marked screenshots)
- **C basement (owner 2026-09-27: "still poor"):** rebuild it from the `C_base` zone and the basement clips, not from
  the old estimates: the stair down (riser count and heights from the route events of the walk down), landing, the
  vaulted corridor (width, vault spring and crown heights from mesh_section profile), barred windows and light wells,
  the art room, the piano room, doors, and how it joins the Dance Hall entry and the F1 stairs.
- **Single steps and small level changes on the paths** (e.g. after passing the sports hall: one step, ~2 m, another
  step, ...): every one from the route events (0a), with its frames.
- **Block C:**
  - The west "Dance Hall" shed roof and its continuation toward the spruces SW of C: shape, depth and height.
  - The basement entry roof: red mono-pitch over the box and stair.
  - The entrance stair cheeks and ramp.
  - The south-front covers and parapet.
- **The A_W gallery (canteen):**
  - A level tiled deck about 0.30 above the walkway, with a single step only between the 1st and 2nd post from the north.
  - The north-end steps + grey ramp on the wall side.
  - Door and window positions.
- **The wide stair north of B's NE corner:** width, cheeks, beds.
- **Sports-hall east end and wing:**
  - One continuous mass; heights and roof are unknown.
  - Door with canopy by the ramp.
  - Passage stair 2.2 m wide with a grey ramp on its west side and a low railing with dense bars.
- **Levels:**
  - The flat alley along B is 6.75/6.63.
  - The walkway along A is 5.35.
  - The lower terrace (garden, gazebos, C plaza) is 5.35.
  - The sports level is ~4.475 → 3.45.
  - Re-measure all of them on the mesh.
- **Block B.** Possibly 0.8 m further east (B–A gap 12.6 vs 13.43).
- **Not built yet:** WC interiors (videos `075725091`, `075928860`, `075931189`) and classroom 203 (`074805359`).
- Full lists: `docs/reference/photo_requests.md`, `docs/reference/campus.md`.

## 6. Surroundings within ~500 m (context ring)
The player sees the city around the campus from the gate, the street, the bus and upper floors. It must be at the right place, the right height and the right shape, but it does not need the campus's detail level.
- **Footprints and heights:**
  - OSM buildings in a 500 m buffer around the campus boundary. Use the Overpass API with `building` + `building:levels` / `height`; the world frame is in section 3 and `Art/Blender/Data/site_osm.json` (origin 42.8566 N, 74.6790 E).
  - Where OSM has no levels: count floors in the owner's street videos, web photos and 2GIS photos, and on Google/Bing obliques (≈3.0 m per residential floor, plus the ground floor and a parapet).
  - Put the list in `r1_progress.md` under "Surroundings" with the evidence for each building.
- **Streets:** carriageways with the real lane count, kerbs, sidewalks, crossings with zebras, bus and trolleybus stops with shelters, trolleybus poles and wires, street lamps, trees, parking, fences and walls. The main street in front of the gate is already partly modelled (SITE_StreetFront, SITE_Gate).
- **Buildings: reuse ready-made models instead of modelling each one.**
  - Sources: Fab (free, Standard License, allowed in games), Poly Haven (CC0), BlenderKit free (Royalty-Free), Sketchfab CC0/CC-BY. Do not use CC-BY-NC or ND.
  - Pick models that match the real type: Soviet-era 5- and 9-storey panel blocks, modern 12–16-storey residential towers, low shops and garages, the industrial halls to the north.
  - Scale each model to the real footprint and floor count, and place and rotate it exactly on the OSM footprint.
  - Record the source URL and licence of every asset in `docs/reference/asset_sources.md` (one line each).
  - Remove real names, logos, signs and brands from the models (AGENTS.md → Lore).
  - Where nothing fits, build a clean massing with window bands and floor lines from the photos.
- **Detail by distance:** buildings the player can walk up to (along the gate street and the west street) get facades, entrances, balconies and ground-floor shops from the photos. Distant blocks get correct massing, roof shape, floor rhythm and colour zones only. Keep the polycount sane (instances for repeated blocks).
- **Collections:** everything outside the campus goes into `CTX_*` collections so UE can stream and HLOD it separately.
