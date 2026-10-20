# Output naming + real-name guard for ue_prep (stdlib only, shared by run.py and the offline check.py).
import re

TILE_INDEX_OFFSET = 50   # tile name index = i + 50 keeps names positive/sortable (SM_Ground_X50_Y50 = tile at origin)

# Real-place / "university" strings that must never reach an output (AGENTS.md lore rules); same pattern as
# Scripts/Blender/scene_qa.py FORBIDDEN.
FORBIDDEN = re.compile(r"ala.?too|\baiu\b|iaau|university|универ", re.I)


def has_banned(text):
    return bool(FORBIDDEN.search(text))


def bytes_banned(raw):
    """Same check on raw file bytes (FBX strings are UTF-8)."""
    return has_banned(raw.decode("utf-8", "replace"))


def ascii_name(s, maxlen=40):
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s.encode("ascii", "ignore").decode()).strip("_")
    s = re.sub(r"_+", "_", s)
    return s[:maxlen].rstrip("_") or "Mesh"


def role_of(obj_name):
    """Object name -> asset role: drop the GBF_/GBS_/GB_ prefix and trailing index groups (_E2_15, _B0_3, _7)."""
    n = re.sub(r"^(GBF|GBS|GB)_", "", obj_name)
    n = re.sub(r"\.\d{3}$", "", n)
    n = re.sub(r"(_[A-Z]?\d+)+$", "", n)
    return ascii_name(n, 36)


def tile_name(i, j):
    return f"SM_Ground_X{i + TILE_INDEX_OFFSET:02d}_Y{j + TILE_INDEX_OFFSET:02d}"
