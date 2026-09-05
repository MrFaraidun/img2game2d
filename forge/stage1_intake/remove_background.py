#!/usr/bin/env python3
"""
Stage 1: Background removal.
Removes background from character/object images, preserving foreground.

Strategy (in order of preference):
  1. If image already has transparent BG (RGBA with alpha) — strip and use directly
  2. Solid color background — chroma key removal
  3. Complex background — rembg (if installed) or GrabCut (OpenCV)
  4. Fallback: save original with note

Usage:
    python3 forge/stage1_intake/remove_background.py character.png \
        --out source/foreground.png \
        --mask source/mask.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def remove_background(
    image_path: str,
    out_path: str,
    mask_path: str | None = None,
    method: str = "auto",
    bg_color: tuple | None = None,
    tolerance: int = 30,
) -> dict:
    """
    Remove background from image.

    Returns dict with:
        method_used: which strategy was applied
        confidence: estimated quality of removal
        output: path to foreground PNG
        mask: path to mask PNG
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        print("ERROR: Pillow and NumPy required: pip install Pillow numpy", file=sys.stderr)
        sys.exit(1)

    img = Image.open(image_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    from _shared.image_utils import defringe_alpha

    # Strategy 1: Already has clean transparency
    if img.mode == "RGBA":
        arr = np.array(img)
        alpha = arr[:, :, 3]
        transparent_ratio = (alpha < 10).mean()
        if transparent_ratio > 0.05:
            # Alpha channel looks meaningful — defringe and use it
            cleaned = defringe_alpha(img)
            cleaned.save(out_path, "PNG")
            if mask_path:
                mask_img = Image.fromarray(np.array(cleaned)[:, :, 3])
                mask_img.save(mask_path, "PNG")
            return {
                "method_used": "existing_alpha",
                "confidence": 0.95,
                "output": out_path,
                "mask": mask_path,
                "defringed": True,
                "note": "Image already has transparency — used existing alpha channel with defringing.",
            }

    img_rgba = img.convert("RGBA")
    arr = np.array(img_rgba)

    # Strategy 2: Solid color BG detection
    if method in ("auto", "solid_bg") and bg_color is None:
        detected_bg = _detect_solid_background(arr)
        if detected_bg is not None:
            bg_color = detected_bg

    if bg_color is not None:
        result_arr = _chroma_key_removal(arr, bg_color, tolerance)
        out_img = Image.fromarray(result_arr)
        out_img.save(out_path, "PNG")
        if mask_path:
            mask_img = Image.fromarray(result_arr[:, :, 3])
            mask_img.save(mask_path, "PNG")
        return {
            "method_used": "chroma_key",
            "confidence": 0.85,
            "bg_color_detected": list(bg_color),
            "output": out_path,
            "mask": mask_path,
        }

    # Strategy 3: rembg (if available)
    if method in ("auto", "rembg"):
        try:
            from rembg import remove
            with open(image_path, "rb") as f:
                input_data = f.read()
            output_data = remove(input_data)
            with open(out_path, "wb") as f:
                f.write(output_data)
            if mask_path:
                result_img = Image.open(out_path).convert("RGBA")
                mask_img = Image.fromarray(np.array(result_img)[:, :, 3])
                mask_img.save(mask_path, "PNG")
            return {
                "method_used": "rembg",
                "confidence": 0.90,
                "output": out_path,
                "mask": mask_path,
            }
        except ImportError:
            pass  # Fall through

    # Strategy 4: OpenCV GrabCut
    if method in ("auto", "grabcut"):
        try:
            import cv2
            result = _grabcut_removal(image_path, arr)
            out_img = Image.fromarray(result)
            out_img.save(out_path, "PNG")
            if mask_path:
                mask_img = Image.fromarray(result[:, :, 3])
                mask_img.save(mask_path, "PNG")
            return {
                "method_used": "grabcut",
                "confidence": 0.70,
                "output": out_path,
                "mask": mask_path,
                "note": "GrabCut may be inaccurate. Review and refine mask manually.",
            }
        except ImportError:
            pass

    # Fallback: save as-is with note
    img_rgba.save(out_path, "PNG")
    print("WARNING: No background removal method available. Saved original as RGBA.", file=sys.stderr)
    print("Install rembg for best results: pip install rembg", file=sys.stderr)
    return {
        "method_used": "none",
        "confidence": 0.0,
        "output": out_path,
        "mask": None,
        "note": "No BG removal applied. Install rembg: pip install rembg",
    }


def _detect_solid_background(arr: "np.ndarray", sample_size: int = 5) -> tuple | None:
    """
    Sample corner pixels to detect solid background color.
    Returns dominant corner color or None if background is complex.
    """
    import numpy as np
    h, w = arr.shape[:2]
    # Sample corners and edges
    corners = [
        arr[0, 0, :3], arr[0, w - 1, :3],
        arr[h - 1, 0, :3], arr[h - 1, w - 1, :3],
        arr[h // 2, 0, :3], arr[h // 2, w - 1, :3],
    ]
    colors = [tuple(c.tolist()) for c in corners]
    # Check if corners are all similar (solid BG)
    ref = colors[0]
    diffs = [max(abs(int(c[i]) - int(ref[i])) for i in range(3)) for c in colors]
    if all(d < 15 for d in diffs):
        return ref
    return None


def _chroma_key_removal(arr: "np.ndarray", bg_color: tuple, tolerance: int) -> "np.ndarray":
    """Remove pixels close to bg_color in RGB space."""
    import numpy as np
    result = arr.copy()
    r, g, b = int(bg_color[0]), int(bg_color[1]), int(bg_color[2])
    dr = np.abs(arr[:, :, 0].astype(int) - r)
    dg = np.abs(arr[:, :, 1].astype(int) - g)
    db = np.abs(arr[:, :, 2].astype(int) - b)
    dist = np.sqrt(dr**2 + dg**2 + db**2)
    mask = dist < tolerance
    result[:, :, 3] = np.where(mask, 0, 255)
    return result


def _grabcut_removal(image_path: str, arr: "np.ndarray") -> "np.ndarray":
    """GrabCut background removal via OpenCV."""
    import cv2
    import numpy as np
    img_bgr = cv2.imread(image_path)
    h, w = img_bgr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    margin = max(2, min(w, h) // 20)
    rect = (margin, margin, w - 2 * margin, h - 2 * margin)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(img_bgr, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    result = np.zeros((h, w, 4), np.uint8)
    result[:, :, :3] = arr[:, :, :3]
    result[:, :, 3] = fg_mask
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove image background")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("--out", default="source/foreground.png")
    parser.add_argument("--mask", default=None, help="Output mask path")
    parser.add_argument("--method", default="auto",
                        choices=["auto", "existing_alpha", "solid_bg", "rembg", "grabcut"])
    parser.add_argument("--tolerance", type=int, default=30)
    parser.add_argument("--result-json", default=None)
    args = parser.parse_args()

    if not Path(args.image).exists():
        print(f"ERROR: Image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    result = remove_background(args.image, args.out, args.mask, args.method, tolerance=args.tolerance)
    print(f"Method used : {result['method_used']}")
    print(f"Confidence  : {result.get('confidence', 0):.0%}")
    print(f"Output      : {result['output']}")
    if result.get("note"):
        print(f"Note: {result['note']}")

    if args.result_json:
        Path(args.result_json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.result_json, "w") as f:
            json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
