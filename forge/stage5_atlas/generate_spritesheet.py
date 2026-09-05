#!/usr/bin/env python3
"""
Stage 5: Row-based sprite sheet generator.
Outputs a single PNG with all frames in a horizontal row per animation.
Also generates a JSON metadata file with frame positions.

Simpler than the atlas packer — one row per animation, no bin-packing.
Ideal for simple game engines or custom renderers.

Usage:
    python3 forge/stage5_atlas/generate_spritesheet.py \
        --frames animations/ \
        --out spritesheets/ \
        [--padding 1] \
        [--scale 1]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json


def generate_spritesheet(
    frames_root: str,
    out_dir: str,
    padding: int = 1,
    scale: float = 1.0,
    asset_spec: dict | None = None,
) -> dict:
    """
    Generate a row-based sprite sheet for each animation clip.
    Returns dict: clip_name → {sheet_path, json_path, cols, rows, frame_w, frame_h}
    """
    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow required: pip install Pillow", file=sys.stderr)
        sys.exit(1)

    frames_root_path = Path(frames_root)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    subdirs = sorted([p for p in frames_root_path.iterdir() if p.is_dir()])
    if not subdirs and sorted(frames_root_path.glob("*.png")):
        subdirs = [frames_root_path]

    results: dict = {}

    for subdir in subdirs:
        frame_files = sorted(subdir.glob("*.png"))
        if not frame_files:
            continue

        clip_name = subdir.name if subdir != frames_root_path else "frames"
        frames = [Image.open(str(f)).convert("RGBA") for f in frame_files]
        n = len(frames)

        # Uniform frame size
        frame_w = max(f.width for f in frames)
        frame_h = max(f.height for f in frames)

        if scale != 1.0:
            frame_w = int(frame_w * scale)
            frame_h = int(frame_h * scale)
            frames = [f.resize((frame_w, frame_h), Image.LANCZOS) for f in frames]

        # Sheet: all frames in one row
        sheet_w = n * frame_w + (n + 1) * padding
        sheet_h = frame_h + 2 * padding

        sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
        frame_meta: list[dict] = []

        fps = 12
        if asset_spec and clip_name in asset_spec.get("animations", {}):
            fps = asset_spec["animations"][clip_name].get("fps", 12)

        for i, frame in enumerate(frames):
            x = padding + i * (frame_w + padding)
            y = padding
            sheet.paste(frame, (x, y), frame)
            frame_meta.append({
                "index": i,
                "x": x, "y": y,
                "w": frame_w, "h": frame_h,
                "filename": frame_files[i].name,
                "duration_ms": round(1000.0 / fps, 1),
            })

        sheet_path = out_path / f"{clip_name}.png"
        sheet.save(str(sheet_path), "PNG")

        meta = {
            "clip": clip_name,
            "image": f"{clip_name}.png",
            "frame_width": frame_w,
            "frame_height": frame_h,
            "frame_count": n,
            "fps": fps,
            "cols": n,
            "rows": 1,
            "padding": padding,
            "sheet_width": sheet_w,
            "sheet_height": sheet_h,
            "frames": frame_meta,
        }
        meta_path = out_path / f"{clip_name}.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        results[clip_name] = {
            "sheet_path": str(sheet_path),
            "json_path": str(meta_path),
            "cols": n,
            "rows": 1,
            "frame_w": frame_w,
            "frame_h": frame_h,
        }
        print(f"  {clip_name}: {n} frames → {sheet_w}×{sheet_h}  {sheet_path.name}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate row-based sprite sheets")
    parser.add_argument("--frames", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--padding", type=int, default=1)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--asset-spec", default=None, dest="asset_spec")
    args = parser.parse_args()

    if not Path(args.frames).exists():
        print(f"ERROR: Not found: {args.frames}", file=sys.stderr)
        sys.exit(1)

    spec = load_json(args.asset_spec) if args.asset_spec and Path(args.asset_spec).exists() else None
    results = generate_spritesheet(args.frames, args.out, args.padding, args.scale, spec)
    print(f"\nGenerated {len(results)} sprite sheets → {args.out}")


if __name__ == "__main__":
    main()
