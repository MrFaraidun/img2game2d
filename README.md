# img2game2d — Image-to-2D-Game-Asset Agent Skill

> Production-ready AI agent skill and CLI tool converting concept art, sketches, reference sheets, and 2D artwork into structured, game-ready 2D assets with layers, rigs, animation frames, texture atlases, and engine exporters (Godot 4, Unity, Phaser 3, PixiJS).

---

## Highlights

- **Structured Reasoning**: Rather than generating noisy monolithic sprite sheets, `img2game2d` uses a staged pipeline: visual intake → asset specification → layer decomposition & rigging → frame generation → quality review & repair → atlas packing → engine export.
- **Deterministic Tooling**: Python scripts for image processing, background removal, layer cropping, IoU evaluation, and atlas packing.
- **Local State Gate**: Built-in state machine (`.img2game2d/state.json`) and step gate (`next.py`) preventing blind skips or hallucinated completions.
- **Strict Quality Gates**: Automated validation for Silhouette IoU ($\ge 0.85$), Color Consistency ($\ge 0.90$), and Frame-to-Frame Continuity ($\ge 0.88$) with guided repair loops.
- **Multi-Engine Ready**: First-class exports for Godot 4 (`.tscn` + `.tres`), Unity (`AnimatorController` + sliced sprite metadata), Phaser 3 (TexturePacker atlas + TypeScript loader), and PixiJS (`AnimatedSprite` factory + JSON).
- **Offline & Incremental**: Standard library, Pillow, and NumPy first; SHA-256 build cache prevents redundant re-generation.

---

## Pipeline Architecture

```
Reference Image
      ↓
[Stage 1: Intake]   ── probe_image ── detect_style ── detect_views ── remove_background
      ↓
[Stage 2: Spec]     ── new_asset_spec ── validate_asset_spec ── layer_decompose ── build_rig
      ↓
[Stage 3: Build]    ── extract_layers ── reconstruct_occlusion ── generate_frames
      ↓
[Stage 4: Review]   ── validate_silhouette ── validate_colors ── validate_continuity ── append_review
      ↓
[Stage 5: Atlas]    ── pack_atlas (power-of-2 bin-packing) ── generate_spritesheet
      ↓
[Stage 6: Export]   ── godot_exporter / unity_exporter / phaser_exporter / pixijs_exporter
```

---

## Directory Structure

```
img2game2d/
├── SKILL.md                        # Primary agent instruction file
├── README.md                       # Documentation and usage guide
├── CHANGELOG.md                    # Release history
├── LICENSE                         # Apache-2.0
├── schemas/                        # JSON Schema validation definitions
│   ├── asset.schema.json
│   ├── layer.schema.json
│   ├── rig.schema.json
│   ├── animation.schema.json
│   └── project.schema.json
├── forge/                          # Deterministic executable scripts
│   ├── next.py                     # State gate check
│   ├── state.py                    # State machine controller
│   ├── _shared/                    # Shared image, cache, and schema utilities
│   ├── stage1_intake/              # Image probe, style & view detection, BG removal
│   ├── stage2_spec/                # Asset spec, layer decomposition, rigging
│   ├── stage3_build/               # Layer extraction, occlusion, frame generation
│   ├── stage4_review/              # Silhouette, color, continuity validation gates
│   ├── stage5_atlas/               # Atlas packer and sprite sheet generators
│   ├── stage6_export/              # Godot, Unity, Phaser, PixiJS exporters
│   └── tests/                      # Automated test suite
├── grimoire/                       # 16 on-demand protocol documents
│   ├── intake/                     # Visual analysis, view detection, style guides
│   ├── spec/                       # Layer, pivot, rig, and animation contracts
│   ├── build/                      # Extraction, occlusion, animation quality guides
│   ├── review/                     # Gates reference and self-correction repair protocol
│   └── export/                     # Engine integration guides (Godot, Unity, Phaser, PixiJS)
├── prompts/                        # Structured AI prompt templates
│   ├── analyze.md
│   ├── decompose.md
│   ├── reconstruct.md
│   ├── animate.md
│   ├── validate.md
│   └── repair.md
├── templates/                      # Production configuration templates
│   ├── project.yaml
│   ├── asset.json
│   └── animation.json
└── examples/
    └── knight/                     # End-to-end example project
```

---

## Installation & Requirements

Python 3.9+ is required.

```bash
pip install Pillow numpy jsonschema
```

Optional dependencies:
- `rembg` (high-fidelity AI background removal)
- `openai` (for AI frame generation providers)

---

## Quick Start (Forge Workflow)

### 1. Initialize State
```bash
python3 forge/state.py init \
  --state .img2game2d/state.json \
  --reference concept.png \
  --profile character
```

### 2. Query Next Step
```bash
python3 forge/next.py --state .img2game2d/state.json
```

### 3. Execute Intake Stage
```bash
# Probe image
python3 forge/stage1_intake/probe_image.py concept.png

# Detect style and turnaround views
python3 forge/stage1_intake/detect_style.py concept.png --out analysis/style.json
python3 forge/stage1_intake/detect_views.py concept.png --out analysis/views.json

# Extract foreground
python3 forge/stage1_intake/remove_background.py concept.png \
  --out source/foreground.png \
  --mask source/mask.png
```

### 4. Create Spec & Rig
```bash
# Build asset spec
python3 forge/stage2_spec/new_asset_spec.py \
  --analysis analysis/analysis.json \
  --out asset.json

# Validate against schema
python3 forge/stage2_spec/validate_asset_spec.py asset.json

# Decompose layers and build skeletal rig
python3 forge/stage2_spec/layer_decompose.py asset.json --out layers/layer-spec.json
python3 forge/stage2_spec/build_rig.py layers/layer-spec.json --out metadata/rig.json
```

### 5. Build Layers & Animations
```bash
# Extract layers and inpaint occluded textures
python3 forge/stage3_build/extract_layers.py \
  --source source/foreground.png \
  --spec layers/layer-spec.json \
  --out layers/

python3 forge/stage3_build/reconstruct_occlusion.py \
  --spec layers/layer-spec.json \
  --layers layers/ \
  --out layers/

# Generate animation frames (stub, openai, or custom generator)
python3 forge/stage3_build/generate_frames.py \
  --reference source/foreground.png \
  --spec asset.json \
  --animations idle,walk,attack \
  --out animations/ \
  --provider stub
```

### 6. Review Against Quality Gates
```bash
# Check silhouette IoU (>= 0.85)
python3 forge/stage4_review/validate_silhouette.py \
  --reference source/foreground.png \
  --frames animations/idle/ \
  --out analysis/silhouette_check.json

# Check color palette consistency (>= 0.90)
python3 forge/stage4_review/validate_colors.py \
  --reference source/foreground.png \
  --frames animations/ \
  --out analysis/color_check.json

# Check frame continuity (>= 0.88)
python3 forge/stage4_review/validate_continuity.py \
  --frames animations/ \
  --out analysis/continuity_check.json

# Generate comparison sheet
python3 forge/stage4_review/make_comparison_sheet.py \
  --reference source/foreground.png \
  --frames animations/idle/ \
  --out analysis/comparison.png
```

### 7. Pack Atlases & Export
```bash
# Pack TexturePacker-compatible power-of-two atlases
python3 forge/stage5_atlas/pack_atlas.py \
  --frames animations/ \
  --out atlases/ \
  --power-of-two

# Export to all game engines
python3 forge/stage6_export/export.py \
  --asset asset.json \
  --atlases atlases/ \
  --engine all \
  --out exports/
```

---

## Supported Game Engines

| Engine | Generated Output | Key Features |
|---|---|---|
| **Godot 4** | `<Name>.tscn`, `<Name>_frames.tres` | Configured `AnimatedSprite2D`, auto-playing idle, full clip definitions |
| **Unity** | `<Name>_sprites/`, `<Name>_atlas.json`, `<Name>_animator.json` | Grid slice coordinates, AnimatorController state machine layout |
| **Phaser 3** | `atlases/*.png`, `<id>.json`, `<id>.ts` | TexturePacker JSON, typed TypeScript preload and animation factory |
| **PixiJS** | `atlases/*.png`, `<id>_<clip>.json`, `<id>.ts` | Multi-spritesheet JSON, `PIXI.AnimatedSprite` TypeScript factory |

---

## Testing

Run the test suite across all stages:
```bash
python3 -m pytest forge/tests/test_all.py -v
```

All 21 comprehensive test cases cover:
- JSON Schema offline validation
- Image probing, art style, and view detection
- Layer decomposition and skeletal rig generation
- Frame generation and power-of-two atlas packing
- Exporters for Godot, Unity, Phaser, and PixiJS
- Incremental hash caching and invalidation

---

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
