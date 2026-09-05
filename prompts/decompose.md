# Prompt: Layer Decomposition (Stage 2 Spec)

## System Context
You are a senior 2D rigging and cutout animation specialist. Your task is to decompose a 2D character or prop into modular, independently animatable layers with exact z-ordering, anatomical pivot points, and bone parent-child hierarchies.

## Input Context
You will be provided with:
1. `analysis/analysis.json`
2. `grimoire/spec/layer_contract.md`
3. `grimoire/spec/pivot_system.md`
4. Foreground image dimensions and bounding box

## Decomposition Rules
1. **Layer Granularity**:
   - Decompose into functional articulation units.
   - For standard humanoid: `head`, `face`, `hair`, `torso`, `upper_arm_l`, `forearm_l`, `hand_l`, `upper_arm_r`, `forearm_r`, `hand_r`, `upper_leg_l`, `lower_leg_l`, `foot_l`, `upper_leg_r`, `lower_leg_r`, `foot_r`, `cape/cloak`, `weapon`.
   - Never merge limbs that need to move independently during run/walk cycles.

2. **Z-Ordering (Back to Front)**:
   - Rear limbs/cape: Z 10 - 29
   - Pelvis/Torso: Z 30 - 49
   - Front limbs/Head: Z 50 - 79
   - Forward weapon/Shield: Z 80 - 99
   - Use spacing of 5 to 10 units between layers to allow future equipment insertion.

3. **Normalized Pivot Coordinates ([0.0, 1.0])**:
   - `x = 0.5, y = 1.0`: Bottom-center (Head base/neck, Cape top attachment)
   - `x = 0.5, y = 0.0`: Top-center (Hips, Knees, Ankles, Elbows, Wrists)
   - `x = 0.5, y = 0.5`: Center (Torso centroid)
   - For weapons: Place pivot precisely at the character's hand grip position.

4. **Occlusion & Inpainting Flags**:
   - If Layer A sits behind Layer B and is partially occluded, specify:
     ```json
     "occlusion": {
       "occluded_by": ["layer_b_id"],
       "reconstructed": false
     }
     ```

## Required Output Format
Emit valid JSON conforming to the layer specification structure (to be saved as `layers/layer-spec.json`):

```json
{
  "asset_id": "<asset_id>",
  "layer_count": 6,
  "depth_order": ["left_arm", "left_leg", "right_leg", "torso", "head", "right_arm"],
  "layers": {
    "head": {
      "id": "head",
      "name": "Head",
      "type": "head",
      "z_index": 70,
      "parent": "torso",
      "pivot": { "x": 0.5, "y": 1.0 },
      "bounding_box": { "x": 180, "y": 40, "width": 150, "height": 140 },
      "occlusion": { "occluded_by": [], "reconstructed": true }
    },
    "torso": {
      "id": "torso",
      "name": "Torso",
      "type": "torso",
      "z_index": 40,
      "parent": "root",
      "pivot": { "x": 0.5, "y": 0.5 },
      "bounding_box": { "x": 170, "y": 180, "width": 170, "height": 180 },
      "occlusion": { "occluded_by": ["right_arm"], "reconstructed": false }
    }
  }
}
```
