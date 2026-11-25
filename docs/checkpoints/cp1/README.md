# Checkpoint 1 (Thu 2026-11-26): freeze the slice, walk the street

**Goal:** one walkable route from the street to the checkpoint, with a frozen plan.

## Hand-in
| Item | Where |
|---|---|
| Slice script | [slice_script.md](slice_script.md) |
| decisions.md entries (slice, owners, canon, character path, game start) | [docs/decisions.md](../../decisions.md), entries dated 2026-11-25 |
| Video: walking street → checkpoint (25 s, 1080p) | [KOCH_CP1_street_to_checkpoint.mp4](KOCH_CP1_street_to_checkpoint.mp4), rendered in-engine from the slice level by `Scripts/Unreal/render_cp1_walk.py` |
| fps / VRAM numbers | [Performance](#performance) below |
| Status table, one owner per asset | [README.md](../../../README.md#status-2026-11-25) |

## In the build
- The game starts on `L_GreyboxTest` at the street start (`PlayerStart_Prologue`, bus stop side), facing the zebra crossing and the gate.
- Placeholder hero: the first-person player mannequin. Placeholder guard: an idle mannequin in front of the turnstile (`Guard_Placeholder_Gate`).
- The route street → crossing → gate is walkable; the turnstile and the sliding gate are shut (the refusal beat). Behind the gate, alley → yard → Block C hall is walkable too (checked with capsule sweeps along the whole route).
- Packaged Win64 build of the slice: `KochSimulator.exe` (Development), cooked from `L_GreyboxTest` only (2.4 GB, kept out of Git). It starts at the street with no editor running. Command: `RunUAT BuildCookRun -platform=Win64 -clientconfig=Development -build -cook -map=/Game/KochSimulator/Maps/L_GreyboxTest -stage -pak -iostore -archive`.

## Performance
Measured 2026-11-25 on reference machine B (Radeon RX 6750 GRE 12 GB, Ryzen 5 5500X3D, 16 GB RAM): `-game` from the editor binary, 1920×1080, Epic scalability, TSR, VSync off, `Scripts/Unreal/perf_capture.py` (30 s FPS chart after 20 s warm-up) at five points along the slice. VRAM is the game process's dedicated GPU memory (Windows counter, median of the run).

**Before** (the slice as it was):

| Point | fps | Game thread | Render thread | GPU | Frames over 16.7 ms | VRAM |
|---|---|---|---|---|---|---|
| Street (bus stop side) | 32.6 | 30.6 ms | 9.9 ms | 13.2 ms | 45.6 % | 5.57 GB |
| Checkpoint | 37.7 | 26.5 ms | 8.5 ms | 14.7 ms | 37.1 % | 5.60 GB |
| Alley | 44.0 | 22.7 ms | 7.5 ms | 14.4 ms | 26.6 % | 5.59 GB |
| Yard | 71.3 | 6.2 ms | 14.0 ms | 12.5 ms | 0.0 % | 5.42 GB |
| Block C hall | 55.9 | 17.9 ms | 6.2 ms | 11.3 ms | 6.8 % | 5.53 GB |

**After** the CP1 optimization (wind trees stop their unused CPU pose update, `docs/decisions.md`):

| Point | fps | Game thread | Render thread | GPU | Frames over 16.7 ms | VRAM |
|---|---|---|---|---|---|---|
| Street (bus stop side) | 71.2 | 1.6 ms | 14.1 ms | 12.7 ms | 0.0 % | 5.09 GB |
| Checkpoint | 63.8 | 1.6 ms | 15.7 ms | 14.4 ms | 0.0 % | 5.19 GB |
| Alley | 64.5 | 1.6 ms | 15.5 ms | 14.2 ms | 0.0 % | 5.25 GB |
| Yard | 72.2 | 1.5 ms | 13.8 ms | 12.5 ms | 0.0 % | 5.19 GB |
| Block C hall | 80.3 | 1.6 ms | 12.5 ms | 11.2 ms | 0.0 % | 5.18 GB |

**Packaged build** (Win64 Development, no editor, 1920×1080 windowed, Epic, CSV profiler over the last 1500 of 2400 frames, `BugItGo` to each point):

| Point | fps | Game thread | Render thread | GPU | Frames over 16.7 ms | VRAM |
|---|---|---|---|---|---|---|
| Street (bus stop side) | 101.6 | 1.7 ms | 9.8 ms | 8.6 ms | 0.1 % | 4.67 GB |
| Checkpoint | 88.3 | 1.5 ms | 11.3 ms | 9.8 ms | 0.0 % | 4.82 GB |
| Alley | 91.6 | 1.4 ms | 10.9 ms | 9.6 ms | 0.0 % | 4.81 GB |
| Block C hall | 117.1 | 1.4 ms | 8.5 ms | 7.4 ms | 0.0 % | 4.75 GB |

Target: 60 fps at 1080p and at most 7 GB VRAM. Met at every point. The limit is now the render thread at the checkpoint and in the alley (15.5 ms, mostly waiting on the RHI thread and visibility tasks); it is the next target for CP2. Not measured yet: reference machine A (RTX 3070 Ti Laptop).

## The guide's questions
- **The slice in 30 seconds:** a man just fired from KOCH comes back with a gun hidden in his guitar case. You cross the street to the KOCH gate, the turnstile refuses you, the guard comes out, and you get past him with pepper spray, a knife or the gun. Then you push through the alley and the yard into the Block C hall. Five minutes on a photoreal 1:1 campus.
- **Delete one beat, does it still work?** Yes for the bus stop: starting at the crossing loses nothing. No for the guard confrontation: it is the prologue.
- **Who owns the build if the main machine breaks?** Eldiyar (R4) owns packaging. Ulukbek's desktop (RX 6750 GRE, reference machine B) has the full toolchain and made the CP1 build, so it is the backup.
