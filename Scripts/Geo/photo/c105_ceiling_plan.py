# Top-view plan of classroom C105 (R1 reference for the block C interior): walls, corner pilasters, bulkheads/beam,
# ceiling tile layout, door and windows, all dimensions. Writes a PNG for the owner. Values in metres.
# v6 (2026-10-01): one consistent scale from 4 independent checks: the door opening 1.98 x 0.92 by the 185 cm person
# (C204 photos 021/025-027), the 0.600 tile pitch (C204 014, C105 150/151/152/153: steps 0.596-0.603), the 70" TV
# (1.575 x 0.870 on 153) and the laminate boards (0.19). Single-view metrology (Criminisi et al. 2000) per photo:
# LSD segments -> vanishing points -> calibrated camera, wall planes from the bulkhead/beam edges.
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

T = 0.60
L, W = 5.77, 6.34          # back wall -> board wall (151: 5.765, 150: 5.74), window -> door wall (153: 6.338)
# along x (back -> board wall): back bulkhead, cut, 8 full, cut (151/150 seams; 152 agrees on the board end)
B_BACK, CUT_BACK, N_X, CUT_FRONT = 0.18, 0.27, 8, 0.52
# along y (door -> window wall): door-wall bulkhead (151 0.275, 150 0.26, 153 0.287), cut 0.16, 9 full, window beam 0.50
B_DOOR, CUT_DOOR, N_Y, B_WIN = 0.28, 0.16, 9, 0.50
H_GRID, H_DOORBOX, H_BEAM = 2.89, 2.66, 2.69   # grid (151 2.90, 153 2.90, 150 2.87); undersides of the door box / window beam
DOOR_X0, DOOR_W, DOOR_H = L - 0.45 - 0.92, 0.92, 1.98   # opening (wall face) 0.45 m from the board-wall corner (151)
WINDOWS = [(0.63, 2.60), (3.24, 5.25)]          # wall-face reveal edges (152, referenced to the board wall)
WIN_SILL, WIN_HEAD = 1.12, 2.54
PILASTERS = [(0, 0, 0.15, 0.25, "0.15×0.25"),                    # back/door corner (150/151)
             (0, W - 0.50, 0.25, 0.50, "0.25×0.50"),             # back/window corner, flush with the beam (152)
             (L - 0.09, W - 0.58, 0.09, 0.58, "0.09×0.58")]      # board/window corner (153)


def main(out):
    fig, ax = plt.subplots(figsize=(15, 14))
    ax.add_patch(Rectangle((0, 0), L, W, fc="#d9e8d2", ec="k", lw=3))
    ax.add_patch(Rectangle((0, 0), L, B_DOOR, fc="#f3d9a4", ec="#a0701a", lw=1))
    ax.add_patch(Rectangle((0, 0), B_BACK, W, fc="#f3d9a4", ec="#a0701a", lw=1))
    ax.add_patch(Rectangle((0, W - B_WIN), L, B_WIN, fc="#e8b4a0", ec="#9a4a2a", lw=1))
    xs = [B_BACK, B_BACK + CUT_BACK] + [B_BACK + CUT_BACK + T * k for k in range(1, N_X + 1)] + [L]
    ys = [B_DOOR, B_DOOR + CUT_DOOR] + [B_DOOR + CUT_DOOR + T * k for k in range(1, N_Y + 1)]
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            w, h = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
            full = abs(w - T) < 1e-6 and abs(h - T) < 1e-6
            ax.add_patch(Rectangle((xs[i], ys[j]), w, h, fc="white" if full else "#dfe7f2", ec="#7a8a9a", lw=0.8))
    ax.add_patch(Rectangle((xs[0], ys[0]), xs[-1] - xs[0], ys[-1] - ys[0], fill=False, ec="#1b4f8a", lw=2))
    for x, y, w, h, lab in PILASTERS:
        ax.add_patch(Rectangle((x, y), w, h, fc="#555", ec="k", lw=1, hatch="///"))
        ax.text(x + w + 0.04, y + h / 2, f"пилястра {lab}", fontsize=8, va="center", color="#333")
    ax.add_patch(Rectangle((DOOR_X0, -0.06), DOOR_W, 0.12, fc="white", ec="white"))
    ax.plot([DOOR_X0, DOOR_X0 + DOOR_W], [0, 0], color="#c0392b", lw=4)
    ax.text(DOOR_X0 + DOOR_W / 2, -0.12, f"ПРОЁМ {DOOR_W:.2f} × {DOOR_H:.2f} (выс.)", ha="center", va="top", fontsize=10, color="#c0392b")
    for a, b in WINDOWS:
        ax.plot([a, b], [W, W], color="#2e86c1", lw=6)
        ax.text((a + b) / 2, W + 0.08, f"окно {b - a:.2f}, низ {WIN_SILL:.2f}, верх {WIN_HEAD:.2f}", ha="center", fontsize=9, color="#2e86c1")

    def dim(p, q, off, txt, vert=False, col="k", fs=10, nudge=0.0):   # nudge: extra text offset so short labels don't collide
        if vert:
            ax.annotate("", (off, p), (off, q), arrowprops=dict(arrowstyle="<->", color=col, lw=1.2))
            ax.text(off - 0.06 - nudge, (p + q) / 2, txt, rotation=90, ha="right", va="center", fontsize=fs, color=col)
        else:
            ax.annotate("", (p, off), (q, off), arrowprops=dict(arrowstyle="<->", color=col, lw=1.2))
            ax.text((p + q) / 2, off - 0.05 - nudge, txt, ha="center", va="top", fontsize=fs, color=col)
    chain_x = [0] + xs
    for k, (a, b) in enumerate(zip(chain_x[:-1], chain_x[1:])):
        dim(a, b, -0.55, f"{b - a:.2f}" if abs(b - a - T) > 1e-6 else f"{T:.2f}", col="#1b4f8a", fs=9, nudge=0.15 * (k % 2) * (b - a < 0.35))
    chain_y = [0] + ys + [W]
    for k, (a, b) in enumerate(zip(chain_y[:-1], chain_y[1:])):
        dim(a, b, -0.3, f"{b - a:.2f}" if abs(b - a - T) > 1e-6 else f"{T:.2f}", vert=True, col="#1b4f8a", fs=9, nudge=0.15 * (k % 2) * (b - a < 0.35))
    dim(0, L, -1.0, f"КЛАСС вдоль окон {L:.2f} м  (короб {B_BACK:.2f} + {CUT_BACK:.2f} + {N_X}×0.60 + {CUT_FRONT:.2f})")
    dim(0, W, -0.85, f"КЛАСС от двери до окон {W:.2f} м  (короб {B_DOOR:.2f} + {CUT_DOOR:.2f} + {N_Y}×0.60 + балка {B_WIN:.2f})", vert=True)
    dim(DOOR_X0 + DOOR_W, L, 0.45, "0.45", col="#c0392b", fs=9)
    ax.text(L / 2, W - B_WIN / 2, f"балка у окон {B_WIN:.2f} м, низ {H_BEAM:.2f} (опущена на {H_GRID - H_BEAM:.2f})",
            ha="center", va="center", fontsize=11, color="#6a2a10")
    ax.text(L / 2 + 0.6, B_DOOR / 2, f"короб у стены с дверью {B_DOOR:.2f} м, низ {H_DOORBOX:.2f} (опущен на {H_GRID - H_DOORBOX:.2f})",
            ha="center", va="center", fontsize=9, color="#6a4a10")
    ax.text(B_BACK / 2, W / 2, f"короб сзади {B_BACK:.2f} м (низ ≈{H_DOORBOX:.2f})", rotation=90, ha="center", va="center",
            fontsize=9, color="#6a4a10")
    ax.text(L - 0.06, W / 2 - 0.4, "стена с доской: короба нет\nТВ 70″ 1.58×0.87, доска 1.8×1.2", rotation=90, ha="right",
            va="center", fontsize=9)
    area = L * W - sum(p[2] * p[3] for p in PILASTERS)
    vol = area * H_GRID - (B_DOOR * (H_GRID - H_DOORBOX) * L + B_BACK * (H_GRID - H_DOORBOX) * (W - B_DOOR - B_WIN)
                           + B_WIN * (H_GRID - H_BEAM) * L)
    ax.text((xs[0] + xs[-1]) / 2, (ys[0] + ys[-1]) / 2,
            f"потолок (сетка) {H_GRID:.2f} м от пола\nплощадь пола {area:.1f} м²\nпериметр {2 * (L + W):.2f} м\nобъём ≈{vol:.0f} м³\n\n"
            f"белые = целые 0.60×0.60\nголубые = подрезанные", ha="center", va="center", fontsize=13, color="#1b4f8a",
            bbox=dict(fc="white", ec="#1b4f8a", alpha=0.92))
    ax.text(L / 2, -1.45, "СТЕНА С ДВЕРЬЮ (коридор)", ha="center", fontsize=11)
    ax.text(-1.35, W / 2, "ЗАДНЯЯ\nСТЕНА", ha="center", va="center", fontsize=11)
    ax.text(L + 0.35, W / 2, "ДОСКА", ha="center", va="center", fontsize=11, rotation=90)
    ax.text(L / 2, W + 0.35, "ОКНА", ha="center", fontsize=11)
    # door elevation inset
    ia = fig.add_axes([0.80, 0.08, 0.13, 0.22]); ia.set_aspect("equal"); ia.axis("off")
    ia.add_patch(Rectangle((-0.25, 0), DOOR_W + 0.5, 2.3, fc="#eee", ec="none"))
    ia.add_patch(Rectangle((0, 0), DOOR_W, DOOR_H, fc="white", ec="#c0392b", lw=2))
    ia.annotate("", (0, DOOR_H + 0.1), (DOOR_W, DOOR_H + 0.1), arrowprops=dict(arrowstyle="<->", lw=1))
    ia.text(DOOR_W / 2, DOOR_H + 0.13, f"{DOOR_W:.2f}", ha="center", va="bottom", fontsize=9)
    ia.annotate("", (DOOR_W + 0.12, 0), (DOOR_W + 0.12, DOOR_H), arrowprops=dict(arrowstyle="<->", lw=1))
    ia.text(DOOR_W + 0.16, DOOR_H / 2, f"{DOOR_H:.2f}", rotation=90, va="center", fontsize=9)
    ia.text(DOOR_W / 2, -0.12, "проём: пол → белый верх", ha="center", va="top", fontsize=8)
    ia.set_xlim(-0.3, DOOR_W + 0.4); ia.set_ylim(-0.35, 2.5)
    ax.set_title("C105 — план сверху, v6: масштаб по проёму 1.98 (рост 185) = плитка 0.600 = ТВ 70″; длины ±3 см, высоты ±2 см",
                 fontsize=13)
    ax.set_xlim(-1.7, L + 0.8); ax.set_ylim(-1.7, W + 0.6); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print(out, f"room {L:.2f} x {W:.2f}, area {area:.2f}, volume {vol:.1f}")


if __name__ == "__main__":
    main(sys.argv[1])
