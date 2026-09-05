#!/usr/bin/env python3
"""
Stage 2: Layer decomposition.
Takes asset.json layers and generates layer-spec.json with bounding box estimates,
z-ordering, pivot points, and depth hierarchy.

Usage:
    python3 forge/stage2_spec/layer_decompose.py asset.json --out layers/layer-spec.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json, save_json


def decompose_layers(asset: dict) -> dict:
    """
    Build a layer decomposition spec from the asset definition.
    Enriches layer data with computed bounding box estimates and hierarchy.
    """
    layers = asset.get("layers", [])
    res = asset.get("resolution", {"width": 512, "height": 512})
    w, h = res["width"], res["height"]

    # Sort by z_index
    sorted_layers = sorted(layers, key=lambda l: l.get("z_index", 0))

    # Build parent map
    parent_map: dict[str, list[str]] = {}
    for layer in sorted_layers:
        parent = layer.get("parent")
        if parent:
            parent_map.setdefault(parent, []).append(layer["id"])

    # Estimate bounding boxes if not already specified
    for layer in sorted_layers:
        if not layer.get("bounding_box"):
            layer["bounding_box"] = _estimate_bbox(layer["id"], layer.get("type", "other"), w, h)

    # Build depth order (back to front)
    depth_order = [l["id"] for l in sorted_layers]

    # Identify root layers (no parent or parent=root)
    roots = [l["id"] for l in sorted_layers if not l.get("parent") or l.get("parent") == "root"]

    spec = {
        "asset_id": asset.get("asset_id"),
        "canvas_size": {"width": w, "height": h},
        "layer_count": len(sorted_layers),
        "depth_order": depth_order,
        "roots": roots,
        "hierarchy": _build_hierarchy(sorted_layers),
        "layers": {l["id"]: l for l in sorted_layers},
        "occlusion_groups": _find_occlusion_groups(sorted_layers),
    }

    return spec


def _estimate_bbox(layer_id: str, layer_type: str, w: int, h: int) -> dict:
    """
    Estimate bounding box for a layer based on its type and canvas size.
    These are rough estimates — agent or manual refinement is expected.
    """
    # Rough anatomical proportions (normalized)
    proportions: dict[str, tuple[float, float, float, float]] = {
        "head":     (0.30, 0.00, 0.40, 0.25),
        "face":     (0.32, 0.04, 0.36, 0.18),
        "hair":     (0.25, 0.00, 0.50, 0.22),
        "horn":     (0.30, 0.00, 0.40, 0.12),
        "eye":      (0.30, 0.08, 0.40, 0.12),
        "ear":      (0.20, 0.05, 0.15, 0.10),
        "neck":     (0.38, 0.22, 0.24, 0.06),
        "torso":    (0.20, 0.25, 0.60, 0.35),
        "chest":    (0.25, 0.25, 0.50, 0.20),
        "cloak":    (0.10, 0.20, 0.80, 0.50),
        "armor":    (0.20, 0.25, 0.60, 0.35),
        "arm":      (0.10, 0.25, 0.25, 0.35),
        "forearm":  (0.10, 0.40, 0.20, 0.25),
        "hand":     (0.10, 0.60, 0.18, 0.15),
        "leg":      (0.25, 0.60, 0.25, 0.30),
        "lower_leg":(0.25, 0.75, 0.22, 0.20),
        "foot":     (0.22, 0.88, 0.25, 0.12),
        "weapon":   (0.60, 0.20, 0.15, 0.45),
        "tail":     (0.65, 0.50, 0.30, 0.40),
        "wing":     (0.00, 0.15, 0.40, 0.50),
    }

    # Check if layer_id contains a known type key
    for key, (nx, ny, nw, nh) in proportions.items():
        if key in layer_id:
            # Adjust for left/right
            if "right" in layer_id:
                nx = 1.0 - nx - nw
            return {
                "x": round(nx * w),
                "y": round(ny * h),
                "width": round(nw * w),
                "height": round(nh * h),
                "estimated": True,
            }

    # Fallback: center box
    return {
        "x": round(w * 0.2),
        "y": round(h * 0.2),
        "width": round(w * 0.6),
        "height": round(h * 0.6),
        "estimated": True,
    }


def _build_hierarchy(layers: list[dict]) -> dict:
    """Build nested hierarchy dict from flat layer list."""
    result: dict = {}
    id_map = {l["id"]: l for l in layers}

    def add_children(parent_id: str, node: dict) -> None:
        children = [l for l in layers if l.get("parent") == parent_id]
        for child in children:
            child_node: dict = {}
            add_children(child["id"], child_node)
            node[child["id"]] = child_node

    for layer in layers:
        parent = layer.get("parent")
        if not parent or parent == "root":
            node: dict = {}
            add_children(layer["id"], node)
            result[layer["id"]] = node

    return result


def _find_occlusion_groups(layers: list[dict]) -> list[dict]:
    """
    Identify layers that occlude others based on z_index overlap.
    Returns list of occlusion pairs.
    """
    groups = []
    for i, layer in enumerate(layers):
        occluded_by = []
        bb = layer.get("bounding_box")
        if not bb:
            continue
        for other in layers[i + 1:]:  # Higher z = in front
            obb = other.get("bounding_box")
            if not obb:
                continue
            if _boxes_overlap(bb, obb):
                occluded_by.append(other["id"])
        if occluded_by:
            groups.append({
                "layer": layer["id"],
                "occluded_by": occluded_by,
                "needs_reconstruction": True,
            })
    return groups


def _boxes_overlap(a: dict, b: dict) -> bool:
    """Check if two bounding boxes overlap."""
    ax1, ay1 = a["x"], a["y"]
    ax2, ay2 = ax1 + a["width"], ay1 + a["height"]
    bx1, by1 = b["x"], b["y"]
    bx2, by2 = bx1 + b["width"], by1 + b["height"]
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1


def main() -> None:
    parser = argparse.ArgumentParser(description="Decompose asset layers")
    parser.add_argument("asset", help="Path to asset.json")
    parser.add_argument("--out", default="layers/layer-spec.json")
    args = parser.parse_args()

    asset = load_json(args.asset)
    spec = decompose_layers(asset)
    save_json(spec, args.out)
    print(f"Layer spec: {spec['layer_count']} layers → {args.out}")
    print(f"Roots      : {spec['roots']}")
    print(f"Occlusions : {len(spec['occlusion_groups'])} groups")


if __name__ == "__main__":
    main()
