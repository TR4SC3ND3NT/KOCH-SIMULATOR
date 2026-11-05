PROPOSAL — not canon. A human lore author must approve and move it into docs/lore/canon/.

# KOCH-SIMULATOR: Story locations

Status: **EXISTS** = in Art/Blender/Specs greybox; **PARTIAL** = shell exists, story rooms missing; **NEEDS BUILD** = not modelled.
All in-game text is KOCH-branded. Items marked TODO_LORE need a human-approved text.

## Overview
| Location | Spec | Status | KOCH function | Missions |
|---|---|---|---|---|
| Arsen's apartment | – | NEEDS BUILD | Home (city) | M00 |
| Bus stop + bus interior | – | NEEDS BUILD | City transit | M00, ending B |
| Street sidewalk | SITE_StreetFront | EXISTS | Avenue in front of HQ | M00 |
| Crossing | SITE_Gate (Crossing, Zebra) | EXISTS | Pedestrian crossing | M00, ending A |
| Gate / checkpoint | SITE_Gate, BLD_GateBooth | EXISTS | KOCH Secure checkpoint, "Post One" | M01, ending A |
| Gate alley | SITE_GateAlley | EXISTS | Main staff walkway north | M02 |
| Block B | BLD_B (exterior) | PARTIAL (interior NEEDS BUILD) | Visitor & PR Center, demo labs, Brew Point | M02 |
| Garden | SITE_Garden, SITE_Garden_Trees | EXISTS | Staff leisure garden, hedge maze, 2 gazebos | M03 |
| C plaza | SITE_CPlaza, SITE_CPlaza_Props | EXISTS | Talent Program forecourt | M04, M06, M07 |
| Block C F1 | INT_C_F1, BLD_C | EXISTS | Talent Program entrance, enrolment | M04 |
| Block C F2–F4 | INT_C_Floors | EXISTS | Annotation Cells, review rooms | M04, M05 |
| Block C F5 attic | INT_C_Floors (F5_*) | PARTIAL | Analysts' offices, Ermekova | M05 |
| Hall–C passage | SITE_HallCPassage | EXISTS | Lower-terrace path to C's west side | M06 |
| C basement | INT_C_Basement | EXISTS (node room NEEDS BUILD) | Staff Studio + SIGHT node room C-001 | M06 |
| Block A exterior | BLD_A_N, BLD_A_S, BLD_A_W | EXISTS | Executive HQ | M07, M08 |
| Block A interiors | – | NEEDS BUILD (friend in progress) | Clinic, Archive, Assembly Hall, CEO floor, HR, Finance, Legal | M07, M08 |
| NE guard booth | BLD_GuardBoothNE | EXISTS | Service gate "Post Two" | Ending B |
| Sports hall | BLD_Hall, BLD_HallWing | EXISTS (exterior) | Staff gym; its gallery borders the garden | M03 (backdrop) |
| Courts | SITE_Sports | NEEDS BUILD | Security drill ground | S01 optional |
| Canteen | BLD_Canteen, BLD_A_E | EXISTS (exterior) | Staff canteen; kitchen service block | S02, S03 optional |
| Block D | BLD_D_M, BLD_D_W | EXISTS (exterior) | KOCH Bio (closed) | S04 optional |

---

## Arsen's apartment — NEEDS BUILD
- **Function:** 2-room flat in a 9-storey Soviet block (match the context-city facades).
- **Who:** Arsen alone (Isa's things untouched).
- **Events:** M00 wake, pack, voicemail.
- **Props:** guitar case open on the floor; rifle wrapped in a blanket under the bed; Isa's mattress, keyboard, Talent Program welcome mug; missing-person flyers (photo of Isa, phone number); KOCH HR letter (C01); calendar with "Day 21" circled; window view of the KOCH rooftop ad.
- **Audio:** fridge hum, neighbours through the wall, trolleybus outside, kettle.

## Bus stop + bus interior — NEEDS BUILD
- **Function:** city bus route to the HQ stop. A trolleybus would match the existing TrolleyPole wires (art choice).
- **Who:** driver, 6–10 passengers (office workers, a grandmother, interns with KOCH lanyards).
- **Events:** M00 ride + Nurai call; ending B epilogue.
- **Props:** route map with stop "KOCH HQ"; on-board screens looping a SIGHT ad "A city that knows you is a safe city" (TODO_LORE slogan); Safe City flyer (C03); worn seats, ticket validator.
- **Audio:** engine whine, radio news (contract signing), passengers' phones.
- **Note:** SITE_Gate says no bus shelter was seen near the crossing; stop position TBD (open question).

## SITE_StreetFront + Crossing — EXISTS
- **Function:** north sidewalk of the avenue along Block B; 4-lane carriageway, zebra 4.3 m wide.
- **Who:** pedestrians, cars (ambient), interns walking to work.
- **Events:** M00 walk + crossing; ending A police cars line up here.
- **Props:** Flagpoles with KOCH flags; StreetTree pits; parked cars; AFrameSign_0/1 = Brew Point boards ("Coffee for visitors, 1st floor Block B"); CrossingSign_N.
- **Audio:** traffic, trolley wire hum, distant construction.

## SITE_Gate + BLD_GateBooth — EXISTS ("Post One")
- **Function:** KOCH Secure checkpoint. Turnstile_In / Turnstile_Out with FaceTerminal_In (faces street) and FaceTerminal_Out; booth with service window, BagRest_Booth, CardReader_Booth, CCTV; SlidingGate for vehicles.
- **Who:** Azamat (Day 0 morning, alone). After M01: patrol pairs. Lockdown: gate fail-locked. Ending A: police, press, Nurai.
- **Events:** M01 refusal, Azamat scene, takedown; ending A walk-out.
- **Props / story text:**
  - FaceTerminal screen states: "LOOK AT THE CAMERA" / "WELCOME, <NAME>" / "FACE NOT VISIBLE. REMOVE FACE COVERING." / ending A "IDENTIFIED: ARSEN".
  - BoothPlaque: "KOCH SECURE – POST ONE". TestCentrePlate: "FACEGATE PILOT SITE 01" (proposal).
  - Billboard_West: SIGHT ad (TODO_LORE slogan).
  - Inside the booth: kettle, family photo taped to the monitor (Azamat's kids), shift log (C04), FaceGate monitor (C05), panic button, coat hook.
  - InfoBoard_Yard: visitor rules ("Faces must be visible at all times").
- **Audio:** turnstile beeps, FaceGate chime / refusal buzz, radio static, street noise through the fence.

## SITE_GateAlley — EXISTS
- **Function:** main walkway north between B (west) and A (east), lower walkway along A, SouthStair, PavilionStair, SideStair + steel ramp.
- **Who:** staff walking in (morning); patrol pair (M02).
- **Events:** M02 stealth approach to B.
- **Props:** benches, PathLamps, BankRose beds (cover); A_S BlockPlate "BLOCK A – EXECUTIVE"; signposts "Visitor Center →", "Talent Program ↑".
- **Audio:** footsteps on pavers, birds in the pines, PA chime from A.

## BLD_B — PARTIAL (exterior EXISTS; interior NEEDS BUILD)
- **Function:** Visitor & PR Center (lobby with FaceGate demo wall), product demo labs, Brew Point coffee shop, small back storeroom with a north back door.
- **Who:** Nurai + 1 barista, visitors, PR staff; patrol guard 1 (M02).
- **Events:** M02 Nurai scene; exit to the garden.
- **Props:** LetteringLogo = KOCH lettering + round logo (TODO_LORE text, 2 blocks of 3 lines); demo wall showing the live gate camera; SIGHT profile kiosk (C07); Talent Program poster (C06); Brew Point menu board, order printer with the Clinic slip (C08), tip jar, staff lockers.
- **Audio:** espresso machine, lounge music, PR video loop.

## SITE_Garden — EXISTS
- **Function:** formal staff garden: 2 gazebos, hedge maze + 8 hedge arches, centre square, pergola walk, HallWalk along the sports hall gallery.
- **Who:** smokers, a gardener (morning); M03 patrols.
- **Events:** M03 companion route with Nurai; Isa's voice note at the west gazebo.
- **Props:** FireBoard_* (security drill memo, C10); bench plaque "In honour of our Talent cohort 5"; cigarette butts in the gazebo; Isa's initials scratched into the gazebo parapet.
- **Audio:** wind in hedges, sparrows, sprinklers, distant drill whistles from the courts.

## SITE_CPlaza — EXISTS
- **Function:** forecourt of Block C; benches, planters, bollards; A_N north wall with AHU_North, FireLadder_North, RoofHatch_North.
- **Who:** interns on break (M04); lockdown teams (M07).
- **Events:** M04 entry; M06 return; M07 lockdown crossing to A.
- **Props:** C entrance canopy sign box: "KOCH TALENT PROGRAM" (proposal); CPlate "C"; intern cigarette corner; lockdown: red strobes, shutters.
- **Audio:** intern chatter, PA "Talent cohort 9, please return to your cells" (dark joke), later sirens.

## Block C F1 — INT_C_F1 — EXISTS
- **Function:** Talent Program entrance hall, WCs, rooms 101–108 (onboarding, enrolment).
- **Who:** interns, a receptionist, cleaner; patrol 2.
- **Events:** M04 entry; M05 exit.
- **Props:** R101 = face enrolment booth (photo light, chair, "Hold still – your face is your future"); room plates "TALENT 101" etc.; notice board: quotas, "Clean Desk Policy", "Interns may not bring USB devices" (foreshadow); vending machines.
- **Audio:** footsteps on terrazzo, LED hum, vending machine.

## Block C F2–F4 — INT_C_Floors — EXISTS
- **Function:** F2–F3 Annotation Cells (rooms with PC rows, CCTV in every room = baseline recording); F2 R207, F3 R307 meeting rooms; F4 management review rooms R405, R408, R409.
- **Who:** 6–8 interns per active cell; instructors; M04 tactical team.
- **Events:** M04 room 203 search + fight; M05 climb.
- **Props:** room 203: 8 screens with face grids and tag buttons ("Calm / Nervous / Hostile"), Isa's cleared desk (C11), instructor PC (C12, C13), whiteboard corner with the music bar + "B-0"; R207 retention minutes (C14); R409 wall screen "Contract signing 12:00 – Assembly Hall"; per-room CCTV with a red rec light.
- **Audio:** mouse clicks, keyboard rattle, a quiet "next" tone every 9 seconds per tagged face.

## Block C F5 attic — PARTIAL
- **Function:** analysts' offices (8 doors: F5_Door_S0–S3, N0–N3), low ceilings, dormer windows. Ermekova's office = east end, beside the east stair (proposal: F5_Door_N3).
- **Who:** 3–4 analysts (civilians), Ermekova.
- **Events:** M05 confrontation.
- **Props:** Ermekova's office: framed "Talent Program – 9 cohorts" photo wall, Brew Point cup, printed annex draft, keycard on lanyard, plant; analysts' desks with dual monitors, SIGHT dashboards ("Refer" queue counts), sticky notes.
- **Audio:** roof creaks, wind on the dormers, server-like PC fans.

## SITE_HallCPassage + C west face — EXISTS
- **Function:** lower-terrace path and granite stair between the sports hall and C's west shed; leads to the sunken basement entry (BLD_C WestShed, Sign_DanceHall, Poster_DanceHall).
- **Events:** M06 approach.
- **Props:** Sign_DanceHall becomes "STAFF STUDIO"; Poster_DanceHall (open question #1) proposal: "KOCH Talent Night – staff & interns welcome" with a piano pictogram.
- **Audio:** hall ventilation, gravel, muffled piano scales from below (ambience before M06).

## C basement — INT_C_Basement — EXISTS (node room NEEDS BUILD)
- **Function:** Staff Studio (ex-Dance Hall: seating, easels, art alcove), corridor, piano rehearsal room (2 uprights, platform), east bay (3 doors), west bay with door "C001" → SIGHT node room C-001.
- **Door plates (proposal, TODO_LORE):** BayE A "STUDIO STORE", B "WARDROBE", C "CLEANERS"; BayW C001 "C-001 NODE – AUTHORISED ONLY", black door "PLANT ROOM", wood door "STORAGE".
- **Who:** M06 patrol 2, then tactical.
- **Events:** M06 drive pickup, contract copy, SIGHT shutdown.
- **Props:** Piano_Notice = rehearsal rota with Isa's name pencilled (C17); piano 2 loose lower panel; node room: 4 racks, cable trays, admin terminal, red "NODE ONLINE" lights, temperature log; BayW_Sign_KOCH emblem.
- **Audio:** piano (the theme), rack fans, after shutdown: dead silence then alarms.

## Block A — exteriors EXIST, interiors NEEDS BUILD
- **Function and proposed placement** (greybox friend decides exact rooms):
  - **A_N F1 north end: Clinic (Health Center)** – desk, 4 ward rooms, treatment room, medicine store. Reached from the C plaza (north door) and the roof hatch (FireLadder_North).
  - **A_W north part: Archive** (library wing) – double-height stacks, mezzanine/stair up to the Assembly Hall rear gallery.
  - **A_W south part: Assembly Hall** – double-height auditorium, stage, lectern, big screen, rear gallery with the AV booth; delegates enter from the A_S entrance pavilion.
  - **A_S F3: CEO floor** – Lind's office (seen from the square; ending cutscene shots), boardroom.
  - **A_S/A_N F1–F2: HR, Finance, Legal** – corridors for M07 routing; HR has the "resignation" letter template.
- **Who:** M07: Elmira, Isa, tactical team. M08: Lind, Temirov, elite, delegates, press camera crew.
- **Props:** Clinic: room 4 chart (C19), restraints, sedative trolley, "Security hold – T." sticker on the door; Archive: AV contract binder (C20), old Talent cohort yearbooks; Assembly Hall: banner "SAFE CITY – SIGNING CEREMONY" (proposal), lectern with KOCH emblem, live camera with red tally light, AV desk + patch bay, Lind's speech draft (part of C20 set).
- **Audio:** Clinic: monitor beeps, ventilation; Archive: hush, paper; Assembly Hall: room tone of 60 people, mic feedback, applause tracks.

## BLD_GuardBoothNE — EXISTS ("Post Two")
- **Function:** service gate on the NE service road; deliveries and night exits ("interns who resigned leave through Post Two").
- **Events:** ending B escape.
- **Props:** barrier arm, delivery log, ashtray.

---

## Needs for the greybox friend (A, B, C)
**Block A (interiors, priority 1)**
- Clinic: reception desk, corridor, 4 ward rooms (room 4 lockable), treatment room; door to the C plaza (A_N north wall).
- Roof hatch interior landing under RoofHatch_North (optional stealth route).
- Corridor from the Clinic south to the Archive (≥ 30 m with side offices for cover).
- Archive: double-height stacks, stair/mezzanine linking to the Assembly Hall rear gallery.
- Assembly Hall: stage + lectern, ~60 seats, side aisles, rear gallery with AV booth (window onto the hall), 2 side exits, stage-left door to backstage.
- CEO office (A_S F3) and the A_S entrance pavilion lobby (delegate arrival, cutscene use).
- HR / Finance / Legal: 1 room each is enough (set dressing, collectibles later).

**Block B (interior, priority 2)**
- Visitor lobby behind the EntrancePorch, demo wall, 1 demo lab.
- Brew Point: counter, 6–8 tables, back storeroom, north back door to the garden apron.

**Block C (priority 1, mostly existing)**
- Room 203 (F2): confirm it sits next to a stair; whiteboard corner visible from the door.
- F5: 8 small offices behind the existing doors; Ermekova's office at the east end with a dormer.
- Basement: SIGHT node room behind BayW door C001 (≈ 4 × 6 m, 4 racks).
- Confirm: no interior link from C F1 to the basement (story uses the outside west entry).
