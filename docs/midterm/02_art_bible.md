# KOCH-SIMULATOR: Art Bible (midterm, 2026-11-09)

Story-driven first-person action game in Unreal Engine 5.8.3. Setting: the headquarters campus of KOCH, a fictional corporation that sells face-recognition "safe city" security. The campus is a 1:1 recreation of a real site; in the game it is only ever KOCH HQ.

**Status note.** The current build has the real campus at final scale but still uses placeholders: the template rifle (white), mannequins and greybox interiors. This bible sets the target that every replacement asset must meet. Where a value is sampled from the build or the site, it says so; where it is a proposal, it says "proposed".

---

## 1. Visual pillars

| # | Pillar | What it means on screen | Test |
|---|---|---|---|
| 1 | **Ordinary place, true scale** | Real geometry, 1:1 in metres, real materials (render, tile, terrazzo, pavers). No fantasy architecture. The game is believable because the place is. | A screenshot next to a site photo shows the same proportions. |
| 2 | **The corporation is the only clean thing** | The city and the campus are worn, dusty, patched. KOCH branding (red, signage, screens, turnstiles) is spotless and new, so it reads as an occupier. | In any frame, the newest-looking object is KOCH's. |
| 3 | **Being watched** | Cameras, face terminals, screens and red recording lights are always somewhere in frame. Faces (posters, profile grids, the hero's mask) are the key motif. | Every playable space has at least one visible camera or screen. |
| 4 | **Grounded violence, readable play** | Daylight realism in the style of a modern crime-sandbox game. Combat stays readable: clear silhouettes, clean sightlines, HUD in the corners only. | At 30 m an enemy is told from a civilian by shape alone. |

---

## 2. Colour palette

### 2.1 Environment (sampled from the engine and site photos, README Checkpoint 4)

| Swatch | Hex | Role |
|---|---|---|
| Render | `#D6C4A0` | Beige wall render, the dominant facade colour. Large areas, mid value. |
| Pilasters | `#782C26` | Maroon pilasters and window frames. Vertical rhythm on every block. |
| Plinth tile | `#A0432F` | Red "brick" tile plinth and canopy soffits. Grounds the buildings. |
| Paving | `#C1B8A7` | Grey herringbone / hexagon pavers. The floor of most exterior shots. |
| Terrazzo | `#CFCAC0` | Block C interior floors. Light, slightly warm, shows dirt paths. |
| Block C panels | `#6E7FD0` | Periwinkle accent panels inside Block C. The only cool saturated colour on campus. |
| Roof red (proposed, sample before lock) | `#B23A30` | Pitched roofs seen from the yard and the air. Must stay darker and duller than KOCH red. |

### 2.2 Brand, HUD and gameplay signals

| Swatch | Hex | Role |
|---|---|---|
| **KOCH red** | `#D42A1E` | Brand colour: logo, flags, lanyards, signage bands, recording lights. Also the alert/threat colour (KOCH ALERT meter, lockdown strobes). Rule: red = KOCH = danger. |
| **HUD amber** | `#FFB000` | Player-owned information: health, ammo, objective label, prompts. Amber is Arsen's colour; it never appears on KOCH property. |
| HUD panel (sampled from the mockup, approx.) | `#141A22` at 75 % opacity | Backing plates for HUD text. Dark and cool so amber and red both pop. |
| HUD text (proposed) | `#F2EDE4` | Objective body text and subtitles. Warm off-white, not pure white. |
| FaceGate accept (proposed) | `#3FAE5A` | "WELCOME" state on face terminals only. The single green in the UI. |
| KOCH Secure grey-blue (proposed) | `#5F7487` | Guard shirts, booth trim. Low saturation so guards blend into the campus until they move. |
| KOCH Secure navy (proposed) | `#1F2A3C` | Guard trousers, tactical uniforms. |
| Elite black (proposed) | `#121417` | Temirov's unit. Darkest value in the game: it should be the darkest shape in any frame it is in. |

### 2.3 Per-zone mood (lighting colour, proposed; hex is an approximate swatch of the light, not a surface)

| Zone / missions | Key light | Swatch | Mood |
|---|---|---|---|
| Apartment, bus, street (M00) | Dawn sun, ~3000 K, low and warm, cold blue fill | `#F2B880` / fill `#8FA6C8` | Quiet, tired, home. |
| Gate, alley, garden (M01–M03) | Morning sun ~5000 K, clear sky with light haze | `#FFF1DE` | Bright, exposed, nowhere to hide. |
| Block C floors (M04–M05) | LED panels ~4000 K plus window daylight | `#FFE4C4` | Flat office light, sterile, fluorescent boredom. |
| C attic (M05) | Shafts from dormers, dust in the air | `#FFE9C9` | Cramped, secret, warm-dusty. |
| Basement studio (M06) | Tungsten practicals ~3200 K | `#E8B27A` | The only warm, human interior: Isa's piano. |
| SIGHT node room (M06) | Rack LEDs, KOCH red | `#D42A1E` | The machine's heart. Red, dark, loud fans. |
| Lockdown campus (M07) | High sun plus red strobes | `#D42A1E` pulses | Alarm; the clean campus turns hostile. |
| Clinic (M07) | Cold clinical ~6000 K | `#DDE8F0` | Cold, guilty, quiet. |
| Assembly Hall (M08) | Stage tungsten, then house lights out | `#FFC58A` | Theatre of power; the live camera's red tally light is the focal point. |

**Value rule:** keep exteriors mid-to-light (render, paving), and put the darkest values on characters and doorways so gameplay reads first.

---

## 3. Typography

All fonts are free under the SIL Open Font License on Google Fonts (they can ship in the game). The city is post-Soviet and Central Asian, so every font must cover Cyrillic; before locking, check the extra Central Asian Cyrillic letters Ң ң, Ө ө, Ү ү in each.

| Use | Font | Why |
|---|---|---|
| **KOCH wordmark, big signage** (gate canopy, block plates, banners) | **Unbounded** (Bold / Black) | Wide, geometric, very "tech brand". It looks expensive and cold next to the old campus, which is pillar 2. Covers Cyrillic. |
| **KOCH wayfinding, posters, screens, face terminals** | **Inter** (Regular / SemiBold) | Neutral corporate sans, built for screens, highly legible at small sizes on decals. Extended Cyrillic. KOCH's documents, kiosk UI and room plates all use it, so the company has one voice. |
| **HUD and menus** (objective, KOCH ALERT, health, prompts) | **IBM Plex Sans Condensed** (Medium / SemiBold) | Condensed fits long Russian/English strings into small corner panels; industrial, not sci-fi. Separates Arsen's interface from KOCH's Inter. |
| **HUD numbers** (ammo 30 / 90, timers) | **IBM Plex Mono** | Fixed-width digits do not jitter when the count changes. Same family as the HUD text. |
| **Subtitles** | IBM Plex Sans (Regular), 36 px at 1080p, on the HUD panel colour | Readable at couch distance; speaker name in amber. |
| **Handwriting** (Isa's notes, shift log, whiteboard "B-0") | **Caveat** | Human hand against corporate type: the clues look personal. Covers Cyrillic. |

Rules
- KOCH text is in-world (diegetic) and uses Unbounded/Inter only. Player UI uses Plex only. Never mix them.
- HUD text: uppercase labels (OBJECTIVE, HEALTH, KOCH ALERT), sentence case for the objective itself, as in `Checkpoint4_Pitch_and_Technical_Bridge/02_ui_mockup_dossier.png`.
- No real names, slogans or logos on any surface (AGENTS.md). Every sign is rewritten as KOCH; slogans are `TODO_LORE` until a human approves them.
- The mockup currently uses a system font; switching to Plex is a task for R4.

---

## 4. Motifs

| Motif | Where it appears | Rule |
|---|---|---|
| **Faces** | FaceGate terminals, profile grids in room 203, Talent Program posters, ID badges, the "Refer / Watch / Green" tiers | KOCH shows faces as data: grids, crops, boxes. The story ends on Arsen's real face. |
| **The mask** | Arsen's black half-face mask; "FACE NOT VISIBLE" screens; balaclavas on tactical guards | Mask = refusal to be read. Both Arsen and KOCH's soldiers wear one; the difference is the guitar case and the hair. |
| **Cameras and red lights** | CCTV in every room and corner, the live broadcast camera, rack LEDs | A small red dot means "you are recorded". After M06 they all go dark (montage). |
| **Turnstiles and gates** | Post One FaceGate, Post Two barrier arm, fail-locked doors | The game opens and closes on a turnstile (refused in M01, opened by his face in ending A). |
| **KOCH red accents** | Flags, lanyards, signage bands, door stripes, posters | Small and sharp: a stripe, a lanyard, a dot. Never a whole red wall (that is the roofs' and pilasters' job, and they are duller). |
| **Music** | Guitar case, the piano in the basement, "the old song", a bar of notes on the whiteboard | The human counter-motif to surveillance. Warm light and wood where it appears. |
| **Corporate cheer** | Motivational posters, PA chimes, "Clean Desk" rules, plaques | Dry humour; always slightly too bright and too new. |
| **Dust and wear** | Kerbs, pavers, stairs, the city | Everything not owned by KOCH is used and repaired. |

---

## 5. Composition rules

### 5.1 First-person gameplay (readability)
- Camera at eye height (≈ 1.65 m for an 1.80 m hero), horizontal FOV 90° default.
- Crosshair at screen centre; HUD lives only in the four corners plus the objective at top centre, as in the mockup. The central 60 % of the screen stays clean.
- The weapon or guitar case occupies the lower-right third at most. When holstered, the view is empty: Arsen reads as a musician.
- **Leading lines:** the campus is a set of alleys and terraces. Paths, kerbs and fence lines point to the next objective (the alley to the gate canopy in `docs/checkpoints/cp4/keyart.jpg` is the model).
- **Landmark per zone:** gate canopy, gazebos, Block C entrance canopy, Block A pavilion. One landmark is visible from every decision point.
- **Lighting guides the player:** the goal door or stair is the brightest thing in its frame (open daylight at the end of the Block C hall in `docs/checkpoints/cp4/block_c_hall.jpg`).
- **Combat spaces:** cover at waist height (benches, planters, hedges at 1.0–1.2 m); enemies enter from a lit side so they silhouette against the background.
- **Red is reserved:** in combat, the only saturated red in frame should be threat (alert, KOCH soldiers' patches, cameras). Do not dress combat spaces with red props.

### 5.2 Cutscenes and key frames
- Lens: 35 mm equivalent for dialogue, 24 mm for establishing shots, 50–85 mm for close-ups (face, mask, red tally light).
- Camera at standing eye level by default; low angles only for KOCH power (Lind on stage, Temirov); high angles only from CCTV (security-camera POV is a recurring shot).
- Rule of thirds; the face (or the mask) sits on the upper third line.
- Frame through things: doorways, turnstile bars, monitor bezels, hedge arches. The player is always looking past a barrier.
- One focal point per shot. If the red tally light is in frame, nothing else is red.
- Short in-engine cutscenes only (5–75 s, see the shot list in `03_production.md`); camera locks rather than cuts where possible (M01 takedown, M07 reunion).

---

## 6. Silhouettes (how each reads at 30 m)

At 30 m a character is about 60 px tall at 1080p, so faces are gone: shape, value and one colour carry the read.

| Type | Shape at 30 m | Value / colour | Read |
|---|---|---|---|
| **Arsen (hero)** | Tall and lean; long black hair in a low ponytail; a hard guitar case slung diagonally across the back (the only diagonal shape on any character); olive field jacket over a hoodie | Mid-dark olive and black; black mask | "Musician." Asymmetric outline; unmistakable in mirrors, reflections and cutscenes. |
| **Checkpoint guard** (Azamat type) | Heavy and round; peaked cap gives a flat top; soft vest; baton and radio at the hips | Grey-blue shirt over navy, mid value | "Doorman with a uniform." Static, posted near booths and desks. |
| **Patrol guard** | Like the checkpoint guard, no peaked cap; pistol and flashlight on the belt; walks in pairs | Grey-blue / navy | Two matching shapes moving together = patrol. |
| **Tactical** | Helmet dome; boxy plate-carrier torso; rifle held across the chest; knee pads | Navy, darker than patrols | "Soldier": the round head + square chest + diagonal rifle combination. Squads of 3–4. |
| **Elite** (Temirov's unit) | Bulkier armour, full-face visor or balaclava; no skin visible | Near black `#121417`; small KOCH red patch | Darkest shape in the frame. Appears only in Block A. |
| **Executive** (Lind, Ermekova, managers) | Narrow vertical column; tailored suit, no gear, no bags | Dark navy / charcoal with a white shirt triangle | "Clean." The only characters with no equipment. |
| **Civilian / intern** | Varied heights; backpacks, shopping bags, coffee cups, phones; lanyards | Mixed, mostly light and mid colours; interns wear navy polos with KOCH red lanyards | Busy outlines and props, light values. Never holds anything gun-shaped. |

Rules
- Threat gets darker and more geometric as the alert level rises: patrol → tactical → elite.
- No civilian may wear navy/black head-to-toe or a helmet-like hat.
- Test: render each archetype as a flat black silhouette at 60 px; a teammate must name all seven.

---

## 7. Lighting and time of day per mission

Story day runs from about 06:40 to 12:15 (premise proposal). Season is assumed early autumn (`TODO_LORE`, open question). The site is at about 43° N, so the noon sun in early October stands at about 40–45°. Exposure is fixed per zone (no wild auto-exposure swings).

| Mission | In-game time (proposed) | Light | Notes |
|---|---|---|---|
| M00 Morning Route | 06:40–07:30 | Dawn: low sun, long shadows, cool blue sky fill; bus interior lit by the window | Cold open: KOCH rooftop ad glows over the apartment blocks. |
| M01 FaceGate | ~07:45 | Low morning sun from the east-southeast, raking across the gate canopy | The face terminal screen is the brightest object at the gate. |
| M02 Brew Point | ~08:15 | Morning sun outside; warm café interior | Café is warmer than the PR lobby (people vs company). |
| M03 Hedge Maze | ~08:45 | Dappled light through trees and hedges; high contrast | Shadows are cover; tune shadow density for stealth readability. |
| M04 Room 203 | ~09:30 | 4000 K LED panels plus daylight through the north windows; screens light the faces | 8 monitors of face grids light the room. |
| M05 The Attic | ~10:15 | Sun shafts through dormers, dusty air | Low ceilings, low key, warm. |
| M06 Staff Studio | ~10:45 | Tungsten practicals in the studio; red rack LEDs in the node room; then emergency light | The camera-blackout montage shifts the campus to alarm mood. |
| M07 Health Center | ~11:15 | High sun outside, red lockdown strobes; cold white Clinic interior | Shutters cut the daylight into strips. |
| M08 Assembly | ~12:00 | Stage tungsten and screen glow; house lights killed in phase 2; AV stage flashes | The live camera's red tally light is the final focal point. |
| Endings | ~12:15 | Hard noon sun at the gate (A) / bus interior (B) | A: the face terminal reads him in full daylight. |

**Current build:** clear blue sky, mid-day sun, Lumen software GI, first lighting pass (`docs/checkpoints/cp4/keyart.jpg`). Open decision: the R1 role brief asks for an overcast sky matching the site photos, while the story assumes a clear morning. Proposal: clear sky for M00–M03 (exposure, readability) and thin high haze for later missions.

---

## 8. Materials and wear rules

- **Physically based, measured.** Albedo stays inside PBR ranges (no pure black or white surfaces); roughness carries most of the realism. Use scanned or CC0 sources (Poly Haven, Megascans/Fab) and calibrate their colour against the palette above.
- **Scale is real.** Texel density target about 1024 px/m for surfaces the player touches, 512 px/m for facades above 3 m. Tile sizes follow the site (pavers, 600 × 600 ceiling grid, brick-tile courses of 0.16 m at the booth).
- **Wear where people go:** darker, polished paths on terrazzo and stair nosings; chipped paint on kerbs and railings; dust in corners; water stains under windowsills and canopy drips; cigarette butts in the gazebos.
- **Repairs, not ruin:** patched render, mismatched replacement tiles, repainted kerbs (yellow, striped). The campus is maintained cheaply, not abandoned.
- **KOCH is new:** KOCH signage, turnstiles, terminals, flags and screens get clean, low-roughness finishes with no wear, so they look installed last month.
- **Decals over unique textures:** dirt, stains, posters and signs are decals (cheap, reusable); details are Nanite geometry, not parallax.
- **Glass and screens:** real reflections via Lumen; screens are emissive with a light scanline-free UI (no sci-fi glow).
- **Budget:** each displaced or layered material is checked against the 60 fps budget (AGENTS.md: Nanite/base 3–4 ms, Lumen ≤ 5 ms).

---

## 9. Mood board

No third-party images are copied into the repo. External references are described; repo images are our own engine frames.

| # | Reference | Source | What we take from it |
|---|---|---|---|
| 1 | Key art: alley toward the gate canopy, Lumen + Nanite, 1080p | [`docs/checkpoints/cp4/keyart.jpg`](../checkpoints/cp4/keyart.jpg) (our build) | Leading-line composition; facade palette (render, maroon pilasters, red tile); context apartment towers framing the far end. |
| 2 | Yard with the companion prototype | [`docs/checkpoints/cp4/yard.jpg`](../checkpoints/cp4/yard.jpg) (our build) | Hard morning shadows on pavers; hedges and spruces as cover and frame. |
| 3 | Block C ground-floor hall | [`docs/checkpoints/cp4/block_c_hall.jpg`](../checkpoints/cp4/block_c_hall.jpg) (our build) | Periwinkle panels on white; bright stair landing as the goal; sterile corporate interior. |
| 4 | Environment sheet: gate, garden and gazebo, north wall path, Block C side | [`Checkpoint4_Pitch_and_Technical_Bridge/03_character_and_environment_sheet.png`](../../Checkpoint4_Pitch_and_Technical_Bridge/03_character_and_environment_sheet.png) (our build) | The four prologue moods and the paving types. |
| 5 | HUD mockup over an in-engine frame | [`Checkpoint4_Pitch_and_Technical_Bridge/02_ui_mockup_dossier.png`](../../Checkpoint4_Pitch_and_Technical_Bridge/02_ui_mockup_dossier.png) (our build) | KOCH ALERT in red, player data in amber, dark translucent panels, corner layout. |
| 6 | Site reference photos and videos (about 600 photos went through the photo-vs-model bug hunt, 4 reviewers × ~150) | Map owner's local capture folder; **not in the repo** (they contain people) | Ground truth for materials, wear and colour; every review compares a build frame with one of these. |
| 7 | Modern crime-sandbox daylight (the Grand Theft Auto V / Red Dead Redemption 2 look) | Described only | Target realism: dense set dressing, believable wear, cinematic sun. |
| 8 | *Severance* (TV series): corporate interiors | Described only | Sterile, colour-coded corporate spaces; cheerful wellness language over something sinister; wayfinding type. |
| 9 | *Children of Men* (film, 2006): long-take, hand-held violence | Described only | Grounded, documentary camera; violence that feels heavy, not stylish. |
| 10 | *Deus Ex: Human Revolution* (game): amber/gold UI | Described only | An amber accent as the player's colour against a dark, neutral world. |
| 11 | *Hitman* (2016) and *Ready or Not* (games) | Described only | Social stealth readability (who is staff, who is a guard) and believable tactical-team silhouettes and kit. |
| 12 | Post-Soviet panel-block (microdistrict) street photography (genre) | Described only | The city around the campus: nine-storey blocks, trolleybus wires, poplars, dust; the procedural context city already follows this. |

---

## 10. Do / Don't

| Do | Don't |
|---|---|
| Match the site 1:1; check proportions against a reference photo | Invent architecture or "improve" the layout |
| Keep KOCH red small and sharp (stripes, dots, lanyards, lights) | Paint large areas KOCH red, or use it for non-KOCH props |
| Use amber only for the player's HUD | Use amber on signage, KOCH screens or enemies |
| Show cameras and screens in every space | Show hacking overlays, holograms or "movie hacker" UIs (*Watch Dogs* style is an anti-reference) |
| Wear and dirt on everything people touch | Clean, new-looking surfaces outside KOCH's own fittings |
| Distinct silhouettes per enemy tier; test them as black shapes | Civilians in navy/black or with helmet-like hats |
| Fixed exposure per zone; goal = brightest point | Auto-exposure pumping in and out of doorways |
| Fictional KOCH branding everywhere; `TODO_LORE` for unapproved text | Any real name, logo, slogan or street name, in textures, decals, file names or builds |
| Unbounded/Inter for KOCH, IBM Plex for the HUD | System fonts, or mixing the two type voices |
| Check every heavy material and character scene against the 60 fps budget | Ship a visual feature without `stat gpu` on a reference machine |
