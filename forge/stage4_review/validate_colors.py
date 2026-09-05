#!/usr/bin/env python3
"""
Stage 4: Validate color consistency across animation frames.
Checks that dominant colors remain stable (prevents random color shifts between frames).

Usage:
    python3 forge/stage4_review/validate_colors.py \
        --reference source/original.png \
        --frames animations/ \
        --out analysis/color_check.json \
        [--threshold 0.90]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def palette_similarity(img_a: "Image.Image", img_b: "Image.Image") -> float:
    """Bhattacharyya coefficient on RGB histograms."""
    import numpy as np
    def hist(img):
        arr = np.array(img.convert("RGB").resize((64, 64)))
        h = np.zeros((8, 8, 8), dtype=float)
        ri = (arr[:, :, 0] // 32).astype(int)
        gi = (arr[:, :, 1] // 32).astype(int)
        bi = (arr[:, :, 2] // 32).astype(int)
        for y in range(arr.shape[0]):
            for x in range(arr.shape[1]):
                h[ri[y, x], gi[y, x], bi[y, x]] += 1
        total = h.sum()
        return h / total if total > 0 else h

    ha = hist(img_a).flatten()
    hb = hist(img_b).flatten()
    return float(sum((ha[i] * hb[i]) ** 0.5 for i in range(len(ha))))


def validate_colors(
    reference_path: str,
    frames_root: str,
    threshold: float = 0.90,
) -> dict:
    try:
        from PIL import Image
    except ImportError:
        return {"error": "Pillow required", "passed": False}

    ref = Image.open(reference_path).convert("RGBA")
    frames_root_path = Path(frames_root)

    # Collect all PNGs recursively (supports animations/ with subdirs)
    frame_files = sorted(frames_root_path.rglob("*.png"))
    if not frame_files:
        return {"passed": False, "error": f"No frames found in {frames_root}", "frame_count": 0}

    scores: list[float] = []
    frame_results: list[dict] = []

    for frame_file in frame_files:
        frame = Image.open(str(frame_file)).convert("RGBA")
        score = palette_similarity(ref, frame)
        scores.append(score)
        frame_results.append({
            "frame": str(frame_file.relative_to(frames_root_path)),
            "score": round(score, 4),
            "passed": score >= threshold,
        })

    mean_score = sum(scores) / len(scores) if scores else 0.0
    passed = mean_score >= threshold
    failing = [f["frame"] for f in frame_results if not f["passed"]]

    return {
        "passed": passed,
        "score": round(mean_score, 4),
        "threshold": threshold,
        "frame_count": len(frame_files),
        "failing_frames": failing,
        "recommendation": None if passed else f"Color consistency {mean_score:.2f} < {threshold}. Check palette drift between frames.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate color consistency")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--frames", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--threshold", type=float, default=0.90)
    args = parser.parse_args()

    for p in [args.reference, args.frames]:
        if not Path(p).exists():
            print(f"ERROR: Not found: {p}", file=sys.stderr)
            sys.exit(1)

    result = validate_colors(args.reference, args.frames, args.threshold)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    status = "✓ PASSED" if result["passed"] else "✗ FAILED"
    print(f"Color check: {status}  score={result.get('score', 0):.3f}  frames={result.get('frame_count', 0)}")
    if not result["passed"]:
        print(f"  {result.get('recommendation', '')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
