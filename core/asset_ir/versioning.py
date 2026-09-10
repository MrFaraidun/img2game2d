"""
Schema versioning and migration engine for img2game2d AssetIR.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

CURRENT_SCHEMA_VERSION = "3.0.0"
SUPPORTED_SCHEMA_VERSIONS = {"3.0.0"}


def parse_semver(version_str: str) -> Tuple[int, int, int]:
    """Parses SemVer string into (major, minor, patch) integer tuple."""
    parts = version_str.strip().split(".")
    try:
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return major, minor, patch
    except ValueError:
        return 0, 0, 0


def is_compatible(version_str: str) -> bool:
    """Checks if a schema version is compatible with current engine."""
    major, _, _ = parse_semver(version_str)
    cur_major, _, _ = parse_semver(CURRENT_SCHEMA_VERSION)
    return major == cur_major


def migrate_to_v3(raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrates a legacy or unversioned asset dictionary to canonical AssetIR v3.0.0 structure.
    """
    version = raw_dict.get("schema_version") or raw_dict.get("version", "1.0.0")

    if version == CURRENT_SCHEMA_VERSION:
        return raw_dict

    migrated = dict(raw_dict)
    migrated["schema_version"] = CURRENT_SCHEMA_VERSION

    # If canvas missing, infer from canvas_size or defaults
    if "canvas" not in migrated:
        c_size = migrated.get("canvas_size", {})
        p_pt = migrated.get("pivot", {})
        migrated["canvas"] = {
            "width": c_size.get("width", 576),
            "height": c_size.get("height", 512),
            "pivot_x": p_pt.get("x", 288),
            "ground_y": p_pt.get("y", 460),
        }

    # Ensure list containers exist
    for field in ["views", "layers", "frames", "animations", "meshes", "colliders", "diagnostics"]:
        if field not in migrated or not isinstance(migrated[field], list):
            migrated[field] = []

    return migrated
