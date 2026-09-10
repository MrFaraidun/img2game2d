"""
Schema serialization, deserialization, and validation for AssetIR.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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


def serialize_asset_ir(asset: AssetIR, indent: Optional[int] = 2) -> str:
    """Serializes an AssetIR instance into a deterministic JSON string."""
    return json.dumps(asset_ir_to_dict(asset), indent=indent, ensure_ascii=False)


def asset_ir_to_dict(asset: AssetIR) -> Dict[str, Any]:
    """Converts an AssetIR instance to a pure Python dictionary."""
    d = asdict(asset)
    # Ensure diagnostics are formatted cleanly
    return d


def deserialize_asset_ir(data: Union[str, Dict[str, Any]]) -> AssetIR:
    """Deserializes JSON string or dictionary into an AssetIR instance."""
    if isinstance(data, str):
        raw = json.loads(data)
    else:
        raw = data

    schema_version = raw.get("schema_version", "3.0.0")

    # 1. Asset Meta
    a_raw = raw.get("asset", {})
    asset_meta = AssetMetaIR(
        id=a_raw.get("id", "unknown"),
        name=a_raw.get("name", "Unknown Asset"),
        source_hash=a_raw.get("source_hash", ""),
        tags=a_raw.get("tags", []),
    )

    # 2. Source Meta
    s_raw = raw.get("source", {})
    source_meta = SourceMetaIR(
        width=s_raw.get("width", 0),
        height=s_raw.get("height", 0),
        color_space=s_raw.get("color_space", "sRGB"),
        has_alpha=s_raw.get("has_alpha", True),
        format=s_raw.get("format", "PNG"),
    )

    # 3. Canvas Meta
    c_raw = raw.get("canvas", {})
    canvas_meta = CanvasMetaIR(
        width=c_raw.get("width", 576),
        height=c_raw.get("height", 512),
        pivot_x=c_raw.get("pivot_x", 288),
        ground_y=c_raw.get("ground_y", 460),
    )

    # 4. Views
    views: List[ViewIR] = []
    for v in raw.get("views", []):
        views.append(
            ViewIR(
                id=v.get("id", ""),
                name=v.get("name", ""),
                yaw_degrees=float(v.get("yaw_degrees", 0.0)),
                pitch_degrees=float(v.get("pitch_degrees", 0.0)),
                landmarks_2d=v.get("landmarks_2d", {}),
            )
        )

    # 5. Layers
    layers: List[LayerIR] = []
    for lyr in raw.get("layers", []):
        layers.append(
            LayerIR(
                id=lyr.get("id", ""),
                name=lyr.get("name", ""),
                semantic_role=lyr.get("semantic_role", "custom"),
                z_index=int(lyr.get("z_index", 0)),
                opacity=float(lyr.get("opacity", 1.0)),
                visible=bool(lyr.get("visible", True)),
            )
        )

    # 6. Frames
    frames: List[FrameIR] = []
    for f in raw.get("frames", []):
        frames.append(
            FrameIR(
                id=f.get("id", ""),
                animation=f.get("animation", "default"),
                index=int(f.get("index", 0)),
                duration_ms=int(f.get("duration_ms", 100)),
                canvas_rect=f.get("canvas_rect", {"x": 0, "y": 0, "w": 0, "h": 0}),
                atlas_rect=f.get("atlas_rect"),
                uv_rect=f.get("uv_rect"),
                pivot=f.get("pivot", {"x": 0.5, "y": 0.5}),
                ground_anchor=bool(f.get("ground_anchor", True)),
                delta_y=int(f.get("delta_y", 0)),
            )
        )

    # 7. Animations
    animations: List[AnimationClipIR] = []
    for anim in raw.get("animations", []):
        curves: Dict[str, AnimationCurveIR] = {}
        for c_key, c_val in anim.get("curves", {}).items():
            kfs = [
                KeyframeIR(
                    time_sec=float(k.get("time_sec", 0.0)),
                    value=float(k.get("value", 0.0)),
                    in_tangent=k.get("in_tangent"),
                    out_tangent=k.get("out_tangent"),
                    interpolation=k.get("interpolation", "linear"),
                )
                for k in c_val.get("keyframes", [])
            ]
            curves[c_key] = AnimationCurveIR(
                property=c_val.get("property", ""),
                target_id=c_val.get("target_id", ""),
                keyframes=kfs,
            )

        animations.append(
            AnimationClipIR(
                id=anim.get("id", ""),
                name=anim.get("name", ""),
                fps=int(anim.get("fps", 10)),
                loop=bool(anim.get("loop", True)),
                frame_ids=anim.get("frame_ids", []),
                curves=curves,
            )
        )

    # 8. Skeleton
    skeleton: Optional[SkeletonIR] = None
    sk_raw = raw.get("skeleton")
    if sk_raw:
        bones = []
        for b in sk_raw.get("bones", []):
            r_raw = b.get("rest", {})
            rest = BoneRestIR(
                x=float(r_raw.get("x", 0.0)),
                y=float(r_raw.get("y", 0.0)),
                rotation_rad=float(r_raw.get("rotation_rad", 0.0)),
                scale_x=float(r_raw.get("scale_x", 1.0)),
                scale_y=float(r_raw.get("scale_y", 1.0)),
            )
            bones.append(
                BoneIR(
                    id=b.get("id", ""),
                    name=b.get("name", ""),
                    parent_id=b.get("parent_id"),
                    length=float(b.get("length", 0.0)),
                    rest=rest,
                    color_hex=b.get("color_hex", "00f0ff"),
                )
            )

        constraints = []
        for c in sk_raw.get("constraints", []):
            constraints.append(
                BoneConstraintIR(
                    id=c.get("id", ""),
                    type=c.get("type", "two_bone_ik"),
                    target_bone_id=c.get("target_bone_id", ""),
                    root_bone_id=c.get("root_bone_id"),
                    mid_bone_id=c.get("mid_bone_id"),
                    pole_target=c.get("pole_target"),
                    bend_positive=bool(c.get("bend_positive", True)),
                    min_angle_rad=c.get("min_angle_rad"),
                    max_angle_rad=c.get("max_angle_rad"),
                    weight=float(c.get("weight", 1.0)),
                )
            )

        skeleton = SkeletonIR(
            root_bone_id=sk_raw.get("root_bone_id", "root"),
            bones=bones,
            constraints=constraints,
        )

    # 9. Meshes
    meshes: List[MeshIR] = []
    for m in raw.get("meshes", []):
        weights = []
        for v_weights in m.get("weights", []):
            weights.append(
                [
                    VertexWeightIR(bone_id=w.get("bone_id", ""), weight=float(w.get("weight", 0.0)))
                    for w in v_weights
                ]
            )
        meshes.append(
            MeshIR(
                id=m.get("id", ""),
                layer_id=m.get("layer_id", ""),
                vertices=m.get("vertices", []),
                triangles=m.get("triangles", []),
                uvs=m.get("uvs", []),
                weights=weights,
            )
        )

    # 10. Colliders
    colliders: List[ColliderIR] = []
    for col in raw.get("colliders", []):
        colliders.append(
            ColliderIR(
                id=col.get("id", ""),
                name=col.get("name", ""),
                type=col.get("type", "hitbox"),
                shape=col.get("shape", "box"),
                offset=col.get("offset", {"x": 0.0, "y": 0.0}),
                size=col.get("size", {"w": 0.0, "h": 0.0}),
                radius=col.get("radius"),
                points=col.get("points"),
                attached_bone_id=col.get("attached_bone_id"),
            )
        )

    # 11. Materials
    materials: Optional[MaterialIR] = None
    mat_raw = raw.get("materials")
    if mat_raw:
        materials = MaterialIR(
            diffuse_map=mat_raw.get("diffuse_map", ""),
            normal_map=mat_raw.get("normal_map"),
            emission_map=mat_raw.get("emission_map"),
            height_map=mat_raw.get("height_map"),
            normal_strength=float(mat_raw.get("normal_strength", 2.5)),
            bloom_emission=bool(mat_raw.get("bloom_emission", True)),
            lum_threshold=float(mat_raw.get("lum_threshold", 140.0)),
            sat_threshold=float(mat_raw.get("sat_threshold", 0.25)),
        )

    # 12. Atlas
    atlas: Optional[AtlasIR] = None
    atl_raw = raw.get("atlas")
    if atl_raw:
        atlas = AtlasIR(
            image_path=atl_raw.get("image_path", ""),
            width=int(atl_raw.get("width", 2048)),
            height=int(atl_raw.get("height", 2048)),
            padding=int(atl_raw.get("padding", 2)),
            power_of_two=bool(atl_raw.get("power_of_two", True)),
            occupancy_ratio=float(atl_raw.get("occupancy_ratio", 0.0)),
            wasted_pixels=int(atl_raw.get("wasted_pixels", 0)),
        )

    # 13. Diagnostics
    diagnostics: List[DiagnosticIR] = []
    for d in raw.get("diagnostics", []):
        diagnostics.append(
            DiagnosticIR(
                severity=d.get("severity", "info"),
                code=d.get("code", ""),
                message=d.get("message", ""),
                asset_id=d.get("asset_id"),
                object_id=d.get("object_id"),
                location=d.get("location"),
                suggested_fix=d.get("suggested_fix"),
            )
        )

    # 14. Provenance
    provenance: Optional[ProvenanceIR] = None
    p_raw = raw.get("provenance")
    if p_raw:
        provenance = ProvenanceIR(
            generator=p_raw.get("generator", "img2game2d"),
            version=p_raw.get("version", "3.0.0"),
            timestamp_utc=p_raw.get("timestamp_utc", ""),
            pipeline_stages=p_raw.get("pipeline_stages", []),
            parameters=p_raw.get("parameters", {}),
        )

    return AssetIR(
        schema_version=schema_version,
        asset=asset_meta,
        source=source_meta,
        canvas=canvas_meta,
        views=views,
        layers=layers,
        frames=frames,
        animations=animations,
        skeleton=skeleton,
        meshes=meshes,
        colliders=colliders,
        materials=materials,
        atlas=atlas,
        diagnostics=diagnostics,
        provenance=provenance,
    )
