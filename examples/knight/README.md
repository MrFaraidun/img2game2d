# Knight Example Project

This walkthrough demonstrates the end-to-end processing of `reference.png` using the `img2game2d` pipeline.

---

## Input Reference

- **File**: `reference.png` (256×256 pixel art sprite)
- **Character**: Armored knight with helmet, chestplate, arms, and legs.

---

## Step-by-Step Execution

### 1. Initialize Pipeline State
```bash
python3 forge/state.py init \
  --state examples/knight/.img2game2d/state.json \
  --reference examples/knight/reference.png \
  --profile character
```

### 2. Run Intake Stage
```bash
# Probe image
python3 forge/stage1_intake/probe_image.py examples/knight/reference.png

# Detect art style
python3 forge/stage1_intake/detect_style.py examples/knight/reference.png \
  --out examples/knight/analysis/style.json

# Detect turnaround views
python3 forge/stage1_intake/detect_views.py examples/knight/reference.png \
  --out examples/knight/analysis/views.json

# Remove background / isolate foreground
python3 forge/stage1_intake/remove_background.py examples/knight/reference.png \
  --out examples/knight/source/foreground.png \
  --mask examples/knight/source/mask.png
```

### 3. Generate Specification & Skeletal Rig
```bash
# Build asset spec
python3 forge/stage2_spec/new_asset_spec.py \
  --analysis examples/knight/analysis/analysis.json \
  --style examples/knight/analysis/style.json \
  --out examples/knight/asset.json

# Validate against asset.schema.json
python3 forge/stage2_spec/validate_asset_spec.py examples/knight/asset.json

# Decompose into layers and compute rig
python3 forge/stage2_spec/layer_decompose.py examples/knight/asset.json \
  --out examples/knight/layers/layer-spec.json

python3 forge/stage2_spec/build_rig.py examples/knight/layers/layer-spec.json \
  --out examples/knight/metadata/rig.json
```

### 4. Build Layers & Animations
```bash
# Extract layers
python3 forge/stage3_build/extract_layers.py \
  --source examples/knight/source/foreground.png \
  --spec examples/knight/layers/layer-spec.json \
  --out examples/knight/layers/

# Reconstruct occluded joints
python3 forge/stage3_build/reconstruct_occlusion.py \
  --spec examples/knight/layers/layer-spec.json \
  --layers examples/knight/layers/ \
  --out examples/knight/layers/

# Generate animation frames
python3 forge/stage3_build/generate_frames.py \
  --reference examples/knight/source/foreground.png \
  --spec examples/knight/asset.json \
  --animations idle,walk,attack \
  --out examples/knight/animations/ \
  --provider stub
```

### 5. Review Quality Gates
```bash
# Validate silhouette IoU (>= 0.85)
python3 forge/stage4_review/validate_silhouette.py \
  --reference examples/knight/source/foreground.png \
  --frames examples/knight/animations/idle/ \
  --out examples/knight/analysis/silhouette_check.json

# Review comparison sheet
python3 forge/stage4_review/make_comparison_sheet.py \
  --reference examples/knight/source/foreground.png \
  --frames examples/knight/animations/idle/ \
  --out examples/knight/analysis/comparison.png
```

### 6. Pack Atlases & Export
```bash
# Pack power-of-two texture atlases
python3 forge/stage5_atlas/pack_atlas.py \
  --frames examples/knight/animations/ \
  --out examples/knight/atlases/ \
  --power-of-two

# Export to all game engines
python3 forge/stage6_export/export.py \
  --asset examples/knight/asset.json \
  --atlases examples/knight/atlases/ \
  --engine all \
  --out examples/knight/exports/
```

---

## Output Result

When complete, the following outputs are generated:
- `exports/godot/`: `Knight.tscn` scene with `AnimatedSprite2D` and `Knight_frames.tres`
- `exports/unity/`: Sliced sprite PNGs, `Knight_atlas.json`, and `Knight_animator.json`
- `exports/phaser/`: `knight.json` atlas metadata and `knight.ts` TypeScript loader
- `exports/pixijs/`: Spritesheets per clip and `knight.ts` `PIXI.AnimatedSprite` factory
