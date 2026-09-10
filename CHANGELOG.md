# Changelog

All notable changes to `img2game2d` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-09-10 — Framework Release & Finnova Bento Web Studio

- **Framework Scaffolding Engine (`forge/scaffold.py`, `forge/cli.py`)**:
  - `img2game2d init [name]`: Interactive terminal scaffolder generating configured 2D game asset workspaces with declarative `img2game2d.config.json`.
  - `img2game2d dev`: Spawns the live Finnova-style Web Studio with live hot-reloading.
  - `img2game2d build`: Zero-configuration headless builds across all game engines.
  - Added standalone `bin/create-img2game2d` for instant CLI execution.
- **Finnova-Inspired Dual-Tone Web Studio (`examples/viewer/`, `exports/viewer/`)**:
  - Complete visual redesign with KPI stat bento cards, pill navigation, and deep indigo workbench (`#121526`).
  - **Interactive 2D Torchlight**: Mouse-driven real-time point light dynamically illuminating surface reliefs via generated normal maps (`_normal.png`).
  - **Real-Time Bloom Emission**: Screen-blended neon glow for cyberblades, plasma shields, and eyes (`_emission.png`).
  - Finnova playback console with speed pills, timeline scrubbing, and synthesized audio.
- **Test Suite Expansion (`forge/tests/test_all.py`)**:
  - Added `TestV200Framework` validating scaffolding, declarative config, and directory tree creation.
  - Full suite expanded to 36/36 tests with 100% passing rate.

## [1.5.0] - 2026-09-10 — Spine 2D Native Runtime & 2D Dynamic Lighting Engine

- **Spine 2D Exporter (`forge/stage6_export/spine_exporter.py`)**:
  - Full export to official Spine 2D `skeleton.json` (Spine 3.8/4.x spec) and standard LibGDX `.atlas` format.
  - Generates bone hierarchies (`root`, `body`), slot attachments, and keyed timeline animations.
  - Native drag-and-drop compatibility with `spine-unity`, `spine-godot`, `spine-ue4`, and web runtimes.
  - Integrated into main export router (`--engine spine` or `--engine all`).
- **2D Dynamic Lighting Engine (`forge/stage5_atlas/generate_lighting_maps.py`)**:
  - **Tangent-Space Normal Maps (`_normal.png`)**: Computes surface gradients via Sobel operators on luminance, encoding surface angles into OpenGL standard tangent vectors `[R: Nx, G: Ny, B: Nz]` for dynamic 2D point/spot lights in Godot 4 CanvasItem and Unity URP 2D.
  - **Emission / Bloom Maps (`_emission.png`)**: Extracts high-saturation, high-energy pixels (cyberblades, shields, visors) onto clean emissive textures for bloom shaders.
- **Test Suite Expansion (`forge/tests/test_all.py`)**:
  - Added `test_spine_exporter` and `test_lighting_maps`.
  - Expanded test suite from 33 to 35 automated tests with 100% passing rate.

## [1.1.0] - 2026-09-06 — Production Character Showcases & Zero-Halo Engine

- **New Live Production Showcases**:
  - **The Architect (`examples/the_architect/`)**: Cyberblade Duelist with 24 frames across 5 action cycles (Idle, Run, Jump, Attack, Defend), 4K ($2048 \times 2048$) and FHD ($1024 \times 1024$) power-of-two texture atlases, and multi-engine exports (Godot 4.x, Unity 2022+, Phaser 3).
  - **The Guardian (`examples/the_guardian/`)**: Armored Enforcer with heavy plate armor, zero edge halos, full collision hurtboxes, ground pivot alignment ($Y=460$), and complete engine packages.
- **Production Dual-Engine QA Viewer (`examples/viewer/`)**:
  - Standalone interactive HTML5 Canvas inspector with real-time character hot-swapping, animation playback controls, speed slider, timeline scrubber, and dynamic canvas scaling.
  - Procedural Web Audio API sound synthesizer producing customized audio cues for attacks, shield deployment, heavy steps, and landing impact.
  - Real-time diagnostic overlays: combat hurtbox, ground pivot crosshair ($X=288, Y=460$), ground reference baseline, and raw frame metadata JSON inspector.
- **Zero-Halo Dual-Contour Alpha De-Matting (`forge/stage1_intake/dematting.py`)**:
  - Dual-contour luminance thresholding eliminating JPEG Gibbs ringing overshoot and bright border halos around dark lineart.
  - Inward alpha dilation and color bleed extension ensuring pixel-perfect alpha blending on arbitrary dark or bright game backgrounds.

## [1.0.0] - 2026-09-06 — Official Launch Release

- **Showcase & Live Production Footages (`examples/hollow_knight`)**:
  - Complete end-to-end game asset demonstration created from a single 2D character concept.
  - High-fidelity animated footages (`idle.gif`, `walk.gif`, `jump.gif`, `attack.gif`, `hurt.gif`, and 24-frame synchronized `showcase_banner.gif`).
  - Includes raw reference, surgical anatomy layers, skeletal rig, packed sprite atlases, engine controller scripts (Godot 4, Unity, PixiJS), and interactive HTML5 web viewer.
  - Architectural pipeline diagram (`pipeline_breakdown.png`).
- **Action Sheet Slicer & Multi-Pose Animation Intake**:
  - `detect_actions.py`: Auto-detects 3 to 6 action figures (idle, walk, jump, attack, hurt) from single-canvas character action sheets.
  - Slices, normalizes dimensions (512x512), and aligns ground planes so characters don't jitter vertically.
  - `cli.py slice-actions`: Standalone panel extraction subcommand and `build --action-sheet` flag.
  - `grimoire/intake/action_sheets.md`: Complete guide and best-practice AI prompt templates.
- **Pre-Flight Quality Gate & AI Prompt Synthesis**:
  - `assess_quality.py`: Evaluates image resolution, border clipping, and background contrast with diagnostic verdicts.
  - Automatically synthesizes positive/negative prompts and Midjourney `/imagine` commands for both Single Neutral Pose and 5-Pose Action Sheets.
  - `cli.py check`: Immediate diagnostic CLI tool.
- **Intake Super-Resolution & Clarity Enhancement**:
  - `enhance.py`: High-order Lanczos super-sampling (2x/4x), contrast-adaptive sharpening (CAS), and dark outline sealing.
  - `cli.py enhance`: Standalone CLI subcommand and `--enhance` build flag.
- **Zero-Halo Alpha De-Matting & Defringing Protocol**:
  - `_shared/image_utils.py:defringe_alpha`: Dual-contour luminance edge detection and dark tone shifting with alpha contour erosion to eliminate white halo borders.
  - Integrated directly into `remove_background.py` and pipeline intake.
- **Exact Inverse-Affine Coordinate Calculus**:
  - `_shared/transforms.py:get_inverse_affine_matrix`: Closed-form inverse affine 6-tuple for PIL `Image.transform(AFFINE)` preventing inverted rotations, coordinate drift, and anatomical detachment.
  - `_shared/transforms.py:apply_continuous_shear`: Non-linear vertical shear deformation for cloaks, robes, and legs, preventing characters from breaking into disconnected rectangular pieces during walk cycles.
  - `_shared/transforms.py:inpaint_contact_seam`: Joint contact hole sealing.
- **Procedural Kinematics & Weapon Articulation**:
  - `stage3_build/procedural_animator.py`: Deterministic procedural animation generator with multi-stage attack arcs (-55° anticipation $\to$ -20° strike $\to$ +32° follow-through).
  - Dynamic procedural crescent slash VFX with glow core.
  - Decoupled weapon logic ensuring swinging blades are never rigidly anchored to back holsters.
- **Turnkey Interactive Web QA Viewer**:
  - `stage6_export/viewer_exporter.py`: Standalone zero-dependency HTML5 Canvas web viewer.
  - Real-time animation scrubber and FPS slider (1–60 FPS).
  - Web Audio API procedural sound synthesizer (whoosh, jump, footsteps, hit effects in pure code).
  - Visual QA overlays: Hitbox collision boxes, skeletal rig bones/pivots, and onion skinning.
  - Multi-engine code snippet exporter (Godot 4, Unity 2D, Phaser 3, PixiJS).
  - `grimoire/export/viewer_guide.md`: Complete operational guide.

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
