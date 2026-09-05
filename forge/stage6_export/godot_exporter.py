"""
Godot 4 exporter for img2game2d.

Generates:
    exports/godot/
    ├── <AssetName>.tscn          — AnimatedSprite2D scene file
    ├── <AssetName>_frames.tres   — SpriteFrames resource
    └── README.md                 — Integration instructions
"""
from __future__ import annotations

import json
from pathlib import Path


class GodotExporter:
    """Exports game assets as Godot 4 AnimatedSprite2D scene files."""

    def export(self, asset: dict, atlases_dir: str, out_dir: str) -> dict:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        atlases_path = Path(atlases_dir)

        asset_id = asset.get("asset_id", "unnamed")
        asset_name = asset.get("name", asset_id).replace(" ", "")
        animations = asset.get("animations", {})

        # Collect atlas info
        atlas_summary_path = atlases_path / "atlas_summary.json"
        if atlas_summary_path.exists():
            with open(atlas_summary_path) as f:
                atlas_summary = json.load(f)
        else:
            atlas_summary = {}

        # ── Generate .tscn scene file ─────────────────────────────────────
        tscn_content = self._build_tscn(asset_name, animations, atlas_summary, atlases_path, out_path)
        tscn_path = out_path / f"{asset_name}.tscn"
        tscn_path.write_text(tscn_content)

        # ── Generate SpriteFrames .tres resource ─────────────────────────
        tres_content = self._build_tres(asset_name, animations, atlas_summary, atlases_path)
        tres_path = out_path / f"{asset_name}_frames.tres"
        tres_path.write_text(tres_content)

        # ── README ───────────────────────────────────────────────────────
        readme = self._build_readme(asset_name, out_path)
        (out_path / "README.md").write_text(readme)

        return {
            "engine": "godot",
            "files": [str(tscn_path), str(tres_path)],
            "scene": str(tscn_path),
            "sprite_frames": str(tres_path),
        }

    def _build_tscn(
        self,
        name: str,
        animations: dict,
        atlas_summary: dict,
        atlases_path: Path,
        out_path: Path,
    ) -> str:
        """Build a Godot 4 .tscn file with AnimatedSprite2D."""
        lines = [
            '[gd_scene load_steps=2 format=3 uid="uid://img2game2d"]',
            "",
            f'[ext_resource type="SpriteFrames" path="{name}_frames.tres" id="1"]',
            "",
            "[node name=\"Root\" type=\"Node2D\"]",
            "",
            f'[node name="{name}" type="AnimatedSprite2D" parent="."]',
            'frames = ExtResource("1")',
            f'animation = "idle"',
            "autoplay = \"idle\"",
            "centered = true",
            "",
        ]
        return "\n".join(lines)

    def _build_tres(
        self,
        name: str,
        animations: dict,
        atlas_summary: dict,
        atlases_path: Path,
    ) -> str:
        """Build a Godot 4 SpriteFrames .tres resource."""
        # Count total textures (one per frame)
        load_steps = 2
        for clip_name, clip_data in atlas_summary.items():
            load_steps += clip_data.get("frame_count", 0)

        lines = [
            f"[gd_resource type=\"SpriteFrames\" load_steps={load_steps} format=3]",
            "",
        ]

        # Declare texture resources (point to atlas PNGs)
        tex_id = 1
        tex_refs: dict[str, dict[str, int]] = {}  # clip_name → {frame_idx → tex_id}

        for clip_name, clip_data in atlas_summary.items():
            atlas_png = atlases_path / f"{clip_name}.png"
            atlas_json_path = atlases_path / f"{clip_name}.json"
            tex_refs[clip_name] = {}

            if atlas_json_path.exists():
                with open(atlas_json_path) as f:
                    atlas_data = json.load(f)
                frame_metas = atlas_data.get("frames", [])
            else:
                frame_metas = []

            for i, frame_meta in enumerate(frame_metas):
                region = frame_meta.get("frame", {})
                lines.append(
                    f'[ext_resource type="Texture2D" path="{atlas_png.name}" id="{tex_id}"]'
                )
                tex_refs[clip_name][i] = tex_id
                tex_id += 1

        lines.append("")
        lines.append('[resource]')
        lines.append("animations = [")

        for clip_name, anim_config in animations.items():
            fps = anim_config.get("fps", 12)
            loop = anim_config.get("loop", True)
            clip_tex = tex_refs.get(clip_name, {})
            frame_count = len(clip_tex)

            lines.append("{")
            lines.append(f'  "frames": [')
            for i in range(frame_count):
                tid = clip_tex.get(i, "")
                if tid:
                    lines.append(f'    {{')
                    lines.append(f'      "duration": 1.0,')
                    lines.append(f'      "texture": ExtResource("{tid}"),')
                    lines.append(f'    }},')
            lines.append(f"  ],")
            lines.append(f'  "loop": {"true" if loop else "false"},')
            lines.append(f'  "name": "{clip_name}",')
            lines.append(f'  "speed": {float(fps)},')
            lines.append("},")

        lines.append("]")
        return "\n".join(lines)

    def _build_readme(self, name: str, out_path: Path) -> str:
        return f"""# {name} — Godot 4 Export

## Files
- `{name}.tscn` — AnimatedSprite2D scene. Drag into your scene tree.
- `{name}_frames.tres` — SpriteFrames resource with all animation clips.

## Setup
1. Copy the entire `godot/` folder into your Godot project's `res://` directory.
2. Open `{name}.tscn` in the Godot editor.
3. The AnimatedSprite2D node is pre-configured with all animation clips.
4. Attach a script and call `$AnimatedSprite2D.play("idle")` to start.

## Animations
See `asset.json` for the full animation list with FPS and loop settings.

Generated by [img2game2d](https://github.com/img2game2d)
"""
