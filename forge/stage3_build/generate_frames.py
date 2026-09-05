#!/usr/bin/env python3
"""
Stage 3: Animation frame generator.

This script orchestrates AI-based frame generation for each animation clip.
It is the ONE place in the pipeline where AI generation is called.

The script itself is deterministic — it reads the spec, manages the output
directory structure, checks the cache, and calls the configured provider.
The AI provider is abstracted: OpenAI, local model, or stub (for testing).

Usage:
    python3 forge/stage3_build/generate_frames.py \
        --reference source/original.png \
        --spec asset.json \
        --animations idle,walk,attack \
        --out animations/ \
        [--provider openai|stub|local]
        [--fps 12]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json
from _shared.cache import Cache


# ── Provider interface ────────────────────────────────────────────────────────

class FrameGenerator:
    """Abstract provider interface for AI frame generation."""

    def generate(
        self,
        reference_path: str,
        animation_name: str,
        frame_index: int,
        frame_count: int,
        asset_spec: dict,
        prompt_hint: str,
    ) -> str | None:
        """
        Generate one animation frame.
        Returns path to generated PNG, or None on failure.
        """
        raise NotImplementedError


class StubGenerator(FrameGenerator):
    """
    Stub generator for testing — creates solid-color placeholder frames.
    Use this when no AI provider is configured.
    """

    COLORS: dict[str, tuple[int, int, int, int]] = {
        "idle":   (100, 120, 200, 220),
        "walk":   (80,  160, 80,  220),
        "run":    (200, 160, 80,  220),
        "attack": (200, 80,  80,  220),
        "jump":   (80,  200, 200, 220),
        "fall":   (160, 80,  200, 220),
        "hurt":   (200, 100, 100, 220),
        "death":  (60,  60,  80,  200),
    }

    def generate(self, reference_path, animation_name, frame_index, frame_count, asset_spec, prompt_hint) -> str | None:
        try:
            from PIL import Image
        except ImportError:
            return None

        # Load reference and tint it
        ref = Image.open(reference_path).convert("RGBA")
        color = self.COLORS.get(animation_name, (128, 128, 128, 220))

        # Vary slightly per frame to show motion
        import numpy as np
        arr = np.array(ref).astype(float)
        t = frame_index / max(frame_count - 1, 1)
        # Slight vertical shift to simulate motion
        shift = int(t * 4 - 2)
        arr[:, :, :3] = arr[:, :, :3] * 0.5 + np.array(color[:3]) * 0.5

        frame = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        if shift != 0:
            frame = frame.transform(frame.size, Image.AFFINE, (1, 0, 0, 0, 1, shift))
        return frame  # Return image object, caller saves


class OpenAIGenerator(FrameGenerator):
    """OpenAI DALL-E based frame generator (requires OPENAI_API_KEY)."""

    def __init__(self, model: str = "dall-e-3"):
        self.model = model

    def generate(self, reference_path, animation_name, frame_index, frame_count, asset_spec, prompt_hint) -> str | None:
        try:
            import openai
        except ImportError:
            print("ERROR: openai package required: pip install openai", file=sys.stderr)
            return None

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
            return None

        # Build generation prompt
        style = asset_spec.get("visual_style", "preserve")
        asset_name = asset_spec.get("name", "character")
        colors = [c.get("hex", "") for c in asset_spec.get("colors", [])[:3]]

        prompt = (
            f"2D game sprite: {asset_name}, {animation_name} animation, "
            f"frame {frame_index + 1} of {frame_count}. "
            f"Style: {style}. Dominant colors: {', '.join(colors)}. "
            f"Transparent background. Consistent anatomy and equipment. "
            f"{prompt_hint}"
        )

        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.images.generate(
                model=self.model,
                prompt=prompt,
                n=1,
                size="512x512",
                response_format="url",
            )
            return response.data[0].url
        except Exception as e:
            print(f"  OpenAI generation failed: {e}", file=sys.stderr)
            return None


# ── Frame generation orchestrator ─────────────────────────────────────────────

ANIMATION_HINTS: dict[str, str] = {
    "idle":   "Character standing still with subtle breathing motion.",
    "walk":   "Character walking cycle, feet alternating.",
    "run":    "Character running fast, arms pumping.",
    "jump":   "Character in mid-air, arms slightly raised.",
    "fall":   "Character falling, arms out for balance.",
    "attack": "Character swinging weapon in attack pose.",
    "hurt":   "Character recoiling from damage.",
    "death":  "Character collapsing to the ground.",
    "dash":   "Character lunging forward at speed.",
    "block":  "Character raising shield in defensive stance.",
}

DEFAULT_FRAME_COUNTS: dict[str, int] = {
    "idle": 4, "walk": 8, "run": 8, "jump": 4,
    "fall": 3, "attack": 6, "hurt": 3, "death": 6,
    "dash": 4, "block": 2,
}


def generate_animation_frames(
    reference_path: str,
    spec: dict,
    animation_names: list[str],
    out_dir: str,
    provider: str = "stub",
    fps_override: int | None = None,
    cache: Cache | None = None,
) -> dict:
    """
    Generate frames for specified animation clips.
    Returns dict: animation_name → list of frame paths.
    """
    from pathlib import Path

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    generator: FrameGenerator
    if provider == "openai":
        generator = OpenAIGenerator()
    elif provider == "stub":
        generator = StubGenerator()
    else:
        print(f"Unknown provider: {provider}, falling back to stub", file=sys.stderr)
        generator = StubGenerator()

    animations_spec = spec.get("animations", {})
    results: dict = {}

    for anim_name in animation_names:
        anim_config = animations_spec.get(anim_name, {})
        fps = fps_override or anim_config.get("fps", 12)
        frame_count = DEFAULT_FRAME_COUNTS.get(anim_name, 4)

        anim_dir = out_path / anim_name
        anim_dir.mkdir(parents=True, exist_ok=True)

        # Check cache
        cache_key = f"build.animations.{anim_name}"
        ref_hash = cache.file_hash(reference_path) if cache else "no-cache"
        if cache and cache.is_cached(cache_key, ref_hash):
            existing = sorted(anim_dir.glob("*.png"))
            if existing:
                print(f"  Cache hit: {anim_name} ({len(existing)} frames)")
                results[anim_name] = [str(p) for p in existing]
                continue

        print(f"  Generating: {anim_name} ({frame_count} frames @ {fps}fps) ...")
        prompt_hint = ANIMATION_HINTS.get(anim_name, "")
        frame_paths = []

        for i in range(frame_count):
            out_file = anim_dir / f"{i:03d}.png"

            frame = generator.generate(
                reference_path=reference_path,
                animation_name=anim_name,
                frame_index=i,
                frame_count=frame_count,
                asset_spec=spec,
                prompt_hint=prompt_hint,
            )

            if frame is None:
                print(f"    Frame {i}: generation failed", file=sys.stderr)
                continue

            # Handle: returned image object (stub) or URL (openai)
            if hasattr(frame, "save"):
                frame.save(str(out_file), "PNG")
            elif isinstance(frame, str) and frame.startswith("http"):
                import urllib.request
                urllib.request.urlretrieve(frame, str(out_file))
            else:
                print(f"    Frame {i}: unknown output type", file=sys.stderr)
                continue

            frame_paths.append(str(out_file))
            print(f"    Frame {i:03d}: {out_file.name}")

        if cache and frame_paths:
            cache.record(cache_key, ref_hash, frame_paths)

        results[anim_name] = frame_paths
        print(f"  Done: {anim_name} → {len(frame_paths)} frames")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate animation frames")
    parser.add_argument("--reference", required=True, help="Source reference PNG")
    parser.add_argument("--spec", required=True, help="asset.json")
    parser.add_argument("--animations", default="idle,walk,attack",
                        help="Comma-separated animation names")
    parser.add_argument("--out", required=True, help="Output animations directory")
    parser.add_argument("--provider", default="stub",
                        choices=["stub", "openai", "local"],
                        help="AI provider to use for frame generation")
    parser.add_argument("--fps", type=int, default=None)
    args = parser.parse_args()

    for p in [args.reference, args.spec]:
        if not Path(p).exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            sys.exit(1)

    spec = load_json(args.spec)
    animation_names = [a.strip() for a in args.animations.split(",") if a.strip()]
    cache = Cache()

    results = generate_animation_frames(
        reference_path=args.reference,
        spec=spec,
        animation_names=animation_names,
        out_dir=args.out,
        provider=args.provider,
        fps_override=args.fps,
        cache=cache,
    )

    print(f"\nGeneration complete:")
    for anim, frames in results.items():
        print(f"  {anim:12s} → {len(frames)} frames")

    # Write results JSON
    results_file = Path(args.out) / "generation_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results: {results_file}")


if __name__ == "__main__":
    main()
