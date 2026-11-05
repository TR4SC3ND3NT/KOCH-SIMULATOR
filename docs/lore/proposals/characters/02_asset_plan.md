PROPOSAL — not canon. A human lore author must approve and move it into docs/lore/canon/.

# Character asset plan (R2, 2026-11-05)

Fab link = `https://www.fab.com/listings/<id>`. Prices in USD, from the 2026-11-05 shortlist. **Free first**; paid items are optional upgrades.

## Perf tiers
| Tier | Use | Mesh / hair / face | Textures | Cap |
|---|---|---|---|---|
| **T0 hero-closeup** | Dialogue and cutscenes (Arsen in mirror/cutscene, mains) | MetaHuman LOD0–1, strand groom (cards beyond ~5 m), RigLogic face + MetaHuman Animator | Face 2k streamed (4k off at 1080p) | 2 per frame |
| **T1 mid** | Enemies, companion, speaking minor NPCs, close civilians | MetaHuman LOD2–4 or ready rigged mesh; **card/mesh hair only**; face rig only while speaking | 1k–2k | 12 animated skeletal |
| **T2 crowd** | Street, bus far seats, lobbies, canteen | MetaHuman Collection (Crowd pipeline) via Mass; Instanced Skinned Mesh at distance (no correctives) | 512–1k shared | 60 visible |

## Per character / archetype

### Main cast
| Character | Build method (MetaHuman Creator recipe) | Paid upgrade (optional) | Skeleton / retarget | Tier | FREE placeholder now |
|---|---|---|---|---|---|
| **Arsen** | MHC: tall-thin male body; Central Asian preset blend, narrow face, high cheekbones, light-tan skin, stubble, brow scar (decal). Built-in long straight groom (loose) + ponytail variant (verify 5.8 groom list). Built-in hoodie/trousers if present; jacket from Urban Hoodie pack upgrade. Mask: Blender static mesh on head socket | Hair cards `c8806a9e-57c1-4bb5-970d-e9d26399f607` $29.99; Urban Adventure Hoodie, Pants, Boots `b48ed7f4-81fd-4082-ab50-8a075cb01099` $14.99; Bandit Face Mask #4 `8c95b263-8f02-4ebb-9065-b8966c921733` $9.99 (matches half-face mask; balaclava alt `120bbe31-2863-4437-bea6-4282e3850329` $19.99); Guitar Case PBR `4bda0854-db1a-4e67-9e46-6ab87ea8796f` $5.99; Pepper Spray `401c648c-0d50-4161-948d-67fe3eb4ea51` $0.99 | MetaHuman body; GAS anims via compatible skeleton or IK Retargeter. First Person Rendering: head, groom and mask hidden to owner in FP (shadow-only), body visible | T0 (cutscene/mirror), T1 body in FP | MetaHuman Creator (in-engine); greybox: NoEdge Free Rigged Male `4f540229-7bdf-44d0-b486-8af9fbb3d82d`; knife: Combat Knife `0e9cae3a-2854-40be-ab39-ede90689665c` |
| **Isa** | MHC: average-slim male; youthful round face, clean-shaven, short undercut groom, glasses accessory (built-in or Blender). Outfit: patient gown (Blender/Marvelous cloth sim → static skinned) | — | MetaHuman body; GAS + injured walk (Mixamo) | T0 rescue, T1 follow | MetaHuman Creator; greybox NoEdge Male |
| **Nurai** | MHC: short slim female; oval face, warm medium skin, freckles, nose stud; high messy bun groom (cards for companion LOD). Apron as Blender mesh over built-in long-sleeve/jeans | MetaHuman Casual Outfit Pack `08842273-aee9-47f7-85f9-f1ae45b51834` $24.99 | MetaHuman body; GAS locomotion; companion = `AKochCompanion` with skeletal mesh (anim BP path already supported) | T0 dialogue, T1 companion | MetaHuman Creator; greybox NoEdge Free Rigged Female `4f84cde6-f6b7-4bae-963b-50b417e77ebb` |
| **Azamat** | MHC: heavy male body; broad weathered face, moustache groom, grey buzz cut. Uniform: re-tint police uniform to KOCH grey-blue, add cap + soft vest | MetaHuman Police Uniform Outfit Pack `023830ca-04d1-4537-9dfa-35287ad420f0` $19.99; alt Modular Security Guard `fa32ca3a-5ae8-44a1-b655-4a58a67952a9` $27.99 | MetaHuman body; checkpoint idles + paired takedown (see animation plan) | T0 at gate cutscene | **Urban Security Officer** `4e63f4d8-eabe-45d0-91d2-a6d7a7d44494` (free) |
| **Temirov** | MHC: tall athletic male; square jaw, scar decal, short beard (cards), short hair shaved sides. Combat kit: black re-tint of tactical guard outfit; office: polo + blazer | Executive Security Suit `dae420ad-67a1-465e-a965-eadc2580111d` $18.99 (office look); UK Armed Police Character `23b05cad-9794-442b-ab03-e8acaf8a06ad` $49.99 (tactical kit + 62 anims) | MetaHuman body; boss AnimBP child of enemy ABP | T0 boss fight (only T0 in that frame) | Urban Security Officer (black re-tint) |
| **Ermekova** | MHC: average slim female; sharp brows, light skin, low chignon groom, rectangular glasses. Blazer/blouse/trousers from built-in wardrobe if present | Business Suit Outfit, parametric `704ec500-c2ad-452d-8970-42e6842d496e` $49.99 | MetaHuman body; office idles | T0 cutscene, T1 otherwise | MetaHuman Creator; greybox NoEdge Female |
| **Lind** | MHC: tall lean male, 55; long face, silver swept-back groom, light tanned skin, rimless glasses. Three-piece suit | Classic Suit Tie `363cfce7-ae32-4b03-a335-606f0f1b524b` $19.99; alt Businessman, Corporate Male `19790a58-c93d-49fd-80d7-18ae1feb400a` $35.99 | MetaHuman body; podium/speech gestures | T0 broadcast | MetaHuman Creator; greybox Office Worker 3/4 (whichever is the suited male; check on import) |

### Minor named NPCs
All: MetaHuman Creator, card hair, T1, built-in wardrobe + re-tints. Speaking lines use audio-driven face animation (MetaHuman Animator audio-to-face) instead of performance capture.

| NPC | Recipe notes | Free placeholder |
|---|---|---|
| Talgat (bus driver) | Heavy male 58, flat cap, cardigan, hi-vis vest | Office Worker 3/4 re-dressed, or City Sample Crowds body |
| Ulukbek (booth) | Thin male 28, gelled hair; Azamat's uniform minus vest | Urban Security Officer |
| Aizada (PR host) | Female 27, blazer with KOCH logo decal, headset mic | Office Worker 3/4 |
| Meerim (intern) | Small female 20, long braid, intern polo | NoEdge Female |
| Zina-apa (cleaner) | Stout female 61, headscarf, work coat | City Sample Crowds body |
| Eldiiar (analyst) | Male 31, beard, hoodie, headphones mesh | NoEdge Male |
| Gulzat (HR) | Female 34, bob, cardigan | Office Worker 3/4 |
| Raisa (archivist) | Female 63, grey bun, knitted vest | City Sample Crowds body |
| Elmira (nurse) | Female 29, nurse tunic | NoEdge Female |
| Kamila (assistant) | Female 30, dress + blazer, earpiece | Office Worker 3/4 |
| Bolot (mini-boss) | Very broad male 34, shaved head, elite kit | Urban Security Officer (black re-tint) |

### Archetypes
| Archetype | Build method | Paid upgrade | Tier | Free placeholder |
|---|---|---|---|---|
| ENM_GuardCheckpoint / ENM_GuardPatrol | 4–6 MHC faces (ages 25–50) sharing one uniform outfit; material-instance variants (cap, vest, sleeves) | Police Uniform Pack $19.99 | T1 | Urban Security Officer |
| ENM_Tactical | Same faces, helmet + plate carrier meshes (face mostly hidden → cheap) | UK Armed Police $49.99 | T1 | Urban Security Officer + helmet static mesh |
| ENM_Elite / ENM_Bolot | Black re-tint of tactical kit, full-face helmet | Executive Security Suit $18.99 (off-duty elite) | T1 | Urban Security Officer (black) |
| CIV_* street, bus, garden, canteen | **Our own MetaHuman Collection**: 12–16 Central Asian + 4 Slavic MHC faces × built-in outfits → Crowd pipeline; City Sample Crowds outfits as extra variety | MetaHuman Casual Outfit Pack $24.99; Pedestrians `ce4f2dee-10b8-49c3-9dba-dc54d2131850` $49.99 | T2 (T1 for 2–4 nearest) | MetaHuman Crowd Sample `5f481d73-afb1-4d94-ba6e-7cabf5d296fa`; City Sample Crowds `903037e9-e1ac-4f41-96e8-1683c6fa7ad4` |
| CIV_OfficeStaff / Executive / Analyst | Collection subset with business wardrobe | Corporate Office NPC Pack `c5a1dc76-a94b-4ab5-8ad3-16878bffb72f` $29.99; Collection of office workers x10 `37f2ef30-2562-404a-8736-67c8cb5589ed` $29.99 | T2 / T1 | Office Worker 3 `007f9793-e57c-47dd-9ee0-0829a57bf1e4`, Office Worker 4 `1f38e404-0322-42d6-897d-5cec85c06175` |
| CIV_Intern | Collection subset, navy polo + lanyard decal | — | T2 / T1 | MetaHuman Crowd Sample |
| CIV_Cleaner / Cook / MedicalStaff | 2–3 MHC each, workwear re-tints | — | T1 | NoEdge Male/Female |
| Far background fill | — | — | T2 | Renderpeople Scanned 3D People Pack `2e872a96-686e-4955-8256-82fa19904f92` — licensed stock scans, allowed (owner dropped the likeness rule, README 2026-10-29); background only, not for named characters |

Notes:
- City Sample Crowds faces come from a US-city demo; use them for bodies/outfits and far crowd only. It dates from UE 5.0: verify it opens in 5.8.3 before relying on it.
- MetaHuman Collections are **Experimental** in UE 5.8 (Epic docs). Keep a fallback: City Sample Crowds or T1 skeletal NPCs with Animation Budget Allocator.
- `AKochCompanion` (playtest code) explodes on any damage; Nurai/Isa companion needs a non-lethal "downed" variant — request to R3/R4.
- `AShooterNPC` uses `HandGrip_R` sockets on both meshes: every enemy skeleton must expose `HandGrip_R` (add to MetaHuman body skeleton, same transform as Manny).

## Skeleton / retarget path
1. **Base:** UE5 Manny (`SK_Mannequin`) is the animation source skeleton (GAS, Lyra, template).
2. **MetaHumans:** MetaHuman body skeleton shares Manny bone names. Cheap path: add as compatible skeleton (translation retargeting = Skeleton for root/pelvis, AnimationScaled for the rest). Quality path (heroes): IK Retargeter `RTG_Manny_To_MetaHuman`, bake montages offline.
3. **Ready Fab characters** (Urban Security Officer, Office Workers, NoEdge): check rig on import; if not Epic skeleton → IK Rig + auto-retarget (IK Retargeter, 5.4+) from Manny.
4. **Mixamo** (`mixamorig`): IK Retargeter auto-retarget to Manny, then same path as above.
5. **Video mocap** (Rokoko Vision / QuickMagic free tiers, per R2 doc): export FBX → retarget to Manny → clean in Control Rig.

## Per-scene performance budget
Character targets (measure with `stat gpu`, `stat anim`, `memreport` on machine A): characters ≤ **1.5 ms GPU**, ≤ **1.2 GB VRAM**, ≤ **2.5 ms game-thread anim**.

| Scene | T0 | T1 (max) | T2 crowd (visible) | Notes |
|---|---|---|---|---|
| M00 Home | Arsen (mirror only) | 0 | 0 | Mirror = planar reflection off; use Lumen reflection or cubemap + cutscene camera |
| M00 Bus | 0 (Arsen FP body = T1) | 6 (Talgat + nearest passengers) | 6–10 seated + 20–30 street (Mass) | Passengers at back = T2; bus windows hide street LOD pops |
| M01 Checkpoint | Arsen + Azamat (cutscene) | 3 (Ulukbek, 2 guards) | 4–8 queue + 20 street | After cutscene Azamat drops to T1 |
| M02 Alley / B | Nurai (dialogue) | 6 | 10–15 | Nurai → T1 when companion |
| M03 Garden | 0 | 10 (8 enemies + companion + 1) | 6–10 | Hedge maze occludes; enable occlusion culling on characters |
| M04–M06 Block C | Ermekova (cutscene) | 10 | 12–20 interns | Interiors: aggressive LOD distance scale |
| M07–M08 Block A | Isa or Lind or Temirov (max 2 together) | 10 | 8–12 | Lind broadcast on hall screens = pre-rendered video on Media Texture, not SceneCapture |
| M08 Escape | 0 | 10 | 20–40 street | Isa follows as T1 |

Crowd LOD strategy:
- **Near (< 10 m):** up to 4 civilians as T1 skeletal MetaHumans (full AnimBP, URO on).
- **Mid (10–40 m):** MetaHuman Collection Mass entities, skeletal LOD3+, card hair.
- **Far (> 40 m):** Instanced Skinned Mesh (no post-process AnimBP), Mass `LOD Params` max counts per LOD; Spawning Count Scale per quality preset (Low 0.5, High 1.0).
- Animation Budget Allocator for all T1; Significance Manager drives tick rate.
- Grooms: strands only on T0 and only in cutscenes/dialogue; gameplay forces card LOD. Groom physics only on Arsen's ponytail in cutscenes.

## Animation plan
| Need | Free source (now) | Paid upgrade | Custom mocap |
|---|---|---|---|
| Locomotion (hero, T1 NPCs) | **Game Animation Sample** `880e319a-a59e-4ed2-b268-b32dac7fa016` (Motion Matching, hero + companion only); simple blendspaces from it for enemies | NPC Animation Pack `99dc596f-c389-4c57-8e73-62a041131998` $24.99 (walk styles) | — |
| Crowd walk/idle | MetaHuman Crowd Sample anims; City Sample crowd anims | — | — |
| Weapon aim/fire/reload (enemies) | Template shooter anims (already in project); Lyra Starter Game (Epic, free; verify 5.8) | UK Armed Police (62 anims) $49.99 | — |
| Bus sitting / standing rail / sway | Mixamo (search: sitting idle, sitting texting, sitting asleep) | **Public Transport Passenger Mocap** `0e455c9e-c5c1-4c55-9e58-70c37ed923a6` $9.99 (55 anims, Manny); Get On Bus `b0902cd1-62c3-474c-a5fa-2227d4633a03` $14.99 | Driver loop (1 clip) |
| Guard checkpoint idle / questioning | Mixamo (standing idle, talking, arguing, pointing) | Police Officer Animations `8e29f282-6aaa-4edf-aa66-da380c24045d` $19.99; Conversation Gesture MoCap `c3a1ed6f-022a-49ef-a942-1bfee0a151b6` $19.99 | Questioning beat: step out of booth, hand-up "stop", point at mask |
| Pepper-spray reaction | Mixamo stand-in (hit react to face, stagger) | — | **Required:** spray hit → eyes covered stagger → bend over (3 clips) |
| Knife takedown | Combat Knife mesh (free); Mixamo stab stand-in | Knife Animations Pack `8a1cf447-2ba1-412a-9e57-62a4ce90bf28` $30.99; Combat Knife With FPS Animations `151f66e9-8a58-4d75-8dff-952c02e18930` $34.99 | **Required:** paired montage (Arsen full-body + Azamat), synced via Motion Warping; FP camera on Arsen's head bone |
| Typing / coffee / phone | Office Worker 3/4 bundled anims (check); Mixamo (typing, drinking) | NPC Animation Pack $24.99 | — |
| Cleaning, cooking, eating | Mixamo (mopping, sitting eating) | — | Cook stir loop if Mixamo lacks |
| Cowering / hands-up / flee | Mixamo (terrified, cower, hands up) | NPC Animation Pack $24.99 | — |
| Hit reacts / deaths | GAS + Lyra hit reacts; ragdoll already in `AShooterNPC` | UK Armed Police $49.99 | — |
| Face (dialogue) | MetaHuman Animator (performance or audio-driven); RigLogic | — | Team VO + phone/webcam capture |
| Lind speech, Temirov taunts | Conversation gestures from Mixamo | Conversation Gesture MoCap $19.99 | Podium speech (1–2 min) |

Mixamo: free with an Adobe account, royalty-free for games — https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html. Crowd docs: https://dev.epicgames.com/documentation/metahuman/metahuman-crowds-in-unreal-engine, sample: https://dev.epicgames.com/documentation/metahuman/metahuman-crowd-sample-tutorial.

Recommended low-cost paid bundle (if approved): Passenger Mocap 9.99 + Bandit Face Mask 9.99 + Police Uniform 19.99 + Classic Suit 19.99 + Hair cards 29.99 + Guitar Case 5.99 + Pepper Spray 0.99 = **$96.93**.

## Import checklist (R2, in order)
Allar rule: Fab packs stay in their own vendor folder (untouched, easy to update); our assembled assets (BP, MI, ABP, retargeted anims, MetaHuman character assets) go under `Content/KochSimulator/Characters/`.

| # | Step | Target folder | Done when |
|---|---|---|---|
| 1 | Add **Game Animation Sample**; migrate locomotion + retarget assets | `Characters/Shared/Animations/Locomotion/`, `Characters/Shared/Retarget/` (`IK_Manny`, `RTG_Manny_To_MetaHuman`) | Manny anims play on a MetaHuman body in PIE |
| 2 | Add **MetaHuman Crowd Sample** plugin; run its sample map on machine A | plugin (own folder) | `stat gpu` numbers logged in `docs/decisions.md` |
| 3 | Build **Arsen** in MetaHuman Creator; FP setup (owner-no-see head/groom/mask, shadow-only) | `Characters/Arsen/` (`MHC_Arsen`, `BP_Arsen`, `ABP_Arsen`, `SM_Arsen_Mask`) | Works with R3's character in FP + mirror |
| 4 | Add **Urban Security Officer**; retarget; `BP_Enemy_GuardCheckpoint` (child of R3's ShooterNPC BP), `HandGrip_R` socket | `Characters/Enemies/GuardCheckpoint/` | Guard patrols and shoots in PIE |
| 5 | Add **Office Worker 3 & 4**, **NoEdge Male/Female**; retarget | `Characters/Civilians/OfficeWorker/`, `Characters/Placeholders/` | Placeholders for all mains/minors placed |
| 6 | **Combat Knife** → hand to R3 (`Content/KochSimulator/Weapons/`); R2 adds hand sockets | `Weapons/` (R3) | Knife attaches to Arsen's hand |
| 7 | Build **Azamat** (MHC) + record pepper-spray and takedown mocap | `Characters/Azamat/`, `Characters/Shared/Animations/Takedown/` (`AM_Takedown_Knife_Arsen`, `AM_Takedown_Knife_Victim`) | M01 sequence plays end-to-end |
| 8 | Build own **Central Asian MetaHuman Collection** (12–16 faces); add **City Sample Crowds** (verify 5.8) | `Characters/Crowd/` (`MHCOL_Civilians`), vendor folder | 40 crowd agents in street test ≤ budget |
| 9 | Build Nurai, Temirov, Isa, Ermekova, Lind (mission order) | `Characters/<Name>/` | Each has T0 + T1 LOD setup |
| 10 | Mixamo pulls (sitting, typing, cower, cleaning) → retarget | `Characters/Shared/Animations/Civilian/` | Idle sets assigned per archetype |
| 11 | Paid bundle (on approval) | vendor folders + `Characters/<Name>/` | — |

Naming: `SK_` skeletal mesh, `SKEL_` skeleton, `PHYS_` physics asset, `ABP_` anim BP, `A_` sequence, `AM_` montage, `BS_` blend space, `IK_`/`RTG_` IK rig/retargeter, `MI_`/`M_`/`T_`, `BP_`. Minor NPCs under `Characters/Minor/<Name>/`, archetypes under `Characters/Enemies/<Archetype>/` and `Characters/Civilians/<Archetype>/`.

## Import status (2026-11-05)
Acquired to the team Fab library: all 10 free items above. Imported into the project (FBX/glTF via Interchange) under `Content/KochSimulator/Characters/Vendor/` and `Content/KochSimulator/Weapons/Vendor/CombatKnife/`:

| Pack | Result | Fix needed |
|---|---|---|
| Urban Security Officer | SK + skeleton + physics + 4 anims, 180 cm | Textures were not in the FBX: download the Blender format or re-link maps |
| Office Worker 4 | SK + 3 anims, 184 cm | Textures ship in a separate folder: import `textures/` and wire the 10 MIs |
| Office Worker 3 | glTF split into 9 skeletal meshes | Re-import from the Blender format as one mesh |
| NoEdge Male / Female | SK + textures, 186 / 165 cm | Retarget to Manny |
| Combat Knife | SM + 4 textures, but ~430 cm long | Scale ≈ 0.07 on import or at the hand socket (R3) |
| City Sample Crowds, MetaHuman Crowd Sample, Renderpeople, Game Animation Sample | UE-format only | Add through the Fab panel in the editor or the Epic Launcher (samples are separate projects; migrate content) |
