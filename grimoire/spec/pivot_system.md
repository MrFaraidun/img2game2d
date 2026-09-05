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

---

## ⚠️ Critical: Inverse Affine Coordinate Mapping in PIL

When generating frames with Python Pillow (`Image.transform(size, Image.AFFINE, data)`), PIL uses **inverse mapping** (output $(x, y) \to$ input $(u, v)$):
$$u = a x + b y + c$$
$$v = d x + e y + f$$

Using forward transformation matrices directly will invert angles, cause drifting pivots, and **break character limbs into disconnected floating chunks**.

The mathematically exact inverse affine 6-tuple around pivot $(c_x, c_y)$ with rotation $\theta$, translation $(\Delta x, \Delta y)$, and scale $(s_x, s_y)$ is:

```python
import math

cos_a = math.cos(angle_rad)
sin_a = math.sin(angle_rad)
inv_sx = 1.0 / max(sx, 1e-5)
inv_sy = 1.0 / max(sy, 1e-5)

a = cos_a * inv_sx
b = sin_a * inv_sx
c = cx - (cos_a * (cx + dx) + sin_a * (cy + dy)) * inv_sx

d = -sin_a * inv_sy
e = cos_a * inv_sy
f = cy - (-sin_a * (cx + dx) + cos_a * (cy + dy)) * inv_sy

matrix = (a, b, c, d, e, f)
transformed = layer.transform(layer.size, Image.AFFINE, matrix, resample=Image.BILINEAR)
```

## Non-Linear Continuous Deformation for Organic Bodies & Cloaks

For characters with contiguous bodies, flowing robes, or capes, **never slice them into rigid rectangular boxes** for walking cycles. Instead, use non-linear continuous shear:

```python
weight = np.clip((yy - hip_y) / span, 0.0, 1.0) ** 1.2
shift_x = weight * stride_pixels
```
This smoothly deflects the lower body and cloth without tearing seams or creating transparent voids.

