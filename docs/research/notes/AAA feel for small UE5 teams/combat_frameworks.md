# Ready-made combat/shooter frameworks and cheap enemy variety for small UE5 teams

Source-quality legend: **[fetched]** = page read in full; **[snippet]** = search-result summary only, page not fetched (treat as unverified; for snippet bullets the URL is the most likely match from the result list, and the claim-to-URL mapping is unverified). Research date 2026-11-27. Project context: UE 5.8 C++, StateTree AI, no GAS, GTA-like TPS/FPS, MetaHuman enemies, 4 people, 60 fps on RTX 3070 Ti laptop.

## Souls-like / melee frameworks: which exist, what they cost, and how they implement lock-on, stamina, dodge i-frames, hit-stop, hit reactions, parry, root motion and motion warping

### Takeaway
The two established melee and hybrid frameworks are **Ascent Combat Framework (ACF)**, a C++ plugin built entirely on GAS that also does ranged combat and multiplayer, and **Dynamic Combat System (DCS)**, a cheap Blueprint/component-based kit whose last dated update was in 2023. Epic's free UE 5.6 Third-Person "Combat" variant covers basic combos and AI. None of the fetched listings states UE 5.8 support. Implementation details for i-frames, stamina and parry were not documented on any page read.

### Cited Findings
**Ascent Combat Framework (Dark Tower Int)**
- **ACF V4 (C++ Action RPG Creator):**
  - Price $174.99, rated 4.6 (297 ratings in the visible text; the JSON-LD says 289) [fetched] — [Fab ACF V4](https://www.fab.com/listings/ca5f015f-4976-4928-84a1-8826954a2a57)
  - The listing calls it a "multi-module C++ plugin" with core systems exposed to Blueprint, and says you need "at least some basics blueprint/unreal knowledge" [fetched] — [Fab ACF V4](https://www.fab.com/listings/ca5f015f-4976-4928-84a1-8826954a2a57)
  - Multiplayer is listed as supported. The combat modules are based on GAS [fetched] — [Fab ACF V4](https://www.fab.com/listings/ca5f015f-4976-4928-84a1-8826954a2a57)
- **ACF V4 features** [fetched] — [Fab ACF V4](https://www.fab.com/listings/ca5f015f-4976-4928-84a1-8826954a2a57):
  - targeting system ("Lock on or magnetic targeting")
  - ranged and melee combat
  - AI framework with a ticketing system (v3.8)
  - HitStop effects (v3.8)
  - "Improved automatic warp" (v3.8)
  - "Complete GASP integration" (v3.8)
  - animation layering, flying mounts, Lyra-inspired inventory
  - v4.2: NPC daily routines and DaySequences day/night
  - Not mentioned on the page: stamina, dodge, parry, hit reactions. UE version support and license terms are also not shown.
- **ACF Ultimate V4.6:**
  - The fetched page shows $349.99, rated 4.9 (124 ratings in the visible text, 91 in the structured data) [fetched] — [Fab ACF Ultimate](https://fab.com/listings/cc258205-8fcf-41e5-9b48-6ec44e46d7eb)
  - **Conflict:** a category-page snippet said "from $699.99" [snippet] — [Fab game-mechanics category](https://www.fab.com/category/tool-and-plugin/game-mechanics?lang=en). The license tiers did not render, so the price may depend on the tier.
  - The listing says combat modules are "fully powered by the Gameplay Ability System" [fetched] — [Fab ACF Ultimate](https://fab.com/listings/cc258205-8fcf-41e5-9b48-6ec44e46d7eb)
  - Melee uses animation warp; AI includes melee and ranged enemies, mages, AI groups and companions [fetched] — [Fab ACF Ultimate](https://fab.com/listings/cc258205-8fcf-41e5-9b48-6ec44e46d7eb)
  - Weapon samples include bows, shotguns, rifles and pistols. V4.6 (dated 11/2026) adds "procedural first-person animation for all weapons" and destructible vehicles [fetched] — [Fab ACF Ultimate](https://fab.com/listings/cc258205-8fcf-41e5-9b48-6ec44e46d7eb)
- **ACF J** is a turn-based JRPG product and not relevant here. Its fetched price is $149.99, against a $299.99 snippet [fetched] — [Fab ACF J](https://www.fab.com/listings/0ee7ddec-cda7-48eb-8cef-9a648a0b20d0)
- **ACF LITE** has not been migrated to Fab and is available only from the Vault for existing owners [snippet] — [UE Marketplace ACF LITE](https://www.unrealengine.com/marketplace/en-US/product/ascent-combat-framework-acf-lite-c-action-rpg-creator)

**Dynamic Combat System (Grzegorz Szewczyk)**
- **DCS Bundle** [fetched] — [Fab DCS Bundle](https://www.fab.com/listings/82994e04-68bb-4434-bf95-763d340a5029):
  - $32.99, rated 4.2 (58 visible ratings, 65 in the JSON)
  - Blueprint tag, with logic built on Actor Components. No C++ is mentioned, and multiplayer is not mentioned.
  - The only dated update is v3 in July 2023, for UE 5.2 and later. No newer date is shown.
- **DCS features** [fetched] — [Fab DCS Bundle](https://www.fab.com/listings/82994e04-68bb-4434-bf95-763d340a5029):
  - trace-based hit detection
  - lock-on, dodge/roll, parry and backstab
  - status effects and an AI system
  - archery, plus guns (rifle, pistol, shotgun) with trace-based and movement-based projectiles
  - save/load of equipment, inventory and stats
- **DCS – Guns** is described as a third-person shooter system "implemented entirely in blueprints" that does not need base DCS [snippet] — [Fab DCS Guns](https://www.fab.com/listings/60895d77-b2a4-4f5f-b62a-32912232a837?lang=tr)
- **Dynamic Combat Framework (DCF)** is a different product: a Blueprint plugin for defence-based melee, supporting UE 5.2–5.4 [snippet] — [DCF](https://docs.unrealengine.com/marketplace/ko/product/dynamic-combat-framework-dcf)

**Soulslike Framework (SLF, by isikdev)** [fetched] — [Epic forum thread](https://forums.unrealengine.com/t/soulslike-framework-complete-soulslike-kit/2443346)
- **Build and support:**
  - Blueprint only: 250+ Blueprints and 150+ Widget Blueprints. Uses Epic's SkeletalMerging plugin.
  - "Simplified Blueprint version of GAS", not real GAS. No motion matching.
  - Not network replicated. Windows supported; Mac and consoles untested.
- **Features:** Perfect Guarding (its parry), Poise/Stance Break, Advanced Boss AI, AI abilities.
- **User feedback:**
  - Praise for breadth and documentation.
  - One bug report: the player was teleported after an execution. It was fixed by adding a notify to the montage.
  - One complaint: a boss strafes 7–8 s without attacking, and the minimum cooldown is 10 s.
  - Price and UE version are not on the page.

**Smaller and specialised C++ pieces**
- **Kiirsh "C++ lock on system plugin":**
  - C++ PlayerCharacter with Souls-style lock-on and camera, targeting "LockOnActors" placed inside enemies [snippet] — [UE Marketplace](https://docs.unrealengine.com/marketplace/ja/product/c-lock-on-system-plugin)
  - UE 5.3, no replication, Windows-focused [snippet] — [UE Marketplace](https://docs.unrealengine.com/marketplace/ja/product/c-lock-on-system-plugin)
  - A UE 5.3 C++ Souls template demo exists [snippet] — [itch.io](https://kiirsh.itch.io/souls-inspired-template-demo)
- **Insodimension Agentic Targeting System:** C++, multiplayer, has a Souls style. Requires UE 5.5+, Gameplay Targeting System and GAS [snippet] — [Epic forum](https://forums.unrealengine.com/t/insodimension-agentic-targeting-system-c-multiplayer-runtime-styles/2685475)
- **Nemesis Stats Framework 1.0:** stats, resources, damage and status effects, announced for UE 5.8 [snippet] — [Epic forum](https://forums.unrealengine.com/t/nemesis-stats-framework-1-0-a-modular-stats-resources-damage-status-framework-for-unreal-engine-5-8/2835858)

**Epic's free templates**
- The UE 5.6 Third-Person template gained a **Combat** variant: simple hand combat, combo attacks, enemy targeting, a health system, AI opponents, an in-world health bar and an example map [snippet] — [Epic news](https://www.unrealengine.com/news/updated-game-templates-for-unreal-engine-5-6available-now); [Variants docs](https://dev.epicgames.com/documentation/unreal-engine/variants-in-game-templates)

**Implementation techniques found**
- **Motion warping:** add a "Motion Warping" Anim Notify State on the montage to define a warp window. Blueprint can create windows at runtime with "Add Root Motion Modifier Skew Warp" [snippet] — [Epic Motion Warping docs](https://dev.epicgames.com/documentation/unreal-engine/motion-warping-in-unreal-engine); API class `UAnimNotifyState_MotionWarping` — [API](https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/MotionWarping/UAnimNotifyState_MotionWarping?lang=en-US)
- **Hit-stop:**
  - Freeze the montage on the attacker and the victims, tuned per combo section [snippet; date not checked, likely pre-2024] — [Epic forum](https://forums.unrealengine.com/t/how-can-i-create-hitstop-system-base-on-different-section-of-the-montage/298007)
  - Apply it only to the instigator and the hit actor, not global time dilation, and blend it in and out [snippet; low-authority student report] — [Staffordshire Hollowborn report](https://gradex.staffs.ac.uk/wp-content/uploads/2025/04/5055_Hollowborn-Dev-Report.pdf)
- **Dodge buffering:** buffer the dodge input before the attack's interruptible window, then run it when the window opens. One poster hit a "root lock stays on" issue when switching montages from a notify [snippet; date not checked, likely pre-2024] — [Epic forum](https://forums.unrealengine.com/t/root-lock-stays-on-momentarily-when-changing-animation-with-a-notify/372932)
- **Melee hit detection:** use montage sections per attack, with notifies that run capsule traces and apply damage [snippet; date not checked, likely pre-2024] — [Epic answers](https://answers.unrealengine.com/questions/43365/fortnite-melee-combat-system.html)

### Inferences
- **ACF:**
  - It is the only listing that is C++, multiplayer and melee + ranged in one, and its versions are still actively dated in 2026.
  - It is GAS-based, so adopting it means adopting GAS. That conflicts with our "No GAS unless decided" rule and would need a line in `docs/decisions.md`.
  - It is an RPG creator (inventory, crafting, mounts, routines), so most of it would be dead weight for a GTA-like shooter.
- **DCS and SLF** are Blueprint-heavy, against our "logic in C++" rule. DCS shows no update past 5.2-era v3, and SLF is not replicated (irrelevant for single-player).
- **Cheapest path for us:** reuse the patterns (montage notify windows for hit and cancel timing; i-frames likely the same way, unsourced; Motion Warping for gap-closing; per-actor hit-stop) in our own C++, and study Epic's free Combat variant. Buying ACF only to read its code is the option if we want a reference implementation.

### Gaps
- **UE 5.7/5.8 support:** no fetched listing (ACF, DCS, SLF) states it. Check the Fab "Supported Engine Versions" field before buying.
- **Fab license terms:** none of the fetched pages rendered the license tiers (personal vs professional seat pricing).
- **Not researched (no source found within budget):** "Combat Components", "SoulsLike Starter", GAS-based melee samples, and "Combat Fury" (mentioned only in a Reddit snippet).
- **Missing mechanics docs:** no source read documents how i-frames, stamina gating, parry windows or hit-reaction selection (directional or bone-based) are implemented in these frameworks. ACF's page does not mention stamina, dodge or parry at all.

## Shooter frameworks and AAA gunplay feel: Lyra, Epic's FP/TP templates (5.5–5.8), ALS/GASP, Fab FPS kits, and what makes guns feel good

### Takeaway
For free bases, Epic's UE 5.6 First-Person "Arena Shooter" variant gives weapon pickups, bullet types, AI and an ammo UI. Lyra gives a modular C++ shooter sample that forum users advise mining for parts rather than adopting whole. For locomotion, MIT-licensed C++ reworks of the Game Animation Sample exist. On feel, the strongest primary source (a Naughty Dog GDC 2024 talk) argues that weapon feel is "almost entirely hit reactions" built on accurate hit collision, plus forgiving aim (camera/character dual probes and a past-frame hit buffer).

### Cited Findings
**Epic templates**
- **UE 5.6 First-Person "Arena Shooter" variant:**
  - Contents: weapon pickups, bullet types, AI opponents that walk the level searching for and shooting the player, an ammo UI, a crosshair, a kill/death counter and an arena map [snippet] — [Epic news](https://www.unrealengine.com/news/updated-game-templates-for-unreal-engine-5-6available-now); [Variants docs](https://dev.epicgames.com/documentation/unreal-engine/variants-in-game-templates)
  - A "Survival Horror" variant also exists [snippet] — [Epic news](https://www.unrealengine.com/news/updated-game-templates-for-unreal-engine-5-6available-now)
  - A launch-time forum report says the Arena Shooter variant loaded without the gun, dummies and other assets [snippet] — [Epic forum](https://forums.unrealengine.com/t/when-will-arena-shooter-variant-for-tp-firstpersonbp-be-ready/2587614)
- **Native First Person Rendering (UE 5.5, experimental):**
  - Renders selected primitives (static and skinned meshes, Niagara) with a separate FOV [snippet] — [Epic docs](https://dev.epicgames.com/documentation/unreal-engine/first-person-rendering)
  - An advanced setup gives visible legs plus a full-body world mesh for shadows and reflections [snippet] — [Epic docs](https://dev.epicgames.com/documentation/unreal-engine/first-person-rendering)
- **First Person Rendering, community reports:**
  - 5.5 had shadow glitches with full body; one user says 5.6 "works perfectly" with Nanite [snippet] — [Epic forum](https://forums.unrealengine.com/t/how-to-use-first-person-rendering-5-5-new-experimental-feature/2122644)
  - Arms warp with camera pitch when the FP FOV and world FOV differ a lot [snippet] — [Epic forum](https://forums.unrealengine.com/t/first-person-rendering-mesh-warping-issue/2697878)
  - With a custom camera manager (Lyra, GASP), you must set FirstPersonFOV on the view itself [snippet] — [Epic forum](https://forums.unrealengine.com/t/5-5-first-person-rendering-fov-with-cameramanager-lyra-or-gasp/2224698)

**Lyra**
- **What it is:** Epic's UE5 sample that replaced UE4 ShooterGame. Scalable mobile to PC, with cross-play via EOS [snippet] — [x157 Lyra notes](https://x157.github.io); [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/lyra-sample-game-in-unreal-engine)
- **Weapons:** most weapon logic is in `B_WeaponInstance_Base` [snippet] — [x157 Weapons](https://x157.github.io/UE5/LyraStarterGame/Weapons)
- **Stripping it down:** duplicate the hero input config/data and remove the unwanted inputs [snippet] — [x157 dev experience](https://x157.github.io/UE5/LyraStarterGame/How-To-Create-New-GameFeature-Dev-Experience)
- **Forum advice:**
  - Treat Lyra as a "total conversion" or "copy and paste re-use" [snippet; date not checked, likely pre-2024] — [Epic forum "Best practices to build upon Lyra"](https://forums.unrealengine.com/t/best-practices-to-build-upon-lyra/515743/27)
  - Build your game as a GameFeature plugin and avoid editing Lyra code [snippet; date not checked, likely pre-2024] — [same thread](https://forums.unrealengine.com/t/best-practices-to-build-upon-lyra/515743/22)
  - "Only the Lyra C++ is reusable in any meaningful form"; treat binary assets as examples [snippet; date not checked, likely pre-2024] — [same thread](https://forums.unrealengine.com/t/best-practices-to-build-upon-lyra/515743/29)
  - Lyra's UI systems are designed to be usable independently of Lyra [snippet] — [Epic Lyra docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/lyra-sample-game-in-unreal-engine)

**Locomotion**
- **ALS-Community (speplworks):** a replicated, optimized ALS V4 for UE 5.0. The README says the plugin source is MIT [snippet; LICENSE file not checked] — [GitHub](https://github.com/speplworks/ALS-Community)
- **GASP Refactored (Spr-Aachen/Unreal-MotionMatchingSystem):** a C++ rework of the Game Animation Sample with ALS overlays, MIT, with a version table listing UE 5.6 for plugin v1.4+ [snippet] — [GitHub](https://github.com/Spr-Aachen/Unreal-MotionMatchingSystem)
- **GASP-ALS (gokhocse):** ALS overlay layering on GASP, MIT [snippet] — [GitHub](https://github.com/gokhocse/GASP-ALS)
- **Epic Game Animation Sample:** 500+ free animations, distributed via Fab [snippet] — [Epic blog](https://www.unrealengine.com/blog/game-animation-sample)

**Fab shooter kits**
- DCS Guns is Blueprint-only and works without base DCS (see the section above).
- ACF Ultimate 4.6 adds procedural first-person animation for all weapons [fetched] — [Fab ACF Ultimate](https://fab.com/listings/cc258205-8fcf-41e5-9b48-6ec44e46d7eb)
- A forum post describes a year spent building a multiplayer shooter template [snippet] — [Epic forum](https://forums.unrealengine.com/t/i-spent-a-year-building-a-multiplayer-shooter-template-and-the-hardest-part-was-letting-players-build-the-map/2841998)

**Gun feel: Naughty Dog GDC 2024, "A Second Shot" (Derek Mattson, TLOU2)** [fetched, speaker notes PDF] — [GDC Vault notes](https://media.gdcvault.com/gdc2024/Slides/GDC+slide+presentations/Mattson_Derek_ASecondShot_Notes.pdf)
- **Feel is mostly hit reactions:**
  - Weapon feel includes VFX, sound, fire rate, camera shake, kick, firing patterns and haptics, "but… it is almost entirely hit reactions".
  - Their example: a leg shot gets a matching reaction, and a neck shot gets a unique death animation even though gameplay treats it as a headshot.
- **Hit collision comes first:**
  - Rigid torso boxes caused wrong hits and misses, so they replaced them with multiple horizontal capsules at spine joints.
  - The thigh was split into two collisions so knee-aimed shots reliably trigger the leg stun.
  - Quote: "Start with a good base before focusing on detail… if you don't start with a good base of animation and hit detection," the FX, sound and haptics add noise.
- **Leg-shot stun state:** instant stun, lower damage. It gives the player more options: an opener for a grab or meat-shield, or a strike follow-up.
- **Third-person camera/character decoupling:**
  - Camera probe: an invisible spherecast that ignores the environment.
  - A "secret" raycast that collides with everything, to prevent accidental wall hits.
  - Character projectile: back-calculated from the camera probe's predicted impact and colliding only with enemies.
- **Input latency forgiveness:**
  - At 30 fps with a double or triple frame pipeline, what the player saw can be up to 3 frames old (0.06–0.1 s).
  - They cast every frame and store the reticle-overlap percentage for the last few frames. On a miss, they look back and roll against the stored chance.
  - A "hit chance curve" remaps values such as 91.84% to 100% ("Just make 95% == 100%", the "XCOM problem").
- **Hitscan:** the base pistols are hitscan. "Weapon probes for 1 frame, everything else that lingers is just feedback."

**Other gun-feel sources (snippets; lower authority)**
- GDC session "Battlefield 6: Game Feel is the Message" covers FPS gunplay feel; only the abstract was seen [snippet] — [GDC schedule](https://schedule.gdconf.com/session/battlefield-6-game-feel-is-the-message/915257)
- Recoil kick exists partly because quickly re-centring the crosshair is a skill expression [snippet; 2019 post] — [The Astronauts blog](https://www.theastronauts.com/2019/03/making-gun-come-to-life/)
- Camera shake is "one of the cheapest ways to add impact" and a fast way to cause nausea. The same post compares spring-decay and authored-curve recoil in UE [snippet; vendor blog, low authority] — [Strayspark](https://www.strayspark.studio/blog/fps-game-design-fundamentals-ue5)
- Hit markers are "overused and often misused" and target reactions are often better feedback [snippet] — [PC Gamer](https://www.pcgamer.com/games/fps/hit-markers-are-an-fps-crutch/)
- Hit markers are mostly reserved for multiplayer in shooters [snippet] — [Giant Bomb](https://giantbomb.com/wiki/Concepts/Single_Player_Hit_Marker)

### Inferences
- **Hit reactions over polish:** for MetaHuman enemies, the biggest return on "AAA feel" is likely per-bone hit reactions (physical animation or partial ragdoll), a better hit-capsule layout and leg/arm stun states. Camera shake and markers come after. This matches the Naughty Dog talk and the PC Gamer critique.
- **Aim forgiveness:** a past-frame reticle buffer with a remap curve is cheap (a few sphere traces per frame) and directly addresses input latency. (Its relevance at 60 fps with TSR is prior knowledge, unsourced.)
- **Lyra:** too large to adopt (GAS, experiences, EOS, multiplayer). Mine selectively: the weapon instance (cited above); spread/recoil heat, camera modes and CommonUI are other candidates (prior knowledge, unsourced).
- **Epic's FP Arena Shooter variant** is the lowest-risk free reference, since it is Epic-maintained (shipped in 5.6; presence in 5.8 not checked).
- **True first-person with full body:** use native First Person Rendering (5.5+). Expect FOV-mismatch arm warping and keep the FOV delta small.

### Gaps
- **Fab FPS kits not found within budget:** no listing data for "FPS Multiplayer Template", "Shooter Game Kit" or "Infima".
- **ALS-Community maintenance:** no source confirmed its status or 5.8 compatibility. The hit says 5.0.
- **Lyra on 5.7/5.8:** no fetched source on the current state or on stripping effort in person-days. The Reddit thread could not be fetched (the mirror failed DNS), and the "Should you make a survival game in Lyra" thread returned 404.
- **Battlefield 6 talk:** content not available.
- **Template variants in 5.8:** sources only cover 5.6; whether the Arena Shooter and Combat variants still ship in 5.8 was not checked.
- **Measured values:** no numbers for recoil pattern design, ADS timings or weapon sway.

## Cheap enemy variety: GAS/data assets per enemy, StateTree/BT reuse, Smart Objects, Mass AI, and cost per new enemy type

### Takeaway
The only fetched source (Epic's Parrot) uses class inheritance (a C++ enemy base and controller), a shared anim template with per-skeleton child AnimBPs, a shared blackboard and tasks, and one BT per enemy. It mentions no data assets. The one-config-asset-per-archetype pattern (perception, ranges, cooldowns, role) rests on vendor snippets only. Commercial enemy frameworks reportedly split high-level strategy (StateTree) from action execution (BT/GAS). No source gave a measured cost per new enemy type.

### Cited Findings
**Epic's Parrot sample (free)** [fetched] — [Epic docs: Enemy Characters in Parrot](https://dev.epicgames.com/documentation/unreal-engine/enemy-characters-in-parrot-for-unreal-engine?lang=en-US)
- **Base classes:** `AParrotCharacterBase` (HP and death, shared with the player) leads to the C++ `AParrotEnemyCharacterBase` (patrol and combat). The controller is `AParrotEnemyAIControllerBase`.
- **Hit and hurt volumes:** defined in the Blueprint child `BP_EnemyCharacter_Base`, because "a trigger volume that is inherited cannot be modified in the derived class" and volumes differ per mesh.
- **Animation:** shared template `ABT_EnemyBase`, plus one child AnimBP per enemy that supplies only its animations as overrides.
- **AI:** shared blackboard `BB_Enemy_Base` and shared tasks (`BTT_FindNextPatrol`, `BTT_AttackPlayer`), with one BT per enemy (Skeleton, HeadlessSkeleton, Sharky, Boss_Shark).
- **Patrol:** a reusable spline patrol rig component. Spawning is deferred, with data passed in before init (Expose on Spawn in Blueprint).

**Commercial and community examples**
- **Soulslike Enemy Combat System (Fab):** "separates high-level strategy (StateTree) from granular action execution (Behavior Trees & GAS)". Roles such as "Aggressor" and "Flanker" are assigned via config files [snippet] — [Fab](https://www.fab.com/listings/7087cec0-6975-4de5-82e0-0de0b9b3e9a7)
- **Hakan Erunsal Soulslike Enemy Combat:** C++ source and a modular data-driven component system [snippet] — [Epic forum](https://forums.unrealengine.com/t/hakan-erunsal-soulslike-enemy-combat/2686654)
- **Animus Ex Machina:** one config asset per enemy archetype, assigned to the AI Controller's Config property, falling back to defaults if none is set [snippet] — [Docs](https://arconiclabs.github.io/AnimusExMachina/reference/configuration)
- **Wardenmind:** a single Profile data asset per enemy type holds team, perception, attack range, cooldown and other tuning [snippet] — [Epic forum](https://forums.unrealengine.com/t/astore-wardenmind/2839752)
- **Indie DungeonRPG devlog:** StateTree custom tasks, with all damage routed through GAS. The loop is: evaluate abilities, pick the best, move into position, attack, repeat [snippet] — [Devlog](https://pavankrao-qlp.github.io/portfolio/blog/unreal-rpg-devlog-part-1---state-tree-based-ai--unreal)
- **UE forum "enemy variation":** a UPrimaryDataAsset-derived asset defines skeletal mesh, physics asset and visuals per enemy [snippet; date not checked, likely pre-2024] — [Epic forum](https://forums.unrealengine.com/t/how-are-you-guys-handling-enemy-variation/144571)
- **KampaiRaptor StateTree AI:** open StateTree AI example repo [snippet; license not checked] — [GitHub](https://github.com/KampaiRaptor/Unreal-Engine-StateTree-AI)
- **ACF V4:** an "AI ticketing system" (v3.8; the page does not explain it) [fetched] — [Fab ACF V4](https://www.fab.com/listings/ca5f015f-4976-4928-84a1-8826954a2a57)
- **Variety from damage states (Naughty Dog GDC 2024):** a leg-shot stun state created new tactical options without a new enemy type [fetched] — [GDC notes](https://media.gdcvault.com/gdc2024/Slides/GDC+slide+presentations/Mattson_Derek_ASecondShot_Notes.pdf)
- **"Class explosion" thread:** the question (spawner, totem, chaser origins × melee/ranged combat × weapon-granted skills such as block and counter) had **no replies** [fetched] — [Epic forum](https://forums.unrealengine.com/t/best-approach-for-structuring-enemy-blueprints-behavior-trees-and-aicontrollers-to-avoid-class-explosion/2626619)

### Inferences
- **Fits our setup:** our current direction (C++ enemy base, StateTree with roles such as Donk peek versus burst-fire, MetaHuman variants) already matches this pattern.
- **Next steps for cheap variety:**
  - a `UPrimaryDataAsset` per archetype (mesh/MetaHuman preset, weapon BP, perception, ranges, role tag, aggression, cooldowns, hit-reaction set)
  - StateTree tasks parameterised by Gameplay Tags instead of per-enemy trees
  - an attack-token/ticket system so roles feel distinct in groups
  - shared damage-state reactions (leg stun, stagger) that all archetypes get for free
- **GAS is optional for variety.** The examples use it for ability selection, but tag-driven C++ components plus data assets achieve the same without the "No GAS" decision change.

### Gaps
- **Not researched (no source found within budget):**
  - GAS AbilitySet-per-enemy data assets (Lyra-style `ULyraAbilitySet`)
  - Smart Objects for enemy behaviour (cover, alarms)
  - Mass AI for crowds (only relevant for ambient civilians; not researched)
  - indie postmortems of games shipping many enemy types
- **Cost per new enemy type:** no source gives hours or days per new archetype.
- **Unverified:** the Fab and forum enemy-framework claims are vendor descriptions from snippets only.

## Warnings from experienced devs about building on marketplace frameworks (tech debt, Blueprint performance, upgrade pain)

### Takeaway
The evidence is thin and mostly anecdotal. Recurring themes are that customising a kit deeply approaches the cost of writing your own, that kits never match a game's specific feel, and that buyers regret buying a "system" when they expected a template. Lyra-specific advice is to keep your game in a separate GameFeature plugin and not edit the base. No sourced data on Blueprint performance or upgrade breakage was found.

### Cited Findings
- **Reddit (r/unrealengine), Soulslike Framework thread:** one commenter argues that once you modify the code you might as well have built your own framework. Separately, the snippet said the top comment (mind4k3r) has 88 upvotes; it is unclear whether these are the same comment [snippet; mirror unreachable] — [Reddit mirror](https://redlib.hackliberty.org/r/unrealengine/comments/1iurzgs/soulslike_framework_complete_soulslike_kit)
- **Same thread, another commenter:** bought "Combat Fury" halfway through their own combat system to save time [snippet; mirror unreachable, permalink-to-claim mapping unverified] — [Reddit mirror](https://redlib.hackliberty.org/r/unrealengine/comments/1iurzgs/soulslike_framework_complete_soulslike_kit/me33mzf/?context=3)
- **A marketplace seller:** every game has specific requirements, style and feel, which "won't be accomplished by gluing together marketplace assets" [snippet] — [Epic forum](https://forums.unrealengine.com/t/about-combat-framework-systems-in-marketplace/1414831)
- **A reviewer** regretted buying a realistic weapon-simulation asset, saying it is "a weapon system rather than a full template" [snippet; date not checked, likely pre-2024] — [Epic forum](https://forums.unrealengine.com/t/realistic-blueprint-weapons-video-review-unreal-marketplace/64412)
- **Lyra:** build as a GameFeature plugin and avoid modifying base Lyra code [snippet; date not checked, likely pre-2024] — [Epic forum](https://forums.unrealengine.com/t/best-practices-to-build-upon-lyra/515743/22)
- **Lyra:** some developers weigh Lyra against GAS Companion as a base [snippet] — [Epic forum](https://forums.unrealengine.com/t/building-on-top-of-lyra-vs-gas-companion/1270464)
- **Observable maintenance risk:**
  - DCS's last dated update is July 2023 (UE 5.2+) [fetched] — [Fab DCS Bundle](https://www.fab.com/listings/82994e04-68bb-4434-bf95-763d340a5029)
  - ACF LITE was never migrated to Fab [snippet] — [UE Marketplace](https://www.unrealengine.com/marketplace/en-US/product/ascent-combat-framework-acf-lite-c-action-rpg-creator)
  - A DCF snippet lists support only for UE 5.2–5.4 [snippet] — [DCF](https://docs.unrealengine.com/marketplace/ko/product/dynamic-combat-framework-dcf)
- **SLF tuning:** a user found the shipped boss AI tuning sluggish (7–8 s strafing, 10 s minimum cooldown) [fetched] — [Epic forum](https://forums.unrealengine.com/t/soulslike-framework-complete-soulslike-kit/2443346)

### Inferences
- **Engine-version risk:** pinned to UE 5.8.3, we are exposed to listings that lag engine versions (DCS, DCF). Verify that a 5.8 build exists before buying.
- **Our rules point to reuse, not adoption:** C++ logic, no GAS, StateTree, and a 60 fps budget all argue for using frameworks as reference code or for isolated C++ pieces (lock-on, targeting, stats), not as the game's foundation.
- **Kits that pull in GAS:** ACF, Insodimension targeting and similar kits require a GAS decision first.

### Gaps
- **Blueprint performance:** no sourced measurements of Blueprint-heavy frameworks (Tick counts, ms cost).
- **Upgrade pain:** no first-hand postmortem on migrating a framework-based project across UE versions, and no shipped indie game named as built on ACF, DCS or SLF.
- **Unread primary threads:** the Reddit thread could not be fetched, so its upvote counts and context are unverified.
- **Fab licensing:** no source on Fab license terms for team use (seat-based "professional" licence for a 4-person team).
