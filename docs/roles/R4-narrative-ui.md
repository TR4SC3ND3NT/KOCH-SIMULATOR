# R4: Narrative, UI, Audio & Integration

**Owns:** `Narrative/` (Ink, CSV), `Content/KochSimulator/UI/`, `Content/KochSimulator/Audio/`, `Source/*/Narrative/`, `Source/*/UI/`, packaging and build scripts.
**Stack:** Ink + Inkpot, String Tables from CSV, Quest DataTable, Runtime Data Layers for world states, UMG (CommonUI optional via a docs/decisions.md entry), MetaSounds.

## Scope
- Turn the human-written story (`docs/lore/canon/`) into quests, dialogue and triggers. Never invent canon; log gaps in `docs/lore/open_questions.md`.
- Menus, HUD, the settings screen with scalability presets and the upscaler choice (TSR / DLSS / FSR), and subtitles.
- Audio: ambience per area, weapon sounds (with R3), music.
- Integration: a nightly packaged build, and a smoke test on both reference machines.

## Checklist per PR
- Text is only in String Tables or Ink.
- Checked against canon.
- UI works with gamepad and keyboard.
- The packaged build still runs.

## First prompt
> Read AGENTS.md and the canon summary. Research Inkpot integration on UE 5.8 and a CommonUI vs UMG settings menu (scalability presets, TSR/DLSS/FSR choice). Build the main menu and settings shell, plus the Ink dialogue pipeline for the opening checkpoint scene (placeholder lines marked TODO_LORE).
