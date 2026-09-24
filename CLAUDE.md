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
- **VibeUE** (landscape, foliage, splines, Python services). Before the first VibeUE call in a session, read `Plugins/VibeUE/Content/samples/AGENTS.md.sample`, then use `ListSkills`/`GetSkills` via `AgentSkillToolset`.
- **Blender batches:** headless `blender -b -P Scripts/Blender/<script>.py`.
- **Research.** Broad research runs in a subagent with precise parallel queries; keep only the conclusion.
- **Reply in the user's language.** Code, commits and docs are in English.
- **When compacting,** keep: modified files, build/test commands, and open decisions.
