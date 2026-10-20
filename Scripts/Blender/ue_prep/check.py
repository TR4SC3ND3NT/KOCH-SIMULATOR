# Offline validator for a ue_prep OUT_DIR (no Blender, stdlib only): every manifest mesh file exists and parses,
# holds exactly its render node + correctly named UBX_/UCX_ collision nodes (counts match the manifest, UBX are real
# boxes), flat hierarchy, Blender/UE axis header, watertight ground seams (exact border vertex sets), no real-place
# strings, totals. Run: python3 Scripts/Blender/ue_prep/check.py OUT_DIR [--quick]   (exit 1 on any error)
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ue_prep.names import bytes_banned, has_banned   # noqa: E402
from ue_prep.fbxread import read                 # noqa: E402

# Blender's own axis system (Z up, front -Y, X right): the frame UE's FBX importer converts to (common.py)
EXPECT_AXES = {"UpAxis": 2, "UpAxisSign": 1, "FrontAxis": 1, "FrontAxisSign": -1, "CoordAxis": 0, "CoordAxisSign": 1}


def _border(model, axis, value):
    """Vertices of boundary edges on coordinate axis == value (file units after the node's Lcl scale/translation:
    Blender writes metres + Lcl Scaling 100), as tuples of the other two coords."""
    sc, tr = model["lcl_s"], model["lcl_t"]
    v = [tuple(p[i] * sc[i] + tr[i] for i in range(3)) for p in model["verts"]]
    cnt = {}
    for p in model["polys"]:
        for a, b in zip(p, p[1:] + p[:1]):
            e = (a, b) if a < b else (b, a)
            cnt[e] = cnt.get(e, 0) + 1
    other = [i for i in range(3) if i != axis]
    out = set()
    for (a, b), n in cnt.items():
        if n == 1 and v[a][axis] == value and v[b][axis] == value:
            out.add(tuple(v[a][i] for i in other))
            out.add(tuple(v[b][i] for i in other))
    return out


def main():
    out = sys.argv[1]
    quick = "--quick" in sys.argv
    errs, warn = [], []
    with open(os.path.join(out, "manifest.json"), encoding="utf-8") as fh:
        text = fh.read()
    man = json.loads(text)
    if has_banned(text):
        errs.append("manifest contains a real-place string")
    meshes, insts = man["meshes"], man["instances"]
    tiles = {}
    n_ubx = n_ucx = 0
    for name, m in sorted(meshes.items()):
        path = os.path.join(out, m["file"])
        if not os.path.isfile(path):
            errs.append(f"{name}: missing {m['file']}")
            continue
        if os.path.splitext(os.path.basename(path))[0] != name or not re.fullmatch(r"SM_[A-Za-z0-9_]+", name):
            errs.append(f"{name}: bad asset/file name")
        with open(path, "rb") as fh:
            raw = fh.read()
        if bytes_banned(raw):
            errs.append(f"{name}: real-place string inside the FBX")
        if quick and m.get("collision", {}).get("kind") not in ("boxes", "convex", "stairs") and "tile" not in m:
            continue
        f = read(path)
        if any(f["axes"].get(k) != v for k, v in EXPECT_AXES.items()) or f["unit"] != 1.0:
            errs.append(f"{name}: axis/unit header {f['axes']} unit={f['unit']}")
        if f["parented"]:
            errs.append(f"{name}: parented nodes {f['parented']} (UE-239476: keep flat)")
        render = [k for k in f["models"] if not re.match(r"U(BX|CX|SP|CP)_", k)]
        if render != [name]:
            errs.append(f"{name}: render nodes {render}")
        c = m["collision"]
        got = {"UBX": 0, "UCX": 0}
        for k, mod in f["models"].items():
            mm = re.fullmatch(r"(UBX|UCX)_(.+)_(\d\d)", k)
            if k == name:
                if any(abs(x) > 1e-9 for x in mod["lcl_r"]) or any(abs(x) > 1e-9 for x in mod["lcl_t"]):
                    errs.append(f"{name}: render node not at the origin")
                continue
            if not mm or mm.group(2) != name:
                errs.append(f"{name}: collision node {k!r} does not pair with the mesh")
                continue
            got[mm.group(1)] += 1
            if len(mod["verts"]) < 4:
                errs.append(f"{k}: degenerate hull")
            if mm.group(1) == "UBX":
                vs = mod["verts"]
                ok = len(vs) == 8 and all(len({round(p[i], 4) for p in vs}) == 2 for i in range(3))
                if not ok:
                    errs.append(f"{k}: UBX is not an axis-aligned box")
        if got["UBX"] != c["ubx"] or got["UCX"] != c["ucx"]:
            errs.append(f"{name}: collision count file {got} vs manifest ubx={c['ubx']} ucx={c['ucx']}")
        if c["kind"] in ("boxes", "convex", "stairs") and not (got["UBX"] + got["UCX"]):
            errs.append(f"{name}: kind {c['kind']} without collision nodes")
        n_ubx += got["UBX"]
        n_ucx += got["UCX"]
        if "tile" in m:
            tiles[tuple(m["tile"])] = f["models"][name]
    # seams: right/top neighbour shares exactly the same border vertices (file units = cm, tile-local)
    side = man["tile_m"] * 100.0
    seams = bad = 0
    for (i, j), mod in tiles.items():
        for di, dj, axis in ((1, 0, 0), (0, 1, 1)):
            nb = tiles.get((i + di, j + dj))
            if nb is None:
                continue
            a, b = _border(mod, axis, side), _border(nb, axis, 0.0)
            seams += 1
            if a != b:
                bad += 1
                errs.append(f"seam {i},{j} -> {i + di},{j + dj}: {len(a ^ b)} unmatched of {len(a)}/{len(b)}")
    for e in insts:
        if e["mesh"] not in meshes:
            errs.append(f"instance {e['name']}: unknown mesh {e['mesh']}")
        if e["role"] == "placeholder" and not e["ue_asset"]:
            errs.append(f"instance {e['name']}: placeholder without slot")
    for root, _, files in os.walk(out):
        for fn in files:
            if has_banned(fn):
                errs.append(f"real-place string in file name {fn}")
    size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(out) for f in fs if not r.endswith("_cache"))
    s = man["stats"]
    print(f"check: {len(meshes)} meshes, {len(insts)} instances, {s['placeholders']} placeholders, "
          f"ubx={n_ubx} ucx={n_ucx}, tiles={len(tiles)} seams={seams} bad={bad}, {size / 1e6:.1f} MB")
    for w in warn:
        print("warn:", w)
    for e in errs[:50]:
        print("ERROR:", e)
    print(f"check: {'FAIL' if errs else 'OK'} ({len(errs)} errors)")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
