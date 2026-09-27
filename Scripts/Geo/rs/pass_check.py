# One command per zone-pass check (R1 handoff section 3a "Token economy"): build (optional) -> route_check along the
# zone's walking clips -> pick_cams at the pass distance band -> sfm_overlay of the zone objects -> overlay_compose,
# then a short verdict (<= ~10 lines). Everything else goes to <work>/pass/<zone>_<pass>/ (logs, composites, json).
# Zone config (local paths, outside git): <work>/pass_zones.json
#   {"Gate": {"box": [x0,y0,z0,x1,y1,z1], "show": ["GBF_BLD_GateBooth", "GBS_Gate"], "clips": ["20260924_065910461"],
#             "models": [["zones/Gate/c8/model.json", "zones/Gate/c8/align.json"], ...]}}
# Pass thresholds (handoff section 0): P0 route 0.30 m >= 95 %; P1 route 0.07, overlay median <= 8 px; P2 route 0.04,
# median <= 3 px and p90 <= 8 px; P3 median <= 2 px.
# Usage: python pass_check.py <zone> <P0|P1|P2|P3> [--build] [--work C:/koch/work] [--cams 2]
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..", "..")
BLENDER = os.environ.get("BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
BLEND = os.path.join(REPO, "Art", "Blender", "KOCH_Campus_Greybox.blend")
PASS = {"P0": dict(tol=0.30, dist="15,150", med=None, p90=None), "P1": dict(tol=0.07, dist="8,80", med=8, p90=None),
        "P2": dict(tol=0.04, dist="2,15", med=3, p90=8), "P3": dict(tol=0.02, dist="0,5", med=2, p90=None)}


def run(cmd, log, env=None, cwd=None):
    with open(log, "w", encoding="utf-8", errors="ignore") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=cwd)
    return r.returncode, open(log, encoding="utf-8", errors="ignore").read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zone"); ap.add_argument("p", choices=list(PASS))
    ap.add_argument("--build", action="store_true"); ap.add_argument("--work", default=r"C:\koch\work")
    ap.add_argument("--cams", type=int, default=2)
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(a.work, "pass_zones.json"), encoding="utf-8"))[a.zone]
    th = PASS[a.p]; out = os.path.join(a.work, "pass", f"{a.zone}_{a.p}"); os.makedirs(out, exist_ok=True)
    verdict, ok_all = [], True
    if a.build:
        rc, txt = run([BLENDER, "-b", BLEND, "-P", os.path.join(REPO, "Scripts", "Blender", "build_all.py")], os.path.join(out, "build.log"))
        val = [l for l in txt.splitlines() if l.startswith("validate:")]
        verdict.append(f"build: exit {rc}, {val[-1] if val else 'no validate line'}"); ok_all &= rc == 0
    # levels along the walking routes
    route = os.path.join(a.work, "route", "route.json")
    if os.path.exists(route) and cfg.get("clips"):
        rc, txt = run([BLENDER, "-b", BLEND, "-P", os.path.join(REPO, "Scripts", "Blender", "route_check.py"), "--",
                       "--route", route, "--out", out, "--tol", str(th["tol"]), "--clips", ",".join(cfg["clips"])],
                      os.path.join(out, "route_check.log"))
        try:
            frac = float(json.load(open(os.path.join(out, "route_check.json")))["within_tol"])   # hit-weighted, all clips
        except Exception:
            frac = None
        ok = frac is not None and frac >= 0.95; ok_all &= ok
        verdict.append(f"route: {'n/a' if frac is None else f'{100 * frac:.0f} %'} within {th['tol']} m ({'ok' if ok else 'FAIL'}); log {out}\\route_check.log")
    else:
        verdict.append("route: no route.json or no clips for this zone (run route_profile.py)"); ok_all = False
    # overlays at the pass distance band
    if th["med"] is not None:
        box = ",".join(str(v) for v in cfg["box"]); worst = []
        for k, (mj, aj) in enumerate(cfg["models"]):
            mj, aj = os.path.join(a.work, mj), os.path.join(a.work, aj)
            rc, txt = run([sys.executable, os.path.join(HERE, "pick_cams.py"), mj, aj, "--box", box, "--n", str(a.cams), "--dist", th["dist"]],
                          os.path.join(out, f"pick_{k}.log"))
            cams = [l.strip() for l in txt.splitlines() if "," in l or l.strip().endswith(".jpg")][-1:] if rc == 0 else []
            if not cams:
                verdict.append(f"model {k}: no camera in the {th['dist']} m band"); continue
            ovl = os.path.join(out, f"ovl_{k}")
            env = dict(os.environ, KOCH_SFM_MODEL=mj, KOCH_SFM_ALIGN=aj, KOCH_SFM_OUT=ovl, KOCH_SFM_CAMS=cams[0],
                       KOCH_SFM_SHOW=",".join(cfg.get("show", [])))
            run([BLENDER, "-b", BLEND, "-P", os.path.join(REPO, "Scripts", "Blender", "sfm_overlay.py")], os.path.join(out, f"ovl_{k}.log"), env=env)
            run([sys.executable, os.path.join(HERE, "overlay_compose.py"), ovl, "--height", "1000"], os.path.join(out, f"compose_{k}.log"))
            try:
                for mt in json.load(open(os.path.join(ovl, "metrics.json"))):
                    worst.append((mt["median_px"], mt.get("p90_px", 0), mt["name"], ovl))
            except Exception:
                verdict.append(f"model {k}: overlay failed (see {ovl})")
        if worst:
            worst.sort(reverse=True)
            ok = all(m <= th["med"] and (th["p90"] is None or p <= th["p90"]) for m, p, _, _ in worst); ok_all &= ok
            verdict.append(f"overlay: {len(worst)} cameras, worst median {worst[0][0]:.1f} px p90 {worst[0][1]:.1f} ({'ok' if ok else 'FAIL'}, limit {th['med']} px)")
            verdict.append("look at: " + ", ".join(sorted({os.path.join(w[3], 'ovl_' + w[2]) for w in worst[:2]})))
        else:
            ok_all = False
    verdict.append(f"{a.zone} {a.p}: {'PASS' if ok_all else 'NOT PASSED'} (scripted part; your own review of the frames is still required)")
    print("\n".join(verdict))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
