"""
img2game2d transform and deformation math.
Provides mathematically exact inverse-affine matrix formulas for PIL,
non-linear continuous deformation for lower-body/cloaks, and gap sealing.
"""
from __future__ import annotations

import math
from typing import Tuple

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


def get_inverse_affine_matrix(
    cx: float,
    cy: float,
    angle_rad: float,
    dx: float = 0.0,
    dy: float = 0.0,
    sx: float = 1.0,
    sy: float = 1.0,
) -> Tuple[float, float, float, float, float, float]:
    """
    Compute the exact 6-parameter affine tuple (a, b, c, d, e, f) for PIL Image.transform.

    PIL's Image.AFFINE uses INVERSE coordinate mapping:
        input_x = a * output_x + b * output_y + c
        input_y = d * output_x + e * output_y + f

    This function inverts the forward transformation:
        Scale(sx, sy) -> Rotate(angle_rad) around (cx, cy) -> Translate(dx, dy)
    guaranteeing that rotating and scaling around (cx, cy) never inverts, shears,
    or drifts away from the intended pivot.
    """
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    inv_sx = 1.0 / max(sx, 1e-5)
    inv_sy = 1.0 / max(sy, 1e-5)

    a = cos_a * inv_sx
    b = sin_a * inv_sx
    c = cx - (cos_a * (cx + dx) + sin_a * (cy + dy)) * inv_sx

    d = -sin_a * inv_sy
    e = cos_a * inv_sy
    f = cy - (-sin_a * (cx + dx) + cos_a * (cy + dy)) * inv_sy

    return (a, b, c, d, e, f)


def transform_layer(
    img: "Image.Image",
    pivot: Tuple[float, float],
    angle_rad: float = 0.0,
    dx: float = 0.0,
    dy: float = 0.0,
    sx: float = 1.0,
    sy: float = 1.0,
) -> "Image.Image":
    """
    Transform an RGBA layer around a pivot point using exact inverse affine math.
    """
    if not PIL_AVAILABLE:
        raise ImportError("Pillow is required for transform_layer")

    cx, cy = pivot
    matrix = get_inverse_affine_matrix(cx, cy, angle_rad, dx=dx, dy=dy, sx=sx, sy=sy)
    return img.transform(img.size, Image.AFFINE, matrix, resample=Image.BILINEAR)


def apply_continuous_shear(
    img: "Image.Image",
    hip_y: float,
    stride_pixels: float,
    span: float = 120.0,
) -> "Image.Image":
    """
    Apply non-linear continuous shear deformation below hip_y.
    This prevents characters with cloaks, robes, or contiguous lower bodies
    from tearing or breaking into disconnected rectangular chunks.

    Displacement increases smoothly from 0 at hip_y to stride_pixels at (hip_y + span).
    """
    if not PIL_AVAILABLE or not NUMPY_AVAILABLE:
        raise ImportError("Pillow and NumPy are required for apply_continuous_shear")

    arr = np.array(img.convert("RGBA"))
    h, w = arr.shape[:2]
    out = np.zeros_like(arr)

    # Precalculate y coordinates
    yy = np.arange(h).reshape(-1, 1)
    xx = np.arange(w).reshape(1, -1)

    # Smooth non-linear weight factor below hip_y
    weight = np.clip((yy - hip_y) / max(span, 1e-4), 0.0, 1.0) ** 1.2
    shift_x = (weight * stride_pixels).astype(np.float32)

    # Compute source x coordinates for inverse sampling
    src_x = np.round(xx - shift_x).astype(np.int32)
    valid_mask = (src_x >= 0) & (src_x < w)

    # Vectorized gathering
    for y in range(h):
        valid = valid_mask[y]
        out[y, valid] = arr[y, src_x[y, valid]]

    return Image.fromarray(out)


def inpaint_contact_seam(
    img: "Image.Image",
    seam_box: Tuple[int, int, int, int],
    fill_color: Tuple[int, int, int, int] = (20, 20, 24, 255),
) -> "Image.Image":
    """
    Fills gaps or voids along joint contact seams (e.g. pelvic/neck intersections)
    to eliminate transparent tears during rotation.
    """
    if not PIL_AVAILABLE or not NUMPY_AVAILABLE:
        raise ImportError("Pillow and NumPy are required for inpaint_contact_seam")

    arr = np.array(img.convert("RGBA")).copy()
    x1, y1, x2, y2 = seam_box
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(arr.shape[1], x2), min(arr.shape[0], y2)

    region = arr[y1:y2, x1:x2]
    # Identify transparent or semi-transparent holes inside the seam box
    hole_mask = region[:, :, 3] < 200
    if np.any(hole_mask):
        region[hole_mask] = fill_color
        arr[y1:y2, x1:x2] = region

    return Image.fromarray(arr)
