#!/usr/bin/env python3
"""
Zero-Halo Sub-Pixel Alpha De-Matting & Edge Defringing Engine.
Complies with 2026 Production Standards for 2D Game Asset pipelines.

Production Pillars:
1. Dual-contour color distance & luminance thresholding to eliminate JPEG Gibbs ringing overshoot.
2. Chroma preservation for neon energy effects (lightsabers, hex shields, red barriers, sparks).
3. Outer flood-fill from canvas borders to eliminate background noise.
4. Dark lineart edge clamping: transitional alpha pixels on non-chroma outlines are de-blended
   and tone-shifted to dark outline colors, completely eliminating white/gray edge halos.
5. Soft-edge boundary falloff for ethereal/fading frames (eliminates box borders).
"""
from __future__ import annotations

from collections import deque
from typing import Tuple
import numpy as np
from PIL import Image


def extract_alpha_demat(
    crop_arr: np.ndarray,
    bg_color: np.ndarray,
    is_fading: bool = False,
) -> Image.Image:
    """
    Extracts an RGBA image from an RGB array against a solid background color,
    completely removing background white/gray halos through color de-matting.
    """
    H, W = crop_arr.shape[:2]
    rgb_f = crop_arr[:, :, :3].astype(np.float32)
    bg_f = bg_color.astype(np.float32)

    diff = np.linalg.norm(rgb_f - bg_f, axis=2)

    # Compute chroma (saturation) and perceived luminance
    c_max = np.max(rgb_f, axis=2)
    c_min = np.min(rgb_f, axis=2)
    chroma = c_max - c_min
    lum = 0.299 * rgb_f[:, :, 0] + 0.587 * rgb_f[:, :, 1] + 0.114 * rgb_f[:, :, 2]

    # Background detection
    if is_fading:
        # Softer thresholding for fading ghost frame
        is_bg = (diff < 18.0) & (chroma < 14.0)
    else:
        # Standard: diff < 38 and low chroma is background
        # Any pixel near or above background luminance (>= 174) with low chroma is JPEG ringing overshoot!
        is_bg = (diff < 38.0) & (chroma < 20.0)
        is_bg |= (lum >= 174.0) & (chroma < 20.0)

    # Outer flood fill starting from all 4 borders to map exterior background
    visited = np.zeros((H, W), dtype=bool)
    queue = deque()

    for x in range(W):
        if is_bg[0, x]:
            queue.append((0, x))
            visited[0, x] = True
        if is_bg[H - 1, x]:
            queue.append((H - 1, x))
            visited[H - 1, x] = True
    for y in range(H):
        if is_bg[y, 0]:
            queue.append((y, 0))
            visited[y, 0] = True
        if is_bg[y, W - 1]:
            queue.append((y, W - 1))
            visited[y, W - 1] = True

    while queue:
        cy, cx = queue.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < H and 0 <= nx < W and not visited[ny, nx]:
                if is_bg[ny, nx]:
                    visited[ny, nx] = True
                    queue.append((ny, nx))

    fg_mask = ~visited

    # Filter small disconnected noise (e.g. isolated floating JPEG blocks or bleed from neighbor)
    fg_labeled = np.zeros((H, W), dtype=np.int32)
    label = 1
    component_sizes = {}
    component_bboxes = {}

    for y in range(H):
        for x in range(W):
            if fg_mask[y, x] and fg_labeled[y, x] == 0:
                cq = deque([(y, x)])
                fg_labeled[y, x] = label
                size = 0
                min_cy, max_cy = y, y
                min_cx, max_cx = x, x
                while cq:
                    ly, lx = cq.popleft()
                    size += 1
                    min_cy, max_cy = min(min_cy, ly), max(max_cy, ly)
                    min_cx, max_cx = min(min_cx, lx), max(max_cx, lx)
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = ly + dy, lx + dx
                        if (
                            0 <= ny < H
                            and 0 <= nx < W
                            and fg_mask[ny, nx]
                            and fg_labeled[ny, nx] == 0
                        ):
                            fg_labeled[ny, nx] = label
                            cq.append((ny, nx))
                component_sizes[label] = size
                component_bboxes[label] = (min_cx, min_cy, max_cx, max_cy)
                label += 1

    max_size = max(component_sizes.values()) if component_sizes else 0
    clean_fg = np.zeros((H, W), dtype=bool)

    for l_id, sz in component_sizes.items():
        bx1, by1, bx2, by2 = component_bboxes[l_id]
        # Discard small components touching the very top or bottom edge (neighbor sprite bleeding)
        touches_top_or_bottom = (by1 <= 1 or by2 >= H - 2)
        if touches_top_or_bottom and sz < 600 and sz < max_size * 0.15:
            continue
        # Discard tiny floating dust/speckles
        if sz < 80 and sz < max_size * 0.03:
            continue
        clean_fg |= (fg_labeled == l_id)

    # Alpha calculation
    alpha = np.zeros((H, W), dtype=np.float32)

    if is_fading:
        base_a = np.clip((diff[clean_fg] - 10.0) / 22.0, 0.0, 0.85)
        alpha[clean_fg] = base_a
        feather_margin = 16
        for y in range(H):
            for x in range(W):
                if alpha[y, x] > 0:
                    dist_border = min(x, W - 1 - x, y, H - 1 - y)
                    if dist_border < feather_margin:
                        factor = dist_border / float(feather_margin)
                        alpha[y, x] *= (factor * factor)
    else:
        # 1. Colored luminous glow (chroma >= 20): lightsaber, hex shield, red barrier, sparks
        is_glow = clean_fg & (chroma >= 20.0)
        alpha[is_glow] = np.clip((diff[is_glow] - 14.0) / 20.0, 0.0, 1.0)
        alpha[is_glow] = np.maximum(alpha[is_glow], np.clip(chroma[is_glow] / 24.0, 0.0, 1.0))
        alpha[is_glow & (diff > 45.0)] = 1.0

        # 2. Dark lineart & character body (chroma < 20.0)
        is_lineart = clean_fg & (chroma < 20.0)
        alpha[is_lineart] = np.clip((174.0 - lum[is_lineart]) / 48.0, 0.0, 1.0)

    # Output RGBA buffer
    out = np.zeros((H, W, 4), dtype=np.float32)
    out[:, :, :3] = rgb_f
    out[:, :, 3] = alpha * 255.0

    # Defringe lineart edges: clamp intermediate alpha pixels on lineart towards dark tones
    if not is_fading:
        edge_lineart = is_lineart & (alpha > 0.01) & (alpha < 0.96)
        if np.any(edge_lineart):
            a_sub = alpha[edge_lineart, np.newaxis]
            c_comp = out[edge_lineart, :3]
            # De-mix background contribution: C_fg = (C_comp - (1-a)*C_bg) / a
            c_unmix = (c_comp - (1.0 - a_sub) * bg_f[np.newaxis, :]) / np.maximum(a_sub, 0.1)
            # Clamp lineart brightness to prevent light fringes
            c_unmix = np.clip(c_unmix, 0.0, 75.0)
            out[edge_lineart, :3] = c_unmix

    # Clean zero alpha to pure transparent black for efficient compression
    out[alpha <= 0.02, :] = 0.0

    return Image.fromarray(out.astype(np.uint8), "RGBA")


def run_unit_tests():
    """Localized unit test assertions for dematting functions."""
    bg = np.array([189, 189, 189], dtype=np.uint8)
    test_arr = np.full((60, 60, 3), 189, dtype=np.uint8)
    # Solid black square [20, 20, 20]
    test_arr[20:40, 20:40] = [20, 20, 20]
    # Glowing cyan border [0, 230, 255]
    test_arr[19:41, 19] = [0, 230, 255]
    test_arr[19:41, 40] = [0, 230, 255]
    # Simulated JPEG ringing artifact [205, 205, 205] outside
    test_arr[15:18, 15:18] = [205, 205, 205]

    res = extract_alpha_demat(test_arr, bg)
    res_arr = np.array(res)

    # 1. Background corners must be 100% transparent
    assert res_arr[0, 0, 3] == 0, "Top-left corner must have alpha 0"
    assert res_arr[59, 59, 3] == 0, "Bottom-right corner must have alpha 0"
    # 2. Simulated JPEG ringing artifact must be completely rejected (alpha 0)
    assert res_arr[16, 16, 3] == 0, "JPEG ringing artifact must be rejected"
    # 3. Square core must be solid
    assert res_arr[30, 30, 3] == 255, "Core must be fully opaque"
    # 4. Cyan glow must be preserved
    assert res_arr[30, 19, 3] > 180, "Cyan glow must have high alpha"
    print("✓ All zero-halo dematting unit tests passed successfully!")


if __name__ == "__main__":
    run_unit_tests()
