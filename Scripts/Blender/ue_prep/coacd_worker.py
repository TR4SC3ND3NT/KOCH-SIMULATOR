# Offline convex decomposition for ue_prep (called by run.py, outside Blender's python):
#   uv run --project Scripts --with coacd python -I Scripts/Blender/ue_prep/coacd_worker.py JOBS.json
# JOBS.json = {"params": {...}, "workers": N, "timeout": s, "jobs": [{"key", "obj", "out"}, ...]}. Every mesh runs in
# its own child process (CoACD can abort() or spin on odd input, which would take a shared pool down), N at a time;
# a crash or 30 s timeout with preprocess "off" (fast, exact for closed manifolds) is retried once with "on"
# (manifold remesh) and the JOBS timeout.
# Each result: {"hulls": [{"v": [[x,y,z]...], "t": [[i,j,k]...]}...], "secs": s} or {"error": msg}.
# CoACD: github.com/SarahWeiii/CoACD (MIT), Wei et al. 2022 "Approximate Convex Decomposition for 3D Meshes with
# Collision-Aware Concavity and Tree Search".
import json
import os
import subprocess
import sys
import time


def read_obj(path):
    import numpy as np
    v, f = [], []
    with open(path) as fh:
        for line in fh:
            if line.startswith("v "):
                v.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("f "):
                f.append([int(x.split("/")[0]) - 1 for x in line.split()[1:4]])
    return np.array(v, np.float64), np.array(f, np.int32)


def run_one(obj, out, params):
    import coacd
    coacd.set_log_level("error")
    t0 = time.time()
    v, f = read_obj(obj)
    parts = coacd.run_coacd(coacd.Mesh(v, f), **params)
    res = {"hulls": [{"v": [list(map(float, p)) for p in hv], "t": [list(map(int, t)) for t in ht]}
                     for hv, ht in parts], "secs": round(time.time() - t0, 2)}
    with open(out, "w") as fh:
        json.dump(res, fh)


def _fail(out, msg):
    with open(out, "w") as fh:
        json.dump({"error": msg}, fh)


def main():
    if sys.argv[1] == "--one":
        run_one(sys.argv[2], sys.argv[3], json.loads(sys.argv[4]))
        return
    with open(sys.argv[1]) as fh:
        spec = json.load(fh)
    jobs, nw = list(spec["jobs"]), spec.get("workers", 2)
    tries = [(json.dumps(dict(spec["params"], preprocess_mode=m)), t) for m, t in (("off", 30),
                                                                                    ("on", spec.get("timeout", 180)))]
    env = dict(os.environ, OMP_NUM_THREADS="2")   # per child; the laptop is shared with the user's editor
    running, done = [], 0
    while jobs or running:
        while jobs and len(running) < nw:
            j = jobs.pop(0)
            params, _ = tries[j.get("try", 0)]
            if os.path.exists(j["out"]):
                os.remove(j["out"])
            errf = open(j["out"] + ".err", "w+b")   # a file, not a pipe: a chatty child can never block
            p = subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "--one", j["obj"], j["out"],
                                  params], env=env, stdout=subprocess.DEVNULL, stderr=errf)
            running.append((p, j, time.time(), errf))
        time.sleep(0.05)
        for item in list(running):
            p, j, t0, errf = item
            rc = p.poll()
            if rc is None and time.time() - t0 < tries[j.get("try", 0)][1]:
                continue
            if rc is None:
                p.kill()
                p.wait()
                rc = "timeout"
                _fail(j["out"], "timeout")
            elif rc != 0 or not os.path.exists(j["out"]):
                errf.seek(0)
                err = errf.read().decode("utf-8", "replace").strip().splitlines()
                _fail(j["out"], f"exit {rc}: {err[-1] if err else ''}")
            errf.close()
            os.remove(j["out"] + ".err")
            running.remove(item)
            if rc not in (0, None) and j.get("try", 0) + 1 < len(tries):
                jobs.append(dict(j, **{"try": j.get("try", 0) + 1}))
                continue
            done += 1
            with open(j["out"]) as fh:
                r = json.load(fh)
            print(f"coacd {done}/{len(spec['jobs'])} {j['key'][:10]} hulls={len(r.get('hulls', []))} "
                  f"{r.get('secs', '')}s {r.get('error', '')}", flush=True)


if __name__ == "__main__":
    main()
