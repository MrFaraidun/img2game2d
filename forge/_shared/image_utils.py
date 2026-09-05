"""
img2game2d shared image utilities.
Wraps PIL/OpenCV for consistent image operations across all forge scripts.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image, ImageFilter, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def require_pil() -> None:
    if not PIL_AVAILABLE:
        raise ImportError("Pillow is required: pip install Pillow")


def require_numpy() -> None:
    if not NUMPY_AVAILABLE:
        raise ImportError("NumPy is required: pip install numpy")


def load_image(path: str) -> "Image.Image":
    require_pil()
    img = Image.open(path)
    if img.mode not in ("RGBA", "RGB", "L"):
        img = img.convert("RGBA")
    return img


def ensure_rgba(img: "Image.Image") -> "Image.Image":
    if img.mode != "RGBA":
        return img.convert("RGBA")
    return img


def save_image(img: "Image.Image", path: str, format: str = "PNG") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format=format)


def crop_to_content(img: "Image.Image", padding: int = 2) -> Tuple["Image.Image", Tuple[int, int, int, int]]:
    """Crop image to non-transparent bounding box. Returns (cropped, bbox)."""
    require_pil()
    rgba = ensure_rgba(img)
    bbox = rgba.getbbox()
    if bbox is None:
        return img, (0, 0, img.width, img.height)
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(img.width, x2 + padding)
    y2 = min(img.height, y2 + padding)
    return img.crop((x1, y1, x2, y2)), (x1, y1, x2, y2)


def dominant_colors(img: "Image.Image", n: int = 8) -> list[Tuple[int, int, int]]:
    """Return n dominant colors from image using quantization."""
    require_pil()
    small = img.convert("RGB").resize((64, 64))
    quantized = small.quantize(colors=n)
    palette = quantized.getpalette()
    if palette is None:
        return []
    return [(palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]) for i in range(n)]


def resize_power_of_two(img: "Image.Image") -> "Image.Image":
    """Resize image to nearest power-of-two dimensions."""
    require_pil()
    import math
    w = 2 ** math.ceil(math.log2(img.width)) if img.width > 1 else 1
    h = 2 ** math.ceil(math.log2(img.height)) if img.height > 1 else 1
    return img.resize((w, h), Image.NEAREST)


def alpha_composite_onto_white(img: "Image.Image") -> "Image.Image":
    """Flatten RGBA onto white background for comparison."""
    require_pil()
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
    return bg.convert("RGB")


def compute_iou_silhouette(img_a: "Image.Image", img_b: "Image.Image") -> float:
    """
    Compute Intersection over Union of the alpha channel silhouettes.
    Returns value in [0, 1].
    """
    require_pil()
    require_numpy()

    def get_mask(img: "Image.Image") -> "np.ndarray":
        rgba = ensure_rgba(img.resize(img_a.size, Image.LANCZOS))
        alpha = np.array(rgba.split()[3]) > 10
        return alpha

    mask_a = get_mask(img_a)
    mask_b = get_mask(img_b)
    intersection = (mask_a & mask_b).sum()
    union = (mask_a | mask_b).sum()
    if union == 0:
        return 1.0
    return float(intersection) / float(union)


def compute_color_similarity(img_a: "Image.Image", img_b: "Image.Image") -> float:
    """
    Compare dominant color palettes. Returns similarity in [0, 1].
    Uses histogram correlation.
    """
    require_pil()
    require_numpy()

    def hist(img: "Image.Image") -> "np.ndarray":
        rgb = img.convert("RGB").resize((64, 64))
        h, _ = np.histogramdd(np.array(rgb).reshape(-1, 3), bins=16, range=[(0, 256)] * 3)
        h = h / h.sum()
        return h.flatten()

    h_a = hist(img_a)
    h_b = hist(img_b)
    # Bhattacharyya coefficient
    bc = float(np.sum(np.sqrt(h_a * h_b)))
    return min(1.0, max(0.0, bc))


def next_power_of_two(n: int) -> int:
    import math
    return 2 ** math.ceil(math.log2(max(n, 1)))
