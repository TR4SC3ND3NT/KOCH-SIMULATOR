# Reflected ceiling plan of room C105 (R1, 2026-09-30 measurements from grid_rectify.py + photo zooms): tile grid with
# cut tiles, perimeter bulkheads/beam, all dimensions. Writes a PNG for the owner. Values in metres.
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Door scale (owner 2026-10-01): the 187 cm person gives the C204 door frame 2.12 m; the tile-scaled door is 1.88 (C105
# photo 151 and C204 photo 014 alike) -> every length x K. The grid module is then 0.60 * K = 0.677 m (to verify on site).
K = 1.0   # v5: the owner phone-measured door profile (13.3-14.3 cm = 167 px) confirms the 0.60 tile scale (predicts 13.9 cm); the person-based K = 2.12 / 1.88 was wrong
T = 0.60 * K
# v2 (single-view metrology, room_svm.py: vanishing points + 0.60 m grid crossings on 3 photos, floor check at the door)
CUT_BACK, CUT_FRONT, N_ALONG = 0.25 * K, 0.50 * K, 8          # along the windows: back wall -> front (board) wall (photo 151: steps 0.600±0.002)
CUT_COR, CUT_WIN, N_ACROSS = 0.142 * K, 0.0, 9            # across: corridor (door) wall -> window wall (photo 153)
B_BACK, B_COR, B_WIN, B_FRONT = 0.24 * K, 0.31 * K, 0.28 * K, 0.0   # bulkhead / beam widths in plan (back: photo 152 corner)
H_GRID, H_WIN, H_COR, H_BACK = 2.795 * K, 2.58 * K, 2.575 * K, 2.6 * K  # heights above the floor


def main(out):
    gx = CUT_BACK + N_ALONG * T + CUT_FRONT
    gy = CUT_COR + N_ACROSS * T + CUT_WIN
    X0, Y0 = -B_BACK, -B_COR
    X1, Y1 = gx + B_FRONT, gy + B_WIN
    fig, ax = plt.subplots(figsize=(15, 14))
    ax.add_patch(Rectangle((X0, Y0), X1 - X0, Y1 - Y0, fc="#d9e8d2", ec="k", lw=2.5))      # room outline (walls)
    ax.add_patch(Rectangle((X0, Y0), X1 - X0, B_COR, fc="#f3d9a4", ec="#a0701a", lw=1))
    ax.add_patch(Rectangle((X0, Y0), B_BACK, Y1 - Y0, fc="#f3d9a4", ec="#a0701a", lw=1))
    ax.add_patch(Rectangle((X0, gy), X1 - X0, B_WIN, fc="#e8b4a0", ec="#9a4a2a", lw=1))
    xs = [0] + ([CUT_BACK] if CUT_BACK > 0 else []) + [CUT_BACK + T * k for k in range(1, N_ALONG + 1)] + ([gx] if CUT_FRONT > 0 else [])
    ys = [0] + ([CUT_COR] if CUT_COR > 0 else []) + [CUT_COR + T * k for k in range(1, N_ACROSS + 1)] + ([gy] if CUT_WIN > 0 else [])
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            w, h = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
            full = abs(w - T) < 1e-6 and abs(h - T) < 1e-6
            ax.add_patch(Rectangle((xs[i], ys[j]), w, h, fc="white" if full else "#dfe7f2", ec="#7a8a9a", lw=0.8))
    ax.add_patch(Rectangle((0, 0), gx, gy, fill=False, ec="#1b4f8a", lw=2))
    def dim(p, q, off, txt, vert=False, col="k"):
        if vert:
            ax.annotate("", (off, p), (off, q), arrowprops=dict(arrowstyle="<->", color=col, lw=1.2))
            ax.text(off - 0.06, (p + q) / 2, txt, rotation=90, ha="right", va="center", fontsize=10, color=col)
        else:
            ax.annotate("", (p, off), (q, off), arrowprops=dict(arrowstyle="<->", color=col, lw=1.2))
            ax.text((p + q) / 2, off - 0.05, txt, ha="center", va="top", fontsize=10, color=col)
    # tile chain along (below the room) and across (left of the room)
    for a, b in zip(xs[:-1], xs[1:]):
        dim(a, b, Y0 - 0.25, f"{b - a:.2f}" if abs(b - a - T) > 1e-6 else f"{T:.3f}", col="#1b4f8a")
    for a, b in zip(ys[:-1], ys[1:]):
        dim(a, b, X0 - 0.25, f"{b - a:.2f}" if abs(b - a - T) > 1e-6 else f"{T:.3f}", vert=True, col="#1b4f8a")
    dim(0, gx, Y0 - 0.75, f"плитки: {gx:.2f} м  ({CUT_BACK:.2f} + {N_ALONG}×{T:.3f} + {CUT_FRONT:.2f})", col="#1b4f8a")
    dim(0, gy, X0 - 0.75, f"плитки: {gy:.2f} м  ({CUT_COR:.2f} + {N_ACROSS}×{T:.3f})", vert=True, col="#1b4f8a")
    dim(X0, X1, Y1 + 0.55, f"КЛАСС вдоль окон ≈ {X1 - X0:.2f} м", col="k")
    dim(Y0, Y1, X1 + 0.55, f"КЛАСС от двери до окон ≈ {Y1 - Y0:.2f} м", vert=True, col="k")
    dim(X0, 0, Y1 + 0.2, f"{B_BACK:.2f}", col="#a0701a")
    ax.text(X1 / 2, gy + B_WIN / 2, f"балка у окон {B_WIN:.2f} м, опущена на {0.21 * K:.2f} м → под ней {H_WIN:.2f} м",
            ha="center", va="center", fontsize=11, color="#6a2a10")
    ax.text(X1 / 2, Y0 + B_COR / 2, f"короб у стены с дверью {B_COR:.2f} м, опущен на {0.22 * K:.2f} м → под ним {H_COR:.2f} м",
            ha="center", va="center", fontsize=9, color="#6a4a10")
    ax.text(X0 + B_BACK / 2, gy / 2, f"короб сзади {B_BACK:.2f} м", rotation=90, ha="center", va="center",
            fontsize=9, color="#6a4a10")
    ax.text(gx + 0.08, gy / 2, f"передняя стена: короба нет, плитка до стены\nТВ {1.56*K:.2f}×{0.90*K:.2f}, доска {1.78*K:.2f}×{1.24*K:.2f}", rotation=90, ha="left",
            va="center", fontsize=9)
    ax.text(gx / 2, gy / 2, f"потолок из плиток\nвысота {H_GRID:.2f} м от пола\n\nбелые = целые {T:.3f}×{T:.3f}\nголубые = подрезанные",
            ha="center", va="center", fontsize=13, color="#1b4f8a",
            bbox=dict(fc="white", ec="#1b4f8a", alpha=0.9))
    ax.text(X1 / 2, Y1 + 0.2, f"ОКНА (2 шт, {1.83 * K:.2f} и {1.88 * K:.2f} м)", ha="center", fontsize=11)
    ax.text(X1 / 2, Y0 - 1.25, "СТЕНА С ДВЕРЬЮ (коридор); дверь по раме ≈0.9 × 1.88 м", ha="center", fontsize=11)
    ax.text(X0 - 1.25, Y1 / 2, "ЗАДНЯЯ\nСТЕНА", ha="center", va="center", fontsize=11)
    ax.text(X1 + 1.0, Y1 / 2, "ДОСКА", ha="center", va="center", fontsize=11, rotation=90)
    ax.set_title("C105 — потолок сверху, v5: плитка 0.60 подтверждена замером двери телефоном (профиль 13.3–14.3 см); ±6 см", fontsize=13)
    ax.set_xlim(X0 - 1.6, X1 + 1.5); ax.set_ylim(Y0 - 1.5, Y1 + 0.9); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print(out, f"grid {gx:.3f} x {gy:.3f}, room {X1 - X0:.2f} x {Y1 - Y0:.2f}")


if __name__ == "__main__":
    main(sys.argv[1])
