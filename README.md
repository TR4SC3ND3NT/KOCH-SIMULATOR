# KOCH-SIMULATOR

A story-driven first-person shooter set in the photoreal headquarters campus of KOCH, a fictional evil corporation. Built in Unreal Engine 5.8.3 by a team of four using Claude Code.

Rules: [AGENTS.md](AGENTS.md) · Plan: [docs/STRATEGY.md](docs/STRATEGY.md) · Roles: [docs/roles/](docs/roles/) · Decisions: [docs/decisions.md](docs/decisions.md)

## Setup (every machine)
1. **UE 5.8.3.** Windows: Epic Launcher. Linux: the prebuilt zip from unrealengine.com/linux.
2. **Clone with plugins:**
   ```bash
   git lfs install
   git clone --recurse-submodules git@github.com:TR4SC3ND3NT/KOCH-SIMULATOR.git
   git config lfs.locksverify true        # Windows also: git config core.longpaths true
   ```
   Plugins come in as submodules under `Plugins/`: VibeUE, UEGitPlugin (dev), Inkpot. After pulling, run `git submodule update --init --recursive`.
3. **Claude Code.** Open the repo in Claude Code and accept:
   - the project MCP servers (`.mcp.json`)
   - the Epic plugin install prompt (`unreal-engine-skills-for-claude-code`).
   - Windows needs Git Bash for the plugin hook.
4. **Blender MCP** (R1/R2, asset work):
   - install `uv` (https://docs.astral.sh/uv/)
   - run `uvx mcp-for-blender install-addon`
   - in Blender, start the add-on server.
5. **Personal context.** Copy `docs/roles/CLAUDE.local.md.example` to `CLAUDE.local.md` and fill in your role and machine.
6. **More web searches.** Recommended, so research isn't capped: `export CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION=1000`.
7. **Unreal MCP.** Once the UE project exists: open it (the `ModelContextProtocol` + `AllToolsets` plugins are enabled in `.uproject`) and start the server with `ModelContextProtocol.StartServer`. For auto-start, set `bAutoStartServer=True` under `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]`.

Third-party: `.claude/skills/ue-*` from quodsoler/unreal-engine-skills (MIT); VibeUE, UEGitPlugin and Inkpot (MIT, see each plugin). Map data © OpenStreetMap contributors (ODbL).
