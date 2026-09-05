#!/usr/bin/env python3
"""
Stage 4: Record a review decision into asset.json.
Updates the validation section and review history.

Usage:
    python3 forge/stage4_review/append_review.py asset.json \
        --stage review \
        --silhouette 0.94 \
        --colors 0.97 \
        --continuity 0.91 \
        --action continue
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json, save_json


def append_review(
    asset_path: str,
    stage: str,
    action: str,
    silhouette: float | None = None,
    colors: float | None = None,
    continuity: float | None = None,
    parts: float | None = None,
    summary: str = "",
) -> dict:
    asset = load_json(asset_path)

    validation = asset.setdefault("validation", {})

    # Update scores
    if silhouette is not None:
        validation["silhouette"] = round(silhouette, 4)
    if colors is not None:
        validation["color_consistency"] = round(colors, 4)
    if continuity is not None:
        validation["frame_alignment"] = round(continuity, 4)
    if parts is not None:
        validation["part_consistency"] = round(parts, 4)

    # Determine overall pass
    thresholds = {"silhouette": 0.85, "color_consistency": 0.90, "frame_alignment": 0.88, "part_consistency": 0.90}
    passed = all(
        validation.get(k, 0) >= v
        for k, v in thresholds.items()
        if validation.get(k) is not None
    )
    validation["passed"] = passed

    # Append to review history
    history = asset.setdefault("review_history", [])
    history.append({
        "stage": stage,
        "action": action,
        "scores": {k: validation.get(k) for k in thresholds},
        "passed": passed,
        "summary": summary,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    })

    save_json(asset, asset_path)
    return validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Record review decision in asset.json")
    parser.add_argument("asset", help="Path to asset.json")
    parser.add_argument("--stage", default="review")
    parser.add_argument("--action", required=True,
                        choices=["continue", "refine-spec", "refine-frames", "request-input", "stop"])
    parser.add_argument("--silhouette", type=float, default=None)
    parser.add_argument("--colors", type=float, default=None)
    parser.add_argument("--continuity", type=float, default=None)
    parser.add_argument("--parts", type=float, default=None)
    parser.add_argument("--summary", default="")
    args = parser.parse_args()

    if not Path(args.asset).exists():
        print(f"ERROR: Not found: {args.asset}", file=sys.stderr)
        sys.exit(1)

    result = append_review(
        args.asset, args.stage, args.action,
        silhouette=args.silhouette,
        colors=args.colors,
        continuity=args.continuity,
        parts=args.parts,
        summary=args.summary,
    )

    status = "✓ PASSED" if result.get("passed") else "✗ NOT PASSING"
    print(f"Review recorded: {args.stage} → {args.action}  {status}")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"  {k:25s}: {v:.3f}")


if __name__ == "__main__":
    main()
