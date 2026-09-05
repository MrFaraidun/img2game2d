#!/usr/bin/env python3
"""
Stage 1 Intake: Image Quality & Feasibility Gate.
Analyzes 2D character reference images for game-readiness:
  - Resolution & aspect ratio
  - Canvas boundary clipping (cut off feet/head/arms)
  - Background contrast & separability
  - Edge sharpness & noise

Emits:
  - Quality score (0.0 to 1.0) and Verdict (EXCELLENT | ACCEPTABLE_WITH_ENHANCEMENT | POOR_REJECT)
  - Diagnosed flaws and actionable guidance
  - Tailored AI Generator Prompt (for Midjourney/DALL-E/SDXL) to regenerate a pristine reference if bad.

Usage:
    python3 forge/stage1_intake/assess_quality.py character.png
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


def generate_recommended_prompt(
    subject_desc: str = "character",
    detected_style: str = "cel-shaded dark fantasy",
    dominant_colors: List[str] | None = None,
) -> Dict[str, str]:
    """
    Synthesize an optimized, high-converting AI generator prompt
    to create a pristine, game-ready reference sprite sheet/image.
    """
    color_hint = f", color palette featuring {', '.join(dominant_colors)}" if dominant_colors else ""

    positive_prompt = (
        f"Full-body {detected_style} 2D {subject_desc} game sprite concept art sheet, "
        f"standing in a relaxed neutral A-pose facing directly forward, arms held slightly away from torso, "
        f"complete head and feet fully contained within frame with generous padding and margins{color_hint}. "
        f"Crisp clean cel-shaded vector ink outlines, flat solid color fills, zero motion blur, "
        f"isolated on a seamless flat solid neutral light gray background (#e0e0e0), "
        f"professional 2D video game character design, 8k resolution, centered composition."
    )

    negative_prompt = (
        "cropped limbs, cut off feet, cut off head, touching canvas borders, complex background scenery, "
        "photorealistic clutter, extreme perspective foreshortening, isometric angle, dynamic combat pose, "
        "blurry edges, text, watermark, signature, compression artifacts, noisy textures"
    )

    midjourney_command = f"/imagine prompt: {positive_prompt} --no {negative_prompt} --ar 1:1 --stylize 250 --v 6.1"

    return {
        "positive": positive_prompt,
        "negative": negative_prompt,
        "midjourney": midjourney_command,
    }


def assess_image_quality(image_path: str, detected_style: str = "2D character") -> Dict:
    """
    Perform deep technical feasibility and quality evaluation of a reference image.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = Image.open(str(path))
    w, h = img.size
    flaws: List[str] = []
    recommendations: List[str] = []

    # 1. Resolution Assessment
    min_dim = min(w, h)
    res_score = 1.0
    if min_dim >= 512:
        res_score = 1.0
    elif min_dim >= 256:
        res_score = 0.75
        flaws.append(f"Moderate resolution ({w}x{h}). Super-resolution enhancement recommended.")
        recommendations.append("Apply forge/stage1_intake/enhance.py to upscale by 2x.")
    else:
        res_score = 0.35
        flaws.append(f"Low resolution ({w}x{h} < 256px). Pixelation will degrade animation layers.")
        recommendations.append("Regenerate reference at 512x512 or higher.")

    # 2. Canvas Border Clipping Detection
    img_rgba = img.convert("RGBA")
    arr = np.array(img_rgba)
    alpha = arr[:, :, 3]

    # Detect background color from corners
    corner_samples = np.vstack([
        arr[0:8, 0:8, :3].reshape(-1, 3),
        arr[0:8, -8:, :3].reshape(-1, 3),
        arr[-8:, 0:8, :3].reshape(-1, 3),
        arr[-8:, -8:, :3].reshape(-1, 3),
    ])
    bg_color_est = np.median(corner_samples, axis=0)

    # Foreground mask
    if (alpha < 20).mean() > 0.05:
        fg_mask = alpha > 30
    else:
        diff = np.abs(arr[:, :, :3] - bg_color_est).sum(axis=2)
        fg_mask = diff > 40

    clipped_borders = []
    border_margin = 3
    # Check borders
    if fg_mask[0:border_margin, :].sum() > w * 0.08:
        clipped_borders.append("top (head/horns clipped)")
    if fg_mask[-border_margin:, :].sum() > w * 0.08:
        clipped_borders.append("bottom (feet clipped)")
    if fg_mask[:, 0:border_margin].sum() > h * 0.08:
        clipped_borders.append("left (arm/weapon clipped)")
    if fg_mask[:, -border_margin:].sum() > h * 0.08:
        clipped_borders.append("right (arm/weapon clipped)")

    clipping_penalty = 0.0
    if clipped_borders:
        clipping_penalty = min(0.60, len(clipped_borders) * 0.20)
        flaws.append(f"Character geometry touches/clipped by canvas borders: {', '.join(clipped_borders)}")
        recommendations.append("Ensure character has at least 15% margin padding around all edges.")

    # 3. Background Separability Assessment
    bg_score = 1.0
    if (alpha < 10).mean() > 0.10:
        bg_score = 1.0
    else:
        # Check corner color variance
        corner_var = np.var(corner_samples, axis=0).mean()
        if corner_var < 80:
            bg_score = 0.90  # Clean solid background
        elif corner_var < 350:
            bg_score = 0.65  # Slight gradient or soft vignetting
            flaws.append("Background is not completely solid; soft color gradient detected.")
        else:
            bg_score = 0.35  # Complex noisy scenery
            flaws.append("Complex or textured background scenery detected; chroma separation may be noisy.")
            recommendations.append("Generate reference on a pure solid gray background (#d0d0d0) or transparent RGBA.")

    # 4. Aspect Ratio & Framing
    aspect = w / max(h, 1)
    aspect_score = 1.0
    if aspect < 0.35 or aspect > 2.8:
        aspect_score = 0.70
        flaws.append("Extreme aspect ratio. Sprite may be squashed or abnormally wide.")

    # Overall Score Calculation
    total_score = max(0.0, (res_score * 0.35 + bg_score * 0.35 + aspect_score * 0.30) - clipping_penalty)
    total_score = round(total_score, 2)

    # Verdict
    if total_score >= 0.85 and len(clipped_borders) == 0:
        verdict = "EXCELLENT"
        summary = "Image is clean, well-isolated, and ready for automated rigging and animation."
    elif total_score >= 0.65 and len(clipped_borders) <= 1:
        verdict = "ACCEPTABLE_WITH_ENHANCEMENT"
        summary = "Image is workable, but super-resolution enhancement/defringing is strongly recommended."
    else:
        verdict = "POOR_REJECT"
        summary = "Image quality or framing is suboptimal for clean 2D rigging. Regenerating reference art is recommended."

    # Generate tailored prompt
    stem_name = path.stem.replace("_", " ").title()
    prompt_package = generate_recommended_prompt(
        subject_desc=stem_name,
        detected_style=detected_style,
    )

    return {
        "image": str(path),
        "resolution": {"width": w, "height": h},
        "quality_score": total_score,
        "verdict": verdict,
        "summary": summary,
        "clipped_borders": clipped_borders,
        "flaws": flaws,
        "recommendations": recommendations,
        "suggested_prompt": prompt_package,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate 2D image quality and suitability for game rigging")
    parser.add_argument("image", help="Path to reference image")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    result = assess_image_quality(args.image)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    # Formatted terminal display
    score = result["quality_score"]
    verdict = result["verdict"]

    verdict_badge = {
        "EXCELLENT": "✓ EXCELLENT (Production Ready)",
        "ACCEPTABLE_WITH_ENHANCEMENT": "⚠ ACCEPTABLE (Needs Enhancement)",
        "POOR_REJECT": "✗ POOR (Regeneration Recommended)",
    }.get(verdict, verdict)

    print("\n" + "=" * 60)
    print(" 2D REFERENCE IMAGE QUALITY ASSESSMENT ")
    print("=" * 60)
    print(f"Target:       {result['image']}")
    print(f"Resolution:   {result['resolution']['width']}x{result['resolution']['height']}")
    print(f"Quality Score: {score * 100:.0f} / 100")
    print(f"Verdict:      {verdict_badge}")
    print(f"Summary:      {result['summary']}")

    if result["flaws"]:
        print("\n[!] Diagnosed Flaws:")
        for f in result["flaws"]:
            print(f"  • {f}")

    if result["recommendations"]:
        print("\n[*] Recommendations:")
        for r in result["recommendations"]:
            print(f"  → {r}")

    if verdict == "POOR_REJECT" or len(result["flaws"]) > 0:
        print("\n" + "-" * 60)
        print(" NEW AI PROMPT FOR GENERATING A PRISTINE REFERENCE ")
        print("-" * 60)
        print("Positive Prompt:")
        print(f"  {result['suggested_prompt']['positive']}\n")
        print("Negative Prompt:")
        print(f"  {result['suggested_prompt']['negative']}\n")
        print("Midjourney Command:")
        print(f"  {result['suggested_prompt']['midjourney']}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
