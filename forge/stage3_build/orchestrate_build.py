#!/usr/bin/env python3
"""
Stage 3: Build pass orchestrator.
Runs the full build stage in sequence:
  1. extract_layers
  2. reconstruct_occlusion
  3. generate_frames

Usage:
    python3 forge/stage3_build/orchestrate_build.py \
        --source source/foreground.png \
        --reference source/original.png \
        --spec layers/layer-spec.json \
        --asset asset.json \
        --animations idle,walk,attack \
        --out-layers layers/ \
        --out-frames animations/ \
        [--provider stub|openai|local]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json
from _shared.cache import Cache


def orchestrate(
    source: str,
    reference: str,
    spec: str,
    asset: str,
    animations: list[str],
    out_layers: str,
    out_frames: str,
    provider: str = "stub",
    fps_override: int | None = None,
) -> dict:
    """Run stages: extract → reconstruct → generate. Returns summary dict."""
    from stage3_build.extract_layers import extract_layers
    from stage3_build.reconstruct_occlusion import reconstruct_occlusion
    from stage3_build.generate_frames import generate_animation_frames

    cache = Cache()
    asset_spec = load_json(asset)
    summary: dict = {}

    # ── 1. Extract layers ────────────────────────────────────────────────
    print("\n── Step 1/3: Extract layers ─────────────────────────────────────")
    cache_key = "build.extract"
    ref_hash = cache.file_hash(source)
    if cache.is_cached(cache_key, ref_hash):
        print("  Cache hit: layer extraction skipped")
        extracted = {}
    else:
        extracted = extract_layers(source, spec, out_layers)
        cache.record(cache_key, ref_hash, list(extracted.values()))
    summary["layers_extracted"] = len(extracted)

    # ── 2. Reconstruct occlusions ────────────────────────────────────────
    print("\n── Step 2/3: Reconstruct occlusions ─────────────────────────────")
    reconstructed = reconstruct_occlusion(spec, out_layers, out_layers)
    summary["layers_reconstructed"] = len(reconstructed)

    # ── 3. Generate animation frames ─────────────────────────────────────
    print("\n── Step 3/3: Generate animation frames ──────────────────────────")
    results = generate_animation_frames(
        reference_path=reference,
        spec=asset_spec,
        animation_names=animations,
        out_dir=out_frames,
        provider=provider,
        fps_override=fps_override,
        cache=cache,
    )
    summary["animations"] = {k: len(v) for k, v in results.items()}
    summary["total_frames"] = sum(len(v) for v in results.values())

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestrate full build stage")
    parser.add_argument("--source", required=True, help="Foreground PNG (BG removed)")
    parser.add_argument("--reference", required=True, help="Original reference PNG")
    parser.add_argument("--spec", required=True, help="layers/layer-spec.json")
    parser.add_argument("--asset", required=True, help="asset.json")
    parser.add_argument("--animations", required=True, help="Comma-separated animation names")
    parser.add_argument("--out-layers", default="layers/", dest="out_layers")
    parser.add_argument("--out-frames", default="animations/", dest="out_frames")
    parser.add_argument("--provider", default="stub", choices=["stub", "openai", "local"])
    parser.add_argument("--fps", type=int, default=None)
    args = parser.parse_args()

    for p in [args.source, args.reference, args.spec, args.asset]:
        if not Path(p).exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            sys.exit(1)

    anim_list = [a.strip() for a in args.animations.split(",") if a.strip()]
    summary = orchestrate(
        source=args.source,
        reference=args.reference,
        spec=args.spec,
        asset=args.asset,
        animations=anim_list,
        out_layers=args.out_layers,
        out_frames=args.out_frames,
        provider=args.provider,
        fps_override=args.fps,
    )

    print("\n── Build Summary ─────────────────────────────────────────────────")
    print(f"  Layers extracted   : {summary.get('layers_extracted', 0)}")
    print(f"  Layers reconstructed: {summary.get('layers_reconstructed', 0)}")
    print(f"  Total frames       : {summary.get('total_frames', 0)}")
    for anim, count in summary.get("animations", {}).items():
        print(f"    {anim:12s} → {count} frames")


if __name__ == "__main__":
    main()
