# KOCH-SIMULATOR

A story-driven first-person shooter / GTA-like sandbox set in the photoreal headquarters campus of KOCH, a fictional evil corporation. Built in Unreal Engine 5.8.3 by a team of four.

Rules: [AGENTS.md](AGENTS.md) · Plan: [docs/STRATEGY.md](docs/STRATEGY.md) · Roles: [docs/roles/](docs/roles/) · Decisions: [docs/decisions.md](docs/decisions.md)

![Key art: the KOCH yard in UE 5.8](docs/checkpoints/cp4/keyart.jpg)

## Status (2026-10-29)
- **World (R1):** the whole campus is a 1:1 greybox in Blender (`Art/Blender/KOCH_Campus_Greybox.blend`), built from JSON specs, and imported into UE as `Content/KochSimulator/Maps/L_GreyboxTest` (2324 Nanite meshes, 7474 actors).
- **UE project (R4):** `KochSimulator.uproject` from the C++ First Person template, with a first pass of materials, vegetation and lighting.
- **Gameplay (prototype):** rifle with reload and ejected cases (Q), companion that follows the player (T), in-game review marks (LMB/RMB).
- **Characters:** not started. Pipeline chosen: phone scan → RealityScan → Mesh to MetaHuman.

## Checkpoint 4

### Part 1: pitch assets
- **Key art:** the image above, a real frame from the UE 5.8 build (Lumen + Nanite, 1080p).
- **UI mockups:** gameplay HUD (health, objective, KOCH alert meter, ammo) and main menu, both laid over in-engine frames. They are in the team's pitch deck.
- **Environment sheet:** three prologue zones and the material palette.

| Yard | Block C hall |
|---|---|
| ![Yard](docs/checkpoints/cp4/yard.jpg) | ![Block C hall](docs/checkpoints/cp4/block_c_hall.jpg) |

Palette, sampled from the engine and site photos (check against the Art Bible): render `#D6C4A0`, pilasters `#782C26`, plinth tile `#A0432F`, paving `#C1B8A7`, terrazzo `#CFCAC0`, Block C panels `#6E7FD0`, KOCH red `#D42A1E`, HUD amber `#FFB000`.

### Part 2: bridge to production

**Asset list:** the 5-minute vertical slice, from the street through the checkpoint and the yard to the Block C hall.

| Asset | Now | Status |
|---|---|---|
| Campus 1:1, blocks A–D | Blender greybox | Done |
| Import into UE 5.8 | `L_GreyboxTest` | Done |
| Street furniture: benches, bins | UE kit | Done |
| Rifle: fire, reload, ejected cases | UE prototype | Done |
| Street and pedestrian crossing | greybox | In progress |
| Checkpoint: booth, canopy, gate | greybox | In progress |
| Garden: hedges, gazebos, trees | UE vegetation | In progress |
| Block C ground floor: hall, stairs, WC | greybox | In progress |
| PBR materials for facades and paving | first pass | In progress |
| Lighting and post-process | first pass | In progress |
| KOCH staff NPCs | mannequins | In progress |
| Companion | UE prototype | In progress |
| HUD | bars + mockup | In progress |
| Hero (long hair, mask) | pipeline chosen | Not started |
| Checkpoint guard | — | Not started |
| Guitar case with the gun | — | Not started |
| Pepper spray, knife | — | Not started |
| Turnstiles with face check | — | Not started |
| Main menu and settings | mockup | Not started |
| Guard dialogue (Ink) | — | Not started |

**Blockout:** top view of the Blender greybox. The prologue route runs: street crossing → checkpoint → alley between B and A → plaza → Block C entrance.

![Blockout: top view of the greybox](docs/checkpoints/cp4/blockout.jpg)

**Pipeline:**
- **Engine:** Unreal Engine 5.8.3, C++, with Lumen, Nanite and World Partition + One File Per Actor.
- **Environment:**
  1. Built in Blender 5.2 from photos and measurements, 1:1 in metres. Every building is a JSON spec in `Art/Blender/Specs/`, and `Scripts/Blender/build_all.py` rebuilds the scene from them.
  2. `Scripts/Blender/ue_prep/run.py` exports deduplicated FBX meshes with collision and a `manifest.json`.
  3. `Scripts/Unreal/import_greybox.py` imports them into `Content/KochSimulator/Greybox/` with Nanite on and places them in the level.
- **Characters:** scanned with a phone, reconstructed in RealityScan, converted with Mesh to MetaHuman.
- **Naming:** Allar's UE style guide: `SM_` meshes, `M_`/`MI_` materials, `T_` textures, `BP_` blueprints.
- **Folders:** everything under `Content/KochSimulator/<type>/`; sandboxes in `Content/Developers/<name>/`.
- **Source control:** `.uasset`/`.umap` live in Git LFS and are locked before editing.

**Performance target:** stable 60 fps at 1080p, at most 7 GB VRAM, on an RTX 3070 Ti Laptop and an RX 6750 GRE.
- **Upscaling:** TSR by default. DLSS Super Resolution (NVIDIA) and FSR (AMD) are options. No frame generation.
- **Measured (2026-10-28, RTX 3070 Laptop, whole campus):** 54.5 fps. With the skinned wind trees hidden: 60.6 fps. The trees cost about 2 ms on the render thread.

| GPU pass | Budget, ms |
|---|---|
| Nanite and base | 3–4 |
| Lumen (software) | ≤ 5 |
| Virtual Shadow Maps | 2–3 |
| Translucency and FX | ≤ 1.5 |
| Post | ~1.5 |
| Reserve | ≥ 2 |

## Setup (every machine)
1. **UE 5.8.3.** Windows: Epic Launcher. Linux: the prebuilt zip from unrealengine.com/linux.
2. **Clone with plugins:**
   ```bash
   git lfs install
   git clone --recurse-submodules git@github.com:TR4SC3ND3NT/KOCH-SIMULATOR.git
   git config lfs.locksverify true        # Windows also: git config core.longpaths true
   ```
   - Plugins come in as submodules under `Plugins/`: VibeUE, UEGitPlugin (dev) and Inkpot. After pulling, run `git submodule update --init --recursive`.
   - On machines without Unreal (code and docs only), skip the LFS binaries: `GIT_LFS_SKIP_SMUDGE=1 git clone …`.
3. **Claude Code.** Open the repo in Claude Code and accept:
   - the project MCP servers (`.mcp.json`);
   - the Epic plugin install prompt (`unreal-engine-skills-for-claude-code`).
   - Windows needs Git Bash for the plugin hook.
4. **Blender MCP** (R1/R2, asset work):
   - install `uv` (https://docs.astral.sh/uv/);
   - run `uvx mcp-for-blender install-addon`;
   - start the add-on server in Blender.
5. **Personal context.** Copy `docs/roles/CLAUDE.local.md.example` to `CLAUDE.local.md` and fill in your role and machine.
6. **More web searches.** Recommended, so research isn't capped: `export CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION=1000`.
7. **Unreal MCP.**
   - Open `KochSimulator.uproject`. The `ModelContextProtocol` and `AllToolsets` plugins are already enabled.
   - Start the server with `ModelContextProtocol.StartServer`.
   - For auto-start, set `bAutoStartServer=True` under `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]`.

Third-party: `.claude/skills/ue-*` from quodsoler/unreal-engine-skills (MIT); VibeUE, UEGitPlugin and Inkpot (MIT, see each plugin). Map data © OpenStreetMap contributors (ODbL).
