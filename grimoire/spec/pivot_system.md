# Pivot System

## When to read this
Read at Stage 2 (Spec) when reviewing or editing pivot points in `asset.json` layers.

---

## What is a Pivot?
A **pivot** (also called an anchor or origin point) is the fixed point a layer rotates around during animation. It is expressed as normalized [0,1] coordinates within the layer's bounding box.

In Godot: this is the `offset` property of Sprite2D.  
In Unity: this is the sprite pivot.  
In Phaser: this is the `setOrigin(x, y)` call.

---

## Pivot vs. Origin
- **Pivot**: The rotation/scaling center for this specific layer
- **Origin**: The attachment point to the parent bone
These are often the same point (e.g. the shoulder joint is both the arm's pivot and its attachment to the torso).

---

## Anatomical Pivot Rules

```
HEAD       → pivot at bottom-center (0.5, 1.0)
             Reason: head rotates around the neck joint at its base.

HAIR       → pivot at top-center (0.5, 0.0)
             Reason: hair moves from the scalp, follows head rotation.

ARM_LEFT   → pivot at right-edge, near-top (1.0, 0.1)
             Reason: arm rotates from shoulder. The shoulder is on the right
             side of the left arm (connected to torso).

ARM_RIGHT  → pivot at left-edge, near-top (0.0, 0.1)
             Reason: mirror of arm_left.

FOREARM    → pivot at top-center (0.5, 0.0)
             Reason: elbow joint at the top of the forearm.

HAND       → pivot at top-center (0.5, 0.0)
             Reason: wrist joint.

LEG        → pivot at top-center (0.5, 0.0)
             Reason: hip joint.

LOWER_LEG  → pivot at top-center (0.5, 0.0)
             Reason: knee joint.

FOOT       → pivot at top-center (0.5, 0.0)
             Reason: ankle joint.

TORSO      → pivot at center (0.5, 0.5)
             Reason: torso is the root; center pivot for breath/sway animation.

CLOAK      → pivot at top-center (0.5, 0.0)
             Reason: cloak flows from the shoulder attachment.

TAIL       → pivot at top or left (0.5, 0.0 or 0.0, 0.5)
             Reason: tail connects to the base of the spine.

WEAPON     → pivot at grip (~0.5, 0.8 for top-held sword)
             Adjust based on weapon type and grip position.
```

---

## How Pivots Are Used

### In the Atlas / Frame
Pivots are stored in the atlas JSON per frame:
```json
{ "frame": {...}, "pivot": { "x": 0.5, "y": 1.0 } }
```

### In Godot
```gdscript
sprite.offset = Vector2(-frame_w * pivot_x, -frame_h * pivot_y)
```

### In Phaser
```javascript
sprite.setOrigin(pivot.x, pivot.y);
```

### In PixiJS
```javascript
sprite.anchor.set(pivot.x, pivot.y);
```

---

## Pivot Review Checklist
Before marking Stage 2 complete, verify:
- [ ] Every layer has a `pivot` field
- [ ] Head pivot is at or near `(0.5, 1.0)`
- [ ] Arm pivots are at shoulder edges (not center)
- [ ] Leg pivots are at top (hip/knee)
- [ ] Weapon pivot is near the grip, not the blade tip
- [ ] No layer has `pivot = (0,0)` unless it's a corner-anchored element
