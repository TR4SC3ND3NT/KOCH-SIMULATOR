PROPOSAL — not canon. A human lore author must approve and move it into docs/lore/canon/.

# KOCH-SIMULATOR: Mission walkthrough (~34 min)

Conventions
- Objective lines in quotes are HUD text (String Table keys TBD by R4).
- Alert: 0 calm / 1 suspicious / 2 search / 3 combat / 4 lockdown (rules in 03_systems.md).
- **AI cap: ≤ 8 active AI pawns at once** (enemies + companion + reactive civilians). Background civilians are crowd-lite (animation + flee path, no controller).
- Locations by spec name; EXISTS / NEEDS BUILD per 02_locations.md.
- Collectible IDs (C01…C20) are listed in 03_systems.md.
- Times assume a normal first playthrough (mix of stealth and combat, ~half the collectibles).

## Pacing table
| ID | Name | Min | Cumulative | Main location | Alert range | Peak AI |
|---|---|---|---|---|---|---|
| M00 | Morning Route | 4.5 | 4.5 | Apartment → bus → SITE_StreetFront → crossing | – | 0 enemies |
| M01 | FaceGate | 3.5 | 8.0 | SITE_Gate, BLD_GateBooth | 0 → 1/2 | 3 |
| M02 | Brew Point | 3.5 | 11.5 | SITE_GateAlley, BLD_B | 1 → 2 | 3 |
| M03 | Hedge Maze | 3.5 | 15.0 | SITE_Garden | 2 (↔3) | 5 (4 + Nurai) |
| M04 | Room 203 | 4.0 | 19.0 | SITE_CPlaza, INT_C_F1, INT_C_Floors F2 | 2 → 3 | 6 |
| M05 | The Attic | 3.0 | 22.0 | INT_C_Floors F3–F5 | 3 | 4 |
| M06 | Staff Studio | 4.0 | 26.0 | SITE_HallCPassage, INT_C_Basement | 2 → 4 | 5 |
| M07 | Health Center | 3.5 | 29.5 | SITE_CPlaza, BLD_A_N (Clinic), BLD_A_W (Archive) | 4 | 6 (5 + Aibek) |
| M08 | Assembly | 4.5 | 34.0 | BLD_A_W Assembly Hall → ending site | 4 | 8 (5 enemies + 3 fleeing delegates) |
| | **Total** | **34.0** | | | | |

Range: speed-run loud ≈ 26 min; full stealth + all collectibles ≈ 42 min.

---

## M00 Morning Route — 4.5 min
- **Start:** DAN_Apartment (NEEDS BUILD). **End:** SITE_Gate, north kerb of the Crossing (Zebra).
- **Characters:** Dan; Nurai (voicemail, then phone call); bus driver, passengers, pedestrians (civilians).
- **Objectives:**
  1. "Get up"
  2. "Pack the guitar case" (rifle + 2 magazines)
  3. "Take the pepper spray and the knife"
  4. "Put on the mask"
  5. "Walk to the bus stop"
  6. "Take the bus to KOCH HQ"
  7. "Get off at the KOCH HQ stop"
  8. "Cross the road"
- **Beats:**
  - Cold open (cutscene, 20 s): dawn over apartment blocks, KOCH tower ad on a roof, alarm 06:40.
  - In-game: small flat. Aibek's mattress made, his keyboard in the corner, missing-person flyers on the table, the KOCH HR letter (C01).
  - Packing is interactive: rifle into the guitar case (teaches the case = holster), spray, knife, mask (type: open question #3).
  - Voicemail from Nurai plays on the phone while packing (C02 is Aibek's older voice memo).
  - Street → bus stop. Bus ride is in-game, seated (60–90 s, skippable after first play). Bus radio news: "today KOCH signs the Safe City contract". Phone call with Nurai: plan and radio channel.
  - Get off at the stop, walk the SITE_StreetFront sidewalk, wait for the light, cross the Zebra. FaceTerminal_In visible ahead.
- **Encounters:** none. Civilians: 6–10 crowd-lite on bus/street; driver.
- **Alert:** meter hidden; it appears at the FaceGate.
- **Save points:** start; bus exit.
- **Key items:** guitar case (rifle, 30/60), pepper spray (3 charges), knife, mask, phone.
- **Cutscene vs in-game:** 20 s cutscene, rest in-game.
- **Optional:** C01, C02, C03 (Safe City flyer on the bus).
- **Player learns:** Aibek missing 3 weeks; KOCH says "resigned"; Nurai thinks he is inside; today is the signing.

## M01 FaceGate — 3.5 min (canon opening)
- **Start:** SITE_Gate sidewalk at Turnstile_In. **End:** top of SouthStair, SITE_GateAlley (gate plaza).
- **Characters:** Dan, Kuban; 2 patrol guards (late); Temirov (radio voice only).
- **Objectives:**
  1. "Get through the checkpoint"
  2. "Talk to the guard"
  3. "Deal with the guard"
  4. "Hide the guard in the booth"
  5. "Take the guard's radio and keycard"
  6. "Get through the checkpoint" (service door, keycard on CardReader_Booth)
  7. "Get to Brew Point"
- **Beats:**
  - FaceTerminal_In: red light, tone, screen "FACE NOT VISIBLE. REMOVE FACE COVERING." Turnstile_In stays locked. Alert meter appears at 1.
  - Kuban comes out of the booth door, questions Dan (dialogue `kuban_checkpoint`, 3 approaches, all converge).
  - Canon outcome, player-driven in first person: prompt → pepper spray to the face → prompt → knife (wounded, not killed; open question #4). Not skippable, no fail.
  - Drag Kuban into the booth (carry/drag). Take radio + keycard. Kuban's radio crackles: "Post One, check in." 45 s timer before a patrol pair walks down from the alley.
  - Booth details: Kuban's shift log (C04), FaceGate monitor showing Dan as "UNIDENTIFIED – MASKED" (C05).
- **Encounters:** Kuban (checkpoint guard, baton) 1 – scripted; patrol guards (pistol) 2 at T+45 s.
- **Alert:** 0 → 1 at the refusal. Stays 1 if Kuban is hidden and Dan is out of the gate plaza before the patrol arrives; else 2.
- **Save points:** at the Crossing; after the takedown.
- **Key items:** KOCH Security radio (hear patrol chatter), Post One keycard (booth, gate service door, B side doors).
- **Cutscene vs in-game:** all in-game; camera locks only during the 2 takedown prompts.
- **Optional:** C04, C05.
- **Player learns:** FaceGate is SIGHT's front door; Dan's unmasked face is already in the system; the radio lets him hear Security.

## M02 Brew Point — 3.5 min
- **Start:** gate plaza, SITE_GateAlley. **End:** BLD_B back (north) door onto the garden apron.
- **Characters:** Dan, Nurai, Temirov (radio); visitors, PR staff, baristas.
- **Objectives:**
  1. "Get to Brew Point"
  2. "Find Nurai"
  3. "Talk to Nurai"
  4. "Follow Nurai"
- **Beats:**
  - Alley: patrol pair answering "Post One". Bench and hedge cover along PathHedge/BankRose beds.
  - B EntrancePorch (east facade) → Visitor & PR Center lobby: a live FaceGate demo wall shows the gate camera; posters for the Talent Program (C06).
  - Optional demo lab: sample SIGHT profile kiosk (C07).
  - Brew Point: Nurai at the counter signals "back room". Dialogue `nurai_brewpoint`: "the old song", the Clinic tea order (C08), her delivery card.
  - Radio: Temirov orders a search: "Masked male, long hair, guitar case. Post One is down." Alert → 2.
  - Nurai leads Dan out the back door into the garden.
- **Encounters:** patrol guards (pistol) 2 in the alley + 1 in the B lobby. Stealth path: alley hedges → porch → lobby behind the demo wall. Civilians: 4 reactive (lobby/café) + crowd-lite.
- **Alert:** 1 → 2 (scripted, Temirov's order).
- **Save points:** B porch; Brew Point back room.
- **Key items:** Nurai's staff delivery card (opens B back door, C entrance, C F5, A Clinic service door — level 1).
- **Cutscene vs in-game:** in-game dialogue (camera free, Nurai animated).
- **Optional:** C06, C07, C08.
- **Player learns:** Aibek's message; Clinic suspicion; Talent Program is unpaid.

## M03 Hedge Maze — 3.5 min
- **Start:** SITE_Garden south apron (behind BLD_B). **End:** SITE_CPlaza south edge (by BLD_A_N north wall).
- **Characters:** Dan, Nurai (companion); patrol + checkpoint guards.
- **Objectives:**
  1. "Follow Nurai through the garden"
  2. "Wait for the patrol to pass" (contextual)
  3. "Reach the west gazebo"
  4. "Listen to Aibek's message"
  5. "Get to Block C"
- **Beats:**
  - Nurai walks ahead through the hedge arches and the maze (companion system), stops at corners, whispers when a guard is near.
  - West Gazebo: Nurai plays Aibek's last voice note on her phone (C09). Dan's first real line about his brother.
  - Patrol sweep from the HallWalk (sports hall gallery side). Nurai: "Go. I'm back at the counter before they miss me." She leaves toward B; companion ends.
  - Dan crosses the PergolaWalk and the stair top to the C plaza (or fights through).
- **Encounters:** patrol guards (pistol) 3 + checkpoint guard (baton) 1 = 4 enemies + Nurai.
- **Alert:** 2; detection → 3, drops back to 2 after 30 s with no line of sight.
- **Save points:** garden entry; after the gazebo.
- **Key items:** none.
- **Cutscene vs in-game:** in-game.
- **Optional:** east gazebo: C10 (security drill memo pinned to the FireBoard).
- **Player learns:** Aibek knew he was in danger; he hid something "where we play".

## M04 Room 203 — 4.0 min
- **Start:** SITE_CPlaza. **End:** INT_C_Floors F2, east stair landing.
- **Characters:** Dan; interns (civilians); patrol guards; tactical response team; Temirov (radio).
- **Objectives:**
  1. "Get into Block C" (staff card at the entrance)
  2. "Get to room 203"
  3. "Search Aibek's desk"
  4. "Check the instructor PC"
  5. "Read the whiteboard"
  6. "Fight your way to the east stair"
  7. "Get to the 5th floor"
- **Beats:**
  - C entrance hall (INT_C_F1): intern lanyards, PA voice, motivational posters. R101 = face enrolment booth (where every intern's face was captured).
  - West stair (F1–F3) to F2. Room 203 is an Annotation Cell: 6 interns tagging faces on screens; they freeze. Optional talk with the intern at Aibek's old desk.
  - Aibek's desk: cleared, name tag scratched off, a pencilled chord chart taped under the drawer (C11).
  - Instructor PC: annotation quota sheet (C12), Dan's own SIGHT profile "Watch: agitator" (C13), incident ticket "Intern C-0417: data exfiltration → Security (T.) / Program Director (E.)". Opening the PC trips the login alarm.
  - Whiteboard corner, under the timetable: one bar of music and "B-0". Dan: "The basement. Our song."
  - Radio: Temirov sends a response team to C. Fight in the F2 corridor (S/N halls, jog, benches as cover). Interns lock themselves in rooms.
- **Encounters:** F1: patrol guards 2 (stealthable). F2: tactical team (rifle, armor) 4 + patrol guards 2 = 6.
- **Alert:** 2 → 3 at the PC (scripted).
- **Save points:** C entrance; after the PC; after the F2 fight.
- **Key items:** first rifle ammo pickups from the tactical team.
- **Cutscene vs in-game:** in-game.
- **Optional:** C11, C12, C13; R207 meeting room: C14 (retention minutes).
- **Player learns:** what interns do; Dan is profiled himself; Ermekova and Temirov handled Aibek; the drive is in the basement.

## M05 The Attic — 3.0 min
- **Start:** INT_C_Floors F2 east stair. **End:** F5, then east stair down to F1 (exit C).
- **Characters:** Dan, Dr. Saltanat Ermekova; analysts (civilians); Temirov (radio, first direct talk).
- **Objectives:**
  1. "Climb to the 5th floor"
  2. "Find Ermekova's office"
  3. "Confront Ermekova"
  4. "Get to the Staff Studio entrance"
- **Beats:**
  - F3: short fight on the landing. F4: glimpse into R409 (management review room): wall screen "City contract signing 12:00 – Assembly Hall".
  - F5 attic: low ceilings, dormer light, 8 small offices; analysts hide under desks.
  - Ermekova's office (F5, east end by the east stair): calm, a Brew Point cup on her desk. Dialogue `ermekova_attic` (3 choices). She reveals Aibek is alive in the Clinic and offers a trade: the drive for the boy.
  - Temirov on Dan's stolen radio, first direct banter. Ermekova or Nurai: the studio basement has only an outside entrance on the west side.
- **Encounters:** F3: tactical 2. After the talk: patrol guards 2 up the east stair. Max 4.
- **Alert:** 3; drops to 2 once Dan leaves Block C unseen.
- **Save points:** F5 landing; after the confrontation.
- **Key items:** Ermekova's keycard (level 3: C basement node room, A Clinic ward).
- **Cutscene vs in-game:** in-game dialogue; 5 s camera push-in on Ermekova at the start.
- **Optional:** C15 (Ermekova → Lind email), C16 (analyst audio log).
- **Player learns:** Aibek is alive (Clinic, room 4); KOCH still lacks the drive; signing at noon.

## M06 Staff Studio — 4.0 min
- **Start:** BLD_C west face via SITE_HallCPassage. **End:** INT_C_Basement exit (sunken stair) → SITE_CPlaza.
- **Characters:** Dan; Temirov (PA + radio); Nurai (radio).
- **Objectives:**
  1. "Get to the Staff Studio entrance"
  2. "Find the piano room"
  3. "Play the old song"
  4. "Take Aibek's drive"
  5. "Get into the SIGHT node room"
  6. "Copy the city contract"
  7. "Shut down SIGHT"
  8. "Get out of the basement"
- **Beats:**
  - Down the sunken stair under the entry canopy (ex-"Dance Hall" sign, now "STAFF STUDIO"). Studio hall: seating, easels, mirrors.
  - Corridor to the piano room. Two uprights. Dan plays a few bars of "the old song" (simple in-game interaction, 8 s). Piano 2's lower panel is loose: the USB drive, taped (key item). Rehearsal notice with Aibek's name pencilled (C17).
  - West bay: door "C-001" (Ermekova's card). Node room: racks, fans, a single admin terminal. Copy the contract annex (C18) onto the drive (20 s hold, defend), then pull the node: every KOCH camera goes dark, FaceGates fail-locked.
  - PA, Temirov: "Lockdown. All teams, weapons free in Block C." Alert → 4.
  - Fight back out through the corridor and the studio hall.
- **Encounters:** before: patrol guards 2 in the studio hall (stealthable). Copy/defend: tactical 3. Exit: tactical 2 at the stair head. Max 5.
- **Alert:** 2 → 4 (scripted at shutdown; stays 4 to the end).
- **Save points:** sunken stair top; after the drive; after shutdown.
- **Key items:** Aibek's drive (evidence), contract annex (on the drive).
- **Cutscene vs in-game:** in-game; 10 s cutscene montage of cameras going dark across the campus.
- **Optional:** C17; art alcove mural.
- **Player learns:** the contract's detention thresholds; Dan now holds proof.

## M07 Health Center — 3.5 min
- **Start:** SITE_CPlaza (lockdown). **End:** Archive, BLD_A_W.
- **Characters:** Dan, Aibek (companion), Elmira (Clinic nurse, minor, added); tactical team.
- **Objectives:**
  1. "Get into Block A" (north door; optional: FireLadder_North → RoofHatch_North)
  2. "Find the Clinic"
  3. "Find Aibek"
  4. "Get Aibek out"
  5. "Take Aibek to the Archive"
- **Beats:**
  - Plaza under lockdown: shutters down, sirens, PA loop "Remain where you are". Armored team at the A_N north entrance.
  - Clinic: Elmira at the desk raises her hands, then quietly hands Dan the real chart (C19) and the room number.
  - Room 4: Aibek sedated, restrained, confused. Reunion (dialogue `clinic_reunion`). Dan cuts the straps.
  - Escort: Aibek follows slowly (companion), cannot fight, hides when shot at. Corridor south through A to the Archive (A_W library wing).
  - Archive: Aibek hides between the stacks. He tells Dan Lind will go on air anyway and call this terrorism. "You built that room. Play it." Old AV contract in the Archive (C20).
- **Encounters:** plaza: tactical 3. Clinic corridor: patrol 2 + tactical 2 (staggered, max 4 alive). Escort: tactical 2. Max 5 enemies + Aibek.
- **Alert:** 4.
- **Save points:** plaza; Clinic; Archive.
- **Key items:** medkits in the Clinic (refill health).
- **Cutscene vs in-game:** in-game; reunion has a 15 s camera lock.
- **Optional:** C19, C20; Temirov's tablet on a dead team lead (part of C19 set, see systems).
- **Player learns:** what was done to Aibek; Lind's plan to spin the attack.

## M08 Assembly — 4.5 min
- **Start:** Archive, BLD_A_W. **End:** ending A at SITE_Gate / ending B at BLD_GuardBoothNE → bus.
- **Characters:** Dan, Viktor Lind, Ruslan Temirov + elite; delegates/press (civilians); Aibek, Nurai (endings).
- **Objectives:**
  1. "Get to the AV booth"
  2. "Patch into the broadcast"
  3. "Play the evidence"
  4. "Survive"
  5. "Stop Temirov"
  6. "Decide" (choice prompt)
- **Beats:**
  - Up the Archive stair to the Assembly Hall rear gallery and the AV booth (Dan installed it; knows the patch bay).
  - Cutscene (in-engine, 40 s): Lind on stage before delegates and cameras: "This morning an armed man attacked our people. This is why the city needs SIGHT."
  - Dan plugs the drive into the AV desk: the stage screen and the live feed show Aibek's profiles, Dan's own "Watch" profile and the annex. Murmurs, phones out. Lind: "Cut the feed!"
  - Boss: Temirov + elite (see 04_dialogue_outlines.md for banter).
    - Phase 1: elite 3 storm the booth gallery; Dan fights from the booth.
    - Phase 2: Temirov kills the house lights; Dan can use the AV desk to flash the stage lights (blind enemies for 3 s, 3 uses). Elite 2 more.
    - Phase 3: Temirov alone on the stage, armor; close range. Pepper spray stuns him once for an opening.
  - Temirov down. Lind alone at the lectern; camera red light on. Choice.
- **Encounters:** Temirov's elite (rifles, heavy armor) 5 total, max 3 alive + Temirov. Delegates 3 reactive + crowd-lite. Max 8.
- **Alert:** 4.
- **Save points:** AV booth; boss phase 2; before the choice.
- **Endings:** see 00_premise.md. A (default) ends at SITE_Gate: the restored FaceGate reads Dan's bare face, "IDENTIFIED", the turnstile opens; police, Nurai, Aibek. B ends at BLD_GuardBoothNE (service road) then a bus interior: radio news, mask back on.
- **Cutscene vs in-game:** opening speech cutscene; boss in-game; endings 60–75 s cutscene each.
- **Player learns:** the cost of each choice.

---

## Side content (optional, later)
| ID | Where | What | Status |
|---|---|---|---|
| S01 | SITE_Sports (courts) | "Drill Ground": Temirov's teams train; sneak in for a rifle upgrade (suppressor) before M04. | NEEDS BUILD (courts not modelled) |
| S02 | BLD_A_E kitchen service block | Alternative entry into A in M07 through the delivery cage; cook gives medkit. | EXISTS (exterior) |
| S03 | BLD_Canteen | Lunch rush civilians; overheard gossip about "the intern who resigned". | EXISTS (exterior) |
| S04 | BLD_D_M / BLD_D_W | KOCH Bio: teaser door, "closed for audit". Sequel hook. | EXISTS (exterior) |
