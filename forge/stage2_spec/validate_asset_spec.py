#!/usr/bin/env python3
"""
Stage 2: Validate asset specification against JSON Schema.

Usage:
    python3 forge/stage2_spec/validate_asset_spec.py asset.json [--strict]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _shared.schema_utils import load_json, validate, load_schema


def validate_asset(path: str, strict: bool = False) -> tuple[bool, list[str]]:
    """
    Validate asset.json. Returns (passed, errors).
    In strict mode, also checks for shallow specs.
    """
    data = load_json(path)
    errors = validate(data, "asset")

    if strict:
        # Strict checks
        layers = data.get("layers", [])
        animations = data.get("animations", {})

        if len(layers) == 0:
            errors.append("STRICT: Asset has no layers defined.")
        if len(animations) == 0:
            errors.append("STRICT: Asset has no animations defined.")
        if data.get("asset_type") == "character":
            if not any(l.get("type") in ("torso", "body", "chest") for l in layers):
                errors.append("STRICT: Character asset has no torso/body layer.")
            if not any(a in animations for a in ("idle", "walk")):
                errors.append("STRICT: Character asset missing 'idle' or 'walk' animation.")
        for layer in layers:
            if not layer.get("pivot"):
                errors.append(f"STRICT: Layer '{layer.get('id', '?')}' missing pivot.")
            if layer.get("z_index") is None:
                errors.append(f"STRICT: Layer '{layer.get('id', '?')}' missing z_index.")

    return len(errors) == 0, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate asset.json against schema")
    parser.add_argument("asset", help="Path to asset.json")
    parser.add_argument("--strict", action="store_true", help="Enable strict checks")
    args = parser.parse_args()

    passed, errors = validate_asset(args.asset, strict=args.strict)

    if passed:
        print(f"✓ Validation passed: {args.asset}")
        sys.exit(0)
    else:
        print(f"✗ Validation failed: {args.asset}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
