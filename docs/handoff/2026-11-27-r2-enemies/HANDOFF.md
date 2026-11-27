# R2 enemies: handoff to Windows (2026-11-27)

Start a new agent session on Windows with: "Read docs/handoff/2026-11-27-r2-enemies/HANDOFF.md and continue."

## Files here
- `session.md`: readable transcript (user and assistant text). Images were removed, and accounts and emails redacted.
- `session.jsonl.gz`: the full sanitized session (tool calls included).
  - To try `claude --resume`, gunzip it into `%USERPROFILE%\.claude\projects\<project-slug>\86f57ec1-9926-45e0-be86-05e188ee279f.jsonl`.
  - The paths inside it are macOS paths, so prefer a fresh session that reads this file.
- `tools/ue_mcp_client.py`: a direct MCP client (`python ue_mcp_client.py script.py [timeout]`). Use it when the agent's unreal-mcp tool listing fails.
- `tools/studio_spawn.py` + `tools/studio_record.py`: record per-enemy GIF frames in Simulate, for the canvas.
- `tools/spawn_donk.py`: runtime spawn via `summon`.

## State (all on `main` @ 15f23f9e)
- **Donk:** done. AK, 120 cm, outfit, fire/reload/hit montages, footsteps, kill feed.
- **Guard / Interceptor / Flanker / Heavy:** MetaHumans built and body skin cut. Each has a `BP_Enemy_*` under `Content/Developers/Azamat/Enemies/<N>`.
  - Weapons: pistol / SMG / shotgun / LMG.
  - Roles: Chase / Intercept / Flank / Shy.
- **Kill feed:** C++ (`Combat/KochKillFeedSubsystem`, `UI/KochKillFeedWidget`), icons in `Content/KochSimulator/UI/KillFeed`.
- **StateTree** `ST_KochEnemy`: the Attack branch uses "Koch Role Is".
- **Design canvas** (options + real-model GIFs of all 5): https://claude.ai/artifact/9drW5gDMVobotohWRghL9X
- **Research:** `docs/research/` (AAA feel for small UE5 teams).

## Left on the Mac only (not pushed, on purpose)
- `L_GreyboxTest` navmesh (R1's map) and its external actors. R1 decides whether to commit them.
- `Content/Developers/Azamat/Donk/Built/` (old v1 build, unused; BuiltV2 is live).
- `Scripts/Characters/make_body_cloth_mask.py` (unused).
- Stash "wip before merging main" (`Config/DefaultEditor.ini`).
- `_local/` (friend's photos). Never commit it.

## Plan (next steps, in order)
1. **Choose mechanics:** the user picks one option letter per enemy on the canvas (Guard, Interceptor, Flanker, Heavy, Blade A/B/C).
2. **Implement the chosen mechanics.**
   - Logic in C++ (`Source/KochSimulator/AI`, `Combat`) plus StateTree tasks. BPs only tune.
   - Add the signature animations: Lyra clips first, then licensed packs.
   - Verify in PIE in `L_EnemyTest`.
3. **Blade (sword enemy):**
   - The user downloads the Mixamo Sword and Shield + Great Sword packs (FBX for Unity, With Skin, Y Bot, 30 fps).
   - Retarget them to the MetaHuman/Lyra skeleton with an IK Retargeter.
   - Add `UKochMeleeComponent` per `docs/design/enemies.md` §4b: poise, stamina, combo windows, dodge.
   - Build a 185 cm MetaHuman, then run `Scripts/Unreal/cut_hidden_body_skin.py`.
4. **Polish:**
   - LMG model (it uses the rifle model now).
   - Ankle gap between the cuff and the shoe.
   - Guard's pistol reload grip.
   - Verify a headshot with a real bullet: the kill feed should show the headshot icon.
5. **Shipping:**
   - Win64 + Linux compile, warning-free.
   - `Automation RunTests KochSimulator`.
   - fps/VRAM on reference machines A and B (≥ 60 fps at 1080p, ≤ 7 GB).
   - A teammate approves the CLAUDE.md and shared-file changes.

## Windows setup checklist
- UE 5.8.3, with the MetaHuman Creator plugin enabled (the .uproject already lists it).
- `git lfs pull`, then build `KochSimulatorEditor Win64 Development` (see AGENTS.md).
- **Editor MCP:** start the Epic unreal-mcp server in the editor (port 8000).
  - Keep the editor in the foreground, or set `bThrottleCPUWhenNotForeground=False`.
- **After any MetaHuman rebuild:**
  - re-run `cut_hidden_body_skin.py`
  - re-point the BP meshes with `Scripts/Unreal/make_enemy_bp.py`
- **Gotchas:** read CLAUDE.md "Editor gotchas". Modal dialogs block MCP. Committed `.uasset` files are read-only until checked out.
