# RealityScan 2.2 exports for the aligned site project (R1 photogrammetry; follows rs_align.py).
#   cams: registration of the largest component as "Internal/External camera parameters" CSV (original names) and
#         COLMAP text with undistorted images (for rs_to_model.py -> sfm_overlay.py), plus the sparse cloud (PLY).
#   mesh: model of a reconstruction region (.rsbox or auto) at preview/normal/high detail, optional simplify and
#         texture, exported as OBJ in the RealityScan grid frame (Z up, same frame as cams.csv).
# Params XMLs carry the export format ids from <RealityScan>/calibration.xml (e.g. COLMAP {280B11A4-...}).
# Usage:
#   python rs_export.py cams --project C:/koch/work/rs/campus.rsproj --out C:/koch/work/rs/exp
#   python rs_export.py mesh --project ... --out ... --detail normal [--region box.rsbox] [--downscale 4]
#                            [--simplify 20000000] [--texture] [--name campus]
import argparse
import os
import subprocess
import sys

RS = os.environ.get("REALITYSCAN", r"C:\Program Files\Epic Games\RealityScan_2.2\RealityScan.exe")
HERE = os.path.dirname(os.path.abspath(__file__))

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
FORMATS = {  # (desc, id) from calibration.xml
    "csv": ("Internal/External camera parameters", "{0CA18733-1EBC-4254-9974-17197EB409BD}", "-1", "-1"),
    "colmap": ("COLMAP", "{280B11A4-F9A3-47D1-AE58-C0DEA33487D8}", "1", "1"),
}


def params(out, kind):
    desc, fid, und, img = FORMATS[kind]
    p = os.path.join(out, f"reg_{kind}.xml")
    with open(p, "w") as f:
        f.write(_REG.format(name=desc, fid=fid, undist=und, images=img))
    return p


def q(s):
    return f'"{s}"'


def run(out, tag, cmds):
    rscmd = os.path.join(out, f"{tag}.rscmd")
    with open(rscmd, "w") as f:
        f.write("\n".join(cmds + ["-quit"]) + "\n")
    log = os.path.join(out, f"{tag}.log")
    with open(log, "w") as fh:
        r = subprocess.run([RS, "-headless", "-stdConsole", "-silent", os.path.join(out, "crash"), "-execRSCMD", rscmd],
                           stdout=fh, stderr=subprocess.STDOUT)
    print(f"{tag}: RealityScan exit {r.returncode}, log {log}")
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["cams", "mesh"])
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--component", help="component name (default: the largest)")
    ap.add_argument("--detail", default="normal", choices=["preview", "normal", "high"])
    ap.add_argument("--region", help=".rsbox reconstruction region (default: automatic)")
    ap.add_argument("--downscale", type=int, help="depth-map image downscale for the normal model (default 2)")
    ap.add_argument("--simplify", type=int, help="target triangle count after meshing")
    ap.add_argument("--texture", action="store_true")
    ap.add_argument("--tex-res", type=int, default=8192)
    ap.add_argument("--tex-count", type=int, default=16)
    ap.add_argument("--name", default="mesh")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    sel = f"-selectComponent {q(a.component)}" if a.component else "-selectMaximalComponent"
    base = ['-set "appAutoSaveMode=false"', f"-load {q(os.path.abspath(a.project))}", sel]
    if a.stage == "cams":
        os.makedirs(os.path.join(out, "colmap"), exist_ok=True)
        cmds = base + [
            f"-exportRegistration {q(os.path.join(out, 'cams.csv'))} {q(params(out, 'csv'))}",
            # not 'cameras.txt': that target name clashes with the file the COLMAP writer puts in sparse/0
            f"-exportRegistration {q(os.path.join(out, 'colmap', 'export.txt'))} {q(params(out, 'colmap'))}",
            f"-exportSparsePointCloud {q(os.path.join(out, 'sparse.ply'))}",
        ]
        return run(out, "cams", cmds)
    cmds = list(base)
    if a.downscale:
        cmds.append(f'-set "mvsNormalDownscaleFactor={a.downscale}"')
    cmds.append(f"-setReconstructionRegion {q(os.path.abspath(a.region))}" if a.region else "-setReconstructionRegionAuto")
    cmds.append({"preview": "-calculatePreviewModel", "normal": "-calculateNormalModel",
                 "high": "-calculateHighModel"}[a.detail])
    cmds.append(f"-renameSelectedModel {a.name}_raw")
    if a.simplify:
        cmds += [f"-simplify {a.simplify}", f"-renameSelectedModel {a.name}"]
    if a.texture:
        cmds += ['-set "unwrapStyle=MaxTexturesCount"', f'-set "unwrapMaximalTexCount={a.tex_count}"',
                 f'-set "unwrapMaxTexResolution={a.tex_res}"', "-unwrap", "-calculateTexture"]
    cmds += [f"-exportSelectedModel {q(os.path.join(out, a.name + '.obj'))}",
             f"-save {q(os.path.abspath(a.project))}"]
    return run(out, f"mesh_{a.name}", cmds)


if __name__ == "__main__":
    sys.exit(main())
