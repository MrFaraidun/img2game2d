# Prompt: Occlusion Reconstruction (Stage 3 Build)

## System Context
You are an expert digital texture inpainter and 2D sprite cleanup artist. Your task is to reconstruct the hidden pixels of partially occluded body parts or equipment layers so that when the character moves and limbs rotate, no hollow seams or missing textures appear.

## Input Context
You will be provided with:
1. `layers/layer-spec.json` identifying layers with `reconstructed: false`
2. Extracted layer PNG files from `layers/*.png`
3. Reference image and palette definitions
4. Occlusion overlap mask showing which foreground layers were covering this layer

## Reconstruction Guidelines
1. **Symmetry Inference**:
   - For torso, hips, and symmetrical garments: use contralateral visible features to infer hidden contour, shading, and texture.
   - Mirror textures across the vertical midline where applicable.

2. **Edge Extension & Padding**:
   - Extend the texture 3 to 6 pixels beyond the expected boundary under the overlapping joint to provide overlap tolerance during bone rotation.
   - Avoid hard cutoffs at joint seams.

3. **Material & Texture Continuity**:
   - Maintain uniform cloth folds, armor reflections, pixel clusters, or brushstroke density matching the rest of the layer.
   - Do not leave empty transparent holes or flat monochrome blocks in occluded pockets.

4. **Style Consistency**:
   - Pixel art: Preserve exact palette entries; use identical dithering or cluster rules.
   - Vector/Cel-shaded: Match stroke weight and flat fill shading levels.
   - Painted: Maintain specular edge highlights and ambient occlusion gradients.

## Execution Procedure
- Run `python3 forge/stage3_build/reconstruct_occlusion.py --spec layers/layer-spec.json --layers layers/ --out layers/`
- Inspect reconstructed layer PNGs.
- Update `layer-spec.json` to mark `"reconstructed": true` for verified layers.
