# Layer Contract

## When to read this
Read at Stage 2 (Spec) before building or editing `asset.json` layers.

---

## Layer Definition Rules

Every layer in `asset.json` must satisfy these constraints:

### Required Fields
| Field | Type | Rules |
|-------|------|-------|
| `id` | string | Snake_case. Unique within asset. Use standard IDs below. |
| `name` | string | Human-readable. Title case. |
| `type` | string | Must be one of the valid types listed below. |
| `z_index` | integer | ≥ 0. Higher = closer to camera. Use multiples of 10. |
| `pivot` | object | `{"x": float, "y": float}`. Both in [0,1]. |

### Optional But Strongly Recommended
| Field | Default | Purpose |
|-------|---------|---------|
| `parent` | `"root"` | Defines skeleton hierarchy for rigging. |
| `bounding_box` | estimated | Pixel coordinates for crop/extraction. |
| `visible` | `true` | Whether this layer renders in default pose. |

---

## Standard Layer IDs

Use these exact IDs. New IDs are allowed for non-standard parts, but document them in `asset_notes`.

```
# Head region
head, face, hair, horn, horns, eye, eyes, ear, ears, mouth, neck, jaw, beard, mustache, mask, helmet, hat

# Torso region
torso, chest, belly, back, shoulder_left, shoulder_right

# Arms
arm_left, arm_right, left_arm, right_arm
forearm_left, forearm_right, left_forearm, right_forearm
hand_left, hand_right, left_hand, right_hand
finger_left, finger_right

# Legs
hip, leg_left, leg_right, left_leg, right_leg
lower_leg_left, lower_leg_right, left_lower_leg, right_lower_leg
foot_left, foot_right, left_foot, right_foot

# Extras
tail, wing_left, wing_right, claw_left, claw_right

# Equipment
cloak, cape, armor, pauldron_left, pauldron_right, gauntlet_left, gauntlet_right
weapon, sword, shield, bow, staff, axe, spear, gun

# Effects
aura, shadow, glow
```

---

## Valid Layer Types

```
head, face, hair, horn, eye, ear, mouth, neck
torso, chest
arm, forearm, hand, shoulder
leg, lower_leg, foot, hip
tail, wing, claw
armor, clothing, cloak
weapon, shield
other
```

---

## Z-Index Convention (back to front)

| Z range | Layer type |
|---------|-----------|
| 0–9 | Background elements (shadow, glow) |
| 10–19 | Back appendages (back wing, back arm) |
| 20–29 | Legs, lower body |
| 30–39 | Torso, pelvis |
| 40–49 | Front legs |
| 50–59 | Arms (behind torso) |
| 60–69 | Torso equipment (cloak, armor) |
| 70–79 | Head |
| 80–89 | Front arms (in front of torso) |
| 90–99 | Weapons, accessories |
| 100+ | Overlaid effects |

---

## Pivot Point Convention

Pivot is normalized [0,1] within the layer's bounding box:
- `(0,0)` = top-left corner
- `(1,1)` = bottom-right corner
- `(0.5, 0.5)` = center
- `(0.5, 1.0)` = bottom-center (used for neck joint on head layer)
- `(0.5, 0.0)` = top-center (used for hip joint on leg layer)

### Standard Pivots by Part
```
head:       (0.5, 1.0)   # Bottom-center = neck attachment
arm_left:   (1.0, 0.1)   # Right edge near top = shoulder joint
arm_right:  (0.0, 0.1)   # Left edge near top = shoulder joint
forearm:    (0.5, 0.0)   # Top = elbow
hand:       (0.5, 0.0)   # Top = wrist
leg_left:   (0.5, 0.0)   # Top = hip joint
leg_right:  (0.5, 0.0)
foot:       (0.5, 0.0)   # Top = ankle
weapon:     (0.5, 0.8)   # Near grip end
cloak:      (0.5, 0.0)   # Top = shoulder attachment
```

---

## Occlusion Handling

If layer A is behind layer B (lower z_index) and they overlap visually:
1. Mark layer A's `occlusion.occluded_by = ["layer_B_id"]`
2. Set `occlusion.reconstructed = false`
3. Stage 3 will reconstruct the hidden pixels via `reconstruct_occlusion.py`

---

## Minimum Viable Layer Set

For a character with no equipment, the minimum valid set is:

```json
["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]
```
