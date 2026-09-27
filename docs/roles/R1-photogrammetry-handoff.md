# R1 handoff: rebuild the campus greybox from a photogrammetry mesh (Windows + RTX 3070 Ti)

For the teammate's PC and its Claude Code. It continues the R1 greybox (`Art/Blender/KOCH_Campus_Greybox.blend`) where the map owner's laptop stopped: that laptop has no NVIDIA GPU, so levels, stairs and platforms were estimated from single frames and are often wrong. **Goal:** one metric mesh of the site from the footage, then every element traced on it.

## 0. Scope and definition of done (map owner, 2026-09-27; overrides any shorter list)
**Scope:** the complete game map, production-ready as geometry in Blender. Unreal, materials, lighting and physics come later.
1. **The whole campus**, every object that appears in the owner's footage or the web media: buildings (every facade, entrance, door, window, roof, dormer, gutter), interiors that were filmed, stairs, ramps, platforms, kerbs, paving and level changes, planters, trees, hedges, the garden with its arches and gazebos, alleys, paths, the gate and checkpoint, fences, parking, the fields and courts, benches, lamps, bins, signs, AC units and everything else visible.
2. **The surroundings within ~500 m of the campus** (section 6): streets, sidewalks, crossings, bus/trolleybus stops, neighbouring buildings and high-rises, walls and fences, open ground.

**How the object list is made:** never from a hard-coded list, including the order suggestions in this file. Walk through all footage (owner capture + web media, see ROUTE.md) and the satellite image, and write every object you can see into `docs/reference/r1_progress.md`, grouped by area. Add objects whenever you find new ones.

**One object at a time, finished before the next:**
1. collect every photo and frame that shows it, and analyse them;
2. align those images in RealityScan and build the mesh (GPU queue);
3. metric scale and world frame;
4. read every size and level off the mesh;
5. model at the detail standard (4a);
6. overlay-check through at least 2 real solved cameras, detail by detail;
7. fix, commit and push, then tick `[x]` with the commit hash.

**Done rules:**
- `approx.`, "already in the model" and "estimated" are NOT done: leave such items unticked.
- A blocker (no footage, alignment impossible) is written next to the item as `BLOCKED: <reason>` and stays unticked. Also add a Russian photo request to `docs/reference/photo_requests.md`.
- The map is finished only when `r1_progress.md` has no `[ ]` and no `approx.`, or only `BLOCKED` items with photo requests.

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
2. **Rebuild zone by zone, in this order:**
   1. C (exterior, basement entry, west shed);
   2. the A_W gallery deck and its plaza;
   3. the B–A alley and its stairs;
   4. the hall–C passage and the sports hall's east end;
   5. the garden;
   6. the gate.

   For each zone:
   - Read the levels (Z) of every walking surface, step, kerb and platform, the plan outlines, and the roof edges directly off the mesh. Snap to faces.
   - Write them into the spec or generator, with evidence strings saying "photogrammetry mesh".
   - Rebuild, then compare with the mesh from several viewpoints and with the photos.
3. **Owner's rules:**
   - **Every item.** Number every screenshot and bug the owner sends, close each one, and report each as done or blocked with a reason.
   - **Verify before "done".** Check from the same viewpoint as the owner's screenshot and the real photo before saying done.
   - **The owner can be wrong** (it happened twice). Verify their claims against the footage and show proof when it disagrees.
   - **Shared machine resources.** Heavy jobs go under a memory cap. Replies to the owner are short and in Russian.
   - **Lore.** No real names or logos anywhere in the game (KOCH only). Never commit the raw footage.

## 3a. Agent and token budget for this job (map owner, 2026-09-27; stricter than AGENTS.md)
- Work solo by default. At most **2 subagents** at a time, only when they really save time; never more.
- **No workflows, no Verify / review / adversarial phases, no "second opinion" agents.** Verification means a build plus
  an overlay through real cameras, done by you.
- The run on 2026-09-27 wasted most of a session limit on a 20-agent review workflow (1.5M tokens) that changed nothing on the map.
- Use high effort; reserve deeper thinking for hard problems (alignment, registration), not for routine measuring.

## 4a. Detail standard: real modelled structure, not boxes (the owner's hard requirement)
The owner wants the Blender result to look close to reality **as geometry**, not a blockout. Model every element as it is built in reality, down to the smallest part with visible relief (about 1 cm or more). Do not move to the next element until the current one matches the footage pixel by pixel.

### What to model as real geometry
- **Walls:**
  - real thickness, window and door reveals;
  - plinth bands and cornices with their true profiles (steps, drips, chamfers);
  - pilasters, expansion joints, parapets and copings.
- **Windows:**
  - outer frame, sashes and mullions with real sections;
  - glass set back in the frame;
  - the exterior sill with its slope and drip;
  - surrounds as separate profiled pieces.
- **Doors:**
  - frame, leaf with stiles, rails and glass panes;
  - handles or pull bars, thresholds, transoms;
  - hinges where visible.
- **Stairs:**
  - each step: tread, riser, nosing/chamfer, stone joints where they are relief;
  - cheek walls and their caps;
  - handrails and balustrades with posts, rails, bars, end curls and wall brackets.
- **Ramps:** grating deck, frame and stringers, rails, posts with feet.
- **Ground:**
  - every kerb with its section (chamfer or round), painted kerbs as separate pieces;
  - planter and tree-pit rims, drains and manhole covers, paving level changes;
  - bank slopes and retaining walls with copings.
- **Roofs:**
  - corrugated or standing-seam sheets as real ribs where visible up close;
  - ridge caps, fascia boards, gutters with hangers, downpipes with elbows and shoes;
  - dormers with their own roofs;
  - snow guards and flashing.
- **Canopies and galleries:** posts with bases and caps, beams, soffit panels, edge trims.
- **Fittings:** AC units with brackets, lamps (pole, arms, lantern), benches (frame, slats), bins, signs (panel and posts; blank KOCH panels), cameras, floodlights, fences (posts, rails, mesh panels, gates with hinges).
- **Interiors (Block C):** skirting, door frames, ceiling grid with LED panels, bulkheads, radiators with pipes, stair balustrades, WC stalls, sinks, cisterns.

### What stays material (for UE, not geometry)
- Surface texture: brick-tile pattern, render roughness, paver pattern, stone grain, dirt.
- If a pattern has real depth (deep mortar joints, corrugation seen close), model it; otherwise leave it to materials and decals.

### Rules for the geometry
- True-scale metres, with the real construction logic: parts join as they do in reality, with no floating and no interpenetrating slabs.
- One surface per real surface (no coplanar overlaps).
- Manifold meshes.
- Repeated parts (windows, doors, lamps, posts, railing bays, benches) as one mesh plus linked instances, i.e. a modular kit.
- Nanite handles dense meshes in UE, so detail is fine. Still, no hidden or internal faces, and no micro-geometry where a material works.
- Put everything through the spec/generator pipeline, extending the builders with new element types and profiles, so it rebuilds. Hand-modelled one-offs are acceptable only for unique pieces; keep them in their own collection with a note.

### Per-element loop (do not skip steps)
1. List the element and its parts. Collect every photo and video frame that shows it; ROUTE.md and file times help.
2. Measure positions, levels and sizes on the photogrammetry mesh (snap to it). Cross-check with the known sizes: storey 3.30, door 0.99 × 2.05, risers, pavers.
3. Model it at the detail standard above.
4. Verify:
   - render the model through at least 2 of the real cameras solved by RealityScan (export its camera poses; `Scripts/Blender/sfm_overlay.py` does photo | blend | model triptychs);
   - compare edges, heights and counts (steps, posts, bars, windows) pixel by pixel;
   - fix and repeat until they match.
5. Also check from the owner's screenshot viewpoint if they marked that spot.
6. Commit only then. Move on to the next element.

## 5. Open items the mesh must settle (from the owner's marked screenshots)
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
