#!/usr/bin/env python3
"""
Stage 2: Build skeletal rig from layer specification.
Creates a hierarchical bone structure matching the layer hierarchy.

Usage:
    python3 forge/stage2_spec/build_rig.py layers/layer-spec.json --out metadata/rig.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json, save_json, validate_or_exit


# Standard attachment points for body parts
ATTACHMENT_POINTS = {
    "head":       "neck",
    "hair":       "head",
    "horn":       "head",
    "horns":      "head",
    "eye":        "head",
    "ear":        "head",
    "mask":       "head",
    "forearm":    "elbow",
    "hand":       "wrist",
    "lower_leg":  "knee",
    "foot":       "ankle",
    "weapon":     "grip",
    "tail":       "base",
    "cloak":      "shoulder",
    "cape":       "shoulder",
    "wing":       "back",
}

# Rotation constraints (min, max degrees)
ROTATION_CONSTRAINTS = {
    "head":       (-45, 45),
    "arm":        (-180, 180),
    "forearm":    (-135, 0),
    "leg":        (-45, 90),
    "lower_leg":  (-120, 0),
    "foot":       (-45, 60),
    "cloak":      (-20, 20),
}


def build_rig(layer_spec: dict) -> dict:
    """Build a skeletal rig from layer specification."""
    asset_id = layer_spec.get("asset_id", "unknown")
    layers = layer_spec.get("layers", {})
    roots = layer_spec.get("roots", [])

    bones = []
    for layer_id, layer in layers.items():
        bb = layer.get("bounding_box", {})
        pivot = layer.get("pivot", {"x": 0.5, "y": 0.5})
        layer_type = layer.get("type", "other")

        # Compute pivot in pixel space
        pivot_px = {
            "x": bb.get("x", 0) + bb.get("width", 0) * pivot.get("x", 0.5),
            "y": bb.get("y", 0) + bb.get("height", 0) * pivot.get("y", 0.5),
        }

        bone: dict = {
            "id": f"bone_{layer_id}",
            "name": layer.get("name", layer_id),
            "parent": f"bone_{layer.get('parent')}" if layer.get("parent") and layer.get("parent") != "root" else None,
            "layer_id": layer_id,
            "pivot": pivot_px,
            "length": _estimate_bone_length(bb, layer_type),
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "attachments": [layer_id],
        }

        # Attachment point
        for key, attachment in ATTACHMENT_POINTS.items():
            if key in layer_id:
                bone["attachment_point"] = attachment
                break

        # Rotation constraints
        bone["constraints"] = []
        for key, (cmin, cmax) in ROTATION_CONSTRAINTS.items():
            if key in layer_id:
                bone["constraints"].append({
                    "type": "rotation_limit",
                    "min": cmin,
                    "max": cmax,
                })
                break

        bones.append(bone)

    # Find root bone
    root_bone_id = f"bone_{roots[0]}" if roots else (f"bone_{next(iter(layers))}" if layers else "bone_root")

    # Add a virtual root if needed
    has_root_bone = any(b["id"] == root_bone_id for b in bones)
    if not has_root_bone:
        bones.insert(0, {
            "id": "bone_root",
            "name": "Root",
            "parent": None,
            "layer_id": None,
            "pivot": {"x": 0.5, "y": 0.5},
            "length": 0,
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "attachments": [],
            "constraints": [],
        })
        root_bone_id = "bone_root"
        # Reparent root-level bones to virtual root
        for bone in bones:
            if bone["id"] != "bone_root" and bone["parent"] is None:
                bone["parent"] = "bone_root"

    rig = {
        "asset_id": asset_id,
        "root": root_bone_id,
        "bone_count": len(bones),
        "bones": bones,
    }

    return rig


def _estimate_bone_length(bb: dict, layer_type: str) -> float:
    """Estimate bone length from bounding box."""
    h = bb.get("height", 0)
    w = bb.get("width", 0)
    if layer_type in ("arm", "forearm", "leg", "lower_leg"):
        return float(h)
    elif layer_type in ("head", "torso", "chest"):
        return float(h * 0.8)
    elif layer_type in ("weapon",):
        return float(h * 0.9)
    return float(max(w, h) * 0.5)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build skeletal rig from layer spec")
    parser.add_argument("layer_spec", help="Path to layer-spec.json")
    parser.add_argument("--out", default="metadata/rig.json")
    args = parser.parse_args()

    layer_spec = load_json(args.layer_spec)
    rig = build_rig(layer_spec)
    validate_or_exit(rig, "rig", label="rig.json")
    save_json(rig, args.out)
    print(f"Rig built: {rig['bone_count']} bones → {args.out}")
    print(f"Root bone: {rig['root']}")


if __name__ == "__main__":
    main()
