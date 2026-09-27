# R1 progress: the whole map as 1:1 geometry, coarse to fine

Checklist for docs/roles/R1-photogrammetry-handoff.md **section 0 (passes)**. Every zone reaches pass N before any zone
starts N+1. A zone-pass is done when its scripted test AND your own review of the frames/overlays both pass (handoff
3a). Each object line gets the highest pass it passed plus the commit, e.g. `P1✓ 1a2b3c4`; `[x]` only at its depth
cap. "approx.", "in the model", "estimated" never count. Blockers: `BLOCKED: <reason>` + a photo request.

- **Meshes** come from the GPU queue (outside git): `C:\koch\work\gpu_queue.ps1` runs the zones of `C:\koch\work\queue.txt` one by one through `Scripts/Geo/rs/zone_job.py` (align → cameras/poses → mesh into `C:\koch\work\zones\<zone>\`). The state of each zone is in `C:\koch\work\status.txt`.
- **Sources:** the owner's capture (`C:\koch\alatoo-capture\raw`, frames in `C:\koch\work\frames_a`, clip ids `PXL_2026092x_<id>`), web media (`C:\koch\web`), satellite orthos (`alatoo-capture/data/ortho`). Meshes, frames, masks and photos stay outside git.
- **Levels:** `route_profile.py` over all zones → `route_check.py` (handoff 0a).

## Pass grid (zone × pass; cell = commit when passed, `—` above the cap)
| Zone (route order) | Cap | P0 | P1 | P2 | P3 |
|---|---|---|---|---|---|
| Street, bus stop, crossing (§12) | P3 | | | | |
| Gate, booth, yard (§4 G.1-G.5) | P3 | | | | |
| Alley B–A (§4 G.6-G.13) | P3 | | | | |
| A_W gallery + plaza (§3) | P3 | | | | |
| C plaza + exterior (§1) | P3 | | | | |
| C interior F1-F5 (§2 CI.1-CI.8) | P3 | | | | |
| C basement (§2 CI.9, §1 C.12) | P3 | | | | |
| Hall–C passage (§5) | P3 | | | | |
| Garden (§6) | P3 | | | | |
| Sports fields (§7) | P3 | | | | |
| Sports hall, canteen (§8, §9) | P3 | | | | |
| Block B (§10) | P3 | | | | |
| Block A (§11) | P3 | | | | |
| Terrain + levels (§15) | P3 | | | | |
| West campus D/E (§13) | P2 | | | | — |
| Ring ≤ 150 m + streets/stops (§16) | P2 | | | | — |
| Ring > 150 m (§16 far) | P1 | | | — | — |

The ticks below from before 2026-09-27 (C.1-C.3) were fitted before the world frame was fixed: they count as P3 only
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
- [ ] CI.3 West stair F1–F3: flights, landings, window, white steel balustrade — approx., in the model (GBS_INT_C_Floors)
- [ ] CI.4 East stair F1–F5: flights, landings, windows, balustrade (riser count per flight) — approx., in the model (GBS_INT_C_Floors)
- [ ] CI.5 WC pair F1: sinks, stalls with black doors, squat pans, high cisterns, tile to 1.4 m — approx., in the model (GBS_INT_C_F1)
- [ ] CI.6 Prototype classroom 203 (computer lab): desks, chairs, TV, whiteboard, grid ceiling, windows with blinds — approx.: computer-lab furniture in the F2 north room next to door N1 (INT_C_Floors F2_Lab_*); room choice from ROUTE (north windows), not confirmed
- [ ] CI.7 Floors F2–F4: corridors, classrooms, WCs (F4 without the west stair: offices) — approx., in the model (GBS_INT_C_Floors)
- [ ] CI.8 F5 attic offices under the roof, lit by the dormers — approx., in the model (GBS_INT_C_Floors)
- [ ] CI.9 Basement: stair down with wrought-iron balustrade, vaulted corridor, barred windows, art room, piano room — approx., in the model (GBS_INT_C_Basement)

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
- [ ] G.1 Checkpoint booth: tile walls, brick plinth, doors, windows, roof — approx., in the model (GBF_BLD_GateBooth)
- [ ] G.2 Gate canopy on its round column: roof pitch, ends, timber soffit, fascia panel (blank KOCH) — approx., in the model (GBS_Gate_GateCanopy)
- [ ] G.3 Turnstiles and the pass-through railings — approx., in the model (GBS_Gate_Turnstile/LaneRail)
- [ ] G.4 Sliding gate leaves, fence panels and posts along the street — approx., in the model (GBS_Gate_SlidingGate/Fence/GatePost)
- [ ] G.5 Yard inside the gate: clover pavers, drain gratings, benches, bins, bike racks, the 3 flagpoles, the decorative bicycle — approx., in the model (GBS_Gate_Bench/BikeRack/WheelieBin/Bed)
- [ ] G.6 Alley B–A: tree row, concrete-edged hedges, kerbs, red lawn edging, yellow-painted kerbs — approx., in the model (GBS_GateAlley Alley/Curb/Lawn/BBed/PathHedge)
- [ ] G.7 South wide stair from the gate down to the A corner — approx., in the model (GBS_GateAlley_SouthStair)
- [ ] G.8 North stair at the end of the lawn (with rails) — approx., in the model (GBS_GateAlley_Steps/StairCoping)
- [ ] G.9 Retaining wall with the granite parapet between the alley and the walkway along A — approx., in the model (GBS_GateAlley_RetWall/LawnCoping)
- [ ] G.10 Grating ramp at the side stair opposite the lettering — approx., in the model (GBS_GateAlley_Ramp/RampRail)
- [ ] G.11 A_S entrance pavilion (pitched roof, door, pilasters, steps) — approx., in the model (GBS_GateAlley_PavilionStair + GBF_BLD_A_S pavilion)
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
- [ ] S.1 Sidewalk: clover/hexagon pavers, kerbs, levels — approx., in the model (GBS_StreetFront_Sidewalk)
- [ ] S.2 Low parapet along the sidewalk with its steps; lawn level behind it — approx., in the model (GBS_StreetFront_Parapet/Hedge)
- [ ] S.3 Tree pits along the sidewalk — approx.: 11 pits + trees on the sidewalk along the parking side (SITE_StreetFront StreetPit/StreetTree), x from Bing crowns
- [ ] S.4 Parking by the sidewalk with yellow-black barrier pipes — approx., in the model (GBS_StreetFront_WheelStop)
- [ ] S.5 Zebra crossing, road kerbs, carriageway — approx., in the model (GBS_Gate_Zebra/Curb)
- [ ] S.6 Bus stop (find it) and trolleybus poles; ATM kiosk by the fence — approx.: trolleybus poles every 35 m on the north kerb (TrolleyPole_*); bus stop not found in any frame or on the satellite, not modelled; ATM kiosk only in 2019 web frames (older state), not modelled
- [ ] S.7 West end of the sidewalk (grey wall with the gas pipe) — approx.: grey wall at the W end of the sidewalk (SidewalkWestWall), gas pipe left to materials
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

- [ ] AW.10 Bench and conifer row along the N end of A_N (new, 081158036) — approx., SITE_CPlaza BenchAN/TreeAN/PlanterAN

## 15. Terrain and levels
- [ ] T.1 Terrace levels re-measured on the meshes (alley along B, walkway along A, garden/gazebos/C plaza, sports level) — approx., in the model (terrain_pads in the specs)
- [ ] T.2 Every outdoor stair and ramp between terraces counted and matched to T.1 — approx.: every stair/ramp in the specs with estimated riser counts (see M-table)
- [ ] T.3 Terrain pads and hard edges in the specs, no terrain poking through paving — approx., in the model (TER + pads)

## 16. Surroundings (500 m ring, handoff section 6; OSM © OpenStreetMap contributors, Art/Blender/Data/ctx_osm.json)
Each building: footprint from OSM, height from OSM `building:levels`/`height`, else floors counted in the owner's street videos / web photos / obliques (≈3.0 m per residential floor + ground floor + parapet); ready-made models (Fab, Poly Haven, BlenderKit free, Sketchfab CC0/CC-BY) scaled to the footprint, sources in docs/reference/asset_sources.md; collections `CTX_*`.

### Near buildings (≤150 m: facades, entrances, balconies, ground-floor shops from photos)
- [ ] CTX.Bway/169915330 yes, SE 2 m, 646 m², levels: count from photos
- [ ] CTX.Bway/206623867 yes, E 3 m, 1492 m², levels: count from photos
- [ ] CTX.Bway/206623848 yes, E 6 m, 452 m², levels: count from photos
- [ ] CTX.Bway/169915374 yes, E 7 m, 260 m², levels: count from photos
- [ ] CTX.Bway/761350988 yes, S 10 m, 24 m², levels: count from photos
- [ ] CTX.Bway/635535016 yes, NE 14 m, 755 m², levels: count from photos
- [ ] CTX.Bway/742042612 residential, NE 15 m, 685 m², 9.0 levels (OSM)
- [ ] CTX.Bway/761341971 yes, NW 16 m, 1109 m², levels: count from photos
- [ ] CTX.Bway/255081513 school, W 19 m, 1126 m², levels: count from photos
- [ ] CTX.Bway/206623794 yes, NE 20 m, 621 m², levels: count from photos
- [ ] CTX.Bway/761350987 yes, S 23 m, 14 m², levels: count from photos
- [ ] CTX.Bway/206623783 yes, N 26 m, 565 m², levels: count from photos
- [ ] CTX.Bway/761341970 yes «Технодом соода борбору», NW 26 m, 2262 m², levels: count from photos
- [ ] CTX.Bway/206614083 yes, W 30 m, 1558 m², levels: count from photos
- [ ] CTX.Bway/1529424567 yes, N 36 m, 3498 m², levels: count from photos
- [ ] CTX.Bway/761341972 yes, N 43 m, 530 m², levels: count from photos
- [ ] CTX.Bway/169828217 yes, SE 46 m, 331 m², levels: count from photos
- [ ] CTX.Bway/635535018 yes, NE 49 m, 971 m², levels: count from photos
- [ ] CTX.Bway/635535017 yes, E 70 m, 617 m², levels: count from photos
- [ ] CTX.Bway/129705598 yes, NW 72 m, 1985 m², levels: count from photos
- [ ] CTX.Bway/635535009 yes, NW 77 m, 879 m², levels: count from photos
- [ ] CTX.Bway/635535023 yes, NE 78 m, 440 m², levels: count from photos
- [ ] CTX.Bway/635535022 yes, NE 78 m, 441 m², levels: count from photos
- [ ] CTX.Bway/635535019 yes, NE 78 m, 440 m², levels: count from photos
- [ ] CTX.Bway/635535021 yes, NE 78 m, 440 m², levels: count from photos
- [ ] CTX.Bway/635535024 yes, NE 80 m, 441 m², levels: count from photos
- [ ] CTX.Bway/761345513 yes, NE 80 m, 1349 m², levels: count from photos
- [ ] CTX.Bway/632728361 yes, SE 82 m, 1128 m², 9.0 levels (OSM)
- [ ] CTX.Bway/341105719 yes «Аю Grand», N 86 m, 22747 m², levels: count from photos
- [ ] CTX.Bway/632728362 yes, S 91 m, 862 m², 9.0 levels (OSM)
- [ ] CTX.Bway/632728363 yes, S 91 m, 1004 m², 9.0 levels (OSM)
- [ ] CTX.Bway/169915344 yes, E 94 m, 5429 m², levels: count from photos
- [ ] CTX.Bway/206623827 yes, E 94 m, 911 m², levels: count from photos
- [ ] CTX.Bway/206623793 yes, E 95 m, 275 m², levels: count from photos
- [ ] CTX.Bway/169915381 yes, E 96 m, 1529 m², levels: count from photos
- [ ] CTX.Bway/335552917 house, SE 99 m, 93 m², 2.0 levels (OSM)
- [ ] CTX.Bway/206623816 yes, E 100 m, 383 m², levels: count from photos
- [ ] CTX.Bway/635535020 yes, NE 114 m, 440 m², levels: count from photos
- [ ] CTX.Bway/1555086426 yes, S 115 m, 237 m², levels: count from photos
- [ ] CTX.Bway/897518010 yes, SE 116 m, 217 m², levels: count from photos
- [ ] CTX.Bway/635535014 yes, NE 120 m, 440 m², levels: count from photos
- [ ] CTX.Bway/635535013 yes, NE 121 m, 440 m², levels: count from photos
- [ ] CTX.Bway/1529424569 roof, N 125 m, 322 m², levels: count from photos
- [ ] CTX.Bway/206623782 yes, NE 126 m, 430 m², levels: count from photos
- [ ] CTX.Bway/169916490 mosque, S 127 m, 1564 m², levels: count from photos
- [ ] CTX.Bway/206613116 yes, W 133 m, 1384 m², levels: count from photos
- [ ] CTX.Bway/168164292 yes, W 134 m, 905 m², levels: count from photos
- [ ] CTX.Bway/394617087 office «Центр обслуживания населения», NW 134 m, 1182 m², levels: count from photos
- [ ] CTX.Bway/168164264 yes, W 135 m, 721 m², levels: count from photos
- [ ] CTX.Bway/407836680 house, SE 136 m, 363 m², 3.0 levels (OSM)
- [ ] CTX.Bway/206613712 yes, W 136 m, 3713 m², levels: count from photos
- [ ] CTX.Bway/635535008 yes, NW 137 m, 1681 m², levels: count from photos
- [ ] CTX.Bway/169828200 house, SE 143 m, 90 m², levels: count from photos
- [ ] CTX.Bway/1529424629 yes, SW 143 m, 214 m², levels: count from photos
- [ ] CTX.Bway/877560915 yes, SE 143 m, 279 m², levels: count from photos

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
- 2026-09-27 P0 frame: per-component auto registration failed (walls vs specs, ground ortho vs Bing, outlines vs photos: the true C-entrance pose scores below wrong ones); up/scale per component are good (ground planes + eye 1.52 m, scale within 0.8 %%). Whole-site alignment ALL (38 exterior clips, every 2nd frame, all stills) queued first for one world frame; cp_fit.py ready for control points on what stays separate. route_profile tested on C_entr (4 events). pass_check.py written.
- 2026-09-27 (evening): C entrance re-expressed from the tower face: the mesh puts the tower wall 0.9 m in front of the storefront (landing 1.75, canopy 4.7, storefront recess 0.9); C.5/C.6 window fit by photo edges is unstable (periodic facade) -> waiting for the C_photos zone mesh; next object H.1-H.3 (C_sw c7: pavers 0.305 u, camera height 4.38 u -> ~0.33-0.37 m/unit, frame is -Y up).
- 2026-09-27: list built from ROUTE.md, campus.md, photo_requests.md, the handoff, the specs, the capture clips (incl. the 2026-09-25 batch: gate, A_W walkway, C west side, C basement) and the web-media triage (C:\koch\web\triage_part1.md, triage_part2.md). Best web sources for roofs and back sides: the 2023-01-28 drone flight, 2022-04-19, 2020-05-16 and 2022-10-30 aerials.
- 2026-09-27: queue extended with WEB_front (2026-05-22, 2023-03-20 clips), WEB_drone (2023-01-28, 640x352), C_F1, C_lab, C_wc (interior clips extracted + masked).
- 2026-09-27: GPU queue started with zones C_sw, AW, Gate, Sports, Garden, Street, C_base.
