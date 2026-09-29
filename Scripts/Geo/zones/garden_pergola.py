# South pergola of the garden (R1, SITE_Garden.json): east start, arch pitch and the benches/bins under it, from the
# owner clip 081904575 t6.0-t7.5 (camera at the stair foot looking west): the first arch stands 5.6 rows of 0.40 m
# diamond tiles (2.25 m) west of the herringbone/diamond joint at the walk's east end; arch legs projected with the tile
# rows (1D projective fit, horizon row 380, K 4000 px*m) are 2.2-2.6 m apart -> pitch 2.4 m; benches stand in every
# second bay starting with the 2nd bay from the east (1.5 m bench centred in a 2.4 m bay, t7.0), a wrought-iron bin
# just west of the first arch against the wall. Run: uv run --project Scripts python Scripts/Geo/zones/garden_pergola.py
import json
import math
import os

SPEC = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Art", "Blender", "Specs", "SITE_Garden.json")
FIRST_ARCH = 2.25      # m west of the walk's east end (diamond-tile start)
PITCH = 2.4            # m between arches
BENCH_OFF, BIN_OFF = 0.70, 0.82   # m from the pergola centre line toward the boulder wall (kept from the 2026-09-28 layout)
EV = "owner clip 081904575 t6.0-7.5 (2026-09-29 measure, garden_pergola.py): first arch 2.25 m west of the walk end, pitch 2.4 m, benches in every 2nd bay"


def main():
    d = json.load(open(SPEC))
    E = d["elements"]
    by = {e["name"]: e for e in E}
    per, walk = by["Pergola_South"], by["PergolaWalk_South"]
    A = per["line"][0]
    B0 = per["line"][1]
    L0 = math.dist(A, B0)
    ux, uy = (B0[0] - A[0]) / L0, (B0[1] - A[1]) / L0      # west -> east
    t_end = (walk["line"][1][0] - A[0]) * ux + (walk["line"][1][1] - A[1]) * uy
    L = t_end - FIRST_ARCH
    per["line"][1] = [round(A[0] + ux * L, 3), round(A[1] + uy * L, 3)]
    per["pitch"] = PITCH
    n = max(1, round(L / PITCH))
    per["evidence"] = per.get("evidence", "").split(" | owner clip 081904575 t6.0-7.5")[0] + f" | {EV}: {n + 1} arches, {L / n:.3f} m apart"
    nx, ny = uy, -ux                                         # right of west->east = south = toward the wall
    at = lambda s, off: [round(A[0] + ux * (L - s) + nx * off, 3), round(A[1] + uy * (L - s) + ny * off, 3)]
    pitch = L / n
    # benches: bays counted from the east arch (s = 0); bench bays 2, 4, 6, ... (1-based)
    tmpl = dict(by["Bench_Pergola_2"])
    old_b = [e for e in E if e["name"].startswith("Bench_Pergola_")]
    bays = [k for k in range(1, n) if k % 2 == 1]            # bay k spans arches k..k+1 (0-based) -> 2nd, 4th, ...
    benches = [dict(tmpl, name=f"Bench_Pergola_{i}", pos=at((k + 0.5) * pitch, BENCH_OFF),
                    evidence=tmpl.get("evidence", "").split(" | owner clip 081904575 t6.0-7.5")[0] + " | " + EV)
               for i, k in enumerate(bays)]
    # bins: one just west of the first arch; the others in the nearest bench-free bay to where they stood
    btm = dict(by["Bin_Pergola_125"])
    old_bins = [e for e in E if e["name"].startswith("Bin_Pergola_")]
    free = [k for k in range(n) if k not in bays]
    bins = [dict(btm, name="Bin_Pergola_East", pos=at(0.8, BIN_OFF), evidence=EV + ": bin just west of the first arch (t7.0)")]
    for b in old_bins:
        s_old = L - ((b["pos"][0] - A[0]) * ux + (b["pos"][1] - A[1]) * uy)
        k = min((k for k in free if k > 0), key=lambda k: abs((k + 0.5) * pitch - s_old))
        free.remove(k)
        bins.append(dict(b, pos=at((k + 0.5) * pitch, BIN_OFF), evidence=b.get("evidence", "").split(" | owner clip")[0] + " | " + EV))
    drop = {e["name"] for e in old_b + old_bins}
    i = next(k for k, e in enumerate(E) if e["name"] in drop)
    E = [e for e in E if e["name"] not in drop]
    E[i:i] = benches + bins
    d["elements"] = E
    json.dump(d, open(SPEC, "w"), indent=1, ensure_ascii=False)
    print(f"pergola: east arch at {per['line'][1]}, {n + 1} arches every {pitch:.3f} m over {L:.2f} m; benches {len(benches)}, bins {len(bins)}")


if __name__ == "__main__":
    main()
