#!/usr/bin/env python3
"""
Stage 4: Validate frame-to-frame animation continuity.
Checks that consecutive frames don't have abrupt silhouette jumps (teleportation).

Usage:
    python3 forge/stage4_review/validate_continuity.py \
        --frames animations/ \
        --out analysis/continuity_check.json \
        [--threshold 0.88]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_continuity(frames_root: str, threshold: float = 0.88) -> dict:
    """
    Check frame-to-frame IoU within each animation clip.
    High between-frame drop = discontinuity / teleportation.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return {"error": "Pillow/NumPy required", "passed": False}

    frames_root_path = Path(frames_root)
    # Find animation subdirs
    subdirs = [p for p in frames_root_path.iterdir() if p.is_dir()]
    # Also check if frames_root itself has PNGs (single animation)
    root_frames = sorted(frames_root_path.glob("*.png"))
    if root_frames:
        subdirs = [frames_root_path]

    if not subdirs:
        return {"passed": False, "error": f"No animation directories in {frames_root}"}

    all_scores: list[float] = []
    clip_results: list[dict] = []

    for subdir in subdirs:
        frame_files = sorted(subdir.glob("*.png"))
        if len(frame_files) < 2:
            continue

        frames = [Image.open(str(f)).convert("RGBA") for f in frame_files]
        target_size = (frames[0].width, frames[0].height)

        def mask(img):
            rgba = img.resize(target_size, Image.LANCZOS)
            return np.array(rgba)[:, :, 3] > 10

        masks = [mask(f) for f in frames]
        pair_scores: list[float] = []

        for i in range(len(masks) - 1):
            a, b = masks[i], masks[i + 1]
            intersection = (a & b).sum()
            union = (a | b).sum()
            iou = float(intersection) / float(union) if union > 0 else 1.0
            pair_scores.append(iou)
            all_scores.append(iou)

        clip_mean = sum(pair_scores) / len(pair_scores) if pair_scores else 1.0
        clip_results.append({
            "clip": subdir.name,
            "frames": len(frame_files),
            "mean_iou": round(clip_mean, 4),
            "min_iou": round(min(pair_scores), 4) if pair_scores else 1.0,
            "passed": clip_mean >= threshold,
        })

    mean_score = sum(all_scores) / len(all_scores) if all_scores else 1.0
    passed = mean_score >= threshold

    return {
        "passed": passed,
        "score": round(mean_score, 4),
        "threshold": threshold,
        "clips": clip_results,
        "recommendation": None if passed else f"Frame continuity {mean_score:.2f} < {threshold}. Check for large pose jumps between consecutive frames.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate animation continuity")
    parser.add_argument("--frames", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--threshold", type=float, default=0.88)
    args = parser.parse_args()

    if not Path(args.frames).exists():
        print(f"ERROR: Not found: {args.frames}", file=sys.stderr)
        sys.exit(1)

    result = validate_continuity(args.frames, args.threshold)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    status = "✓ PASSED" if result["passed"] else "✗ FAILED"
    print(f"Continuity check: {status}  score={result.get('score', 0):.3f}")
    if not result["passed"]:
        print(f"  {result.get('recommendation', '')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
