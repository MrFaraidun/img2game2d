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


def defringe_alpha(
    img: "Image.Image",
    edge_tone: Tuple[int, int, int] = (14, 14, 20),
    luminance_threshold: int = 180,
    erode_bleed: bool = True,
) -> "Image.Image":
    """
    Remove white/light background matting halos around alpha boundaries.
    Detects high-luminance anti-aliased edge pixels along the boundary and shifts
    them toward the dark outline tone, with optional 1-pixel outer erosion.
    """
    require_pil()
    require_numpy()

    rgba = ensure_rgba(img)
    arr = np.array(rgba).copy()
    alpha = arr[:, :, 3]

    # Boundary zone: anti-aliased transition pixels
    boundary_mask = (alpha > 5) & (alpha < 240)

    if np.any(boundary_mask):
        # Calculate pixel luminance (standard Rec. 601)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        lum = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)

        # Pixels that are both on the alpha boundary AND light/whitish
        fringe_mask = boundary_mask & (lum > luminance_threshold)

        # Tone shift: replace fringed RGB with edge outline tone while preserving smooth alpha
        arr[fringe_mask, 0] = edge_tone[0]
        arr[fringe_mask, 1] = edge_tone[1]
        arr[fringe_mask, 2] = edge_tone[2]

    # Optional 1-pixel alpha erosion for severe halo bleed
    if erode_bleed:
        from PIL import ImageFilter
        alpha_img = Image.fromarray(alpha)
        # MinFilter erodes alpha contour by 1 pixel
        eroded_alpha = np.array(alpha_img.filter(ImageFilter.MinFilter(3)))
        # Only erode very soft fringes
        arr[:, :, 3] = np.where(boundary_mask & (alpha < 80), eroded_alpha, arr[:, :, 3])

    return Image.fromarray(arr)


def enhance_image(
    img: "Image.Image",
    scale: float = 2.0,
    clarity_strength: float = 1.3,
    denoise: bool = True,
    seal_outlines: bool = True,
) -> "Image.Image":
    """
    Enhance character sprite resolution, edge sharpness, and outline clarity.
    Applies high-order Lanczos super-sampling, contrast-adaptive sharpening,
    and optional dark outline sealing.
    """
    require_pil()
    require_numpy()

    rgba = ensure_rgba(img)
    orig_w, orig_h = rgba.size
    target_w = max(1, int(orig_w * scale))
    target_h = max(1, int(orig_h * scale))

    # 1. Super-sample with high-order Lanczos filter
    upscaled = rgba.resize((target_w, target_h), Image.LANCZOS)

    # 2. Separate RGB and Alpha channels for independent enhancement
    r, g, b, a = upscaled.split()
    rgb = Image.merge("RGB", (r, g, b))

    # Optional gentle median filter to remove diffusion noise / JPEG blockiness
    if denoise:
        rgb = rgb.filter(ImageFilter.MedianFilter(size=3))

    # 3. Smart Unsharp Masking for crisp inking lines without ringing
    radius = 1.5
    percent = int(120 * clarity_strength)
    threshold = 3
    sharpened = rgb.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))

    # 4. Cel-edge dark line sealing (deepens ink outlines and eliminates blurry edges)
    if seal_outlines:
        arr_rgb = np.array(sharpened).astype(np.float32)
        lum = 0.299 * arr_rgb[:, :, 0] + 0.587 * arr_rgb[:, :, 1] + 0.114 * arr_rgb[:, :, 2]
        # Dark lines (lum < 60) get boosted contrast / deepening
        dark_mask = (lum < 75)[:, :, np.newaxis]
        arr_rgb = np.where(dark_mask, arr_rgb * 0.82, arr_rgb)
        sharpened = Image.fromarray(np.clip(arr_rgb, 0, 255).astype(np.uint8))

    # Recombine with alpha
    res_r, res_g, res_b = sharpened.split()
    enhanced = Image.merge("RGBA", (res_r, res_g, res_b, a))

    # Clean any residual fringes
    return defringe_alpha(enhanced)

