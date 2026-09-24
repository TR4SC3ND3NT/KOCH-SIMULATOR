# R1: World / Map

**Owns:** `Content/KochSimulator/Environment/`, `Content/KochSimulator/Maps/`, landscape, PCG graphs, foliage, lighting, post-process, HLOD, `Source/*/World/`, `Scripts/Editor/world_*`.
**Tools:** Unreal MCP + VibeUE, Blender MCP, PCG.
**Machine:** heavy editor work on a real GPU. The ThinkPad is for scripts, data and Blender only.

## Scope notes
- **Opening route:** a street segment of Ankara St (renamed in-game), the bus stop, the pedestrian crossing, the gate canopy and the checkpoint booth with turnstiles. These are gameplay-critical for the opening.
- **Hero's home:** a separate small level (TBD).
- **Rebranding:** every real sign, logo, plaque and slogan becomes KOCH branding. Nothing real is shown in-game.
- **Quality bar:** every object is built to professional, photoreal quality (`/realism-check`). No placeholder-looking assets ship.

## Phases
1. **Blockout 1:1.** Generate building boxes from OSM footprints (height = floors × ~3.3 m). Add paths, gates, fence and terraces, then check them against the capture videos. Result: a walkable campus.
2. **Modular kits** per facade style: wall bays, windows, maroon pilasters, brick-tile plinth, canopies, stairs, railings. Assemble them onto the footprints with PCG/Python.
3. **Block C interior:** floor plan, interior kit (terrazzo, blue accent panels, black aluminium doors, radiators, LED panels, granite stairs), props with collision and physics.
4. **Exterior dressing:** blue spruce, pine and elm trees (Nanite foliage), the hedge maze and arch, gazebos, three paver types with displacement, benches, bins, lamps, the street outside, the crossing and bus, and low-cost high-rise backdrops.
5. **Lighting and look:** Lumen, a real sun position for Bishkek (42.86°N) in autumn, an overcast sky matching the reference, fixed exposure, a colour grade matched to the photos.
6. **Combat readiness:** navmesh, cover, sightlines and spawn areas, coordinated with R3.
7. **Performance:** HLOD, and a profile pass on both reference machines.

## Checklist per PR
- Scale is 1:1.
- `/realism-check` skill is done.
- Side-by-side screenshot with the reference photo.
- `stat gpu` on at least one reference machine for heavy scenes.
- Locks released.

## First prompt
> Read AGENTS.md, docs/reference/campus.md and ~/alatoo-capture/data (OSM geojson, satellite, fest map). Research the best way to build a 1:1 World Partition blockout from OSM footprints in UE 5.8 (PCG vs Python/Unreal MCP vs VibeUE). Then generate the campus blockout (buildings as floors × 3.9 m boxes, paths, fence, gate, street and crossing) and verify the distances against the capture videos.
