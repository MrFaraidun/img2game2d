# Changelog

All notable changes to `img2game2d` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-05

### Added
- **Core Architecture**: Modeled after `img2threejs` with staged pipeline, local state gate (`.img2game2d/state.json`), grimoire reference docs, and incremental build cache.
- **Stage 1 (Intake)**:
  - `probe_image.py`: Format, dimensions, aspect ratio, alpha presence, DPI probing.
  - `detect_style.py`: Robust heuristic art style detection (pixel art, anime, painted, vector, etc.) with NumPy numerical error safety.
  - `detect_views.py`: Turnaround sheet multi-panel and perspective orientation detection based on content runs.
  - `remove_background.py`: Multi-strategy background extraction (existing alpha, color keying, edge detection, and rembg fallback).
- **Stage 2 (Spec)**:
  - `new_asset_spec.py`: Automated `asset.json` specification generation.
  - `validate_asset_spec.py`: Local offline `$ref`-resolving JSON Schema validator.
  - `layer_decompose.py`: Articulation layer decomposition with z-depth and pivot points.
  - `build_rig.py`: Hierarchical skeletal rig generator with anatomical bone rotation constraints.
- **Stage 3 (Build)**:
  - `extract_layers.py`: Bounding-box layer crop and alpha mask extraction.
  - `reconstruct_occlusion.py`: Mirror-fill and nearest-neighbor texture inpainting for occluded joints.
  - `generate_frames.py`: Animation frame generator supporting stub, OpenAI, and local backends with SHA-256 caching.
  - `orchestrate_build.py`: Automated multi-pass build coordinator.
- **Stage 4 (Review)**:
  - `validate_silhouette.py`: Silhouette Intersection-over-Union (IoU) gate against reference.
  - `validate_colors.py`: Multi-channel color histogram Bhattacharyya coefficient gate.
  - `validate_continuity.py`: Frame-to-frame displacement and animation continuity gate.
  - `make_comparison_sheet.py`: Side-by-side visual audit sheet generator.
  - `append_review.py`: State and review ledger recorder.
- **Stage 5 (Atlas)**:
  - `pack_atlas.py`: Power-of-two greedy bin-packer with TexturePacker-compatible JSON format.
  - `generate_spritesheet.py`: Horizontal strip sprite sheet generator with frame timing metadata.
- **Stage 6 (Export)**:
  - `export.py`: Router for multi-engine target export.
  - `godot_exporter.py`: Godot 4 `.tscn` and `SpriteFrames.tres` scene/resource generation.
  - `unity_exporter.py`: Unity sprite slice metadata and `AnimatorController` JSON stubs.
  - `phaser_exporter.py`: Phaser 3 atlas definitions and typed TypeScript animation loader.
  - `pixijs_exporter.py`: PixiJS spritesheet JSON and `AnimatedSprite` TypeScript factory.
- **Grimoire & Documentation**:
  - 16 comprehensive reference guides across intake, spec, build, review, and export.
  - 6 AI prompt specifications for guided visual reasoning and self-correction loops.
  - Production templates for `project.yaml`, `asset.json`, and `animation.json`.
- **Testing**:
  - Full automated pytest test suite (`test_all.py`) with 21/21 passing test cases.
