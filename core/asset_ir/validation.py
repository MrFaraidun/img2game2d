"""
Validation engine for img2game2d AssetIR.
Produces structured, actionable DiagnosticIR reports.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Set

from .types import (
    AssetIR,
    AtlasIR,
    BoneIR,
    CanvasMetaIR,
    ColliderIR,
    DiagnosticIR,
    FrameIR,
    MaterialIR,
    MeshIR,
    SkeletonIR,
)


def validate_asset_ir(asset: AssetIR) -> List[DiagnosticIR]:
    """Runs all structural and semantic validators on an AssetIR document."""
    diagnostics: List[DiagnosticIR] = []

    # 1. Schema version check
    if not asset.schema_version.startswith("3."):
        diagnostics.append(
            DiagnosticIR(
                severity="error",
                code="INVALID_SCHEMA_VERSION",
                message=f"Unsupported schema version '{asset.schema_version}', expected '3.x.x'",
                suggested_fix="Upgrade asset using versioning migration helper.",
            )
        )

    # 2. Frames and animations validation
    diagnostics.extend(validate_frames(asset.frames, asset.canvas))

    frame_ids = {f.id for f in asset.frames}
    for anim in asset.animations:
        if not anim.frame_ids:
            diagnostics.append(
                DiagnosticIR(
                    severity="warning",
                    code="EMPTY_ANIMATION",
                    message=f"Animation '{anim.name}' has 0 frames.",
                    object_id=anim.id,
                    suggested_fix="Add at least one frame to the animation sequence.",
                )
            )
        for f_id in anim.frame_ids:
            if f_id not in frame_ids:
                diagnostics.append(
                    DiagnosticIR(
                        severity="error",
                        code="DANGLING_FRAME_REF",
                        message=f"Animation '{anim.name}' references non-existent frame '{f_id}'.",
                        object_id=anim.id,
                        suggested_fix="Ensure frame is defined in asset frames list.",
                    )
                )

    # 3. Skeleton validation
    if asset.skeleton:
        diagnostics.extend(validate_skeleton(asset.skeleton))

    # 4. Atlas validation
    if asset.atlas:
        diagnostics.extend(validate_atlas(asset.atlas, asset.frames))

    # 5. Mesh validation
    if asset.meshes:
        diagnostics.extend(validate_mesh(asset.meshes, asset.skeleton))

    # 6. Colliders validation
    if asset.colliders:
        diagnostics.extend(validate_colliders(asset.colliders))

    # 7. Materials validation
    if asset.materials:
        diagnostics.extend(validate_materials(asset.materials))

    return diagnostics


def validate_frames(frames: List[FrameIR], canvas: CanvasMetaIR) -> List[DiagnosticIR]:
    """Validates frame bounds, pivots, and ground drift."""
    diagnostics: List[DiagnosticIR] = []

    # Track ground drift across frames in same animation
    anim_ground_y: Dict[str, List[Tuple[int, int]]] = {}

    for f in frames:
        rect = f.canvas_rect
        w = rect.get("w", 0)
        h = rect.get("h", 0)
        x = rect.get("x", 0)
        y = rect.get("y", 0)

        if w <= 0 or h <= 0:
            diagnostics.append(
                DiagnosticIR(
                    severity="error",
                    code="EMPTY_FRAME",
                    message=f"Frame '{f.id}' has zero or negative dimension: {w}x{h}.",
                    object_id=f.id,
                    location={"x": x, "y": y, "frame": f.index},
                    suggested_fix="Adjust crop boundaries to encompass sprite pixels.",
                )
            )

        # Pivot validation: normalized pivot should generally be within [0, 1]
        px = f.pivot.get("x", 0.5)
        py = f.pivot.get("y", 0.5)
        if px < -0.5 or px > 1.5 or py < -0.5 or py > 1.5:
            diagnostics.append(
                DiagnosticIR(
                    severity="error",
                    code="INVALID_PIVOT",
                    message=f"Frame '{f.id}' has extreme pivot ({px:.2f}, {py:.2f}).",
                    object_id=f.id,
                    suggested_fix="Normalize pivot to standard range around center/ground.",
                )
            )

        # UV coordinates validation
        if f.uv_rect:
            u0 = f.uv_rect.get("u0", 0.0)
            v0 = f.uv_rect.get("v0", 0.0)
            u1 = f.uv_rect.get("u1", 0.0)
            v1 = f.uv_rect.get("v1", 0.0)
            if min(u0, v0, u1, v1) < 0.0 or max(u0, v0, u1, v1) > 1.0001:
                diagnostics.append(
                    DiagnosticIR(
                        severity="error",
                        code="UV_OUT_OF_RANGE",
                        message=f"Frame '{f.id}' UVs outside [0..1] range: ({u0:.3f}, {v0:.3f}) - ({u1:.3f}, {v1:.3f}).",
                        object_id=f.id,
                        suggested_fix="Recompute UVs after atlas packing.",
                    )
                )

        # Check ground drift if ground anchored
        if f.ground_anchor:
            bottom_y = y + h
            drift = abs(bottom_y - canvas.ground_y)
            if drift > 8:
                diagnostics.append(
                    DiagnosticIR(
                        severity="warning",
                        code="GROUND_DRIFT",
                        message=f"Frame '{f.id}' bottom Y ({bottom_y}) drifts by {drift}px from ground baseline ({canvas.ground_y}).",
                        object_id=f.id,
                        location={"x": x, "y": y, "frame": f.index},
                        suggested_fix="Align frame baseline to ground_y or adjust delta_y.",
                    )
                )

    return diagnostics


def validate_skeleton(skeleton: SkeletonIR) -> List[DiagnosticIR]:
    """Validates bone hierarchy, cycles, and parent references."""
    diagnostics: List[DiagnosticIR] = []
    bone_ids = {b.id for b in skeleton.bones}

    if skeleton.root_bone_id not in bone_ids:
        diagnostics.append(
            DiagnosticIR(
                severity="error",
                code="MISSING_PARENT_BONE",
                message=f"Root bone ID '{skeleton.root_bone_id}' does not exist in skeleton bones.",
                object_id=skeleton.root_bone_id,
                suggested_fix="Assign root_bone_id to an existing root bone.",
            )
        )

    # Check parent references
    for b in skeleton.bones:
        if b.parent_id is not None and b.parent_id not in bone_ids:
            diagnostics.append(
                DiagnosticIR(
                    severity="error",
                    code="MISSING_PARENT_BONE",
                    message=f"Bone '{b.name}' ({b.id}) references missing parent '{b.parent_id}'.",
                    object_id=b.id,
                    suggested_fix="Set parent_id to a valid bone ID or None for root.",
                )
            )

    # Check for cycles
    visited: Set[str] = set()
    in_stack: Set[str] = set()

    bone_map: Dict[str, BoneIR] = {b.id: b for b in skeleton.bones}

    def has_cycle(bone_id: str) -> bool:
        visited.add(bone_id)
        in_stack.add(bone_id)
        bone = bone_map.get(bone_id)
        if bone and bone.parent_id:
            parent = bone.parent_id
            if parent in bone_map:
                if parent not in visited:
                    if has_cycle(parent):
                        return True
                elif parent in in_stack:
                    return True
        in_stack.remove(bone_id)
        return False

    for b in skeleton.bones:
        if b.id not in visited:
            if has_cycle(b.id):
                diagnostics.append(
                    DiagnosticIR(
                        severity="error",
                        code="BONE_CYCLE_DETECTED",
                        message=f"Circular dependency detected in bone hierarchy involving '{b.name}'.",
                        object_id=b.id,
                        suggested_fix="Re-parent bone to eliminate cycle.",
                    )
                )
                break

    return diagnostics


def validate_atlas(atlas: AtlasIR, frames: List[FrameIR]) -> List[DiagnosticIR]:
    """Validates atlas dimensions, POT compliance, and frame rect overlaps."""
    diagnostics: List[DiagnosticIR] = []

    if atlas.width <= 0 or atlas.height <= 0:
        diagnostics.append(
            DiagnosticIR(
                severity="error",
                code="INVALID_ATLAS_DIMENSIONS",
                message=f"Invalid atlas dimensions: {atlas.width}x{atlas.height}",
                suggested_fix="Set atlas width and height to positive integers.",
            )
        )
        return diagnostics

    if atlas.power_of_two:
        w_pot = (atlas.width & (atlas.width - 1)) == 0
        h_pot = (atlas.height & (atlas.height - 1)) == 0
        if not (w_pot and h_pot):
            diagnostics.append(
                DiagnosticIR(
                    severity="warning",
                    code="NON_POT_ATLAS",
                    message=f"Atlas dimensions ({atlas.width}x{atlas.height}) are not Power-of-Two.",
                    suggested_fix="Resize atlas to 1024x1024, 2048x2048, or 4096x4096.",
                )
            )

    # Check for overlapping atlas rectangles among frames
    atlas_frames = [f for f in frames if f.atlas_rect is not None]
    for i in range(len(atlas_frames)):
        f1 = atlas_frames[i]
        r1 = f1.atlas_rect
        if not r1:
            continue
        for j in range(i + 1, len(atlas_frames)):
            f2 = atlas_frames[j]
            r2 = f2.atlas_rect
            if not r2:
                continue

            # Check AABB collision
            x_overlap = (r1["x"] < r2["x"] + r2["w"]) and (r1["x"] + r1["w"] > r2["x"])
            y_overlap = (r1["y"] < r2["y"] + r2["h"]) and (r1["y"] + r1["h"] > r2["y"])

            if x_overlap and y_overlap:
                diagnostics.append(
                    DiagnosticIR(
                        severity="error",
                        code="ATLAS_OVERLAP",
                        message=f"Atlas frames '{f1.id}' and '{f2.id}' overlap in texture bounds.",
                        object_id=f1.id,
                        suggested_fix="Re-pack atlas with increased dimensions or shelf bin-packing.",
                    )
                )

    return diagnostics


def validate_mesh(meshes: List[MeshIR], skeleton: Optional[SkeletonIR]) -> List[DiagnosticIR]:
    """Validates vertex weight normalization sum(w) == 1.0 and triangle index integrity."""
    diagnostics: List[DiagnosticIR] = []
    bone_ids = {b.id for b in skeleton.bones} if skeleton else set()

    for mesh in meshes:
        v_count = len(mesh.vertices) // 2
        for tri_idx in mesh.triangles:
            if tri_idx < 0 or tri_idx >= v_count:
                diagnostics.append(
                    DiagnosticIR(
                        severity="error",
                        code="DEGENERATE_TRIANGLE_INDEX",
                        message=f"Mesh '{mesh.id}' contains out-of-range triangle index {tri_idx} (vertex count: {v_count}).",
                        object_id=mesh.id,
                        suggested_fix="Re-triangulate mesh boundary.",
                    )
                )
                break

        # Validate bone weights normalization
        for v_i, weights in enumerate(mesh.weights):
            total_w = sum(w.weight for w in weights)
            if abs(total_w - 1.0) > 1e-3:
                diagnostics.append(
                    DiagnosticIR(
                        severity="error",
                        code="WEIGHT_SUM_INVALID",
                        message=f"Mesh '{mesh.id}' vertex {v_i} weights sum to {total_w:.4f}, expected 1.0.",
                        object_id=mesh.id,
                        suggested_fix="Normalize vertex weight vectors so sum equals 1.0.",
                    )
                )
            if skeleton:
                for w in weights:
                    if w.bone_id not in bone_ids:
                        diagnostics.append(
                            DiagnosticIR(
                                severity="error",
                                code="UNKNOWN_BONE_WEIGHT",
                                message=f"Mesh '{mesh.id}' references unknown bone '{w.bone_id}'.",
                                object_id=mesh.id,
                                suggested_fix="Ensure weighted bone exists in skeleton.",
                            )
                        )

    return diagnostics


def validate_colliders(colliders: List[ColliderIR]) -> List[DiagnosticIR]:
    """Validates hitbox and collision bounds."""
    diagnostics: List[DiagnosticIR] = []
    for c in colliders:
        w = c.size.get("w", 0)
        h = c.size.get("h", 0)
        if w <= 0 or h <= 0:
            diagnostics.append(
                DiagnosticIR(
                    severity="error",
                    code="INVALID_COLLIDER_SIZE",
                    message=f"Collider '{c.name}' has invalid dimensions: {w}x{h}.",
                    object_id=c.id,
                    suggested_fix="Provide positive width and height for collider box.",
                )
            )
    return diagnostics


def validate_materials(material: MaterialIR) -> List[DiagnosticIR]:
    """Validates material maps and shader parameters."""
    diagnostics: List[DiagnosticIR] = []
    if not material.diffuse_map:
        diagnostics.append(
            DiagnosticIR(
                severity="error",
                code="MISSING_DIFFUSE_MAP",
                message="Material missing required diffuse_map texture reference.",
                suggested_fix="Specify valid path to diffuse texture atlas.",
            )
        )
    return diagnostics
