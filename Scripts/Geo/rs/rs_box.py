# World box -> RealityScan reconstruction region (.rsbox) in the RealityScan grid frame (R1 photogrammetry): the
# 8 corners of the campus-world box are mapped through the inverse of align.json (world = s R x + t) and the region
# is their axis-aligned box in the grid (yaw/pitch/roll 0), so a zone can be meshed at high detail on its own.
# Format as written by RealityScan 2.2 -exportReconstructionRegion. Usage:
#   python rs_box.py align.json --box 165,-15,4,212,30,24 --out zoneC.rsbox
import argparse
import json
import sys

import numpy as np

TEMPLATE = """<ReconstructionRegion globalCoordinateSystem="NONE" globalCoordinateSystemWkt="NONE" globalCoordinateSystemName="NONE"
   isGeoreferenced="0" isLatLon="0" yawPitchRoll="0 -0 -0" widthHeightDepth="{w} {h} {d}">
  <Header magic="5395016" version="2"/>
  <CentreEuclid>
    <centre>{cx} {cy} {cz}</centre>
  </CentreEuclid>
  <Residual R="1 0 0 0 1 0 0 0 1" t="0 0 0" s="1" ownerId="{{A514E61A-E75B-4DE5-B2CE-D289FB86277C}}"/>
</ReconstructionRegion>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("align")
    ap.add_argument("--box", required=True, help="x0,y0,z0,x1,y1,z1 campus world metres")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    al = json.load(open(a.align))
    s, R, t = float(al["scale"]), np.array(al["R"]), np.array(al["t"])
    x0, y0, z0, x1, y1, z1 = map(float, a.box.split(","))
    W = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    G = ((W - t) @ R) / s                      # grid = R^T (world - t) / s
    lo, hi = G.min(0), G.max(0)
    c, size = (lo + hi) / 2, hi - lo
    open(a.out, "w").write(TEMPLATE.format(w=size[0], h=size[1], d=size[2], cx=c[0], cy=c[1], cz=c[2]))
    print(f"{a.out}: grid centre {np.round(c, 3)}, size {np.round(size, 3)}")


if __name__ == "__main__":
    sys.exit(main())
