# One zone of the R1 photogrammetry queue (run by C:\koch\work\gpu_queue.ps1, one step per call, one RealityScan
# instance at a time). A zone is C:\koch\work\zones\<id>\job.json:
#   {"clips": ["20260924_070647586", ...],          frame folders under frames_root (adaptive frames + masks)
#    "photos": ["p20260925/PXL_20260925_0124*.jpg"],  globs under photos_root (masks next to them if present)
#    "min_cams": 25, "mesh_comps": 2, "detail": "high", "simplify": 20000000}
# Steps (each writes zones/<id>/<step>.ok when it finished; the queue skips finished steps after a restart):
#   prep   hard-link the images and masks into zones/<id>/imgs/<clip>/ (RealityScan picks masks up by name)
#   align  RealityScan: per-clip prior lens + calibration group, align, save <id>.rsproj, overview report
#   merge  mergeComponents + re-align with High overlap (joins clips filmed at other times of day)
#   cams   per component with >= min_cams images: registration CSV, COLMAP (undistorted), sparse cloud, model.json
#   mesh   largest mesh_comps components: region box from the sparse cloud near the cameras, model, simplify, OBJ
# Every RealityScan run is headless with appQuitOnError=true and a hard timeout (process tree killed on expiry).
# Usage: python zone_job.py <step> <id> [--work C:/koch/work]
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

import numpy as np

RS = os.environ.get("REALITYSCAN", r"C:\Program Files\Epic Games\RealityScan_2.2\RealityScan.exe")
REPORTS = os.path.join(os.path.dirname(RS), "Reports")
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
FORMATS = {  # (desc, id, undistort, images) from <RealityScan>/calibration.xml
    "csv": ("Internal/External camera parameters", "{0CA18733-1EBC-4254-9974-17197EB409BD}", "-1", "-1"),
    "colmap": ("COLMAP", "{280B11A4-F9A3-47D1-AE58-C0DEA33487D8}", "1", "1"),
}
_REG = """<Configuration id="{{2D5793BC-A65D-4318-A1B9-A05044608385}}">
  <entry key="calexTrans" value="1"/>
  <entry key="calexHasDisabled" value="0x0"/>
  <entry key="MvsExportScaleX" value="1.0"/>
  <entry key="MvsExportScaleY" value="1.0"/>
  <entry key="MvsExportScaleZ" value="1.0"/>
  <entry key="MvsExportIsGeoreferenced" value="0x0"/>
  <entry key="MvsExportIsModelCoordinates" value="0"/>
  <entry key="MvsExportRotationX" value="0.0"/>
  <entry key="MvsExportRotationY" value="0.0"/>
  <entry key="MvsExportRotationZ" value="0.0"/>
  <entry key="MvsExportMoveX" value="0.0"/>
  <entry key="MvsExportMoveY" value="0.0"/>
  <entry key="MvsExportMoveZ" value="0.0"/>
  <entry key="MvsExportcoordinatesystemtype" value="0"/>
  <entry key="hasCalexFilePath" value="1"/>
  <entry key="hasCalexFileName" value="1"/>
  <entry key="calexHasUndistort" value="{undist}"/>
  <entry key="calexHasImageExport" value="{images}"/>
  <entry key="calexFileFormat" value="{name}"/>
  <entry key="calexFileFormatId" value="{fid}"/>
</Configuration>
"""
BOX = """<ReconstructionRegion globalCoordinateSystem="NONE" globalCoordinateSystemWkt="NONE" globalCoordinateSystemName="NONE"
   isGeoreferenced="0" isLatLon="0" yawPitchRoll="0 -0 -0" widthHeightDepth="{w} {h} {d}">
  <Header magic="5395016" version="2"/>
  <CentreEuclid>
    <centre>{cx} {cy} {cz}</centre>
  </CentreEuclid>
  <Residual R="1 0 0 0 1 0 0 0 1" t="0 0 0" s="1" ownerId="{{A514E61A-E75B-4DE5-B2CE-D289FB86277C}}"/>
</ReconstructionRegion>
"""


def q(s):
    return f'"{s}"'


def jload(path):
    return json.load(open(path, encoding="utf-8-sig"))   # files written by PowerShell may carry a BOM


def log(zdir, msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line, flush=True)
    with open(os.path.join(zdir, "job.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


BUSY_EXIT = 75   # "another RealityScan is running": the queue waits and retries the step, it is not a failure


class Busy(Exception):
    pass


def rs_procs():
    """[(pid, command line)] of every RealityScan.exe (GUI, manual runs and the queue's own)."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='RealityScan.exe'\" | "
                        "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"],
                       capture_output=True, text=True, timeout=120)
    out = []
    for line in r.stdout.splitlines():
        if "\t" in line:
            pid, cmd = line.split("\t", 1)
            out.append((int(pid), cmd))
    return out


def run_rs(zdir, tag, cmds, timeout_s):
    """Headless RealityScan on an .rscmd; returns True on exit 0 before the timeout. Strictly one heavy RealityScan
    job at a time: while any other instance runs (a GUI, a manual run) it waits up to 30 min, then raises Busy so
    the queue retries the step later instead of failing the zone."""
    t0 = time.time()
    while rs_procs():
        if time.time() - t0 > 1800:
            log(zdir, f"{tag}: another RealityScan is running, step postponed")
            raise Busy()
        time.sleep(30)
    t0 = time.time()
    rscmd = os.path.join(zdir, f"{tag}.rscmd")
    with open(rscmd, "w") as f:
        f.write("\n".join(['-set "appQuitOnError=true"', '-set "appAutoSaveMode=false"'] + cmds + ["-quit"]) + "\n")
    rlog = os.path.join(zdir, f"{tag}.rs.log")
    log(zdir, f"{tag}: RealityScan start (timeout {timeout_s / 60:.0f} min)")
    with open(rlog, "w") as fh:
        p = subprocess.Popen([RS, "-headless", "-stdConsole", "-silent", os.path.join(zdir, "crash"), "-execRSCMD", rscmd],
                             stdout=fh, stderr=subprocess.STDOUT)
        try:
            rc = p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            kill_tree(p.pid)
            log(zdir, f"{tag}: TIMEOUT after {timeout_s / 60:.0f} min, RealityScan killed")
            return False
    txt = open(rlog, encoding="utf-8", errors="ignore").read()
    bad = re.findall(r"(?im)^.*(?:error|failed|exception).*$", txt)
    log(zdir, f"{tag}: RealityScan exit {rc} in {(time.time() - t0) / 60:.1f} min" + (f"; log: {bad[-1][:200]}" if bad else ""))
    return rc == 0


def reg_params(zdir, kind):
    desc, fid, und, img = FORMATS[kind]
    p = os.path.join(zdir, f"reg_{kind}.xml")
    with open(p, "w") as f:
        f.write(_REG.format(name=desc, fid=fid, undist=und, images=img))
    return p


def link(src, dst):
    if os.path.exists(dst):
        return
    try:
        os.link(src, dst)                  # hard links: RealityScan does not follow junctions
    except OSError:
        shutil.copy2(src, dst)


def step_prep(z, job, zdir, a):
    imgs = os.path.join(zdir, "imgs")
    if os.path.isdir(imgs):
        shutil.rmtree(imgs)                 # hard links only: a changed job.json must not keep stale images
    n = 0
    for clip in job.get("clips", []):
        src = os.path.join(a.frames, clip)
        if not os.path.isdir(src):
            raise SystemExit(f"prep: frame folder missing: {src}")
        dst = os.path.join(imgs, clip)
        os.makedirs(dst, exist_ok=True)
        jpgs = sorted(f for f in os.listdir(src) if f.endswith(".jpg"))[::max(1, int(job.get("every", 1)))]
        for f in jpgs:          # "every": N keeps every N-th adaptive frame (whole-site alignment jobs)
            link(os.path.join(src, f), os.path.join(dst, f)); n += 1
            if os.path.exists(os.path.join(src, f + ".mask.png")):
                link(os.path.join(src, f + ".mask.png"), os.path.join(dst, f + ".mask.png"))
    dst = os.path.join(imgs, "photos")
    for pat in job.get("photos", []):
        hits = sorted(glob.glob(os.path.join(a.photos, pat)))
        if not hits:
            log(zdir, f"prep: no photos for {pat}")
        os.makedirs(dst, exist_ok=True)
        for p in hits:
            if p.endswith(".mask.png"):
                continue
            link(p, os.path.join(dst, os.path.basename(p)))
            n += 1
            if os.path.exists(p + ".mask.png"):
                link(p + ".mask.png", os.path.join(dst, os.path.basename(p) + ".mask.png"))
    log(zdir, f"prep: {n} images linked")
    json.dump({"images": n}, open(os.path.join(zdir, "prep.json"), "w"))
    return n > 0


def step_align(z, job, zdir, a):
    imgs = os.path.join(zdir, "imgs")
    n = jload(os.path.join(zdir, "prep.json"))["images"]
    cmds = ['-set "appIncSubdirs=true"',
            f'-set "sfmMaxFeaturesPerImage={job.get("features", 80000)}"',
            f'-set "sfmImagesOverlap={job.get("overlap", "Low")}"',
            f'-set "sfmDistortionModel={job.get("distortion", "Brown3")}"',
            f'-set "sfmDetectorSensitivity={job.get("sensitivity", "High")}"',
            "-newScene", f"-addFolder {q(imgs)}"]
    for k, clip in enumerate(job.get("clips", [])):
        # one lens + calibration group per video clip (EIS crop varies per clip, not within a clip)
        cmds += [f"-selectImage g/{clip}_f/ set", f"-setPriorLensGroup {k + 1}", f"-setPriorCalibrationGroup {k + 1}"]
    proj = os.path.join(zdir, f"{z}.rsproj")
    cmds += ["-deselectAllImages", "-align", f"-save {q(proj)}",
             f"-exportReport {q(os.path.join(zdir, 'report_overview.html'))} {q(os.path.join(REPORTS, 'Overview.html'))}"]
    tmo = job.get("align_timeout_s", min(8 * 3600, 900 + 8 * n))
    return run_rs(zdir, "align", cmds, tmo) and os.path.exists(proj)


def step_merge(z, job, zdir, a):
    """Second pass: clips filmed at other times of day often land in their own components; mergeComponents plus a
    re-align with High image overlap (more candidate pairs between clips) joins what shares enough features."""
    proj = os.path.join(zdir, f"{z}.rsproj")
    before = components(zdir)
    shutil.copy2(os.path.join(zdir, "report_overview.html"), os.path.join(zdir, "report_overview_align1.html"))
    n = jload(os.path.join(zdir, "prep.json"))["images"]
    cmds = [f"-load {q(proj)}", f'-set "sfmImagesOverlap={job.get("merge_overlap", "High")}"',
            "-mergeComponents", "-align", f"-save {q(proj)}",
            f"-exportReport {q(os.path.join(zdir, 'report_overview.html'))} {q(os.path.join(REPORTS, 'Overview.html'))}"]
    ok = run_rs(zdir, "merge", cmds, job.get("merge_timeout_s", min(8 * 3600, 900 + 12 * n)))
    after = components(zdir)
    log(zdir, "merge: largest before " + ", ".join(f"{n_}" for _, n_ in before[:6]) +
        " | after " + ", ".join(f"{n_}" for _, n_ in after[:6]))
    return ok and bool(after)


def components(zdir):
    """[(name, registered images)] from the overview report, largest first."""
    txt = re.sub(r"<[^>]*>", " ", open(os.path.join(zdir, "report_overview.html"), encoding="utf-8", errors="ignore").read())
    txt = re.sub(r"\s+", " ", txt)
    comps = [(m.group(1), int(m.group(2))) for m in
             re.finditer(r"Component: (Component \d+) Count of registered images (\d+) / \d+", txt)]
    return sorted(comps, key=lambda c: -c[1])


def step_cams(z, job, zdir, a):
    proj = os.path.join(zdir, f"{z}.rsproj")
    comps = [c for c in components(zdir) if c[1] >= job.get("min_cams", 25)]
    log(zdir, "cams: components " + ", ".join(f"{c}={n}" for c, n in components(zdir)))
    if not comps:
        log(zdir, "cams: no component with enough images")
        return False
    # component numbers change when a zone is re-aligned: the outputs of the previous alignment move to prev\
    old = [d for d in glob.glob(os.path.join(zdir, "c[0-9]*")) if os.path.isdir(d)]
    if old:
        prev = os.path.join(zdir, "prev")
        if os.path.isdir(prev):
            shutil.rmtree(prev)
        os.makedirs(prev)
        for d in old:
            shutil.move(d, prev)
    cmds = [f"-load {q(proj)}"]
    for name, n in comps:
        cid = "c" + name.split()[-1]
        out = os.path.join(zdir, cid)
        os.makedirs(os.path.join(out, "colmap"), exist_ok=True)
        cmds += [f"-selectComponent {q(name)}",
                 f"-exportRegistration {q(os.path.join(out, 'cams.csv'))} {q(reg_params(zdir, 'csv'))}",
                 # not 'cameras.txt': that name clashes with the file the COLMAP writer puts in sparse/0
                 f"-exportRegistration {q(os.path.join(out, 'colmap', 'export.txt'))} {q(reg_params(zdir, 'colmap'))}",
                 f"-exportSparsePointCloud {q(os.path.join(out, 'sparse.ply'))}"]
    if not run_rs(zdir, "cams", cmds, job.get("cams_timeout_s", 1800 + 3 * sum(n for _, n in comps))):
        return False
    ok = True
    for name, n in comps:
        out = os.path.join(zdir, "c" + name.split()[-1])
        r = subprocess.run([PY, os.path.join(HERE, "rs_to_model.py"), out, os.path.join(out, "model.json"), "--zone", z],
                           capture_output=True, text=True, timeout=1800)
        log(zdir, f"cams: {name} ({n} images) model.json exit {r.returncode} {r.stdout.strip()[-200:]} {r.stderr.strip()[-300:]}")
        ok &= r.returncode == 0
    json.dump({"components": [{"name": c, "images": n, "dir": "c" + c.split()[-1]} for c, n in comps]},
              open(os.path.join(zdir, "components.json"), "w"), indent=1)
    return ok


def region(out, pad=0.12):
    """Reconstruction box (RealityScan grid frame): sparse points that lie near the camera path (drops far
    skyline points), 1-99 percentile, plus the camera centres, padded."""
    import open3d as o3d
    P = np.asarray(o3d.io.read_point_cloud(os.path.join(out, "sparse.ply")).points)
    m = jload(os.path.join(out, "model.json"))
    C = np.array([c["center"] for c in m["cameras"]])
    # up axis of this component: RealityScan components are not always Z-up, so take the mean camera "up"
    # (image -y of the upright phone frames) and extend the box along the grid axis closest to it
    up = np.mean([np.array(c["R"]).T @ np.array([0.0, -1.0, 0.0]) for c in m["cameras"]], axis=0)
    k = int(np.argmax(np.abs(up))); sgn = 1.0 if up[k] > 0 else -1.0
    from scipy.spatial import cKDTree
    d, _ = cKDTree(C).query(P)
    keep = P[d < 3.0 * np.median(d)]
    lo = np.minimum(np.percentile(keep, 1, axis=0), C.min(0))
    hi = np.maximum(np.percentile(keep, 99, axis=0), C.max(0))
    ext = hi - lo
    lo, hi = lo - pad * ext, hi + pad * ext
    # facades and roofs above the phone: sparse points thin out with height, so keep at least 0.6 x the plan
    # extent above the highest camera (RealityScan only meshes where the depth maps have data)
    plan = max(ext[j] for j in range(3) if j != k)
    if sgn > 0:
        hi[k] = max(hi[k], C[:, k].max() + 0.6 * plan)
    else:
        lo[k] = min(lo[k], C[:, k].min() - 0.6 * plan)
    c, w = (lo + hi) / 2, hi - lo
    box = os.path.join(out, "region.rsbox")
    with open(box, "w") as f:
        f.write(BOX.format(w=w[0], h=w[1], d=w[2], cx=c[0], cy=c[1], cz=c[2]))
    return box, lo, hi


def step_mesh(z, job, zdir, a):
    proj = os.path.join(zdir, f"{z}.rsproj")
    proj_mesh = os.path.join(zdir, f"{z}_mesh.rsproj")   # the aligned project itself is never overwritten
    comps = jload(os.path.join(zdir, "components.json"))["components"][: job.get("mesh_comps", 2)]
    ok = True
    for c in comps:
        out = os.path.join(zdir, c["dir"])
        obj = os.path.join(out, "mesh.obj")
        done = os.path.join(out, "mesh.done")           # written only after a clean export: a killed export
        if os.path.exists(done) and os.path.exists(obj):  # leaves a truncated obj that must not count
            continue
        for f in glob.glob(os.path.join(out, "mesh.*")):
            os.remove(f)
        try:
            box, lo, hi = region(out)
        except Exception as e:                       # no model.json / sparse cloud: let RealityScan choose
            log(zdir, f"mesh: {c['name']} region from the sparse cloud failed ({e}); automatic region")
            box = None
        else:
            log(zdir, f"mesh: {c['name']} region {np.round(lo, 2).tolist()} .. {np.round(hi, 2).tolist()}")
        cmds = [f"-load {q(proj)}", f"-selectComponent {q(c['name'])}",
                f"-setReconstructionRegion {q(box)}" if box else "-setReconstructionRegionAuto",
                {"preview": "-calculatePreviewModel", "normal": "-calculateNormalModel",
                 "high": "-calculateHighModel"}[job.get("detail", "high")],
                f"-renameSelectedModel {c['dir']}_raw",
                f"-simplify {job.get('simplify', 20000000)}", f"-renameSelectedModel {c['dir']}",
                f"-exportSelectedModel {q(obj)}", f"-save {q(proj_mesh)}"]
        tmo = job.get("mesh_timeout_s", min(6 * 3600, 1800 + 60 * c["images"]))
        good = run_rs(zdir, f"mesh_{c['dir']}", cmds, tmo) and os.path.exists(obj)
        if good:
            open(done, "w").write(time.strftime("%Y-%m-%d %H:%M:%S"))
        ok &= good
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["prep", "align", "merge", "cams", "mesh", "steps"])
    ap.add_argument("id")
    ap.add_argument("--work", default=r"C:\koch\work")
    a = ap.parse_args()
    a.frames = os.path.join(a.work, "frames_a")
    a.photos = os.path.join(a.work, "photos")
    zdir = os.path.join(a.work, "zones", a.id)
    job = jload(os.path.join(zdir, "job.json"))
    steps = job.get("steps", ["prep", "align", "merge", "cams", "mesh"])
    if a.step == "steps":
        print(" ".join(steps))
        return 0
    # a step that runs again invalidates everything after it (its outputs feed the later steps)
    for later in steps[steps.index(a.step) + 1:] if a.step in steps else []:
        f = os.path.join(zdir, f"{later}.ok")
        if os.path.exists(f):
            os.remove(f)
    fn = {"prep": step_prep, "align": step_align, "merge": step_merge, "cams": step_cams, "mesh": step_mesh}[a.step]
    try:
        ok = fn(a.id, job, zdir, a)
    except Busy:
        return BUSY_EXIT
    if ok:
        open(os.path.join(zdir, f"{a.step}.ok"), "w").write(time.strftime("%Y-%m-%d %H:%M:%S"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
