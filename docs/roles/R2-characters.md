# R2: Characters & Animation

**Owns:** `Content/KochSimulator/Characters/`: MetaHumans, enemy and NPC meshes, skeletons, AnimBPs, Control Rigs, IK retargeters, mocap data.
**Tools:** MetaHuman Creator (in-engine, 5.8), Mesh to MetaHuman (e.g. from a RealityScan phone scan), video mocap (MetaHuman Animator markerless plugin on Windows RTX; Rokoko Vision / QuickMagic free tiers), IK Retargeter.

## Scope
- Player first-person arms/body (the First Person template uses First Person Rendering).
- Enemies and NPCs: MetaHumans for realism.
- Animation sets: locomotion, aim, reload, hit reacts, deaths. Face animation for story scenes.

## Performance notes
- Use MetaHuman LODs.
- Limit on-screen full-quality MetaHumans. Test with `stat gpu` and budget per scene.
- Grooms are expensive; use card-based LODs at distance.

## Checklist per PR
- Correct skeleton and retargeting.
- LODs set.
- Collision/physics asset checked.
- Tested in PIE with R3's character class.

## First prompt
> Read AGENTS.md and the canon summary. Research the best UE 5.8 pipeline for a first-person hero (full-body First Person Rendering) plus realistic MetaHuman enemies (corporate guards and mercs) within our VRAM budget. Then set up the hero skeleton and anim BP placeholders that plug into R3's character class.
