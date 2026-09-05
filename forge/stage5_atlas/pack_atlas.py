#!/usr/bin/env python3
"""
Stage 5: Sprite atlas packer.
Packs animation frames into texture atlases using a greedy bin-packing algorithm.

Output per animation:
    atlases/<anim>.png   — packed texture
    atlases/<anim>.json  — frame metadata (x, y, w, h, pivot, duration)

Usage:
    python3 forge/stage5_atlas/pack_atlas.py \
        --frames animations/ \
        --out atlases/ \
        [--max-width 2048] \
        [--max-height 2048] \
        [--padding 2] \
        [--power-of-two]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json


def next_pow2(n: int) -> int:
    return 2 ** math.ceil(math.log2(max(n, 1)))


def pack_atlas(
    frames_root: str,
    out_dir: str,
    max_width: int = 2048,
    max_height: int = 2048,
    padding: int = 2,
    power_of_two: bool = True,
    asset_spec: dict | None = None,
) -> dict:
    """
    Pack animation frames into atlases.
    Returns dict: animation_name → {atlas_path, json_path, frames}.
    """
    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow required: pip install Pillow", file=sys.stderr)
        sys.exit(1)

    frames_root_path = Path(frames_root)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Find animation clips (subdirectories with PNGs)
    subdirs = sorted([p for p in frames_root_path.iterdir() if p.is_dir()])
    # Also handle flat directory
    if not subdirs and sorted(frames_root_path.glob("*.png")):
        subdirs = [frames_root_path]

    results: dict = {}

    for subdir in subdirs:
        frame_files = sorted(subdir.glob("*.png"))
        if not frame_files:
            continue

        clip_name = subdir.name if subdir != frames_root_path else "frames"

        # Load all frames
        frames = []
        for ff in frame_files:
            img = Image.open(str(ff)).convert("RGBA")
            frames.append((ff.name, img))

        if not frames:
            continue

        # Determine atlas layout (row-based: one row per animation = simplest for games)
        max_w = max(f.width for _, f in frames)
        max_h = max(f.height for _, f in frames)
        n = len(frames)

        # Calculate grid: prefer rows
        cols = min(n, max_width // (max_w + padding))
        if cols == 0:
            cols = 1
        rows = math.ceil(n / cols)

        atlas_w = cols * (max_w + padding) + padding
        atlas_h = rows * (max_h + padding) + padding

        if power_of_two:
            atlas_w = next_pow2(atlas_w)
            atlas_h = next_pow2(atlas_h)

        atlas_w = min(atlas_w, max_width)
        atlas_h = min(atlas_h, max_height)

        # Get FPS from asset spec if available
        fps = 12
        if asset_spec and clip_name in asset_spec.get("animations", {}):
            fps = asset_spec["animations"][clip_name].get("fps", 12)
        frame_duration_ms = 1000.0 / fps

        # Pack frames onto atlas
        atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
        frame_meta: list[dict] = []

        for i, (fname, frame_img) in enumerate(frames):
            col = i % cols
            row = i // cols
            x = padding + col * (max_w + padding)
            y = padding + row * (max_h + padding)

            # Center frame if smaller than max
            cx = x + (max_w - frame_img.width) // 2
            cy = y + (max_h - frame_img.height) // 2

            if cx + frame_img.width <= atlas_w and cy + frame_img.height <= atlas_h:
                atlas.paste(frame_img, (cx, cy), frame_img)

            frame_meta.append({
                "filename": fname,
                "frame": {"x": x, "y": y, "w": max_w, "h": max_h},
                "sourceSize": {"w": frame_img.width, "h": frame_img.height},
                "pivot": {"x": 0.5, "y": 0.5},
                "duration": frame_duration_ms,
            })

        # Save atlas PNG
        atlas_png = out_path / f"{clip_name}.png"
        atlas.save(str(atlas_png), "PNG")

        # Save atlas JSON
        atlas_json_data = {
            "meta": {
                "app": "img2game2d",
                "clip": clip_name,
                "image": f"{clip_name}.png",
                "size": {"w": atlas_w, "h": atlas_h},
                "fps": fps,
                "frame_count": n,
                "loop": asset_spec.get("animations", {}).get(clip_name, {}).get("loop", True) if asset_spec else True,
            },
            "frames": frame_meta,
        }
        atlas_json = out_path / f"{clip_name}.json"
        with open(atlas_json, "w") as f:
            json.dump(atlas_json_data, f, indent=2)

        results[clip_name] = {
            "atlas_path": str(atlas_png),
            "json_path": str(atlas_json),
            "frame_count": n,
            "atlas_size": [atlas_w, atlas_h],
        }
        print(f"  {clip_name}: {n} frames → {atlas_w}×{atlas_h}  {atlas_png.name}")

    if results:
        with open(out_path / "atlas_summary.json", "w") as f:
            json.dump(results, f, indent=2)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Pack sprite atlas")
    parser.add_argument("--frames", required=True, help="Animations directory")
    parser.add_argument("--out", required=True, help="Output atlases directory")
    parser.add_argument("--max-width", type=int, default=2048, dest="max_width")
    parser.add_argument("--max-height", type=int, default=2048, dest="max_height")
    parser.add_argument("--padding", type=int, default=2)
    parser.add_argument("--power-of-two", action="store_true", dest="power_of_two")
    parser.add_argument("--asset-spec", default=None, dest="asset_spec")
    args = parser.parse_args()

    if not Path(args.frames).exists():
        print(f"ERROR: Not found: {args.frames}", file=sys.stderr)
        sys.exit(1)

    asset_spec = load_json(args.asset_spec) if args.asset_spec and Path(args.asset_spec).exists() else None

    results = pack_atlas(
        frames_root=args.frames,
        out_dir=args.out,
        max_width=args.max_width,
        max_height=args.max_height,
        padding=args.padding,
        power_of_two=args.power_of_two,
        asset_spec=asset_spec,
    )

    print(f"\nPacked {len(results)} atlases → {args.out}")

    # Write summary
    summary_path = Path(args.out) / "atlas_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
