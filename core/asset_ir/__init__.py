"""
img2game2d Canonical AssetIR (Intermediate Representation) Package.
"""
from .types import (
    AnimationClipIR,
    AnimationCurveIR,
    AssetIR,
    AssetMetaIR,
    AtlasIR,
    BoneConstraintIR,
    BoneIR,
    BoneRestIR,
    CanvasMetaIR,
    ColliderIR,
    DiagnosticIR,
    FrameIR,
    KeyframeIR,
    LayerIR,
    MaterialIR,
    MeshIR,
    ProvenanceIR,
    SkeletonIR,
    SourceMetaIR,
    VertexWeightIR,
    ViewIR,
)
from .transforms import (
    canvas_to_spine,
    canvas_to_uv,
    canvas_to_world,
    deg_to_rad,
    normalize_angle_rad,
    rad_to_deg,
    spine_to_canvas,
    uv_to_canvas,
    world_to_canvas,
)
from .validation import (
    validate_asset_ir,
    validate_atlas,
    validate_colliders,
    validate_frames,
    validate_materials,
    validate_mesh,
    validate_skeleton,
)
from .schema import (
    asset_ir_to_dict,
    deserialize_asset_ir,
    serialize_asset_ir,
)
from .versioning import (
    CURRENT_SCHEMA_VERSION,
    is_compatible,
    migrate_to_v3,
    parse_semver,
)
from .manifest import (
    ProjectManifest,
)
from .converter import (
    convert_legacy_character_to_asset_ir,
)

__all__ = [
    # Types
    "AssetIR",
    "AssetMetaIR",
    "SourceMetaIR",
    "CanvasMetaIR",
    "ViewIR",
    "LayerIR",
    "FrameIR",
    "AnimationClipIR",
    "AnimationCurveIR",
    "KeyframeIR",
    "SkeletonIR",
    "BoneIR",
    "BoneRestIR",
    "BoneConstraintIR",
    "MeshIR",
    "VertexWeightIR",
    "ColliderIR",
    "MaterialIR",
    "AtlasIR",
    "DiagnosticIR",
    "ProvenanceIR",
    # Transforms
    "canvas_to_world",
    "world_to_canvas",
    "canvas_to_spine",
    "spine_to_canvas",
    "canvas_to_uv",
    "uv_to_canvas",
    "normalize_angle_rad",
    "deg_to_rad",
    "rad_to_deg",
    # Validation
    "validate_asset_ir",
    "validate_frames",
    "validate_atlas",
    "validate_skeleton",
    "validate_mesh",
    "validate_colliders",
    "validate_materials",
    # Schema
    "serialize_asset_ir",
    "deserialize_asset_ir",
    "asset_ir_to_dict",
    # Versioning
    "CURRENT_SCHEMA_VERSION",
    "is_compatible",
    "migrate_to_v3",
    "parse_semver",
    # Manifest
    "ProjectManifest",
    # Converter
    "convert_legacy_character_to_asset_ir",
]
