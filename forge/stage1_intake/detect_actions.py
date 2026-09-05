#!/usr/bin/env python3
"""
Stage 1 Intake: Action Sheet Slicer & Multi-Pose Detector.
Detects and slices multi-pose character action sheets containing sequential
poses (idle, walk, jump, attack, hurt).

Normalizes canvas dimensions and aligns ground lines across all extracted keyframes.

Usage:
    python3 forge/stage1_intake/detect_actions.py action_sheet.png --out poses/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("ERROR: Pillow and NumPy are required: pip install Pillow numpy", file=sys.stderr)
    sys.exit(1)


ACTION_PRESETS: Dict[int, List[str]] = {
    1: ["idle"],
    2: ["idle", "attack"],
    3: ["idle", "walk", "attack"],
    4: ["idle", "walk", "attack", "hurt"],
    5: ["idle", "walk", "jump", "attack", "hurt"],
    6: ["idle", "walk", "run", "jump", "attack", "hurt"],
}


def _find_content_intervals(has_content: np.ndarray, min_run: int = 12, min_gap: int = 6) -> List[Tuple[int, int]]:
    """
    Find contiguous intervals of True separated by at least min_gap False.
    """
    intervals: List[Tuple[int, int]] = []
    in_run = False
    start = 0
    gap_count = 0

    for i, val in enumerate(has_content):
        if val:
            if not in_run:
                in_run = True
                start = i
            gap_count = 0
        else:
            if in_run:
                gap_count += 1
                if gap_count >= min_gap or i == len(has_content) - 1:
                    end = i - gap_count + 1
                    if end - start >= min_run:
                        intervals.append((start, end))
                    in_run = False
                    gap_count = 0

    if in_run:
        end = len(has_content)
        if end - start >= min_run:
            intervals.append((start, end))

    return intervals


def detect_and_slice_actions(
    image_path: str,
    out_dir: str,
    action_labels: List[str] | None = None,
    normalize_size: int = 512,
) -> Dict:
    """
    Detects individual character action figures in an action sheet,
    crops each pose, aligns ground feet, and saves them to out_dir/<action>.png.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {image_path}")

    img = Image.open(str(path)).convert("RGBA")
    w, h = img.size
    arr = np.array(img)
    alpha = arr[:, :, 3]

    # Detect foreground mask
    if (alpha < 20).mean() > 0.05:
        fg_mask = alpha > 25
    else:
        # Detect solid background from corners
        corners = np.vstack([
            arr[0:6, 0:6, :3].reshape(-1, 3),
            arr[0:6, -6:, :3].reshape(-1, 3),
            arr[-6:, 0:6, :3].reshape(-1, 3),
            arr[-6:, -6:, :3].reshape(-1, 3),
        ])
        bg_col = np.median(corners, axis=0)
        diff = np.abs(arr[:, :, :3] - bg_col).sum(axis=2)
        fg_mask = diff > 35

    # Find horizontal panels
    col_content = fg_mask.any(axis=0)
    col_runs = _find_content_intervals(col_content, min_run=max(12, w // 40), min_gap=max(6, w // 100))

    # Find vertical bounds
    row_content = fg_mask.any(axis=1)
    row_runs = _find_content_intervals(row_content, min_run=max(12, h // 40), min_gap=max(6, h // 100))

    if not col_runs:
        col_runs = [(0, w)]
    if not row_runs:
        row_runs = [(0, h)]

    # Collect figures (row by row or strip)
    panels: List[Tuple[int, int, int, int]] = []
    if len(row_runs) == 1:
        ry1, ry2 = row_runs[0]
        for (cx1, cx2) in col_runs:
            # Tighten vertical crop for this specific column run
            panel_fg = fg_mask[ry1:ry2, cx1:cx2]
            if panel_fg.any():
                py = np.where(panel_fg.any(axis=1))[0]
                px = np.where(panel_fg.any(axis=0))[0]
                if len(py) > 0 and len(px) > 0:
                    y1 = ry1 + py[0]
                    y2 = ry1 + py[-1] + 1
                    x1 = cx1 + px[0]
                    x2 = cx1 + px[-1] + 1
                    panels.append((x1, y1, x2, y2))
                else:
                    panels.append((cx1, ry1, cx2, ry2))
    else:
        for (ry1, ry2) in row_runs:
            for (cx1, cx2) in col_runs:
                panel_fg = fg_mask[ry1:ry2, cx1:cx2]
                if panel_fg.sum() > (cx2 - cx1) * (ry2 - ry1) * 0.02:
                    panels.append((cx1, ry1, cx2, ry2))

    num_panels = len(panels)
    if not action_labels:
        action_labels = ACTION_PRESETS.get(num_panels, [f"action_{i}" for i in range(num_panels)])

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    extracted: Dict[str, str] = {}
    panel_meta: List[Dict] = []

    # Find maximum height to align ground line
    max_panel_h = max((y2 - y1) for (x1, y1, x2, y2) in panels) if panels else h

    for i, (x1, y1, x2, y2) in enumerate(panels):
        label = action_labels[i] if i < len(action_labels) else f"pose_{i}"
        crop = img.crop((x1, y1, x2, y2))

        # Ground-aligned placement into normalized canvas
        norm_canvas = Image.new("RGBA", (normalize_size, normalize_size), (0, 0, 0, 0))
        # Scale to fit nicely with padding
        scale = min((normalize_size * 0.8) / max(crop.width, 1), (normalize_size * 0.8) / max(max_panel_h, 1))
        cw = max(1, int(crop.width * scale))
        ch = max(1, int(crop.height * scale))
        scaled_crop = crop.resize((cw, ch), Image.LANCZOS)

        # Center horizontally, ground-align at 88% height
        dest_x = (normalize_size - cw) // 2
        dest_y = int(normalize_size * 0.88 - ch)

        norm_canvas.paste(scaled_crop, (dest_x, dest_y), mask=scaled_crop.split()[3])

        out_file = out_path / f"{label}.png"
        norm_canvas.save(str(out_file), "PNG")
        extracted[label] = str(out_file)

        panel_meta.append({
            "action": label,
            "source_bbox": [x1, y1, x2 - x1, y2 - y1],
            "file": str(out_file),
        })

    return {
        "action_sheet": str(path),
        "total_actions_detected": num_panels,
        "actions": panel_meta,
        "extracted_files": extracted,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Action Sheet Slicer & Multi-Pose Intake")
    parser.add_argument("sheet", help="Path to action sheet image")
    parser.add_argument("--out", "-o", default="poses", help="Output directory for extracted poses")
    parser.add_argument("--labels", help="Comma-separated custom action names (e.g. idle,walk,jump,attack,hurt)")
    parser.add_argument("--size", type=int, default=512, help="Normalized canvas size (default: 512)")
    args = parser.parse_args()

    labels = [l.strip() for l in args.labels.split(",")] if args.labels else None
    res = detect_and_slice_actions(args.sheet, args.out, action_labels=labels, normalize_size=args.size)

    print(f"\n✓ Detected {res['total_actions_detected']} action poses from {args.sheet}:")
    for a in res["actions"]:
        bbox = a["source_bbox"]
        print(f"  • {a['action']:<10} -> {a['file']} (BBox: {bbox[0]},{bbox[1]} {bbox[2]}x{bbox[3]})")


if __name__ == "__main__":
    main()
