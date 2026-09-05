# View Detection Protocol

## When to read this
Read at Stage 1 (Intake) when the image contains multiple character views or the view angle is ambiguous.

---

## What is a "View"?
A **view** is a single perspective of the character:
- `front` — Character facing directly toward the viewer
- `back` — Character facing directly away
- `left` — Character facing left
- `right` — Character facing right
- `front-left` / `front-right` — Three-quarter front angles
- `back-left` / `back-right` — Three-quarter back angles
- `side` — Pure profile (90°)
- `three-quarter` — ~45° between front and side
- `top` — Bird's-eye view
- `isometric` — Isometric projection

---

## Multi-View Reference Sheets

A **reference sheet** (also called a turnaround) contains multiple views laid out horizontally. Common layouts:

| Panel count | Typical order |
|-------------|---------------|
| 2 | front, back |
| 3 | front, side, back |
| 4 | front, side-right, back, side-left |
| 5 | front, front-right, side, back-right, back |

### How to detect panels
1. Run `python3 forge/stage1_intake/detect_views.py <image>` — it finds content-region separators.
2. Read the output `views.json`.
3. **Verify and correct labels** — the script labels panels generically (view_0, view_1...). Replace with correct directional names.

### Example correction
```json
// Before (auto-labeled)
{ "label": "view_0", "bbox": [0, 0, 256, 512] }
{ "label": "view_1", "bbox": [256, 0, 256, 512] }

// After (corrected)
{ "label": "front", "bbox": [0, 0, 256, 512] }
{ "label": "back", "bbox": [256, 0, 256, 512] }
```

---

## Single-View Heuristics

If the image contains only one character:

| Observation | Likely View |
|-------------|-------------|
| High left/right symmetry (>0.85) | `front` or `back` |
| Moderate symmetry (0.65–0.85) | `three-quarter` |
| Low symmetry (<0.65) | `side` |
| Visible ears/horns on both sides | `front` |
| Only one ear/horn visible | `side` |
| Back of head visible | `back` |

---

## Output: `analysis/views.json`
The script writes this. Verify it looks correct before continuing.

---

## Priority Rule
**The agent's visual assessment takes priority over the script output.**  
If you can clearly see the character is facing front but the script guessed `side`, correct it.
