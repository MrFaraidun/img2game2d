#!/usr/bin/env python3
"""
Stage 3: Extract individual layer PNGs from a foreground image.
Uses bounding boxes from layer-spec.json to crop each layer.

This is a deterministic script — no AI involved.

Usage:
    python3 forge/stage3_build/extract_layers.py \
        --source source/foreground.png \
        --spec layers/layer-spec.json \
        --out layers/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json


def extract_layers(source_path: str, spec_path: str, out_dir: str) -> dict:
    """
    Crop each layer from the source foreground image using bounding boxes.
    Returns dict: layer_id → output path
    """
    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow required: pip install Pillow", file=sys.stderr)
        sys.exit(1)

    source = Image.open(source_path).convert("RGBA")
    spec = load_json(spec_path)
    layers = spec.get("layers", {})
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    results: dict = {}
    canvas_w = spec.get("canvas_size", {}).get("width", source.width)
    canvas_h = spec.get("canvas_size", {}).get("height", source.height)

    # Resize source to canvas size if needed
    if source.width != canvas_w or source.height != canvas_h:
        source = source.resize((canvas_w, canvas_h), Image.LANCZOS)

    for layer_id, layer in layers.items():
        bb = layer.get("bounding_box")
        if not bb:
            print(f"  SKIP {layer_id}: no bounding box", file=sys.stderr)
            continue

        x = max(0, int(bb.get("x", 0)))
        y = max(0, int(bb.get("y", 0)))
        w = max(1, int(bb.get("width", 32)))
        h = max(1, int(bb.get("height", 32)))

        # Clamp to image bounds
        x2 = min(x + w, source.width)
        y2 = min(y + h, source.height)
        if x2 <= x or y2 <= y:
            print(f"  SKIP {layer_id}: bounding box out of bounds ({x},{y},{w},{h})", file=sys.stderr)
            continue

        crop = source.crop((x, y, x2, y2))

        # Save with layer ID as filename
        out_file = out_path / f"{layer_id}.png"
        crop.save(str(out_file), "PNG")
        results[layer_id] = str(out_file)
        print(f"  Extracted: {layer_id}.png  ({x},{y},{x2-x},{y2-y})")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract layer PNGs from foreground image")
    parser.add_argument("--source", required=True, help="Foreground PNG (BG removed)")
    parser.add_argument("--spec", required=True, help="layer-spec.json")
    parser.add_argument("--out", required=True, help="Output directory for layer PNGs")
    parser.add_argument("--result-json", default=None)
    args = parser.parse_args()

    for p in [args.source, args.spec]:
        if not Path(p).exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            sys.exit(1)

    results = extract_layers(args.source, args.spec, args.out)
    print(f"\nExtracted {len(results)} layers → {args.out}")

    if args.result_json:
        Path(args.result_json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.result_json, "w") as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
