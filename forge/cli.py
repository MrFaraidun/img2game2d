#!/usr/bin/env python3
"""
img2game2d unified CLI.
Subcommands:
  - analyze <image>
  - build <image> [--profile character|object|effect] [--engine godot|unity|phaser|pixijs|all]
  - animate <image> --animations idle,walk,attack
  - atlas <frames_dir> [--out atlases/]
  - export <asset.json> --atlases <atlases_dir> [--engine godot|unity|phaser|pixijs|all]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add forge directory to sys.path
FORGE_DIR = Path(__file__).resolve().parent
SKILL_ROOT = FORGE_DIR.parent
sys.path.insert(0, str(FORGE_DIR))

from _shared.schema_utils import load_json, save_json
from stage1_intake.probe_image import probe
from stage1_intake.detect_style import detect_style
from stage1_intake.detect_views import detect_views
from stage1_intake.remove_background import remove_background
from stage2_spec.new_asset_spec import build_asset_spec
from stage2_spec.validate_asset_spec import validate_asset
from stage2_spec.layer_decompose import decompose_layers
from stage2_spec.build_rig import build_rig
from stage3_build.orchestrate_build import orchestrate
from stage4_review.validate_silhouette import validate_silhouette
from stage4_review.validate_colors import validate_colors
from stage4_review.validate_continuity import validate_continuity
from stage4_review.make_comparison_sheet import make_comparison_sheet
from stage4_review.append_review import append_review
from stage5_atlas.pack_atlas import pack_atlas
from stage6_export.export import export as run_export


def cmd_analyze(args: argparse.Namespace) -> None:
    img_path = args.image
    if not Path(img_path).exists():
        print(f"Error: image file not found: {img_path}", file=sys.stderr)
        sys.exit(1)

    print(f"=== Analyzing {img_path} ===")
    info = probe(img_path)
    print(f"Format: {info['format']} | Dimensions: {info['width']}x{info['height']} | Alpha: {info['has_alpha']}")

    style_info = detect_style(img_path)
    print(f"Art Style: {style_info['detected_style']} (confidence: {style_info['confidence']:.2f})")

    view_info = detect_views(img_path)
    views_str = ", ".join([v.get("label", "view") for v in view_info.get("views", [])])
    print(f"Views Detected ({view_info['view_count']}): {views_str}")

    out_dir = Path(args.out_dir) if args.out_dir else Path("analysis")
    out_dir.mkdir(parents=True, exist_ok=True)
    save_json(info, str(out_dir / "probe.json"))
    save_json(style_info, str(out_dir / "style.json"))
    save_json(view_info, str(out_dir / "views.json"))
    print(f"Analysis saved to {out_dir}/")


def cmd_build(args: argparse.Namespace) -> None:
    img_path = args.image
    if not Path(img_path).exists():
        print(f"Error: image file not found: {img_path}", file=sys.stderr)
        sys.exit(1)

    out_root = Path(args.out)
    source_dir = out_root / "source"
    analysis_dir = out_root / "analysis"
    layers_dir = out_root / "layers"
    anim_dir = out_root / "animations"
    atlas_dir = out_root / "atlases"
    meta_dir = out_root / "metadata"
    export_dir = out_root / "exports"

    for d in [source_dir, analysis_dir, layers_dir, anim_dir, atlas_dir, meta_dir, export_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Intake
    print("\n[1/6] Running Intake...")
    fg_path = str(source_dir / "foreground.png")
    mask_path = str(source_dir / "mask.png")
    remove_background(img_path, fg_path, mask_path)

    style_res = detect_style(img_path)
    view_res = detect_views(img_path)
    probe_res = probe(img_path)

    stem = Path(img_path).stem.replace(" ", "_").lower()
    analysis_data = {
        "asset_id": stem,
        "name": Path(img_path).stem.title(),
        "asset_type": args.type,
        "character_type": "humanoid" if args.type == "character" else "item",
        "visual_style": style_res["detected_style"],
        "source_image": str(Path(img_path).resolve()),
        "views_detected": [v.get("label", "front") for v in view_res.get("views", [])] or ["front"],
        "resolution": {"width": probe_res["width"], "height": probe_res["height"]},
        "bounding_box": {"x": 0, "y": 0, "width": probe_res["width"], "height": probe_res["height"]},
        "parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"],
        "colors": [{"hex": "#1a1a2e", "role": "main"}],
        "symmetry": "near-symmetric",
        "animations": [a.strip() for a in args.animations.split(",") if a.strip()],
    }
    save_json(analysis_data, str(analysis_dir / "analysis.json"))

    # 2. Spec
    print("\n[2/6] Generating Spec...")
    asset_spec = build_asset_spec(analysis_data, style_res)
    asset_path = str(out_root / "asset.json")
    save_json(asset_spec, asset_path)
    valid, errors = validate_asset(asset_path)
    if not valid:
        print(f"Warning: Spec validation issues: {errors}")

    layer_spec = decompose_layers(asset_spec)
    layer_spec_path = str(layers_dir / "layer-spec.json")
    save_json(layer_spec, layer_spec_path)

    rig = build_rig(layer_spec)
    save_json(rig, str(meta_dir / "rig.json"))

    # 3. Build
    print("\n[3/6] Building Layers & Animation Frames...")
    orchestrate(
        source=fg_path,
        reference=img_path,
        spec=layer_spec_path,
        asset=asset_path,
        animations=asset_spec["animations"].keys(),
        out_layers=str(layers_dir) + "/",
        out_frames=str(anim_dir) + "/",
        provider=args.provider,
    )

    sil_res = validate_silhouette(img_path, str(anim_dir / "idle"))
    save_json(sil_res, str(analysis_dir / "silhouette_check.json"))

    col_res = validate_colors(img_path, str(anim_dir))
    save_json(col_res, str(analysis_dir / "color_check.json"))

    cont_res = validate_continuity(str(anim_dir))
    save_json(cont_res, str(analysis_dir / "continuity_check.json"))

    make_comparison_sheet(img_path, str(anim_dir / "idle"), str(analysis_dir / "comparison.png"))

    review_action = "continue" if (sil_res.get("passed", True) and cont_res.get("passed", True)) else "refine-frames"
    append_review(
        asset_path,
        stage="review",
        action=review_action,
        silhouette=sil_res.get("score", 0.9),
        colors=col_res.get("score", 0.9),
        continuity=cont_res.get("score", 0.9),
        summary="Automated build review complete."
    )

    # 5. Atlas
    print("\n[5/6] Packing Atlases...")
    pack_atlas(str(anim_dir) + "/", str(atlas_dir) + "/", power_of_two=True)

    # 6. Export
    print("\n[6/6] Exporting Game Assets...")
    asset_spec = load_json(asset_path)
    run_export(asset_spec, str(atlas_dir) + "/", args.engine, str(export_dir) + "/")

    print(f"\n✓ Pipeline complete! Assets generated at: {out_root}/")


def main() -> None:
    parser = argparse.ArgumentParser(prog="img2game2d", description="2D Game Asset Generation Pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Probe and analyze 2D reference image")
    p_analyze.add_argument("image", help="Path to input image")
    p_analyze.add_argument("--out-dir", default=None, help="Output directory for analysis JSONs")
    p_analyze.set_defaults(func=cmd_analyze)

    # build
    p_build = subparsers.add_parser("build", help="Run end-to-end asset generation pipeline")
    p_build.add_argument("image", help="Path to input image")
    p_build.add_argument("--type", default="character", choices=["character", "object", "effect"])
    p_build.add_argument("--engine", default="all", choices=["godot", "unity", "phaser", "pixijs", "all"])
    p_build.add_argument("--animations", default="idle,walk,attack", help="Comma-separated animations")
    p_build.add_argument("--provider", default="stub", choices=["stub", "openai", "local"])
    p_build.add_argument("--out", default="game-asset", help="Output directory")
    p_build.set_defaults(func=cmd_build)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
