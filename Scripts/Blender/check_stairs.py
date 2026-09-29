# Level check for every stair flight in the site/interior specs (R1 zone loop): the surface in front of the bottom
# riser must be at the foot level and the surface behind the top nosing at the top level. Prints mismatches > TOL.
# Run: blender -b FILE.blend -P Scripts/Blender/check_stairs.py
import json
import math
import os

import bpy
from mathutils import Vector

TOL = 0.03
SPECS = os.path.join(os.path.dirname(__file__), "..", "..", "Art", "Blender", "Specs")
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
DOWN = Vector((0, 0, -1))


def surface(x, y, z_hint, skip):
    """Highest up-facing surface under (x, y) within 0.6 m above / 1.5 m below z_hint, skipping objects in skip."""
    org = Vector((x, y, z_hint + 0.6))
    for _ in range(8):
        hit, loc, n, _, ob, _ = sc.ray_cast(dg, org, DOWN, distance=2.1)
        if not hit:
            return None, None
        if ob.name not in skip and n.z > 0.5:
            return loc.z, ob.name
        org = loc - Vector((0, 0, 0.002))
    return None, None


rows = []
for fn in sorted(os.listdir(SPECS)):
    if not fn.endswith(".json"):
        continue
    spec = json.load(open(os.path.join(SPECS, fn)))
    pref = "GBS_" + spec["id"].replace("SITE_", "").replace("INT_", "") + "_"
    # a flight whose foot is the top of the next flight (chained flights): the probe lands on that flight's treads
    tops = {e["name"]: e["z_top"] for e in spec.get("elements", []) if e.get("type") == "stairs_run" and "z_top" in e}
    chained = lambda o, zf: any(o and o.endswith(n) and abs(zt - zf) <= TOL for n, zt in tops.items())
    for el in spec.get("elements", []):
        if el.get("type") not in ("stairs_run",) or "z_top" not in el:
            continue
        nm = el.get("name", "")
        obs = [o.name for o in bpy.data.objects if o.name.endswith(nm) or o.name.endswith(nm + "_2")]
        a = math.radians(el["dir_deg"]); f = Vector((math.cos(a), math.sin(a), 0))
        n, rh, tr = int(el["risers"]), el["riser_h"], el["tread"]
        rb = el.get("bottom_riser_h", rh)
        z_top = el["z_top"]; z_foot = z_top - (n - 1) * rh - rb
        run = (n - 1) * tr + el.get("run_out", 0.0)
        top = Vector((el["top"][0], el["top"][1], 0))
        pf = top + f * (run + 0.25); pt = top - f * 0.25
        zf, of = surface(pf.x, pf.y, z_foot, set(obs)); zt, ot = surface(pt.x, pt.y, z_top, set(obs))
        for tag, zexp, z, o in (("foot", z_foot, zf, of), ("top", z_top, zt, ot)):
            if z is None:
                rows.append((fn[:-5], nm, tag, zexp, None, None, "NO SURFACE"))
            elif abs(z - zexp) > TOL and not (tag == "foot" and chained(o, zexp)):
                rows.append((fn[:-5], nm, tag, round(zexp, 3), round(z, 3), round(z - zexp, 3), o))
print("STAIRS checked; mismatches > %.2f m: %d" % (TOL, len(rows)))
for r in rows:
    print("STAIR", *r)
