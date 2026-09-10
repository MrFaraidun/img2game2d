"""
Converts legacy character metadata and TexturePacker atlases into canonical AssetIR v3.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import (
    AnimationClipIR,
    AssetIR,
    AssetMetaIR,
    AtlasIR,
    BoneIR,
    BoneRestIR,
    CanvasMetaIR,
    ColliderIR,
    DiagnosticIR,
    FrameIR,
    MaterialIR,
    ProvenanceIR,
    SkeletonIR,
    SourceMetaIR,
)


def convert_legacy_character_to_asset_ir(
    char_dir: Path | str,
    project_root: Optional[Path | str] = None,
) -> AssetIR:
    """
    Ingests legacy character directory containing:
    - metadata/character.json
    - atlases/<char_id>_atlas.json
    - atlases/<char_id>_atlas.png
    and converts it into canonical AssetIR v3.
    """
    c_dir = Path(char_dir)
    char_id = c_dir.name

    meta_file = c_dir / "metadata" / "character.json"
    if not meta_file.exists():
        raise FileNotFoundError(f"Missing character metadata: {meta_file}")

    with open(meta_file, "r", encoding="utf-8") as f:
        char_meta = json.load(f)

    # 1. Canvas & Pivot
    c_size = char_meta.get("canvas_size", {})
    canvas_w = int(c_size.get("width", 576))
    canvas_h = int(c_size.get("height", 512))
    p_pt = char_meta.get("pivot", {})
    pivot_x = int(p_pt.get("x", 288))
    ground_y = int(p_pt.get("y", 460))

    canvas_meta = CanvasMetaIR(
        width=canvas_w,
        height=canvas_h,
        pivot_x=pivot_x,
        ground_y=ground_y,
    )

    # 2. Atlas Data
    atlas_json_file = c_dir / "atlases" / f"{char_id}_atlas.json"
    atlas_ir: Optional[AtlasIR] = None
    frames_dict: Dict[str, Any] = {}

    if atlas_json_file.exists():
        with open(atlas_json_file, "r", encoding="utf-8") as f:
            atlas_raw = json.load(f)
        frames_dict = atlas_raw.get("frames", {})
        meta_raw = atlas_raw.get("meta", {})
        size_raw = meta_raw.get("size", {})
        atlas_w = int(size_raw.get("w", 2048))
        atlas_h = int(size_raw.get("h", 2048))

        # Calculate occupancy
        total_frame_area = sum(
            f_info.get("frame", {}).get("w", 0) * f_info.get("frame", {}).get("h", 0)
            for f_info in frames_dict.values()
        )
        atlas_area = atlas_w * atlas_h
        occupancy = total_frame_area / atlas_area if atlas_area > 0 else 0.0

        atlas_ir = AtlasIR(
            image_path=meta_raw.get("image", f"{char_id}_atlas.png"),
            width=atlas_w,
            height=atlas_h,
            padding=2,
            power_of_two=True,
            occupancy_ratio=round(occupancy, 4),
            wasted_pixels=max(0, atlas_area - total_frame_area),
        )

    # 3. Frames
    frames: List[FrameIR] = []
    anim_clips_map: Dict[str, AnimationClipIR] = {}

    anims_meta = char_meta.get("animations", {})
    for anim_name, anim_data in anims_meta.items():
        fps = int(anim_data.get("fps", 10))
        loop = bool(anim_data.get("loop", True))
        frame_ids: List[str] = []

        for rel_frame_path in anim_data.get("frames", []):
            # rel_frame_path looks like 'run/000.png'
            # In atlas, key is 'run_00.png'
            stem = Path(rel_frame_path).stem  # '000'
            try:
                frame_idx = int(stem)
            except ValueError:
                frame_idx = 0

            atlas_key = f"{anim_name}_{frame_idx:02d}.png"
            f_info = frames_dict.get(atlas_key, {})

            f_rect = f_info.get("frame", {})
            sss = f_info.get("spriteSourceSize", {})
            pivot_info = f_info.get("pivot", {"x": pivot_x / canvas_w, "y": ground_y / canvas_h})

            cw = sss.get("w", f_rect.get("w", 100))
            ch = sss.get("h", f_rect.get("h", 100))
            cx = sss.get("x", pivot_x - cw // 2)
            cy = sss.get("y", ground_y - ch)

            frame_id = f"{char_id}_{anim_name}_{frame_idx:02d}"
            frame_ids.append(frame_id)

            # Calculate normalized UV
            uv_rect = None
            if atlas_ir and f_rect:
                u0 = f_rect.get("x", 0) / atlas_ir.width
                v0 = f_rect.get("y", 0) / atlas_ir.height
                u1 = (f_rect.get("x", 0) + f_rect.get("w", 0)) / atlas_ir.width
                v1 = (f_rect.get("y", 0) + f_rect.get("h", 0)) / atlas_ir.height
                uv_rect = {"u0": round(u0, 6), "v0": round(v0, 6), "u1": round(u1, 6), "v1": round(v1, 6)}

            # Check if config has ground_anchor and delta_y
            is_ground_anchor = True
            delta_y = 0
            try:
                import sys
                forge_dir = c_dir.parent.parent / "forge"
                if str(forge_dir) not in sys.path:
                    sys.path.insert(0, str(forge_dir))
                import pipeline
                if char_id in pipeline.CHARACTER_CONFIGS:
                    for cf in pipeline.CHARACTER_CONFIGS[char_id].get("frames", []):
                        if cf.get("anim") == anim_name and cf.get("idx") == frame_idx:
                            is_ground_anchor = cf.get("ground_anchor", True)
                            delta_y = cf.get("delta_y", 0)
                            break
            except Exception:
                pass

            frame_ir = FrameIR(
                id=frame_id,
                animation=anim_name,
                index=frame_idx,
                duration_ms=int(round(1000.0 / fps)) if fps > 0 else 100,
                canvas_rect={"x": cx, "y": cy, "w": cw, "h": ch},
                atlas_rect={"x": f_rect.get("x", 0), "y": f_rect.get("y", 0), "w": f_rect.get("w", 0), "h": f_rect.get("h", 0)} if f_rect else None,
                uv_rect=uv_rect,
                pivot={"x": round(pivot_info.get("x", 0.5), 4), "y": round(pivot_info.get("y", 0.9), 4)},
                ground_anchor=is_ground_anchor,
                delta_y=delta_y,
            )
            frames.append(frame_ir)

        anim_clips_map[anim_name] = AnimationClipIR(
            id=f"{char_id}_{anim_name}",
            name=anim_name,
            fps=fps,
            loop=loop,
            frame_ids=frame_ids,
        )

    # 4. Hitbox Collider
    colliders: List[ColliderIR] = []
    hb = char_meta.get("hitbox")
    if hb:
        colliders.append(
            ColliderIR(
                id=f"{char_id}_hitbox",
                name="hitbox_main",
                type="hitbox",
                shape="box",
                offset={"x": float(hb.get("offset_x", 0)), "y": float(hb.get("offset_y", 0))},
                size={"w": float(hb.get("width", 60)), "h": float(hb.get("height", 180))},
            )
        )

    # 5. Materials
    materials = MaterialIR(
        diffuse_map=f"{char_id}_atlas.png",
        normal_map=f"{char_id}_atlas_normal.png",
        emission_map=f"{char_id}_atlas_emission.png",
        normal_strength=2.5,
        bloom_emission=True,
        lum_threshold=140.0,
        sat_threshold=0.25,
    )

    # 6. Skeleton (from Spine export if exists)
    skeleton: Optional[SkeletonIR] = None
    root_dir = Path(project_root) if project_root else c_dir.parent.parent
    spine_file = root_dir / "exports" / "spine" / char_id / f"{char_id}_skeleton.json"

    if spine_file.exists():
        try:
            with open(spine_file, "r", encoding="utf-8") as f:
                sp_data = json.load(f)
            bones_list: List[BoneIR] = []
            for b in sp_data.get("bones", []):
                bones_list.append(
                    BoneIR(
                        id=b.get("name", ""),
                        name=b.get("name", ""),
                        parent_id=b.get("parent"),
                        length=float(b.get("length", 0.0)),
                        rest=BoneRestIR(
                            x=float(b.get("x", 0.0)),
                            y=float(b.get("y", 0.0)),
                            rotation_rad=float(b.get("rotation", 0.0)) * 3.14159265 / 180.0,
                            scale_x=float(b.get("scaleX", 1.0)),
                            scale_y=float(b.get("scaleY", 1.0)),
                        ),
                        color_hex=b.get("color", "00f0ff"),
                    )
                )
            skeleton = SkeletonIR(root_bone_id="root", bones=bones_list)
        except Exception:
            skeleton = None

    # 7. Metadata & Provenance
    provenance = ProvenanceIR(
        generator="img2game2d",
        version="3.0.0",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        pipeline_stages=["legacy_ingest", "dematting", "atlas_packing", "asset_ir_conversion"],
        parameters={"source_char_id": char_id},
    )

    return AssetIR(
        schema_version="3.0.0",
        asset=AssetMetaIR(
            id=char_id,
            name=char_meta.get("name", char_id),
            source_hash=f"sha256_{char_id}",
            tags=[char_meta.get("title", "")],
        ),
        source=SourceMetaIR(
            width=canvas_w,
            height=canvas_h,
            color_space="sRGB",
            has_alpha=True,
            format="PNG",
        ),
        canvas=canvas_meta,
        views=[],
        layers=[],
        frames=frames,
        animations=list(anim_clips_map.values()),
        skeleton=skeleton,
        meshes=[],
        colliders=colliders,
        materials=materials,
        atlas=atlas_ir,
        diagnostics=[],
        provenance=provenance,
    )
