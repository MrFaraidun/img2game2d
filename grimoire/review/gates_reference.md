# Validation Gates Reference

## When to read this
Read at Stage 4 (Review) before running validation checks.

---

## Gate 1: Silhouette IoU
**Script**: `forge/stage4_review/validate_silhouette.py`  
**Threshold**: ≥ 0.85

Measures how well the generated frame's silhouette matches the reference character's silhouette using Intersection over Union of alpha masks.

| Score | Status | Action |
|-------|--------|--------|
| ≥ 0.90 | ✓ Excellent | Continue |
| 0.85–0.90 | ✓ Pass | Continue |
| 0.75–0.85 | ⚠ Warning | Flag frames, continue if overall pass |
| < 0.75 | ✗ Fail | Regenerate failing frames |

**Common failures**:
- Extra limbs added by AI (extra arm visible)
- Character too large or small vs reference
- Character facing wrong direction
- Missing major body part

---

## Gate 2: Color Consistency
**Script**: `forge/stage4_review/validate_colors.py`  
**Threshold**: ≥ 0.90

Bhattacharyya histogram coefficient between reference and frame color palettes. Catches random color shifts (red becoming blue, skin becoming green).

| Score | Status | Action |
|-------|--------|--------|
| ≥ 0.95 | ✓ Excellent | Continue |
| 0.90–0.95 | ✓ Pass | Continue |
| 0.80–0.90 | ⚠ Warning | Review frames visually |
| < 0.80 | ✗ Fail | Regenerate with tighter palette constraint |

**Common failures**:
- AI hallucinating random palette
- Background leakage coloring the frame
- Skin tone shifting between frames

---

## Gate 3: Frame Continuity
**Script**: `forge/stage4_review/validate_continuity.py`  
**Threshold**: ≥ 0.88

Frame-to-frame IoU within each animation clip. Detects "teleportation" (character jumping to completely different position between consecutive frames).

| Score | Status | Action |
|-------|--------|--------|
| ≥ 0.92 | ✓ Excellent | Smooth animation |
| 0.88–0.92 | ✓ Pass | Acceptable motion |
| 0.80–0.88 | ⚠ Warning | May look jerky |
| < 0.80 | ✗ Fail | Regenerate transitions |

**Common failures**:
- AI generating completely different poses between frames
- Walk cycle with no continuity between steps

---

## Gate 4: Schema Validation
**Script**: `forge/stage2_spec/validate_asset_spec.py`  
**Threshold**: 0 errors

Hard gate — asset.json must pass JSON Schema validation before Stage 3.

---

## Overall Review Decision

After running all gates, call:
```bash
python3 forge/stage4_review/append_review.py asset.json \
  --stage review \
  --action <action> \
  --silhouette <score> \
  --colors <score> \
  --continuity <score>
```

Valid actions:
- `continue` — All gates pass, proceed to Stage 5
- `refine-frames` — Frames need regeneration (return to Stage 3)
- `refine-spec` — Layer spec needs correction (return to Stage 2)
- `request-input` — Cannot resolve autonomously, ask human
- `stop` — Hard stop (correction limit reached)

---

## Correction Budget
The state machine tracks corrections. After **6 total corrections**, `next.py` exits with code 3 and requests human review. Do not bypass this limit.
