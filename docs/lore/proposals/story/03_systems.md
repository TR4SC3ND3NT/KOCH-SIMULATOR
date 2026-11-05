PROPOSAL — not canon. A human lore author must approve and move it into docs/lore/canon/.

# KOCH-SIMULATOR: Story-driven systems

Design rules for R3 (gameplay) and R4 (narrative/UI). Numbers are starting values for tuning.

## 1. KOCH alert meter (HUD top-left "KOCH ALERT")
| Level | Name | Meaning | AI behaviour | HUD / audio |
|---|---|---|---|---|
| 0 | Calm | Nobody looking for Dan | Patrols walk routes; civilians ignore a holstered guitar case | Meter empty, no music |
| 1 | Suspicious | Something is off (masked person on camera, Post One silent) | Nearest patrol walks to the last report point; guards stop and stare at a masked man | Meter 25 %, low pulse |
| 2 | Search | Security is hunting a described suspect | Patrols in pairs, check hiding spots, radio chatter; FaceGates refuse all masked people | Meter 50 %, search music layer |
| 3 | Combat | Shots fired / Dan seen armed | All enemies in the zone engage; tactical team spawns from the nearest entry | Meter 75 % red, combat music |
| 4 | Lockdown | Campus sealed (after M06) | Permanent; shutters, fail-locked doors, teams roam; no decay | Meter full, flashing, siren bed |

**Raises**
- Masked Dan in a CCTV cone for 2 s: +1 (max 2). (Cameras: every room and corner has one per specs.)
- Dan seen with the rifle drawn by a guard or reactive civilian: → 3 (civilians call it in after 3 s; stop them by leaving their sight).
- Body found: +1. Gunshot (unsuppressed) heard: → 3.
- Scripted: M01 refusal (→1), M02 Temirov order (→2), M04 PC login (→3), M06 SIGHT shutdown (→4).

**Decay**
- 3 → 2 after 30 s with no enemy line of sight. 2 → 1 after 60 s hidden. Never below the mission's scripted floor (M02–M03: 2 after Temirov's order; M04–M05: 2; M06–M08: 4).

## 2. Mask and FaceGate rule
- **Masked:** cameras cannot identify Dan, so they flag "UNIDENTIFIED – MASKED" (+1 per rule above). FaceGates refuse him.
- **Unmasked:** SIGHT knows Dan's face from his visit two weeks ago: any camera match = instant alert 2 + Temirov gets a name. Therefore the mask stays on; there is no unmask button until the ending.
- **After M06 (SIGHT shut down):** cameras are dark; the mask no longer matters to cameras, only to people. FaceGates are fail-locked (doors need keycards or force).
- **Ending A:** unmask is the final player action; the FaceGate at the exit reads "IDENTIFIED: DANIYAR".

## 3. Stealth vs loud
| Tool | Use | Noise | Notes |
|---|---|---|---|
| Guitar case (holster) | Rifle hidden; Dan reads as a musician | – | Draw (Q) takes 1.2 s (unzip + lift). Civilians react only to a drawn rifle. |
| Pepper spray | Non-lethal stun 4 s; then knife or walk past | Low | 3 charges; refill at Brew Point (M02) and Clinic (M07). Story use: Kuban (M01), Temirov (M08 phase 3). |
| Knife | Silent takedown from behind / on a stunned enemy | Silent | Bodies must be hidden (drag) or they raise the alert. |
| Rifle | Loud; the game's main weapon (30/90 HUD) | Loud | Ammo from tactical team and elite drops; patrol pistol ammo does not fit. |
| PA panels (Dan's skill) | Wall panels in B, C, A: play a scripted announcement to move guards/civilians ("Fire drill on floor 2"; "Coffee delivery at the north door") | – | 1 use per panel, 6 panels total. Dead after M06 except the Assembly Hall AV desk. |
| CCTV | Shoot (noise +1) or cut at a junction box (silent, 3 s) | – | Junction boxes: one per floor in C, one at the gate booth. |
| Keycards | Level 1 Post One (gate, B), Level 1 Nurai (B, C entrance, C F5, Clinic service), Level 3 Ermekova (C-001, Clinic ward) | – | Shown as icons beside the objective. |

- Every mission is finishable loud. Stealth reward: fewer enemies spawned (the tactical team in M04 is 4 if alert reaches 3 before the PC, 2 if Dan reaches the PC unseen).
- **Civilians** never appear in objectives, never drop loot, flee and hide. Shooting a civilian = immediate fail ("KOCH would like that."). Melee on civilians is disabled.

## 4. Health and saves
- Health bar (HUD bottom-left), no auto-regen above 30 %; medkits at the Clinic, Brew Point first-aid box, and on tactical team leaders.
- Checkpoints are listed per mission in 01_walkthrough.md; death reloads the last one with the alert level it had.

## 5. Phone and radio
| Channel | Device | Who | When |
|---|---|---|---|
| Phone calls | Dan's phone (HUD subtitle + portrait) | Nurai | M00 voicemail, M00 bus call, M03 after she leaves, M06 piano, M07 lockdown, ending A |
| Security radio | Kuban's radio (from M01) | Temirov, team leads, dispatch | Ambient chatter tells the player where patrols go; scripted lines for story beats |
| PA | Building speakers | KOCH announcer, Temirov (lockdown) | Ambient corporate jokes; Temirov's PA lines in M06–M08 |

- Nurai never gives map markers; she gives verbal directions and context (grounded).
- Radio chatter is the stealth hint system: "Team 2 moving to the garden north arch" = avoid that route.

## 6. Companion use (existing companion NPC)
| Mission | Companion | Behaviour | Rules |
|---|---|---|---|
| M03 | Nurai | Leads (inverse follow: walks ahead, waits at corners, crouches when a patrol is near) | Not a target at alert ≤ 2; at alert 3 she drops to scripted cover and is invulnerable to enemy fire. Player shooting her = fail. Leaves at the end of M03. |
| M07 | Aibek | Follows Dan (existing follow behaviour), slow walk, flinches at gunfire | Takes no enemy damage while in cover; hides when Dan fights; teleport catch-up allowed indoors only. Stays in the Archive for M08. |
| Endings | Aibek | Walks beside Dan (cutscene) | – |

Prototype note: the "explodes when shot" behaviour must be off for story companions.

## 7. Collectibles (20)
Picked up = readable in a "Evidence" journal. Types: E = email/document, A = audio log, P = SIGHT profile.
| ID | Type | Title | Content (one line) | Location (mission) |
|---|---|---|---|---|
| C01 | E | "Notice of Resignation" | KOCH HR thanks Aibek for his "voluntary resignation" and wishes him well "in his new city". | Apartment table (M00) |
| C02 | A | "Song idea #4" | Aibek on his phone, humming the old song, joking that Dan stole it. | Dan's phone (M00) |
| C03 | E | "Safe City flyer" | "Faces are the new keys" – SIGHT pitch to citizens, with a phone number to report "suspicious behaviour". | Bus seat (M00) |
| C04 | E | "Post One shift log" | Kuban's handwriting: "22:40 – 2 interns out via Post Two, Security escort, no bags. Again." | Gate booth (M01) |
| C05 | P | "FaceGate event: UNIDENTIFIED" | Gate camera frame of masked Dan, auto-tagged "risk: unknown, posture: tense". | Booth monitor (M01) |
| C06 | E | "Join the Talent Program!" | Poster/leaflet: "No salary. All future." Fine print: consent to "image and behaviour recording". | B lobby (M02) |
| C07 | P | "Demo profile: Citizen 00412" | A sample SIGHT profile of a bus driver: routes, mood score, "Watch" because he attended a strike. | B demo lab (M02) |
| C08 | E | "Order slip #5531" | Brew Point printer: "Clinic room 4 – black tea, 3 sugars, for the boy. Daily." | Brew Point (M02) |
| C09 | A | "Voice note to Nurai" | Aibek, scared, whispering: if he vanishes, tell Dan "the old song"; he is sorry about the coffee money. | Nurai's phone, west gazebo (M03) |
| C10 | E | "Drill memo" | Temirov: response teams to drill "detention of non-compliant visitors" on the courts, Thursdays. | East gazebo FireBoard (M03) |
| C11 | E | "Chord chart" | Pencilled chords of the old song with "piano 2, low" in Aibek's handwriting. | Aibek's desk, room 203 (M04) |
| C12 | E | "Cell 203 quota" | Annotation targets: 400 faces/hour/intern; "below 300 = extension of unpaid period". | Instructor PC, room 203 (M04) |
| C13 | P | "Profile: DANIYAR" | Dan's own profile: street musician, ex-contractor, "agitator, crowds 40+", tier Watch. | Instructor PC, room 203 (M04) |
| C14 | E | "Cohort 9 retention minutes" | Management agrees to extend unpaid interns 3 more months "pending SIGHT go-live". | R207 meeting room (M04) |
| C15 | E | "RE: intern incident" | Ermekova to Lind: "Incident contained, subject stable in Health Center, asset recovery pending. Not before the signing." | Ermekova's PC, F5 (M05) |
| C16 | A | "Analyst, 23:10" | A tired analyst records a memo to himself: the Refer queue sent 40 people to police review today, he wants to quit. | F5 analyst office (M05) |
| C17 | E | "Studio rehearsal rota" | Staff studio piano booking sheet; Aibek's name every lunch hour until three weeks ago. | Piano room notice (M06) |
| C18 | E | "Contract annex 4: Referral thresholds" | City contract: SIGHT "Refer" tier triggers police detention review without a warrant in pilot districts. | Node room terminal (M06) |
| C19 | E | "Patient 4 chart" | No name; sedation protocol; "Security hold – T. Do not discharge. Relocate after 12:00." | Clinic desk / Elmira (M07) |
| C20 | E | "AV install contract" | KOCH contract for the Assembly Hall AV booth; installer "D." – unpaid final invoice stapled on top. | Archive (M07) |

Collecting C11 is required (story). C18 and C19 are auto-collected by objectives. The rest are optional.
