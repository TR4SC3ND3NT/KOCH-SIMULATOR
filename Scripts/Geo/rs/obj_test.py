# Per-object overlay test (R1 handoff section 0 pass tests, one object at a time): for every object name prefix, its
# world bbox from the .blend, the best cameras of each placed component (pick_cams.py, pass distance band), a render
# of only that object over the frames (sfm_overlay.py, KOCH_SFM_SHOW) and the edge distances (overlay_compose.py).
# Prints one line per object: cameras, median / p90 px per camera, verdict for the pass limit. Frames with people or
# cars in front of the object score high p90; the median is the pass number (handoff: P1 median <= 8, P2 <= 3).
# Usage: python obj_test.py --objects GBF_BLD_GateBooth,GBS_Gate_GateCanopy --comps Gate/c13,Street/c2 [--pass P1]
#        [--work C:/koch/work] [--cams 2]
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..", "..")
BLENDER = os.environ.get("BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
BLEND = os.path.join(REPO, "Art", "Blender", "KOCH_Campus_Greybox.blend")
BANDS = {"P1": ("8,80", 8.0), "P2": ("2,15", 3.0), "P3": ("0,5", 2.0)}
BBOX_PY = r'''
import bpy, json, sys
from mathutils import Vector
pre = sys.argv[sys.argv.index("--") + 1].split(","); out = {}
for p in pre:
    bb = [o.matrix_world @ Vector(c) for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(p) for c in o.bound_box]
    if bb:
        out[p] = [min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb), max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)]
print("BBOX" + json.dumps(out))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", required=True); ap.add_argument("--comps", required=True)
    ap.add_argument("--pass", dest="p", default="P1", choices=list(BANDS)); ap.add_argument("--work", default=r"C:\koch\work")
    ap.add_argument("--cams", type=int, default=2)
    ap.add_argument("--dist", help="override the pass distance band (long objects: the walker is close to them)")
    a = ap.parse_args()
    band, limit = BANDS[a.p]
    band = a.dist or band
    tmp = os.path.join(tempfile.gettempdir(), "koch_bbox.py"); open(tmp, "w").write(BBOX_PY)
    r = subprocess.run([BLENDER, "-b", BLEND, "-P", tmp, "--", a.objects], capture_output=True, text=True)
    boxes = json.loads(next(l[4:] for l in r.stdout.splitlines() if l.startswith("BBOX")))
    res = {}
    for obj, bb in boxes.items():
        per = []
        for comp in a.comps.split(","):
            mj = os.path.join(a.work, "zones", comp, "model.json"); aj = os.path.join(a.work, "zones", comp, "align.json")
            if not os.path.exists(aj):
                continue
            pk = subprocess.run([sys.executable, os.path.join(HERE, "pick_cams.py"), mj, aj, "--box", ",".join(f"{v:.2f}" for v in bb),
                                 "--n", str(a.cams), "--dist", band], capture_output=True, text=True).stdout.strip().splitlines()
            cams = pk[-1] if pk and pk[-1].endswith(".jpg") else ""
            if not cams:
                continue
            out = os.path.join(a.work, "objtest", obj, comp.replace("/", "_"))
            env = dict(os.environ, KOCH_SFM_MODEL=mj, KOCH_SFM_ALIGN=aj, KOCH_SFM_OUT=out, KOCH_SFM_CAMS=cams, KOCH_SFM_SHOW=obj)
            subprocess.run([BLENDER, "-b", BLEND, "-P", os.path.join(REPO, "Scripts", "Blender", "sfm_overlay.py")], env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([sys.executable, os.path.join(HERE, "overlay_compose.py"), out, "--height", "900"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                for mt in json.load(open(os.path.join(out, "metrics.json"))):
                    per.append((comp, mt["name"][-10:-4], mt["median_px"], mt.get("p90_px", 0)))
            except Exception:
                pass
        res[obj] = per
        if per:
            meds = sorted(m for _, _, m, _ in per)
            ok = sum(m <= limit for m in meds) >= 2
            print(f"{obj}: {len(per)} cams, median px {', '.join(f'{c}:{n} {m:.1f}' for c, n, m, _ in per)} -> {a.p} {'ok' if ok else 'FAIL'} (>= 2 cams <= {limit:.0f} px)")
        else:
            print(f"{obj}: no placed camera in the {band} m band")
    json.dump(res, open(os.path.join(a.work, "objtest", f"result_{a.p}.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
