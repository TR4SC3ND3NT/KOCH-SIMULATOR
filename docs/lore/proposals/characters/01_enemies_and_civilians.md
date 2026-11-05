PROPOSAL — not canon. A human lore author must approve and move it into docs/lore/canon/.

# Enemies and civilians (R2, 2026-11-05)

- Enemies all derive from `AShooterNPC` (HP via `CurrentHP`, default 100; `TeamByte`; `WeaponClass`; ragdoll death). Armour/headshot multipliers below are requests to R3 (not in code yet).
- Faction: all enemies are **KOCH Secure** (corporate security). Uniform base colour grey-blue + navy; patches show the fictional KOCH Secure shield. No real police/army insignia.
- "Max on-screen" is a perf cap (see 02_asset_plan.md budget), not a story count.

## Enemy archetypes

| Id | Look | Loadout | Behaviour (StateTree) | HP / armour tier | Spawns | Max on-screen |
|---|---|---|---|---|---|---|
| ENM_GuardCheckpoint | Kuban's uniform: grey-blue shirt, navy trousers, soft vest, peaked cap, radio. Mixed ages 25–50, some overweight | Baton (melee); radio | Before alarm: post idles, questions, waves people through. After: melee rush in pairs, calls for backup, flees at <30 % HP | T1: 100 HP, no armour, head ×2 | Gate booth, FaceGate line, B entrance desk | 3 |
| ENM_GuardPatrol | Same uniform without cap, black cap or bare head, duty belt, flashlight | Pistol (9 mm), baton | Patrol routes in pairs; investigate noise; take cover, shoot in bursts; radio report (raises alert level) | T1: 100 HP, no armour, head ×2 | Alley, garden/maze, canteen, B/C/A lobbies and stairwells | 6 |
| ENM_Tactical | Navy tactical uniform, plate carrier, ballistic helmet with goggles, black balaclava or face visible, knee pads, gloves | Rifle (5.45/5.56 class), sidearm, frag/smoke (optional, R3) | Arrives after the alarm in squads of 3–4 from vans; flank and suppress; use cover, peek, push | T2: 150 HP; torso ×0.6 (vest); head ×1.5 (helmet) | Drill ground (sports courts), gate, garden stairs, C/A entrances | 6 |
| ENM_Elite | Black tactical kit, heavy plate carrier, full-face/visor helmet or black balaclava + glasses, Temirov unit patch | Rifle with optic or SMG, flashbang (optional) | Temirov's squad: coordinated breach, flash then rush; hold doorways; do not flee | T3: 200 HP; torso ×0.5; head ×1.25 | Block A (Clinic, CEO floor, Assembly Hall), M08 pursuit | 4 |
| ENM_Bolot (mini-boss) | Elite kit, open-face helmet, shaved head, very broad | LMG or shotgun | Aggressive push, taunts; summons 2 elites at 50 % | Boss: 600 HP; torso ×0.5 | Block A Clinic corridor (M07–M08) | 1 |
| ENM_Temirov (final boss) | See cast | Rifle + pistol; smoke | 3 phases: (1) cover-shooting with 2 elite, (2) flank via stage/catwalk, (3) close-quarters pistol/knife | Boss: 900 HP; torso ×0.5; no helmet | Assembly Hall (proposal) | 1 |

Alert flow (request to R3/R4): Before = guards passive; Alarm (M01 stab) = patrols hostile, tactical team dispatched after ~60 s; Block A = elite only. Combined enemies on screen ≤ 10.

## Civilian archetypes

All civilians: non-hostile, flee/cower on gunfire, never block the player permanently. Before alarm they react to the masked hero with stares only.

| Id | Zone | Look | Density (visible) | Animation needs |
|---|---|---|---|---|
| CIV_Pedestrian | Street, crossing, bus stop | Mixed ages, autumn layers: light jackets, hoodies, headscarves on older women, school uniforms (`TODO_LORE:` school days) | 20–40 (Mass crowd), 6–10 near stop | Walk variants, phone idle, waiting idle, crossing, smoke, look-at hero |
| CIV_BusPassenger | Bus interior | Commuters, students, elderly woman with shopping bags, worker in overalls | 8–12 (seated + standing) | Sit idle, sit phone, sit sleep-nod, stand holding rail, sway on braking, get on/off |
| NPC_BusDriver (Talgat) | Bus | See cast | 1 | Seated driving loop, door-lever, glance mirror |
| CIV_StaffQueue | Gate (FaceGate line) | Office staff in business-casual, interns with lanyards | 4–8 before alarm, 0 after | Queue idle, step-through turnstile, badge tap, impatient shift, flee |
| CIV_Visitor | Block B Visitor/PR Center | Visitors in coats, a school excursion pair, an official in a suit | 6–10 | Watch demo, point, photo with phone, talk |
| CIV_Barista | Block B Brew Point | Like Nurai's apron, 1–2 extra baristas | 2 | Coffee machine loop, serve cup, wipe counter |
| CIV_OfficeStaff | Block B, Block A, Block C lobbies | Business-casual and suits; KOCH lanyards | B 4–6, A 8–12, C 4–6 | Typing, phone, walk with folder, coffee, talk in pairs, meeting sit |
| CIV_Executive | Block A CEO floor, Finance, Legal | Dark suits, ties, heels | 3–5 | Phone pacing, meeting sit, hands-up on threat |
| CIV_Intern | Block C (incl. room 203), canteen, garden | 18–22, navy Talent Program polo, lanyards, backpacks | C 12–20, garden 3–6 | Typing at desks, talking in corridor, vending machine, sit on stairs, cower under desk |
| CIV_Analyst | Block C F5 attic | Hoodies, headphones, laptops | 3–5 | Typing, two-screen staring, coffee, hide |
| CIV_Cleaner | Block A, B, C corridors and WCs | Blue work coats, headscarves, carts | 1–2 per building | Mopping, wiping, pushing cart, cower |
| CIV_Cook | Canteen | White chef jacket, cap, apron | 2–4 | Stir pot, serve tray, wipe, carry crate |
| CIV_Diner | Canteen | Staff and interns | 15–25 | Sit eat, sit talk, sit phone, carry tray, queue |
| CIV_GardenWalker | Garden, maze, gazebos | Staff on break | 6–10 | Bench sit, smoke, walk, talk in gazebo, read |
| CIV_MedicalStaff | Block A Clinic | Scrubs, white coats | 2–3 | Check monitor, walk with clipboard, cower |

After alarm: zone density drops to 20–30 %; remaining civilians use cower, flee, hands-up or hide-under-desk sets. Killing civilians is penalised (R3/R4 decision).

## Shared animation set list (civilians)
- Idle: phone, coffee/cup, typing seated, cleaning (mop/wipe), talking pair, sitting (bench, chair, bus), eating, smoking, reading.
- Locomotion: walk (casual, hurried, elderly), run-flee.
- Reactions: startled, cower crouch, hands-up, hide-under-desk, flee look-back, hit react, death (ragdoll handoff).
