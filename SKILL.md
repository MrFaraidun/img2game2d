---
name: img2game2d
description: Convert character/object concept images, reference sheets, sketches, turnarounds, and existing 2D artwork into structured, game-ready 2D assets. Use for sprite sheets, skeletal rigs, animation clips, sprite atlases, and engine exports (Godot, Unity, Phaser, PixiJS).
license: Apache-2.0
version: 1.0.0
---

# img2game2d — Image to 2D Game Asset

Converts any 2D reference image into production-ready game assets through a **staged,
evidence-gated pipeline** with structured intermediate data at every step.

This is NOT a simple "image → sprite sheet" tool. It is a structured agent skill with:
- Visual understanding before generation
- Deterministic Python scripts for all non-AI steps
- AI for interpretation, decomposition, and frame generation only
- Validation and repair loops
- Incremental caching
- Engine-specific exporters

Agent-agnostic: works under Claude Code, Codex, or OpenCode.

---

## When To Use

Activate this skill when the user:
- Provides a concept art / character sheet / reference image and wants game assets
- Provides a multi-pose Action Sheet (e.g. 5 poses: idle, walk, jump, attack, hurt on one canvas)
- Needs sprite sheets, animation frames, sprite atlases
- Needs Godot `.tscn`, Unity prefab stubs, Phaser/PixiJS atlas JSON
- Wants a skeletal rig JSON from a 2D character reference
- Needs layer decomposition of a character into head/body/arms/etc.
- Asks for "game-ready sprites" from any 2D artwork

## When NOT To Use Certain Stages

```
If input is an action sheet (5 poses: idle, walk, jump, attack, hurt):
    run detect_actions.py first (or build --action-sheet).
    Extracts ground-truth artist poses directly into animation clips.

If input is already a clean sprite sheet:
    skip Stage 3 (layer extraction) and Stage 2 decomposition.
    Proceed directly to Stage 5 (atlas packing).

If input is pixel art:
    set style: pixel_art.
    Do NOT apply smoothing, anti-aliasing, or style transfer.
    Use nearest-neighbor scaling only.

If input contains a turnaround sheet:
    run detect_views.py first.
    Use all detected views to improve consistency.

If user requests only static sprite:
    skip Stage 3 animation generation entirely.

If asset is an effect (slash, hit, explosion):
    skip rig generation (Stage 2 rig).
    Generate frame animation only.

If user provides pre-separated layers:
    skip Stage 2 decomposition.
    Proceed to Stage 3 with provided layers.
```

---

## Mandatory Local State Gate

`.img2game2d/state.json` is the checklist authority for every project.
**Always run `next.py` first** before ANY other step.

```bash
# Initialize state for a new project
python3 forge/state.py init \
  --state .img2game2d/state.json \
  --reference character.png \
  --profile character   # or: object, effect

# Query next step
python3 forge/next.py --state .img2game2d/state.json

# Mark a step complete with evidence
python3 forge/state.py mark <step-id> \
  --state .img2game2d/state.json \
  --evidence <path>
```

Exit code 3 or `status=stopped` = hard stop. Report reason. Never continue from memory.

---

## Pipeline Stages

### Stage 1 — Intake

Read `grimoire/intake/image_analysis.md` before this stage.

```bash
# 0. Pre-Flight Quality Gate (Assess suitability, detect border clipping & generate prompt if bad)
python3 forge/stage1_intake/assess_quality.py character.png
# Or: python3 forge/cli.py check character.png

# 1. (Optional) Enhance character resolution, ink lines & clarity
python3 forge/stage1_intake/enhance.py character.png \
  --out source/enhanced.png \
  --scale 2.0 \
  --clarity 1.3

# 2. Probe image metadata
python3 forge/stage1_intake/probe_image.py character.png

# 3. Detect art style
python3 forge/stage1_intake/detect_style.py character.png --out analysis/style.json

# 4. Detect views (front/side/back/turnaround)
python3 forge/stage1_intake/detect_views.py character.png --out analysis/views.json

# 5. Detect & slice action poses (if providing a 5-pose action sheet)
python3 forge/stage1_intake/detect_actions.py action_sheet.png --out source/poses/

# 6. Remove background (with auto-defringing to eliminate white alpha halos)
python3 forge/stage1_intake/remove_background.py character.png \
  --out source/foreground.png \
  --mask source/mask.png
```

After scripts: perform **agent visual analysis** using `prompts/analyze.md`.
Produce `analysis/analysis.json` covering all fields in `schemas/asset.schema.json`.

### Stage 2 — Spec

Read `grimoire/spec/layer_contract.md` and `grimoire/spec/pivot_system.md`.

```bash
# Generate asset spec from analysis
python3 forge/stage2_spec/new_asset_spec.py \
  --analysis analysis/analysis.json \
  --style analysis/style.json \
  --out asset.json

# Validate spec
python3 forge/stage2_spec/validate_asset_spec.py asset.json

# Decompose into layers
python3 forge/stage2_spec/layer_decompose.py asset.json \
  --out layers/layer-spec.json

# Build rig (skip for effects and simple objects)
python3 forge/stage2_spec/build_rig.py layers/layer-spec.json \
  --out metadata/rig.json
```

### Stage 3 — Build

Read `grimoire/build/layer_extraction.md`.

```bash
# Extract individual layers as PNGs
python3 forge/stage3_build/extract_layers.py \
  --source source/foreground.png \
  --spec layers/layer-spec.json \
  --out layers/

# Reconstruct occluded regions (if needed)
python3 forge/stage3_build/reconstruct_occlusion.py \
  --spec layers/layer-spec.json \
  --layers layers/ \
  --out layers/

# Generate animation frames (Procedural Kinematics or AI stage)
python3 forge/stage3_build/generate_frames.py \
  --reference source/foreground.png \
  --spec asset.json \
  --provider procedural \
  --animations idle,walk,jump,attack,hurt \
  --out animations/

# Or run direct procedural generator:
python3 forge/stage3_build/procedural_animator.py \
  --source source/foreground.png \
  --spec layers/layer-spec.json \
  --animations idle,walk,jump,attack,hurt \
  --out animations/
```

### Stage 4 — Review

Read `grimoire/review/gates_reference.md` BEFORE any review.

```bash
# Silhouette validation
python3 forge/stage4_review/validate_silhouette.py \
  --reference source/original.png \
  --frames animations/idle/ \
  --out analysis/silhouette_check.json

# Color consistency
python3 forge/stage4_review/validate_colors.py \
  --reference source/original.png \
  --frames animations/ \
  --out analysis/color_check.json

# Frame continuity
python3 forge/stage4_review/validate_continuity.py \
  --frames animations/ \
  --out analysis/continuity_check.json

# Generate comparison sheet
python3 forge/stage4_review/make_comparison_sheet.py \
  --reference source/original.png \
  --frames animations/idle/ \
  --out analysis/comparison.png

# Record review
python3 forge/stage4_review/append_review.py asset.json \
  --stage review \
  --silhouette 0.94 \
  --colors 0.97 \
  --continuity 0.91 \
  --action continue
```

If any score < threshold: run `repair` stage using `prompts/repair.md`.
Repair loop limit: 3 iterations per stage, 6 total.

### Stage 5 — Atlas

```bash
# Pack sprite atlas
python3 forge/stage5_atlas/pack_atlas.py \
  --frames animations/ \
  --out atlases/ \
  --max-width 2048 \
  --max-height 2048 \
  --padding 2 \
  --power-of-two

# Generate row-based sprite sheet
python3 forge/stage5_atlas/generate_spritesheet.py \
  --frames animations/idle/ \
  --out atlases/idle_sheet.png \
  --json atlases/idle_sheet.json
```

### Stage 6 — Export

Read the relevant `grimoire/export/<engine>_guide.md`.

```bash
# Export to specific engine (godot, unity, phaser, pixijs, viewer)
python3 forge/stage6_export/export.py \
  --asset asset.json \
  --atlases atlases/ \
  --engine godot \
  --out exports/godot/

# Interactive Web QA Viewer (Canvas 2D + Web Audio Synthesizer)
python3 forge/stage6_export/export.py \
  --asset asset.json \
  --atlases atlases/ \
  --engine viewer \
  --out exports/viewer/

# All engines (includes Web QA viewer)
python3 forge/stage6_export/export.py \
  --asset asset.json \
  --atlases atlases/ \
  --engine all \
  --out exports/
```

---

## 5 Production Pillars of 2D Asset Engineering

1. **Zero-Halo Alpha De-Matting & Defringing Protocol**:
   Never trust naive alpha masks. Anti-aliasing against white/bright backgrounds causes unsightly white halo borders. Always run dual-contour luminance checking and edge tone-shifting (`forge/_shared/image_utils.py:defringe_alpha`).
2. **Exact Inverse-Affine Coordinate Calculus**:
   PIL `Image.transform(AFFINE)` maps output pixels to input coordinates. Always compute the exact inverse affine matrix around pivots (`forge/_shared/transforms.py:get_inverse_affine_matrix`). Never use forward rotation matrices.
3. **Non-Linear Continuous Shear Deformation**:
   Characters with contiguous bodies, robes, or capes will break apart if severed into rigid rectangular boxes. Use continuous vertical shear deformation (`apply_continuous_shear`) to produce fluid walking cycles without anatomical tearing.
4. **Decoupled Weapon Articulation & Crescent Slash VFX**:
   Handheld weapons must never be baked into torso/cloak back-holsters. Separate the blade layer and articulate it through dynamic swing arcs (-55° anticipation $\to$ -20° lunging strike $\to$ +32° follow-through) composited with glowing crescent slash VFX (`procedural_animator.py`).
5. **Turnkey Interactive Web QA Viewer**:
   Every asset export must be immediately verifiable via a standalone, zero-dependency HTML5 Canvas web viewer with Web Audio API procedural sound synthesis (whoosh, jump, footsteps, hit), hitbox overlays, and skeletal rig visualizers (`forge/stage6_export/viewer_exporter.py`).

---

## Output Structure

```
game-asset/
├── source/
│   ├── original.png          # Untouched input (never modified)
│   ├── foreground.png        # BG-removed
│   └── mask.png
├── analysis/
│   ├── analysis.json         # Full visual analysis
│   ├── style.json
│   ├── views.json
│   ├── silhouette_check.json
│   ├── color_check.json
│   └── continuity_check.json
├── layers/
│   ├── layer-spec.json       # Layer definition with pivots
│   ├── head.png
│   ├── body.png
│   └── ...
├── animations/
│   ├── idle/
│   │   ├── 000.png ... N.png
│   ├── walk/
│   └── attack/
├── atlases/
│   ├── idle.png
│   ├── idle.json
│   └── ...
├── metadata/
│   ├── character.json
│   ├── rig.json
│   └── animations.json
├── exports/
│   ├── godot/
│   ├── unity/
│   ├── phaser/
│   └── pixijs/
└── README.md
```

---

## Required Inputs

- One image path (concept art / reference sheet / turnaround / existing sprite)
- Intended asset type: `character`, `object`, `effect` (agent may detect if omitted)
- Target engine(s): `godot`, `unity`, `phaser`, `pixijs`, `all` (default: all)
- Target resolution: 32 / 64 / 128 / 256 / 512 / 1024 (default: preserve source)

---

## Validation Thresholds

Default thresholds (configurable in project config):
```yaml
validation:
  silhouette_min: 0.85
  color_consistency_min: 0.90
  frame_continuity_min: 0.88
  part_consistency_min: 0.90
```

Below threshold → enter repair loop. After 3 repair iterations → stop and report.

---

## Self-Correction

After every review stage, choose exactly one:
`continue | refine-spec | refine-frames | request-input | stop`

- `refine-spec` — fix layer decomposition or animation spec
- `refine-frames` — regenerate failing frames only
- `request-input` — need more views / cleaner reference
- `stop` — cannot reach requested quality from this image

Read `grimoire/review/self_correction.md` before deciding.

---

## Transparency Rules

- Never claim "done" when only "improved"
- Report what changed after each repair with evidence (scores before/after)
- Name what still doesn't match reference
- A passing threshold is not proof of artistic quality

---

## Output (brief)

- **Analysis-only** (`img2game2d analyze`): asset type, style, views, parts list, layer hierarchy, pivot system, animation feasibility
- **Full build** (`img2game2d build`): all output directories populated, metadata valid, atlases packed, exports generated
- **Not feasible**: name the blocker. "Cannot extract clean layers from this image" is a valid result.
