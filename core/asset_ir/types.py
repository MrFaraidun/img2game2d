"""
img2game2d v3 Canonical AssetIR Types.
Defines engine-neutral, local-first data classes and structures for 2D game assets.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional, Tuple


@dataclass
class AssetMetaIR:
    id: str
    name: str
    source_hash: str
    tags: List[str] = field(default_factory=list)


@dataclass
class SourceMetaIR:
    width: int
    height: int
    color_space: Literal["sRGB", "Linear"] = "sRGB"
    has_alpha: bool = True
    format: str = "PNG"


@dataclass
class CanvasMetaIR:
    width: int
    height: int
    pivot_x: int
    ground_y: int


@dataclass
class ViewIR:
    id: str
    name: str
    yaw_degrees: float = 0.0
    pitch_degrees: float = 0.0
    landmarks_2d: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class LayerIR:
    id: str
    name: str
    semantic_role: str  # head, chest, upper_arm_L, weapon, etc.
    z_index: int = 0
    opacity: float = 1.0
    visible: bool = True


@dataclass
class FrameIR:
    id: str
    animation: str
    index: int
    duration_ms: int
    # Canvas coordinates (px): [x, y, w, h]
    canvas_rect: Dict[str, int]
    # Tight crop in packed atlas (px): [x, y, w, h]
    atlas_rect: Optional[Dict[str, int]] = None
    # Normalized UV [0.0 .. 1.0]: [u0, v0, u1, v1]
    uv_rect: Optional[Dict[str, float]] = None
    pivot: Dict[str, float] = field(default_factory=lambda: {"x": 0.5, "y": 0.5})
    ground_anchor: bool = True
    delta_y: int = 0


@dataclass
class KeyframeIR:
    time_sec: float
    value: float
    in_tangent: Optional[float] = None
    out_tangent: Optional[float] = None
    interpolation: Literal["linear", "step", "bezier"] = "linear"


@dataclass
class AnimationCurveIR:
    property: str
    target_id: str
    keyframes: List[KeyframeIR] = field(default_factory=list)


@dataclass
class AnimationClipIR:
    id: str
    name: str
    fps: int
    loop: bool
    frame_ids: List[str]
    curves: Dict[str, AnimationCurveIR] = field(default_factory=dict)


@dataclass
class BoneRestIR:
    x: float
    y: float
    rotation_rad: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0


@dataclass
class BoneConstraintIR:
    id: str
    type: Literal["two_bone_ik", "foot_lock", "aim"]
    target_bone_id: str
    root_bone_id: Optional[str] = None
    mid_bone_id: Optional[str] = None
    pole_target: Optional[Dict[str, float]] = None
    bend_positive: bool = True
    min_angle_rad: Optional[float] = None
    max_angle_rad: Optional[float] = None
    weight: float = 1.0


@dataclass
class BoneIR:
    id: str
    name: str
    parent_id: Optional[str]
    length: float
    rest: BoneRestIR
    color_hex: str = "00f0ff"


@dataclass
class SkeletonIR:
    root_bone_id: str
    bones: List[BoneIR] = field(default_factory=list)
    constraints: List[BoneConstraintIR] = field(default_factory=list)


@dataclass
class VertexWeightIR:
    bone_id: str
    weight: float


@dataclass
class MeshIR:
    id: str
    layer_id: str
    vertices: List[float]  # [x0, y0, x1, y1, ...] in canvas coordinates
    triangles: List[int]   # [i0, i1, i2, ...]
    uvs: List[float]       # [u0, v0, u1, v1, ...]
    weights: List[List[VertexWeightIR]] = field(default_factory=list)


@dataclass
class ColliderIR:
    id: str
    name: str
    type: Literal["hitbox", "hurtbox", "body", "foot", "interaction"]
    shape: Literal["box", "circle", "capsule", "polygon"]
    offset: Dict[str, float]
    size: Dict[str, float]
    radius: Optional[float] = None
    points: Optional[List[Dict[str, float]]] = None
    attached_bone_id: Optional[str] = None


@dataclass
class MaterialIR:
    diffuse_map: str
    normal_map: Optional[str] = None
    emission_map: Optional[str] = None
    height_map: Optional[str] = None
    normal_strength: float = 2.5
    bloom_emission: bool = True
    lum_threshold: float = 140.0
    sat_threshold: float = 0.25


@dataclass
class AtlasIR:
    image_path: str
    width: int
    height: int
    padding: int = 2
    power_of_two: bool = True
    occupancy_ratio: float = 0.0
    wasted_pixels: int = 0


@dataclass
class DiagnosticIR:
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    asset_id: Optional[str] = None
    object_id: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ProvenanceIR:
    generator: str = "img2game2d"
    version: str = "3.0.0"
    timestamp_utc: str = ""
    pipeline_stages: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssetIR:
    schema_version: str
    asset: AssetMetaIR
    source: SourceMetaIR
    canvas: CanvasMetaIR
    views: List[ViewIR] = field(default_factory=list)
    layers: List[LayerIR] = field(default_factory=list)
    frames: List[FrameIR] = field(default_factory=list)
    animations: List[AnimationClipIR] = field(default_factory=list)
    skeleton: Optional[SkeletonIR] = None
    meshes: List[MeshIR] = field(default_factory=list)
    colliders: List[ColliderIR] = field(default_factory=list)
    materials: Optional[MaterialIR] = None
    atlas: Optional[AtlasIR] = None
    diagnostics: List[DiagnosticIR] = field(default_factory=list)
    provenance: Optional[ProvenanceIR] = None
