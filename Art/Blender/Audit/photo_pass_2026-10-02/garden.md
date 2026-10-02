ZONE garden (agent af38e17ab1c7db1bd). Generators: zone_garden.py (paths, hedges, edging, arches, square, lamps; rewrites OWN names), garden_pergola.py (pergola, benches, bins), hall_bed.py (HallBed_*), zone_sports.py (SITE_HallCPassage).
GD-1 P1 hedge arches ~2x: zone_garden.py ARCH_T 1.6, ARCH_H 2.7, new ARCH_D 1.2; per-arch: Arch_Bnd_G1_N span 1.3 thk 1.75 h 2.9 d 1.2; Arch_Bnd_G2_SE span 1.2 thk 1.6 h 2.35 d 1.2 (doughnut, outer 4.6x3.5 needs crown_thk/outer_h). medium. A019-A022, A217, A218, A136, A008.
GD-2 no boundary hedge (edging + lawn; arches free-standing) - CONFLICTS owner note 09-28/29 -> ask owner.
GD-3 boundary scalloped edging lines (Edging_Bnd_S [[99.762,-48.436],[152.299,-51.006]] gaps at x122.4, 129.0, (137.4?); Edging_Bnd_N [[100.553,-9.827],[158.297,-13.759]] gaps at (117.6,-11.34),(130.8,-12.24); Edging_Bnd_E [[158.297,-13.759],[156.9,-39.0],[153.482,-44.603]] gaps at G2_E (157.09,-29.28), G2_SE). h 0.27 thk 0.1 kind scalloped_edging.
GD-4 delete Arch_Bnd_G1_SSE, Arch_Bnd_Centre_NS_S; G1_SSE west hedge strip dropped. medium.
GD-5 north walk: diamond-tile band (~4.5 m from the N boundary line, width low conf) + plain concrete to the hall; herringbone only NE of a red kerb (hall_bed.py HallBed_Paving).
GD-6 HallBed_Bench_*: length 3.0, depth 0.55, seat_h 0.47, back_h 0.85, ue_asset bench_slats_steel_frame; Bench_Pergola_* same asset.
GD-7 CentreSquare_Lamp: 3 globes (top + 2 S-scroll arms 1.3 m apart), globe 0.38, h 3.8, pedestal 0.35x0.35x1.0 on pad 0.75x0.75x0.05; needs builder.
GD-8 edging blocks h 0.27 (pitch 0.20, thk 0.10).
GD-9 gazebo inner parapet face + central column maroon paint (needs builder slots _ParapetInner/_Column). high.
GD-10 Passage_Bench = red sheet-metal sloped cover box, h 0.45 at the wall, slot M_Sheet_Red (zone_sports.py).
GD-11 confirmed: boulder wall ~0.9, pergola pitch 2.4-2.5, walk width ~2.2 (Pergola_South width 2.2, legs on walk edges).
GD-12 pergola walk west end: red brick wall ~1.8 m [[99.3,-47.9],[99.5,-53.4]] thk 0.25 + yellow gas pipe d0.1 at ~0.5 m. low.
Signs: A_W gallery LetterBand 'GATEWAY TO THE WORLD!' (blue caps 0.5-0.6 m on white band 12-15 m) -> KOCH.
Questions: boundary hedge? north walk diamond band width; diamond tile module 0.40?; south sector hedge lines (video along the pergola walk, G2_SSW path).
