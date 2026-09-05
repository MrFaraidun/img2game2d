# Standalone Interactive Web QA Viewer Guide

## Overview
The `viewer` exporter produces a zero-dependency, local HTML5 Canvas web application designed for instant visual verification, animation testing, and engine code generation.

## Key Capabilities

1. **Real-Time Animation Playback**:
   - Scrub through individual frames with timeline slider.
   - Adjust playback rate from 1 to 60 FPS in real time.
   - Instant clip switching (`idle`, `walk`, `jump`, `attack`, `hurt`).

2. **Web Audio API Procedural SFX Synthesizer**:
   - Synthesizes dynamic sound effects in pure JavaScript without external audio assets:
     - **Whoosh**: Frequency sweep + noise filter for weapon swings (`attack`).
     - **Footsteps**: Soft ground impact pops for locomotion (`walk`).
     - **Jump**: Ascending pitch sweep for liftoff (`jump`).
     - **Hit**: Crunchy impact transient for damage recoil (`hurt`).

3. **Visual QA Diagnostic Overlays**:
   - **Hitbox Toggle**: Renders bounding collision envelopes for combat alignment.
   - **Rig Bones Toggle**: Overlays skeletal hierarchies, joints, and pivot anchors.
   - **Onion Skinning**: Renders translucent ghost previews of adjacent frames to verify motion arc continuity.

4. **Engine Code Generation**:
   - One-click access to copy-pasteable script templates for:
     - **Godot 4** (`CharacterBody2D` & `AnimatedSprite2D`)
     - **Unity 2D** (`MonoBehaviour` Animator controller)
     - **Phaser 3** (`this.anims.create`)
     - **PixiJS** (`PIXI.AnimatedSprite`)

## Usage

```bash
# Export viewer as part of full build
python3 forge/cli.py build character.png --engine viewer --out dist/

# Or generate viewer independently from existing assets
python3 forge/stage6_export/viewer_exporter.py \
  --asset dist/asset.json \
  --animations dist/animations/ \
  --out dist/viewer/

# Serve and view locally
python3 -m http.server 8080 --directory dist/viewer
```
