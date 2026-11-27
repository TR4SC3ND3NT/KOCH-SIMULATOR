# Animation pipeline and asset sources for near-AAA character animation in small UE5 teams (UE 5.4–5.8, 2026)

Context: KOCH-SIMULATOR runs UE 5.8 on Apple Silicon, with MetaHuman enemies and Lyra rifle/pistol clips. The target is 60 fps at 1080p on an RTX 3070 Ti laptop.
Research budget: 14 search/fetch calls. Items marked "(unsourced, prior knowledge)" are the researcher's own knowledge, not findings. unrealengine.com blog/tech-blog pages returned HTTP 403, so facts from them come from search snippets only and are marked "(snippet)".

## 1. Epic's Game Animation Sample (GASP): contents, versions, extension, cost, license

### Takeaway
GASP is Epic's free, Fab-distributed sample. It has 500+ mocap animations on the UEFN Mannequin, motion matching driven by Chooser tables over Pose Search databases, traversal (vault/climb/drop), and a MetaHuman body sandbox. The docs say it is updated with each major release. The versions actually seen are 5.4 (launch), 5.5 (via the Hollowborn report), 5.7 (Dec 2025) and 5.8 (Aug 2026); no 5.6 version turned up. Epic's blog says the animations may be used and retargeted freely. I did not see the formal license text.

### Cited Findings
- **Versions.**
  - First released with UE 5.4 — [Epic tech blog, 5.7 update](https://www.unrealengine.com/en-US/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7) (snippet; page 403).
  - UE 5.7 update, Dec 2025: main addition is the Mover plugin (Experimental), plus a slide mechanic — same source (snippet).
  - UE 5.8 update, dated 12 Aug 2026 — [Epic tech blog, 5.8 update](https://www.unrealengine.com/tech-blog/download-the-latest-game-animation-sample-project-now-updated-for-ue-5-8) (snippet; page 403).
  - The docs page sits in the UE 5.9 doc set and says the project is updated with each major engine release. It has no formal compatibility table — [Epic docs: Game Animation Sample Project](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine).
- **Size and distribution.** "500+ game-ready animations", free on Fab — [Epic blog: Get over 500 free animations](https://www.unrealengine.com/en-US/blog/game-animation-sample) (snippet).
- **Usage rights.** Epic's blog: "You're free to use all these animations with or without their accompanying animation Blueprints and retarget them to your own characters" — [Epic blog](https://www.unrealengine.com/en-US/blog/game-animation-sample) (snippet). This is a blog statement, not license text. The Fab listing page ([fab.com/s/46a85e1ef0c5](https://fab.com/s/46a85e1ef0c5)) returned no readable license text.
- **Architecture** (all from [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine)):
  - Motion matching queries the character's movement model and picks poses from Pose Search databases.
  - The Pose History node supplies the trajectory.
  - Chooser tables filter which databases are eligible by gameplay context (e.g. walk databases only while walking). The docs say this filtering also improves performance.
  - Databases live under `Content/Characters/UEFN_Mannequin/Animations/MotionMatchingData/Databases`.
  - Traversal (vault, climb, drop) runs as montages through the Default Slot.
  - Base skeleton is the UEFN Mannequin. `CPB_Sandbox_MetaHuman_Bodies` switches MetaHuman body types (keys 1–9, 0 toggles masculine/feminine).
  - Custom characters are set up through an IK Retargeter.
- **Debug and perf tools in the sample** — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine):
  - max-FPS caps, timescale
  - "Motion Matching Database LOD" to compare dense vs sparse data.
- **Known issues** — same docs page:
  - the Offset Root Bone node is experimental (no collision checks, hard-coded interpolation)
  - turn-in-place while aiming is still in progress.
- **Reusing assets.** Migrate the AnimSequences from `Content/Characters/UEFN_Mannequin/Animations` into another project (right-click > Migrate), or Export — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine).
- **How people extend it:**
  - A 2025 student souls-like ("Hollowborn") adapted motion matching from Epic's UE 5.5 sample and used motion warping for combat — [Staffordshire Univ. Hollowborn dev report, Apr 2025](https://gradex.staffs.ac.uk/wp-content/uploads/2025/04/5055_Hollowborn-Dev-Report.pdf) (snippet).
  - An indie devlog adds turn matching with motion matching plus procedural warping for weapon-equipped movement — [LonelyGameDev itch.io devlog, Aug 2025](https://itch.io/devlog/999625/realistic-turn-matching-motion-matching-usecase.amp) (snippet).
- **Per-character cost (community, UE 5.7, one character)** — [Epic forum: State Machine vs Motion Matching perf analysis](https://forums.unrealengine.com/t/state-machine-vs-motion-matching-demo-performance-analysis-share/2721152):
  - GASP motion-matching locomotion selection about 0.25 ms
  - total worker-thread anim eval about 0.50 ms
  - game-thread anim about 0.14 ms
  - See section 2 for caveats.

### Inferences
- GASP is unlikely to be Fab "Reference Only" content, because Epic invites retargeting to your own characters. It is most likely shippable in a commercial UE game, but confirm the license tab on the Fab listing before shipping.
- GASP is a locomotion/traversal sample. It has no sword combat and no weapon/aim layers beyond basics, so souls-like attacks and shooter aiming need other sources (section 5) plus warping (section 4).
- The 5.7+ versions are Mover-based (`SandboxCharacter_Mover`) alongside a CMC variant (`SandboxCharacter_CMC`, seen in the forum thread in section 3). A project on CharacterMovementComponent should take the CMC variant.

### Gaps
- Exact license text on the Fab listing (Standard vs other); page not readable.
- Exact 5.8 changelog contents (page 403).
- Exact animation count per version.
- Official Epic per-character CPU numbers.

## 2. Motion matching vs classic state machine + blend spaces (Lyra style)

### Takeaway
Motion matching costs more CPU to pick the pose (one community profile: about 0.25 ms vs 0.008 ms per character). Total anim worker cost per character was similar (0.50 vs 0.43 ms), because other nodes dominate. For about 10 enemies the extra cost would be a few ms of aggregate worker-thread time, which URO/LOD can cut. That figure is extrapolated from one user's UE 5.7 profile of a single character, hardware unstated. Epic's docs name channels and sample rate as the main cost levers.

### Cited Findings
- Epic docs on cost — [Epic docs: Motion Matching](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-matching-in-unreal-engine) (snippet):
  - more channels and more samples per channel raise memory and runtime cost; use as few channels as needed
  - a higher Sample Rate gives more refined searches but more memory
  - query cost against an indexed pose is the sum of the channel costs.
- Community profile, UE 5.7, Unreal Insights, same machine for both (specs not given), both scenes GPU-bound — [Epic forum thread](https://forums.unrealengine.com/t/state-machine-vs-motion-matching-demo-performance-analysis-share/2721152):

  | Per character | State machine (19 chars, averaged) | GASP motion matching (1 char) |
  |---|---|---|
  | Locomotion selection | 0.008 ms | about 0.25 ms (about 31x) |
  | Worker-thread eval | about 0.43 ms | 0.50 ms |
  | Game-thread anim | about 0.07 ms | about 0.14 ms |

  - In the state-machine scene, PoseDriver (0.21 ms/char, 3.94 ms total) and ControlRig (0.08 ms/char) were the largest costs. These are independent of the locomotion method.
  - The author projects that moving the 19-character scene to motion matching adds about 4.6 ms of aggregate worker time, reducible with URO (Update Rate Optimization).
  - Worker figures are aggregate CPU time across workers, not wall-clock game-thread time.
- Chooser filtering of databases reduces the data searched and improves performance — [Epic docs: GASP](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine).
- Research: motion matching is expensive because the database is searched repeatedly. A GPU-parallel approach in UE cut CPU time — [GPU-based Motion Matching for Crowds in UE (SIGGRAPH Asia 2020 poster)](https://katalog.lib.cas.cz/KNAV/EdsRecord/edsair,edsair.doi...........d1b4aadea41e63b7bddb12a354a05ee9) (snippet).
- Pose Warping lets you reach the same movement coverage with fewer animations — [Epic docs: Locomotion](https://dev.epicgames.com/documentation/unreal-engine/locomotion-in-unreal-engine) (snippet).

### Inferences
- 10 enemies at about 0.25 ms extra selection each is about 2.5 ms of aggregate worker time. That figure is extrapolated from one UE 5.7 sample, not measured. Anim work runs in parallel worker tasks (the profile shows parallel worker tasks), so the game-thread impact should be well under that. Both profiled scenes were GPU-bound.
- (unsourced, prior knowledge) A common split:
  - motion matching for the player
  - for enemies, either motion matching with sparse DB LOD / URO, or a state machine + blend spaces + pose warping.
  - Lyra's AnimBP (state machine, distance matching, stride/orientation warping) is a lower-cost baseline.
- (unsourced, prior knowledge) Quality: motion matching gives better starts/stops/pivots and less hand-authoring of transitions with a large mocap set. A well-tuned state machine with warping looks close for shooter strafing.

### Gaps
- No sourced quality comparison (motion matching vs state machine) was found.
- No official Epic benchmark for N motion-matched NPCs.
- No measurements on Apple Silicon or the RTX 3070 Ti reference.
- Found no GDC source (For Honor / EA) in this pass, so no citation on their production numbers.

## 3. Retargeting (IK Retargeter, auto-retarget, MetaHuman, Mixamo/Lyra/GASP)

### Takeaway
Epic's documented workflow is IK Rig, then "Auto Create Retarget Chains" (MetaHuman skeletons are pre-set for it), then "Auto Create IK", then an IK Retargeter. Most findings are bug reports. UE 5.6 changed the retargeter to an op stack, and some users saw different results. In 5.7, auto-generation is sensitive to MetaHumans made in the new MetaHuman Creator. GASP ships runtime retargeting to MetaHumans (`Retarget Pose From Mesh` + `RTG_UEFN_to_Metahuman_nrw`). One 5.8-specific bug, "hook hands", has a known workaround.

### Cited Findings
- Building a custom retargeter — [Epic MetaHuman docs: Create a custom IK Retargeter](https://dev.epicgames.com/documentation/en-us/metahuman/create-a-custom-ik-retargeter) (snippet):
  - create an IK Rig, then Auto Create Retarget Chains (MetaHuman skeletons are pre-set for this), then Auto Create IK, then build the IK Retargeter.
- Epic recommends `RTG_MH_IKRig`-based retargeting for MetaHuman body animation, tuned for MetaHuman full-body IK. For faces it suggests auto-generating a retargeter — [Epic MetaHuman docs: Retarget MetaHuman Creator animation](https://dev.epicgames.com/documentation/metahuman/retarget-metahuman-creator-animation) (snippet; the snippet-to-URL mapping is unverified).
- Runtime retargeting — [Epic MetaHuman docs: runtime retargeting](https://dev.epicgames.com/documentation/en-us/metahuman/runtime-retargeting) (snippet):
  - GASP uses a `Retarget Pose From Mesh` node with IK Retargeter `RTG_UEFN_to_MetaHuman_nrw`
  - "Basic Translation Retargeting" moves animation between assembled MetaHumans.
- UE 5.6 introduced a new retarget op stack. The community "Mixamo Animation Retargeting V2" tool updated its generated IK Rigs/Retargeters for it, and added IK-bone support for the 5.6 Third Person template — [Epic forum: Mixamo Animation Retargeting V2](https://forums.unrealengine.com/t/mixamo-animation-retargeting-v2-for-unreal-engine-5-and-metahuman/552648?page=3) (snippet).
- 5.6 reports (anecdotal, no Epic confirmation):
  - different MetaHuman retarget results vs 5.5 — [forum: 5.6 Animation Retargeting Bug](https://forums.unrealengine.com/t/5-6-animation-retargeting-bug/2521595) (snippet)
  - auto-retarget failure fixed by building the IK Rig + Retargeter manually — [forum: Unable to retarget to MetaHuman 5.6](https://forums.unrealengine.com/t/unable-to-retarget-animation-to-metahuman-unreal-5-6/2539409) (snippet)
  - a community tutorial exists for retargeting template animations to MetaHumans in 5.6 — [forum tutorial](https://forums.unrealengine.com/t/community-tutorial-retarget-template-animations-to-metahumans-in-ue-5-6/2606313).
- UE 5.7: Auto Generate Retargeter is sensitive to MetaHumans made in the new MetaHuman Creator (`SKM_MHC` meshes) — [forum: retargeting broken on SKM_MHC (5.7)](https://forums.unrealengine.com/t/animation-retargeting-broken-on-new-skm-mhc-metahuman-skeletal-mesh-ue-5-7/2720169) (snippet).
- UE 5.8 + GASP "hook hands" bug — [forum: GameAnimationSample 5.8 bad retargeting to MetaHuman](https://forums.unrealengine.com/t/gameanimationsample-5-8-bad-retargeting-to-metahuman/2837097):
  - Symptom: MetaHuman wrists/hands stay bent at runtime via `Retarget Pose From Mesh`; the preview is fine.
  - Setup: `SandboxCharacter_Mover`, `ABP_GenericRetarget`, `RTG_UEFN_to_Metahuman_nrw`, `IK_Metahuman_Retarget` / `IK_UEFN_Mannequin`.
  - Reported fix: set the hidden source mesh `CharacterMesh0` to Forced LOD Model = 1. A hidden mesh can sit at a low LOD with no finger bones. `r.ForceLOD 0` did not help.
  - Temporary PIE workaround: `DDCvar.VisualOverride -1` and back.
  - No official response; cause unverified.

### Inferences
- Our enemies are `MHC_`-created MetaHumans on 5.8, so the 5.7 SKM_MHC auto-generate sensitivity and the 5.8 hook-hands LOD issue both likely apply. Use the Forced LOD fix, or offline-retarget clips to the MetaHuman skeleton instead of runtime `Retarget Pose From Mesh`.
- Runtime retargeting as GASP does it means a hidden source mesh plus a retarget node per character, which matters for 10 NPCs. (unsourced, prior knowledge) Offline batch retargeting (exporting retargeted sequences from the IK Retargeter) avoids that.
- GASP uses the UEFN Mannequin (cited in section 1). (unsourced, prior knowledge) Lyra uses the UE5 Mannequin. Mixamo clips need the community V2 tool or a manual IK Rig, because the Mixamo skeleton has no IK bones and uses different bone naming.

### Gaps
- No official Epic notes on 5.8 retargeter changes.
- No measured CPU cost of runtime `Retarget Pose From Mesh` per character.

## 4. Polish layers (Control Rig, foot IK, distance matching, warping, inertialization, procedural recoil)

### Takeaway
Epic's Animation Warping plugin provides Stride, Orientation and Slope Warping as AnimBP nodes. Motion Warping, a separate component plus montage notify windows, aligns root motion to targets, and indie souls-likes use it for melee. Distance matching drives starts/stops by distance-to-target. These are the main AAA-feel layers on top of either locomotion system.

### Cited Findings
- Pose Warping — [Epic docs: Pose Warping](https://dev.epicgames.com/documentation/en-us/unreal-engine/pose-warping-in-unreal-engine) (snippet):
  - requires the Animation Warping plugin; includes Stride, Orientation and Slope Warping plus the Root Motion Delta attribute
  - Stride Warping adjusts animated stride to match capsule speed
  - Orientation Warping rotates leg IK bones toward the movement direction and twists the spine to keep the facing angle.
- Motion Warping — [Epic docs: Motion Warping](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-warping-in-unreal-engine) (snippet):
  - dynamically adjusts root motion to align to targets
  - needs a Motion Warping Component on the Blueprint, with warp windows set in Animation Montages
  - API: [MotionWarping plugin API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MotionWarping).
- Distance Matching uses a calculated distance to/from a target to drive Animation Sequences — [Epic docs: Locomotion](https://dev.epicgames.com/documentation/unreal-engine/locomotion-in-unreal-engine) (snippet).
- In GASP, traversal montages are injected via the Default Slot, and Offset Root Bone is experimental — [Epic docs: GASP](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine).
- Indie souls-like practice:
  - "Use motion warping and generous hit boxes" — [Hollowborn dev report](https://gradex.staffs.ac.uk/wp-content/uploads/2025/04/5055_Hollowborn-Dev-Report.pdf) (snippet)
  - a solo UE5 souls-like prototype lists animation warping, blendspaces and AnimBPs for player and AI — [Alberto Coello souls-like prototype](https://sites.google.com/view/albertocoello/games/souls-like-prototype) (snippet).
- Control Rig cost reference: 0.08 ms per character in a 19-character UE 5.7 scene — [Epic forum perf thread](https://forums.unrealengine.com/t/state-machine-vs-motion-matching-demo-performance-analysis-share/2721152).

### Inferences
- (unsourced, prior knowledge) Melee: root-motion attack montages, plus a Motion Warping "lunge" window targeting the enemy (translation and rotation clamped), plus hit-stop/inertialized blends. Shooter: Orientation Warping for strafing, plus aim offsets, plus procedural recoil (additive Control Rig or code-driven bone offsets).
- Foot IK via Control Rig on 10 enemies costs about 0.8 ms aggregate worker time, based on the 0.08 ms/char figure from one scene. It can be disabled at distance via LOD thresholds.

### Gaps
- Did not fetch Epic pages on Inertialization, Control Rig foot IK or the Distance Matching node, so no citations or version notes for them.
- No source on procedural recoil/sway plugins.
- The UE version in which Pose Warping, Motion Warping and Distance Matching appeared or changed was not confirmed. The doc pages seen are current-version pages.

## 5. Animation asset sources and licenses

### Takeaway
What was verified:
- Mixamo is royalty-free for commercial games, but the raw files can't be redistributed.
- Fab's Standard License has Personal and Professional tiers; a forum post claims Personal is limited to small revenue (unconfirmed).
- Kubold's own FAQ says its license is personal, non-transferable, and covers use in your games.

Not verified:
- GASP's license text (only Epic's blog wording was seen).
- Lyra's license.
- Which license Kubold, GDH or other sword packs carry on Fab.
- Fab prices.

### Cited Findings
- **Mixamo.**
  - Adobe's FAQ: characters and animations are royalty-free for personal, commercial and non-profit projects, including video games, and free with no purchase — [Adobe Mixamo FAQ](https://helpx.adobe.com/au/creative-cloud/faq/mixamo-faq.html) (snippet).
  - Only restriction: don't distribute the raw character/animation files. Attribution not required — [Adobe community Mixamo licensing FAQ](https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/td-p/13234775) (snippet; 2022 thread, community post).
- **Fab licensing.**
  - Epic docs describe Standard License tiers, Personal and Professional. Personal may include a "Reference Only" (UEFN) version — [Epic docs: Licenses and pricing in Fab](https://dev.epicgames.com/documentation/en-us/fab/licenses-and-pricing-in-fab) (snippet).
  - A forum post says Personal applies under about $100k annual revenue; I could not confirm this in Epic text — [forum: Fab license terms](https://forums.unrealengine.com/t/fab-license-terms-standard-license/2094243/4) (snippet).
  - Legacy Marketplace license is being retired for new products — [forum: All free assets now Standard License](https://forums.unrealengine.com/t/all-free-assets-including-ue-ones-are-now-standard-license-on-fab-meaning-no-commercial-use/2080626) (snippet; the snippet-to-URL mapping is unverified).
- **Kubold.**
  - Kubold's FAQ: the license is for the buyer only, not transferable to other people/companies, and covers use in your video games — [Kubold Unreal FAQ](https://www.kubold.com/unreal-faq-2) (snippet).
  - Only verified price: Kubold "Longsword Animset Pro", $50 on the Unity Asset Store, 205 mocap animations — [Unity Asset Store](https://marketplace.unity.com/packages/3d/animations/longsword-animset-pro-92239) (snippet). That is Unity, not Fab.
- **Frank (old Marketplace) sword packs** exist: Frank Action RPG Sword 1 Basic Set, Frank RPG Great Sword, Frank RPG Dual, Frank Sword 2 — [Marketplace: frank action rpg sword 1](https://www.unrealengine.com/marketplace/en-US/product/frank-action-rpg-sword-1-basic-set) (snippets). For Sword 1 Basic Set only, the Japanese page says the seller has not migrated to Fab, so it is available only from the Epic Launcher vault — [ja note](https://www.unrealengine.com/marketplace/ja/product/frank-action-rpg-sword-1-basic-set).
- **Other Fab sword packs** (sellers not shown in snippets, so not attributable to Kubold):
  - "One Handed Sword Animation V1": 417 animations on the UE5 mannequin, root motion and in-place — [fab.com/s/e2d9de6366c4](https://fab.com/s/e2d9de6366c4) (snippet; the snippet-to-URL mapping is unverified).
- **Game Dev Hero (GDH) All Animation Bundle.** 2025 UE5 packs: sword & shield, dual sword, two-handed sword, unarmed V3. One sword pack lists 10 in-place + 10 root-motion animations — [itch.io GDH devlogs](https://itch.io/devlog/966242/added-new-animation-pack-sword-and-shield-animations-v1.amp), [two-handed](https://itch.io/devlog/984736/added-new-animation-pack-two-handed-sword-animations-v1.amp) (snippets).
- **Cascadeur.** Its blog spotlights indie melee projects: a solo UE5 melee combat system ("not a Souls-like, not a hack-and-slash") — [Cascadeur: OG Realistic Combat System](https://cascadeur.com/blog/view/indie-project-spotlight-og-realistic-combat-system); and Crowned in Steel, inspired by modern souls-likes and Severance: Blade of Darkness — [Cascadeur: Crowned in Steel](https://cascadeur.com/blog/general/indie-spotlight-crowned-in-steel) (snippets). There is also an article titled "Creating gameplay animations without an expensive mocap suit" — [80.lv](https://80.lv/articles/creating-gameplay-animations-without-an-expensive-mocap-suit/) (title only; content not read).

### Inferences
- A legal indie stack (GASP and Lyra licenses are unverified, see Gaps):
  - GASP for locomotion and traversal
  - Lyra for rifle/pistol (already used here)
  - one paid Fab melee pack (Kubold or GDH style), plus Mixamo for fillers
  - Cascadeur for custom hits, reactions and finishers.
- Each person who uses a paid asset may need their own seat: Kubold's license is personal and non-transferable. Check the Fab team/seat terms for a 4-person team.

### Gaps
- Not researched (no calls left): Paragon asset license terms, ActorCore/Reallusion pricing, MoCap Online pricing, Fab free-monthly content.
- No current Fab prices for Kubold UE packs.
- "Two Handed Sword Animation V3" appeared in a Fab snippet with no attributable URL.
- Lyra's license was not researched.
- The Fab Standard License full text (fab.com/eula) was not fetched.

## 6. Typical cost/time for a 4-person team to reach AAA-feeling locomotion + combat

### Takeaway
I found no reliable source quantifying cost or time for a small team. The only evidence is project-level: student and solo souls-like prototypes in UE 5.5 built on GASP motion matching plus motion warping.

### Cited Findings
- A student team adapted Epic's UE 5.5 motion-matching sample plus motion warping for a souls-like and playtested with souls-like players — [Hollowborn dev report](https://gradex.staffs.ac.uk/wp-content/uploads/2025/04/5055_Hollowborn-Dev-Report.pdf) (snippet).
- A solo developer built a UE5 souls-like combat prototype with animation warping and blendspaces for player and AI — [Alberto Coello prototype](https://sites.google.com/view/albertocoello/games/souls-like-prototype) (snippet).

### Inferences
- Asset cost is low: GASP, Lyra and Mixamo are free, plus a paid melee pack or two. Most effort goes into integration and tuning: retarget QA, warp windows, hit reactions and AI-driven anim selection.

### Gaps
- No sourced numbers for hours, weeks or budget. Do not estimate without data.
