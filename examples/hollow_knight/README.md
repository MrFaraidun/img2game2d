# Hollow Knight Showcase Example

An end-to-end production showcase demonstrating the reconstruction, layer decomposition, inverse-affine skeletal rigging, procedural kinematics, and multi-engine export of a single 2D character sprite using **`img2game2d`**.

![Hollow Knight Showcase Banner](animations/showcase_banner.gif)

---

## 🎬 Animation Cycles

All cycles are procedurally synthesized using PIL closed-form inverse-affine transformation matrices, sub-pixel pivot anchoring, and multi-pass procedural visual effects:

| Cycle | Preview | Frames | Mechanics & Physics |
| :--- | :---: | :---: | :--- |
| **Idle** | <img src="animations/idle.gif" width="160"/> | 4 frames | Vertical sinus breathing bounce with lagging cloak trailing drape. |
| **Walk** | <img src="animations/walk.gif" width="160"/> | 8 frames | Pendulum stride cadence with torso tilt and dynamic cloak shear physics. |
| **Jump** | <img src="animations/jump.gif" width="160"/> | 6 frames | Pre-takeoff anticipation squash, ballistic rise, apex hang, and landing shock dampening. |
| **Attack** | <img src="animations/attack.gif" width="160"/> | 6 frames | Windup anticipation, violent downward slash, multi-pass luminous crescent VFX wave, and recovery. |
| **Hurt** | <img src="animations/hurt.gif" width="160"/> | 4 frames | Ballistic impact recoil, weapon kickback, and staggered re-equilibration. |

---

## 🔬 Pipeline Architecture

![Pipeline Breakdown](pipeline_breakdown.png)

### 1. Intake & Enhancement
- **Input Reference**: [`source/character.png`](source/character.png) (single character concept).
- **Super-Resolution**: Lanczos 2x super-sampling + Contrast-Adaptive Sharpening (CAS).
- **Zero-Halo Defringing**: Transparent background separation without black border halos.

### 2. Anatomical Layer Decomposition
- **Head**: Horned mask with eye sockets ([`layers/head.png`](layers/head.png)).
- **Cloak**: Outer drapery with lower hem shearing profile ([`layers/cloak.png`](layers/cloak.png)).
- **Nail / Weapon**: Articulated melee blade with independent rotational pivot ([`layers/sword.png`](layers/sword.png)).
- **Torso**: Internal chest core and leg base ([`layers/body.png`](layers/body.png)).

### 3. Procedural Kinematics & VFX
- **Transform Math**: Exact closed-form PIL `Image.AFFINE` inverse mapping formula around arbitrary pivots $(cx, cy)$.
- **Slash Arc VFX**: Procedural multi-pass crescent energy arc rendered directly in code.

---

## 🕹️ Interactive Web QA Viewer

Launch the built-in HTML5 Canvas test runner to preview animations with procedural sound synthesis (Web Audio API) and hitboxes:

```bash
# From workspace root
python3 -m http.server 8888 --directory examples/hollow_knight
# Open in browser: http://localhost:8888/viewer/
```

- **Interactive Controls**: Play, pause, step forward/backward, speed slider (0.1x to 2.0x).
- **Overlays**: Hitbox boundaries, origin pivots, and bone hierarchy toggles.
- **Synthesizer**: Procedural whoosh, jump, impact, and footstep sound effects generated on the fly.

---

## 📦 Engine Integration

### Godot 4.x (`CharacterBody2D`)
```gdscript
extends CharacterBody2D

@onready var anim: AnimatedSprite2D = $AnimatedSprite2D

func _physics_process(delta: float) -> void:
    if Input.is_action_just_pressed("attack"):
        anim.play("attack")
    elif velocity.y != 0:
        anim.play("jump")
    elif velocity.x != 0:
        anim.play("walk")
    else:
        anim.play("idle")
```

### Unity 2022+ C#
```csharp
using UnityEngine;

[RequireComponent(typeof(SpriteRenderer))]
public class HollowKnightController : MonoBehaviour {
    public Sprite[] idleFrames;
    public Sprite[] walkFrames;
    public Sprite[] attackFrames;
    // ...
}
```

### PixiJS 7.x
```javascript
import { Application, AnimatedSprite, Assets } from 'pixi.js';

const sheet = await Assets.load('atlases/attack.json');
const anim = new AnimatedSprite(sheet.animations['attack']);
anim.animationSpeed = 0.16;
anim.play();
```
