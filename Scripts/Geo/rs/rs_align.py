# RealityScan 2.2 alignment of the whole site (R1 photogrammetry, docs/roles/R1-photogrammetry-handoff.md section 2).
# Writes an .rscmd (one command per line, RealityScan CLI syntax: rshelp.capturingreality.com, tutorials/
# commandline*.htm) and runs RealityScan headless on it. Frames: <frames>/<clip>/<clip>_fNNNNN.jpg, stills:
# <photos>/<set>/*.jpg; masks are picked up by name (<image>.mask.png, image-layer naming). Each video clip gets its
# own lens group (EIS crop changes the intrinsics per frame, so calibration stays per image).
# Usage: python rs_align.py --frames C:/koch/work/frames --photos C:/koch/work/photos --project C:/koch/work/rs/campus.rsproj
import argparse
import os
import subprocess
import sys

RS = os.environ.get("REALITYSCAN", r"C:\Program Files\Epic Games\RealityScan_2.2\RealityScan.exe")
REPORTS = os.path.join(os.path.dirname(RS), "Reports")


def q(s):
    return f'"{s}"'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--photos")
    ap.add_argument("--project", required=True)
    ap.add_argument("--max-features", type=int, default=40000)
    ap.add_argument("--overlap", default="Medium", choices=["Low", "Medium", "High"])
    ap.add_argument("--distortion", default="Brown3")
    ap.add_argument("--sensitivity", default="Medium", choices=["Low", "Medium", "High", "Ultra"])
    ap.add_argument("--clip-calib", action="store_true", help="one calibration group (focal, principal point) per clip")
    ap.add_argument("--dry", action="store_true", help="write the .rscmd only")
    a = ap.parse_args()
    work = os.path.dirname(os.path.abspath(a.project))
    os.makedirs(work, exist_ok=True)
    clips = sorted(d for d in os.listdir(a.frames) if os.path.isdir(os.path.join(a.frames, d)))
    cmd = [
        '-set "appIncSubdirs=true"',
        '-set "appAutoSaveMode=false"',
        '-set "appQuitOnError=true"',  # never hang headless on an error dialog
        f'-set "sfmMaxFeaturesPerImage={a.max_features}"',
        f'-set "sfmImagesOverlap={a.overlap}"',
        f'-set "sfmDistortionModel={a.distortion}"',
        f'-set "sfmDetectorSensitivity={a.sensitivity}"',
        "-newScene",
        f"-addFolder {q(os.path.abspath(a.frames))}",
    ]
    if a.photos:
        cmd.append(f"-addFolder {q(os.path.abspath(a.photos))}")
    for k, clip in enumerate(clips):
        cmd += [f"-selectImage g/{clip}_f/ set", f"-setPriorLensGroup {k + 1}"]
        if a.clip_calib:
            cmd.append(f"-setPriorCalibrationGroup {k + 1}")
    cmd += [
        "-deselectAllImages",
        "-align",
        f"-save {q(os.path.abspath(a.project))}",
        f"-exportReport {q(os.path.join(work, 'report_overview.html'))} {q(os.path.join(REPORTS, 'Overview.html'))}",
        "-selectMaximalComponent",
        f"-exportReport {q(os.path.join(work, 'report_component.html'))} "
        f"{q(os.path.join(REPORTS, 'SelectedComponent.html'))}",
        "-quit",
    ]
    rscmd = os.path.join(work, "align.rscmd")
    with open(rscmd, "w") as f:
        f.write("\n".join(cmd) + "\n")
    print(f"{rscmd}: {len(clips)} clips")
    if a.dry:
        return 0
    log = os.path.join(work, "align.log")
    with open(log, "w") as out:
        r = subprocess.run([RS, "-headless", "-stdConsole", "-silent", os.path.join(work, "crash"),
                            "-execRSCMD", rscmd], stdout=out, stderr=subprocess.STDOUT)
    print("RealityScan exit", r.returncode, "log", log)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
