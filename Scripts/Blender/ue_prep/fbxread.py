# Minimal binary-FBX reader (stdlib only) for ue_prep check.py / roundtrip.py: global axis settings, mesh models with
# their vertices, polygons and local transforms. Format: code.blender.org/2013/08/fbx-binary-file-format-specification
import struct
import zlib

_ARR = {"f": ("f", 4), "d": ("d", 8), "l": ("q", 8), "i": ("i", 4), "b": ("?", 1)}
_SCALAR = {"Y": ("<h", 2), "C": ("<?", 1), "I": ("<i", 4), "F": ("<f", 4), "D": ("<d", 8), "L": ("<q", 8)}


def _props(data, pos, n):
    out = []
    for _ in range(n):
        t = chr(data[pos])
        pos += 1
        if t in _SCALAR:
            fmt, sz = _SCALAR[t]
            out.append(struct.unpack_from(fmt, data, pos)[0])
            pos += sz
        elif t in _ARR:
            ln, enc, clen = struct.unpack_from("<III", data, pos)
            pos += 12
            raw = data[pos:pos + clen]
            pos += clen
            if enc == 1:
                raw = zlib.decompress(raw)
            c, sz = _ARR[t]
            out.append(list(struct.unpack(f"<{ln}{c}", raw[:ln * sz])))
        elif t in "SR":
            ln = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            b = data[pos:pos + ln]
            pos += ln
            out.append(b.decode("utf-8", "replace") if t == "S" else b)
        else:
            raise ValueError(f"fbxread: unknown property type {t!r} at {pos}")
    return out, pos


def _node(data, pos, wide):
    if wide:
        end, n, _ = struct.unpack_from("<QQQ", data, pos)
        pos += 24
    else:
        end, n, _ = struct.unpack_from("<III", data, pos)
        pos += 12
    nlen = data[pos]
    pos += 1
    if end == 0:
        return None, pos
    name = data[pos:pos + nlen].decode()
    pos += nlen
    props, pos = _props(data, pos, n)
    kids = []
    while pos < end:
        k, pos = _node(data, pos, wide)
        if k is None:
            break
        kids.append(k)
    return (name, props, kids), end


def parse(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if not data.startswith(b"Kaydara FBX Binary  \x00"):
        raise ValueError(f"fbxread: not a binary FBX: {path}")
    ver = struct.unpack_from("<I", data, 23)[0]
    pos, top = 27, []
    while pos < len(data):
        n, pos = _node(data, pos, ver >= 7500)
        if n is None:
            break
        top.append(n)
    return top, ver


def _child(node, name):
    return next((k for k in node[2] if k[0] == name), None)


def _p70(node):
    p = _child(node, "Properties70")
    return {k[1][0]: k[1][4:] for k in p[2]} if p else {}


def read(path):
    """-> {"axes": {...}, "unit": float, "models": {name: {"lcl_t", "lcl_r", "lcl_s", "verts", "polys"}}}."""
    top, ver = parse(path)
    t = {n[0]: n for n in top}
    gs = _p70(t["GlobalSettings"])
    axes = {k: gs.get(k, [None])[0] for k in ("UpAxis", "UpAxisSign", "FrontAxis", "FrontAxisSign", "CoordAxis",
                                              "CoordAxisSign")}
    geoms, models, conns = {}, {}, []
    for o in t["Objects"][2]:
        if o[0] == "Geometry":
            v = _child(o, "Vertices")
            pv = _child(o, "PolygonVertexIndex")
            geoms[o[1][0]] = (v[1][0] if v else [], pv[1][0] if pv else [])
        elif o[0] == "Model":
            p = _p70(o)
            models[o[1][0]] = {"name": o[1][1].split("\x00")[0], "lcl_t": p.get("Lcl Translation", [0, 0, 0]),
                               "lcl_r": p.get("Lcl Rotation", [0, 0, 0]), "lcl_s": p.get("Lcl Scaling", [1, 1, 1])}
    for c in t.get("Connections", ("", [], []))[2]:
        if c[0] == "C" and c[1][0] == "OO":
            conns.append((c[1][1], c[1][2]))
    out = {}
    for child, parent in conns:
        if child in geoms and parent in models:
            m = models[parent]
            v, pv = geoms[child]
            polys, cur = [], []
            for i in pv:
                if i < 0:
                    cur.append(~i)
                    polys.append(cur)
                    cur = []
                else:
                    cur.append(i)
            out[m["name"]] = {"lcl_t": m["lcl_t"], "lcl_r": m["lcl_r"], "lcl_s": m["lcl_s"],
                              "verts": [tuple(v[i:i + 3]) for i in range(0, len(v), 3)], "polys": polys}
    roots = {models[c]["name"] for c, p in conns if c in models and p != 0 and p in models}
    return {"version": ver, "axes": axes, "unit": gs.get("UnitScaleFactor", [None])[0], "models": out,
            "parented": sorted(roots)}
