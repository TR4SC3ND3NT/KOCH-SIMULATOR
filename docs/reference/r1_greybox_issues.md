# Greybox issues for R1 (found in UE, fixed level-side by Scripts/Unreal/fix_site.py)

Generated 2026-10-27 from Saved/QA/fixes.json. UE cm = (100x, -100y, 100z) of Blender m. Please fix in the specs/.blend so the level-side patches can be removed.

## 1. PavilionStair is built 90 deg off its spec
- `SITE_GateAlley.json` PavilionStair: dir_deg -2.808 (down east, 8 x 0.175 / 0.34) but the mesh runs its steps N/S; the walkway side is a 1.2 m wall. UE now hides it and rebuilds the flight east (landing 6.76 -> walkway 5.37, 8 risers 17.4 cm).
- Worth checking the other `stairs_run` builds for the same yaw issue.

## 2. Open ground steps (49 edges): the upper ground is a one-sided sheet, no vertical face
From below you look under the terrain and see sky (owner playtest: hall passage ramp). UE closes them with 12 cm concrete walls. Largest:

- UE (9544, -8450) along x, 650 cm long, z 218..278 cm
- UE (21250, -8519) along y, 650 cm long, z 161..218 cm
- UE (20600, -8544) along y, 650 cm long, z 162..218 cm
- UE (19950, -8569) along y, 650 cm long, z 164..218 cm
- UE (19300, -8594) along y, 650 cm long, z 168..218 cm
- UE (18650, -8619) along y, 650 cm long, z 171..218 cm
- UE (18000, -8644) along y, 650 cm long, z 176..218 cm
- UE (10400, -7895) along y, 650 cm long, z 218..257 cm
- UE (17350, -8669) along y, 650 cm long, z 180..218 cm
- UE (10200, -8955) along y, 650 cm long, z 218..254 cm
- UE (15500, -923) along y, 250 cm long, z 449..535 cm
- UE (16700, -8694) along y, 650 cm long, z 185..218 cm
- UE (10850, -8930) along y, 650 cm long, z 218..250 cm
- UE (9981, 5100) along x, 250 cm long, z 559..631 cm
- UE (11500, -8905) along y, 650 cm long, z 218..243 cm

## 3. Floating props

- GBS_Garden_Bin_Pergola_West (SITE_Garden, bin_wrought_iron): 49.0 cm above its support
- GBS_Gate_FaceTerminal_In (SITE_Gate, face_recognition_terminal): 35.0 cm above its support
- GBS_Gate_FaceTerminal_Out (SITE_Gate, face_recognition_terminal): 35.0 cm above its support
- GBS_Sports_GuardPost_FaceID (SITE_Sports, face_terminal): 120.0 cm above its support

## 4. Export notes
- Ground tile seams 2,-2 -> 2,-1 and 2,0 -> 3,0 do not match (ue_prep check.py: 1-2 unmatched vertices).
- 206 non-context meshes exceed the 15 m piece rule for Lumen SW (e.g. SM_GB_Sports_LowerYard_Retain_West, SM_GB_BLD_D_M_Cladding).
- SM_GB_BLD_B_GasPipeCover_North: 33k tris for a pipe cover.
- Zone names SITE_Sport (15) and SITE_Sports (605) look like a typo split.
- SM_GB_BLD_C_Wall_2d884e77 has two slots both named M_Paint_White (UE merges them).
- Review palette lives only in Material.diffuse_color; Principled BSDF stays default 0.8 grey (export_material_colors.py reads diffuse_color).

## 5. Owner playtest 2026-10-27
- TER_Ground step walls from settle.py are wound into the higher ground (8204 faces, e.g. east gate lane x 202.1 m); UE culls them and the sky shows through. ue_prep/terrain.py now turns them out and gives them the top's material; open rims get a 0.5 m skirt. Please fix the winding in settle.py.
- GBS_Trees_WestStrip_OT_west_strip_00..09_conifer: not on the real site (owner). Hidden level-side via Scripts/Unreal/owner_removed.json.
- GBS_Sports_NorthBoundary_Wall: one 360 m mesh with a straight bottom; over the uneven ground it hovers up to ~25 cm. fix_site.py adds a concrete footing strip; a wall that follows the ground (or a modelled footing) would retire it.
- The ground tiles stop ~200 m out while the OSM context blocks reach ~800 m; place_far_ground.py adds a far ground under them.
