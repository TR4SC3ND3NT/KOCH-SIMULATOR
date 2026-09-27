# Zone-to-zone joins through shared frames (R1 pass P0, handoff section 4.2 "shared frames first"): the zones were
# aligned separately in RealityScan, but a walking clip that crosses two zones puts the same frame names into
# components of both. For every component pair with >= --min shared frames: similarity from the shared camera poses
# (rotation from the orientations, scale + translation from the centres, robust; pair_merge.fit) and the residual.
# Then the world pose spreads from the anchored components (those with an align.json whose "frame" starts with
# "world") over the graph, strongest links first; each new pose gets REG = residual of the shared centres in metres.
# Writes <comp>/align_graph.json (never overwrites a hand/anchor align.json) and prints one line per link used.
# Usage: python comp_graph.py [--work C:/koch/work] [--min 8] [--write]
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pair_merge import fit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=r"C:\koch\work"); ap.add_argument("--min", type=int, default=8)
    ap.add_argument("--write", action="store_true", help="write align_graph.json for the reached components")
    a = ap.parse_args()
    comps = {}
    for mj in glob.glob(os.path.join(a.work, "zones", "*", "c*", "model.json")):
        key = os.path.relpath(os.path.dirname(mj), os.path.join(a.work, "zones")).replace("\\", "/")
        if key.startswith("ALL/"):
            continue                       # whole-site alignment: not a zone (handoff 4.2)
        cams = json.load(open(mj))["cameras"]
        comps[key] = {os.path.basename(c["name"]): (np.array(c["R"]), np.array(c["center"])) for c in cams}
    keys = sorted(comps); links = []
    for i, p in enumerate(keys):
        for q in keys[i + 1:]:
            sh = sorted(set(comps[p]) & set(comps[q]))
            if len(sh) < a.min:
                continue
            Ra = [comps[p][n][0] for n in sh]; Ca = np.array([comps[p][n][1] for n in sh])
            Rb = [comps[q][n][0] for n in sh]; Cb = np.array([comps[q][n][1] for n in sh])
            s, R, t, r, keep, ang = fit(Ra, Ca, Rb, Cb)          # x_q = s R x_p + t
            links.append((len(sh), p, q, s, R, t, r, keep, ang))
    print(f"{len(comps)} components, {len(links)} links with >= {a.min} shared frames")
    # anchors: world aligns
    pose = {}
    for k in keys:
        aj = os.path.join(a.work, "zones", k, "align.json")
        if os.path.exists(aj):
            al = json.load(open(aj))
            if str(al.get("frame", "")).startswith("world"):
                pose[k] = (al["scale"], np.array(al["R"]), np.array(al["t"]), "anchor")
    print("anchors:", ", ".join(sorted(pose)) or "none")
    links.sort(key=lambda l: -l[0]); changed = True
    while changed:
        changed = False
        for n, p, q, s, R, t, r, keep, ang in links:
            for src, dst, fwd in ((p, q, True), (q, p, False)):
                if src in pose and dst not in pose:
                    S, Rw, tw, _ = pose[src]
                    # world = S Rw x_src + tw ; x_q = s R x_p + t
                    if fwd:     # src = p, dst = q: x_p = R^T (x_q - t) / s
                        S2 = S / s; R2 = Rw @ R.T; t2 = tw - S2 * (R2 @ t)
                    else:       # src = q, dst = p: x_q = s R x_p + t
                        S2 = S * s; R2 = Rw @ R; t2 = S * (Rw @ t) + tw
                    reg = float(np.sqrt((r[keep] ** 2).mean()) * (S if not fwd else S / s))
                    pose[dst] = (S2, R2, t2, f"via {src} ({n} shared, REG {reg:.2f} m, rot {ang:.1f} deg)")
                    print(f"  {dst:<14} <- {src:<14} {n:4d} shared  REG {reg:5.2f} m  rot {ang:4.1f} deg {'ok' if reg <= 0.30 and ang < 2 else 'CHECK'}")
                    changed = True
    for k, (S, Rw, tw, how) in sorted(pose.items()):
        if how == "anchor" or not a.write:
            continue
        json.dump({"scale": float(S), "R": Rw.tolist(), "t": tw.tolist(), "frame": "world (graph)",
                   "note": f"comp_graph.py: {how}"}, open(os.path.join(a.work, "zones", k, "align_graph.json"), "w"), indent=1)
    unreached = [k for k in keys if k not in pose]
    print(f"reached {len(pose)}/{len(keys)}; not reached: {len(unreached)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
