#!/usr/bin/env python3
"""
Stage 6: Engine export entry point.
Routes to the appropriate exporter based on --engine flag.

Usage:
    python3 forge/stage6_export/export.py \
        --asset asset.json \
        --atlases atlases/ \
        --engine godot \
        --out exports/godot/

    python3 forge/stage6_export/export.py \
        --asset asset.json \
        --atlases atlases/ \
        --engine all \
        --out exports/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json


ENGINES = ["godot", "unity", "phaser", "pixijs"]


def export(asset: dict, atlases_dir: str, engine: str, out_dir: str) -> dict:
    """Route to engine-specific exporter."""
    if engine == "all":
        results = {}
        for eng in ENGINES:
            eng_out = Path(out_dir) / eng
            eng_out.mkdir(parents=True, exist_ok=True)
            results[eng] = export(asset, atlases_dir, eng, str(eng_out))
        return results
    elif engine == "godot":
        from stage6_export.godot_exporter import GodotExporter
        return GodotExporter().export(asset, atlases_dir, out_dir)
    elif engine == "unity":
        from stage6_export.unity_exporter import UnityExporter
        return UnityExporter().export(asset, atlases_dir, out_dir)
    elif engine == "phaser":
        from stage6_export.phaser_exporter import PhaserExporter
        return PhaserExporter().export(asset, atlases_dir, out_dir)
    elif engine == "pixijs":
        from stage6_export.pixijs_exporter import PixiJSExporter
        return PixiJSExporter().export(asset, atlases_dir, out_dir)
    else:
        raise ValueError(f"Unknown engine: {engine}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export game asset to target engine")
    parser.add_argument("--asset", required=True, help="Path to asset.json")
    parser.add_argument("--atlases", required=True, help="Directory with packed atlases")
    parser.add_argument("--engine", required=True,
                        choices=ENGINES + ["all"],
                        help="Target engine")
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    for p in [args.asset, args.atlases]:
        if not Path(p).exists():
            print(f"ERROR: Not found: {p}", file=sys.stderr)
            sys.exit(1)

    asset = load_json(args.asset)
    engines = ENGINES if args.engine == "all" else [args.engine]

    all_results: dict = {}
    for engine in engines:
        engine_out = Path(args.out) / engine if args.engine == "all" else Path(args.out)
        engine_out.mkdir(parents=True, exist_ok=True)
        print(f"\n── {engine.upper()} Exporter ──")
        try:
            result = export(asset, args.atlases, engine, str(engine_out))
            all_results[engine] = result
            print(f"  ✓ {engine} export complete → {engine_out}")
        except Exception as e:
            print(f"  ✗ {engine} export failed: {e}", file=sys.stderr)
            all_results[engine] = {"error": str(e)}

    print(f"\nExport complete: {', '.join(all_results)}")


if __name__ == "__main__":
    main()
