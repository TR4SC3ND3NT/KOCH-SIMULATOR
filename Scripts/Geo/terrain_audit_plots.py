# Diagnostic figures for the terrain audit (R1): before/after height (hillshade + contours), slope, correction map
# (dz with protected zones) and cross-sections of the hardest slopes, from terrain_audit.py grids.
# Run: python3 Scripts/Geo/terrain_audit_plots.py BEFORE_TAG AFTER_TAG   (system python: numpy + matplotlib)
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "Art", "Blender", "Audit")
SECTIONS = [   # (label, start xy, end xy): the hardest slopes and the audited transitions
    ("PassageUpper -> PassageLower -> sports platform (x 165)", (165, -5), (165, 50)),
    ("B corner wide stair (y -54)", (140, -54), (170, -54)),
    ("alley bank B -> alley -> A_S (y -78; x 140-147 is inside B: basement ground, hidden)", (140, -78), (175, -78)),
    ("gate sidewalk -> gate plaza -> south stair -> alley (x 158; y -97..-94 inside the solid SouthBed planter, hidden)", (158, -140), (158, -85)),
    ("sports platform -> north terrace -> lower yard (x 178)", (178, 55), (178, 99)),
    ("sports west edge (y 58)", (90, 58), (125, 58)),
]


def load(tag):
    d = np.load(os.path.join(OUT, tag + "_grid.npz"))
    return {k: d[k] for k in d.files}


def hillshade(Z, s, az=315, alt=45):
    gy, gx = np.gradient(np.nan_to_num(Z, nan=np.nanmean(Z)), s)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
    a, z = np.radians(az), np.radians(90 - alt)
    return np.cos(z) * np.cos(slope) + np.sin(z) * np.sin(slope) * np.cos(a - aspect)


def sample(G, p0, p1, step=0.1):
    xs, ys, Z = G["xs"], G["ys"], G["Z"]
    n = int(np.hypot(p1[0] - p0[0], p1[1] - p0[1]) / step) + 1
    t = np.linspace(0, 1, n)
    x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
    s = xs[1] - xs[0]
    fi, fj = (x - xs[0]) / s, (y - ys[0]) / s
    i, j = np.floor(fi).astype(int), np.floor(fj).astype(int)
    ok = (i >= 0) & (j >= 0) & (i < len(xs) - 1) & (j < len(ys) - 1)
    i, j = np.clip(i, 0, len(xs) - 2), np.clip(j, 0, len(ys) - 2)
    tx, ty = fi - i, fj - j
    z = (Z[j, i] * (1 - tx) * (1 - ty) + Z[j, i + 1] * tx * (1 - ty) + Z[j + 1, i] * (1 - tx) * ty + Z[j + 1, i + 1] * tx * ty)
    return t * np.hypot(p1[0] - p0[0], p1[1] - p0[1]), np.where(ok, z, np.nan)


def main(bt, at):
    B, A = load(bt), load(at)
    xs, ys = A["xs"], A["ys"]; s = xs[1] - xs[0]
    ext = [xs[0] - s / 2, xs[-1] + s / 2, ys[0] - s / 2, ys[-1] + s / 2]
    # 1. height before/after
    fig, ax = plt.subplots(2, 1, figsize=(15, 20))
    for a, G, t in ((ax[0], B, "before (" + bt + ")"), (ax[1], A, "after (" + at + ")")):
        Z = G["Z"]
        a.imshow(Z, origin="lower", extent=ext, cmap="terrain", vmin=np.nanpercentile(Z, 1), vmax=np.nanpercentile(Z, 99))
        a.imshow(hillshade(Z, s), origin="lower", extent=ext, cmap="gray", alpha=0.35)
        a.contour(xs, ys, Z, levels=np.arange(np.floor(np.nanmin(Z)), np.nanmax(Z), 0.25), colors="k", linewidths=0.25)
        for lab, p0, p1 in SECTIONS:
            a.plot([p0[0], p1[0]], [p0[1], p1[1]], "r-", lw=1)
        a.set_title("TER_Ground height, 0.25 m contours, " + t); a.set_aspect("equal")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"diag_height_{bt}_vs_{at}.png"), dpi=110); plt.close(fig)
    # 2. slope after
    fig, a = plt.subplots(figsize=(15, 10.5))
    im = a.imshow(np.degrees(np.arctan(A["slope"])), origin="lower", extent=ext, cmap="magma", vmin=0, vmax=30)
    fig.colorbar(im, ax=a, label="slope (deg)", shrink=0.7); a.set_title("slope after (" + at + ")"); a.set_aspect("equal")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"diag_slope_{at}.png"), dpi=110); plt.close(fig)
    # 3. corrected areas: dz, protected zones hatched grey, remaining defects
    dz = A["Z"] - B["Z"]
    fig, a = plt.subplots(figsize=(15, 10.5))
    a.imshow(hillshade(A["Z"], s), origin="lower", extent=ext, cmap="gray", alpha=0.6)
    lim = 0.3
    im = a.imshow(np.ma.masked_where(np.abs(dz) < 0.005, dz), origin="lower", extent=ext, cmap="coolwarm", vmin=-lim, vmax=lim)
    a.contour(xs, ys, A["protected"].astype(float), levels=[0.5], colors="g", linewidths=0.4)
    dj, di = np.nonzero(A["defect"])
    a.scatter(xs[di], ys[dj], s=1, c="k")
    fig.colorbar(im, ax=a, label="z after - before (m); |dz| < 5 mm blank", shrink=0.7)
    a.set_title("corrected areas (colour), protected zone outlines (green), remaining flagged cells (black)")
    a.set_aspect("equal"); fig.tight_layout(); fig.savefig(os.path.join(OUT, f"diag_corrections_{bt}_vs_{at}.png"), dpi=110)
    plt.close(fig)
    # 4. cross-sections
    fig, ax = plt.subplots(len(SECTIONS), 1, figsize=(13, 3.1 * len(SECTIONS)))
    for a, (lab, p0, p1) in zip(ax, SECTIONS):
        d, zb = sample(B, p0, p1); _, za = sample(A, p0, p1)
        a.plot(d, zb, color="0.6", lw=2.2, label="before")
        a.plot(d, za, color="C3", lw=1.0, label="after")
        a.set_title(f"{lab}: {p0} -> {p1}", fontsize=9); a.set_ylabel("z (m)"); a.grid(alpha=0.3)
        a.set_aspect(3.0, adjustable="datalim"); a.legend(fontsize=7, loc="best")
    ax[-1].set_xlabel("distance along section (m), vertical exaggeration 3x")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"diag_sections_{bt}_vs_{at}.png"), dpi=110); plt.close(fig)
    ch = np.abs(dz) > 0.005
    print(json.dumps({"changed_cells": int(ch.sum()), "changed_m2": float(ch.sum() * s * s),
                      "changed_in_protected_share": float((ch & A["protected"]).sum() / max(1, ch.sum())),
                      "max_abs_dz": float(np.nanmax(np.abs(dz)))}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
