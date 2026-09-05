# Image Analysis Protocol

## When to read this
Read this doc at the START of Stage 1 (Intake), before performing any visual analysis on the reference image.

---

## Your Mission
You are performing structured visual analysis on a 2D game character or object reference image. Your output must be a **machine-readable `analysis.json`** that the downstream forge scripts can consume directly. Do NOT skip fields. Do NOT guess silently — flag uncertainty explicitly.

---

## Required Output: `analysis.json`

```json
{
  "asset_id": "snake_character",
  "name": "Snake Character",
  "asset_type": "character",
  "character_type": "humanoid|creature|vehicle|fantasy|robot|other",
  "source_image": "source/original.png",
  "views_detected": ["front"],
  "resolution": { "width": 512, "height": 512 },
  "bounding_box": { "x": 40, "y": 10, "width": 430, "height": 490 },
  "silhouette_score": 0.92,
  "symmetry": "near-symmetric",
  "proportions": {
    "head_to_body_ratio": 0.28,
    "limb_length": "normal"
  },
  "parts": [
    "head", "mask", "horns", "eyes",
    "torso", "cloak",
    "left_arm", "right_arm",
    "left_leg", "right_leg",
    "weapon"
  ],
  "colors": [
    { "hex": "#1a1a2e", "role": "armor_dark", "coverage": 0.35 },
    { "hex": "#c0a050", "role": "gold_trim", "coverage": 0.12 }
  ],
  "animations": ["idle", "walk", "attack", "death"],
  "silhouette_notes": "Clear silhouette with good contrast against transparent background.",
  "occlusion_notes": "Left arm partially behind cloak. Torso partially behind cloak.",
  "uncertainty": []
}
```

---

## Analysis Rules

### 1. Asset Type Classification
- `character` — Any humanoid, creature, or character with a body
- `object` — Inanimate prop, item, or interactive element
- `effect` — Particle, projectile, visual effect
- `ui` — Interface element

### 2. Parts Inventory
List every visually distinct body part you can identify. Use snake_case IDs.  
Standard IDs (use these exact strings when applicable):
```
head, face, hair, horn, horns, eye, eyes, ear, ears, mouth, neck
torso, chest, belly
shoulder, arm_left, arm_right, left_arm, right_arm
forearm_left, forearm_right, hand_left, hand_right
hip, leg_left, leg_right, left_leg, right_leg
knee_left, knee_right, foot_left, foot_right, left_foot, right_foot
tail, wing_left, wing_right, claw_left, claw_right
cloak, cape, armor, helmet, mask, glove
weapon, sword, shield, bow, staff, axe
```

### 3. Silhouette Quality
Score from 0.0–1.0:
- 1.0 = Perfect clean edges, high contrast, no noise
- 0.8 = Good but minor fringing or soft edges
- 0.6 = Noisy background or poor contrast — flag for background removal
- < 0.5 = STOP. Request a cleaner reference image.

### 4. Symmetry Assessment
- `symmetric` — Left/right halves are mirror images (e.g. front-facing idle pose)
- `near-symmetric` — Minor differences (e.g. weapon hand)
- `asymmetric` — Clearly different sides (e.g. 3/4 view, action pose)

### 5. Color Extraction
Extract the 5–8 most dominant colors (ignore near-transparent pixels).
Assign a semantic role:
- `skin`, `hair`, `eyes`, `primary_armor`, `secondary_armor`, `accent`, `weapon`, `shadow`, `highlight`

### 6. Animation Defaults
If the user did not specify animations, infer from asset type:
- **humanoid character** → `idle, walk, run, attack, hurt, death`
- **creature** → `idle, walk, attack, hurt, death`
- **flying creature** → `idle, fly, attack, hurt, death`
- **object/item** → `idle`
- **effect** → `play`

### 7. Uncertainty Protocol
If you are unsure about any field, add it to the `uncertainty` array:
```json
"uncertainty": [
  { "field": "parts", "note": "Cannot clearly see if character has a tail behind the cloak." },
  { "field": "symmetry", "note": "Pose is ambiguous between front and three-quarter view." }
]
```
Do NOT silently guess. Always flag uncertainty.

---

## After Analysis
Save output to `analysis/analysis.json`.  
Then run: `python3 forge/state.py mark intake.analyze --evidence analysis/analysis.json`
