# img2game2d v3 — Architectural Milestone Plan

This document establishes the roadmap, architectural contracts, and delivery milestones for **img2game2d v3: Production 2D Game Asset Compiler**.

---

## Roadmap Overview

```text
V3.0 (Foundation & AssetIR) ──> V3.1 (Perception Layer) ──> V3.2 (Rigging & IK)
                                                                 │
V3.5 (Validation & Quality) <── V3.4 (GPU & WebGL2) <── V3.3 (Deformation)
     │
     └──> V3.6 (Studio Workstation) ──> V3.7 (Engine Exporters) ──> V3.8 (Ecosystem & Benchmark)
```

---

## Milestone V3.0: Foundation & Canonical AssetIR

### Scope
- Design and implement the canonical, engine-neutral Intermediate Representation (**AssetIR**).
- Establish strict schema versioning (SemVer) and data migration protocols.
- Implement comprehensive structural and semantic validation producing actionable diagnostic objects (`DiagnosticIR`).
- Define explicit coordinate system definitions and bi-directional transform math (Canvas, World, Spine, Normalized UV).
- Implement standard project manifest (`*.img2game2d.json`) loading and persistence.
- Implement backwards compatibility layer for existing `forge/` scripts and workflows.
- Implement converter from legacy `character.json` and TexturePacker atlases to canonical AssetIR.

### Dependencies
- Python 3.10+ standard library (`dataclasses`, `typing`, `json`, `math`, `pathlib`, `unittest`).
- TypeScript 5.x / 6.x in `studio/`.

### Acceptance Criteria
- [x] Zero external dependencies required for core AssetIR validation and serialization.
- [x] Complete round-trip serialization: `AssetIR -> JSON -> AssetIR` produces identical object graphs.
- [x] Coordinate transforms satisfy inverse identity: `world_to_canvas(canvas_to_world(p)) == p`.
- [x] Validators detect structural flaws (empty frames, invalid pivots, disconnected bone parents, unnormalized weights) with machine-readable error codes.
- [x] Existing scripts (`pipeline.py`, `dematting.py`, `lighting.py`, `export_spine.py`) run unmodified.
- [x] Studio builds cleanly with new type contracts (`npm run build`).

### Tests
- `tests/test_asset_ir.py`: Serialization, deserialization, schema validation.
- `tests/test_transforms.py`: Coordinate transform invariance and precision.
- `tests/test_converter.py`: Lossless conversion from legacy character data.

### Risks & Mitigations
- *Risk:* Divergence between Python AssetIR and TypeScript Studio types.
  *Mitigation:* Co-located schemas and automated type tests mirroring properties 1:1.
- *Risk:* Breaking legacy CLI invocations in existing pipelines.
  *Mitigation:* Dedicated `forge/cli.py` facade delegating to legacy scripts when old syntax is invoked.

### Rollback Strategy
AssetIR operates additively under `core/asset_ir/`. If needed, legacy scripts continue running directly without touching `core/`.

---

## Milestone V3.1: Intelligent Perception Layer

### Scope
- Multi-mode sprite sheet discovery (horizontal, vertical, irregular grid, multi-character).
- Automated background detection and adaptive foreground masking.
- Connected component clustering and character boundary proposals.
- Optional SAM 2 (Segment Anything Model 2) backend with graceful OpenCV/contour fallback.
- Pose and keypoint backend interface (local MediaPipe / RTMPose / heuristic joint detection).
- Semantic-part segmentation (head, torso, upper/lower arms, hands, legs, feet, accessories/weapons).
- Confidence scoring model:
  $$\text{Score} = 0.30 S_{\text{silhouette}} + 0.20 S_{\text{aspect}} + 0.20 S_{\text{pose}} + 0.15 S_{\text{color}} + 0.15 S_{\text{cluster}}$$

### Dependencies
- Milestone V3.0 (AssetIR).
- Optional: OpenCV (`cv2`), PyTorch (for SAM 2), MediaPipe.

### Acceptance Criteria
- Slices irregular sprite sheets without requiring manually hardcoded crop rectangles.
- SAM 2 backend is purely optional; system functions locally with standard OpenCV/NumPy.
- Low-confidence detections (< 0.70) generate `DiagnosticIR` warnings rather than false silent successes.
- Semantic parts map to canonical humanoid bone hierarchy.

### Tests
- Grid detection benchmarks on varied sprite sheets.
- Fallback assertions when deep learning models are absent.

### Risks & Mitigations
- *Risk:* Huge memory footprint or CUDA dependency from SAM 2.
  *Mitigation:* Strict Protocol-based backend interface; CPU fallback; lazy loading.

### Rollback Strategy
Manual crop configurations in `CHARACTER_CONFIGS` remain supported as explicit overrides.

---

## Milestone V3.2: Rigging & Constraint System

### Scope
- Normalized humanoid rig template parameterized by proportional body ratios.
- Silhouette skeletonization using medial axis transform and distance fields.
- Automatic joint fitting matching detected landmarks against rig templates.
- Analytical Two-Bone Inverse Kinematics (IK) solver with pole targets, bend directions, and joint limits.
- Foot locking constraint system (`FootPlantConstraint`) to eliminate foot sliding.
- Weapon aiming constraint system (`AimConstraint`) for mouse and target tracking.

### Dependencies
- Milestone V3.0 (AssetIR), Milestone V3.1 (Perception / Landmarks).

### Acceptance Criteria
- Analytical Two-Bone IK runs in $< 0.05\text{ ms}$ per chain in both TypeScript and Python.
- Joint angle limits clamp rotations deterministically without flipping singularities.
- Foot locking maintains world position across planted frame intervals, flagging `FOOT_SLIDE_ERROR` if ground drift occurs.

### Tests
- Property-based tests for IK solver reaching reachable targets within $10^{-4}$ tolerance.
- Singular / unreachable target clamping tests.

### Risks & Mitigations
- *Risk:* Singularities when target is at exact limb extension ($c = a + b$).
  *Mitigation:* Epsilon boundary clamping on triangle side length $c \le a + b - \varepsilon$.

---

## Milestone V3.3: 2D Mesh Generation & Skinning

### Scope
- Automatic Delaunay triangulation and boundary mesh generation from alpha masks.
- Heat and Euclidean distance-based vertex bone weight calculation.
- Weight normalization guaranteeing $\sum w_i = 1.0$ per vertex.
- Authoritative CPU reference skinning implementation ($v' = \sum w_i M_i v$).
- Preparation of vertex buffer data for GPU vertex shaders.

### Dependencies
- Milestone V3.0, Milestone V3.2 (Skeleton).

### Acceptance Criteria
- Generated meshes have valid indices with zero degenerate or inverted triangles.
- Validator strictly rejects vertices with $\left| \sum w_i - 1.0 \right| > 10^{-4}$.
- CPU skinning matches WebGL2 vertex shader transform outputs identically.

### Tests
- Mesh topology verification (Euler characteristic, boundary manifoldness).
- Weight normalization invariance tests.

---

## Milestone V3.4: GPU Rendering & Lighting Engine

### Scope
- WebGL2 multi-pass rendering pipeline (CanvasRenderer fallback retained).
- G-Buffer layout: Albedo, OpenGL Tangent Normal, Emission, Height.
- Multi-light support (8–32 simultaneous lights): Ambient, Directional, Point, Spot.
- 2D shadow system: Contour extraction, occluder polygon extrusion, shadow framebuffer.
- Height field generation via distance transform and edge-aware smoothing.
- Configurable normal mapping modes: Sobel, Distance-based bevel, Hybrid.

### Dependencies
- Milestone V3.0 (AssetIR), Milestone V3.3 (Meshes).

### Acceptance Criteria
- Interactive viewport achieves stable 60 FPS under 16 dynamic lights.
- Normal and emission maps match Godot 4 CanvasItem and Unity 2D URP specifications.
- Directional and point light shadows cast realistically without self-intersection artifacts.

### Tests
- Framebuffer readback assertions against reference renders.
- Headless WebGL2 context initialization test.

---

## Milestone V3.5: Validation, Golden Images & Diagnostics

### Scope
- Three-tier validation engine: Structural, Visual, Engine Runtime.
- Visual regression framework: Golden image comparisons (Pixel error, SSIM, PSNR, Alpha delta).
- Engine runtime validation:
  - Headless Godot 4 verification: `godot --headless --path test_project --editor --quit`.
  - Headless Unity batchmode verification: Prefab instantiation, sprite loading, controller validation.
- "Fix this asset" auto-remediation engine for `GROUND_DRIFT`, `ALPHA_HALO`, and `PIVOT_ERROR`.

### Dependencies
- Milestone V3.0 through V3.4.

### Acceptance Criteria
- Visual regression catches $\ge 1\text{ px}$ pivot shifts or $\ge 1\%$ alpha halo regressions.
- Headless engine runners fail CI if imported scenes trigger engine errors or missing resource warnings.
- Diagnostics provide actionable `suggestedFix` properties for all warning/error codes.

### Tests
- Test cases injecting deliberate errors (broken bone, bad UV, halo) verifying diagnostic triggers.

---

## Milestone V3.6: Studio Workstation Upgrade

### Scope
- Interactive Asset Graph (Source -> Mask -> Layers -> Rig -> Animation -> Material -> Atlas -> Export).
- Reversible Command Pattern (`Command`, `History` undo/redo stack) for all editing operations.
- Interactive Rig Editor with Two-Bone IK drag handles and bone angle limits.
- Collision & Hurtbox/Hitbox polygon editor.
- Animation Curve Editor with Bezier tangent controls.
- Asset diagnostics inspection panel with one-click "Auto Fix".
- Local project persistence (`*.img2game2d.json`).

### Dependencies
- Milestone V3.0 through V3.5.

### Acceptance Criteria
- Unlimited undo/redo stack without mutating raw source assets.
- Asset Graph nodes reflect real-time validity status (`VALID`, `WARNING`, `ERROR`).
- Zero full-page React re-renders on pointer/gizmo manipulation.

### Tests
- Command execution and undo identity tests in Studio.
- Component snapshot and interaction tests.

---

## Milestone V3.7: Multi-Engine Exporters & Packaging

### Scope
- Uniform Exporter interface: `export(asset_ir, options) -> ExportResult`.
- Targets:
  1. Godot 4.x (CharacterBody2D, AnimatedSprite2D, SpriteFrames .tres, .tscn).
  2. Unity (2D URP Prefab, Sprite Atlas, Animation Clips).
  3. Spine 2D (official skeleton.json v3.8/v4.x, .atlas, attachments).
  4. Bevy (Rust sprite animation resources, texture atlases, component bundles).
  5. Defold (Atlas and `.animationset` resources).
  6. Unreal Engine / PaperZD (Paper2D sprites, flipbooks, integration metadata).
  7. Phaser 3 / PixiJS (TexturePacker JSON Hash & Array).
- Exporters consume AssetIR exclusively and never modify source files.

### Dependencies
- Milestone V3.0 (AssetIR).

### Acceptance Criteria
- Every export package includes a manifest, output assets, and an engine-specific validation report.
- Exported scenes and prefabs open without manual adjustments in clean target projects.

### Tests
- Golden manifest validation for each engine export target.

---

## Milestone V3.8: Benchmark Suite & Ecosystem Distribution

### Scope
- Benchmark test corpus spanning 15 asset categories (humanoid, monster, animal, pixel art, anime, painted, overlapping limbs, weapons).
- Benchmark metrics: Mask IoU, Part IoU, Pose Accuracy, Pivot Error, Ground Drift, Atlas Efficiency.
- Packaging for distribution:
  - Python: `pyproject.toml` publishing `img2game2d` CLI.
  - npm: `@img2game2d/schema` and `@img2game2d/studio`.
- Agent-first CLI command suite: `inspect`, `detect`, `segment`, `rig`, `animate`, `light`, `atlas`, `validate`, `export` with `--json`.
- Complete documentation overhaul and showcase assets.

### Dependencies
- Milestones V3.0 through V3.7.

### Acceptance Criteria
- `img2game2d benchmark --json` executes across the suite and reports machine-readable accuracy scores.
- `pip install img2game2d` and `npx img2game2d` function seamlessly.
