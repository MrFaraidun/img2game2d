#!/usr/bin/env python3
"""
Stage 1: Detect art style from image.
Classifies the visual style: pixel_art, anime, hand_drawn, vector, painted, 3d_rendered, etc.

Uses deterministic heuristics — no AI required for basic classification.
Agent should review and may override the detected style.

Usage:
    python3 forge/stage1_intake/detect_style.py character.png --out analysis/style.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

STYLES = [
    "pixel_art", "hand_drawn", "anime", "cartoon", "comic",
    "vector", "painted", "3d_rendered", "low_poly", "stylized", "realistic"
]


def detect_style(image_path: str) -> dict:
    """
    Heuristic style detection using image statistics.
    Returns confidence scores for each style.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return {
            "detected_style": "unknown",
            "confidence": 0.0,
            "scores": {},
            "error": "Pillow/NumPy required for style detection",
        }

    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    w, h = img.width, img.height

    scores: dict[str, float] = {}

    # ── Pixel art detection ──────────────────────────────────────────────────
    # Pixel art: small unique color count, blocky edges, often small dimensions
    flat = arr.reshape(-1, 3)
    unique_colors = len(set(map(tuple, flat.tolist())))
    color_density = unique_colors / (w * h)

    # Check for sharp edges (no anti-aliasing)
    small = img.resize((64, 64), Image.NEAREST)
    restored = small.resize((w, h), Image.NEAREST)
    diff = np.abs(arr.astype(int) - np.array(restored).astype(int)).mean()
    sharp_edges = diff < 5.0  # Very low difference = no anti-aliasing

    pixel_art_score = 0.0
    if unique_colors < 256:
        pixel_art_score += 0.4
    elif unique_colors < 1024:
        pixel_art_score += 0.2
    if sharp_edges:
        pixel_art_score += 0.3
    if max(w, h) <= 128:
        pixel_art_score += 0.2
    if color_density < 0.001:
        pixel_art_score += 0.1
    scores["pixel_art"] = min(1.0, pixel_art_score)

    # ── Anime / cartoon detection ─────────────────────────────────────────────
    # Anime: strong outlines, limited palette, flat color regions, high saturation
    from PIL import ImageFilter
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_arr = np.array(edges)
    edge_ratio = (edge_arr > 30).mean()

    hsv_saturation = _mean_saturation(arr)
    anime_score = 0.0
    if edge_ratio > 0.05:
        anime_score += 0.3  # Strong outlines
    if hsv_saturation > 0.4:
        anime_score += 0.3  # High saturation
    if unique_colors < 8192 and not sharp_edges:
        anime_score += 0.2  # Limited palette but anti-aliased
    if unique_colors > 256:
        anime_score += 0.1  # Not pixel art
    scores["anime"] = min(1.0, anime_score)
    scores["cartoon"] = min(1.0, anime_score * 0.9)  # Similar heuristics

    # ── Painted / realistic detection ────────────────────────────────────────
    # High unique color count, gradient-rich, no sharp quantization
    painted_score = 0.0
    if unique_colors > 100_000:
        painted_score += 0.4
    elif unique_colors > 50_000:
        painted_score += 0.2
    if not sharp_edges:
        painted_score += 0.2
    if edge_ratio < 0.03:
        painted_score += 0.2  # Soft edges
    if color_density > 0.1:
        painted_score += 0.2
    scores["painted"] = min(1.0, painted_score)
    scores["realistic"] = min(1.0, painted_score * 0.8)

    # ── Hand-drawn ────────────────────────────────────────────────────────────
    # Irregular edges, sketch-like, often grayscale or low color
    hand_drawn_score = 0.0
    gray_ratio = 1.0 - hsv_saturation
    if gray_ratio > 0.6:
        hand_drawn_score += 0.3
    if edge_ratio > 0.08:
        hand_drawn_score += 0.2
    if unique_colors < 10_000:
        hand_drawn_score += 0.1
    scores["hand_drawn"] = min(1.0, hand_drawn_score)

    # ── 3D rendered ───────────────────────────────────────────────────────────
    # Complex lighting gradients, high color count, smooth shading
    scores["3d_rendered"] = min(1.0, painted_score * 1.1)
    scores["low_poly"] = min(1.0, scores["3d_rendered"] * 0.6)
    scores["stylized"] = min(1.0, (scores["anime"] + scores["cartoon"]) / 2)
    scores["vector"] = min(1.0, scores["cartoon"] * 0.8)
    scores["comic"] = min(1.0, scores["cartoon"] * 0.9)

    # Pick winner
    best_style = max(scores, key=lambda s: scores[s])
    best_score = scores[best_style]

    return {
        "detected_style": best_style,
        "confidence": round(best_score, 3),
        "scores": {k: round(v, 3) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
        "unique_colors": unique_colors,
        "color_density": round(color_density, 6),
        "edge_ratio": round(float(edge_ratio), 4),
        "mean_saturation": round(float(hsv_saturation), 4),
        "note": "Heuristic detection — agent should review and override if incorrect.",
    }


def _mean_saturation(arr: "np.ndarray") -> float:
    """Estimate mean saturation from RGB array."""
    import numpy as np
    r, g, b = arr[:, :, 0].astype(float), arr[:, :, 1].astype(float), arr[:, :, 2].astype(float)
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    delta = max_c - min_c
    with np.errstate(invalid="ignore", divide="ignore"):
        sat = np.where(max_c > 0, delta / max_c, 0.0)
    return float(sat.mean())


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect image art style")
    parser.add_argument("image", help="Path to image")
    parser.add_argument("--out", help="Output JSON path", default="analysis/style.json")
    args = parser.parse_args()

    if not Path(args.image).exists():
        print(f"ERROR: Image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    result = detect_style(args.image)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Style detected: {result['detected_style']} (confidence: {result['confidence']:.1%})")
    print(f"Written to: {args.out}")


if __name__ == "__main__":
    main()
