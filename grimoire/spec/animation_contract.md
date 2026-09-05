# Animation Contract

## When to read this
Read at Stage 2 (Spec) when defining animations in `asset.json`, and again at Stage 3 (Build) before generating frames.

---

## Animation Entry Format

```json
"idle": {
  "name": "idle",
  "fps": 8,
  "loop": true,
  "frames": [],
  "frame_count": 0
}
```

Fields are populated progressively:
- **Stage 2**: define name, fps, loop — frames stays empty
- **Stage 3**: frames list fills in as generation completes
- **Stage 4**: validated against reference silhouette

---

## Standard Animation Definitions

### Character Animations

| Name | FPS | Loop | Description |
|------|-----|------|-------------|
| `idle` | 6–8 | true | Subtle breathing or stance hold |
| `walk` | 10–12 | true | Standard walk cycle (2-step loop) |
| `run` | 14–16 | true | Run cycle (faster, more dynamic) |
| `jump` | 10 | false | Jump up → peak → landing |
| `fall` | 8 | true | Mid-air falling loop |
| `land` | 12 | false | Landing impact frames |
| `dash` | 16 | false | Quick dash or dodge |
| `attack` | 12–16 | false | Primary attack swing |
| `attack2` | 12–16 | false | Secondary attack or combo |
| `hurt` | 12 | false | Hit reaction / stagger |
| `death` | 8 | false | Death collapse |
| `block` | 8 | false | Shield or guard pose |
| `crouch` | 8 | false | Crouch down |
| `climb` | 10 | true | Climbing animation |

### Object Animations
| Name | FPS | Loop | Description |
|------|-----|------|-------------|
| `idle` | 4–6 | true | Gentle bob, glow, or static |
| `activate` | 12 | false | Item pickup or trigger |
| `destroy` | 10 | false | Break/destroy animation |

### Effect Animations
| Name | FPS | Loop | Description |
|------|-----|------|-------------|
| `play` | 24 | false | One-shot particle/effect |
| `loop` | 24 | true | Looping effect (fire, smoke) |

---

## Frame Count Guidelines

| Animation | Min frames | Recommended |
|-----------|-----------|-------------|
| idle | 2 | 4–6 |
| walk | 4 | 8 |
| run | 4 | 8 |
| jump | 2 | 4 |
| fall | 2 | 3 |
| attack | 3 | 5–7 |
| hurt | 2 | 3 |
| death | 3 | 6–8 |

---

## Quality Requirements Per Frame

Every generated frame MUST:
1. **Silhouette match** — IoU ≥ 0.85 vs reference
2. **Palette match** — Bhattacharyya coefficient ≥ 0.90 vs reference
3. **Continuity** — IoU ≥ 0.88 vs previous frame (no teleportation)
4. **Consistent anatomy** — No extra/missing limbs
5. **Consistent equipment** — Weapon must appear in every frame where it should be visible
6. **Transparent background** — Alpha channel, no background leakage

---

## Key Frames to Get Right

### walk cycle (8 frames)
- Frame 0: neutral pose
- Frame 2: right leg forward
- Frame 4: neutral (opposite)
- Frame 6: left leg forward

### attack (6 frames)
- Frame 0: wind-up pose
- Frame 1–2: swing motion
- Frame 3: impact / connection
- Frame 4–5: follow-through / recovery

### death (6 frames)
- Frame 0: hit reaction
- Frame 1–3: falling
- Frame 4: ground contact
- Frame 5: final resting pose (static)
