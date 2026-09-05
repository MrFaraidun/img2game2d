# Self-Correction Protocol

## When to read this
Read when a validation gate fails and you need to decide how to repair the output.

---

## Correction Loop Rules

1. **Do not loop more than 3 times on the same gate.** Each loop uses one correction credit.
2. **Change the approach each loop.** If loop 1 fails with prompt A, loop 2 must change the strategy.
3. **If a gate fails twice for the same clip, flag it and skip it** — move on, mark it for human review.
4. **Never alter the reference image.** Only alter prompts, parameters, or generated outputs.

---

## Silhouette Failure → Repair Protocol

**Root cause**: AI generated a character with wrong size, shape, or pose.

**Repair actions** (try in order):
1. **Add explicit silhouette constraint** to generation prompt:
   - "Match this exact silhouette. Character width: {W}px. Height: {H}px."
   - "Do not add extra limbs. Character has exactly {N} visible limbs."
2. **Reduce frame count** — fewer frames = less drift
3. **Use a pose-specific prompt** with exact bone angles instead of animation name
4. **Inpaint only the silhouette edge** — keep interior, fix borders

---

## Color Failure → Repair Protocol

**Root cause**: AI shifted the color palette away from the reference.

**Repair actions** (try in order):
1. **Inject palette explicitly** into prompt:
   - "Use ONLY these colors: {hex1}, {hex2}, {hex3}. No other colors."
2. **Post-process with palette quantization** (reduce to N colors, remap to reference palette)
3. **Blend frames** — mix the generated frame 80% with the reference to restore palette
4. **Regenerate with reference image as conditioning** (use img2img if supported)

---

## Continuity Failure → Repair Protocol

**Root cause**: Consecutive frames are too different (pose jumps).

**Repair actions** (try in order):
1. **Generate intermediate frames** — add frames between the discontinuous pair
2. **Use previous frame as conditioning** for next frame generation
3. **Interpolate** — blend two adjacent frames to fill the gap
4. **Reduce FPS** — fewer frames = fewer transitions = less chance of jump

---

## Schema Failure → Repair Protocol

**Root cause**: `asset.json` has missing or invalid fields.

**Repair actions**:
1. Read the validation error output carefully
2. Fix the specific field(s) in `asset.json`
3. Re-run `validate_asset_spec.py`
4. Check schemas at `schemas/*.schema.json` for field definitions

---

## When to Escalate to Human

Always escalate if:
- The same gate fails 3 times with different approaches
- Silhouette score is below 0.60 (fundamentally wrong character shape)
- Color score is below 0.50 (completely wrong palette)
- Correction budget is exhausted (6 credits used)

Use:
```bash
python3 forge/stage4_review/append_review.py asset.json \
  --stage review --action request-input \
  --summary "Silhouette IoU stuck at 0.72 after 3 attempts. Manual regeneration needed."
```
