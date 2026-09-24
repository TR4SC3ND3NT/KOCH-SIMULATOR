# Metric rectification of a building facade from one photo (single-view metrology), for R1 facade specs.
# Method: vertical + facade-horizontal vanishing points (OpenCV LSD segments, RANSAC) + intrinsics from EXIF
# (35 mm-equivalent focal) give the facade plane orientation; the photo is warped to a fronto-parallel view.
# Scale comes from one known length on the facade (e.g. the footprint edge length) via --scale X0 X1 METRES.
# Refs: Criminisi, Reid, Zisserman, "Single View Metrology", IJCV 2000; Hartley & Zisserman ch. 8.
# Run: uv run --project Scripts python Scripts/Geo/facade_rectify.py photo.jpg out_prefix [--hor-range -40 40]
#      [--scale 812 3890 30.64] [--grid 0.5]   (scale x positions are in the unscaled rectified image, px)
import argparse
import json
import math

import cv2
import numpy as np
from PIL import Image, ImageOps

DIAG_35MM = math.hypot(36.0, 24.0)  # 43.27 mm: 35 mm-equivalent focal is defined on the diagonal


def load_photo(path, f35_override=None):
    im = Image.open(path)
    exif = im.getexif().get_ifd(0x8769)
    f35 = float(f35_override or exif.get(41989) or 0)  # FocalLengthIn35mmFilm; video frames need --f35
    im = ImageOps.exif_transpose(im).convert("RGB")
    rgb = np.asarray(im)
    h, w = rgb.shape[:2]
    if not f35:
        raise SystemExit("no 35 mm focal in EXIF: pass --f35 (video frames: ~26 mm for Pixel 9 4K with EIS)")
    f = f35 * math.hypot(w, h) / DIAG_35MM
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]])
    return rgb, K, f35


def segments(gray, min_len):
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    lines = lsd.detect(gray)[0]
    if lines is None:
        return np.zeros((0, 4))
    s = lines.reshape(-1, 4)
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    return s[L >= min_len]


def ransac_vp(seg, iters=3000, tol_deg=1.0, seed=0):
    """Vanishing point (homogeneous) supported by the most segment length; returns (vp, inlier mask)."""
    rng = np.random.default_rng(seed)
    p1 = np.column_stack([seg[:, :2], np.ones(len(seg))])
    p2 = np.column_stack([seg[:, 2:], np.ones(len(seg))])
    lines = np.cross(p1, p2)
    mid = (seg[:, :2] + seg[:, 2:]) / 2
    d = seg[:, 2:] - seg[:, :2]
    L = np.hypot(d[:, 0], d[:, 1])
    d = d / L[:, None]
    best, best_score, best_in = None, -1, None
    tol = math.radians(tol_deg)
    for _ in range(iters):
        i, j = rng.choice(len(seg), 2, replace=False)
        vp = np.cross(lines[i], lines[j])
        if np.linalg.norm(vp) < 1e-12:
            continue
        inl = _inliers(vp, mid, d, tol)
        score = L[inl].sum()
        if score > best_score:
            best, best_score, best_in = vp, score, inl
    # Refine: least-squares VP of all inlier lines (smallest singular vector).
    A = lines[best_in] / np.linalg.norm(lines[best_in][:, :2], axis=1)[:, None]
    vp = np.linalg.svd(A * L[best_in][:, None])[2][-1]
    return vp, _inliers(vp, mid, d, tol)


def _inliers(vp, mid, d, tol):
    if abs(vp[2]) > 1e-9 * np.linalg.norm(vp):
        to = vp[:2] / vp[2] - mid
    else:  # VP at infinity: direction only
        to = np.tile(vp[:2], (len(mid), 1))
    to = to / (np.linalg.norm(to, axis=1)[:, None] + 1e-12)
    c = np.abs((to * d).sum(1))
    return c > math.cos(tol)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("out")
    ap.add_argument("--hor-range", type=float, nargs=2, default=[-45.0, 45.0],
                    help="image angle range (deg, 0 = horizontal) of the facade's horizontal lines")
    ap.add_argument("--min-len", type=float, default=60.0, help="min segment length, px")
    ap.add_argument("--width", type=int, default=3000, help="rectified output width, px")
    ap.add_argument("--scale", type=float, nargs=3, metavar=("X0", "X1", "M"),
                    help="two x positions in the rectified image (px) that are M metres apart along the facade")
    ap.add_argument("--grid", type=float, default=0.5, help="metric grid step (m), needs --scale")
    ap.add_argument("--f35", type=float, help="35 mm-equivalent focal override (video frames have no EXIF)")
    ap.add_argument("--solve-f", action="store_true",
                    help="solve the focal from the two (orthogonal) vanishing points instead of EXIF")
    ap.add_argument("--roi", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"),
                    help="use only segments inside this box (fractions of the photo), e.g. to skip ground paving")
    a = ap.parse_args()

    rgb, K, f35 = load_photo(a.photo, a.f35)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    seg = segments(gray, a.min_len)
    if a.roi:
        h0, w0 = gray.shape
        mx, my = (seg[:, 0] + seg[:, 2]) / 2 / w0, (seg[:, 1] + seg[:, 3]) / 2 / h0
        seg = seg[(mx >= a.roi[0]) & (mx <= a.roi[2]) & (my >= a.roi[1]) & (my <= a.roi[3])]
    ang = np.degrees(np.arctan2(seg[:, 3] - seg[:, 1], seg[:, 2] - seg[:, 0]))
    ang = (ang + 90) % 180 - 90  # -90..90, 0 = horizontal
    vert = seg[np.abs(ang) > 70]
    hor = seg[(ang >= a.hor_range[0]) & (ang <= a.hor_range[1])]
    vv, vin = ransac_vp(vert)
    vh, hin = ransac_vp(hor)
    if a.solve_f:  # orthogonal VPs: (v1 - c).(v2 - c) + f^2 = 0 (square pixels, principal point at centre)
        c0 = K[:2, 2]
        if abs(vv[2]) > 1e-9 and abs(vh[2]) > 1e-9:
            d = -((vv[:2] / vv[2] - c0) @ (vh[:2] / vh[2] - c0))
            if d > 0:
                K[0, 0] = K[1, 1] = math.sqrt(d)
                f35 = K[0, 0] * DIAG_35MM / math.hypot(*gray.shape[::-1])
                print("solved focal: %.0f px (%.1f mm-eq)" % (K[0, 0], f35))
    Ki = np.linalg.inv(K)
    up = Ki @ vv
    up /= np.linalg.norm(up)
    if up[1] > 0:  # image y points down: facade up must have negative camera-y
        up = -up
    hx = Ki @ vh
    hx -= up * (hx @ up)  # orthogonalise against up (VP noise)
    hx /= np.linalg.norm(hx)
    if hx[0] < 0:
        hx = -hx  # facade +u to the image right
    n = np.cross(hx, up)
    ortho_err = math.degrees(math.acos(min(1.0, abs((Ki @ vh / np.linalg.norm(Ki @ vh)) @ up))))

    # Plane-to-image homography with the plane at unit depth along the principal ray: x ~ K [hx up c] (u, w, 1).
    c = np.array([0.0, 0.0, 1.0])
    H = K @ np.column_stack([hx, -up, c])  # -up so that rectified +y points down like an image
    Hi = np.linalg.inv(H)
    h, w = gray.shape
    corners = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], float).T
    pc = Hi @ corners
    pc = pc[:2] / pc[2]
    x0, y0 = pc[0].min(), pc[1].min()
    x1, y1 = pc[0].max(), pc[1].max()
    s = a.width / (x1 - x0)
    out_h = int((y1 - y0) * s)
    if out_h > 4 * a.width:  # horizon inside the photo: clip the sky side
        out_h = 4 * a.width
    T = np.array([[s, 0, -x0 * s], [0, s, -y0 * s], [0, 0, 1]])
    M = T @ Hi
    rect = cv2.warpPerspective(rgb, M, (a.width, out_h), flags=cv2.INTER_LINEAR)

    meta = {"photo": a.photo, "f35_mm": f35, "K": K.tolist(), "vp_vertical": (vv / vv[2]).tolist() if abs(vv[2]) > 1e-9 else vv.tolist(),
            "vp_horizontal": (vh / vh[2]).tolist() if abs(vh[2]) > 1e-9 else vh.tolist(),
            "n_segments": [int(vin.sum()), int(hin.sum())], "vp_orthogonality_err_deg": round(90 - ortho_err, 2),
            "facade_normal_cam": n.tolist(), "image_to_rect": M.tolist(), "rect_size": [a.width, out_h]}
    img = Image.fromarray(rect)
    if a.scale:
        X0, X1, metres = a.scale
        mpp = metres / abs(X1 - X0)  # metres per rectified pixel
        meta["m_per_px"] = mpp
        from PIL import ImageDraw
        dr = ImageDraw.Draw(img)
        step = a.grid / mpp
        k = 0
        x = min(X0, X1)
        while x > 0:
            x -= step
        while x < a.width:
            col = (255, 255, 0) if round((x - min(X0, X1)) / step) % 10 == 0 else (0, 255, 255)
            dr.line([(x, 0), (x, out_h)], fill=col, width=1)
            x += step
            k += 1
        y = out_h
        j = 0
        while y > 0:
            dr.line([(0, y), (a.width, y)], fill=(255, 255, 0) if j % 10 == 0 else (0, 255, 255), width=1)
            y -= step
            j += 1
    img.save(a.out + ".jpg", quality=92)
    json.dump(meta, open(a.out + ".json", "w"), indent=1)
    print("segments v/h:", meta["n_segments"], "VP orthogonality error (deg):", meta["vp_orthogonality_err_deg"],
          "out", a.width, "x", out_h)


if __name__ == "__main__":
    main()
