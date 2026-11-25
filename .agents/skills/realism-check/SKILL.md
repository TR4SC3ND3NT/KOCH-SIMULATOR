---
name: realism-check
description: Checklist to push an environment, material, lighting or prop change toward photoreal (GTA-6-level) quality while staying within the 1080p/60fps budget. Use before finishing any visual/content task.
---
Check, fix, then report only the failures you fixed:

- **Scale.** True 1:1: doors ≈ 0.95×2.05 m, classroom ≈ 3.0 m, corridor ≈ 3.5 m, floor-to-floor ≈ 3.8–4.0 m (`docs/reference/campus.md`).
- **Materials.**
  - Albedo in physical ranges (no pure black or white).
  - Roughness varies (no flat values).
  - Normal/height detail present.
  - Nanite displacement for close-up pavers and ground.
- **Wear.** Decals for dirt, stains, cracks, scuffs and edge wear. Grime in corners and at floor/wall joints.
- **Set dressing.** Clutter that matches the reference photos: signage, bins, cables, posters, leaves. No empty clean boxes.
- **Lighting.**
  - Lumen with a physically correct sun and sky for Bishkek (42.86°N).
  - Correct light units.
  - Manual/fixed exposure when comparing.
  - No light leaks (walls ≥ 10 cm).
- **Post.** Filmic tonemapper and a restrained grade matched to the reference. No heavy bloom, chromatic aberration or vignette.
- **Reference.** A side-by-side screenshot against the site photo, listing the differences.
- **Budget.** `stat gpu` stays within the AGENTS.md budget and VRAM ≤ 7 GB. If it's over, cut the cheapest-to-notice cost first.
