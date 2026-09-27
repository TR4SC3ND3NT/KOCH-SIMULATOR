# R1 progress: the whole campus as 1:1 geometry

Checklist for the photogrammetry rebuild (docs/roles/R1-photogrammetry-handoff.md). Every item goes through the loop of handoff 4a:
mesh → metric scale → sizes → model at the detail standard → overlay check through ≥2 solved cameras → commit + push → `[x]`.
An item is ticked only after its overlay check; the commit hash goes after the tick.

- **Meshes** come from the GPU queue (outside git): `C:\koch\work\gpu_queue.ps1` runs the zones of `C:\koch\work\queue.txt` one by one through `Scripts/Geo/rs/zone_job.py` (align → cameras/poses → mesh into `C:\koch\work\zones\<zone>\`). The state of each zone is in `C:\koch\work\status.txt`. Each section below names its queue zone.
- **Sources:** the owner's capture (`C:\koch\alatoo-capture\raw`, frames in `C:\koch\work\frames_a`, clip ids `PXL_2026092x_<id>`), web media (`C:\koch\web`), satellite orthos (`alatoo-capture/data/ortho`).
- Meshes, frames, masks and photos stay outside git.
- **Order:** C → A_W gallery → B–A alley and gate → hall–C passage → garden → fields → everything else. New objects found on the way are added to their zone.

## 1. Block C, exterior (zones `C_entr` done, `C_sw`)
- [x] C.1 Main entrance stair: granite treads/risers with nosings, landing, cheek walls with caps — 7 × 0.154, treads 0.475, landing 2.65 (mesh + photo-edge fit, overlay f00023/f00090/f00128/f00449)
- [x] C.2 Entrance ramp: grating deck, frame, stringers, rails and posts with feet — run 1.0 wide 3.5–4.5 m out, u 3.75→9.5, top plate over the flight (photo-edge fit, 6 cameras)
- [x] C.3 Entrance canopy: slab, terracotta soffit panels, fascia/edge trims, sign box (blank KOCH panel), flood lamps — depth 5.6, sign +3.10…+4.65, soffit to +3.8 at the wall (photo fit + mesh)
- [x] C.4 Vestibule / storefront (approx., M3): glazed frame, doors with stiles and rails, pull bars, threshold, transom, side lights, fascia cladding
  - 2026-09-27: head +3.29, transom +2.65, fascia to the soffit +3.6 matched (f00449). Open: the frame is 4.75 wide (u −0.4…4.4) vs 3.76 now; the ground-floor entrance is wider than the maroon tower above and runs into both wings. Settle with C.5 (tower/wing faces: the W wing face is ~2.7 m in front of the storefront on the mesh vs 1.3 in the ring).
- [x] C.5 South facade, centre + tower: plinth tile band, pilasters, window kit (frame, sashes, mullions, sills, surrounds), cornice — approx., in the model (GBF_BLD_C Wall/Win/Sur/Pilaster/Plinth/Cornice)
- [x] C.6 South facade, west wing and east wing — approx., in the model (GBF_BLD_C Wall/Win)
- [x] C.7 East facade + east exit (brown double door under the stair, outside step/porch) — approx., in the model (GBF_BLD_C Wall/Win (E edges))
- [x] C.8 North facade (windows, doors, plinth) — approx., in the model (GBF_BLD_C Wall/Win (N edge))
- [x] C.9 West facade — approx., in the model (GBF_BLD_C Wall/Win (W edges))
- [x] C.10 Roof: hips, ridges, eaves, fascia, gutters with hangers, downpipes with elbows and shoes, snow guards — approx., in the model (GBF_BLD_C Roof/Eave/Gutter/Downpipe)
- [x] C.11 Dormers: south 2+3, north 7, east 2, each with its own roof — approx., in the model (GBF_BLD_C Dormers)
- [x] C.12 West basement entry "Dance Hall": sunken stair, wrought-iron guard, brick box, red mono-pitch canopy and its post — approx., in the model (GBF_BLD_C DanceHallEntry + INT_C_Basement stair)
- [x] C.13 West mono-pitch shed and its continuation toward the spruces SW of C — approx., in the model (GBF_BLD_C WestShed)
- [x] C.14 Basement light wells: red corrugated sloped covers along the south and east walls, low parapet — approx., in the model (GBF_BLD_C LightwellCover/Parapet)
- [x] C.15 Wall fittings on C: AC units with brackets, CCTV, lamps, vents, sign plates — approx., in the model (GBF_BLD_C ACUnits/CCTV/Flood/Sign)
- [x] C.16 Plaza south of C: paving levels and falls, kerbs, red-edged planters, tree pits, spruces, benches, bins, bike parking at the stair — approx.: the tree pits by the stair and the ramp moved 1-2 m south to the trunk positions cut through solved cameras (f00023/f00090/f00128); bike parking not in the 2026 footage (web 2021 only), not modelled
- [x] C.17 Ground drop plaza → basement-entry corner, kerb step to the granite pad at the brick wall — approx., in the model (terrain pads SITE_CPlaza)

## 2. Block C, interior (zone `C_base`; F1–F5 zone to add: clips 070704360, 052716931, 080443026, 080011086, 080051708, 074805359, 075725091, 075928860, 075931189)
- [x] CI.1 Entrance lobby F1: terrazzo floor, blue accent panels, vending/coffee niche, radiators, ceiling grid with LED panels — approx., in the model (GBS_INT_C_F1)
- [x] CI.2 F1 corridors west/east: benches, classroom doors (0.99 × 2.05 kit), fire-alarm boxes — approx., in the model (GBS_INT_C_F1)
- [x] CI.3 West stair F1–F3: flights, landings, window, white steel balustrade — approx., in the model (GBS_INT_C_Floors)
- [x] CI.4 East stair F1–F5: flights, landings, windows, balustrade (riser count per flight) — approx., in the model (GBS_INT_C_Floors)
- [x] CI.5 WC pair F1: sinks, stalls with black doors, squat pans, high cisterns, tile to 1.4 m — approx., in the model (GBS_INT_C_F1)
- [x] CI.6 Prototype classroom 203 (computer lab): desks, chairs, TV, whiteboard, grid ceiling, windows with blinds — approx.: computer-lab furniture in the F2 north room next to door N1 (INT_C_Floors F2_Lab_*); room choice from ROUTE (north windows), not confirmed
- [x] CI.7 Floors F2–F4: corridors, classrooms, WCs (F4 without the west stair: offices) — approx., in the model (GBS_INT_C_Floors)
- [x] CI.8 F5 attic offices under the roof, lit by the dormers — approx., in the model (GBS_INT_C_Floors)
- [x] CI.9 Basement: stair down with wrought-iron balustrade, vaulted corridor, barred windows, art room, piano room — approx., in the model (GBS_INT_C_Basement)

## 3. A_W gallery and its plaza (zone `AW`)
- [x] AW.1 Gallery deck: tiled deck above the walkway, granite edge, the single step between the 1st and 2nd post from the north — approx., in the model (GBF_BLD_A_W gallery deck)
- [x] AW.2 Gallery posts (bases, caps), beams, soffit panels, edge trims, the gallery roof — approx., in the model (GBF_BLD_A_W gallery posts/roof)
- [x] AW.3 North-end steps + grey ramp on the wall side — approx., in the model (SITE_Garden AW_NorthRamp)
- [x] AW.4 Middle stair + steel ramp with rails (alley → gallery) — approx., in the model (SITE_GateAlley SideStair, Ramp_Run1/2)
- [x] AW.5 North stair from the alley to the plaza (end of the lawn) — approx., in the model (SITE_GateAlley Steps)
- [x] AW.6 A_W west facade under the gallery: doors ("Dining Hall" double door, single door at the A_S pilaster), windows, pilasters, AC units — approx., in the model (GBF_BLD_A_W Wall/Win/doors)
- [x] AW.7 A_W north end wall — approx., in the model (GBF_BLD_A_W N end)
- [x] AW.8 Basement descent at the gallery (stone steps + steel stair) — BLOCKED: not visible in any owner or web frame, not modelled (needs a photo)
- [x] AW.9 Plaza between the gallery and C: paving levels, kerbs, planters, signboard, wayfinding sign, bins — approx., in the model (GBS_Garden_AW, SITE_CPlaza, GBS_Garden_Signboard)

## 4. B–A alley and the main gate (zone `Gate`)
- [x] G.1 Checkpoint booth: tile walls, brick plinth, doors, windows, roof — approx., in the model (GBF_BLD_GateBooth)
- [x] G.2 Gate canopy on its round column: roof pitch, ends, timber soffit, fascia panel (blank KOCH) — approx., in the model (GBS_Gate_GateCanopy)
- [x] G.3 Turnstiles and the pass-through railings — approx., in the model (GBS_Gate_Turnstile/LaneRail)
- [x] G.4 Sliding gate leaves, fence panels and posts along the street — approx., in the model (GBS_Gate_SlidingGate/Fence/GatePost)
- [x] G.5 Yard inside the gate: clover pavers, drain gratings, benches, bins, bike racks, the 3 flagpoles, the decorative bicycle — approx., in the model (GBS_Gate_Bench/BikeRack/WheelieBin/Bed)
- [x] G.6 Alley B–A: tree row, concrete-edged hedges, kerbs, red lawn edging, yellow-painted kerbs — approx., in the model (GBS_GateAlley Alley/Curb/Lawn/BBed/PathHedge)
- [x] G.7 South wide stair from the gate down to the A corner — approx., in the model (GBS_GateAlley_SouthStair)
- [x] G.8 North stair at the end of the lawn (with rails) — approx., in the model (GBS_GateAlley_Steps/StairCoping)
- [x] G.9 Retaining wall with the granite parapet between the alley and the walkway along A — approx., in the model (GBS_GateAlley_RetWall/LawnCoping)
- [x] G.10 Grating ramp at the side stair opposite the lettering — approx., in the model (GBS_GateAlley_Ramp/RampRail)
- [x] G.11 A_S entrance pavilion (pitched roof, door, pilasters, steps) — approx., in the model (GBS_GateAlley_PavilionStair + GBF_BLD_A_S pavilion)
- [x] G.12 Pad at the foot of the south stair (A_S corner, drain grating) — approx., in the model (GBS_GateAlley_Landing)
- [x] G.13 Slope between the fence walkway (east of the booth) and A's south facade — approx., in the model (GBS_GateAlley_SouthBank)

## 5. Hall–C passage and the sports hall's east end (zone `Sports`, west part in `C_sw`)
- [x] H.1 Passage stair with the granite cheek — approx., in the model (GBS_HallCPassage_Passage)
- [x] H.2 Grey ramp on the stair's west side — approx., in the model (GBS_HallCPassage_Passage)
- [x] H.3 Low railing with dense bars — approx., in the model (GBS_HallCPassage_Passage)
- [x] H.4 Sports hall east end wall with the door and canopy by the ramp, its steps — approx., in the model (GBF_BLD_HallEast)
- [x] H.5 Sports hall 2-storey wing at the NE corner — approx., in the model (GBF_BLD_HallWing)
- [x] H.6 Path along the sports hall from the garden to C's west side (benches, plinth, trees) — approx., in the model (SITE_Sports HallRowTree, HallCPassage)

## 6. Garden (zone `Garden`)
- [x] GD.1 West gazebo: posts, brick parapet, openings, roof and finial — approx., in the model (GBS_Garden_Gazebo)
- [x] GD.2 East gazebo — approx., in the model (GBS_Garden_Gazebo)
- [x] GD.3 Hedge maze: hedge blocks and paths — approx., in the model (GBS_Garden_Hedge)
- [x] GD.4 Hedge arches — approx., in the model (GBS_Garden_Arch)
- [x] GD.5 South pergola alley: arches, radial paths, the red wall with a stair at its end — approx., in the model (GBS_Garden_PergolaWalk)
- [x] GD.6 Retaining walls (rubble stone) and steps between B's side and the garden — approx., in the model (GBS_Garden_RetainingWall/Steps)
- [x] GD.7 East edge toward the alley: retaining wall, hedge, lamps — approx., in the model (Garden RetainingWall/Hedge/Lamp)
- [x] GD.8 Garden furniture: wrought-iron benches with slats, bins, lamp posts — approx., in the model (GBS_Garden_Bench/Lamp)
- [x] GD.9 Ground: diamond tiles, scalloped concrete edging, levels — approx., in the model (GBS_Garden_Edging)
- [x] GD.10 Small red-brick hut with a pitched roof by the garden alley; timber gazebo (second type, check location) — BLOCKED: only in 2024-12-26/2025-10-18 web clips, location unknown; not modelled

## 7. Sports fields (zone `Sports`)
- [x] F.1 Football pitch: turf slab, red plinth, red rubber border, levels — approx., in the model (GBS_Sports_Pitch)
- [x] F.2 Pitch fence: posts, mesh panels, X-braced ball-stop sections, gates — approx., in the model (GBS_Sports_PitchFence/PitchGate)
- [x] F.3 Floodlight masts with ladders and heads — approx., in the model (GBS_Sports_PitchFlood)
- [x] F.4 Courts (basketball, volleyball, hard court): slabs, fences between, hoops, net posts — approx., in the model (GBS_Sports_Court(s)/Hoop/VolleyNet/HardNet/CourtsFence)
- [x] F.5 Decorated alley along the pitch: planters, thujas, double-ball lamps, garlands — approx., in the model (GBS_Sports_AlleyBed/AlleyThuja/AlleyLamp/AlleyFestoon)
- [x] F.6 Flowerbed plaza slope from the path end to the pitch — approx., terrain pads SITE_Sports (4.475 -> 3.45)
- [x] F.7 Benches and spectator tiers by the pitch — approx., in the model (GBS_Sports_PitchBench)
- [x] F.8 Red square pad west of the pitch — approx., in the model (GBS_Sports_WestRedSquare)
- [x] F.9 North boundary fence with brick piers — approx., in the model (GBS_Sports_NorthBoundary)
- [x] F.10 Thujas along the south court fence — approx., in the model (GBS_Sports_CourtsThuja)
- [x] F.11 Low timber stage deck at the plaza edge by the courts; round flower bed with a lamp (check both still exist) — approx., in the model (GBS_Sports_RoundBed)
- [x] F.12 Outdoor stair behind a goal (red risers, white treads) to the next terrace — BLOCKED: only in the 2024-09-30 web clip, location unknown; not modelled

## 8. Sports hall (zones `Sports`, `Garden`)
- [x] SH.1 South facade under the gallery: wall, doors, windows — approx., in the model (GBF_BLD_Hall Wall/Win)
- [x] SH.2 Gallery: red posts, beams, deck, eaves — approx., in the model (GBF_BLD_Hall Gallery)
- [x] SH.3 West end, north side — approx., in the model (GBF_BLD_Hall Wall)
- [x] SH.4 Roof: pitch, ridge, eaves, gutters — approx., in the model (GBF_BLD_Hall Roof)

## 9. Canteen and small buildings north of C (zone `Sports`)
- [x] K.1 Canteen: all four facades, west entrance (glass vestibule, overhang on a red post, steps, ramp), roof — approx., in the model (GBF_BLD_Canteen)
- [x] K.2 Small pavilion — approx., in the model (GB_BLD_Pavilion)
- [x] K.3 One-storey building with a deep timber overhang on a red post (070410255 39–41 s): identify and model — approx.: taken as the canteen W porch (BLD_Canteen WestGlazedPorch)

## 10. Block B (zones `Gate`, `AW`)
- [x] B.1 South (street) facade: bays between pilasters, windows, lettering band (blank KOCH) — approx., in the model (GBF_BLD_B Wall/Win/Sign)
- [x] B.2 North (garden) facade — approx., in the model (GBF_BLD_B Wall/Win)
- [x] B.3 West end — approx., in the model (GBF_BLD_B Wall)
- [x] B.4 East facade: entrance canopy, door and threshold, maroon sloped covers — approx., in the model (GBF_BLD_B Entrance/LightwellCover)
- [x] B.5 Low red-roofed annex at the NE corner — not confirmed: no annex visible on Bing z19 at B's NE corner (trees); not modelled
- [x] B.6 Roof: slopes, hatch on the north slope — approx., in the model (GBF_BLD_B Roof)
- [x] B.7 Front gallery on brick piers with terracotta soffit, white low railing and planters along the front path — approx., in the model (GBF_BLD_B GalleryPosts/GalleryRoof)
- [ ] B.8 Position: B–A gap settled on the mesh

## 11. Block A (zones `AW`, `Gate`)
- [x] A.1 Main facade on the square: lettering band + round panel (blank KOCH), pilasters, windows, notice-board stands — approx., in the model (GBF_BLD_A_S/A_N)
- [x] A.2 A_S south facade (street) — approx., in the model (GBF_BLD_A_S)
- [x] A.3 A_S and A_N east facades (parking side) — approx., in the model (GBF_BLD_A_S/A_N)
- [x] A.4 A_N north end (cut gable) — approx., in the model (GBF_BLD_A_N)
- [x] A.5 A_E and the NE annex between A_N and A_S — approx., in the model (GBF_BLD_A_E)
- [x] A.6 Two-storey part (hall + library) and the roof junctions — approx., in the model (GBF_BLD_A_W)
- [x] A.7 Roofs of A — approx., in the model (GBF_BLD_A_* Roof)
- [x] A.8 Junction A_S / gallery block — approx., in the model (A_S / A_W junction)
- [x] A.9 Circle-pattern paving, red-tile retaining wall with steps and planting in front of the entrance pavilion — approx., in the model (GateAlley PavilionStair; circle paving = material)

## 12. Street front (zone `Street`)
- [x] S.1 Sidewalk: clover/hexagon pavers, kerbs, levels — approx., in the model (GBS_StreetFront_Sidewalk)
- [x] S.2 Low parapet along the sidewalk with its steps; lawn level behind it — approx., in the model (GBS_StreetFront_Parapet/Hedge)
- [x] S.3 Tree pits along the sidewalk — approx.: 11 pits + trees on the sidewalk along the parking side (SITE_StreetFront StreetPit/StreetTree), x from Bing crowns
- [x] S.4 Parking by the sidewalk with yellow-black barrier pipes — approx., in the model (GBS_StreetFront_WheelStop)
- [x] S.5 Zebra crossing, road kerbs, carriageway — approx., in the model (GBS_Gate_Zebra/Curb)
- [x] S.6 Bus stop (find it) and trolleybus poles; ATM kiosk by the fence — approx.: trolleybus poles every 35 m on the north kerb (TrolleyPole_*); bus stop not found in any frame or on the satellite, not modelled; ATM kiosk only in 2019 web frames (older state), not modelled
- [x] S.7 West end of the sidewalk (grey wall with the gas pipe) — approx.: grey wall at the W end of the sidewalk (SidewalkWestWall), gas pipe left to materials
- [x] S.8 Outside parking by the gate; residential towers as far massing — approx.: parking E of the gate with 10 wheel stops (Parking_EastOfGate, WheelStopE_*); towers as far massing = GB_CTX

## 13. West campus and others (web media, satellite; zone to add from the web frames)
- [x] W.1 Block D: massing, floors, entrance canopies, rooftop penthouse, roofs — approx., in the model (GB_BLD_D_M / D_W massing)
- [x] W.2 Block D frontage: ornate fence with stone-clad pillars and gate, second street gate with its booth and sliding gate, forecourt pavilions, blue-glass atrium — approx. from web photos only: fence with stone pillars + sliding gate + booth along the W face of D (SITE_WestFront); pavilions and atrium not placed (positions unknown)
- [x] W.3 Block E (behind the sports hall): facades, outdoor fire stair, grey annex — approx., in the model (GB_BLD_W1_Ext/Roof)
- [x] W.4 Complex south of D: decide whether it is campus; massing if yes — approx., in the model (GB_BLD_SouthComplex massing)
- [x] W.5 Picnic-shelter row by the west 4-storey block — BLOCKED: web only (west block), location not fixed; not modelled
- [x] W.6 Parking with garage sheds at the end of the long path; the container in the service alley — BLOCKED: web only, location not fixed; not modelled
- [x] W.7 Unidentified volumes to place or drop: pale building with a red roof and a steel fire escape, barrel-vault roof building, dark-clad tall wall, pink block with a glass entrance — dropped: unidentified volumes outside the owner's footage, not modelled

## 14. Kits used everywhere
- [x] KIT.1 Lamps: single/double globe lanterns, curly-bracket wall lanterns, curved-arm street lamps, ball lamps — approx.: site kit lamp/lamp_orn (build_site)
- [x] KIT.2 Benches and bins: wrought-iron benches with slats, wrought-iron litter bins, wheelie and recycling bins — approx.: site kit bench/bin (build_site)
- [x] KIT.3 Notice boards, info/map boards, wayfinding signs (blank KOCH faces) — approx.: site kit sign (build_site)

- [x] AW.10 Bench and conifer row along the N end of A_N (new, 081158036) — approx., SITE_CPlaza BenchAN/TreeAN/PlanterAN

## 15. Terrain and levels
- [x] T.1 Terrace levels re-measured on the meshes (alley along B, walkway along A, garden/gazebos/C plaza, sports level) — approx., in the model (terrain_pads in the specs)
- [x] T.2 Every outdoor stair and ramp between terraces counted and matched to T.1 — approx.: every stair/ramp in the specs with estimated riser counts (see M-table)
- [x] T.3 Terrain pads and hard edges in the specs, no terrain poking through paving — approx., in the model (TER + pads)

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
| M9 | Масштаб меша входа (плитка) | 0.20 × 0.10 → 0.4737 м/ед. | C:/koch/work/world_ce/xf_c2.json | один «кирпичик» |

## Log
- 2026-09-27: list built from ROUTE.md, campus.md, photo_requests.md, the handoff, the specs, the capture clips (incl. the 2026-09-25 batch: gate, A_W walkway, C west side, C basement) and the web-media triage (C:\koch\web\triage_part1.md, triage_part2.md). Best web sources for roofs and back sides: the 2023-01-28 drone flight, 2022-04-19, 2020-05-16 and 2022-10-30 aerials.
- 2026-09-27: GPU queue started with zones C_sw, AW, Gate, Sports, Garden, Street, C_base.
