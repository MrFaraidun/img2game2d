#!/usr/bin/env python3
"""
Stage 5: Generate 2D Dynamic Lighting Maps (Normal & Emission).

Generates:
  1. Tangent-Space Normal Map (<name>_normal.png):
     - Calculates Sobel gradients on diffuse luminance.
     - Encodes surface angles into standard tangent-space [R, G, B] vectors.
     - Compatible with Godot 4 CanvasItem Light2D and Unity URP 2D Normal Map channels.
  2. Emission / Bloom Map (<name>_emission.png):
     - Isolates glowing saturated or hyper-luminous pixels (blades, eyes, magic shields).

Usage:
    python3 forge/stage5_atlas/generate_lighting_maps.py \
        --input atlases/hero_atlas.png \
        --out atlases/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image


def compute_normal_map(
    img: Image.Image,
    strength: float = 2.5,
    invert_y: bool = False,
) -> Image.Image:
    """Computes an OpenGL tangent-space normal map from an RGBA image."""
    rgba = np.array(img.convert("RGBA"), dtype=np.float32)
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]

    # Luminance channel for height estimation
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]

    # Sobel kernels
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    padded_lum = np.pad(lum, pad_width=1, mode="edge")
    h, w = lum.shape
    dx = np.zeros_like(lum)
    dy = np.zeros_like(lum)

    for i in range(3):
        for j in range(3):
            sub = padded_lum[i : i + h, j : j + w]
            dx += sub * kernel_x[i, j]
            dy += sub * kernel_y[i, j]

    dx = (dx / 255.0) * strength
    dy = (dy / 255.0) * strength

    if invert_y:
        dy = -dy

    dz = np.ones_like(lum, dtype=np.float32)
    magnitude = np.sqrt(dx * dx + dy * dy + dz * dz)
    magnitude = np.maximum(magnitude, 1e-6)

    nx = -dx / magnitude
    ny = dy / magnitude
    nz = dz / magnitude

    r = np.clip((nx * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    g = np.clip((ny * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    b = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    a = alpha.astype(np.uint8)

    # Flat normal (128, 128, 255) where transparent
    zero_mask = a == 0
    r[zero_mask] = 128
    g[zero_mask] = 128
    b[zero_mask] = 255

    normal_array = np.stack([r, g, b, a], axis=-1)
    return Image.fromarray(normal_array, mode="RGBA")


def compute_emission_map(
    img: Image.Image,
    lum_threshold: float = 140.0,
    sat_threshold: float = 0.25,
    boost: float = 1.2,
) -> Image.Image:
    """Extracts emissive glowing regions."""
    rgba = np.array(img.convert("RGBA"), dtype=np.float32)
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]

    max_c = np.maximum.reduce([rgb[..., 0], rgb[..., 1], rgb[..., 2]])
    min_c = np.minimum.reduce([rgb[..., 0], rgb[..., 1], rgb[..., 2]])
    delta = max_c - min_c

    sat = np.zeros_like(max_c)
    non_zero = max_c > 0
    sat[non_zero] = delta[non_zero] / max_c[non_zero]
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]

    emissive_mask = ((sat >= sat_threshold) & (lum >= lum_threshold)) | (lum >= 235.0)
    emissive_mask = emissive_mask & (alpha > 10)

    out_rgb = np.zeros_like(rgb)
    out_alpha = np.zeros_like(alpha)
    boosted_rgb = np.clip(rgb * boost, 0, 255)

    out_rgb[emissive_mask] = boosted_rgb[emissive_mask]
    out_alpha[emissive_mask] = alpha[emissive_mask]

    emissive_array = np.stack(
        [
            out_rgb[..., 0].astype(np.uint8),
            out_rgb[..., 1].astype(np.uint8),
            out_rgb[..., 2].astype(np.uint8),
            out_alpha.astype(np.uint8),
        ],
        axis=-1,
    )
    return Image.fromarray(emissive_array, mode="RGBA")


def generate_lighting_maps(
    input_path: Path | str,
    output_dir: Path | str,
    strength: float = 2.5,
) -> dict[str, str]:
    """Generates both normal and emission maps."""
    inp = Path(input_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    img = Image.open(inp).convert("RGBA")
    stem = inp.stem

    normal_img = compute_normal_map(img, strength=strength)
    normal_path = out / f"{stem}_normal.png"
    normal_img.save(normal_path, "PNG")

    emission_img = compute_emission_map(img)
    emission_path = out / f"{stem}_emission.png"
    emission_img.save(emission_path, "PNG")

    return {
        "diffuse": str(inp),
        "normal": str(normal_path),
        "emission": str(emission_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate 2D Lighting Maps (Normal & Emission)")
    parser.add_argument("--input", required=True, help="Input diffuse sprite/atlas PNG")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--strength", type=float, default=2.5, help="Normal bevel strength")
    args = parser.parse_args()

    res = generate_lighting_maps(args.input, args.out, strength=args.strength)
    print(f"✓ Normal map:   {res['normal']}")
    print(f"✓ Emission map: {res['emission']}")


if __name__ == "__main__":
    main()
