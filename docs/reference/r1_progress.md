# R1 progress: the whole map as 1:1 geometry, coarse to fine

Checklist for docs/roles/R1-photogrammetry-handoff.md **section 0 (passes)**. Every zone reaches pass N before any zone
starts N+1. A zone-pass is done when its scripted test AND your own review of the frames/overlays both pass (handoff
3a). Each object line gets the highest pass it passed plus the commit, e.g. `P1✓ 1a2b3c4`; `[x]` only at its depth
cap. "approx.", "in the model", "estimated" never count. Blockers: `BLOCKED: <reason>` + a photo request.

- **Meshes** come from the GPU queue (outside git): `C:\koch\work\gpu_queue.ps1` runs the zones of `C:\koch\work\queue.txt` one by one through `Scripts/Geo/rs/zone_job.py` (align → cameras/poses → mesh into `C:\koch\work\zones\<zone>\`). The state of each zone is in `C:\koch\work\status.txt`.
- **Sources:** the owner's capture (`C:\koch\alatoo-capture\raw`, frames in `C:\koch\work\frames_a`, clip ids `PXL_2026092x_<id>`), web media (`C:\koch\web`), satellite orthos (`alatoo-capture/data/ortho`). Meshes, frames, masks and photos stay outside git.
- **Levels:** `route_profile.py` over all zones → `route_check.py` (handoff 0a).

## Pass grid (zone × pass; cell = commit when passed, `—` above the cap; P3 is done later in Unreal)
| Zone (route order) | Stream | Cap | P0 | P1 | P2 |
|---|---|---|---|---|---|
| Street, bus stop, crossing (§12) | A | P2 | | |  |
| Gate, booth, yard (§4 G.1-G.5) | A | P2 | | |  |
| Alley B–A (§4 G.6-G.13) | A | P2 | | |  |
| A_W gallery + plaza (§3) | A | P2 | | |  |
| C plaza + exterior (§1) | A | P2 | | |  |
| C interior F1-F5 (§2 CI.1-CI.8) | A | P2 | | |  |
| C basement (§2 CI.9, §1 C.12) | A | P2 | | |  |
| Hall–C passage (§5) | B | P2 | | |  |
| Garden (§6) | B | P2 | | |  |
| Sports fields (§7) | B | P2 | | |  |
| Sports hall, canteen (§8, §9) | B | P2 | | |  |
| Block B (§10) | A | P2 | | |  |
| Block A (§11) | A | P2 | | |  |
| Terrain + levels (§15) | A+B (pads of own zones) | P2 | | |  |
| West campus D/E (§13) | B | P2 | | |  |
| Ring ≤ 150 m + streets/stops (§16) | A | P2 | | |  |
| Ring > 150 m (§16 far) | A | P1 | | | — |

Streams: handoff 0b (A = RTX PC, B = owner laptop). Log lines start with [A] or [B].

The ticks below from before 2026-09-27 (C.1-C.3) were fitted before the world frame was fixed: they count as P2 only
after the C zone passes P0 and P1 with them unchanged.

## 1. Block C, exterior (zones `C_entr` done, `C_sw`)
- [x] C.1 Main entrance stair: granite treads/risers with nosings, landing, cheek walls with caps — 7 × 0.154, treads 0.475, landing 2.65 (mesh + photo-edge fit, overlay f00023/f00090/f00128/f00449) (cdb826f)
- [x] C.2 Entrance ramp: grating deck, frame, stringers, rails and posts with feet — run 1.0 wide 3.5–4.5 m out, u 3.75→9.5, top plate over the flight (photo-edge fit, 6 cameras) (87bf358)
- [x] C.3 Entrance canopy: slab, terracotta soffit panels, fascia/edge trims, sign box (blank KOCH panel), flood lamps — depth 5.6, sign +3.10…+4.65, soffit to +3.8 at the wall (photo fit + mesh) (2a4bd43)
- [ ] C.4 Vestibule / storefront (approx., M3): glazed frame, doors with stiles and rails, pull bars, threshold, transom, side lights, fascia cladding — BLOCKED: storefront frame is 4.75 m wide on its plane (f00449) but the maroon tower above is ~3.95 m and the mesh puts the tower face ~0.9 m in front of the storefront, so the recess would run under the W wing; needs tape (photo request 2026-09-27 «Вход C: ниша»)
  - 2026-09-27: head +3.29, transom +2.65, fascia to the soffit +3.6 matched (f00449). Open: the frame is 4.75 wide (u −0.4…4.4) vs 3.76 now; the ground-floor entrance is wider than the maroon tower above and runs into both wings. Settle with C.5 (tower/wing faces: the W wing face is ~2.7 m in front of the storefront on the mesh vs 1.3 in the ring).
- [ ] C.5 South facade, centre + tower: plinth tile band, pilasters, window kit (frame, sashes, mullions, sills, surrounds), cornice — approx., in the model (GBF_BLD_C Wall/Win/Sur/Pilaster/Plinth/Cornice)
- [ ] C.6 South facade, west wing and east wing — approx., in the model (GBF_BLD_C Wall/Win)
- [ ] C.7 East facade + east exit (brown double door under the stair, outside step/porch) — approx., in the model (GBF_BLD_C Wall/Win (E edges))
- [ ] C.8 North facade (windows, doors, plinth) — approx., in the model (GBF_BLD_C Wall/Win (N edge))
- [ ] C.9 West facade — approx., in the model (GBF_BLD_C Wall/Win (W edges))
- [ ] C.10 Roof: hips, ridges, eaves, fascia, gutters with hangers, downpipes with elbows and shoes, snow guards — approx., in the model (GBF_BLD_C Roof/Eave/Gutter/Downpipe)
- [ ] C.11 Dormers: south 2+3, north 7, east 2, each with its own roof — approx., in the model (GBF_BLD_C Dormers)
- [ ] C.12 West basement entry "Dance Hall": sunken stair, wrought-iron guard, brick box, red mono-pitch canopy and its post — approx., in the model (GBF_BLD_C DanceHallEntry + INT_C_Basement stair)
- [ ] C.13 West mono-pitch shed and its continuation toward the spruces SW of C — approx., in the model (GBF_BLD_C WestShed)
- [ ] C.14 Basement light wells: red corrugated sloped covers along the south and east walls, low parapet — approx., in the model (GBF_BLD_C LightwellCover/Parapet)
- [ ] C.15 Wall fittings on C: AC units with brackets, CCTV, lamps, vents, sign plates — approx., in the model (GBF_BLD_C ACUnits/CCTV/Flood/Sign)
- [ ] C.16 Plaza south of C: paving levels and falls, kerbs, red-edged planters, tree pits, spruces, benches, bins, bike parking at the stair — approx.: the tree pits by the stair and the ramp moved 1-2 m south to the trunk positions cut through solved cameras (f00023/f00090/f00128); bike parking not in the 2026 footage (web 2021 only), not modelled
- [ ] C.17 Ground drop plaza → basement-entry corner, kerb step to the granite pad at the brick wall — approx., in the model (terrain pads SITE_CPlaza)

## 2. Block C, interior (zone `C_base`; F1–F5 zone to add: clips 070704360, 052716931, 080443026, 080011086, 080051708, 074805359, 075725091, 075928860, 075931189)
- [ ] CI.1 Entrance lobby F1: terrazzo floor, blue accent panels, vending/coffee niche, radiators, ceiling grid with LED panels — approx., in the model (GBS_INT_C_F1)
- [ ] CI.2 F1 corridors west/east: benches, classroom doors (0.99 × 2.05 kit), fire-alarm boxes — approx., in the model (GBS_INT_C_F1)
- [ ] CI.3 West stair F1–F3: flights, landings, window, white steel balustrade — P1 partly: riser 0.155 confirms 0.1535, tread 0.30 from the C_F1 mesh (was 0.332); landing positions and which stair the clip climbs still to confirm once C_F1 is placed in C
- [ ] CI.4 East stair F1–F5: flights, landings, windows, balustrade (riser count per flight) — P1 partly: tread 0.30 / riser 0.1535 as the west stair (same design, C_F1 mesh); riser count per flight (11 + half bottom riser) not yet seen as a full flight
- [ ] CI.5 WC pair F1: sinks, stalls with black doors, squat pans, high cisterns, tile to 1.4 m — approx., in the model (GBS_INT_C_F1)
- [ ] CI.6 Prototype classroom 203 (computer lab): desks, chairs, TV, whiteboard, grid ceiling, windows with blinds — approx.: computer-lab furniture in the F2 north room next to door N1 (INT_C_Floors F2_Lab_*); room choice from ROUTE (north windows), not confirmed
- [ ] CI.7 Floors F2–F4: corridors, classrooms, WCs (F4 without the west stair: offices) — approx., in the model (GBS_INT_C_Floors)
- [ ] CI.8 F5 attic offices under the roof, lit by the dormers — approx., in the model (GBS_INT_C_Floors)
- [ ] CI.9 Basement: stair down with wrought-iron balustrade, vaulted corridor, barred windows, art room, piano room — P1 partly: stair count re-checked on 012547860 f00008/f00233 (8 upper + landing + 2 lower, spec OK); C_base c11 eye-height scale fails on the stair (camera path 2.4x too deep), mesh empty on the treads -> riser 0.138 stays from the earlier SfM; corridor/rooms not measured yet

## 3. A_W gallery and its plaza (zone `AW`)
- [ ] AW.1 Gallery deck: tiled deck above the walkway, granite edge, the single step between the 1st and 2nd post from the north — approx., in the model (GBF_BLD_A_W gallery deck)
- [ ] AW.2 Gallery posts (bases, caps), beams, soffit panels, edge trims, the gallery roof — approx., in the model (GBF_BLD_A_W gallery posts/roof)
- [ ] AW.3 North-end steps + grey ramp on the wall side — approx., in the model (SITE_Garden AW_NorthRamp)
- [ ] AW.4 Middle stair + steel ramp with rails (alley → gallery) — approx., in the model (SITE_GateAlley SideStair, Ramp_Run1/2)
- [ ] AW.5 North stair from the alley to the plaza (end of the lawn) — approx., in the model (SITE_GateAlley Steps)
- [ ] AW.6 A_W west facade under the gallery: doors ("Dining Hall" double door, single door at the A_S pilaster), windows, pilasters, AC units — approx., in the model (GBF_BLD_A_W Wall/Win/doors)
- [ ] AW.7 A_W north end wall — approx., in the model (GBF_BLD_A_W N end)
- [ ] AW.8 Basement descent at the gallery (stone steps + steel stair) — BLOCKED: not visible in any owner or web frame, not modelled (needs a photo)
- [ ] AW.9 Plaza between the gallery and C: paving levels, kerbs, planters, signboard, wayfinding sign, bins — approx., in the model (GBS_Garden_AW, SITE_CPlaza, GBS_Garden_Signboard)

## 4. B–A alley and the main gate (zone `Gate`)
- [ ] G.1 Checkpoint booth: tile walls, brick plinth, doors, windows, roof — approx., in the model (GBF_BLD_GateBooth) — P1✓ 3e8ba38 (obj_test: GBF_BLD_GateBooth median 2.2/4.2 px Street c3, 5.0/4.0 px Gate c13; own look c13 f00401, c2 f02711)
- [ ] G.2 Gate canopy on its round column: roof pitch, ends, timber soffit, fascia panel (blank KOCH) — approx., in the model (GBS_Gate_GateCanopy) — P1✓ 3e8ba38 (obj_test: GateCanopy 2.0/3.0 px Street c3, 3.6/3.0 px Gate c13; own look c13 f00146/f00401)
- [ ] G.3 Turnstiles and the pass-through railings — approx., in the model (GBS_Gate_Turnstile/LaneRail)
- [ ] G.4 Sliding gate leaves, fence panels and posts along the street — approx., in the model (GBS_Gate_SlidingGate/Fence/GatePost) — P1✓ 3e8ba38 (obj_test: SlidingGate 1.0/1.0 px Street c3, 3.6/4.0 px Gate c13; Fence 1.0/1.0, 7.0/4.0 px; own look c13 f00401)
- [ ] G.5 Yard inside the gate: clover pavers, drain gratings, benches, bins, bike racks, the 3 flagpoles, the decorative bicycle — approx., in the model (GBS_Gate_Bench/BikeRack/WheelieBin/Bed)
- [ ] G.6 Alley B–A: tree row, concrete-edged hedges, kerbs, red lawn edging, yellow-painted kerbs — approx., in the model (GBS_GateAlley Alley/Curb/Lawn/BBed/PathHedge)
- [ ] G.7 South wide stair from the gate down to the A corner — BLOCKED: riser height not measurable (Gate c8 mesh has no surface at the stair, no clip climbs it); tape request in photo_requests.md (Аллея B–A: высоты ступеней)
- [ ] G.8 North stair at the end of the lawn (with rails) — approx., in the model (GBS_GateAlley_Steps/StairCoping)
- [ ] G.9 Retaining wall with the granite parapet between the alley and the walkway along A — approx., in the model (GBS_GateAlley_RetWall/LawnCoping)
- [ ] G.10 Grating ramp at the side stair opposite the lettering — approx., in the model (GBS_GateAlley_Ramp/RampRail)
- [ ] G.11 A_S entrance pavilion (pitched roof, door, pilasters, steps) — pavilion block found in the Gate c8 mesh (4 m out from the A_S face, used to place c8); stair BLOCKED: mesh empty under the porch (people masked), tape request in photo_requests.md
- [ ] G.12 Pad at the foot of the south stair (A_S corner, drain grating) — approx., in the model (GBS_GateAlley_Landing)
- [ ] G.13 Slope between the fence walkway (east of the booth) and A's south facade — approx., in the model (GBS_GateAlley_SouthBank)

## 5. Hall–C passage and the sports hall's east end (zone `Sports`, west part in `C_sw`)
- [ ] H.1 Passage stair with the granite cheek — approx., in the model (GBS_HallCPassage_Passage)
- [ ] H.2 Grey ramp on the stair's west side — approx., in the model (GBS_HallCPassage_Passage)
- [ ] H.3 Low railing with dense bars — approx., in the model (GBS_HallCPassage_Passage)
- [ ] H.4 Sports hall east end wall with the door and canopy by the ramp, its steps — approx., in the model (GBF_BLD_HallEast)
- [ ] H.5 Sports hall 2-storey wing at the NE corner — approx., in the model (GBF_BLD_HallWing)
- [ ] H.6 Path along the sports hall from the garden to C's west side (benches, plinth, trees) — approx., in the model (SITE_Sports HallRowTree, HallCPassage)

## 6. Garden (zone `Garden`)
- [ ] GD.1 West gazebo: posts, brick parapet, openings, roof and finial — approx., in the model (GBS_Garden_Gazebo)
- [ ] GD.2 East gazebo — approx., in the model (GBS_Garden_Gazebo)
- [ ] GD.3 Hedge maze: hedge blocks and paths — approx., in the model (GBS_Garden_Hedge)
- [ ] GD.4 Hedge arches — approx., in the model (GBS_Garden_Arch)
- [ ] GD.5 South pergola alley: arches, radial paths, the red wall with a stair at its end — approx., in the model (GBS_Garden_PergolaWalk)
- [ ] GD.6 Retaining walls (rubble stone) and steps between B's side and the garden — approx., in the model (GBS_Garden_RetainingWall/Steps)
- [ ] GD.7 East edge toward the alley: retaining wall, hedge, lamps — approx., in the model (Garden RetainingWall/Hedge/Lamp)
- [ ] GD.8 Garden furniture: wrought-iron benches with slats, bins, lamp posts — approx., in the model (GBS_Garden_Bench/Lamp)
- [ ] GD.9 Ground: diamond tiles, scalloped concrete edging, levels — approx., in the model (GBS_Garden_Edging)
- [ ] GD.10 Small red-brick hut with a pitched roof by the garden alley; timber gazebo (second type, check location) — BLOCKED: only in 2024-12-26/2025-10-18 web clips, location unknown; not modelled

## 7. Sports fields (zone `Sports`)
- [ ] F.1 Football pitch: turf slab, red plinth, red rubber border, levels — approx., in the model (GBS_Sports_Pitch)
- [ ] F.2 Pitch fence: posts, mesh panels, X-braced ball-stop sections, gates — approx., in the model (GBS_Sports_PitchFence/PitchGate)
- [ ] F.3 Floodlight masts with ladders and heads — approx., in the model (GBS_Sports_PitchFlood)
- [ ] F.4 Courts (basketball, volleyball, hard court): slabs, fences between, hoops, net posts — approx., in the model (GBS_Sports_Court(s)/Hoop/VolleyNet/HardNet/CourtsFence)
- [ ] F.5 Decorated alley along the pitch: planters, thujas, double-ball lamps, garlands — approx., in the model (GBS_Sports_AlleyBed/AlleyThuja/AlleyLamp/AlleyFestoon)
- [ ] F.6 Flowerbed plaza slope from the path end to the pitch — approx., terrain pads SITE_Sports (4.475 -> 3.45)
- [ ] F.7 Benches and spectator tiers by the pitch — approx., in the model (GBS_Sports_PitchBench)
- [ ] F.8 Red square pad west of the pitch — approx., in the model (GBS_Sports_WestRedSquare)
- [ ] F.9 North boundary fence with brick piers — approx., in the model (GBS_Sports_NorthBoundary)
- [ ] F.10 Thujas along the south court fence — approx., in the model (GBS_Sports_CourtsThuja)
- [ ] F.11 Low timber stage deck at the plaza edge by the courts; round flower bed with a lamp (check both still exist) — approx., in the model (GBS_Sports_RoundBed)
- [ ] F.12 Outdoor stair behind a goal (red risers, white treads) to the next terrace — BLOCKED: only in the 2024-09-30 web clip, location unknown; not modelled

## 8. Sports hall (zones `Sports`, `Garden`)
- [ ] SH.1 South facade under the gallery: wall, doors, windows — approx., in the model (GBF_BLD_Hall Wall/Win)
- [ ] SH.2 Gallery: red posts, beams, deck, eaves — approx., in the model (GBF_BLD_Hall Gallery)
- [ ] SH.3 West end, north side — approx., in the model (GBF_BLD_Hall Wall)
- [ ] SH.4 Roof: pitch, ridge, eaves, gutters — approx., in the model (GBF_BLD_Hall Roof)

## 9. Canteen and small buildings north of C (zone `Sports`)
- [ ] K.1 Canteen: all four facades, west entrance (glass vestibule, overhang on a red post, steps, ramp), roof — approx., in the model (GBF_BLD_Canteen)
- [ ] K.2 Small pavilion — approx., in the model (GB_BLD_Pavilion)
- [ ] K.3 One-storey building with a deep timber overhang on a red post (070410255 39–41 s): identify and model — approx.: taken as the canteen W porch (BLD_Canteen WestGlazedPorch)

## 10. Block B (zones `Gate`, `AW`)
- [ ] B.1 South (street) facade: bays between pilasters, windows, lettering band (blank KOCH) — approx., in the model (GBF_BLD_B Wall/Win/Sign)
- [ ] B.2 North (garden) facade — approx., in the model (GBF_BLD_B Wall/Win)
- [ ] B.3 West end — approx., in the model (GBF_BLD_B Wall)
- [ ] B.4 East facade: entrance canopy, door and threshold, maroon sloped covers — approx., in the model (GBF_BLD_B Entrance/LightwellCover)
- [ ] B.5 Low red-roofed annex at the NE corner — not confirmed: no annex visible on Bing z19 at B's NE corner (trees); not modelled
- [ ] B.6 Roof: slopes, hatch on the north slope — approx., in the model (GBF_BLD_B Roof)
- [ ] B.7 Front gallery on brick piers with terracotta soffit, white low railing and planters along the front path — approx., in the model (GBF_BLD_B GalleryPosts/GalleryRoof)
- [ ] B.8 Position: B–A gap settled on the mesh — approx.: Bing z19 roof edges B 147.0 / A gallery roof 157.6 (+2.2 m gallery) give a wall gap ≈13.0 m, close to the spec (13.4); B not moved (the Gate mesh is too hole-filled here; see M12)

## 11. Block A (zones `AW`, `Gate`)
- [ ] A.1 Main facade on the square: lettering band + round panel (blank KOCH), pilasters, windows, notice-board stands — approx., in the model (GBF_BLD_A_S/A_N)
- [ ] A.2 A_S south facade (street) — approx., in the model (GBF_BLD_A_S)
- [ ] A.3 A_S and A_N east facades (parking side) — approx., in the model (GBF_BLD_A_S/A_N)
- [ ] A.4 A_N north end (cut gable) — approx., in the model (GBF_BLD_A_N)
- [ ] A.5 A_E and the NE annex between A_N and A_S — approx., in the model (GBF_BLD_A_E)
- [ ] A.6 Two-storey part (hall + library) and the roof junctions — approx., in the model (GBF_BLD_A_W)
- [ ] A.7 Roofs of A — approx., in the model (GBF_BLD_A_* Roof)
- [ ] A.8 Junction A_S / gallery block — approx., in the model (A_S / A_W junction)
- [ ] A.9 Circle-pattern paving, red-tile retaining wall with steps and planting in front of the entrance pavilion — approx., in the model (GateAlley PavilionStair; circle paving = material)

## 12. Street front (zone `Street`)
- [ ] S.1 Sidewalk: clover/hexagon pavers, kerbs, levels — P1 measured x 92-118: 5.45 m from the planter-wall face to the parking bars, flat (ground mosaic + mesh cross-profiles, zone Street c3); x 118-150 4.3 m from Google; south side of the road: asphalt footway 1.9 m at y -135 between two lawn strips + paved link from the zebra (Google z20 + Street c6 mosaic), added
- [ ] S.2 Low parapet along the sidewalk with its steps; lawn level behind it — P1 measured: planter wall 0.35 m (mesh 0.31/0.38), west end at the block pillar x 90.95; steps at the joints and thickness (~0.12-0.15 m) still open (P2)
- [ ] S.3 Tree pits along the sidewalk — P1 partly: pit 02 measured (x 114.4, 1.5 m wide, >= 4.2 m long, overlay f01622 2.0 px), pits 01, 03, 04, 05 removed (paved in the Street c3/c2 mosaics and in f03347; trees 03/04 moved into the planter strip); pit 00 (mosaic hole) and 06-10 (east of the gate) still from Bing crowns
- [ ] S.4 Parking by the sidewalk with yellow-black barrier pipes — P1 partly: bar line 5.55 m from the parapet centreline at x 98-105 (was 3.6), tapering to 4.5 m at x 140 (Google noses); bar pitch not measured (mosaic: bars at x 98.0-99.6 and 102.3-104.7, model still 2.6 m)
- [ ] S.5 Zebra crossing, road kerbs, carriageway — P1 partly: crossing clip 065856484 (Gate c13, levelled on its sparse ground, placed on the Google zebra) matches the zebra (1.0 m stripe period) and the booth west edge (x 156.9 vs spec 157.3); south kerb 0.15 confirmed by the walked profile, north kerb dropped (flush) over the zebra; overlays f00146/f00401 median 5.0/4.0 px; carriageway camber and the gutter strip still open — P1✓ 3e8ba38 (obj_test: Zebra 2.0/5.0 px Street c3, 3.6 px Street c2, 4.0 px Gate c13; kerbs from the walked profile: south 0.14, north dropped)
- [ ] S.6 Bus stop (find it) and trolleybus poles; ATM kiosk by the fence — approx.: trolleybus poles every 35 m on the north kerb (TrolleyPole_*); bus stop not found in any frame or on the satellite, not modelled; ATM kiosk only in 2019 web frames (older state), not modelled | 2026-09-28 [A]: clip 065838589 f00004-f00066: the bus stops on the north kerb just east of the zebra, in front of the gate (x ~156-165); no shelter, no pavilion; a stop sign/plate not visible in any frame -> BLOCKED for the sign: photo request «Остановка у ворот»
- [ ] S.7 West end of the sidewalk (grey wall with the gas pipe) — P1 partly: block pillar / wall east face at x 90.9 (3 frames projected; was 92.2 and blocked the view), overlay f00030 1.4 px; mesh fence behind the kerb and the gas pipe not modelled yet
- [ ] S.8 Outside parking by the gate; residential towers as far massing — approx.: parking E of the gate with 10 wheel stops (Parking_EastOfGate, WheelStopE_*); towers as far massing = GB_CTX

## 13. West campus and others (web media, satellite; zone to add from the web frames)
- [ ] W.1 Block D: massing, floors, entrance canopies, rooftop penthouse, roofs — approx., in the model (GB_BLD_D_M / D_W massing)
- [ ] W.2 Block D frontage: ornate fence with stone-clad pillars and gate, second street gate with its booth and sliding gate, forecourt pavilions, blue-glass atrium — approx. from web photos only: fence with stone pillars + sliding gate + booth along the W face of D (SITE_WestFront); pavilions and atrium not placed (positions unknown)
- [ ] W.3 Block E (behind the sports hall): facades, outdoor fire stair, grey annex — approx., in the model (GB_BLD_W1_Ext/Roof)
- [ ] W.4 Complex south of D: decide whether it is campus; massing if yes — approx., in the model (GB_BLD_SouthComplex massing)
- [ ] W.5 Picnic-shelter row by the west 4-storey block — BLOCKED: web only (west block), location not fixed; not modelled
- [ ] W.6 Parking with garage sheds at the end of the long path; the container in the service alley — BLOCKED: web only, location not fixed; not modelled
- [ ] W.7 Unidentified volumes to place or drop: pale building with a red roof and a steel fire escape, barrel-vault roof building, dark-clad tall wall, pink block with a glass entrance — dropped: unidentified volumes outside the owner's footage, not modelled

## 14. Kits used everywhere
- [ ] KIT.1 Lamps: single/double globe lanterns, curly-bracket wall lanterns, curved-arm street lamps, ball lamps — approx.: site kit lamp/lamp_orn (build_site)
- [ ] KIT.2 Benches and bins: wrought-iron benches with slats, wrought-iron litter bins, wheelie and recycling bins — approx.: site kit bench/bin (build_site)
- [ ] KIT.3 Notice boards, info/map boards, wayfinding signs (blank KOCH faces) — approx.: site kit sign (build_site)

- [ ] AW.10 (CHECK: the inventory puts this bench row at the sports-hall east end, not A_N N end) Bench and conifer row along the N end of A_N (new, 081158036) — approx., SITE_CPlaza BenchAN/TreeAN/PlanterAN

## 15. Terrain and levels
- [ ] T.1 Terrace levels re-measured on the meshes (alley along B, walkway along A, garden/gazebos/C plaza, sports level) — approx., in the model (terrain_pads in the specs)
- [ ] T.2 Every outdoor stair and ramp between terraces counted and matched to T.1 — approx.: every stair/ramp in the specs with estimated riser counts (see M-table)
- [ ] T.3 Terrain pads and hard edges in the specs, no terrain poking through paving — approx., in the model (TER + pads)

## 16. Surroundings (500 m ring, handoff section 6; OSM © OpenStreetMap contributors, Art/Blender/Data/ctx_osm.json)
Each building: footprint from OSM, height from OSM `building:levels`/`height`, else floors counted in the owner's street videos / web photos / obliques (≈3.0 m per residential floor + ground floor + parapet); ready-made models (Fab, Poly Haven, BlenderKit free, Sketchfab CC0/CC-BY) scaled to the footprint, sources in docs/reference/asset_sources.md; collections `CTX_*`.

### Near buildings (≤150 m: facades, entrances, balconies, ground-floor shops from photos)
- [ ] CTX.Bway/169915330 yes, SE 2 m, 646 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/206623867 yes, E 3 m, 1492 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/206623848 yes, E 6 m, 452 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/169915374 yes, E 7 m, 260 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/761350988 yes, S 10 m, 24 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535016 yes, NE 14 m, 755 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/742042612 residential, NE 15 m, 685 m², 9.0 levels (OSM)
- [ ] CTX.Bway/761341971 yes, NW 16 m, 1109 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/255081513 school, W 19 m, 1126 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/206623794 yes, NE 20 m, 621 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/761350987 yes, S 23 m, 14 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/206623783 yes, N 26 m, 565 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/761341970 yes «Технодом соода борбору», NW 26 m, 2262 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/206614083 yes, W 30 m, 1558 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/1529424567 yes, N 36 m, 3498 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/761341972 yes, N 43 m, 530 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/169828217 yes, SE 46 m, 331 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535018 yes, NE 49 m, 971 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535017 yes, E 70 m, 617 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/129705598 yes, NW 72 m, 1985 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535009 yes, NW 77 m, 879 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535023 yes, NE 78 m, 440 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535022 yes, NE 78 m, 441 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535019 yes, NE 78 m, 440 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535021 yes, NE 78 m, 440 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535024 yes, NE 80 m, 441 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/761345513 yes, NE 80 m, 1349 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/632728361 yes, SE 82 m, 1128 m², 9.0 levels (OSM)
- [ ] CTX.Bway/341105719 yes «Аю Grand», N 86 m, 22747 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/632728362 yes, S 91 m, 862 m², 9.0 levels (OSM)
- [ ] CTX.Bway/632728363 yes, S 91 m, 1004 m², 9.0 levels (OSM)
- [ ] CTX.Bway/169915344 yes, E 94 m, 5429 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/206623827 yes, E 94 m, 911 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/206623793 yes, E 95 m, 275 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/169915381 yes, E 96 m, 1529 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/335552917 house, SE 99 m, 93 m², 2.0 levels (OSM)
- [ ] CTX.Bway/206623816 yes, E 100 m, 383 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535020 yes, NE 114 m, 440 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/1555086426 yes, S 115 m, 237 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/897518010 yes, SE 116 m, 217 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535014 yes, NE 120 m, 440 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535013 yes, NE 121 m, 440 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/1529424569 roof, N 125 m, 322 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/206623782 yes, NE 126 m, 430 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/169916490 mosque, S 127 m, 1564 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/206613116 yes, W 133 m, 1384 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/168164292 yes, W 134 m, 905 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/394617087 office «Центр обслуживания населения», NW 134 m, 1182 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/168164264 yes, W 135 m, 721 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/407836680 house, SE 136 m, 363 m², 3.0 levels (OSM)
- [ ] CTX.Bway/206613712 yes, W 136 m, 3713 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/635535008 yes, NW 137 m, 1681 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/169828200 house, SE 143 m, 90 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/1529424629 yes, SW 143 m, 214 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»
- [ ] CTX.Bway/877560915 yes, SE 143 m, 279 m², levels: count from photos — BLOCKED: not visible from any placed camera of the owner clips (campus blocks/trees in front, 2026-09-28 check); photo request «Окружение: фасады соседних зданий»

### Far buildings (150–500 m: massing, roof shape, floor rhythm, colour zones), grouped by direction
- [ ] CTX.FAR_E 21 buildings E of the campus (1 with OSM levels, 20 to count from photos/obliques)
- [ ] CTX.FAR_N 19 buildings N of the campus (1 with OSM levels, 18 to count from photos/obliques)
- [ ] CTX.FAR_NE 27 buildings NE of the campus (1 with OSM levels, 26 to count from photos/obliques)
- [ ] CTX.FAR_NW 29 buildings NW of the campus (0 with OSM levels, 29 to count from photos/obliques)
- [ ] CTX.FAR_S 31 buildings S of the campus (3 with OSM levels, 28 to count from photos/obliques)
- [ ] CTX.FAR_SE 65 buildings SE of the campus (22 with OSM levels, 43 to count from photos/obliques)
- [ ] CTX.FAR_SW 27 buildings SW of the campus (1 with OSM levels, 26 to count from photos/obliques)
- [ ] CTX.FAR_W 34 buildings W of the campus (1 with OSM levels, 33 to count from photos/obliques)

### Streets and stops
- [ ] CTX.ST Чолпон-Ата көчөсү: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Анкара көчөсү: carriageway (lanes 4), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST unnamed residential: carriageway (lanes 2), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Чокон Валиханов көчөсү: carriageway (lanes 3), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Исакеева улица: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Чолпон-Атинская улица: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Исакеев көчөсү: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Isakeeva street: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Altyn-Ordo street: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Akmatova Zhusupa street: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Subanova Temirkana street: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Kadyrbay Ata street: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.ST Alieva Chynybeka street: carriageway (lanes from photos), kerbs, sidewalks, lamps, trees, parking
- [ ] CTX.CROSS 17 crossings with zebras and signals
- [ ] CTX.STOPnode/1985920206 stop (no name) (SE 55 m): shelter, sign, kerb
- [ ] CTX.STOPnode/1985920208 stop "Ала-Тоо" университети (SW 107 m): shelter, sign, kerb
- [ ] CTX.STOPnode/13938860732 stop (no name) (S 108 m): shelter, sign, kerb
- [ ] CTX.STOPnode/1987293827 stop (no name) (W 196 m): shelter, sign, kerb
- [ ] CTX.STOPnode/3659060695 stop (no name) (SE 240 m): shelter, sign, kerb
- [ ] CTX.STOPnode/5886987749 stop Аю Гранд Комфорт (NW 420 m): shelter, sign, kerb
- [ ] CTX.STOPnode/5886987748 stop Аю Гранд Комфорт (NW 441 m): shelter, sign, kerb
- [ ] CTX.TROLLEY trolleybus poles and wires along the served streets

## 17. Objects added from the owner-footage inventory (2026-09-27, C:\koch\workiews\inventory_owner.md; sheets in views\inv)
### Street front
- [ ] INV.ST.1 Pink-tinted clover-paver patches set into the grey sidewalk and forecourt : 065653194_s3, 065934318_s2
- [ ] INV.ST.2 Storm-drain grating in the sidewalk against the parapet : 065653194_s1, 065653194_s2
- [ ] INV.ST.3 Two A-frame sandwich-board signs with blue faces at the crossing pole : 065856484_s1, 065856484_s2
- [ ] INV.ST.4 Two steel pyramid rebar tree guards on the pavement near the gate : 061913764_s2, 065856484_s1
- [ ] INV.ST.5 Blue traffic sign on a post by the crossing (pedestrian-crossing sign) : 061913764_s2, 012108212_s1
### Gate + booth + yard
- [ ] INV.GT.1 Brass "ALA-TOO INTERNATIONAL UNIVERSITY" plaque on the booth : 065910461_s1, 061913764_s1, 065856484_s1, 012136583_s1
- [ ] INV.GT.2 "Approved Test Centre" steel plate on the booth : 065910461_s1
- [ ] INV.GT.3 White round bulkhead lamps or sensors on the booth corners, x2 : 065910461_s1
- [ ] INV.GT.4 Card-reader box on the booth wall by the turnstile : 065910461_s1, 070021774_s1
- [ ] INV.GT.5 Brown steel pipe post with an electric meter box and cable, west of the booth : 065934318_s1
- [ ] INV.GT.6 Square recessed lights in the canopy soffit, x4–5 : 065910461_s1, 065910461_s2, 061757320_s3, 012136583_s1
- [ ] INV.GT.7 CCTV bullet camera under the canopy at the booth corner : 065910461_s2, 061913764_s1
- [ ] INV.GT.8 Hikvision face-recognition terminal on a steel pole/frame at the turnstiles : 065910461_s1, 065910461_s2, 070021774_s1
- [ ] INV.GT.9 Blue info plates on the gate and fence, x2 : 065856484_s1, 065910461_s2, 061757320_s3, 012136583_s1
- [ ] INV.GT.10 "Abiturient 2026" advertising billboard on 2 posts, leaning, west of the gate : 061913764_s1, 065653194_s3, 012136583_s2, 012108212_s2
- [ ] INV.GT.11 Green container/bin outside the fence : 082337333_s2
- [ ] INV.GT.12 Large pines beside the gate and a big poplar/elm over the booth : 061913764_s1, 012136583_s1, 012136583_s2, 082337333_s2
- [ ] INV.GT.13 Round cast-iron manhole cover (radial pattern) at the head of the south stair : 070309303_s1, photos_p20260925_s1 (012258813)
### Alley B-A
- [ ] INV.AL.1 Round manhole cover at the foot of the south stair : photos_p20260925_s1 (012205046), 061757320_s2
- [ ] INV.AL.2 Linear drainage channel between the circle strip and the herringbone : 082537786_s1, 082537786_s2
- [ ] INV.AL.3 Round clipped shrubs, x3–4, in the bed along A_S : 070309303_s3, 061757320_s2, 082537786_s2, 012327726_s1
- [ ] INV.AL.4 Maroon ledge/plinth boxes at the foot of A_S, plus a small maroon box : 012327726_s1, 012404116_s1
- [ ] INV.AL.5 Benches (black frame, wooden slats) under the trees at the A_S corner, x2 : 070021774_s2
### A_W gallery + plaza between C and A
- [ ] INV.AWP.1 Flat grey corrugated-metal awnings over the doors under the gallery, x2 : 012327726_s1, 070309303_s2
- [ ] INV.AWP.2 Yellow sign plate above a gallery door : 070309303_s2, 012404116_s2
- [ ] INV.AWP.3 Floor drain grille in the gallery deck : 012327726_s2
- [ ] INV.AWP.4 White plastic chair under the gallery (movable) : 070309303_s2, 070309303_s3
- [ ] INV.AWP.5 White downpipes on the A_W wall, x3 : 070309303_s3
- [ ] INV.AWP.6 LED floodlight on the A_W wall at F2 sill level, x1–2 : 070309303_s3
- [ ] INV.AWP.7 Round vent hole in the A_W wall : 070309303_s3
- [ ] INV.AWP.8 Round manhole cover on the plaza by the gallery : 012327726_s2, 012404116_s1
- [ ] INV.AWP.9 Red-kerbed lawn beds with small conifers : 070309303_s3
- [ ] INV.AWP.10 Small ground spot lamp in one of those beds : 070309303_s3
- [ ] INV.AWP.11 Blue spruces x3 and a thuja row at the plaza : 081235159_s1, 081235159_s2, 012404116_s2
- [ ] INV.AWP.12 Stamped pink pavers with a painted red line on the paving : 081235159_s1, 081249927_s1
- [ ] INV.AWP.13 Yellow bar or tape across the far path (temporary?) : 081235159_s1
### C plaza + exterior
- [ ] INV.CX.1 Small "C" plate above the storefront : 070647586_s2, photos_p20260924_s1 (061431726, 061631264), zz_c_front2
- [ ] INV.CX.2 Small ground flood-lamp boxes standing on the light-well cover, x2 : 081158036_s2
- [ ] INV.CX.3 Parked cars east of C (a parking area) : 070647586_s1, zz_c_front, photos_p20260924_s1 (061621646, 061624280)
- [ ] INV.CX.4 Brown/maroon boundary fence far east of C : 070647586_s1, zz_c_front
- [ ] INV.CX.5 Overhead wires crossing over C and the plaza : 070647586_s1, 081158036_s1, 070629483_s1, zz_c_side
- [ ] INV.CX.6 Wall vent grille on the C.12 box : photos_p20260925_s2 (012520140)
- [ ] INV.CX.7 Black lamp post, blue spruce and yellow-kerbed lawn behind the west shed : photos_p20260925_s1 (012456258), photos_p20260925_s2 (012458018), zz_c_side
- [ ] INV.CX.8 Second sunken basement stair with rails at the north end of the C west wall : 070629483_s2, 012436367_s2, photos_p20260925_s2 (012526070)
- [ ] INV.CX.9 White painted arrows on the paving west of C, x3 : 070629483_s2, 012436367_s2, photos_p20260925_s2 (012507444)
- [ ] INV.CX.10 Parked cars at the north end of the C west side : 070629483_s2
### C interior (lobby, corridors, stairs, classroom, WC)
- [ ] INV.CIN.1 Water cooler with a blue bottle : 070704360_s1, 080443026_s1
- [ ] INV.CIN.2 Double wall socket by the cooler : 070704360_s1
- [ ] INV.CIN.3 Pull-up banner stands (blue/yellow), x2 : 070704360_s1
- [ ] INV.CIN.4 Red fire-hose cabinets: lobby, stair hall, below the landing [CI.2 lists only fire-alarm boxes] : 070704360_s1, 070704360_s2, 080051708_s1
- [ ] INV.CIN.5 Linear LED wall lights in the stair hall and landings : 070704360_s2, 080051708_s2
- [ ] INV.CIN.6 Wall-mounted CCTV in the lobby corridor, CCTV domes on the stair-hall ceiling and a landing corner : 070704360_s1, 052716931_s2, 080051708_s2
- [ ] INV.CIN.7 White heating pipes along the floor and walls, riser pipes with brass/red valves : 070704360_s2, 080011086_s1, 080051708_s2, 080443026_s2, 052716931_s2
- [ ] INV.CIN.8 Potted plants on landing sills and ledges: x3 in the stair hall, x2 in the stairwell, spider plants x3 on the landing ledge : 070704360_s2, 080011086_s1, 080051708_s1
- [ ] INV.CIN.9 Potted floor plants (ficus/dracaena), x4, along the rail at the foot of the stair : 052716931_s2
- [ ] INV.CIN.10 Black utility doors at the landings, beside the landing windows : 070704360_s2, 080011086_s2, 080051708_s2
- [ ] INV.CIN.11 Red fire box on the upper landing : 080011086_s2
- [ ] INV.CIN.12 Light switches in the stairwell : 080011086_s1
- [ ] INV.CIN.13 Small black notice frames on the blue panels, x2 : 080443026_s1
- [ ] INV.CIN.14 Black wall-mounted units high on the corridor walls (Wi-Fi APs/speakers), x3 : 080443026_s1, 080443026_s2
- [ ] INV.CIN.15 Card reader/electronic lock on a classroom door : 052716931_s1
- [ ] INV.CIN.16 Open double glazed doors from the corridor to the stair hall : 052716931_s2
- [ ] INV.CIN.17 Black network rack cabinet with a distribution board below it, on the classroom wall : 074805359_s1, 074805359_s2
- [ ] INV.CIN.18 Round smoke detector and a CCTV dome in the corner of the classroom ceiling : 074805359_s1, 074805359_s2
- [ ] INV.CIN.19 Sloped ceiling bulkhead along one classroom wall : 074805359_s1
- [ ] INV.CIN.20 Teal wire waste bin by the classroom door : 074805359_s2
- [ ] INV.CIN.21 Light switch by the classroom door : 074805359_s2
- [ ] INV.CIN.22 Heating pipe along the classroom skirting : 074805359_s2
- [ ] INV.CIN.23 WC large frameless mirror : 075931189_s1, 075931189_s2
- [ ] INV.CIN.24 WC white soap dispenser : 075931189_s1, 075931189_s2
- [ ] INV.CIN.25 WC waste bin with a black bag between the sinks : 075931189_s1, 075931189_s2
- [ ] INV.CIN.26 WC radiator, 6-section : 075931189_s1
- [ ] INV.CIN.27 WC high narrow window with a transom at the end wall : 075931189_s1, 075931189_s2
- [ ] INV.CIN.28 WC wall vent grille above the tile, and a socket : 075931189_s2
- [ ] INV.CIN.29 WC round ceiling light and white cornice moulding : 075931189_s1, 075725091_s1
- [ ] INV.CIN.30 Small floor-drain grate in the WC vestibule : 075931189_s2
- [ ] INV.CIN.31 Aluminium threshold at the black solid WC entry door : 075931189_s2
- [ ] INV.CIN.32 WC stall: grey gloss stretch ceiling with a round downlight and a round vent diffuser : 075725091_s1, 075725091_s2
- [ ] INV.CIN.33 WC stall: cistern pull chain, flexi hose, angle valve, white flush pipe : 075725091_s1, 075725091_s2
- [ ] INV.CIN.34 WC stall: vertical riser pipe in the corner, tiled duct ledge on the back wall : 075725091_s1, 075725091_s2
- [ ] INV.CIN.35 WC stall: toilet-brush holder, "FOCUS" paper dispensers : 075725091_s1, 075725091_s2, 075928860_s1
- [ ] INV.CIN.36 WC stall: small grey or black lidded bins, x2+ : 075725091_s2, 075928860_s1
- [ ] INV.CIN.37 WC stall: air-freshener can : 075725091_s2
- [ ] INV.CIN.38 WC stall door lever handles; light switch on the tile : 075725091_s2, 075928860_s1
### C basement
- [ ] INV.CB.1 Wood-look PVC door in the red-tile wall at the stair landing : 012547860_s1
- [ ] INV.CB.2 Beige brick-slip tile wainscot ~1 m, with white textured plaster above : 012547860_s1, 012547860_s2, photos_p20260925_s2 (012657890)
- [ ] INV.CB.3 White coved cornice : 012547860_s1
- [ ] INV.CB.4 Recessed round downlights in a row, x10+ : 012547860_s1, 012547860_s2
- [ ] INV.CB.5 Round inline duct fans (blue/steel) high on the wall, x2 : 012547860_s1, 012547860_s2
- [ ] INV.CB.6 Tall orange-laminate wardrobes stored along the corridor, x3 : 012547860_s1, 012547860_s2
- [ ] INV.CB.7 Stored orange laminate desks/benches, x3 : 012547860_s3
- [ ] INV.CB.8 Second stair, 4–5 granite risers with a scroll rail, up to an exit under a white corrugated canopy : 012547860_s1, 012547860_s2
- [ ] INV.CB.9 Bentwood chairs in the piano room, x2 : 012547860_s3, photos_p20260925_s2 (012646951, 012648584)
- [ ] INV.CB.10 Paper notices on the piano-room walls, x2 : 012547860_s3, photos_p20260925_s2 (012646951)
- [ ] INV.CB.11 One-step raised floor/threshold strip and a sloped ceiling under the stair : 012547860_s3
- [ ] INV.CB.12 Basement exit: brown steel door : photos_p20260925_s2 (012657890)
- [ ] INV.CB.13 Barred transom windows, x3, and flanking windows, x2, with hexagon grilles at the exit door : photos_p20260925_s2 (012657890)
- [ ] INV.CB.14 Stainless 3-bar floor frame (boot scraper or drain frame) on the tile : photos_p20260925_s3 (012705563)
- [ ] INV.CB.15 Basement hall (assumed C basement, check): beige polished porcelain 60 × 60 tiles with dark-grey border strips : 012714931_s1, 012714931_s2, 012800431_s1, 012800431_s2
- [ ] INV.CB.16 Grey-painted dado ~1.1 m, white above : 012714931_s1, 012744144_s1, 012800431_s1
- [ ] INV.CB.17 LED 600 panels (recessed and surface-mounted) : 012714931_s1, 012744144_s1, 012744144_s2
- [ ] INV.CB.18 Black 4-seat beam seating (airport style), x2, plus a 2-seat, x1 : 012714931_s1, 012714931_s2
- [ ] INV.CB.19 White marble-look wardrobes (2-door, and a tall one) : 012714931_s1, 012744144_s2
- [ ] INV.CB.20 Hall radiators and a black bin : 012714931_s1
- [ ] INV.CB.21 Exposed black cable conduit along the ceiling : 012714931_s1, 012744144_s2
- [ ] INV.CB.22 White electrical cabinet with a hazard sign in a wall niche : 012714931_s1
- [ ] INV.CB.23 CCTV domes, x2+ : 012714931_s1, 012714931_s2, 012744144_s1, 012744144_s2
- [ ] INV.CB.24 Arched vestibule with 2 brown wooden doors (vision panel, card lock, name plates) and black louvred vent grilles high up, x2 : 012714931_s2
- [ ] INV.CB.25 Brown tile steps with grooved nosings: 1–3 risers into the vestibule, 4 risers down to the lower lobby, 3–4 risers at the "C001 LAB" door : 012714931_s2, 012744144_s1, 012800431_s1, 012800431_s2
- [ ] INV.CB.26 "C001 LAB" wooden door with a purple plate, vision panel, card reader, QR poster : 012800431_s1
- [ ] INV.CB.27 Wooden doors with vision panels and plates, and a door plated "ИЗОБРАЖ…" (art room), x3+ : 012744144_s1, 012800431_s2
- [ ] INV.CB.28 Black door with an ornamental frame, circle emblem and vision panel : 012800431_s2
- [ ] INV.CB.29 Art room: black office chairs, x2–3 : 012744144_s1
- [ ] INV.CB.30 Art room: stacked wooden easels and plywood boards, ~15 : 012744144_s1, 012714931_s1, 012714931_s2
- [ ] INV.CB.31 Brown line-art wall mural (mountains, horse, yurt) : 012744144_s1, 012714931_s2
- [ ] INV.CB.32 Art room: radiators x2, surface LED panels x2, smoke detector, CCTV domes x2 : 012744144_s1
- [ ] INV.CB.33 Round Ala-Too logo discs on the walls above the arches, x2 : 012744144_s2, 012800431_s1, 012800431_s2
- [ ] INV.CB.34 Black-framed notice board on the wall : 012744144_s2
- [ ] INV.CB.35 Rectangular wall moulding panels, x2–3 : 012800431_s2
- [ ] INV.CB.36 Exit end wall: steel entry door with a "ПОЖАР / ВЫХОД" sign, barred transom windows x3, flanking barred windows x2, radiators x2 : 012744144_s2
- [ ] INV.CB.37 Navy/blue steel 2-door locker cabinet with posters : 012800431_s2
- [ ] INV.CB.38 Blue folding panel leaning on the wall : 012800431_s2
- [ ] INV.CB.39 Ceiling access hatches, x2 : 012800431_s1, 012800431_s2
- [ ] INV.CB.40 Small wall vent grilles, x2 : 012800431_s2
### Hall-C passage + sports hall + wing
- [ ] INV.HP.1 Red steel ladder up to a roof-hatch opening : 081158036_s1
- [ ] INV.HP.2 Tall galvanised ventilation duct up the corner; 2 exhaust stacks above the roof : 081158036_s1, 070629483_s1, 061707849_s1
- [ ] INV.HP.3 Galvanised ventilation box units with fans at ground level, x2 : 061707849_s1, 061707849_s2, photos_p20260924_s1 (061638726)
- [ ] INV.HP.4 BEKO AC outdoor unit on the ground; AC units on the wall, x2 : 061707849_s1, 081158036_s1
- [ ] INV.HP.5 White and red downpipes, x2 : 061707849_s1, 081158036_s1
- [ ] INV.HP.6 Black tarp-covered pile (generator or stock), with leaning boards/planks and a wooden dog-kennel box : 061707849_s1, 061707849_s2, 081158036_s1, 081213784_s1, 070629483_s1, 012436367_s1
- [ ] INV.HP.7 Black-yellow striped bollards at the parking entrance, x2, plus a short post : photos_p20260924_s1 (061643243, 061648727), 061707849_s2
- [ ] INV.HP.8 Parking lot beside the hall, ~10 cars, with a brown corrugated-sheet boundary fence : 081158036_s1, 061707849_s2, photos_p20260924_s1 (061643243, 061648727)
- [ ] INV.HP.9 CCTV under the east-end canopy soffit : 012429784_s1
- [ ] INV.HP.10 Floodlights on the wing fascia, x2 : 081213784_s1, 070629483_s1
- [ ] INV.HP.11 Small stair with handrails at the end of the wing, and a brick pier : 081213784_s1
- [ ] INV.HP.12 Vent/AC box near the hall corner by the passage : 012436367_s1
- [ ] INV.HP.13 2 steps up to the gallery deck (red-brown granite edge), with a ramp and rail at the far end : 070410255_s1
- [ ] INV.HP.14 Colourful mural band with windows on the pink hall wall, seen from the garden gazebo : 082013462_s2
### Garden
- [ ] INV.GDN.1 Gazebo recessed downlights in the soffit, x2 : 082013462_s1
- [ ] INV.GDN.2 Continuous polygonal wooden bench on steel legs inside the gazebo : 081924271_s1, 081924271_s3
- [ ] INV.GDN.3 "NO SMOKING" sign on a gazebo pillar : 082013462_s1
- [ ] INV.GDN.4 Maroon fence/wall behind the rubble-stone wall : 081958653_s1
- [ ] INV.GDN.5 Red-brick block/seat or stand at the far side : 081924271_s1
- [ ] INV.GDN.6 Bench with an arched ornamental back rail (a second bench type) : 082006491_s1
- [ ] INV.GDN.7 Big white-bark poplars x2, a willow : 081946180_s1, 081958653_s1, 082006491_s1
- [ ] INV.GDN.8 Sprinkler risers in the lawn, x3 : 081856511_s1
- [ ] INV.GDN.9 Boulder in the lawn : 081946180_s1
- [ ] INV.GDN.10 Orange flower pot at the mouth of a path : 081958653_s1
- [ ] INV.GDN.11 Rose bed with a low fence along the B north facade : 082013462_s1
- [ ] INV.GDN.12 Yellow wheelie bin at the garden edge : 012404116_s2
### Sports fields/courts + decorated alley
- [ ] INV.SPF.1 White football goal : 070541257_s2
- [ ] INV.SPF.2 Black bin by the pitch gate : 070410255_s3
- [ ] INV.SPF.3 Wooden-framed glazed hexagonal kiosk/conservatory at the E corner of the pitch : 070410255_s3
- [ ] INV.SPF.4 Clover pavers laid in a pink-and-grey pattern on the sports plaza : 070410255_s3
- [ ] INV.SPF.5 Blue spruces, x3, on the plaza slope : 070410255_s2
- [ ] INV.SPF.6 Plant name tag on a stake by a shrub : 070410255_s3
- [ ] INV.SPF.7 Yellow painted line on the paving (plaza boundary) : 070410255_s2
- [ ] INV.SPF.8 Manhole cover in the square : 070410255_s2
- [ ] INV.SPF.9 Rose shrubs in the alley beds : 070541257_s1, 070541257_s2
### Canteen + small buildings
- [ ] INV.KN.1 Ventilation grilles/boxes at the base of the canteen wall, x2 : 070541257_s1
- [ ] INV.KN.2 Grey-green cylindrical fan box on a stand in the service yard : 070410255_s3
- [ ] INV.KN.3 Parked cars behind the canteen, x4 (service parking) : 070410255_s3
- [ ] INV.KN.4 Yellow-kerbed planter bed with a young tree in the service yard : 070410255_s3
- [ ] INV.KN.5 Short yellow/white painted parking-stop kerb segments on the paving, x3 : 070541257_s1
- [ ] INV.KN.6 Blue spruces x3–4 and thuja pairs x3 around the canteen lawn : 081249927_s1, 081249927_s2, 081213784_s1
- [ ] INV.KN.7 Triangular lawn with yellow and white painted kerbs; curving herringbone path : 081249927_s1, 081249927_s2
- [ ] INV.KN.8 Tall chimney/flue mast : 061550830_s1, 070541257_s1, 081235159_s1, 061707849_s1
### Block B
- [ ] INV.BB.1 White-column gallery on the B north side, seen beyond the hedge : 082006491_s1, 082006491_s2
- [ ] INV.BB.2 Blue-roofed sheds and corrugated structures at B's rear : 081904575_s1, 081904575_s2
- [ ] INV.BB.3 AC outdoor units on the B south facade upper floors, x5–6 : 065934318_s1, 065934318_s2
- [ ] INV.BB.4 Drain grating at the far end of the front path : 065934318_s1
- [ ] INV.BB.5 Step down from the booth apron to the front path : 065934318_s1
- [ ] INV.BB.6 Pines and poplars along the front path : 065934318_s1, 065934318_s2
### Block A
- [ ] INV.BA.1 Benches (black), x3, along the path in front of A : 082248481_s1
- [ ] INV.BA.2 Small ground spot lamps on short posts in the lawn, x2 : 082248481_s1, 082606037_s1
- [ ] INV.BA.3 Pavilion horizontal downpipe : 070309303_s1, 061757320_s2
- [ ] INV.BA.4 Wheelie bin under the pavilion : 082537786_s1
- [ ] INV.BA.5 "A Block" blue plate on the maroon corner pilaster : 082337333_s1, 070309303_s1, photos_p20260925_s1 (012208814)
- [ ] INV.BA.6 CCTV bullet cameras on the A_S corner pilaster, x2 : 082337333_s1, 070309303_s1, 070021774_s1, photos_p20260925_s1 (012208814)
- [ ] INV.BA.7 AC unit cluster (AUX/Beko/Midea) on the A_S west face over F1–F2, x6+ : 082337333_s1, 070309303_s2, photos_p20260925_s1 (012227815, 012231007)
- [ ] INV.BA.8 Potted plants on the A_S window sills : 070309303_s2
- [ ] INV.BA.9 Small clipped conifers planted in the paving in front of A_S, x2 : 082337333_s1
- [ ] INV.BA.10 Round manhole cover beside a red-kerbed planter at the A_S corner : 070021774_s2
- [ ] INV.BA.11 Red-kerbed sloped planter with a conifer at the stair head : 070021774_s2
### Other
- [ ] INV.OT.1 Overhead power/telecom wires strung across the campus between the buildings : 070647586_s1, 081158036_s1, 081249927_s1, 070410255_s1, 012436367_s1, zz_c_side

## Замеры для проверки (значения по оценке; после рулетки править только указанное поле и пересобрать)
Rebuild: `blender -b Art/Blender/KOCH_Campus_Greybox.blend -P Scripts/Blender/build_all.py`

| # | Что | Сейчас | Поле в спеке | Что замерить |
|---|---|---|---|---|
| M1 | Ширина бордовой башни C | 3.80 | BLD_C.json `ring` (x 12.8…16.6) | по фасаду над козырьком |
| M2 | Вынос зап. крыла перед витриной | 1.30 (меш даёт ~2.7) | BLD_C.json `ring` (y 0 / 1.3) | от витрины до фасада зап. крыла |
| M3 | Ширина витрины входа | 3.76 (фото даёт 4.75) | BLD_C `facades[edge 2].entrance.u0/u1` | по раме |
| M4 | Подступенок / проступь крыльца | 0.154 / 0.475, 7 шт | BLD_C `attachments[stairs].riser_h/tread/risers` | одна ступень |
| M5 | Глубина площадки у двери | 2.65 | BLD_C `attachments[stairs].landing` | от витрины до края верхней ступени |
| M6 | Козырёк: вынос, низ и верх короба | 5.6 / +3.10 / +4.65 | BLD_C `attachments[canopy].depth/z0/sign.z1` | вынос шагами, высоты рулеткой |
| M7 | Пандус: ширина, отступ от фасада, длина | 1.0 / 3.5 / до u 9.5 | BLD_C `attachments[ramp name Run]` | ширина настила, где кончается |
| M8 | Высота этажа C | 3.30 | BLD_C `storey_m` | подступенки одного марша × высота |
| M10 | Сев. торец A_N / A_W (стена) | y −20.2 (сдвинут на 3.3 м к югу; фото даёт −22.5±1.5) | BLD_A_N.json / BLD_A_W.json `ring` (y 73.2 / 72.95) | от угла C до торца A_N |
| M11 | Окна вост. крыла C | сдвиг ~0.3 м от фото | BLD_C.json `facades[edge 3].windows[].u` | шаг окон по фасаду |
| M12 | Зазор B–A (стена B – стена A_S) | 13.0–13.4 | BLD_B.json `ring` / anchor | рулеткой поперёк аллеи |
| M9 | Масштаб меша входа (плитка) | 0.20 × 0.10 → 0.4737 м/ед. | C:/koch/work/world_ce/xf_c2.json | один «кирпичик» |

## Log
- [A] 2026-09-28: AW c8 (clip 012404116, B-corner steps -> gallery -> garden arch) placed at P0 (+-2 m): yaw from its gallery-front line, across on the gallery post line x 162.8, along from the steps. f00638: the red-edged planters with trees stand on the plaza in front of the A_W gallery (confirms the PlanterAN/TreeAN row near the gallery); planter positions still ~1-2 m off in that frame (P1 open).
- [A] 2026-09-28: C light-well covers + plinth overlaid on 070647586 f00302/f00354 (only these objects): cover slope and its end at the stair cheek line up in f00354 (8.0 px); f00302 23.6 px is the stair in front (render has no occluders). Whole-C overlay on f00302/081158036 f00629: window grid, tower, canopy and sign match by eye (16-22 px from trees/people).
- [A] 2026-09-28: C south-west wing windows next to the tower checked large on 070647586 f00354 (windows + surrounds only): F1/F2 columns sit on the photo windows -> the +0.9 m column offset seen in the C_entr mesh section is a mesh artefact, spec kept. obj_test over C_entr c2: AC units pass (6.0/2.2 px); canopy, plinth, cornice, windows, plaza planters/trees/benches fail on the picked frames because the object is hidden (trees, the canopy, off-frame) - the metric is not meaningful there, own look per object needed.
- [A] 2026-09-28: obj_test P1 over Street c3/c2, Gate c13/c8: pass (>= 2 cams <= 8 px) booth, canopy, sliding gate, fence, zebra, pit 02, tree 02, flagpoles, billboard, A_S, B; fail: parapet/hedge (c8 view 14-17 px), trolley pole 0 and west wall (1 camera only), wheel stops (35.8 px in c3 f01053: bar pitch not measured). Note: the edge metric is lenient in cluttered frames (trees) - ticks only where the own look agreed.
- [A] 2026-09-28: street banner billboard moved to x ~129.8 at the planter edge (was 143.6; bearings from 3 Street c2 frames + its 2 m height), 2 white flagpoles added next to it; overlays f02711/f02947 median 2.0/2.2 px.
- [A] 2026-09-28: near ring floor counts: 49 buildings have no OSM levels; projected into every placed camera (Street c3/c2, Gate c13/c8, C_entr c2): only 6 in view and those hidden behind campus blocks/trees -> BLOCKED with one photo request (street walk around the campus). P2 material slots everywhere (site/facade/name/ground surfaces).
- [A] 2026-09-28: basement stair count confirmed from frames (8 + 2); lesson: eye-height scale is unreliable where the walker is on a stair or in a narrow stairwell (few ground planes) - check the scale on a known size before using a walk depth.
- [A] 2026-09-28: C south-west wing facade section on the C_entr mesh: window heads F1 9.01 / F2 12.16 (spec rows 8.85+0.2 / 12.15: confirmed); the last wing column lies at u 10.3-12.7 in the mesh vs 9.57-11.80 in the spec (+0.9 m, same size as the old storefront/tower offset) - overlays from 070647586 f00354 / 081158036 f00644 inconclusive (11 / 17 px); left as is until a frontal check.
- [A] 2026-09-28: gate forecourt checked on Google z20 (parking noses/bars, north kerb, booth, pits 06/07 under the canopy) - no gross error. AW c8 (clip 012404116): the B-corner steps counted again 6 granite + kerb = 7 risers (spec OK); the -0.75 m in its walk profile is the phone lowered at the stair foot, not a descent; the mesh has no stair (region misses it), riser 0.183 stays unverified. C_F2F5 (upper floors) aligned into small pieces only (largest 49 of ~830 frames: white walls).
- [A] 2026-09-28: Street P1 pass_check: route 76 % within 0.07 m (FAIL) - the bad runs are camera-height artefacts (phone lowered/raised at the clip ends, gap between c3 and c2), the mesh sidewalk is flat 7.46-7.53 vs the model 7.57-7.37; overlays median <= 8 px. South footway + zebra link added (Google z20, Street c6 is bent).
- [A] 2026-09-28: C_F1 meshed at Normal (c3 288 cams, 3M tris; c5). Main stair profile on the mesh: risers 0.149-0.169 (median 0.155), treads 0.28-0.30 -> all 12 C stair flights tread 0.332 -> 0.30. C_sw c1 mesh is a 10 x 5 m spot (camera stood still): not usable for placement.
- [A] 2026-09-28: Gate c8 (alley B-A walk) placed: yaw from its A_S facade line, along from the A_S porch block in the mesh, across from the Google z20 ortho (B gallery left of the walker in f00550); +-1.5 m along. Alley walk profile flat 6.8-7.1 (no steps on that line). Gate c6 is a pan from one spot (weak mesh) -> forecourt stays on Google z20. Queue: unfinished zones switched to detail normal + simplify 3M (handoff 2.5).
- [A] 2026-09-27: mesh drop Garden (c8, c3), Sports (c2, c9), C_sw (c1, c7), WEB_drone (c1, c2) -> C:\koch\drop\koch_meshes_20260927.zip (321 MB): world-metre PLY <= 3M tris (vertex clustering 0.8-5.6 cm), cameras, route.json; aligns are levelled + eye-height metric with xy/yaw placeholders (WEB_drone raw RS units, not metric).
- 2026-09-27 (night): crossing: Gate c13 placed (sparse ground plane + Google zebra); dropped kerb at the zebra, parking bars 0.25 m (Street c2 mesh), route_profile over Street c3/c2 + Gate c13: sidewalk flat 7.46-7.53, the -0.42/-1.69 'events' in c2 are the phone lowered at the end of the clip (mesh ground flat), not steps.
- 2026-09-27 (night): Street c2 placed by the gate booth SW corner (triangulated 40.6 m in f02711/f02947/f03103, booth face width gives 40.2 m) with the yaw from the walked line; walked line 2.0 m from the wall face (c3: 2.4). Its mosaic: no pits at x 118.8-140 -> pits 03, 04, 05 removed; overlay f02711 median 3.0 px.
- 2026-09-27 (night): world frame: pairwise merge Street+Gate (pair_merge.py) failed three ways (GLOMAP pair: scale differs 3x between the zones; strict incremental: 10 models, Street and Gate never joined) -> zones placed by the mesh/satellite (owner rule). Street c3 placed by the planter-wall face (yaw, lateral) and the block pillar (along), scale from the eye height checked on the paver lattice; sidewalk, bars, pit 02, west wall and planter-wall height set from a ground mosaic of the frames (tools/ground_mosaic.py) and mesh profiles.
- 2026-09-27 P0 frame: per-component auto registration failed (walls vs specs, ground ortho vs Bing, outlines vs photos: the true C-entrance pose scores below wrong ones); up/scale per component are good (ground planes + eye 1.52 m, scale within 0.8 %%). Whole-site alignment ALL (38 exterior clips, every 2nd frame, all stills) queued first for one world frame; cp_fit.py ready for control points on what stays separate. route_profile tested on C_entr (4 events). pass_check.py written.
- 2026-09-27 (evening): C entrance re-expressed from the tower face: the mesh puts the tower wall 0.9 m in front of the storefront (landing 1.75, canopy 4.7, storefront recess 0.9); C.5/C.6 window fit by photo edges is unstable (periodic facade) -> waiting for the C_photos zone mesh; next object H.1-H.3 (C_sw c7: pavers 0.305 u, camera height 4.38 u -> ~0.33-0.37 m/unit, frame is -Y up).
- 2026-09-27: list built from ROUTE.md, campus.md, photo_requests.md, the handoff, the specs, the capture clips (incl. the 2026-09-25 batch: gate, A_W walkway, C west side, C basement) and the web-media triage (C:\koch\web\triage_part1.md, triage_part2.md). Best web sources for roofs and back sides: the 2023-01-28 drone flight, 2022-04-19, 2020-05-16 and 2022-10-30 aerials.
- 2026-09-27: queue extended with WEB_front (2026-05-22, 2023-03-20 clips), WEB_drone (2023-01-28, 640x352), C_F1, C_lab, C_wc (interior clips extracted + masked).
- 2026-09-27: GPU queue started with zones C_sw, AW, Gate, Sports, Garden, Street, C_base.
