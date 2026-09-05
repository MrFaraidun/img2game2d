#!/usr/bin/env python3
"""
Stage 4: Validate silhouette consistency between reference and animation frames.
Uses IoU (Intersection over Union) of alpha-channel silhouettes.

Usage:
    python3 forge/stage4_review/validate_silhouette.py \
        --reference source/original.png \
        --frames animations/idle/ \
        --out analysis/silhouette_check.json \
        [--threshold 0.85]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_silhouette(
    reference_path: str,
    frames_dir: str,
    threshold: float = 0.85,
) -> dict:
    """
    Compute silhouette IoU for all frames vs reference.
    Returns validation result dict.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return {"error": "Pillow/NumPy required", "passed": False}

    ref = Image.open(reference_path).convert("RGBA")
    frames_path = Path(frames_dir)
    frame_files = sorted(frames_path.glob("*.png"))

    if not frame_files:
        return {
            "passed": False,
            "error": f"No PNG frames found in {frames_dir}",
            "frame_count": 0,
        }

    def alpha_mask(img: Image.Image, target_size: tuple) -> "np.ndarray":
        rgba = img.resize(target_size, Image.LANCZOS).convert("RGBA")
        return np.array(rgba)[:, :, 3] > 10

    target_size = (ref.width, ref.height)
    ref_mask = alpha_mask(ref, target_size)

    scores: list[float] = []
    frame_results: list[dict] = []

    for frame_file in frame_files:
        frame = Image.open(str(frame_file)).convert("RGBA")
        frame_mask = alpha_mask(frame, target_size)

        intersection = (ref_mask & frame_mask).sum()
        union = (ref_mask | frame_mask).sum()
        iou = float(intersection) / float(union) if union > 0 else 1.0

        scores.append(iou)
        frame_results.append({
            "frame": frame_file.name,
            "iou": round(iou, 4),
            "passed": iou >= threshold,
        })

    mean_iou = sum(scores) / len(scores) if scores else 0.0
    passed = mean_iou >= threshold
    failing = [f for f in frame_results if not f["passed"]]

    return {
        "passed": passed,
        "score": round(mean_iou, 4),
        "threshold": threshold,
        "frame_count": len(frame_files),
        "failing_frames": [f["frame"] for f in failing],
        "frames": frame_results,
        "recommendation": None if passed else f"Silhouette IoU {mean_iou:.2f} < {threshold}. Regenerate failing frames with tighter silhouette constraints.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate silhouette consistency")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--frames", required=True, help="Directory containing frame PNGs")
    parser.add_argument("--out", required=True)
    parser.add_argument("--threshold", type=float, default=0.85)
    args = parser.parse_args()

    for p in [args.reference, args.frames]:
        if not Path(p).exists():
            print(f"ERROR: Not found: {p}", file=sys.stderr)
            sys.exit(1)

    result = validate_silhouette(args.reference, args.frames, args.threshold)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    status = "✓ PASSED" if result["passed"] else "✗ FAILED"
    print(f"Silhouette check: {status}  score={result.get('score', 0):.3f}  frames={result.get('frame_count', 0)}")
    if not result["passed"]:
        print(f"  {result.get('recommendation', '')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
