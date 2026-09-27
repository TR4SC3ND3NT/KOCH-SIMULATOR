# R1 progress: the whole campus as 1:1 geometry

Checklist for the photogrammetry rebuild (docs/roles/R1-photogrammetry-handoff.md). Every item goes through the loop of handoff 4a:
mesh → metric scale → sizes → model at the detail standard → overlay check through ≥2 solved cameras → commit + push → `[x]`.
An item is ticked only after its overlay check; the commit hash goes after the tick.

- Sources: the owner's capture (`C:\koch\raw`, frames `C:\koch\work\frames_a`, clip ids below are `PXL_2026092x_<id>`), web media (`C:\koch\web`, triage in `triage_part*.md`), satellite orthos (`alatoo-capture/data/ortho`).
- Meshes, frames, masks and photos stay outside git (`C:\koch\work`).
- Order: C → A_W gallery → B–A alley and gate → hall–C passage → garden → fields → everything else.
- New objects found on the way are added to their zone.

## 1. Block C, exterior (mesh: rs_zCS2 component 2 = clips 070647586 + 081158036; plaza: 061707849, photos 0924_0614xx)
- [ ] C.1 Main entrance stair: granite treads/risers with nosings, landing, cheek walls with caps (7 risers × ~0.15)
- [ ] C.2 Entrance ramp: deck, stringers, kerb, rails and posts with feet
- [ ] C.3 Entrance handrails and balustrades (stair + landing): posts, rails, bars, end curls, wall brackets
- [ ] C.4 Entrance canopy: slab, terracotta soffit, fascia/edge trims, supports, rainwater
- [ ] C.5 Vestibule / storefront: glazed frame, double doors with stiles and rails, pull bars, threshold, transom, side lights
- [ ] C.6 South facade, centre + tower: plinth tile band, pilasters, window kit (frame, sashes, mullions, sills, surrounds), cornice
- [ ] C.7 South facade, west wing and east wing (12.8 wall to wall)
- [ ] C.8 East facade + east exit (brown double door under the stair, outside step/porch)
- [ ] C.9 North facade (windows, doors, plinth)
- [ ] C.10 West facade
- [ ] C.11 Roof: hips, ridges, eaves, fascia, gutters with hangers, downpipes with elbows and shoes, snow guards
- [ ] C.12 Dormers: south 2+3, north 7, east 2, each with its own roof
- [ ] C.13 West basement entry "Dance Hall": sunken stair 8+2 risers, wrought-iron guard, brick box, red mono-pitch canopy and its post
- [ ] C.14 West mono-pitch shed (high at C, sloping toward the sports hall) and its continuation toward the spruces SW of C
- [ ] C.15 Basement light wells / red sloped covers along the walls
- [ ] C.16 Wall fittings on C: AC units with brackets, CCTV, lamps, vents, the blank KOCH sign panel
- [ ] C.17 Plaza south of C: paving levels, kerbs, red-edged planters, tree pits, spruces and trees (trunks as proxies), benches, bins
- [ ] C.18 Ground drop plaza → basement-entry corner (~0.7 m), kerb step to the granite pad at the brick wall

## 2. Block C, interior (clips 070704360, 052716931, 080443026, 080011086, 080051708, 074805359, 075725091, 075928860, 075931189; photos 0924_0811xx, 0924_0526xx, 080420598)
- [ ] CI.1 Entrance lobby F1: terrazzo floor, blue accent panels, vending/coffee niche, radiators, ceiling grid with LED panels
- [ ] CI.2 F1 corridors west/east with benches, doors (0.99 × 2.05 kit), fire-alarm boxes
- [ ] CI.3 West stair F1–F3: flights, landings, window, white steel balustrade
- [ ] CI.4 East stair F1–F5: flights, landings, windows, balustrade (settle 11+11 vs 12+10 risers, landing +1.80)
- [ ] CI.5 WC pair F1 (sinks, stalls with black doors, squat pans, high cisterns, tile to 1.4 m)
- [ ] CI.6 Prototype classroom 203 (computer lab): desks, chairs, TV, whiteboard, grid ceiling, windows with blinds
- [ ] CI.7 Floors F2–F4: corridors, classrooms, WCs (F4 without the west stair: offices)
- [ ] CI.8 F5 attic offices under the roof, lit by the dormers
- [ ] CI.9 Basement: stair down, corridor with barred window, piano room

## 3. A_W gallery and its plaza (mesh: rs_zC component 22 = c22_ds2.obj, 339 cams)
- [ ] AW.1 Gallery deck: tiled deck ~0.30 above the walkway, granite edge, single step between the 1st and 2nd post from the north
- [ ] AW.2 Gallery posts (bases, caps), beams, soffit panels, edge trims, roof over the gallery
- [ ] AW.3 North-end steps + grey ramp on the wall side
- [ ] AW.4 Middle stair + steel ramp with rails (alley → gallery)
- [ ] AW.5 North stair from the alley to the plaza (end of the lawn)
- [ ] AW.6 A_W west facade under the gallery: doors ("Dining Hall" double door, single door at the A_S pilaster), windows, pilasters
- [ ] AW.7 A_W north end wall
- [ ] AW.8 Basement descent at the gallery (stone steps + steel stair)
- [ ] AW.9 Plaza between the gallery and C: paving levels, kerbs, signboard, yellow bins, wayfinding sign

## 4. B–A alley and the main gate (clips 065910461, 065934318, 070021774, 070309303, 061913764, 061757320)
- [ ] G.1 Checkpoint booth 3.42 × 3.10: tile walls, brick plinth, doors, windows, roof
- [ ] G.2 Gate canopy 11.9 × 3.45 on a round column: roof pitch, ends, soffit
- [ ] G.3 Turnstiles and the pass-through railings
- [ ] G.4 Gate leaves, fence panels and posts along the street
- [ ] G.5 Yard just inside the gate: benches, bins, bike racks, herringbone paving
- [ ] G.6 Alley B–A: tree row, concrete-edged hedges, kerbs, lawn edging (red), yellow-painted kerbs
- [ ] G.7 South wide stair from the gate down to the A corner
- [ ] G.8 North stair at the end of the lawn (with rails)
- [ ] G.9 Retaining wall with the granite parapet between the alley and the walkway along A (~1.35 m)
- [ ] G.10 Grating ramp at the side stair opposite the lettering
- [ ] G.11 A_S entrance pavilion (pitched roof, door 1.55, pilasters, steps)
- [ ] G.12 Pad at the foot of the south stair (A_S corner, drain grating)
- [ ] G.13 Slope between the fence walkway (east of the booth) and A's south facade

## 5. Hall–C passage and the sports hall's east end (clips 070410255, 070541257, 081834–081838)
- [ ] H.1 Passage stair 2.2 m wide (5 × ~0.175), granite cheek
- [ ] H.2 Grey ramp on the stair's west side
- [ ] H.3 Low railing with dense bars
- [ ] H.4 Sports hall east end wall (pink/orange) with the door and canopy by the ramp, 3 steps
- [ ] H.5 Sports hall 2-storey wing at the NE corner (one continuous mass)

## 6. Garden (clips 081856511–082013462, 061757320)
- [ ] GD.1 West gazebo: 7.7 across posts, 9.15 roof, posts 2.6, brick parapet 0.94, roof and finial
- [ ] GD.2 East gazebo (orientation by the A side)
- [ ] GD.3 Hedge maze: hedge blocks and paths
- [ ] GD.4 Hedge arches (south, north)
- [ ] GD.5 South pergola alley: arches, radial paths
- [ ] GD.6 Retaining wall and steps between B's side and the garden (~1 m drop)
- [ ] GD.7 East edge toward the alley: cobble retaining wall, hedge, lamps
- [ ] GD.8 Garden furniture: wrought-iron benches with slats, bins, lamp posts
- [ ] GD.9 Ground: diamond tiles, scalloped concrete edging, levels

## 7. Sports fields (clips 070410255, 070541257)
- [ ] F.1 Football pitch: turf slab, red plinth around it, levels (+0.35 over the south pad)
- [ ] F.2 Pitch fence: posts, mesh panels 8.2 m, gates
- [ ] F.3 Floodlight masts (8.6 m) with heads
- [ ] F.4 Courts ×3 (basketball, volleyball, hard court): slabs, markings as decals, fences between, hoops, net posts
- [ ] F.5 Decorated alley along the pitch: planters, thujas, double-ball lamps, garlands
- [ ] F.6 Flowerbed plaza slope from the path end to the pitch (4.475 → 3.45)
- [ ] F.7 Benches by the pitch
- [ ] F.8 Red square pad west of the pitch (~11 × 6.4)
- [ ] F.9 North boundary fence with brick piers along the road
- [ ] F.10 Thujas along the south court fence

## 8. Sports hall (long one-storey block north of the garden)
- [ ] SH.1 South facade under the gallery: wall, doors, windows
- [ ] SH.2 Gallery: red posts, beams, deck, eaves
- [ ] SH.3 West end, north side
- [ ] SH.4 Roof: pitch, ridge, eaves, gutters

## 9. Canteen and small buildings north of C
- [ ] K.1 Canteen: all four facades, west entrance (glass vestibule, overhang on a red post, steps, ramp), roof
- [ ] K.2 Small pavilion
- [ ] K.3 One-storey building with a deep timber overhang on a red post (070410255 39–41 s): identify and model

## 10. Block B
- [ ] B.1 South (street) facade: bays between pilasters, windows, blank KOCH lettering band
- [ ] B.2 North (garden) facade
- [ ] B.3 West end
- [ ] B.4 East facade: entrance canopy, door and threshold, maroon sloped covers
- [ ] B.5 Low red-roofed annex at the NE corner
- [ ] B.6 Roof: slopes, hatch on the north slope
- [ ] B.7 Position: B–A gap (13.4 vs 12.6) settled on the mesh

## 11. Block A
- [ ] A.1 Main facade on the square: blank KOCH lettering + round panel, pilasters, windows
- [ ] A.2 A_S south facade (street)
- [ ] A.3 A_S and A_N east facades (parking side)
- [ ] A.4 A_N north end (cut gable)
- [ ] A.5 A_E and the NE annex between A_N and A_S
- [ ] A.6 Two-storey part (hall + library) and the roof junctions
- [ ] A.7 Roofs of A (pitch, ridges, valleys)
- [ ] A.8 Junction A_S / gallery block (gap or light well)
- [ ] A.9 Circle-pattern paving and levels in front of A

## 12. Street front (clips 065653194, 065812371, 065838589, 065856484, photo 0924_065835)
- [ ] S.1 Sidewalk: clover/hexagon pavers, kerbs, levels
- [ ] S.2 Low parapet along the sidewalk with its steps; lawn level behind it
- [ ] S.3 Tree pits along the sidewalk
- [ ] S.4 Parking by the sidewalk with yellow-black barrier pipes
- [ ] S.5 Zebra crossing 4.3 m, road kerbs 0.15, carriageway 14.8
- [ ] S.6 Bus stop (find it) and trolleybus poles
- [ ] S.7 West end of the sidewalk (grey wall with the gas pipe)
- [ ] S.8 Outside parking by the gate and the residential towers as far massing

## 13. West campus (web media, satellite; owner footage has none)
- [ ] W.1 Block D: massing, 4 floors, curved entrance canopy, roofs with light strips
- [ ] W.2 Block E (behind the sports hall, likely BLD_W1): facades, outdoor fire stair, grey annex
- [ ] W.3 Complex south of D: decide whether it is campus; massing if yes

## 14. Found in the web media (C:\koch\web\triage_part1.md, triage_part2.md)
- [ ] X.1 Bike parking at the C entrance stair
- [ ] X.2 Three flagpoles by the main gate canopy; the yellow decorative bicycle inside the fence by the canopy column
- [ ] X.3 Gate canopy fascia panel and the plaque pillar (blank KOCH panels)
- [ ] X.4 ATM kiosk on the south sidewalk by the fence
- [ ] X.5 Second street gate with its booth, sliding gate and ornate fence (west street side, by D)
- [ ] X.6 Blue-glass curtain-wall atrium on the street facade; rooftop penthouse on the 4-storey red/white block (D)
- [ ] X.7 Dark hipped/octagonal pavilions in the D forecourt; the picnic-shelter row by the west 4-storey block
- [ ] X.8 Pitch extras: spectator benches/tiers, X-braced ball-stop fence, red rubber border, mast ladders
- [ ] X.9 Low timber stage deck at the plaza edge by the courts
- [ ] X.10 Outdoor stair behind a goal (red risers, white treads) to the next terrace; red wall with a stair at the end of the pergola alley
- [ ] X.11 Metal hoop arch on the terrace at the head of a wide granite stair
- [ ] X.12 Round flower bed with a lamp post on the plaza by the courts (check it still exists)
- [ ] X.13 Small red-brick hut with a pitched roof by the garden alley; timber gazebo (second type)
- [ ] X.14 Notice-board stands (2 in front of A's lettering, garden, alleys), info/map boards
- [ ] X.15 Lamp kit: single/double globe lanterns, curly-bracket wall lanterns, curved-arm street lamps
- [ ] X.16 Bins kit: wrought-iron litter bins, wheelie and recycling bins
- [ ] X.17 Parking with low garage sheds at the end of the long path; car canopy at the west path end
- [ ] X.18 Blue 20-ft container in the service alley
- [ ] X.19 Unidentified volumes to place or drop: pale building with red roof and steel fire escape, barrel-vault roof building N, dark-clad tall wall, pink block with glass entrance, chimney (skyline)

## 15. Terrain and levels
- [ ] T.1 Terrace levels re-measured on the mesh: alley along B 6.75/6.63, walkway along A 5.35, garden/gazebos/C plaza 5.35, sports level 4.475 → 3.45
- [ ] T.2 Every outdoor stair and ramp between terraces counted and matched to T.1
- [ ] T.3 Terrain pads and hard edges in the specs, no terrain poking through paving

## Log
- 2026-09-27: list created from ROUTE.md, campus.md, photo_requests.md, the handoff, the specs and the capture clips, then extended with the web-media triage (82 video sheets, 6 photo sheets). Best web sources for roofs and back sides: the 2023-01-28 full drone flight, 2022-04-19 (pitch, courts, booth from above, D), 2020-05-16 and 2022-10-30 aerials.
- 2026-09-27, C entrance component (rs_zCS2 comp. 2): scale 0.4737 m/unit from the 0.20 × 0.10 herringbone module (5 frames, 10 readings, ±1.5 %), cross-checked by a walking person (1.85 m) and the camera height (1.61 m); the RealityScan grid is tilted ~3.1° (north low), corrected from the plaza and tread planes.
