#!/usr/bin/env python3
"""
2D Dynamic Lighting Map Generator for img2game2d & Game Engines.
Generates:
  1. Tangent-Space Normal Maps (_normal.png / _n.png):
     - Computes surface gradients via Sobel operators on luminance.
     - Maps unit normals to standard OpenGL tangent space [R: Nx, G: Ny, B: Nz].
     - Fully compatible with Godot 4 Light2D CanvasItem and Unity URP 2D Normal Map channels.
  2. Emission / Glow Maps (_emission.png / _e.png):
     - Extracts high-saturation, high-energy pixels (cyberblades, shields, visors).
     - Isolates glowing regions for bloom shaders and post-processing stacks.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image


def compute_normal_map(
    img: Image.Image,
    strength: float = 2.5,
    invert_y: bool = False,
    smooth_radius: int = 1,
) -> Image.Image:
    """
    Computes an OpenGL tangent-space normal map from an RGBA image.
    Preserves input transparency.
    """
    rgba = np.array(img.convert("RGBA"), dtype=np.float32)
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]

    # Luminance channel for height estimation
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]

    # Sobel kernels for height gradients
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    # Pad image to handle boundaries
    padded_lum = np.pad(lum, pad_width=1, mode="edge")

    h, w = lum.shape
    dx = np.zeros_like(lum)
    dy = np.zeros_like(lum)

    # Vectorized convolution
    for i in range(3):
        for j in range(3):
            sub = padded_lum[i : i + h, j : j + w]
            dx += sub * kernel_x[i, j]
            dy += sub * kernel_y[i, j]

    # Scale gradients by strength factor
    dx = (dx / 255.0) * strength
    dy = (dy / 255.0) * strength

    if invert_y:
        dy = -dy

    # Z component represents the surface normal facing outward towards camera
    dz = np.ones_like(lum, dtype=np.float32)

    # Normalize vectors (Nx, Ny, Nz) to unit length
    magnitude = np.sqrt(dx * dx + dy * dy + dz * dz)
    magnitude = np.maximum(magnitude, 1e-6)

    nx = -dx / magnitude
    ny = dy / magnitude
    nz = dz / magnitude

    # Map [-1.0, 1.0] -> [0, 255]
    r = np.clip((nx * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    g = np.clip((ny * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    b = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    a = alpha.astype(np.uint8)

    # Zero out normal maps in empty alpha areas (standard tangent flat: 128, 128, 255)
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
    """
    Isolates emissive/glow regions (e.g. cyber blades, energy shields, glowing runes).
    Calculates saturation and luminance to extract vibrant active energy elements.
    """
    rgba = np.array(img.convert("RGBA"), dtype=np.float32)
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]

    max_c = np.maximum.reduce([rgb[..., 0], rgb[..., 1], rgb[..., 2]])
    min_c = np.minimum.reduce([rgb[..., 0], rgb[..., 1], rgb[..., 2]])
    delta = max_c - min_c

    # Saturation calculation in range [0.0, 1.0]
    sat = np.zeros_like(max_c)
    non_zero = max_c > 0
    sat[non_zero] = delta[non_zero] / max_c[non_zero]

    # Luminance channel
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]

    # Emissive mask:
    # 1. High saturation and bright (colored energy: cyan, neon orange, magic runes)
    # 2. OR ultra-bright specular highlights (>235)
    emissive_mask = ((sat >= sat_threshold) & (lum >= lum_threshold)) | (lum >= 235.0)
    emissive_mask = emissive_mask & (alpha > 10)

    # Build emissive texture (black everywhere except glow areas)
    out_rgb = np.zeros_like(rgb)
    out_alpha = np.zeros_like(alpha)

    # Boost color intensity for glow regions
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


def generate_lighting_pack(
    source_path: Path | str,
    output_dir: Path | str,
    base_name: Optional[str] = None,
    strength: float = 2.5,
) -> dict[str, str]:
    """Generates both normal and emission maps and writes them to output_dir."""
    src = Path(source_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(f"Source texture not found: {src}")

    name = base_name or src.stem
    img = Image.open(src).convert("RGBA")

    # 1. Normal Map
    normal_img = compute_normal_map(img, strength=strength)
    normal_path = out / f"{name}_normal.png"
    normal_img.save(normal_path, "PNG")

    # 2. Emission Map
    emission_img = compute_emission_map(img)
    emission_path = out / f"{name}_emission.png"
    emission_img.save(emission_path, "PNG")

    return {
        "diffuse": str(src),
        "normal": str(normal_path),
        "emission": str(emission_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate 2D Normal & Emission Maps for Sprite Atlases")
    parser.add_argument("input", help="Path to input diffuse sprite or atlas PNG")
    parser.add_argument("--out", default=None, help="Output directory (defaults to input dir)")
    parser.add_argument("--strength", type=float, default=2.5, help="Normal map bevel strength")
    parser.add_argument("--name", default=None, help="Base name for outputs")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.out) if args.out else input_path.parent

    results = generate_lighting_pack(
        source_path=input_path,
        output_dir=out_dir,
        base_name=args.name,
        strength=args.strength,
    )
    print(f"✓ Normal map saved:   {results['normal']}")
    print(f"✓ Emission map saved: {results['emission']}")


if __name__ == "__main__":
    main()
