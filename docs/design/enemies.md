# Enemy squad design (Pac-Man roles + CS-style Donk)

Living spec for hostile NPCs. Owner: R3 (AI/Combat) with R2 (characters/anims). Code: `Source/KochSimulator/AI/`.
In-game names are placeholders (`TODO_LORE`); working names below.

## 1. Core idea
Enemies run at the player and try to kill them. Like the four Pac-Man ghosts, each type picks a **different target point**, so the squad surrounds the player instead of queueing behind each other. The squad alternates **Chase** (press the player) and **Regroup** (fall back to cover/anchor points) on a timer, which gives the player breathing room. Difficulty changes reaction, accuracy, speed, coordination and the timer.

Source of the ghost rules: Pittman, *The Pac-Man Dossier* — https://pacman.holenet.info/

## 2. Roster
| Working name | Pac-Man role | Height | Weapon | Movement / behaviour |
|---|---|---|---|---|
| Guard | Blinky — **Chaser** | 178 cm | Pistol | Targets the player's current position. Squad "leader" for the Flanker. |
| Interceptor | Pinky — **Ambusher** | 182 cm, lean | SMG | Targets where the player **will be**: position + velocity × lead time, snapped to the navmesh. Cuts off corridors/doorways ahead. |
| Flanker | Inky — **Flanker** | 172 cm | Shotgun | Target = 2·(player + forward·4 m) − Guard position → always on the opposite side of the player from the Guard (pincer). |
| Heavy | Clyde — **Shy** | 195 cm, heavy build | LMG (later: riot shield) | Rushes when farther than 12 m; inside 12 m falls back to cover and suppresses. Slow. |
| **Donk** | Blinky + "Cruise Elroy" — **Peeker** | **120 cm** (MetaHuman at 160 cm × 0.75 scale) | **AK-47** | Hardest enemy. Direct chaser that fights like a CS2 pro (§4). Gets faster when the squad is almost dead (Elroy). All difficulties (only enemy built so far). |

Scale: MetaHuman parametric height minimum is ~135 cm, so Donk is built at 160 cm with adult proportions and the actor is scaled 0.75 (capsule scales with it). He must read as a small adult, not a child.

## 3. Squad phases (Regroup ↔ Chase)
Pac-Man's scatter/chase table, used as wave rhythm (seconds, Regroup/Chase/…; last value = chase forever):

| Difficulty | Pac-Man level | Schedule |
|---|---|---|
| Easy | 1 | R 7 / C 20 / R 7 / C 20 / R 5 / C 20 / R 5 / C ∞ |
| Medium | 2–4 | R 7 / C 20 / R 7 / C 20 / R 5 / C ∞ (the 1033 s / 1 s steps collapse to "chase forever") |
| Hard | 5+ | R 5 / C 20 / R 5 / C 20 / R 5 / C ∞ |

- **Regroup** = each role heads to its own anchor (the Pac-Man "corner"): cover points picked by EQS near the squad spawn, one per role.
- On each phase switch every enemy re-paths immediately (Pac-Man ghosts reverse direction).
- **Elroy**: when ≤ 2 enemies are alive (Medium) or ≤ 3 (Hard), Donk/Guard get +5 % / +10 % speed and ignore Regroup.
- **Frightened → "Suppressed"**: an enemy under heavy fire (≥ 3 hits in 1.5 s) or under 30 % HP flees to cover for 2–6 s (shorter on Hard). No ghost-eating mechanic.

## 3a. Awareness — hunting, not following
Enemies never read the player's true position unless they can see him. `UKochAwarenessComponent` (per enemy, 0.1 s timer):
- **Senses:** AI Perception sight (range / cone per difficulty) and hearing. Gunfire is loud (`ShotNoiseRange` 5000 cm). Player footsteps make noise only when running on the ground (`UKochSquadSubsystem` emits them every 0.35 s); walking and crouching are silent, like CS.
- **Noticing:** needs `NoticeTime` of continuous visibility (faster when close or already alert), so a quick peek past an unaware enemy can go unseen.
- **Memory:** last known position + velocity; extrapolated ≤ 1 s, useless after `MemoryTime`.
- **Callouts:** an engaged enemy radios the squad once a second; others get it after 1.2 / 0.7 / 0.35 s (Easy / Medium / Hard).
- **States:**
  | State | Enters when | Moves to |
  |---|---|---|
  | Unaware | start, or search gave up | its anchor |
  | Suspicious | heard footsteps | the noise (walking) |
  | Hunt | gunfire, callout, or lost sight > `LoseSightGrace` | Pac-Man role target around the **believed** position |
  | Engage | noticed the player | best fighting spot: line of sight, inside the engage band, low cover preferred, spaced from squadmates (re-picked every 1 s) |
  | Search | reached the last known position or memory expired | last known position, then 4 random reachable points nearby (walking) |
- StateTree uses `Koch Awareness Is` conditions per state and `Koch Move To Awareness Goal`; Engage adds `Koch Shoot Burst` (others) or `Koch CS Peek` (Donk).

| Awareness tuning | Easy | Medium | Hard |
|---|---|---|---|
| Sight range / half-angle | 2500 cm / 55° | 3500 cm / 70° | 4500 cm / 80° |
| Notice time | 0.9 s | 0.5 s | 0.25 s |
| Hearing range | 2000 cm | 3000 cm | 4000 cm |
| Memory / search time | 5 / 6 s | 8 / 12 s | 12 / 20 s |

## 4. Donk — CS2-style fighting
Numbers from CS2 (AK-47) where known; Source units converted at 1.905 cm/u (Valve's "player" scale).

| Parameter | CS2 | Donk (Hard) | Notes |
|---|---|---|---|
| Run speed | 215 u/s ≈ 410 cm/s | 450 cm/s | small and fast; Easy n/a, Medium 410 |
| Accurate only below | 34 % of max speed | 34 % | above it the aim cone widens a lot |
| Counter-strafe stop | ≈ 80 ms | 80 ms | braking decel ≈ 5600 cm/s² |
| Fire rate | 600 RPM (0.1 s) | 0.1 s | |
| Damage | 36, head ×4 (144), armor pen 77.5 % | same ratios on our HP scale | |
| Magazine | 30 | 30 | reload ≈ 2.4 s (unconfirmed) |
| Spray | first ~10 shots climb straight up, then left, then right | recoil curve asset | |

Peek techniques (state "Peek" in the StateTree):
- **Jiggle peek** — strafe 40–80 cm out of cover and back in 0.15–0.3 s to bait a shot; no firing.
- **Shoulder peek** — 20–40 cm, just to make the player shoot/reveal.
- **Wide swing** — commit 150–250 cm past the angle, counter-strafe to a stop, fire a 2–4 round burst.
- **Pre-fire** — when the player was last heard/seen around a corner, start firing as he swings.
- **Crouch-spray** — at < 10 m: crouch (−25 % spread) and spray 6–10 rounds.
- Always **stop before shooting** (accuracy gate), strafe between bursts.

## 5. Difficulty tuning (per enemy type, DataTable later)
| | Easy | Medium | Hard |
|---|---|---|---|
| Reaction time (see → first shot) | 0.6 s | 0.35 s | 0.2 s (Donk 0.15 s) |
| Aim cone half-angle (still) | 6° | 3.5° | 2° (Donk 1.2°) |
| Move speed × | 0.85 | 1.0 | 1.1 |
| Health × | 0.8 | 1.0 | 1.25 |
| Roles used | everyone acts as Chaser | full roles | full roles + Elroy + pre-fire |
| Max simultaneous shooters | 2 | 3 | 4 |
| Regroup/Chase table | Easy row | Medium row | Hard row |
| Donk present | 1 | 1 | 1–2 |

### Donk per difficulty (first enemy; every enemy type gets the same Easy/Medium/Hard table in its BP)
| | Easy | Medium | Hard |
|---|---|---|---|
| Run speed | 340 cm/s | 410 cm/s | 450 cm/s |
| Reaction | 0.5 s | 0.3 s | 0.15 s |
| Aim cone still / running | 5° / 15° | 2.5° / 12° | 1.2° / 10° |
| Acceleration / braking | 2048 / 1350 | 3400 / 1350 | 3400 / 1350 |
| Health | 80 | 100 | 125 |
| Peeks | wide swing only | jiggle + shoulder + wide swing | all + crouch-spray + pre-fire |

## 6. Assets (to source)
CS2-*like* look and sound from licensed packs (no files extracted from Valve games):
- Locomotion: Epic **Game Animation Sample** (free, usable in own projects) retargeted to MetaHuman; rifle/pistol layers, fire, reload, death from **Lyra** (license TBC) or **Mixamo** (royalty-free). Tune play rate / root-motion speed so Donk's run, stop and strafe timings match §4.
- Animations needed: rifle idle/walk/run/strafe, crouch idle/walk, crouch-fire, quick stop, lean peek L/R, jump, fire, reload, hit react, death.
- SFX: Sonniss GDC bundles (commercial, no attribution) + CC0 (Kenney, Free Firearm Sound Library): AK close/distant shot, reload, dry fire, impacts, bullet whizz, footsteps per surface, jump/land, short pain/death vocal (record our own if none fits).
- Kill-feed / HUD icons: our own.

## 7. Tech
- **StateTree** per enemy (already used by `Variant_Shooter`), squad brain = `UKochSquadSubsystem` (world subsystem): role targets, phase timer, Elroy, shooter tokens.
- **Fighting spots:** C++ sampler in `UKochAwarenessComponent` (17 nav points, line-of-sight + low-cover traces, 1×/s while engaged). EQS (`FStateTreeRunEnvQueryTask`) only if designers need to author queries.
- **AI Perception**: sight + hearing. Gunfire `MakeNoise` exists (`ShooterWeapon`); raise `ShotNoiseRange` 300 → 5000 cm; add a footstep `MakeNoise` anim notify.
- **Avoidance** (todo): Detour crowd (`UCrowdFollowingComponent`), RVO off.
- Budget: ≤ 10 enemies, AI cost ≪ 1 ms game thread; MetaHuman Optimized/Medium, groom cards, LODSync.

## 8. Status
- [x] Donk MetaHuman v2 (face fitted from the de-haired head mesh, male, slim, 160 cm built, 120 cm in game).
- [x] C++: difficulty subsystem, squad subsystem + role targeting, enemy character (accuracy gate, scale, tuning), StateTree nodes (awareness condition, move-to-goal, shoot burst, CS peek); unit tests for targeting.
- [x] C++: awareness layer (perception, memory, callouts, 5 states, fighting-spot picker, player footstep noise).
- [x] Donk playable: `BP_Enemy_Donk` + `BP_KochAIController` + `ST_KochEnemy`, tested in PIE on `Content/Developers/Azamat/Maps/L_EnemyTest` (notices, engages from a fighting spot, peeks, kills the player in ~10 s on Medium).
- [ ] BPs for Guard / Interceptor / Flanker / Heavy; Engage branch with Koch Shoot Burst for non-peekers.
- [ ] Balance: Medium Donk is very lethal; tune after real playtests (player HP, burst length, reaction).
- [ ] Animations + SFX: Donk uses the template rifle anim BP for now (Manny clips on the MetaHuman skeleton via compatible skeletons). Game Animation Sample + Lyra are in the Fab library; download blocked by Launcher crashes.
- [ ] Other 4 enemy models (MetaHuman presets).
