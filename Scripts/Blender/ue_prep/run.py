# Blender -> UE 5.8 greybox hand-off (R1 -> everyone): deduplicated static meshes with generated collision and UVs,
# 64 m terrain tiles, and manifest.json for Scripts/Unreal/import_greybox.py. Read-only on the .blend (works on the
# in-memory copy, never saves).
# Run: blender -b IN.blend -P Scripts/Blender/ue_prep/run.py -- OUT_DIR [--cache DIR] [--no-coacd] [--workers N]
# Check: python3 Scripts/Blender/ue_prep/check.py OUT_DIR; round trip: Scripts/Blender/ue_prep/roundtrip.py.
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.dirname(HERE))
for _m in [m for m in sys.modules if m == "ue_prep" or m.startswith("ue_prep.")]:
    del sys.modules[_m]   # a live Blender session keeps old module versions

from ue_prep import collision as col                                    # noqa: E402
from ue_prep.common import (BARRIER_PREFIX, SKIP_COLLECTIONS, SKIP_PREFIX, TERRAIN, TILE_INDEX_OFFSET, TILE_M,  # noqa
                            UE_ROOT, ascii_name, blender_to_ue, box_uvs, has_banned, role_of, rot_z90)
from ue_prep.export import Writer                                       # noqa: E402
from ue_prep.geom import canonical, decompose, geo_from_mesh            # noqa: E402
from ue_prep.terrain import build_tiles, carry_flatten                  # noqa: E402

VERSION = 1
DECOR_TYPES = {"paint", "zebra", "string_lights", "net_roof", "tree"}
DECOR_NAME = re.compile(r"Paint|Festoon|Decal|Marking")
STAIR_TYPES = {"stairs_run", "steps"}
STAIR_NAME = re.compile(r"(Stairs?|Steps|Flight)(_|\d|$)")
STAIR_NOT = re.compile(r"Cheek|Rail|Landing|Lamp|Pot|Door|Radiator|Light|Wall|Paint|Top|Leg|Platform|Well|Plant")
COACD_PARAMS = {"threshold": 0.08, "max_convex_hull": col.DECOMP_CAP, "resolution": 2000,
                "mcts_iterations": 100, "merge": True, "seed": 0}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="ue_prep")
    ap.add_argument("out")
    ap.add_argument("--cache", default="", help="CoACD result cache (default OUT/_cache)")
    ap.add_argument("--no-coacd", action="store_true", help="non-convex leftovers -> complex_as_simple")
    ap.add_argument("--workers", type=int, default=2)
    return ap.parse_args(argv)


def zone_of(ob, parents):
    """(zone collection, building) of an object; None if it lives only in skipped collections."""
    cols = sorted((c for c in ob.users_collection if c.name not in SKIP_COLLECTIONS), key=lambda c: c.name)
    for c in cols:
        chain, p = [c.name], parents.get(c.name)
        while p:
            chain.append(p)
            p = parents.get(p)
        if any(n in SKIP_COLLECTIONS for n in chain):
            continue
        z = c.name
        if z.startswith("BLD_"):
            b = z
        elif z.startswith("INT_C"):
            b = "BLD_C"
        elif z.startswith("CTX_") or z == "08_Context":
            b = "CTX"
        elif ob.name.startswith(BARRIER_PREFIX):
            b = "Barriers"
        else:
            b = z
        return z, b
    return None


def collect():
    sc = bpy.context.scene
    parents = {}
    for c in bpy.data.collections:
        for ch in c.children:
            parents[ch.name] = c.name
    out, terrain = [], None
    for ob in sorted(sc.objects, key=lambda o: o.name):
        if ob.type != "MESH" or ob.name.startswith(SKIP_PREFIX):
            continue
        if ob.hide_render and not ob.name.startswith(BARRIER_PREFIX):
            continue   # phase-1 massing replaced by detailed specs (same rule as export_ue.py)
        if ob.name == TERRAIN:
            terrain = ob
            continue
        z = zone_of(ob, parents)
        if z is None:
            continue
        out.append((ob, z[0], z[1]))
    return out, terrain


def instance_flags(ob, zone):
    slot = str(ob.get("koch_ue_asset", ob.get("ue_asset", "")) or "")
    kt = str(ob.get("koch_type", "") or "")
    none = ""
    if slot and slot != "blocking_volume":
        none = "placeholder"
    elif kt in DECOR_TYPES or DECOR_NAME.search(ob.name):
        none = "decor"
    elif zone == "CTX_Far":
        none = "context_far"
    stairs = (kt in STAIR_TYPES or bool(STAIR_NAME.search(ob.name))) and not STAIR_NOT.search(ob.name) \
        and not DECOR_NAME.search(ob.name)
    return {"slot": slot, "type": kt, "none": none, "stairs": stairs,
            "collision_only": bool(ob.get("koch_collision_only", False)),
            "barrier": ob.name.startswith(BARRIER_PREFIX)}


def object_geo(ob, dg):
    if ob.modifiers:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        g = geo_from_mesh(me)
        ev.to_mesh_clear()
        return g
    return geo_from_mesh(ob.data)


def run_coacd(jobs, cache, workers):
    """jobs: {key: geo}. Returns {key: [(verts, tris)] or None}; results cached by geometry hash + params."""
    ptag = hashlib.sha1(json.dumps(COACD_PARAMS, sort_keys=True).encode()).hexdigest()[:8]
    os.makedirs(cache, exist_ok=True)
    todo, res = [], {}
    for key, g in jobs.items():
        out = os.path.join(cache, f"{key}_{ptag}.json")
        if not os.path.exists(out):
            objp = os.path.join(cache, f"{key}.obj")
            co, t = col.tri_soup(g)
            with open(objp, "w") as fh:
                fh.write("".join(f"v {x:.6f} {y:.6f} {z:.6f}\n" for x, y, z in co))
                fh.write("".join(f"f {a + 1} {b + 1} {c + 1}\n" for a, b, c in t))
            todo.append({"key": key, "obj": objp, "out": out})
    if todo:
        spec = os.path.join(cache, "_jobs.json")
        with open(spec, "w") as fh:
            json.dump({"params": COACD_PARAMS, "workers": workers, "timeout": 120, "jobs": todo}, fh)
        cmd = ["uv", "run", "--project", os.path.join(REPO, "Scripts"), "--with", "coacd==1.0.*", "python", "-I",
               os.path.join(HERE, "coacd_worker.py"), spec]
        print(f"ue_prep: CoACD on {len(todo)} meshes ({workers} workers)...", flush=True)
        subprocess.run(cmd, check=False, cwd=cache)
    for key in jobs:
        out = os.path.join(cache, f"{key}_{ptag}.json")
        try:
            with open(out) as fh:
                r = json.load(fh)
        except (OSError, ValueError):
            r = {"error": "missing"}
        res[key] = None if r.get("error") or not r.get("hulls") else \
            [(np.array(h["v"], np.float64), np.array(h["t"], np.int64)) for h in r["hulls"]]
    return res


def main():
    args = parse_args()
    t0 = time.time()
    out = os.path.abspath(args.out)
    cache = os.path.abspath(args.cache) if args.cache else os.path.join(out, "_cache")
    os.makedirs(out, exist_ok=True)
    sc = bpy.context.scene
    us = sc.unit_settings
    if us.system != "METRIC" or abs(us.scale_length - 1.0) > 1e-6:
        raise SystemExit(f"ue_prep: scene units must be metric, scale 1.0 (got {us.system}, {us.scale_length})")
    bpy.context.view_layer.update()   # objects placed via ob.location keep a stale matrix_world until this
    dg = bpy.context.evaluated_depsgraph_get()
    obs, terrain = collect()
    if terrain:   # owner ground corrections carried by the lawn strips on that ground (ue_prep/terrain.py)
        print(f"ue_prep: {carry_flatten(terrain, [o for o, _, _ in obs])} carried vertices lowered", flush=True)
        dg = bpy.context.evaluated_depsgraph_get()   # re-evaluate the edited meshes
    print(f"ue_prep: {len(obs)} objects, terrain={'yes' if terrain else 'no'}", flush=True)

    # 1. per object: bake scale/mirror into the mesh, canonicalise, hash
    insts, assets = [], {}
    for ob, zone, bld in obs:
        g = object_geo(ob, dg)
        if g.nfaces == 0:
            continue
        rig, s, ok = decompose(ob.matrix_world)
        if not ok:   # sheared: bake the whole 3x3, keep only the translation
            g = g.transformed(np.asarray(ob.matrix_world)[:3, :3])
            rig = np.eye(4)
            rig[:3, 3] = np.asarray(ob.matrix_world)[:3, 3]
        elif np.abs(s - 1).max() > 1e-6:
            g = g.transformed(np.diag(s))
        key, k, piv, mkey = canonical(g)
        if key is None:   # > 1 km local extent: own asset, no dedup
            key, k, piv = "u" + hashlib.sha1(ob.name.encode()).hexdigest()[:39], 0, g.co.min(0) * [0, 0, 1]
        m_inst = rig @ _r4(rot_z90(k).T) @ _t4(piv)   # world = M_obj R_k^T (v_c + p)
        rec = {"ob": ob.name, "zone": zone, "building": bld, "m": m_inst, "key": key, "mirrored": bool(s.prod() < 0),
               "koch_id": str(ob.get("koch_id", "") or ""), **instance_flags(ob, zone)}
        insts.append(rec)
        a = assets.get(key)
        if a is None:   # first (= smallest) object name is the representative
            assets[key] = a = {"key": key, "mirror_key": mkey, "rep": ob.name, "insts": [],
                               "geo": g.transformed(rot_z90(k), -piv)}
        a["insts"].append(rec)
    t_hash = time.time() - t0
    print(f"ue_prep: {len(insts)} instances -> {len(assets)} unique meshes ({t_hash:.0f} s)", flush=True)

    # 2. names (role of the representative + hash, stable across rebuilds), folders
    names = {}
    for key in sorted(assets):
        a = assets[key]
        role = role_of(a["rep"])
        for n in (8, 12, 40):
            nm = ascii_name(f"SM_GB_{role}_{key[:n]}", 52)
            if nm not in names:
                break
        names[nm] = key
        a["name"] = nm
        blds = {r["building"] for r in a["insts"]}
        a["folder"] = blds.pop() if len(blds) == 1 else "Shared"
    by_key = {k: a["name"] for k, a in assets.items()}
    for a in assets.values():
        tw = by_key.get(a["mirror_key"])
        a["mirror_of"] = tw if tw and tw != a["name"] else ""

    # 3. collision
    decomp = {}
    for key in sorted(assets):
        a = assets[key]
        reasons = {r["none"] for r in a["insts"]}
        none = "" if "" in reasons else sorted(reasons)[0]   # any instance needing collision wins
        kind, prims, info = col.classify(a["geo"], none_reason=none, stairs=any(r["stairs"] for r in a["insts"]),
                                         force_complex=any(r["collision_only"] for r in a["insts"]))
        a.update(ckind=kind, prims=prims, cinfo=info)
        if kind == "decomp":
            decomp[key] = a["geo"]
    if decomp:
        res = {} if args.no_coacd else run_coacd(decomp, cache, args.workers)
        for key in decomp:
            a = assets[key]
            hulls = res.get(key)
            prims = [("UCX", v, t) for v, t in hulls] if hulls else None
            if prims and len(prims) > col.DECOMP_CAP:   # CoACD's own merge can stop above the cap
                prims = col.merge_prims(prims, col.DECOMP_CAP, ratio=2.0)
            if prims:
                a["prims"] = prims
                a["cinfo"]["hulls"] = len(prims)
            else:
                a["ckind"] = "complex_as_simple"
                a["cinfo"]["reason"] = "coacd_off" if args.no_coacd else "coacd_failed"
    t_col = time.time() - t0 - t_hash
    print(f"ue_prep: collision done ({t_col:.0f} s, {len(decomp)} via CoACD)", flush=True)

    # 4. terrain tiles
    tiles, seams = build_tiles(terrain) if terrain else ([], [])

    # 5. export
    w = Writer()
    meshes = {}
    try:
        for key in sorted(assets):
            a = assets[key]
            g = a["geo"]
            n, _ = g.face_normals()
            uv = box_uvs(g.co[g.loop_vert], n, g.loop_face())   # asset space: every instance shares the UVs
            rel = f"Meshes/{a['folder']}/{a['name']}.fbx"
            slots = w.write(os.path.join(out, rel), a["name"], g, uv, a["prims"])
            lo, hi = g.co.min(0), g.co.max(0)
            meshes[a["name"]] = {
                "file": rel, "ue_path": f"{UE_ROOT}/Meshes/{a['folder']}/{a['name']}", "key": key,
                "role": role_of(a["rep"]), "source": a["rep"], "instances": len(a["insts"]),
                "slots": slots, "tris": int((g.loop_total - 2).sum()), "verts": len(g.co),
                "bounds_m": [lo.round(4).tolist(), hi.round(4).tolist()], "mirror_of": a["mirror_of"],
                "collision": {"kind": a["ckind"], "ubx": sum(p[0] == "UBX" for p in a["prims"]),
                              "ucx": sum(p[0] == "UCX" for p in a["prims"]), **a["cinfo"]}}
        for t in tiles:
            rel = f"Ground/{t['name']}.fbx"
            slots = w.write(os.path.join(out, rel), t["name"], t["geo"], t["uv"], [])
            meshes[t["name"]] = {"file": rel, "ue_path": f"{UE_ROOT}/Ground/{t['name']}", "role": "Ground",
                                 "source": TERRAIN, "instances": 1, "slots": slots, "tris": t["tris"],
                                 "verts": len(t["geo"].co), "tile": t["ij"], "corner_m": t["corner_m"],
                                 "collision": {"kind": "complex_as_simple", "ubx": 0, "ucx": 0, "reason": "terrain"}}
    finally:
        w.close()

    # 6. manifest
    inst_out, groups, placeholders = [], {}, []
    for r in insts:
        a = assets[r["key"]]
        tr = blender_to_ue(r["m"])
        e = {"name": r["ob"], "mesh": a["name"], **tr, "zone": r["zone"], "building": r["building"],
             "koch_id": r["koch_id"], "koch_type": r["type"], "ue_asset": r["slot"],
             "collision": a["ckind"], "slots": meshes[a["name"]]["slots"],
             "role": "barrier" if r["barrier"] else ("placeholder" if r["none"] == "placeholder" else "static")}
        if r["mirrored"]:
            e["mirrored_src"] = True
        inst_out.append(e)
        if e["role"] == "placeholder":
            placeholders.append({"name": r["ob"], "slot": r["slot"], "mesh": a["name"], "loc": tr["loc"],
                                 "rot": tr["rot"], "building": r["building"]})
        groups.setdefault(r["building"], {"zones": set(), "instances": 0})
        groups[r["building"]]["zones"].add(r["zone"])
        groups[r["building"]]["instances"] += 1
    for t in tiles:
        x0, y0, _ = t["corner_m"]
        inst_out.append({"name": t["name"], "mesh": t["name"], **blender_to_ue(_t4([x0, y0, 0.0])), "zone": "Ground",
                         "building": "Ground", "koch_id": "", "koch_type": "terrain", "ue_asset": "",
                         "collision": "complex_as_simple", "slots": meshes[t["name"]]["slots"], "role": "ground"})
    groups = {b: {"zones": sorted(v["zones"]), "instances": v["instances"],
                  "packed_level_actor": f"PLA_GB_{ascii_name(b)}", "folder": f"Greybox/{b}"}
              for b, v in sorted(groups.items())}
    kinds = {}
    for m in meshes.values():
        c = m["collision"]
        kinds.setdefault(c["kind"], {"meshes": 0, "ubx": 0, "ucx": 0})
        kinds[c["kind"]]["meshes"] += 1
        kinds[c["kind"]]["ubx"] += c["ubx"]
        kinds[c["kind"]]["ucx"] += c["ucx"]
    n_obj = len(insts)
    n_uni = len(assets)
    stats = {"objects": n_obj, "unique_meshes": n_uni, "dedup_ratio": round(n_obj / max(n_uni, 1), 3),
             "mirror_twins": sum(1 for a in assets.values() if a["mirror_of"]),
             "mirrored_sources": sum(1 for r in insts if r["mirrored"]),
             "collision": kinds, "tiles": len(tiles), "tile_tris_max": max((t["tris"] for t in tiles), default=0),
             "tile_tris_total": sum(t["tris"] for t in tiles), "seams": len(seams),
             "seam_mismatch": sum(s["mismatch"] for s in seams), "placeholders": len(placeholders),
             "runtime_s": round(time.time() - t0, 1)}
    manifest = {
        "version": VERSION, "generator": "Scripts/Blender/ue_prep/run.py", "format": "fbx",
        "source": os.path.basename(bpy.data.filepath),
        "units": "UE cm; loc = (100x, -100y, 100z) of Blender metres; rot = UE Rotator [pitch, yaw, roll] deg",
        "pivot": "meshes: bottom-centre of the canonical bbox; ground tiles: tile min corner (x0, y0, 0)",
        "tile_m": TILE_M, "tile_index_offset": TILE_INDEX_OFFSET, "ue_root": UE_ROOT,
        "meshes": meshes, "instances": inst_out, "placeholders": placeholders, "groups": groups,
        "seams": seams, "stats": stats}
    text = json.dumps(manifest, indent=1)
    if has_banned(text):
        raise SystemExit("ue_prep: a real-place string reached the manifest; fix the source names first")
    with open(os.path.join(out, "manifest.json"), "w") as fh:
        fh.write(text)
    print("ue_prep: " + json.dumps(stats), flush=True)


def _r4(r3):
    m = np.eye(4)
    m[:3, :3] = r3
    return m


def _t4(t):
    m = np.eye(4)
    m[:3, 3] = t
    return m


main()
