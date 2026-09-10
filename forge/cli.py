#!/usr/bin/env python3
"""
img2game2d Unified CLI & Backwards-Compatible Command Gateway.

Provides:
- Legacy command compatibility: dev, build, lighting, slice-actions
- v3 Agent-first commands: inspect, validate, convert, export (with --json support)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

FORGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FORGE_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(FORGE_DIR))

from core.asset_ir import (
    AssetIR,
    CURRENT_SCHEMA_VERSION,
    ProjectManifest,
    asset_ir_to_dict,
    convert_legacy_character_to_asset_ir,
    deserialize_asset_ir,
    serialize_asset_ir,
    validate_asset_ir,
)
import pipeline
import lighting


def cmd_build(args: argparse.Namespace) -> int:
    """Executes full asset extraction, normalization, atlas packing, and engine exports."""
    print("▶ Running full asset compilation pipeline...")
    results = pipeline.run_full_pipeline()
    if getattr(args, "json", False):
        print(json.dumps({"status": "success", "results": results}, default=str, indent=2))
    return 0


def cmd_lighting(args: argparse.Namespace) -> int:
    """Generates 2D normal and emission lighting maps for character atlases."""
    print("▶ Generating 2D dynamic lighting maps...")
    pipeline.generate_all_lighting_maps()
    if getattr(args, "json", False):
        print(json.dumps({"status": "success", "operation": "lighting_maps_generated"}, indent=2))
    return 0


def cmd_slice_actions(args: argparse.Namespace) -> int:
    """Extracts and slices character action sheets."""
    char_id = getattr(args, "character", None) or "all"
    characters = ["the_architect", "the_guardian"] if char_id == "all" else [char_id]
    results = {}
    for c in characters:
        print(f"▶ Slicing actions for {c}...")
        results[c] = pipeline.process_character(c)
    if getattr(args, "json", False):
        print(json.dumps({"status": "success", "characters": results}, default=str, indent=2))
    return 0


def cmd_dev(args: argparse.Namespace) -> int:
    """Launches the interactive Studio workstation development server."""
    studio_dir = PROJECT_ROOT / "studio"
    print(f"▶ Starting Studio dev server in {studio_dir}...")
    try:
        subprocess.run(["npm", "run", "dev"], cwd=studio_dir, check=True)
        return 0
    except KeyboardInterrupt:
        print("\nStudio server terminated.")
        return 0
    except Exception as e:
        print(f"Error starting studio: {e}", file=sys.stderr)
        return 1


def resolve_asset_ir(target: str) -> AssetIR:
    """Resolves character ID, directory, or JSON file to an AssetIR instance."""
    p = Path(target)
    if p.is_file():
        if p.name.endswith(".img2game2d.json"):
            manifest = ProjectManifest.load(p)
            asset_path = p.parent / manifest.asset_ir
            with open(asset_path, "r", encoding="utf-8") as f:
                return deserialize_asset_ir(f.read())
        with open(p, "r", encoding="utf-8") as f:
            return deserialize_asset_ir(f.read())

    # Check character directories
    char_candidate = PROJECT_ROOT / "characters" / target
    if char_candidate.is_dir():
        return convert_legacy_character_to_asset_ir(char_candidate, project_root=PROJECT_ROOT)

    if p.is_dir():
        return convert_legacy_character_to_asset_ir(p, project_root=PROJECT_ROOT)

    raise FileNotFoundError(f"Cannot resolve target '{target}' to a valid character or AssetIR file.")


def cmd_inspect(args: argparse.Namespace) -> int:
    """Inspects an asset and outputs metadata, structure, and stats."""
    try:
        asset_ir = resolve_asset_ir(args.target)
        info = {
            "id": asset_ir.asset.id,
            "name": asset_ir.asset.name,
            "schema_version": asset_ir.schema_version,
            "canvas": {
                "width": asset_ir.canvas.width,
                "height": asset_ir.canvas.height,
                "pivot_x": asset_ir.canvas.pivot_x,
                "ground_y": asset_ir.canvas.ground_y,
            },
            "frames_count": len(asset_ir.frames),
            "animations": [
                {"name": a.name, "fps": a.fps, "loop": a.loop, "frames": len(a.frame_ids)}
                for a in asset_ir.animations
            ],
            "skeleton": {
                "root": asset_ir.skeleton.root_bone_id if asset_ir.skeleton else None,
                "bones_count": len(asset_ir.skeleton.bones) if asset_ir.skeleton else 0,
            },
            "materials": {
                "diffuse": asset_ir.materials.diffuse_map if asset_ir.materials else None,
                "normal": asset_ir.materials.normal_map if asset_ir.materials else None,
                "emission": asset_ir.materials.emission_map if asset_ir.materials else None,
            },
            "atlas": {
                "size": f"{asset_ir.atlas.width}x{asset_ir.atlas.height}" if asset_ir.atlas else None,
                "occupancy": f"{asset_ir.atlas.occupancy_ratio * 100:.1f}%" if asset_ir.atlas else None,
            },
        }
        if getattr(args, "json", False):
            print(json.dumps(info, indent=2))
        else:
            print(f"\nAsset: {info['name']} ({info['id']}) [AssetIR v{info['schema_version']}]")
            print(f"Canvas: {info['canvas']['width']}x{info['canvas']['height']} (Ground: {info['canvas']['ground_y']}, Pivot: {info['canvas']['pivot_x']})")
            print(f"Total Frames: {info['frames_count']}")
            print(f"Animations ({len(info['animations'])}):")
            for a in info["animations"]:
                print(f"  • {a['name']:<12} {a['frames']:>2} frames @ {a['fps']:>2} fps {'[loop]' if a['loop'] else ''}")
            if info["skeleton"]["bones_count"] > 0:
                print(f"Skeletal Rig: {info['skeleton']['bones_count']} bones (Root: {info['skeleton']['root']})")
            if info["atlas"]["size"]:
                print(f"Texture Atlas: {info['atlas']['size']} (Occupancy: {info['atlas']['occupancy']})")
        return 0
    except Exception as e:
        if getattr(args, "json", False):
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"Error inspecting asset: {e}", file=sys.stderr)
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Validates an asset against AssetIR rules and returns diagnostics."""
    try:
        asset_ir = resolve_asset_ir(args.target)
        diagnostics = validate_asset_ir(asset_ir)
        errors = [d for d in diagnostics if d.severity == "error"]
        warnings = [d for d in diagnostics if d.severity == "warning"]
        is_valid = len(errors) == 0

        result = {
            "valid": is_valid,
            "asset_id": asset_ir.asset.id,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "diagnostics": [d.to_dict() for d in diagnostics],
        }

        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            status_str = "✓ VALID" if is_valid else "✗ INVALID"
            print(f"\nValidation Result: {status_str} ({len(errors)} errors, {len(warnings)} warnings)")
            for d in diagnostics:
                prefix = "✖ ERROR" if d.severity == "error" else "⚠ WARN "
                loc_str = f" [Frame {d.location.get('frame')}]" if d.location and "frame" in d.location else ""
                print(f"  {prefix} [{d.code}]{loc_str}: {d.message}")
                if d.suggested_fix:
                    print(f"         Suggested Fix: {d.suggested_fix}")

        return 0 if is_valid else 1
    except Exception as e:
        if getattr(args, "json", False):
            print(json.dumps({"valid": False, "error": str(e)}, indent=2))
        else:
            print(f"Validation failed with error: {e}", file=sys.stderr)
        return 1


def cmd_convert(args: argparse.Namespace) -> int:
    """Converts a legacy character directory to canonical AssetIR and project manifest."""
    try:
        char_dir = Path(args.source)
        if not char_dir.is_dir():
            char_dir = PROJECT_ROOT / "characters" / args.source
        if not char_dir.is_dir():
            raise FileNotFoundError(f"Character directory not found: {args.source}")

        asset_ir = convert_legacy_character_to_asset_ir(char_dir, project_root=PROJECT_ROOT)
        out_dir = Path(args.out) if args.out else char_dir

        out_asset_file = out_dir / f"{asset_ir.asset.id}.assetir.json"
        with open(out_asset_file, "w", encoding="utf-8") as f:
            f.write(serialize_asset_ir(asset_ir))

        manifest = ProjectManifest(
            name=asset_ir.asset.name,
            source=f"charatcer 1.jpeg" if "architect" in asset_ir.asset.id else "charatcer 2.jpeg",
            asset_ir=out_asset_file.name,
            materials={"diffuse": asset_ir.materials.diffuse_map if asset_ir.materials else ""},
        )
        out_manifest_file = out_dir / f"{asset_ir.asset.id}.img2game2d.json"
        manifest.save(out_manifest_file)

        res = {
            "status": "success",
            "asset_id": asset_ir.asset.id,
            "asset_ir_file": str(out_asset_file),
            "manifest_file": str(out_manifest_file),
        }
        if getattr(args, "json", False):
            print(json.dumps(res, indent=2))
        else:
            print(f"✓ Converted '{asset_ir.asset.id}' to AssetIR v3:")
            print(f"  AssetIR:  {out_asset_file}")
            print(f"  Manifest: {out_manifest_file}")
        return 0
    except Exception as e:
        if getattr(args, "json", False):
            print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        else:
            print(f"Conversion error: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        prog="img2game2d",
        description="img2game2d v3 — Production 2D Game Asset Compiler",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 3.0.0 (Milestone V3.0 Asset Compiler)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. Legacy commands
    p_dev = subparsers.add_parser("dev", help="Start Studio workstation development server")
    p_dev.set_defaults(func=cmd_dev)

    p_build = subparsers.add_parser("build", help="Run full asset extraction and export pipeline")
    p_build.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_build.set_defaults(func=cmd_build)

    p_light = subparsers.add_parser("lighting", help="Generate 2D normal and emission lighting maps")
    p_light.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_light.set_defaults(func=cmd_lighting)

    p_slice = subparsers.add_parser("slice-actions", help="Extract and slice character action sheets")
    p_slice.add_argument("character", nargs="?", default="all", help="Character ID or 'all'")
    p_slice.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_slice.set_defaults(func=cmd_slice_actions)

    # 2. v3 Core commands
    p_inspect = subparsers.add_parser("inspect", help="Inspect asset metadata and hierarchy")
    p_inspect.add_argument("target", help="Character ID, directory, or manifest path")
    p_inspect.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_inspect.set_defaults(func=cmd_inspect)

    p_validate = subparsers.add_parser("validate", help="Validate asset structural integrity and geometry")
    p_validate.add_argument("target", help="Character ID, directory, or manifest path")
    p_validate.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_validate.set_defaults(func=cmd_validate)

    p_convert = subparsers.add_parser("convert", help="Convert legacy character metadata to canonical AssetIR")
    p_convert.add_argument("source", help="Character ID or path")
    p_convert.add_argument("--out", default=None, help="Output directory")
    p_convert.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_convert.set_defaults(func=cmd_convert)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
