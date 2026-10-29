# KOCH-SIMULATOR

<!-- Rules for every AI agent and human. Keep under ~100 lines: every line must prevent a real mistake. Details live in docs/ and .claude/skills/. -->

Story-driven first-person **shooter / action sandbox** (GTA-like) in **Unreal Engine 5.8.3** (exact version for everyone).
- **Setting:** the headquarters campus of **KOCH**, a fictional evil corporation. The architecture is a faithful 1:1 recreation of a real campus, and the layout must match reality (grading requirement).
- **In-game it is never a university,** and the real place is never named.
- **Block C** is the detailed, physics-interactive interior.
- **Team:** 4 people, one agent each.

## Priorities (in order)
1. **Photoreal look.** Target GTA-6-level realism: correct scale, physically based materials, wear and dirt, dense set dressing, cinematic lighting.
2. **Performance.** 1080p output, **stable ≥ 60 fps** on both reference machines, VRAM ≤ 7 GB:
   - A: RTX 3070 Ti Laptop 8 GB
   - B: RX 6750 GRE 12 GB
3. **Token economy: save on prose, never on code.** Code quality, research and verification get whatever they need. Chat replies, docs and explanations are kept minimal.

## IMPORTANT: research and reuse before building
- **Research.** Before any non-trivial technical choice (render setting, algorithm, plugin, pipeline, AI, physics, architecture), research it (skill `/research`). Compare 2–3 options on realism vs GPU ms/VRAM at 1080p.
- **No time limit on hard problems.** Depth scales with difficulty: think, research and iterate as long as the problem needs. Never rush a hard task to finish sooner.
- **Reuse.** Finding a proven solution first saves development time. Before writing a system, search online for the best known algorithm, method or implementation and adapt/optimize it for our task:
  - Epic samples/templates
  - free Fab plugins
  - MIT/Apache GitHub code
  - papers, talks, forum/doc snippets
  Check the license and 5.8 compatibility, and credit the source in a code comment. Only if nothing fits, write it ourselves, to the same quality bar.
- **Verify APIs.** Never invent API names; check them against the docs or engine headers.

## IMPORTANT: agent and token budget (hard limits)
- **Max 4 subagents per task, in total,** including every agent inside a workflow. Never more, and no nested fan-out.
- **Subagents run Opus at high effort.** Use the `researcher` agent (`.claude/agents/researcher.md`) for research.
- **No verify, adversarial-review or "second opinion" phases or agents** unless the user explicitly asks. Verification means build, test, and a screenshot compared with the reference.
- **Never stop, kill or relaunch a running agent or workflow.** Let it finish and reuse its result. Never redo work that already has a result.
- **State the agent count first.** Before any multi-agent run, say in one line how many agents and why.
- **Why this rule exists.** On 2026-09-24 a research workflow spent about 690k tokens on 4 agents (186k + 133k + 168k + 204k), then started 3 verify agents. When told to skip verify, it killed them and the 204k-token agent that was almost done, then relaunched that agent. Those tokens were thrown away twice.

## Output discipline
- **Replies to the user are short.** Give the result, what you verified (command/output/screenshot), and the next step or a blocking question. No recaps and no tables unless asked.
- **No new .md files or long docs unless the user asks.** Only these exceptions:
  - one line in `docs/decisions.md` for choices that affect the frame budget or architecture
  - questions in `docs/lore/open_questions.md`.
- **Code comments: short and precise, so no teammate gets lost.**
  - One line at the top of each file/class: what it is, and who uses it.
  - Brief notes on non-obvious *why*, units (cm, degrees, seconds) and gotchas.
  - A source link for adapted code.
  - No essays, and no comments that restate the code.
- **Code quality is non-negotiable.** Code must be correct, robust and fast at runtime for the 60 fps budget (no per-frame allocations, no Tick where events/timers work, cached lookups). It must compile warning-free on Linux and Windows.

## Lore
- **IMPORTANT: no real names in the game.** Use only KOCH (or other fictional) branding everywhere in the game: text, signage, logos, textures, decals, asset/file names, builds.
  - Never use "Ala-Too", "AIU", "IAAU", real logos, slogans or street names.
  - The real name may appear only in `docs/reference/`.
- **Human-only canon.** `docs/lore/canon/` is written by humans only. Never edit it and never invent canon.
- **Missing lore:** use `TODO_LORE:` placeholders and add a question to `docs/lore/open_questions.md`.
- **Dialogue:** Ink (`Narrative/Ink/`). Quest/item data: CSV → DataTables. Player-facing text goes in String Tables.

## Tech defaults (change only with a line in docs/decisions.md)
- **Rendering:**
  - Lumen software RT at High; Nanite on all static meshes and foliage; Virtual Shadow Maps.
  - TSR as the baseline, with DLSS SR (NVIDIA) and FSR (AMD) as options. No frame generation.
  - Hardware RT only as an "Ultra" option.
- **GPU budget at 60 fps:**

  | Pass | Budget |
  |---|---|
  | Nanite/base | 3–4 ms |
  | Lumen | ≤ 5 ms |
  | Virtual Shadow Maps | 2–3 ms |
  | Translucency/FX | ≤ 1.5 ms |
  | Post | ~1.5 ms |
  | Reserve | ≥ 2 ms |

  Verify with `stat gpu` / Unreal Insights on a reference machine.
- **Logic:**
  - Logic in C++. Blueprints are thin children (asset refs, tuning). No Level Blueprint logic.
  - Enhanced Input, Gameplay Tags, components and interfaces; StateTree/BT for AI; Chaos physics. No GAS unless decided.
- **World:**
  - World Partition + One File Per Actor. 1 uu = 1 cm, true 1:1 scale.
  - Campus facts and measurements are in `docs/reference/campus.md`.
- **Naming:**
  - Allar UE5 style guide.
  - Everything under `Content/KochSimulator/`; sandboxes in `Content/Developers/<name>/`.
  - Never rename by changing case only (Linux is case-sensitive).

## Roles (owners TBD, each person states theirs in CLAUDE.local.md)
| Role | Owns |
|---|---|
| R1 World/Map | Environment, Maps, landscape, PCG, foliage, lighting, `Source/*/World` |
| R2 Characters & Animation | Characters, MetaHumans, AnimBPs, mocap, retargeting |
| R3 Gameplay & Combat | `Source/*/{Player,Combat,AI,Interaction}`: weapons, enemy AI, damage, physics interaction |
| R4 Narrative, UI & Integration | `Narrative/`, UI, Audio, `Source/*/{Narrative,UI}`, settings menu, packaging |

- Stay in your role's folders.
- Shared files need approval from 2 people: `Source/*/Core`, `Config/`, `.uproject`, `AGENTS.md`, `CLAUDE.md`.
- Role details: `docs/roles/`.

## Git
- **Locking.** `.uasset`/`.umap` are LFS-lockable:
  - run `git lfs locks` before editing
  - lock the file (UEGitPlugin "Check Out" or `git lfs lock`)
  - push and unlock the same day.
- **Branches.** One task = one short branch, `feat/<role>/<slug>`. PR to `main` daily; keep PRs small.
- **No AI attribution, ever.** Commits, PRs, docs and code carry no `Co-Authored-By`, `Claude-Session`, "Generated with …" or any other Claude/AI credit, from anyone.
  - `.claude/settings.json` turns Claude Code's attribution off (`attribution` empty, `sessionUrl` false); keep it that way.
  - Check `git log -1` before every push and strip any such line.
- **Never commit:** `Binaries/ Intermediate/ Saved/ DerivedDataCache/`, or raw site captures (they contain people).
- **Editors.** One editor per person; never run two agents against one editor.

## Build and test (project not created yet; names are placeholders)
```bash
"$UE_ROOT/Engine/Build/BatchFiles/Linux/Build.sh" KochSimulatorEditor Linux Development -Project="$PWD/KochSimulator.uproject" -WaitMutex
"%UE_ROOT%\Engine\Build\BatchFiles\Build.bat" KochSimulatorEditor Win64 Development -Project="%CD%\KochSimulator.uproject" -WaitMutex
UnrealEditor-Cmd KochSimulator.uproject -ExecCmds="Automation RunTests KochSimulator;Quit" -unattended -nullrhi -nosplash
```

- **Header or reflected (UPROPERTY/UFUNCTION) changes:** close the editor and do a full build. Live Coding is Windows-only and for `.cpp`-only changes.
- **Done means:**
  - it compiles
  - tests pass
  - it was checked in PIE
  - the budget was checked if rendering or content changed.
