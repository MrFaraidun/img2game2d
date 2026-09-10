"""
Spine 2D exporter for img2game2d.

Generates:
    exports/spine/
    ├── <AssetName>_skeleton.json — Spine 3.8/4.x compatible skeleton, bone & animation manifest
    ├── <AssetName>.atlas        — Standard LibGDX / Spine texture atlas definition
    ├── <AssetName>_atlas.png    — Atlas diffuse texture
    ├── <AssetName>_atlas_normal.png (optional dynamic 2D lighting normal map)
    ├── <AssetName>_atlas_emission.png (optional bloom glow map)
    └── README.md                — Integration instructions for Unity, Godot, and Unreal runtimes
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional


class SpineExporter:
    """Exports game assets as Spine 2D compatible skeleton and atlas files."""

    def __init__(self, spine_version: str = "3.8.99"):
        self.spine_version = spine_version

    def export(self, asset: dict, atlases_dir: str, out_dir: str) -> dict:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        atlases_path = Path(atlases_dir)

        asset_id = asset.get("asset_id", "unnamed")
        asset_name = asset.get("name", asset_id).replace(" ", "_")
        animations = asset.get("animations", {})

        # Find atlas json and png files
        atlas_json_files = list(atlases_path.glob("*.json"))
        atlas_png_files = list(atlases_path.glob("*.png"))

        # Filter out summary json if present
        primary_json = None
        for jf in atlas_json_files:
            if "summary" not in jf.name.lower():
                primary_json = jf
                break
        if not primary_json and atlas_json_files:
            primary_json = atlas_json_files[0]

        primary_png = None
        for pf in atlas_png_files:
            if not pf.name.endswith(("_normal.png", "_emission.png", "_n.png", "_e.png")):
                primary_png = pf
                break
        if not primary_png and atlas_png_files:
            primary_png = atlas_png_files[0]

        frames_dict = {}
        atlas_w = 2048
        atlas_h = 2048
        canvas_w = 576
        canvas_h = 512

        if primary_json and primary_json.exists():
            with open(primary_json, "r", encoding="utf-8") as f:
                jdata = json.load(f)
                if "frames" in jdata:
                    # TexturePacker hash or array
                    if isinstance(jdata["frames"], dict):
                        frames_dict = jdata["frames"]
                    elif isinstance(jdata["frames"], list):
                        for item in jdata["frames"]:
                            if "filename" in item:
                                frames_dict[item["filename"]] = item
                if "meta" in jdata:
                    atlas_w = jdata["meta"].get("size", {}).get("w", 2048)
                    atlas_h = jdata["meta"].get("size", {}).get("h", 2048)

        # Detect source canvas size
        for f_data in frames_dict.values():
            ss = f_data.get("sourceSize", {})
            if ss.get("w") and ss.get("h"):
                canvas_w = ss["w"]
                canvas_h = ss["h"]
                break

        # Group frames by animation
        anim_frames: Dict[str, List[tuple[int, str, dict]]] = {}
        for f_name, f_info in frames_dict.items():
            stem = f_name.replace(".png", "")
            parts = stem.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit():
                clip = parts[0]
                idx = int(parts[1])
            else:
                clip = "default"
                idx = 0
            anim_frames.setdefault(clip, []).append((idx, stem, f_info))

        for clip in anim_frames:
            anim_frames[clip].sort(key=lambda x: x[0])

        first_attachment = ""
        for clip, flist in anim_frames.items():
            if flist:
                first_attachment = flist[0][1]
                break

        # ── 1. Spine skeleton.json ─────────────────────────────────────────
        skeleton_json: Dict[str, Any] = {
            "skeleton": {
                "hash": f"{asset_name}_hash",
                "spine": self.spine_version,
                "x": -round(canvas_w / 2),
                "y": 0,
                "width": canvas_w,
                "height": canvas_h,
                "images": "./",
            },
            "bones": [
                {"name": "root"},
                {
                    "name": "body",
                    "parent": "root",
                    "x": 0,
                    "y": round(canvas_h * 0.1),
                },
            ],
            "slots": [
                {
                    "name": "character",
                    "bone": "body",
                    "attachment": first_attachment,
                }
            ],
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

        skin_attachments = skeleton_json["skins"][0]["attachments"]["character"]

        for clip, flist in anim_frames.items():
            for _, stem, f_info in flist:
                f_box = f_info.get("frame", {})
                s_box = f_info.get("spriteSourceSize", {})
                pivot = f_info.get("pivot", {"x": 0.5, "y": 0.8984})

                aw = f_box.get("w", 100)
                ah = f_box.get("h", 100)
                px = pivot.get("x", 0.5) * canvas_w
                py = (1.0 - pivot.get("y", 0.8984)) * canvas_h

                trim_x = s_box.get("x", 0)
                trim_y = canvas_h - (s_box.get("y", 0) + ah)

                cx = (trim_x + aw / 2.0) - px
                cy = (trim_y + ah / 2.0) - py

                skin_attachments[stem] = {
                    "x": round(cx, 2),
                    "y": round(cy, 2),
                    "width": aw,
                    "height": ah,
                }

        # Build animation timelines
        for clip, flist in anim_frames.items():
            fps = animations.get(clip, {}).get("fps", 10)
            duration = 1.0 / max(1, fps)
            timeline = []
            for i, (_, stem, _) in enumerate(flist):
                timeline.append({"time": round(i * duration, 4), "name": stem})
            skeleton_json["animations"][clip] = {
                "slots": {
                    "character": {
                        "attachment": timeline
                    }
                }
            }

        skeleton_path = out_path / f"{asset_name}_skeleton.json"
        with open(skeleton_path, "w", encoding="utf-8") as f:
            json.dump(skeleton_json, f, indent=2)

        # ── 2. Spine .atlas ──────────────────────────────────────────────
        atlas_img_name = primary_png.name if primary_png else f"{asset_name}_atlas.png"
        atlas_lines = [
            atlas_img_name,
            f"size: {atlas_w},{atlas_h}",
            "format: RGBA8888",
            "filter: Linear,Linear",
            "repeat: none",
        ]

        for f_name, f_info in frames_dict.items():
            stem = f_name.replace(".png", "")
            f_box = f_info.get("frame", {})
            s_box = f_info.get("spriteSourceSize", {})
            s_size = f_info.get("sourceSize", {})

            ow = s_size.get("w", canvas_w)
            oh = s_size.get("h", canvas_h)
            tw = f_box.get("w", ow)
            th = f_box.get("h", oh)
            ox = s_box.get("x", 0)
            oy = oh - (s_box.get("y", 0) + th)

            atlas_lines.extend(
                [
                    stem,
                    "  rotate: false",
                    f"  xy: {f_box.get('x', 0)}, {f_box.get('y', 0)}",
                    f"  size: {tw}, {th}",
                    f"  orig: {ow}, {oh}",
                    f"  offset: {ox}, {oy}",
                    "  index: -1",
                ]
            )

        atlas_text_path = out_path / f"{asset_name}.atlas"
        with open(atlas_text_path, "w", encoding="utf-8") as f:
            f.write("\n".join(atlas_lines) + "\n")

        # Copy textures
        copied_files = [str(skeleton_path), str(atlas_text_path)]
        if primary_png and primary_png.exists():
            dest_png = out_path / primary_png.name
            shutil.copy2(primary_png, dest_png)
            copied_files.append(str(dest_png))

        # Copy normal/emission maps if found
        for extra in atlases_path.glob("*_normal.png"):
            dest_extra = out_path / extra.name
            shutil.copy2(extra, dest_extra)
            copied_files.append(str(dest_extra))
        for extra in atlases_path.glob("*_emission.png"):
            dest_extra = out_path / extra.name
            shutil.copy2(extra, dest_extra)
            copied_files.append(str(dest_extra))

        # ── 3. README ────────────────────────────────────────────────────
        readme = f"""# {asset_name} — Spine 2D Export

Generated by img2game2d.

## Included Assets
- `{asset_name}_skeleton.json` — Spine 3.8/4.x skeleton with keyed animations.
- `{asset_name}.atlas` — LibGDX/Spine texture atlas.
- `{atlas_img_name}` — RGBA atlas diffuse texture.

## Quick Integration
- **Unity**: Import `spine-unity` runtime, drag files into `Assets/`, create `SkeletonAnimation`.
- **Godot 4**: Import `spine-godot` GDExtension, create a `SpineSprite` node.
- **Unreal Engine**: Import into Content Browser via `spine-ue4` plugin.
"""
        (out_path / "README.md").write_text(readme)

        return {
            "engine": "spine",
            "files": copied_files,
            "skeleton": str(skeleton_path),
            "atlas": str(atlas_text_path),
        }
