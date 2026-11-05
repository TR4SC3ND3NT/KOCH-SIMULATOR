# KOCH-SIMULATOR: Production (midterm, 2026-11-09)

Asset and shot list with status, pipeline notes, team roles and the plan for the six weeks after the midterm.

**Status keys:** **Done** = in the UE project and working in PIE (prototype quality is marked as such). **In progress** = started in the repo, not final. **Not started** = planned only (a design doc may exist).
**Evidence:** README (status 2026-10-29), Checkpoint 4 documents, `docs/lore/proposals/` (2026-11-05) and git history (489 commits since 2026-09-24, 192 of them since 2026-10-01).

Story missions referenced below (story is a **proposal** awaiting the human lore author): M00 Morning Route, M01 FaceGate, M02 Brew Point, M03 Hedge Maze, M04 Room 203, M05 The Attic, M06 Staff Studio, M07 Health Center, M08 Assembly. About 34 minutes in total.

---

## 1. Asset list

### 1.1 Environment (R1)

| Asset | Now | Status | Missions |
|---|---|---|---|
| Campus 1:1 greybox in Blender (blocks A–D, sports hall, canteen, both guard booths, site areas) | 34 JSON specs in `Art/Blender/Specs/`, rebuilt by `Scripts/Blender/build_all.py` | **Done** | all |
| Import into UE 5.8 | `Maps/L_GreyboxTest`: 2324 Nanite meshes, 7474 actors, World Partition | **Done** | all |
| Context city around the campus | 310 apartment blocks with a procedural facade material (`M_FacadeApartment`) | **Done** | M00, backdrops |
| Ground: holes, steps, kerbs, far ground | Fixed after owner review rounds (12 marked photos, in-game marks); `SM_FarGround`, `M_KerbStriped` | **Done** | all exteriors |
| City yard trees | 700 HISM instances, Nanite voxel foliage (cheap) | **Done** | backdrops |
| Street furniture kit (benches, bins, pallets of slabs) | `Environment/Props/Street`, 25 benches re-oriented from review marks | **Done** | M00–M03 |
| Street, pedestrian crossing (zebra 4.3 m) | Greybox | In progress | M00, ending A |
| Checkpoint "Post One": booth, canopy, sliding gate | Greybox (booth 3.42 × 3.10 m, canopy 11.9 × 3.45 m) | In progress | M01 |
| Gate alley, plaza, stairs | Greybox, walkable | In progress | M02 |
| Garden: hedges, maze, gazebos, trees | UE vegetation pass; skinned wind trees cost ~2 ms (render thread) and must be replaced by static meshes with WPO wind | In progress | M03 |
| PBR materials for facades and paving | First pass (Poly Haven CC0 surfaces, `MI_FacadeOffice`) | In progress | all |
| Lighting and post-process | First pass, Lumen software RT | In progress | all |
| Block C ground floor: hall, stairs, WC | Greybox, walkable, coloured review materials | In progress | M04 |
| Block C F2–F5 (room 203, attic offices) | Greybox spec `INT_C_Floors`; no set dressing | In progress (greybox only) | M04, M05 |
| Block C basement: Staff Studio, piano room | Greybox spec `INT_C_Basement` | In progress (greybox only) | M06 |
| SIGHT node room C-001 (4 racks) | — | Not started | M06 |
| Turnstiles with face terminals (in/out) | — | Not started | M01, ending A |
| KOCH signage set (wordmark, block plates, room plates, posters, flags) | Art Bible rules only | Not started | all |
| Block B interior: PR lobby, demo lab, Brew Point café | Exterior exists | Not started | M02 |
| Block A interiors: Clinic, Archive, Assembly Hall, CEO floor | Exteriors exist | Not started | M07, M08 |
| Arsen's apartment (separate small level) | — | Not started | M00 |
| Bus stop and bus/trolleybus interior | — | Not started | M00, ending B |
| Courts / drill ground | Spec exists, not built in UE | Not started | optional |
| Modular facade detail kits (final P3 detail in UE) | Decision made: detail in UE with Nanite displacement, decals and Fab props | Not started | all |

### 1.2 Characters (R2)

Placeholders imported 2026-11-05 from free Fab packs into `Content/KochSimulator/Characters/Vendor/` (see `docs/lore/proposals/characters/02_asset_plan.md`, "Import status").

| Asset | Now | Status | Fix / next step |
|---|---|---|---|
| Companion NPC prototype (follows the player, T key) | UE mannequin rig, `AKochCompanion` | **Done (prototype)** | Story companions need a non-lethal "downed" mode |
| Urban Security Officer (guard placeholder) | Skeletal mesh + skeleton + physics + 4 anims, 180 cm | In progress | Textures missing from the FBX: re-link maps |
| Office Worker 4 (staff placeholder) | Skeletal mesh + 3 anims, 184 cm | In progress | Import `textures/`, wire 10 material instances |
| Office Worker 3 | glTF split into 9 skeletal meshes | In progress | Re-import from the Blender format as one mesh |
| NoEdge Male / Female (placeholders for mains) | Skeletal mesh + textures, 186 / 165 cm | In progress | Retarget to the UE Manny skeleton |
| City Sample Crowds, MetaHuman Crowd Sample, Game Animation Sample, Renderpeople | In the team Fab library; UE-format only | Not started | Add via the Fab panel / Epic Launcher, migrate content |
| Arsen (hero), full-body first person | Look defined (cast bible) | Not started | MetaHuman Creator; mask as a static mesh on a head socket |
| Azamat (checkpoint guard, M01) | Look defined | Not started | MetaHuman + re-tinted uniform |
| Nurai, Isa, Temirov, Ermekova, Lind | Looks defined | Not started | MetaHuman Creator, in mission order |
| Enemy archetypes: checkpoint, patrol, tactical, elite | Archetype table written | Not started | One shared uniform, 4–6 faces, material variants |
| Civilian crowd (Central Asian MetaHuman collection, 12–16 faces) | Plan only | Not started | MetaHuman Collection + Mass; fallback City Sample |
| Takedown and pepper-spray animations | Plan only | Not started | Video mocap (paired montage Arsen + Azamat) |

### 1.3 Weapons and props (R3, with R2)

| Asset | Now | Status |
|---|---|---|
| Rifle: draw (Q), fire, reload (R), ejected cases | `BP_Rifle_AK`, `AM_Rifle_Reload`, `SM_Shell_762`, `M_Brass`; uses the template's white rifle mesh | **Done (prototype)** |
| Final rifle mesh (AK-type, worn) | — | Not started |
| Combat knife | `Weapons/Vendor/CombatKnife` imported; ~430 cm long, needs ≈ 0.07 scale | In progress |
| Guitar case (holster for the rifle) | — | Not started |
| Pepper spray | — | Not started |
| Arsen's mask | — | Not started |
| Story props and 20 collectibles (letters, logs, profiles, piano, monitors) | Listed in `docs/lore/proposals/story/03_systems.md` | Not started |
| In-game review marks (LMB drop, RMB remove; dev tool) | `KochReviewMarksComponent` | **Done** (tool) |

### 1.4 UI (R4)

| Asset | Now | Status |
|---|---|---|
| HUD mockup: KOCH ALERT, objective, health, ammo | Laid over an engine frame (`Checkpoint4_Pitch_and_Technical_Bridge/02_ui_mockup_dossier.png`) | **Done (mockup)** |
| In-game HUD bars (health, ammo) | Amber bars in the build (`docs/checkpoints/cp4/keyart.jpg`) | In progress |
| Working KOCH ALERT meter (levels 0–4) | Rules written in `03_systems.md` | Not started |
| Objective panel and String Tables | — | Not started |
| Main menu and settings (scalability, TSR / DLSS / FSR) | Mockup in the pitch deck | Not started |
| Subtitles, phone/radio portraits | — | Not started |
| Face-terminal screen states ("LOOK AT THE CAMERA", refusal, "WELCOME") | Text drafted (proposal) | Not started |
| Evidence journal (collectibles) | — | Not started |
| Font switch to the Art Bible fonts (Plex, Inter, Unbounded) | — | Not started |

### 1.5 Audio (R4)

There is no `Content/KochSimulator/Audio/` folder yet. All audio is **Not started**; per-location sound lists exist in `docs/lore/proposals/story/02_locations.md`.

| Asset | Status |
|---|---|
| Ambience beds: street and trolleybus wires, alley birds, garden wind, Block C LED hum, basement fans | Not started |
| Rifle (fire, tail, reload, casings), knife, pepper spray | Not started (template sounds only, if any) |
| Face terminal chime / refusal buzz, turnstile beep | Not started |
| KOCH PA announcer lines, guard radio chatter | Not started |
| Music: "the old song" theme (guitar / piano), search and combat layers | Not started |
| Dialogue VO (team voices) | Not started |

### 1.6 Narrative (R4, lore author)

| Asset | Status |
|---|---|
| Canon summary (human-written, opening draft) | **Done** (`docs/lore/canon/00_canon_summary.md`) |
| Story proposal: premise, walkthrough M00–M08, locations, systems, dialogue outlines | In progress (proposal, needs human approval) |
| Cast bible, enemy/civilian archetypes, character asset plan | In progress (proposal, 2026-11-05) |
| Ink dialogue (`Narrative/Ink/`) for M01 Azamat scene | Not started (Inkpot plugin is installed as a submodule) |
| Quest DataTables from CSV | Not started |

---

## 2. Shot list (cinematics and key frames)

All cutscenes are short and in-engine (Sequencer). No cutscene is built yet; locations marked "exists" have a greybox.

| ID | Mission | Shot | Length | Camera / composition (Art Bible §5) | Location | Status |
|---|---|---|---|---|---|---|
| S00-1 | M00 | Cold open: dawn over apartment blocks, KOCH rooftop ad, alarm at 06:40 | 20 s | 24 mm wide, slow push; ad = only red | Context city (exists), apartment (not built) | Not started |
| S00-2 | M00 | Bus ride, radio news about the signing, Nurai call | 60–90 s, in-game | Seated first person, window frames the street | Bus (not built) | Not started |
| S01-1 | M01 | Face terminal refusal: "FACE NOT VISIBLE" | in-game | Framed through the turnstile bars; screen brightest | Gate (exists) | Not started |
| S01-2 | M01 | Azamat questions Arsen, then pepper spray and knife takedown | 2 camera locks | Close two-shot at 35 mm; mask on the upper third | Gate booth (exists) | Not started |
| S04-1 | M04 | Room 203 reveal: 8 screens of face grids | in-game | Doorway frame; faces light the room | Block C F2 (greybox) | Not started |
| S05-1 | M05 | Push-in on Ermekova | 5 s | 50 mm push, low key, dormer light | C attic (partial) | Not started |
| S06-1 | M06 | Montage: cameras go dark across the campus | 10 s | CCTV POVs, high angles, red lights cut out one by one | Campus (exists) | Not started |
| S07-1 | M07 | Reunion with Isa in Clinic room 4 | 15 s camera lock | Cold light, 35 mm, hold | Block A Clinic (not built) | Not started |
| S08-1 | M08 | Lind's broadcast speech before delegates | 40 s | Low angle on Lind, live camera tally light as focal point | Assembly Hall (not built) | Not started |
| S08-2 | M08 | Ending A: unmasking on camera, walk out through the face gate ("IDENTIFIED") | 60–75 s | Close-up 85 mm on the face; gate in noon sun | Assembly Hall + gate | Not started |
| S08-3 | M08 | Ending B: shot on air, escape via the north-east service gate, bus radio, mask back on | 60–75 s | Hand-held, then bus window | Assembly Hall + NE booth (exists) + bus | Not started |
| KF-1 | pitch | Key art: alley to the gate canopy | still | Leading lines, rule of thirds | Gate alley | **Done** (`docs/checkpoints/cp4/keyart.jpg`) |
| KF-2 | pitch | Yard, Block C hall, environment sheet, top-down blockout | stills | — | Prologue zones | **Done** (`docs/checkpoints/cp4/`, `Checkpoint4_Pitch_and_Technical_Bridge/`) |

---

## 3. Pipeline notes

### 3.1 Engine and software

| Tool | Version | Use |
|---|---|---|
| Unreal Engine | **5.8.3** (exact, everyone) | C++ project `KochSimulator` from the First Person template (shooter variant). Lumen software RT (High), Nanite, Virtual Shadow Maps, TSR (DLSS / FSR optional, no frame generation), World Partition + One File Per Actor, 1 uu = 1 cm |
| Blender | 5.2 | Campus greybox from photos and measurements, 1:1 in metres; mesh fixes for vendor assets |
| Python (uv) | — | Geo data (OSM, terrain), spec builders, UE import scripts, QA (walk holes, z-fight, thin walls), perf capture |
| RealityScan | 2.2 | Site photogrammetry reference; optional team face scans |
| MetaHuman Creator / Animator | in-engine 5.8 | Characters and facial animation |
| Mixamo, Rokoko Vision / QuickMagic (free tiers) | — | Stand-in animations, video mocap |
| Ink + Inkpot | plugin (submodule) | Dialogue |
| Git + Git LFS + UEGitPlugin | — | Source control and file locking |
| Claude Code with Unreal MCP and Blender MCP | — | AI agents drive the editor and Blender under the rules in `AGENTS.md` |

Performance target: **stable 60 fps at 1080p, ≤ 7 GB VRAM** on an RTX 3070 Ti Laptop and an RX 6750 GRE. Measured 2026-10-28 on an RTX 3070 Laptop, whole campus: 54.5 fps; 60.6 fps with the skinned wind trees hidden (they cost ~2 ms). Measurement script: `Scripts/Unreal/perf_capture.py`.

### 3.2 Environment: Blender spec → FBX → UE

1. **Spec.** Every building or site area is a JSON spec in `Art/Blender/Specs/` (each element carries its evidence and a confidence; low confidence shows orange in the greybox). The `.blend` is a build artifact.
2. **Build.** `Scripts/Blender/build_all.py` rebuilds the whole scene, with a manifold and naming validator; QA scripts check walk holes, coincident faces (z-fighting) and walls thinner than 10 cm (Lumen).
3. **Export.** `Scripts/Blender/ue_prep/run.py` exports deduplicated FBX meshes with collision (UCX) and a `manifest.json`; pieces ≤ ~15 m for Lumen.
4. **Import.** `Scripts/Unreal/import_greybox.py` imports through Interchange into `Content/KochSimulator/Greybox/` with Nanite on, and places the actors in the level.
5. **Level passes.** `fix_site.py`, `apply_facades.py`, `place_vegetation.py`, `place_props.py`, `place_far_ground.py` dress the level without touching the source model.
6. **Review.** In-game marks (LMB/RMB) and photo comparisons go back into the specs (e.g. `Scripts/Unreal/bench_flips.json`).

### 3.3 Characters

- **Main path:** MetaHuman Creator (in-engine) recipes from the cast bible → MetaHuman body on the Manny-compatible skeleton → animations from Manny (Game Animation Sample, Mixamo, mocap) through the IK Retargeter (`RTG_Manny_To_MetaHuman`).
- **Optional:** phone scan → RealityScan → Mesh to MetaHuman for team members' faces (allowed since 2026-10-28; raw captures are never committed).
- **Vendor imports (Fab):** the pack stays untouched in its own vendor folder (`Characters/Vendor/<Pack>/`, `Weapons/Vendor/<Pack>/`); our assembled assets (BP, MI, ABP, retargeted anims) live under `Characters/<Name>/`, `Characters/Enemies/<Archetype>/`, `Characters/Civilians/<Archetype>/`. Check scale (cm), skeleton and textures on import (see the 2026-11-05 fixes above).
- **Performance tiers:** T0 close-up (max 2 per frame, strand hair only in cutscenes), T1 mid (max 12 animated, card hair), T2 crowd (Mass, max 60 visible). Character budget ≤ 1.5 ms GPU, ≤ 1.2 GB VRAM.
- Every enemy skeleton exposes a `HandGrip_R` socket (needed by the shooter NPC code).

### 3.4 Folders and naming

```
Content/KochSimulator/
  Characters/   Vendor/<Pack>/, <Name>/, Enemies/<Archetype>/, Civilians/<Archetype>/, Shared/Animations/
  Environment/  Facades/, FarGround/, Kerbs/, Props/, Surfaces/, Vegetation/
  Greybox/      imported Blender meshes and materials
  Maps/         L_GreyboxTest (+ HLOD layers)
  Weapons/      BP_Rifle_AK, AM_Rifle_Reload, Vendor/CombatKnife
  UI/, Audio/   (to be created by R4)
Content/Developers/<name>/   personal sandboxes, never referenced by shipping content
```

- Naming follows Allar's UE5 style guide: `SM_` static mesh, `SK_` skeletal mesh, `SKEL_` skeleton, `PHYS_` physics asset, `M_` / `MI_` materials, `T_` textures, `BP_` blueprints, `ABP_` anim BP, `AM_` montage, `A_` anim sequence, `BS_` blend space, `IK_` / `RTG_` retarget, `L_` maps, `IA_` input actions.
- Open team decision: Allar's guide uses `S_` for static meshes; we use Epic's `SM_` and should confirm it in `docs/decisions.md`.
- No real names in any asset or file name. Never rename by changing case only (Linux is case-sensitive).

### 3.5 Source control

- `.uasset` / `.umap` are in Git LFS and lockable: run `git lfs locks`, lock (UEGitPlugin "Check Out" or `git lfs lock`), push and unlock the same day.
- One task = one short branch `feat/<role>/<slug>`; small PRs to `main`.
- Never committed: `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`, raw site captures.
- Open team decision: LFS host (GitHub with a paid budget vs Azure DevOps); the free GitHub LFS quota (10 GiB) is too small.

---

## 4. Team roles

| Role | Owner | Owns | Midterm state |
|---|---|---|---|
| **R1 World / Map** | TODO: name | Environment, maps, terrain, foliage, lighting, post-process, HLOD | Campus 1:1 greybox built and imported, context city, ground fixes, street furniture, first material and lighting pass, perf measurement |
| **R2 Characters & Animation** | TODO: name | Characters, MetaHumans, anim BPs, mocap, retargeting | Cast bible and character asset plan written; 6 free placeholder packs imported (fixes pending); no final character yet |
| **R3 Gameplay & Combat** | TODO: name | Player, weapons, enemy AI, damage, interaction, physics (C++) | Rifle with reload and ejected cases, companion prototype, review-marks tool; enemy AI and takedown not started |
| **R4 Narrative, UI & Integration** | TODO: name | Ink dialogue, quests, HUD, menus, settings, audio, packaging | UE project set up, HUD mockup and amber HUD bars; story proposal written; menu, audio, Ink and packaging not started |

Shared files (`Source/*/Core`, `Config/`, `.uproject`, `AGENTS.md`) need two approvals.

---

## 5. Plan for the six weeks after the midterm

**Goal:** a playable **vertical slice (~5 minutes)** from the bus stop through the checkpoint and the alley to the Block C hall, covering the end of M00 and all of M01 at near-final quality, with a packaged build running at 60 fps on both reference machines.

| Week | Dates | R1 World | R2 Characters | R3 Gameplay | R4 Narrative / UI / Audio | Exit check |
|---|---|---|---|---|---|---|
| W1 | Nov 10–16 | Static trees with WPO wind (recover the ~2 ms); street and crossing final layout | Fix vendor imports (textures, single mesh, retarget to Manny); add Game Animation Sample | Interaction component (doors, pickups); health / damage interfaces | Main menu + settings shell (scalability, upscaler); HUD font switch | Whole campus ≥ 60 fps on machine A |
| W2 | Nov 17–23 | Checkpoint booth, canopy and turnstile meshes; KOCH signage set v1 | Arsen in MetaHuman Creator, full-body first person (head/hair/mask hidden to the camera) | Holster/draw with the guitar case; pepper spray; knife | Ink pipeline; Azamat scene draft (`TODO_LORE` lines); face-terminal screen widget | Walk the route as Arsen |
| W3 | Nov 24–30 | Gate and alley materials, decals and wear pass; lighting for the morning | Azamat in MetaHuman; guard uniform material variants | Face-gate refusal logic; KOCH alert meter 0–3; patrol pair AI MVP (StateTree) | Alert meter HUD; objective panel and String Tables; first ambience beds (street, gate) | M01 refusal plays end to end |
| W4 | Dec 1–7 | Block C hall and stairs set dressing; navmesh and cover for the alley | Takedown mocap (paired montage) and pepper-spray reaction; 4–6 guard faces | Paired takedown with motion warping; body drag; patrol shooting and cover | Guard radio and PA lines (team VO); rifle and terminal SFX | Full M01 encounter playable |
| W5 | Dec 8–14 | Lighting and post polish; HLOD; profile on both machines | Civilian queue at the gate (placeholders + 2–4 MetaHumans); LOD setup | Bug fixing, tuning from playtests | Packaged build + smoke test script; subtitles | Packaged slice ≥ 60 fps on A and B |
| W6 | Dec 15–21 | Final screenshots and capture | Polish faces and hair for the cutscene | Polish | Trailer capture, slice build, documentation update | Vertical slice demo |

Risks
- **Characters are the largest gap:** no final character exists yet. If MetaHuman work slips, the slice ships with the imported Fab placeholders re-tinted to the Art Bible palette.
- **Performance:** the campus is already at 54.5 fps before characters; trees must be fixed first (W1) and every character scene measured.
- **Lore approval:** the story is a proposal; Azamat's dialogue stays `TODO_LORE` until the lore author approves it.
- **Block A / B interiors** are out of scope for the slice (needed for M02, M07, M08 later).

---

## 6. What we need from the instructor and the team

**From the instructor**
- Feedback on the art direction: palette roles (KOCH red vs amber), silhouettes, and whether the "corporation is the only clean thing" pillar reads in the key frames.
- Agreement on the scope: is the vertical slice (end of M00 + M01, bus stop to the Block C hall) the right target for the final submission?
- Advice on the cutscene composition for the M01 confrontation and the M08 broadcast.

**From the team**
- Owner names for R1–R4 in `AGENTS.md`.
- The lore author's approval (or edits) of the story and cast proposals, especially the mask type, season and Azamat's fate.
- Decisions: LFS host; `SM_` vs `S_` prefix; approval of the optional paid character bundle (about $97: mask, uniform, suit, hair cards, guitar case, pepper spray, passenger mocap).
- Access to reference machine B (RX 6750 GRE) once a week for profiling.
- Voices for Azamat, Arsen, the PA announcer and guard radio, and a 2-hour mocap session for the takedown.
