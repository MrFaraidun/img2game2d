#!/usr/bin/env python3
"""
Stage 1: Probe image metadata.
Outputs basic file info without performing visual analysis.

Usage:
    python3 forge/stage1_intake/probe_image.py character.png [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add forge to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def probe(image_path: str) -> dict:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    result: dict = {
        "path": str(path.resolve()),
        "filename": path.name,
        "stem": path.stem,
        "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
    }

    supported = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".tif"}
    if path.suffix.lower() not in supported:
        result["warning"] = f"Format '{path.suffix}' may not be fully supported. Prefer PNG."

    try:
        from PIL import Image
        img = Image.open(image_path)
        result["width"] = img.width
        result["height"] = img.height
        result["mode"] = img.mode
        result["has_alpha"] = img.mode in ("RGBA", "LA", "PA")
        result["format"] = img.format or "unknown"

        if hasattr(img, "info"):
            dpi = img.info.get("dpi")
            if dpi:
                result["dpi"] = list(dpi)

        # Check for animated (GIF/APNG)
        try:
            img.seek(1)
            result["frames"] = getattr(img, "n_frames", 1)
            result["animated"] = True
        except EOFError:
            result["animated"] = False
            result["frames"] = 1

        result["aspect_ratio"] = round(img.width / img.height, 4) if img.height > 0 else None

        # Estimate if background is likely transparent
        if result["has_alpha"]:
            import numpy as np
            arr = np.array(img.convert("RGBA"))
            alpha = arr[:, :, 3]
            transparent_pixels = (alpha < 10).sum()
            total_pixels = alpha.size
            result["transparency_ratio"] = round(float(transparent_pixels) / total_pixels, 4)
            result["likely_transparent_bg"] = result["transparency_ratio"] > 0.1

    except ImportError:
        result["warning_pil"] = "Pillow not installed. Install with: pip install Pillow"
        result["width"] = None
        result["height"] = None
        result["mode"] = None
        result["has_alpha"] = None

    result["suitable"] = path.suffix.lower() in supported
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe image metadata")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--json", action="store_true", dest="json_out", help="Output JSON")
    parser.add_argument("--out", help="Write JSON output to file")
    args = parser.parse_args()

    try:
        result = probe(args.image)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json_out or args.out:
        output = json.dumps(result, indent=2)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            with open(args.out, "w") as f:
                f.write(output)
            print(f"Probe written to: {args.out}")
        else:
            print(output)
    else:
        # Human-readable
        print(f"\n=== Image Probe: {result['filename']} ===")
        print(f"  Size        : {result.get('width')}×{result.get('height')} px")
        print(f"  Mode        : {result.get('mode')}")
        print(f"  Has alpha   : {result.get('has_alpha')}")
        print(f"  File size   : {result['size_bytes']:,} bytes")
        print(f"  Frames      : {result.get('frames', 1)}")
        print(f"  Animated    : {result.get('animated', False)}")
        print(f"  Suitable    : {result['suitable']}")
        if "transparency_ratio" in result:
            print(f"  Transp ratio: {result['transparency_ratio']:.1%}")
        if result.get("warning"):
            print(f"  WARNING: {result['warning']}")


if __name__ == "__main__":
    main()
