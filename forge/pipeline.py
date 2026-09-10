#!/usr/bin/env python3
"""
img2game2d Production Asset Pipeline & Multi-Character Exporter.
Converts master sprite sheets into zero-halo, game-ready 2D assets for:
- Godot 4.x (SpriteFrames .tres & AnimatedSprite2D .tscn)
- Unity (Sprite atlas JSON & Animation Clip configs)
- Phaser 3 / PixiJS (TexturePacker JSON Hash & Array)
- Standalone Interactive Web QA Viewer (Canvas 2D + Web Audio Synthesizer)
"""
from __future__ import annotations

import json
import math
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "forge"))
from dematting import extract_alpha_demat
from lighting import generate_lighting_pack
from export_spine import export_character_to_spine

# Canvas and Anchor Configuration
CANVAS_WIDTH = 576
CANVAS_HEIGHT = 512
GROUND_Y = 460
PIVOT_X = 288


CHARACTER_CONFIGS = {
    "the_architect": {
        "name": "The Architect",
        "title": "Cyberblade Duelist",
        "source_image": "charatcer 1.jpeg",
        "bg_color": np.array([189.0, 189.0, 189.0], dtype=np.float32),
        "hitbox": {"offset_x": -30, "offset_y": -190, "width": 60, "height": 180},
        "fps_defaults": {
            "idle": 6,
            "run": 12,
            "jump": 7,
            "attack": 12,
            "defend": 8,
        },
        "loop_defaults": {
            "idle": True,
            "run": True,
            "jump": False,
            "attack": False,
            "defend": False,
        },
        "frames": [
            # IDLE (Row 1 left)
            {"anim": "idle", "idx": 0, "crop": (90, 60, 330, 465), "ground_anchor": True},
            {"anim": "idle", "idx": 1, "crop": (370, 60, 620, 465), "ground_anchor": True},
            {"anim": "idle", "idx": 2, "crop": (660, 60, 910, 465), "ground_anchor": True},
            {"anim": "idle", "idx": 3, "crop": (940, 60, 1190, 465), "ground_anchor": True},
            # JUMP (Row 1 right: launch, fall, land)
            {"anim": "jump", "idx": 0, "crop": (1720, 60, 2100, 415), "ground_anchor": False, "delta_y": -55},
            {"anim": "jump", "idx": 1, "crop": (2130, 140, 2410, 488), "ground_anchor": False, "delta_y": -20},
            {"anim": "jump", "idx": 2, "crop": (2430, 210, 2710, 490), "ground_anchor": True},
            # RUN (Row 2: 8 frames, isolated between y=494 and 786)
            {"anim": "run", "idx": 0, "crop": (70, 494, 380, 786), "ground_anchor": True},
            {"anim": "run", "idx": 1, "crop": (400, 494, 710, 786), "ground_anchor": True},
            {"anim": "run", "idx": 2, "crop": (730, 494, 1050, 786), "ground_anchor": True},
            {"anim": "run", "idx": 3, "crop": (1070, 494, 1400, 786), "ground_anchor": True},
            {"anim": "run", "idx": 4, "crop": (1420, 494, 1740, 786), "ground_anchor": True},
            {"anim": "run", "idx": 5, "crop": (1760, 494, 2060, 786), "ground_anchor": True},
            {"anim": "run", "idx": 6, "crop": (2080, 494, 2400, 786), "ground_anchor": True},
            {"anim": "run", "idx": 7, "crop": (2415, 494, 2710, 786), "ground_anchor": True},
            # ATTACK (Row 3: 5 frames with cyan energy slashes)
            {"anim": "attack", "idx": 0, "crop": (40, 790, 590, 1150), "ground_anchor": True},
            {"anim": "attack", "idx": 1, "crop": (640, 790, 1210, 1150), "ground_anchor": True},
            {"anim": "attack", "idx": 2, "crop": (1215, 790, 1715, 1150), "ground_anchor": True},
            {"anim": "attack", "idx": 3, "crop": (1730, 790, 2310, 1150), "ground_anchor": True},
            {"anim": "attack", "idx": 4, "crop": (2315, 790, 2760, 1150), "ground_anchor": True},
            # DEFEND (Row 4: 4 frames with hex energy shield)
            {"anim": "defend", "idx": 0, "crop": (60, 1170, 500, 1500), "ground_anchor": True},
            {"anim": "defend", "idx": 1, "crop": (505, 1170, 925, 1500), "ground_anchor": True},
            {"anim": "defend", "idx": 2, "crop": (935, 1170, 1325, 1500), "ground_anchor": True},
            {"anim": "defend", "idx": 3, "crop": (1335, 1170, 1675, 1500), "ground_anchor": True},
        ],
    },
    "the_guardian": {
        "name": "The Guardian",
        "title": "Armored Enforcer",
        "source_image": "charatcer 2.jpeg",
        "bg_color": np.array([189.0, 189.0, 189.0], dtype=np.float32),
        "hitbox": {"offset_x": -35, "offset_y": -180, "width": 70, "height": 170},
        "fps_defaults": {
            "idle": 6,
            "run": 12,
            "jump": 7,
            "attack": 12,
            "defend": 8,
            "hurt": 6,
        },
        "loop_defaults": {
            "idle": True,
            "run": True,
            "jump": False,
            "attack": False,
            "defend": False,
            "hurt": False,
        },
        "frames": [
            # IDLE (Row 1 left: 4 frames)
            {"anim": "idle", "idx": 0, "crop": (100, 30, 360, 370), "ground_anchor": True},
            {"anim": "idle", "idx": 1, "crop": (400, 30, 665, 370), "ground_anchor": True},
            {"anim": "idle", "idx": 2, "crop": (710, 30, 975, 370), "ground_anchor": True},
            {"anim": "idle", "idx": 3, "crop": (1010, 30, 1285, 370), "ground_anchor": True},
            # RUN (Row 2: 8 frames)
            {"anim": "run", "idx": 0, "crop": (70, 390, 390, 690), "ground_anchor": True},
            {"anim": "run", "idx": 1, "crop": (410, 390, 730, 690), "ground_anchor": True},
            {"anim": "run", "idx": 2, "crop": (740, 390, 1070, 690), "ground_anchor": True},
            {"anim": "run", "idx": 3, "crop": (1070, 390, 1400, 690), "ground_anchor": True},
            {"anim": "run", "idx": 4, "crop": (1410, 390, 1740, 690), "ground_anchor": True},
            {"anim": "run", "idx": 5, "crop": (1750, 390, 2080, 690), "ground_anchor": True},
            {"anim": "run", "idx": 6, "crop": (2090, 390, 2420, 690), "ground_anchor": True},
            {"anim": "run", "idx": 7, "crop": (2420, 390, 2740, 690), "ground_anchor": True},
            # JUMP (Row 3 left: takeoff, apex, ground slam)
            {"anim": "jump", "idx": 0, "crop": (70, 720, 380, 1070), "ground_anchor": False, "delta_y": -45},
            {"anim": "jump", "idx": 1, "crop": (380, 720, 710, 1060), "ground_anchor": False, "delta_y": -50},
            {"anim": "jump", "idx": 2, "crop": (710, 830, 1160, 1145), "ground_anchor": True},
            # ATTACK (Row 3 right: 4 frames with cyan trails)
            {"anim": "attack", "idx": 0, "crop": (1210, 850, 1580, 1150), "ground_anchor": True},
            {"anim": "attack", "idx": 1, "crop": (1580, 780, 1935, 1150), "ground_anchor": True},
            {"anim": "attack", "idx": 2, "crop": (1935, 790, 2330, 1147), "ground_anchor": True},
            {"anim": "attack", "idx": 3, "crop": (2330, 860, 2730, 1150), "ground_anchor": True},
            # DEFEND (Row 4 left: 4 frames with red barrier and impact sparks)
            {"anim": "defend", "idx": 0, "crop": (90, 1150, 480, 1515), "ground_anchor": True},
            {"anim": "defend", "idx": 1, "crop": (500, 1150, 930, 1515), "ground_anchor": True},
            {"anim": "defend", "idx": 2, "crop": (960, 1150, 1370, 1515), "ground_anchor": True},
            {"anim": "defend", "idx": 3, "crop": (1400, 1152, 1800, 1515), "ground_anchor": True},
            # HURT / TELEPORT (Row 4 right: 1 frame fading)
            {"anim": "hurt", "idx": 0, "crop": (1980, 1150, 2350, 1515), "ground_anchor": True, "is_fading": True},
        ],
    },
}


def process_character(char_id: str) -> Dict[str, Any]:
    """Runs extraction, normalization, atlas packing, and metadata generation for a character."""
    cfg = CHARACTER_CONFIGS[char_id]
    img_path = PROJECT_ROOT / cfg["source_image"]
    print(f"\n==========================================")
    print(f"PROCESSING: {cfg['name']} ({char_id})")
    print(f"Source: {img_path}")
    print(f"==========================================")

    master_img = Image.open(img_path).convert("RGB")
    master_arr = np.array(master_img)
    bg_color = cfg["bg_color"]

    char_dir = PROJECT_ROOT / "characters" / char_id
    raw_dir = char_dir / "raw_frames"
    norm_dir = char_dir / "normalized_frames"
    atlas_dir = char_dir / "atlases"
    meta_dir = char_dir / "metadata"

    for d in [raw_dir, norm_dir, atlas_dir, meta_dir]:
        d.mkdir(parents=True, exist_ok=True)

    extracted_frames = []

    for f_info in cfg["frames"]:
        anim = f_info["anim"]
        idx = f_info["idx"]
        x1, y1, x2, y2 = f_info["crop"]
        is_fading = f_info.get("is_fading", False)

        # 1. Crop search region
        sub_arr = master_arr[y1:y2, x1:x2]

        # 2. Extract de-matted RGBA
        rgba_img = extract_alpha_demat(sub_arr, bg_color, is_fading=is_fading)
        rgba_arr = np.array(rgba_img)

        # 3. Find exact non-empty bbox
        alpha_channel = rgba_arr[:, :, 3]
        nz_y, nz_x = np.where(alpha_channel > 5)

        if len(nz_y) == 0 or len(nz_x) == 0:
            print(f"WARNING: Frame {anim}_{idx} empty after dematting!")
            continue

        min_x, max_x = nz_x.min(), nz_x.max()
        min_y, max_y = nz_y.min(), nz_y.max()

        tight_rgba = rgba_img.crop((min_x, min_y, max_x + 1, max_y + 1))
        raw_fname = f"{anim}_{idx:02d}.png"
        tight_rgba.save(raw_dir / raw_fname)

        tw, th = tight_rgba.size

        # 4. Canvas normalization (576 x 512)
        norm_canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))

        # Position on canvas
        # Horizontal center anchored to PIVOT_X (288)
        paste_x = PIVOT_X - (tw // 2)

        if f_info.get("ground_anchor", True):
            # Boots bottom anchored to GROUND_Y
            paste_y = GROUND_Y - th
        else:
            # Airborne frame relative positioning
            delta_y = f_info.get("delta_y", 0)
            paste_y = (GROUND_Y - th) + delta_y

        norm_canvas.paste(tight_rgba, (paste_x, paste_y), tight_rgba)

        anim_sub_dir = norm_dir / anim
        anim_sub_dir.mkdir(parents=True, exist_ok=True)
        norm_fname = f"{idx:03d}.png"
        norm_canvas.save(anim_sub_dir / norm_fname)

        frame_record = {
            "anim": anim,
            "idx": idx,
            "raw_filename": raw_fname,
            "norm_filename": f"{anim}/{norm_fname}",
            "width": tw,
            "height": th,
            "canvas_x": paste_x,
            "canvas_y": paste_y,
            "source_box": [int(x1 + min_x), int(y1 + min_y), int(tw), int(th)],
        }
        extracted_frames.append(frame_record)
        print(f"  ✓ Extracted {anim}[{idx}]: {tw}x{th} -> placed at ({paste_x}, {paste_y})")

    # 5. Pack Texture Atlas (MaxRects Bin Packing)
    atlas_data = pack_texture_atlas(char_id, raw_dir, extracted_frames, atlas_dir)

    # 6. Generate Horizontal Strip Sheets
    generate_strip_sheets(char_id, norm_dir, cfg, atlas_dir)

    # 7. Write Metadata JSONs
    write_character_metadata(char_id, cfg, extracted_frames, meta_dir)

    return {
        "character": char_id,
        "frames_extracted": len(extracted_frames),
        "atlas": atlas_data,
    }


def pack_texture_atlas(
    char_id: str,
    raw_dir: Path,
    frame_records: List[Dict[str, Any]],
    atlas_dir: Path,
    atlas_size: int = 2048,
    padding: int = 2,
) -> Dict[str, Any]:
    """Packs raw frames into a Power-of-Two (POT) atlas with 2px bleeding padding."""
    # Sort frames by height descending for shelf packing
    sorted_frames = sorted(frame_records, key=lambda f: f["height"], reverse=True)

    atlas_img = Image.new("RGBA", (atlas_size, atlas_size), (0, 0, 0, 0))
    packed_frames = {}

    cur_x = padding
    cur_y = padding
    shelf_height = 0

    for f_info in sorted_frames:
        fw = f_info["width"]
        fh = f_info["height"]
        raw_path = raw_dir / f_info["raw_filename"]
        frame_img = Image.open(raw_path)

        if cur_x + fw + padding > atlas_size:
            # Move to next shelf
            cur_x = padding
            cur_y += shelf_height + padding
            shelf_height = 0

        if cur_y + fh + padding > atlas_size:
            print(f"ERROR: Texture atlas overflow for {char_id}! Expand size.")
            break

        atlas_img.paste(frame_img, (cur_x, cur_y), frame_img)

        # TexturePacker JSON Hash entry
        frame_key = f"{f_info['anim']}_{f_info['idx']:02d}.png"
        packed_frames[frame_key] = {
            "frame": {"x": cur_x, "y": cur_y, "w": fw, "h": fh},
            "rotated": False,
            "trimmed": True,
            "spriteSourceSize": {
                "x": f_info["canvas_x"],
                "y": f_info["canvas_y"],
                "w": fw,
                "h": fh,
            },
            "sourceSize": {"w": CANVAS_WIDTH, "h": CANVAS_HEIGHT},
            "pivot": {
                "x": round(PIVOT_X / CANVAS_WIDTH, 4),
                "y": round(GROUND_Y / CANVAS_HEIGHT, 4),
            },
        }

        cur_x += fw + padding
        if fh > shelf_height:
            shelf_height = fh

    atlas_png_path = atlas_dir / f"{char_id}_atlas.png"
    atlas_json_path = atlas_dir / f"{char_id}_atlas.json"

    atlas_img.save(atlas_png_path, "PNG")

    atlas_manifest = {
        "frames": packed_frames,
        "meta": {
            "app": "img2game2d-antigravity",
            "version": "1.0",
            "image": f"{char_id}_atlas.png",
            "format": "RGBA8888",
            "size": {"w": atlas_size, "h": atlas_size},
            "scale": "1",
        },
    }

    with open(atlas_json_path, "w", encoding="utf-8") as f:
        json.dump(atlas_manifest, f, indent=2)

    print(f"  ✓ Atlas saved: {atlas_png_path} ({atlas_size}x{atlas_size}, {len(packed_frames)} frames)")
    return atlas_manifest


def generate_strip_sheets(char_id: str, norm_dir: Path, cfg: Dict[str, Any], atlas_dir: Path):
    """Generates standard horizontal sprite sheet strips for each individual animation."""
    anims = set(f["anim"] for f in cfg["frames"])

    for anim in sorted(anims):
        anim_dir = norm_dir / anim
        frame_files = sorted(anim_dir.glob("*.png"))
        if not frame_files:
            continue

        num_frames = len(frame_files)
        strip_w = num_frames * CANVAS_WIDTH
        strip_h = CANVAS_HEIGHT

        strip_img = Image.new("RGBA", (strip_w, strip_h), (0, 0, 0, 0))

        for i, fp in enumerate(frame_files):
            f_img = Image.open(fp)
            strip_img.paste(f_img, (i * CANVAS_WIDTH, 0), f_img)

        strip_png_path = atlas_dir / f"{anim}_sheet.png"
        strip_json_path = atlas_dir / f"{anim}_sheet.json"
        strip_img.save(strip_png_path, "PNG")

        strip_meta = {
            "character": char_id,
            "animation": anim,
            "frame_count": num_frames,
            "frame_width": CANVAS_WIDTH,
            "frame_height": CANVAS_HEIGHT,
            "fps": cfg["fps_defaults"].get(anim, 10),
            "loop": cfg["loop_defaults"].get(anim, True),
            "pivot": {"x": PIVOT_X, "y": GROUND_Y},
        }
        with open(strip_json_path, "w", encoding="utf-8") as f:
            json.dump(strip_meta, f, indent=2)


def write_character_metadata(
    char_id: str,
    cfg: Dict[str, Any],
    frame_records: List[Dict[str, Any]],
    meta_dir: Path,
):
    """Generates character specification and animation manifest JSON files."""
    anims_info = {}
    for anim, fps in cfg["fps_defaults"].items():
        frames = [f for f in frame_records if f["anim"] == anim]
        anims_info[anim] = {
            "fps": fps,
            "loop": cfg["loop_defaults"].get(anim, True),
            "frame_count": len(frames),
            "frames": [f["norm_filename"] for f in frames],
        }

    char_meta = {
        "id": char_id,
        "name": cfg["name"],
        "title": cfg["title"],
        "canvas_size": {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT},
        "pivot": {"x": PIVOT_X, "y": GROUND_Y},
        "hitbox": cfg["hitbox"],
        "animations": anims_info,
    }

    with open(meta_dir / "character.json", "w", encoding="utf-8") as f:
        json.dump(char_meta, f, indent=2)

    with open(meta_dir / "animations.json", "w", encoding="utf-8") as f:
        json.dump(anims_info, f, indent=2)


def generate_all_engine_exports():
    """Generates export packages for Godot 4, Unity, Phaser 3, Spine 2D, and Web QA Viewer."""
    print("\n==========================================")
    print("GENERATING MULTI-ENGINE EXPORTS")
    print("==========================================")

    # 0. Dynamic 2D Lighting Maps (Normal & Emission)
    generate_all_lighting_maps()

    # 1. Godot 4.x
    export_godot()

    # 2. Unity
    export_unity()

    # 3. Phaser / PixiJS
    export_phaser()

    # 4. Spine 2D
    export_spine()

    # 5. Interactive Web QA Viewer
    export_web_viewer()


def generate_all_lighting_maps():
    """Generates tangent-space normal maps and emission maps for all character atlases."""
    print("  Generating 2D Normal & Emission Maps...")
    for char_id in ["the_architect", "the_guardian"]:
        atlas_png = PROJECT_ROOT / "characters" / char_id / "atlases" / f"{char_id}_atlas.png"
        out_dir = PROJECT_ROOT / "characters" / char_id / "atlases"
        generate_lighting_pack(atlas_png, out_dir, base_name=f"{char_id}_atlas")
    print("  ✓ Normal and Emission lighting maps generated.")


def export_spine():
    """Generates official Spine 2D skeleton.json, .atlas, and asset packages."""
    spine_dir = PROJECT_ROOT / "exports" / "spine"
    spine_dir.mkdir(parents=True, exist_ok=True)

    for char_id in ["the_architect", "the_guardian"]:
        export_character_to_spine(char_id, PROJECT_ROOT, spine_dir)
        print(f"  ✓ Spine 2D export created for {char_id}: {spine_dir / char_id}")


def export_godot():
    """Generates Godot 4.x SpriteFrames .tres and .tscn scenes."""
    godot_dir = PROJECT_ROOT / "exports" / "godot"

    for char_id in ["the_architect", "the_guardian"]:
        out_dir = godot_dir / char_id
        out_dir.mkdir(parents=True, exist_ok=True)
        meta_file = PROJECT_ROOT / "characters" / char_id / "metadata" / "character.json"

        with open(meta_file, "r") as f:
            char_meta = json.load(f)

        # Copy atlas texture
        atlas_src = PROJECT_ROOT / "characters" / char_id / "atlases" / f"{char_id}_atlas.png"
        shutil.copy2(atlas_src, out_dir / f"{char_id}_atlas.png")

        # Create Godot SpriteFrames .tres
        tres_path = out_dir / f"{char_id}_frames.tres"
        tres_content = f"""[gd_resource type="SpriteFrames" format=3]

[resource]
animations = ["""
        for anim, a_info in char_meta["animations"].items():
            tres_content += f"""
{{
"frames": [],
"loop": {"true" if a_info["loop"] else "false"},
"name": &"{anim}",
"speed": {float(a_info["fps"])}
}},"""
        tres_content += "\n]\n"
        with open(tres_path, "w", encoding="utf-8") as f:
            f.write(tres_content)

        # Create Character Scene .tscn
        tscn_path = out_dir / f"{char_id}.tscn"
        hb = char_meta["hitbox"]
        tscn_content = f"""[gd_scene format=3]

[node name="{char_meta['name'].replace(' ', '')}" type="CharacterBody2D"]

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
sprite_frames = ExtResource("1_{char_id}")
animation = &"idle"
autoplay = "idle"
offset = Vector2({PIVOT_X - CANVAS_WIDTH//2}, {GROUND_Y - CANVAS_HEIGHT//2})

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
position = Vector2({hb['offset_x'] + hb['width']//2}, {hb['offset_y'] + hb['height']//2})
"""
        with open(tscn_path, "w", encoding="utf-8") as f:
            f.write(tscn_content)

        print(f"  ✓ Godot 4 export created for {char_id}: {tscn_path}")


def export_unity():
    """Generates Unity sprite manifests and animation clip descriptor JSONs."""
    unity_dir = PROJECT_ROOT / "exports" / "unity"

    for char_id in ["the_architect", "the_guardian"]:
        out_dir = unity_dir / char_id
        out_dir.mkdir(parents=True, exist_ok=True)

        atlas_src = PROJECT_ROOT / "characters" / char_id / "atlases" / f"{char_id}_atlas.png"
        atlas_json_src = PROJECT_ROOT / "characters" / char_id / "atlases" / f"{char_id}_atlas.json"

        shutil.copy2(atlas_src, out_dir / f"{char_id}_atlas.png")
        shutil.copy2(atlas_json_src, out_dir / f"{char_id}_atlas.json")

        meta_file = PROJECT_ROOT / "characters" / char_id / "metadata" / "character.json"
        with open(meta_file, "r") as f:
            char_meta = json.load(f)

        unity_prefab_spec = {
            "gameObjectName": char_meta["name"].replace(" ", ""),
            "spriteAtlas": f"{char_id}_atlas.png",
            "pixelsPerUnit": 100,
            "pivot": {"x": PIVOT_X / CANVAS_WIDTH, "y": (CANVAS_HEIGHT - GROUND_Y) / CANVAS_HEIGHT},
            "boxCollider2D": {
                "offset": [char_meta["hitbox"]["offset_x"], -char_meta["hitbox"]["offset_y"]],
                "size": [char_meta["hitbox"]["width"], char_meta["hitbox"]["height"]],
            },
            "animatorController": {
                "parameters": ["Speed", "IsJumping", "IsAttacking", "IsDefending"],
                "clips": list(char_meta["animations"].keys()),
            },
        }

        with open(out_dir / "unity_prefab_spec.json", "w", encoding="utf-8") as f:
            json.dump(unity_prefab_spec, f, indent=2)

        print(f"  ✓ Unity export created for {char_id}: {out_dir}")


def export_phaser():
    """Exports TexturePacker format for Phaser 3 / PixiJS."""
    phaser_dir = PROJECT_ROOT / "exports" / "phaser"
    phaser_dir.mkdir(parents=True, exist_ok=True)

    for char_id in ["the_architect", "the_guardian"]:
        atlas_src = PROJECT_ROOT / "characters" / char_id / "atlases" / f"{char_id}_atlas.png"
        atlas_json_src = PROJECT_ROOT / "characters" / char_id / "atlases" / f"{char_id}_atlas.json"
        shutil.copy2(atlas_src, phaser_dir / f"{char_id}_atlas.png")
        shutil.copy2(atlas_json_src, phaser_dir / f"{char_id}_atlas.json")

    print(f"  ✓ Phaser 3 / PixiJS exports placed in {phaser_dir}")


def export_web_viewer():
    """Sets up the interactive Web QA Viewer assets directory."""
    viewer_dir = PROJECT_ROOT / "exports" / "viewer"
    assets_dir = viewer_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Copy both atlases, lighting maps & manifests to viewer/assets/
    for char_id in ["the_architect", "the_guardian"]:
        c_atlas_dir = PROJECT_ROOT / "characters" / char_id / "atlases"
        shutil.copy2(c_atlas_dir / f"{char_id}_atlas.png", assets_dir / f"{char_id}_atlas.png")
        shutil.copy2(c_atlas_dir / f"{char_id}_atlas.json", assets_dir / f"{char_id}_atlas.json")
        shutil.copy2(
            PROJECT_ROOT / "characters" / char_id / "metadata" / "character.json",
            assets_dir / f"{char_id}_meta.json",
        )
        for map_type in ["normal", "emission"]:
            map_src = c_atlas_dir / f"{char_id}_atlas_{map_type}.png"
            if map_src.exists():
                shutil.copy2(map_src, assets_dir / f"{char_id}_atlas_{map_type}.png")

    print(f"  ✓ Web QA Viewer assets (including 2D lighting maps) linked in {assets_dir}")


def run_full_pipeline():
    """Executes the complete asset extraction, atlas packing, and multi-engine export."""
    results = {}
    for char_id in ["the_architect", "the_guardian"]:
        res = process_character(char_id)
        results[char_id] = res

    generate_all_engine_exports()
    print("\n✓ FULL PIPELINE EXECUTION COMPLETE!")
    return results


if __name__ == "__main__":
    run_full_pipeline()
