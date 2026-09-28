# Zone before/after sheet for the R1 zone loop: height map of the zone, cross-sections (before/after, from two
# terrain_audit.py grids) and the parameter table (current / real / source / deviation) -> one PNG for the owner.
# Run: python3 Scripts/Geo/zone_report.py ZONE.json   (system python: numpy + matplotlib)
# ZONE.json: {"name", "before", "after" (audit tags), "bbox": [x0,y0,x1,y1], "sections": [[label, [x,y], [x,y]], ...],
#             "table": [[param, before, after, real, source], ...], "notes": [str, ...], "out": path}
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

AUDIT = os.path.join(os.path.dirname(__file__), "..", "..", "Art", "Blender", "Audit")


def grid(tag):
    d = np.load(os.path.join(AUDIT, tag + "_grid.npz"))
    return d["xs"], d["ys"], d["Z"]


def sample(xs, ys, Z, p0, p1, step=0.05):
    n = int(np.hypot(p1[0] - p0[0], p1[1] - p0[1]) / step) + 1
    t = np.linspace(0, 1, n)
    x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
    s = xs[1] - xs[0]
    i = np.clip(np.round((x - xs[0]) / s).astype(int), 0, len(xs) - 1)   # nearest cell: keeps vertical steps sharp
    j = np.clip(np.round((y - ys[0]) / s).astype(int), 0, len(ys) - 1)
    return t * np.hypot(p1[0] - p0[0], p1[1] - p0[1]), Z[j, i]


def main(cfg):
    xb, yb, Zb = grid(cfg["before"]); xa, ya, Za = grid(cfg["after"])
    x0, y0, x1, y1 = cfg["bbox"]
    ii = (xa >= x0) & (xa <= x1); jj = (ya >= y0) & (ya <= y1)
    ns = len(cfg["sections"])
    fig = plt.figure(figsize=(18, 7 + 3.2 * ns + 0.32 * len(cfg["table"])))
    gs = fig.add_gridspec(2 + ns, 2, height_ratios=[7] + [3.2] * ns + [0.32 * len(cfg["table"]) + 1.5])
    for k, (Z, t) in enumerate(((Zb, "до"), (Za, "после"))):
        ax = fig.add_subplot(gs[0, k])
        sub = Z[np.ix_(jj, ii)]
        vmin, vmax = np.nanpercentile(Za[np.ix_(jj, ii)], 1), np.nanpercentile(Za[np.ix_(jj, ii)], 99)
        im = ax.imshow(sub, origin="lower", extent=[x0, x1, y0, y1], cmap="terrain", vmin=vmin, vmax=vmax)
        ax.contour(xa[ii], ya[jj], sub, levels=np.arange(np.floor(vmin * 10) / 10, vmax, 0.1), colors="k", linewidths=0.3)
        for lab, p0, p1 in cfg["sections"]:
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], "r-", lw=1.5); ax.text(*p0, lab.split(":")[0], color="r", fontsize=9)
        for lx, ly, txt in cfg.get("labels", []):
            ax.text(lx, ly, txt, fontsize=8, ha="center", bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.4))
        ax.set_title(f"{cfg['name']} — земля {t} (изолинии 0.1 м)"); ax.set_aspect("equal")
        fig.colorbar(im, ax=ax, shrink=0.8, label="z, м")
    for k, (lab, p0, p1) in enumerate(cfg["sections"]):
        ax = fig.add_subplot(gs[1 + k, :])
        d, zb = sample(xb, yb, Zb, p0, p1); _, za = sample(xa, ya, Za, p0, p1)
        ax.plot(d, zb, color="0.6", lw=2.5, label="до"); ax.plot(d, za, color="C3", lw=1.3, label="после")
        for m, zz in zip(d[::max(1, len(d) // 12)], za[::max(1, len(d) // 12)]):
            if np.isfinite(zz):
                ax.text(m, zz + 0.08, f"{zz:.2f}", fontsize=7, ha="center", color="C3")
        ax.set_title(lab, fontsize=10); ax.set_ylabel("z, м"); ax.grid(alpha=0.3); ax.legend(fontsize=8)
        ax.set_aspect(4, adjustable="datalim")
    ax = fig.add_subplot(gs[-1, :]); ax.axis("off")
    rows = [["параметр", "было", "стало", "реально", "источник"]] + [[str(c) for c in r] for r in cfg["table"]]
    tb = ax.table(cellText=rows, loc="upper center", cellLoc="left", colWidths=[0.28, 0.1, 0.1, 0.1, 0.42])
    tb.auto_set_font_size(False); tb.set_fontsize(9); tb.scale(1, 1.35)
    for c in range(5):
        tb[0, c].set_facecolor("#dddddd")
    if cfg.get("notes"):
        ax.text(0.0, -0.05, "\n".join(cfg["notes"]), transform=ax.transAxes, fontsize=9, va="top")
    fig.tight_layout()
    out = os.path.expanduser(cfg["out"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=100); plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    main(json.load(open(sys.argv[1], encoding="utf-8")))
