@AGENTS.md
@docs/lore/canon/00_canon_summary.md

# Claude Code specifics
- **Your role.** `CLAUDE.local.md` (personal, gitignored) states the user's role and machine. If it's missing, ask once and suggest copying `docs/roles/CLAUDE.local.md.example`.
- **Skills** in `.claude/skills/` load on demand:
  - `/research`: before decisions and before writing systems.
  - `/realism-check`: before finishing visual work.
  - `ue-*` (27 UE C++ skills, audited against engine source): project facts for them are in `.agents/ue-project-context.md`.
  - Epic's plugin (`.claude/settings.json`) adds `unreal-mcp` and `create-toolset`.
- **MCP servers** (`.mcp.json`):
  - `unreal-mcp` (Epic, the editor must be running with the server started).
  - `blender` (`mcp-for-blender`; the Blender add-on must be running).
  - If one is down, say so and don't guess.
- **Driving the editor.** Follow the `unreal-mcp` skill. Save and commit first, make one change at a time, and read back or screenshot every change (some 5.8 tools fail silently). Never use `--dangerously-skip-permissions`.
- **Editor gotchas (UE 5.8, found the hard way):**
  - Any modal dialog freezes MCP calls (timeouts): "Save Content" on quit, "Restore Packages" after a kill, PIE compile errors, memory warnings. Save dirty packages before quitting; before relaunching after a kill, move `Saved/Autosaves` away.
  - After a crash, `CrashReportClient` can keep port 8000, so the next editor's MCP can't bind: kill it.
  - Committed `.uasset`/`.umap` files are read-only (LFS lockable): `chmod u+w` before editing and check every save returns True.
  - Never call blocking editor APIs (MetaHuman, mesh builds) from a Slate tick callback: re-entrancy deadlocks the editor.
  - Blend spaces made from Python play the bind pose until opened once in the asset editor (`AssetEditorSubsystem.open_editor_for_assets`, then save).
  - MetaHuman Creator: `can_build_meta_human` needs both the cloud rig and the textures; request one character at a time (parallel requests fail); save the build with `save_dirty_packages`; builds hang while the screen is locked.
  - Python `set_editor_property` on asset structs: pass `PropertyAccessChangeNotifyMode.ALWAYS` when PostEditChange must run.
  - Measuring fps: the first `-game` run after a pull builds distance fields and stutters; warm it up ~10 min, then use `Scripts/Unreal/perf_capture.py` (absolute path). On a background Mac set `EditorPerformanceSettings.bThrottleCPUWhenNotForeground=False`.
- **VibeUE** (landscape, foliage, splines, Python services). Before the first VibeUE call in a session, read `Plugins/VibeUE/Content/samples/AGENTS.md.sample`, then use `ListSkills`/`GetSkills` via `AgentSkillToolset`.
- **Blender batches:** headless `blender -b -P Scripts/Blender/<script>.py`.
- **Research.** Broad research runs in the `researcher` subagent (Opus, high effort) with precise parallel queries; keep only the conclusion.
- **Workflows (multi-agent orchestration):** only when the user explicitly asks, and always within the AGENTS.md budget: at most 4 agents total and no Verify phase. If a workflow is running, never stop it or relaunch it.
- **Reply in the user's language.** Code, commits and docs are in English.
- **When compacting,** keep: modified files, build/test commands, and open decisions.
