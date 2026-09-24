---
name: research
description: Precise web research before a technical decision or before writing a system from scratch in this UE 5.8 project. Use when choosing render settings, algorithms, plugins, asset pipelines, AI/physics approaches, or when existing code might already solve the task.
---
Goal: find the best **realism per millisecond** option, or a proven implementation to reuse and adapt. A good existing solution saves development time.
Depth scales with the problem: a small choice needs a few queries, a hard problem gets as much research and thinking as it needs, with no time limit.

1. Run 3–6 precise queries in parallel. Always include "UE 5.8" or "Unreal Engine 5.8", plus the exact feature or class name. Use a subagent if more than a few pages must be read.
2. Sources, in order of trust:
   - dev.epicgames.com docs and release notes
   - forums.unrealengine.com
   - Epic GitHub, plugin repos and their issues
   - Unreal Fest / GDC talks
   - Tom Looman, 80.lv, CG Channel
   - r/unrealengine
   Prefer 2025–2026 sources. Treat UE4-era advice as unverified.
3. Reuse check: look for the best known algorithm or method (papers, GDC/Unreal Fest talks, blog posts) and for working code: GitHub (MIT/Apache/BSD), Fab free plugins, and Epic samples (Lyra, Game Animation Sample, City Sample, Content Examples, Stack O Bot). Check the license, UE version and last update. Adapt it to our task. If nothing fits, design it ourselves at the same quality.
4. Compare 2–3 options on:
   - realism
   - GPU ms and VRAM at 1080p on the RTX 3070 Ti Laptop 8 GB and RX 6750 GRE
   - stability in 5.8
   - effort.
5. Output: a 3–5 line conclusion with the choice and source URLs. Add one line to `docs/decisions.md` only if the choice affects the frame budget or architecture. Then implement.
