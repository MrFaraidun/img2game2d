#!/usr/bin/env python3
"""
Stage 1: Detect views in a reference sheet.
Identifies front/side/back/three-quarter views in a sprite sheet or turnaround.

For multi-panel sheets (turnarounds, character sheets), locates each distinct
panel by finding columns/rows where the image has no visible content between
two content regions.

For single-character images, guesses the view angle from pose symmetry.

Usage:
    python3 forge/stage1_intake/detect_views.py reference-sheet.png --out analysis/views.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


VIEW_LABELS = [
    "front", "back", "left", "right",
    "front-left", "front-right", "back-left", "back-right",
    "side", "three-quarter", "top", "bottom",
]

# Common turnaround view orders (left-to-right)
COMMON_ORDERS: dict[int, list[str]] = {
    1: ["front"],
    2: ["front", "back"],
    3: ["front", "side", "back"],
    4: ["front", "side", "back", "side"],
    5: ["front", "front-right", "side", "back", "back-right"],
    6: ["front", "front-right", "side", "back", "back-left", "left"],
}


def detect_views(image_path: str) -> dict:
    """
    Detect multi-view panels in a reference image.
    Falls back to single-view symmetry guess for solo character images.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return {
            "views": [{"label": "unknown", "bbox": None}],
            "multi_view": False,
            "error": "Pillow/NumPy required: pip install Pillow numpy",
        }

    img = Image.open(image_path).convert("RGBA")
    w, h = img.width, img.height
    arr = np.array(img)
    alpha = arr[:, :, 3]  # shape: (h, w)

    result: dict = {
        "source_image": str(Path(image_path).resolve()),
        "image_size": [w, h],
        "views": [],
        "multi_view": False,
    }

    # ── Build content masks ───────────────────────────────────────────────────
    # A column/row "has content" if any pixel in it has alpha > 20
    col_has_content = (alpha > 20).any(axis=0)   # shape: (w,)
    row_has_content = (alpha > 20).any(axis=1)   # shape: (h,)

    # Find contiguous content runs separated by empty gaps
    v_runs = _content_runs(col_has_content, min_run=max(10, w // 20))
    h_runs = _content_runs(row_has_content, min_run=max(10, h // 20))

    if len(v_runs) > 1 or len(h_runs) > 1:
        # ── Multi-panel sheet ──────────────────────────────────────────────
        result["multi_view"] = True
        panels = []
        for (ry1, ry2) in h_runs:
            for (rx1, rx2) in v_runs:
                panels.append((rx1, ry1, rx2, ry2))

        n = len(panels)
        # Assign labels: try horizontal-first ordering
        if len(h_runs) == 1:
            # Pure horizontal strip: use standard turnaround order
            labels = COMMON_ORDERS.get(n, [f"view_{i}" for i in range(n)])
        else:
            labels = [f"view_{i}" for i in range(n)]

        for i, (x1, y1, x2, y2) in enumerate(panels):
            result["views"].append({
                "label": labels[i] if i < len(labels) else f"view_{i}",
                "bbox": [x1, y1, x2 - x1, y2 - y1],
                "note": "Auto-detected from content runs. Agent must verify label correctness.",
            })
    else:
        # ── Single-character image ─────────────────────────────────────────
        # Guess view angle from left/right content symmetry
        cx = w // 2
        left_mass = float(alpha[:, :cx].sum())
        right_mass = float(alpha[:, cx:].sum())
        total = left_mass + right_mass
        if total == 0:
            symmetry = 1.0
        else:
            symmetry = min(left_mass, right_mass) / max(left_mass, right_mass)

        if symmetry > 0.85:
            guessed_view = "front"   # Symmetric → likely front or back
        elif symmetry > 0.65:
            guessed_view = "three-quarter"
        else:
            guessed_view = "side"

        # Content bounding box
        content_cols = np.where(col_has_content)[0]
        content_rows = np.where(row_has_content)[0]
        if len(content_cols) and len(content_rows):
            cx1, cx2 = int(content_cols[0]), int(content_cols[-1])
            cy1, cy2 = int(content_rows[0]), int(content_rows[-1])
            bbox = [cx1, cy1, cx2 - cx1, cy2 - cy1]
        else:
            bbox = [0, 0, w, h]

        result["views"].append({
            "label": guessed_view,
            "bbox": bbox,
            "symmetry": round(float(symmetry), 3),
            "note": "Single-view heuristic guess. Agent must verify.",
        })

    result["view_count"] = len(result["views"])
    return result


def _content_runs(has_content: "np.ndarray", min_run: int = 10) -> list[tuple[int, int]]:
    """
    Find contiguous runs of True in a boolean array (content columns or rows).
    Returns list of (start, end) inclusive index pairs.
    Only returns runs longer than min_run pixels.
    """
    import numpy as np
    runs = []
    in_run = False
    start = 0
    for i, val in enumerate(has_content):
        if val and not in_run:
            in_run = True
            start = i
        elif not val and in_run:
            in_run = False
            if (i - start) >= min_run:
                runs.append((start, i))
    if in_run and (len(has_content) - start) >= min_run:
        runs.append((start, len(has_content)))
    return runs


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect views in reference sheet")
    parser.add_argument("image", help="Path to image")
    parser.add_argument("--out", default="analysis/views.json", help="Output JSON path")
    args = parser.parse_args()

    if not Path(args.image).exists():
        print(f"ERROR: Image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    result = detect_views(args.image)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    tag = "multi-view" if result["multi_view"] else "single view"
    print(f"Views detected: {result['view_count']} ({tag})")
    for v in result["views"]:
        print(f"  {v['label']:20s}  bbox={v.get('bbox')}")
    print(f"Written to: {args.out}")


if __name__ == "__main__":
    main()
