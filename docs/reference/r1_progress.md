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
- [ ] C.3 Entrance canopy: slab, terracotta soffit panels, fascia/edge trims, sign box (blank KOCH panel), flood lamps
- [ ] C.4 Vestibule / storefront: glazed frame, doors with stiles and rails, pull bars, threshold, transom, side lights, fascia cladding
- [ ] C.5 South facade, centre + tower: plinth tile band, pilasters, window kit (frame, sashes, mullions, sills, surrounds), cornice
- [ ] C.6 South facade, west wing and east wing
- [ ] C.7 East facade + east exit (brown double door under the stair, outside step/porch)
- [ ] C.8 North facade (windows, doors, plinth)
- [ ] C.9 West facade
- [ ] C.10 Roof: hips, ridges, eaves, fascia, gutters with hangers, downpipes with elbows and shoes, snow guards
- [ ] C.11 Dormers: south 2+3, north 7, east 2, each with its own roof
- [ ] C.12 West basement entry "Dance Hall": sunken stair, wrought-iron guard, brick box, red mono-pitch canopy and its post
- [ ] C.13 West mono-pitch shed and its continuation toward the spruces SW of C
- [ ] C.14 Basement light wells: red corrugated sloped covers along the south and east walls, low parapet
- [ ] C.15 Wall fittings on C: AC units with brackets, CCTV, lamps, vents, sign plates
- [ ] C.16 Plaza south of C: paving levels and falls, kerbs, red-edged planters, tree pits, spruces, benches, bins, bike parking at the stair
- [ ] C.17 Ground drop plaza → basement-entry corner, kerb step to the granite pad at the brick wall

## 2. Block C, interior (zone `C_base`; F1–F5 zone to add: clips 070704360, 052716931, 080443026, 080011086, 080051708, 074805359, 075725091, 075928860, 075931189)
- [ ] CI.1 Entrance lobby F1: terrazzo floor, blue accent panels, vending/coffee niche, radiators, ceiling grid with LED panels
- [ ] CI.2 F1 corridors west/east: benches, classroom doors (0.99 × 2.05 kit), fire-alarm boxes
- [ ] CI.3 West stair F1–F3: flights, landings, window, white steel balustrade
- [ ] CI.4 East stair F1–F5: flights, landings, windows, balustrade (riser count per flight)
- [ ] CI.5 WC pair F1: sinks, stalls with black doors, squat pans, high cisterns, tile to 1.4 m
- [ ] CI.6 Prototype classroom 203 (computer lab): desks, chairs, TV, whiteboard, grid ceiling, windows with blinds
- [ ] CI.7 Floors F2–F4: corridors, classrooms, WCs (F4 without the west stair: offices)
- [ ] CI.8 F5 attic offices under the roof, lit by the dormers
- [ ] CI.9 Basement: stair down with wrought-iron balustrade, vaulted corridor, barred windows, art room, piano room

## 3. A_W gallery and its plaza (zone `AW`)
- [ ] AW.1 Gallery deck: tiled deck above the walkway, granite edge, the single step between the 1st and 2nd post from the north
- [ ] AW.2 Gallery posts (bases, caps), beams, soffit panels, edge trims, the gallery roof
- [ ] AW.3 North-end steps + grey ramp on the wall side
- [ ] AW.4 Middle stair + steel ramp with rails (alley → gallery)
- [ ] AW.5 North stair from the alley to the plaza (end of the lawn)
- [ ] AW.6 A_W west facade under the gallery: doors ("Dining Hall" double door, single door at the A_S pilaster), windows, pilasters, AC units
- [ ] AW.7 A_W north end wall
- [ ] AW.8 Basement descent at the gallery (stone steps + steel stair)
- [ ] AW.9 Plaza between the gallery and C: paving levels, kerbs, planters, signboard, wayfinding sign, bins

## 4. B–A alley and the main gate (zone `Gate`)
- [ ] G.1 Checkpoint booth: tile walls, brick plinth, doors, windows, roof
- [ ] G.2 Gate canopy on its round column: roof pitch, ends, timber soffit, fascia panel (blank KOCH)
- [ ] G.3 Turnstiles and the pass-through railings
- [ ] G.4 Sliding gate leaves, fence panels and posts along the street
- [ ] G.5 Yard inside the gate: clover pavers, drain gratings, benches, bins, bike racks, the 3 flagpoles, the decorative bicycle
- [ ] G.6 Alley B–A: tree row, concrete-edged hedges, kerbs, red lawn edging, yellow-painted kerbs
- [ ] G.7 South wide stair from the gate down to the A corner
- [ ] G.8 North stair at the end of the lawn (with rails)
- [ ] G.9 Retaining wall with the granite parapet between the alley and the walkway along A
- [ ] G.10 Grating ramp at the side stair opposite the lettering
- [ ] G.11 A_S entrance pavilion (pitched roof, door, pilasters, steps)
- [ ] G.12 Pad at the foot of the south stair (A_S corner, drain grating)
- [ ] G.13 Slope between the fence walkway (east of the booth) and A's south facade

## 5. Hall–C passage and the sports hall's east end (zone `Sports`, west part in `C_sw`)
- [ ] H.1 Passage stair with the granite cheek
- [ ] H.2 Grey ramp on the stair's west side
- [ ] H.3 Low railing with dense bars
- [ ] H.4 Sports hall east end wall with the door and canopy by the ramp, its steps
- [ ] H.5 Sports hall 2-storey wing at the NE corner
- [ ] H.6 Path along the sports hall from the garden to C's west side (benches, plinth, trees)

## 6. Garden (zone `Garden`)
- [ ] GD.1 West gazebo: posts, brick parapet, openings, roof and finial
- [ ] GD.2 East gazebo
- [ ] GD.3 Hedge maze: hedge blocks and paths
- [ ] GD.4 Hedge arches
- [ ] GD.5 South pergola alley: arches, radial paths, the red wall with a stair at its end
- [ ] GD.6 Retaining walls (rubble stone) and steps between B's side and the garden
- [ ] GD.7 East edge toward the alley: retaining wall, hedge, lamps
- [ ] GD.8 Garden furniture: wrought-iron benches with slats, bins, lamp posts
- [ ] GD.9 Ground: diamond tiles, scalloped concrete edging, levels
- [ ] GD.10 Small red-brick hut with a pitched roof by the garden alley; timber gazebo (second type, check location)

## 7. Sports fields (zone `Sports`)
- [ ] F.1 Football pitch: turf slab, red plinth, red rubber border, levels
- [ ] F.2 Pitch fence: posts, mesh panels, X-braced ball-stop sections, gates
- [ ] F.3 Floodlight masts with ladders and heads
- [ ] F.4 Courts (basketball, volleyball, hard court): slabs, fences between, hoops, net posts
- [ ] F.5 Decorated alley along the pitch: planters, thujas, double-ball lamps, garlands
- [ ] F.6 Flowerbed plaza slope from the path end to the pitch
- [ ] F.7 Benches and spectator tiers by the pitch
- [ ] F.8 Red square pad west of the pitch
- [ ] F.9 North boundary fence with brick piers
- [ ] F.10 Thujas along the south court fence
- [ ] F.11 Low timber stage deck at the plaza edge by the courts; round flower bed with a lamp (check both still exist)
- [ ] F.12 Outdoor stair behind a goal (red risers, white treads) to the next terrace

## 8. Sports hall (zones `Sports`, `Garden`)
- [ ] SH.1 South facade under the gallery: wall, doors, windows
- [ ] SH.2 Gallery: red posts, beams, deck, eaves
- [ ] SH.3 West end, north side
- [ ] SH.4 Roof: pitch, ridge, eaves, gutters

## 9. Canteen and small buildings north of C (zone `Sports`)
- [ ] K.1 Canteen: all four facades, west entrance (glass vestibule, overhang on a red post, steps, ramp), roof
- [ ] K.2 Small pavilion
- [ ] K.3 One-storey building with a deep timber overhang on a red post (070410255 39–41 s): identify and model

## 10. Block B (zones `Gate`, `AW`)
- [ ] B.1 South (street) facade: bays between pilasters, windows, lettering band (blank KOCH)
- [ ] B.2 North (garden) facade
- [ ] B.3 West end
- [ ] B.4 East facade: entrance canopy, door and threshold, maroon sloped covers
- [ ] B.5 Low red-roofed annex at the NE corner
- [ ] B.6 Roof: slopes, hatch on the north slope
- [ ] B.7 Front gallery on brick piers with terracotta soffit, white low railing and planters along the front path
- [ ] B.8 Position: B–A gap settled on the mesh

## 11. Block A (zones `AW`, `Gate`)
- [ ] A.1 Main facade on the square: lettering band + round panel (blank KOCH), pilasters, windows, notice-board stands
- [ ] A.2 A_S south facade (street)
- [ ] A.3 A_S and A_N east facades (parking side)
- [ ] A.4 A_N north end (cut gable)
- [ ] A.5 A_E and the NE annex between A_N and A_S
- [ ] A.6 Two-storey part (hall + library) and the roof junctions
- [ ] A.7 Roofs of A
- [ ] A.8 Junction A_S / gallery block
- [ ] A.9 Circle-pattern paving, red-tile retaining wall with steps and planting in front of the entrance pavilion

## 12. Street front (zone `Street`)
- [ ] S.1 Sidewalk: clover/hexagon pavers, kerbs, levels
- [ ] S.2 Low parapet along the sidewalk with its steps; lawn level behind it
- [ ] S.3 Tree pits along the sidewalk
- [ ] S.4 Parking by the sidewalk with yellow-black barrier pipes
- [ ] S.5 Zebra crossing, road kerbs, carriageway
- [ ] S.6 Bus stop (find it) and trolleybus poles; ATM kiosk by the fence
- [ ] S.7 West end of the sidewalk (grey wall with the gas pipe)
- [ ] S.8 Outside parking by the gate; residential towers as far massing

## 13. West campus and others (web media, satellite; zone to add from the web frames)
- [ ] W.1 Block D: massing, floors, entrance canopies, rooftop penthouse, roofs
- [ ] W.2 Block D frontage: ornate fence with stone-clad pillars and gate, second street gate with its booth and sliding gate, forecourt pavilions, blue-glass atrium
- [ ] W.3 Block E (behind the sports hall): facades, outdoor fire stair, grey annex
- [ ] W.4 Complex south of D: decide whether it is campus; massing if yes
- [ ] W.5 Picnic-shelter row by the west 4-storey block
- [ ] W.6 Parking with garage sheds at the end of the long path; the container in the service alley
- [ ] W.7 Unidentified volumes to place or drop: pale building with a red roof and a steel fire escape, barrel-vault roof building, dark-clad tall wall, pink block with a glass entrance

## 14. Kits used everywhere
- [ ] KIT.1 Lamps: single/double globe lanterns, curly-bracket wall lanterns, curved-arm street lamps, ball lamps
- [ ] KIT.2 Benches and bins: wrought-iron benches with slats, wrought-iron litter bins, wheelie and recycling bins
- [ ] KIT.3 Notice boards, info/map boards, wayfinding signs (blank KOCH faces)

## 15. Terrain and levels
- [ ] T.1 Terrace levels re-measured on the meshes (alley along B, walkway along A, garden/gazebos/C plaza, sports level)
- [ ] T.2 Every outdoor stair and ramp between terraces counted and matched to T.1
- [ ] T.3 Terrain pads and hard edges in the specs, no terrain poking through paving

## Log
- 2026-09-27: list built from ROUTE.md, campus.md, photo_requests.md, the handoff, the specs, the capture clips (incl. the 2026-09-25 batch: gate, A_W walkway, C west side, C basement) and the web-media triage (C:\koch\web\triage_part1.md, triage_part2.md). Best web sources for roofs and back sides: the 2023-01-28 drone flight, 2022-04-19, 2020-05-16 and 2022-10-30 aerials.
- 2026-09-27: GPU queue started with zones C_sw, AW, Gate, Sports, Garden, Street, C_base.
