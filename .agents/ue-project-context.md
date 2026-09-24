# UE project context (read by the ue-* skills; full rules in /AGENTS.md)
- Engine: UE 5.8.3 (launcher/prebuilt). C++ project `KochSimulator` (First Person template), single-player story FPS.
- Platforms: Win64 (primary: RTX 3070 Ti Laptop 8 GB, RX 6750 GRE 12 GB), Linux (dev only).
- Modules: `KochSimulator` (runtime, feature folders Core/Player/Combat/AI/Interaction/World/Narrative/UI), optional `KochSimulatorEditor`.
- Key plugins: ModelContextProtocol + AllToolsets (Unreal MCP), PythonScriptPlugin, VibeUE, UEGitPlugin, Inkpot, EnhancedInput, StateTree, Chaos.
- Conventions: Epic C++ standard, Allar asset naming, logic in C++ / thin BPs, no GAS, no replication needed.
- Budget: 1080p ≥60 fps, VRAM ≤7 GB (see AGENTS.md).
