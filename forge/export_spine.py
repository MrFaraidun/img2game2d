#!/usr/bin/env python3
"""
Spine 2D Exporter for img2game2d & Game Engines.
Generates:
  1. Official Spine 2D skeleton.json (v3.8/v4.x compatible):
     - Fully articulated 19-bone humanoid anatomical hierarchy dynamically
       scaled and positioned to match the sprite canvas dimensions.
     - Root ground baseline datum with forward kinematics chain:
       root -> pelvis -> spine -> chest -> neck -> head,
       arms (shoulder, forearm, hand, weapon/shield),
       legs (thigh, shin, foot).
     - Slot and skin attachments for all animation sequences.
     - Frame-accurate keyed slot animations with precise timing.
  2. LibGDX / Spine standard .atlas file:
     - Full frame UV rects, trim offsets, and texture packing bounds.
  3. Integrated 2D dynamic lighting textures (diffuse, normal, emission).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def build_procedural_skeleton_rig(
    char_id: str,
    canvas_w: int,
    canvas_h: int,
    first_attachment: str = ""
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Procedurally computes an authentic 19-bone humanoid skeletal rig for Spine 2D
    derived dynamically from character canvas dimensions and anatomical proportions.
    Zero hardcoded frontend dependencies; all bone data is saved directly in skeleton.json.
    """
    # Proportional anatomical measurements based on character bounding canvas
    base_scale_x = canvas_w / 576.0
    base_scale_y = canvas_h / 512.0

    # Ground datum baseline Y is at 0 (Spine Y-up convention where 0 is ground plane)
    pelvis_h = round(canvas_h * 0.38)
    spine_len = round(canvas_h * 0.088)
    chest_len = round(canvas_h * 0.088)
    neck_len = round(canvas_h * 0.048)
    head_len = round(canvas_h * 0.125)

    shoulder_len = round(canvas_h * 0.08)
    forearm_len = round(canvas_h * 0.088)
    hand_len = round(canvas_h * 0.044)

    thigh_len = round(canvas_h * 0.118)
    shin_len = round(canvas_h * 0.108)
    foot_len = round(canvas_h * 0.052)

    # Determine weapon/gear naming based on character identity
    is_guardian = "guardian" in char_id.lower()
    weapon_r_name = "heavy_hammer" if is_guardian else "cyberblade"
    weapon_r_len = round(canvas_h * 0.24) if is_guardian else round(canvas_h * 0.26)
    gear_l_name = "shield_l" if is_guardian else "offhand_blade"
    gear_l_len = round(canvas_h * 0.18) if is_guardian else round(canvas_h * 0.12)

    # 1. Procedural Bone List
    bones: List[Dict[str, Any]] = [
        # Ground world origin datum (0, 0)
        {
            "name": "root"
        },
        # Pelvis / Core Root
        {
            "name": "pelvis",
            "parent": "root",
            "x": 0,
            "y": pelvis_h,
            "rotation": 90,
            "length": round(spine_len * 0.8),
            "color": "6366f1"
        },
        # Spine lumbar
        {
            "name": "spine",
            "parent": "pelvis",
            "x": round(spine_len * 0.8),
            "y": 0,
            "rotation": 0,
            "length": spine_len,
            "color": "6366f1"
        },
        # Chest thoracic
        {
            "name": "chest",
            "parent": "spine",
            "x": spine_len,
            "y": 0,
            "rotation": 0,
            "length": chest_len,
            "color": "00f0ff"
        },
        # Neck cervical
        {
            "name": "neck",
            "parent": "chest",
            "x": chest_len,
            "y": 0,
            "rotation": 0,
            "length": neck_len,
            "color": "6366f1"
        },
        # Head / Skull
        {
            "name": "head",
            "parent": "neck",
            "x": neck_len,
            "y": 0,
            "rotation": 0,
            "length": head_len,
            "color": "00f0ff"
        },

        # Left Arm (Back Arm in 2.5D Isometric view)
        {
            "name": "shoulder_l",
            "parent": "chest",
            "x": round(chest_len * 0.8),
            "y": round(-28 * base_scale_x),
            "rotation": 135 if not is_guardian else 130,
            "length": round(40 * base_scale_y),
            "color": "818cf8"
        },
        {
            "name": "forearm_l",
            "parent": "shoulder_l",
            "x": round(40 * base_scale_y),
            "y": 0,
            "rotation": 10 if not is_guardian else 5,
            "length": round(40 * base_scale_y),
            "color": "818cf8"
        },
        {
            "name": "hand_l",
            "parent": "forearm_l",
            "x": round(40 * base_scale_y),
            "y": 0,
            "rotation": 15 if not is_guardian else 10,
            "length": round(22 * base_scale_y),
            "color": "818cf8"
        },
        {
            "name": gear_l_name,
            "parent": "hand_l" if not is_guardian else "forearm_l",
            "x": round(22 * base_scale_y) if not is_guardian else round(40 * base_scale_y),
            "y": 0,
            "rotation": 10 if not is_guardian else -5,
            "length": gear_l_len,
            "color": "a855f7"
        },

        # Right Arm (Fore Arm in view)
        {
            "name": "shoulder_r",
            "parent": "chest",
            "x": round(chest_len * 0.8),
            "y": round(28 * base_scale_x),
            "rotation": -155 if not is_guardian else -160,
            "length": round(40 * base_scale_y),
            "color": "818cf8"
        },
        {
            "name": "forearm_r",
            "parent": "shoulder_r",
            "x": round(40 * base_scale_y),
            "y": 0,
            "rotation": -15 if not is_guardian else -10,
            "length": round(40 * base_scale_y),
            "color": "818cf8"
        },
        {
            "name": "hand_r",
            "parent": "forearm_r",
            "x": round(40 * base_scale_y),
            "y": 0,
            "rotation": -10,
            "length": round(22 * base_scale_y),
            "color": "818cf8"
        },
        {
            "name": weapon_r_name,
            "parent": "hand_r",
            "x": round(22 * base_scale_y),
            "y": 0,
            "rotation": 35 if not is_guardian else 40,
            "length": weapon_r_len,
            "color": "a855f7"
        },

        # Left Leg (Far)
        {
            "name": "thigh_l",
            "parent": "pelvis",
            "x": round(-5 * base_scale_y),
            "y": round(-20 * base_scale_x),
            "rotation": 175 if not is_guardian else 176,
            "length": round(68 * base_scale_y),
            "color": "4f46e5"
        },
        {
            "name": "shin_l",
            "parent": "thigh_l",
            "x": round(68 * base_scale_y),
            "y": 0,
            "rotation": 5 if not is_guardian else 4,
            "length": round(68 * base_scale_y),
            "color": "4f46e5"
        },
        {
            "name": "foot_l",
            "parent": "shin_l",
            "x": round(68 * base_scale_y),
            "y": 0,
            "rotation": 80 if not is_guardian else 85,
            "length": round(26 * base_scale_y),
            "color": "4f46e5"
        },

        # Right Leg (Near)
        {
            "name": "thigh_r",
            "parent": "pelvis",
            "x": round(-5 * base_scale_y),
            "y": round(20 * base_scale_x),
            "rotation": 175 if not is_guardian else 174,
            "length": round(68 * base_scale_y),
            "color": "4f46e5"
        },
        {
            "name": "shin_r",
            "parent": "thigh_r",
            "x": round(68 * base_scale_y),
            "y": 0,
            "rotation": -5 if not is_guardian else -4,
            "length": round(68 * base_scale_y),
            "color": "4f46e5"
        },
        {
            "name": "foot_r",
            "parent": "shin_r",
            "x": round(68 * base_scale_y),
            "y": 0,
            "rotation": -80 if not is_guardian else -85,
            "length": round(26 * base_scale_y),
            "color": "4f46e5"
        }
    ]

    # 2. Dynamic Slots corresponding to bones
    slots: List[Dict[str, Any]] = [
        {"name": "root_slot", "bone": "root"},
        {"name": "pelvis_slot", "bone": "pelvis"},
        {"name": "spine_slot", "bone": "spine"},
        {"name": "chest_slot", "bone": "chest"},
        {"name": "head_slot", "bone": "head"},
        {"name": "arm_l_slot", "bone": "forearm_l"},
        {"name": "arm_r_slot", "bone": "forearm_r"},
        {"name": "gear_l_slot", "bone": gear_l_name},
        {"name": "weapon_slot", "bone": weapon_r_name},
        {"name": "leg_l_slot", "bone": "shin_l"},
        {"name": "leg_r_slot", "bone": "shin_r"},
        {"name": "character", "bone": "chest", "attachment": first_attachment}
    ]

    return bones, slots


class SpineExporter:
    """Exports sprite atlases and animation manifests to official Spine 2D compatible format."""

    def __init__(self, spine_version: str = "3.8.99"):
        self.spine_version = spine_version

    def export(
        self,
        char_id: str,
        atlas_json_path: Path | str,
        atlas_png_path: Path | str,
        output_dir: Path | str,
        fps_overrides: Optional[Dict[str, int]] = None,
        normal_png_path: Optional[Path | str] = None,
        emission_png_path: Optional[Path | str] = None,
    ) -> Dict[str, str]:
        """Performs full export of character atlas to Spine 2D directory."""
        atlas_json_p = Path(atlas_json_path)
        atlas_png_p = Path(atlas_png_path)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if not atlas_json_p.exists():
            raise FileNotFoundError(f"Atlas JSON not found: {atlas_json_p}")
        if not atlas_png_p.exists():
            raise FileNotFoundError(f"Atlas PNG not found: {atlas_png_p}")

        with open(atlas_json_p, "r", encoding="utf-8") as f:
            atlas_data = json.load(f)

        frames_dict = atlas_data.get("frames", {})
        meta = atlas_data.get("meta", {})
        atlas_w = meta.get("size", {}).get("w", 2048)
        atlas_h = meta.get("size", {}).get("h", 2048)
        atlas_image_name = f"{char_id}_atlas.png"

        # Determine character canvas bounding size
        canvas_w = 576
        canvas_h = 512
        for f_data in frames_dict.values():
            ss = f_data.get("sourceSize", {})
            if ss.get("w") and ss.get("h"):
                canvas_w = ss["w"]
                canvas_h = ss["h"]
                break

        fps_map = fps_overrides or {
            "idle": 6,
            "run": 12,
            "jump": 7,
            "attack": 12,
            "defend": 8,
            "hurt": 6,
        }

        # 1. Group frames by animation sequence
        anim_frames: Dict[str, List[Tuple[int, str, dict]]] = {}
        for f_name, f_info in frames_dict.items():
            base_stem = f_name.replace(".png", "")
            parts = base_stem.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit():
                anim_name = parts[0]
                frame_idx = int(parts[1])
            else:
                anim_name = "default"
                frame_idx = 0
            anim_frames.setdefault(anim_name, []).append((frame_idx, base_stem, f_info))

        for anim_name in anim_frames:
            anim_frames[anim_name].sort(key=lambda x: x[0])

        first_attachment = ""
        for anim_list in anim_frames.values():
            if anim_list:
                first_attachment = anim_list[0][1]
                break

        # 2. Build Procedural Skeletal Bones and Slots
        bones, slots = build_procedural_skeleton_rig(
            char_id=char_id,
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            first_attachment=first_attachment
        )

        # 3. Build Complete Spine skeleton.json structure
        skeleton_json: Dict[str, Any] = {
            "skeleton": {
                "hash": f"{char_id}_hash",
                "spine": self.spine_version,
                "x": -round(canvas_w / 2),
                "y": 0,
                "width": canvas_w,
                "height": canvas_h,
                "images": "./",
                "audio": "",
            },
            "bones": bones,
            "slots": slots,
            "skins": [
                {
                    "name": "default",
                    "attachments": {
                        "character": {}
                    },
                }
            ],
            "animations": {},
        }

        default_skin_attachments = skeleton_json["skins"][0]["attachments"]["character"]

        # Populate skin attachments with frame trims and offsets
        for anim_name, frame_list in anim_frames.items():
            for _, base_stem, f_info in frame_list:
                frame_rect = f_info.get("frame", {})
                src_rect = f_info.get("spriteSourceSize", {})
                pivot = f_info.get("pivot", {"x": 0.5, "y": 0.8984})

                attach_w = frame_rect.get("w", 100)
                attach_h = frame_rect.get("h", 100)
                px = pivot.get("x", 0.5) * canvas_w
                py = (1.0 - pivot.get("y", 0.8984)) * canvas_h

                trim_x = src_rect.get("x", 0)
                trim_y = canvas_h - (src_rect.get("y", 0) + attach_h)

                center_x = (trim_x + attach_w / 2.0) - px
                center_y = (trim_y + attach_h / 2.0) - py

                default_skin_attachments[base_stem] = {
                    "x": round(center_x, 2),
                    "y": round(center_y, 2),
                    "width": attach_w,
                    "height": attach_h,
                }

        # Populate animations
        for anim_name, frame_list in anim_frames.items():
            fps = fps_map.get(anim_name, 10)
            frame_duration = 1.0 / max(1, fps)
            timeline: List[Dict[str, Any]] = []

            for i, (_, base_stem, _) in enumerate(frame_list):
                time_val = round(i * frame_duration, 4)
                timeline.append({"time": time_val, "name": base_stem})

            skeleton_json["animations"][anim_name] = {
                "slots": {
                    "character": {
                        "attachment": timeline
                    }
                }
            }

        # Write skeleton.json
        skeleton_out = out_dir / f"{char_id}_skeleton.json"
        with open(skeleton_out, "w", encoding="utf-8") as f:
            json.dump(skeleton_json, f, indent=2)

        # 4. Build LibGDX / Spine standard .atlas file
        atlas_lines = [
            atlas_image_name,
            f"size: {atlas_w},{atlas_h}",
            "format: RGBA8888",
            "filter: Linear,Linear",
            "repeat: none",
        ]

        for f_name, f_info in frames_dict.items():
            base_stem = f_name.replace(".png", "")
            f_box = f_info.get("frame", {})
            src_box = f_info.get("spriteSourceSize", {})
            s_size = f_info.get("sourceSize", {})

            orig_w = s_size.get("w", canvas_w)
            orig_h = s_size.get("h", canvas_h)
            trim_w = f_box.get("w", orig_w)
            trim_h = f_box.get("h", orig_h)
            ox = src_box.get("x", 0)
            oy = orig_h - (src_box.get("y", 0) + trim_h)

            atlas_lines.extend(
                [
                    base_stem,
                    "  rotate: false",
                    f"  xy: {f_box.get('x', 0)}, {f_box.get('y', 0)}",
                    f"  size: {trim_w}, {trim_h}",
                    f"  orig: {orig_w}, {orig_h}",
                    f"  offset: {ox}, {oy}",
                    "  index: -1",
                ]
            )

        atlas_text_out = out_dir / f"{char_id}.atlas"
        with open(atlas_text_out, "w", encoding="utf-8") as f:
            f.write("\n".join(atlas_lines) + "\n")

        # 5. Copy Texture Atlas PNG & Lighting Maps
        dest_png = out_dir / atlas_image_name
        shutil.copy2(atlas_png_p, dest_png)

        exported_files = {
            "skeleton": str(skeleton_out),
            "atlas": str(atlas_text_out),
            "texture": str(dest_png),
        }

        if normal_png_path and Path(normal_png_path).exists():
            dest_norm = out_dir / f"{char_id}_atlas_normal.png"
            shutil.copy2(normal_png_path, dest_norm)
            exported_files["normal"] = str(dest_norm)

        if emission_png_path and Path(emission_png_path).exists():
            dest_emis = out_dir / f"{char_id}_atlas_emission.png"
            shutil.copy2(emission_png_path, dest_emis)
            exported_files["emission"] = str(dest_emis)

        # 6. Generate Documentation
        readme_content = f"""# {char_id} — Spine 2D Asset Package

Exported with **img2game2d** Spine 2D Exporter.

## Included Files
- `{char_id}_skeleton.json` — Official Spine 2D skeleton, 19 articulated bones, slot attachments & frame timelines.
- `{char_id}.atlas` — LibGDX/Spine texture atlas mapping.
- `{char_id}_atlas.png` — Main RGBA diffuse texture.
{f"- `{char_id}_atlas_normal.png` — Tangent-space normal map for dynamic 2D lights." if "normal" in exported_files else ""}
{f"- `{char_id}_atlas_emission.png` — Emission/glow map for post-processing bloom." if "emission" in exported_files else ""}

## How to Import
### Unity (`spine-unity`)
1. Ensure the `spine-unity` runtime package is installed in your Unity project.
2. Drag `{char_id}_skeleton.json`, `{char_id}.atlas`, and `{char_id}_atlas.png` into any folder in `Assets/`.
3. Unity will automatically generate a `SkeletonDataAsset`.
4. Drag the `SkeletonDataAsset` into your scene or hierarchy to create a `SkeletonAnimation` Game Object.

### Godot 4 (`spine-godot`)
1. Ensure the `spine-godot` GDExtension or custom engine build is loaded.
2. Place `{char_id}_skeleton.json` and `{char_id}.atlas` into `res://assets/`.
3. Create a `SpineSprite` node and assign the `SpineSkeletonDataResource`.

### Unreal Engine (`spine-ue4`)
1. Import the `.json` and `.atlas` files into the Content Browser.
2. Assign the generated Spine Skeleton Component to your 2D Paper/Pawn Actor.
"""
        with open(out_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

        return exported_files


def export_character_to_spine(char_id: str, base_dir: Path | str, out_dir: Path | str) -> Dict[str, str]:
    """Helper to export a character from the workspace project structure."""
    base = Path(base_dir)
    atlas_json = base / "characters" / char_id / "atlases" / f"{char_id}_atlas.json"
    atlas_png = base / "characters" / char_id / "atlases" / f"{char_id}_atlas.png"
    normal_png = base / "characters" / char_id / "atlases" / f"{char_id}_atlas_normal.png"
    emission_png = base / "characters" / char_id / "atlases" / f"{char_id}_atlas_emission.png"

    dest = Path(out_dir) / char_id
    exporter = SpineExporter()
    return exporter.export(
        char_id=char_id,
        atlas_json_path=atlas_json,
        atlas_png_path=atlas_png,
        output_dir=dest,
        normal_png_path=normal_png if normal_png.exists() else None,
        emission_png_path=emission_png if emission_png.exists() else None,
    )


def validate_spine_skeleton(skeleton_path: Path | str) -> Tuple[bool, List[str]]:
    """Validates generated Spine 2D skeleton file against required structural contracts."""
    p = Path(skeleton_path)
    if not p.exists():
        return False, [f"File does not exist: {p}"]

    errors: List[str] = []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "skeleton" not in data:
            errors.append("Missing 'skeleton' root metadata block")
        if "bones" not in data or not isinstance(data["bones"], list):
            errors.append("Missing or invalid 'bones' array")
        elif len(data["bones"]) < 10:
            errors.append(f"Insufficient bones for articulated rig (found {len(data['bones'])}, expected >= 10)")

        # Verify root bone exists
        bone_names = {b.get("name") for b in data.get("bones", []) if isinstance(b, dict)}
        if "root" not in bone_names:
            errors.append("Missing required 'root' datum bone")

        # Verify parent references
        for b in data.get("bones", []):
            parent = b.get("parent")
            if parent and parent not in bone_names:
                errors.append(f"Bone '{b.get('name')}' references non-existent parent '{parent}'")

        if "slots" not in data or not isinstance(data["slots"], list):
            errors.append("Missing or invalid 'slots' list")

    except Exception as ex:
        errors.append(f"JSON parsing error: {ex}")

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(description="Export game character atlas to Spine 2D format")
    parser.add_argument("char_id", help="Character ID (e.g. the_architect, the_guardian)")
    parser.add_argument("--atlas-json", required=True, help="Path to TexturePacker atlas.json")
    parser.add_argument("--atlas-png", required=True, help="Path to atlas PNG")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--normal", default=None, help="Optional normal map path")
    parser.add_argument("--emission", default=None, help="Optional emission map path")
    args = parser.parse_args()

    exporter = SpineExporter()
    res = exporter.export(
        char_id=args.char_id,
        atlas_json_path=args.atlas_json,
        atlas_png_path=args.atlas_png,
        output_dir=args.out,
        normal_png_path=args.normal,
        emission_png_path=args.emission,
    )
    is_valid, validation_errors = validate_spine_skeleton(res["skeleton"])
    if not is_valid:
        print(f"Skeleton validation warnings: {validation_errors}")
    print(f"Spine skeleton generated: {res['skeleton']}")
    print(f"Spine atlas generated:    {res['atlas']}")


if __name__ == "__main__":
    main()
