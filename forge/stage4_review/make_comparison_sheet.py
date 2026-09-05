#!/usr/bin/env python3
"""
Stage 4: Generate side-by-side comparison sheet (reference vs frames).

Usage:
    python3 forge/stage4_review/make_comparison_sheet.py \
        --reference source/original.png \
        --frames animations/idle/ \
        --out analysis/comparison.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def make_comparison_sheet(reference_path: str, frames_dir: str, out_path: str, max_frames: int = 8) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("ERROR: Pillow required: pip install Pillow", file=sys.stderr)
        sys.exit(1)

    ref = Image.open(reference_path).convert("RGBA")
    frame_files = sorted(Path(frames_dir).glob("*.png"))[:max_frames]

    if not frame_files:
        print(f"No frames found in {frames_dir}", file=sys.stderr)
        sys.exit(1)

    # Uniform thumb size
    thumb_w, thumb_h = 128, 128
    padding = 4
    label_h = 20

    # Sheet: [reference] [frame0] [frame1] ...
    all_images = [ref] + [Image.open(str(f)).convert("RGBA") for f in frame_files]
    n = len(all_images)
    sheet_w = n * (thumb_w + padding) + padding
    sheet_h = thumb_h + label_h + padding * 2

    sheet = Image.new("RGBA", (sheet_w, sheet_h), (40, 40, 40, 255))

    try:
        draw = ImageDraw.Draw(sheet)
    except Exception:
        draw = None

    for i, img in enumerate(all_images):
        thumb = img.resize((thumb_w, thumb_h), Image.LANCZOS)
        # White background for RGBA
        bg = Image.new("RGBA", (thumb_w, thumb_h), (255, 255, 255, 255))
        bg.paste(thumb, mask=thumb.split()[3] if thumb.mode == "RGBA" else None)
        x = padding + i * (thumb_w + padding)
        y = padding + label_h
        sheet.paste(bg, (x, y))
        # Label
        if draw:
            label = "REF" if i == 0 else frame_files[i - 1].name
            draw.text((x + 2, padding + 2), label[:12], fill=(200, 200, 200, 255))

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, "PNG")
    print(f"Comparison sheet saved: {out_path}  ({n} images)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate comparison sheet")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--frames", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-frames", type=int, default=8, dest="max_frames")
    args = parser.parse_args()

    for p in [args.reference, args.frames]:
        if not Path(p).exists():
            print(f"ERROR: Not found: {p}", file=sys.stderr)
            sys.exit(1)

    make_comparison_sheet(args.reference, args.frames, args.out, args.max_frames)


if __name__ == "__main__":
    main()
