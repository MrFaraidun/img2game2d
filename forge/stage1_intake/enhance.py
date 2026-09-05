#!/usr/bin/env python3
"""
Stage 1 Intake: Image Enhancement & Super-Resolution.
Enhances character concept art / sprites with high-order Lanczos super-sampling,
contrast-adaptive sharpening (CAS), cel-outline darkening, and alpha defringing.

Usage:
    python3 forge/stage1_intake/enhance.py input.png --out enhanced.png --scale 2.0 --clarity 1.3
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.image_utils import enhance_image, load_image, save_image


def run_enhance(
    input_path: str,
    out_path: str,
    scale: float = 2.0,
    clarity: float = 1.3,
    denoise: bool = True,
    seal_outlines: bool = True,
) -> dict:
    """
    Enhances an input image and saves it to out_path.
    Returns metadata dict.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    img = load_image(str(input_file))
    orig_size = img.size

    enhanced = enhance_image(
        img,
        scale=scale,
        clarity_strength=clarity,
        denoise=denoise,
        seal_outlines=seal_outlines,
    )

    save_image(enhanced, out_path)
    new_size = enhanced.size

    return {
        "input": str(input_file),
        "output": str(out_path),
        "orig_resolution": {"width": orig_size[0], "height": orig_size[1]},
        "enhanced_resolution": {"width": new_size[0], "height": new_size[1]},
        "scale": scale,
        "clarity": clarity,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Enhance 2D character image resolution and clarity")
    parser.add_argument("input", help="Path to input image")
    parser.add_argument("--out", "-o", required=True, help="Path for output enhanced image")
    parser.add_argument("--scale", "-s", type=float, default=2.0, help="Upscale factor (default: 2.0)")
    parser.add_argument("--clarity", "-c", type=float, default=1.3, help="Edge clarity/sharpening factor (default: 1.3)")
    parser.add_argument("--no-denoise", action="store_true", help="Disable median denoising")
    parser.add_argument("--no-seal", action="store_true", help="Disable cel-outline dark line sealing")

    args = parser.parse_args()
    res = run_enhance(
        args.input,
        args.out,
        scale=args.scale,
        clarity=args.clarity,
        denoise=not args.no_denoise,
        seal_outlines=not args.no_seal,
    )
    print(f"Enhanced {res['orig_resolution']['width']}x{res['orig_resolution']['height']} -> "
          f"{res['enhanced_resolution']['width']}x{res['enhanced_resolution']['height']} "
          f"saved to {res['output']}")


if __name__ == "__main__":
    main()
