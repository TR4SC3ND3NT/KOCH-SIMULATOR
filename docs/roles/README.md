# Roles

Four roles, one per teammate. Owners are TBD, so fill them in the Roles table in `AGENTS.md` once you've decided.
Each teammate creates a personal `CLAUDE.local.md` in the repo root (gitignored) from `CLAUDE.local.md.example`, so their Claude knows its role.

| File | Role |
|---|---|
| [R1-world.md](R1-world.md) | World / Map (campus, landscape, buildings, lighting) |
| [R2-characters.md](R2-characters.md) | Characters & Animation |
| [R3-gameplay.md](R3-gameplay.md) | Gameplay & Combat (C++) |
| [R4-narrative-ui.md](R4-narrative-ui.md) | Narrative, UI, Audio & Integration |

How the roles connect:
- R3 defines C++ interfaces early (`IInteractable`, `IDamageable`, weapon/AI components) so the others can build against them.
- R1 provides the navmesh, cover and combat spaces R3 needs.
- R2 delivers skeletons and anim BPs to R3's character classes.
- R4 wires quests and dialogue to R3's gameplay events and owns the settings/scalability menu.
