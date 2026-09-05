#!/usr/bin/env python3
"""
Stage 2: Generate asset specification from visual analysis.

Takes analysis/analysis.json (produced by agent visual analysis) and creates
a validated asset.json conforming to schemas/asset.schema.json.

Usage:
    python3 forge/stage2_spec/new_asset_spec.py \
        --analysis analysis/analysis.json \
        --style analysis/style.json \
        --out asset.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import validate_or_exit, save_json, load_json


def build_asset_spec(analysis: dict, style: dict | None = None) -> dict:
    """
    Build a minimal valid asset.json from visual analysis data.
    Agent is expected to have produced detailed analysis — this script
    structures it into a schema-compliant spec.
    """
    style_data = style or {}
    detected_style = style_data.get("detected_style", "preserve")
    views = analysis.get("views_detected", ["front"])

    # Build layer list from detected parts
    raw_parts = analysis.get("parts", [])
    layers = []
    z_counter = 10
    for i, part in enumerate(raw_parts):
        if isinstance(part, str):
            part_id = part.lower().replace(" ", "_").replace("-", "_")
            layer = {
                "id": part_id,
                "name": part.replace("_", " ").title(),
                "type": _guess_part_type(part_id),
                "parent": _guess_parent(part_id, raw_parts),
                "z_index": z_counter + i * 10,
                "pivot": _default_pivot(part_id),
                "visible": True,
                "occlusion": {"occluded_by": [], "reconstructed": False},
            }
            layers.append(layer)
        elif isinstance(part, dict):
            layers.append(part)

    # Colors
    colors = []
    for c in analysis.get("colors", []):
        if isinstance(c, dict):
            colors.append(c)
        elif isinstance(c, str):
            colors.append({"hex": c, "role": "unknown"})

    # Build animations spec
    anim_names = analysis.get("animations", _default_animations(analysis.get("asset_type", "character")))
    fps_map = {
        "idle": 8, "walk": 12, "run": 16, "jump": 10, "fall": 10,
        "attack": 14, "hurt": 10, "death": 8, "dash": 16,
    }
    animations = {}
    for anim in anim_names:
        fps = fps_map.get(anim, 12)
        animations[anim] = {
            "name": anim,
            "fps": fps,
            "loop": anim not in ("death", "attack", "hurt", "jump"),
            "frames": [],
            "frame_count": 0,
        }

    spec = {
        "asset_id": analysis.get("asset_id", "unnamed_asset"),
        "name": analysis.get("name", "Unnamed Asset"),
        "asset_type": analysis.get("asset_type", "character"),
        "visual_style": detected_style,
        "source_image": analysis.get("source_image", ""),
        "views_detected": views,
        "resolution": analysis.get("resolution", {"width": 512, "height": 512}),
        "bounding_box": analysis.get("bounding_box", {"x": 0, "y": 0, "width": 512, "height": 512}),
        "silhouette_score": analysis.get("silhouette_score", 0.0),
        "symmetry": analysis.get("symmetry", "unknown"),
        "proportions": analysis.get("proportions", {}),
        "colors": colors,
        "layers": layers,
        "animations": animations,
        "validation": {
            "passed": False,
            "silhouette": 0.0,
            "color_consistency": 0.0,
            "frame_alignment": 0.0,
            "part_consistency": 0.0,
        },
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "img2game2d_version": "1.0.0",
            "source_analysis": "analysis/analysis.json",
        },
    }

    # Add character/object type
    if analysis.get("character_type"):
        spec["character_type"] = analysis["character_type"]
    if analysis.get("object_type"):
        spec["object_type"] = analysis["object_type"]

    return spec


def _guess_part_type(part_id: str) -> str:
    type_map = {
        "head": "head", "face": "face", "hair": "hair", "horn": "horn", "horns": "horn",
        "eye": "eye", "eyes": "eye", "mouth": "mouth", "ear": "ear", "ears": "ear",
        "neck": "neck", "torso": "torso", "body": "torso", "chest": "chest",
        "arm": "arm", "arm_left": "arm", "arm_right": "arm", "left_arm": "arm", "right_arm": "arm",
        "forearm": "forearm", "hand": "hand", "shoulder": "shoulder",
        "leg": "leg", "leg_left": "leg", "leg_right": "leg", "left_leg": "leg", "right_leg": "leg",
        "foot": "foot", "feet": "foot", "hip": "hip",
        "tail": "tail", "wing": "wing", "claw": "claw",
        "cloak": "cloak", "cape": "cloak", "armor": "armor", "clothing": "clothing",
        "weapon": "weapon", "sword": "weapon", "shield": "shield",
        "mask": "armor", "nail": "weapon",
    }
    for key, val in type_map.items():
        if key in part_id:
            return val
    return "other"


def _guess_parent(part_id: str, all_parts: list) -> str | None:
    """Infer parent based on anatomical hierarchy."""
    torso_parts = ["torso", "body", "chest"]
    head_parts = ["head", "face", "hair", "horn", "eye", "ear", "mask"]
    arm_parts = ["forearm", "hand"]
    leg_parts = ["foot", "lower_leg"]

    for p in head_parts:
        if p in part_id:
            # Head parts parent to "head" if it exists
            if any("head" in pp.lower() for pp in all_parts if isinstance(pp, str)):
                return "head"
            return "torso"

    for p in arm_parts:
        if p in part_id:
            return "arm_left" if "left" in part_id else "arm_right" if "right" in part_id else "arm"

    for p in leg_parts:
        if p in part_id:
            return "leg_left" if "left" in part_id else "leg_right" if "right" in part_id else "leg"

    if any(p in part_id for p in ["arm", "leg", "cloak", "cape"]):
        return "torso"

    if any(p in part_id for p in torso_parts):
        return "root"

    return "root"


def _default_pivot(part_id: str) -> dict:
    """Return sensible default pivot points for common body parts."""
    pivot_map = {
        "head":       {"x": 0.5, "y": 1.0},  # Bottom-center (neck joint)
        "arm_left":   {"x": 1.0, "y": 0.1},  # Right edge, near top (shoulder)
        "arm_right":  {"x": 0.0, "y": 0.1},
        "left_arm":   {"x": 1.0, "y": 0.1},
        "right_arm":  {"x": 0.0, "y": 0.1},
        "forearm":    {"x": 0.5, "y": 0.0},  # Top (elbow)
        "hand":       {"x": 0.5, "y": 0.0},  # Top (wrist)
        "leg_left":   {"x": 0.5, "y": 0.0},  # Top (hip)
        "leg_right":  {"x": 0.5, "y": 0.0},
        "left_leg":   {"x": 0.5, "y": 0.0},
        "right_leg":  {"x": 0.5, "y": 0.0},
        "foot":       {"x": 0.5, "y": 0.0},  # Top (ankle)
        "weapon":     {"x": 0.5, "y": 0.8},  # Near grip
        "cloak":      {"x": 0.5, "y": 0.0},  # Top (shoulder attachment)
    }
    for key, pivot in pivot_map.items():
        if key in part_id:
            return pivot
    return {"x": 0.5, "y": 0.5}  # Center default


def _default_animations(asset_type: str) -> list[str]:
    """Return default animation set for asset type."""
    if asset_type == "character":
        return ["idle", "walk", "run", "jump", "fall", "attack", "hurt", "death"]
    elif asset_type == "object":
        return ["idle"]
    elif asset_type == "effect":
        return ["play"]
    return ["idle"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate asset spec from analysis")
    parser.add_argument("--analysis", required=True, help="Path to analysis.json")
    parser.add_argument("--style", default=None, help="Path to style.json")
    parser.add_argument("--out", default="asset.json")
    args = parser.parse_args()

    analysis = load_json(args.analysis)
    style = load_json(args.style) if args.style and Path(args.style).exists() else None

    spec = build_asset_spec(analysis, style)
    validate_or_exit(spec, "asset", label="asset.json")
    save_json(spec, args.out)
    print(f"Asset spec generated: {args.out}")
    print(f"  Layers    : {len(spec['layers'])}")
    print(f"  Animations: {list(spec['animations'].keys())}")
    print(f"  Style     : {spec['visual_style']}")


if __name__ == "__main__":
    main()
