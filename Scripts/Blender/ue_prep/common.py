# Shared constants and Blender->UE conversions for the ue_prep hand-off pipeline (run.py, roundtrip.py, check.py).
# Pure python + numpy (no bpy), so check.py and the tests can import it outside Blender.
#
# Coordinate convention (verified by roundtrip.py on the exported FBX headers):
#   FBX written with Epic Send2UE settings (axis_forward Y, axis_up Z, apply_unit_scale, FBX_SCALE_NONE): the file
#   declares Z-up / front -Y / right-handed (Blender's own system, == the system UE's FBX importer converts to), unit cm.
#   UE's FBX importer then mirrors Y (left-handed): UE point = S * Blender point * 100, with S = diag(1, -1, 1).
#   Mesh assets: v_ue = 100 * S v_local. Actor: R_ue = S R S, t_ue = 100 * S t, scale unchanged.
#   Sources: github.com/EpicGamesExt/BlenderTools send2ue/resources/settings.json (export settings),
#   send2ue/core/utilities.py convert_blender_to_unreal_location -> [x*100, -y*100, z*100].
import math

import numpy as np

from .names import TILE_INDEX_OFFSET, ascii_name, has_banned, role_of, tile_name   # noqa: F401  (re-export)

SKIP_COLLECTIONS = ("00_Reference", "REF_Satellite", "REF_Plans", "99_Replaced_Phase1")
SKIP_PREFIX = ("REF_", "CAM_")
TERRAIN = "TER_Ground"
BARRIER_PREFIX = "GBS_Barriers"
UE_ROOT = "/Game/KochSimulator/Greybox"

# 64 m terrain tiles: 2x2 tiles per 128 m World Partition cell (UE 5.x MainGrid default 12800 uu), so tile borders
# fall on cell borders and no tile straddles a cell. Tile index i covers x in [64 i, 64 (i+1)) m.
TILE_M = 64.0

MM = 1000.0              # dedup grid: 1 mm
S_FLIP = np.diag([1.0, -1.0, 1.0])

# ---- transforms -------------------------------------------------------------------------------------------------

def rotator_from_ue_matrix(r):
    """UE FRotator (pitch, yaw, roll) in degrees from a 3x3 UE rotation (columns = images of the local X/Y/Z axes).
    Port of FMatrix::Rotator() (Engine/Source/Runtime/Core/Private/Math/UnrealMath.cpp)."""
    x, y, z = r[:, 0], r[:, 1], r[:, 2]
    pitch = math.atan2(x[2], math.hypot(x[0], x[1]))
    yaw = math.atan2(x[1], x[0])
    sy_axis = np.array([-math.sin(yaw), math.cos(yaw), 0.0])   # Y axis of FRotationMatrix(pitch, yaw, 0)
    roll = math.atan2(float(z @ sy_axis), float(y @ sy_axis))
    return [math.degrees(pitch), math.degrees(yaw), math.degrees(roll)]


def ue_matrix_from_rotator(pitch, yaw, roll):
    """Inverse of rotator_from_ue_matrix: FRotationTranslationMatrix rows (UE row-vector convention) as columns."""
    p, y, r = (math.radians(a) for a in (pitch, yaw, roll))
    sp, cp, sy, cy, sr, cr = math.sin(p), math.cos(p), math.sin(y), math.cos(y), math.sin(r), math.cos(r)
    rows = np.array([[cp * cy, cp * sy, sp],
                     [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp],
                     [-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp]])
    return rows.T


def blender_to_ue(m4, scale=(1.0, 1.0, 1.0)):
    """Rigid Blender world matrix (4x4, metres) + local scale -> UE {loc cm, rot [pitch, yaw, roll] deg, scale}."""
    m4 = np.asarray(m4, dtype=np.float64)
    r_ue = S_FLIP @ m4[:3, :3] @ S_FLIP
    loc = S_FLIP @ m4[:3, 3] * 100.0
    rot = rotator_from_ue_matrix(r_ue)
    return {"loc": [round(float(v), 4) for v in loc], "rot": [round(v, 6) + 0.0 for v in rot],
            "scale": [round(float(s), 6) for s in scale]}


def ue_to_blender(loc, rot, scale=(1.0, 1.0, 1.0)):
    """Inverse of blender_to_ue -> 4x4 Blender world matrix (metres) incl. scale; used by roundtrip.py/check.py."""
    m = np.eye(4)
    m[:3, :3] = S_FLIP @ ue_matrix_from_rotator(*rot) @ S_FLIP @ np.diag(scale)
    m[:3, 3] = S_FLIP @ np.asarray(loc, dtype=np.float64) / 100.0
    return m


def rot_z90(k):
    """Exact 3x3 rotation by k * 90 degrees about Z."""
    c, s = [(1, 0), (0, 1), (-1, 0), (0, -1)][k % 4]
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)


# ---- box-projection UVs ------------------------------------------------------------------------------------------

def box_uvs(loop_co, face_normals, loop_face):
    """World-scale box projection (1 m = 1 UV), per face axis from the dominant normal; u runs to the viewer's right
    on every side so textures are never mirrored. loop_co (L,3) m, face_normals (F,3), loop_face (L,) -> (L,2)."""
    n = face_normals[loop_face]
    ax = np.abs(n).argmax(1)
    sg = np.sign(n[np.arange(len(n)), ax])
    sg[sg == 0] = 1
    x, y, z = loop_co[:, 0], loop_co[:, 1], loop_co[:, 2]
    u = np.where(ax == 0, sg * y, np.where(ax == 1, -sg * x, x))
    v = np.where(ax == 2, sg * y, z)
    return np.stack([u, v], 1)
