# Top-view before/after plan of one zone from two export_tops.py dumps: objects of the zone drawn as footprints,
# labelled with length x width (minimum rotated rectangle, m) and top z; changed objects highlighted. R1 zone loop.
# Run: python3 Scripts/Geo/zone_plan.py BEFORE.npz AFTER.npz "x0,y0,x1,y1" PREFIX_REGEX OUT.png "title"
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
from shapely.geometry import box  # noqa: E402

SMALL = re.compile(r"Tree|Crown|Shrub|Thuja|Conifer|Bush|Lamp|Sign|Light|Bin|Rung|Post|Leg|Flood|Hoop|Net|Cam|Bollard|Bike|Plant_|Flower|Rail", re.I)


def load(path, view):
    d = np.load(path)
    tris, owner, names, zr = d["tris"], d["owner"], [str(s) for s in d["names"]], d["zr"]
    o = np.argsort(owner, kind="stable"); tris, owner = tris[o], owner[o]
    cuts = np.searchsorted(owner, np.arange(len(names) + 1))
    out = {}
    for k, nm in enumerate(names):
        T = tris[cuts[k]:cuts[k + 1]]
        mn, mx = T[:, :, :2].reshape(-1, 2).min(0), T[:, :, :2].reshape(-1, 2).max(0)
        if mx[0] < view.bounds[0] or mn[0] > view.bounds[2] or mx[1] < view.bounds[1] or mn[1] > view.bounds[3]:
            continue
        ps = shapely.polygons(T[:, :, :2].astype(float)); ps = ps[shapely.area(ps) > 1e-6]
        if len(ps):
            out[nm] = (shapely.union_all(shapely.buffer(ps, 0.005)).buffer(-0.005).simplify(0.02), float(zr[k][1]))
    return out


def patch(ax, g, **kw):
    for q in (g.geoms if hasattr(g, "geoms") else [g]):
        if q.geom_type != "Polygon" or q.area < 1e-4:
            continue
        v, c = [], []
        for ring in [q.exterior] + list(q.interiors):
            a = np.asarray(ring.coords); v += a.tolist(); c += [MPath.MOVETO] + [MPath.LINETO] * (len(a) - 2) + [MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(v, c), **kw))


def dims(g):
    c = np.asarray(g.minimum_rotated_rectangle.exterior.coords)[:4]
    e = [np.linalg.norm(c[(i + 1) % 4] - c[i]) for i in range(2)]
    return max(e), min(e)


def main(bp, ap, bb, rx, out, title):
    view = box(*[float(v) for v in bb.split(",")]); rx = re.compile(rx)
    B, A = load(bp, view), load(ap, view)
    w, h = view.bounds[2] - view.bounds[0], view.bounds[3] - view.bounds[1]
    fig, axs = plt.subplots(1, 2, figsize=(22, 22 * h / (2 * w) + 2))
    for ax, D, other, t in ((axs[0], B, A, "до"), (axs[1], A, B, "после")):
        for nm, (g, z) in D.items():
            mine = bool(rx.search(nm))
            changed = nm not in other or abs(other[nm][0].symmetric_difference(g).area) > 0.05
            patch(ax, g, fc=("#e8553e55" if changed else "#3a7bd544") if mine else "#cccccc", ec="#333" if mine else "#999", lw=0.5)
        seen = []
        for nm, (g, z) in sorted(D.items(), key=lambda t: -t[1][0].area):
            if not rx.search(nm) or SMALL.search(nm):
                continue
            L, W = dims(g)
            if L < 1.0 or g.area < 0.4:
                continue
            p = g.representative_point()
            if not view.contains(p) or any(p.distance(s) < 1.8 for s in seen):
                continue
            seen.append(p)
            short = re.sub(r"^GBS_[A-Za-z]+_", "", nm)[:20]
            ax.text(p.x, p.y, f"{short}\n{L:.1f}x{W:.1f} z{z:.2f}", fontsize=5.5, ha="center", va="center")
        ax.set_xlim(view.bounds[0], view.bounds[2]); ax.set_ylim(view.bounds[1], view.bounds[3]); ax.set_aspect("equal")
        ax.grid(alpha=0.2); ax.set_title(f"{title} — {t} (красный = изменено)")
        ax.plot([view.bounds[0] + 2, view.bounds[0] + 12], [view.bounds[1] + 1.5] * 2, "k-", lw=3); ax.text(view.bounds[0] + 7, view.bounds[1] + 2.2, "10 м", ha="center")
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig); print("saved", out)


if __name__ == "__main__":
    main(*sys.argv[1:7])
