# Action Sheet & Multi-Pose Animation Protocol

## Overview
When higher fidelity or custom artistic character expressions are desired (such as distinct facial reactions for hurt, dynamic perspective shifts during an attack swing, or authentic cloth flow during jump), providing a **5-Pose Action Sheet** is superior to animating from a single static image.

---

## What is an Action Sheet?
An **Action Sheet** contains 3 to 6 keyframe action poses of the **exact same character** laid out horizontally on a single canvas.

Standard 5-Pose Sequence (Left to Right):
1. **`idle`**: Standing ready in neutral combat posture.
2. **`walk`**: Full walking stride with alternating legs.
3. **`jump`**: Tucked airborne silhouette with floating cloak/hair.
4. **`attack`**: Explosive weapon strike with momentum and slash trajectory.
5. **`hurt`**: Knockback damage recoil with grimace/squint.

---

## Recommended AI Generation Prompt

To avoid character drift across different images, **always generate all 5 poses in one single canvas generation**:

```text
Full-body cel-shaded 2D character action sprite sheet, showing 5 sequential poses of the EXACT SAME character on a single horizontal canvas arranged left-to-right:
1. [idle] standing ready in combat stance
2. [walk] walking stride pose with legs extended
3. [jump] tucked mid-air jumping pose with cloak floating upward
4. [attack] explosive weapon slash strike with glowing crescent arc
5. [hurt] damage recoil knockback pose
Consistent character costume, exact same proportions and colors, crisp clean cel-shaded vector ink outlines, isolated on a seamless flat solid neutral light gray background (#e0e0e0), professional 2D video game sprite sheet, 8k.
```

**Negative Prompt**:
```text
cropped limbs, cut off feet, cut off head, touching canvas borders, complex background scenery, photorealistic clutter, extreme perspective foreshortening, isometric angle, dynamic combat pose, blurry edges, text, watermark, signature, compression artifacts, noisy textures
```

---

## Pipeline Execution

```bash
# 1. Inspect and slice the action sheet into individual action poses
python3 forge/stage1_intake/detect_actions.py action_sheet.png --out source/poses/

# Or via unified CLI:
python3 forge/cli.py slice-actions action_sheet.png --out source/poses/

# 2. Run full build using the action sheet
python3 forge/cli.py build action_sheet.png --action-sheet --engine viewer --out dist/
```
