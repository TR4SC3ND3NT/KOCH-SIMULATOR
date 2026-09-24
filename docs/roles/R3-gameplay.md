# R3: Gameplay & Combat

**Owns:** `Source/*/Player/`, `Source/*/Combat/`, `Source/*/AI/`, `Source/*/Interaction/`, and their thin BP children.
**Stack:** C++ first, Enhanced Input, Gameplay Tags, components and interfaces, StateTree or Behavior Tree for AI, EQS for cover, Chaos physics, `UPhysicsHandleComponent` for grabbing. GAS only via a docs/decisions.md entry.

## Early deliverables (unblocks everyone)
1. The character and controller built on the First Person template (C++).
2. `IInteractable` + `UInteractionComponent`: doors, pickups, grabbable physics props.
3. `UHealthComponent` / `IDamageable`, damage types, hit reactions hook for R2.
4. The weapon component: hitscan and/or projectile, recoil, ammo. Data comes from a DataTable (CSV).
5. Enemy AI MVP: perception, cover, attack (with R1's navmesh).

## Checklist per PR
- Compiles on Linux and Windows.
- Automation tests for core logic.
- No logic in Level Blueprints.
- Tunables live in data, not hard-coded.

## First prompt
> Read AGENTS.md. Research proven UE 5.8 C++ FPS implementations (Epic templates and samples, MIT GitHub) for the character, interaction, health/damage and hitscan weapons. Adapt the best one: create the C++ character/controller, IInteractable + UInteractionComponent, UHealthComponent and a data-driven weapon component, with automation tests.
