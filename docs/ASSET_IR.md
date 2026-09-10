# AssetIR Specification (v3.0.0)

`AssetIR` (Asset Intermediate Representation) is the authoritative, engine-neutral data contract for 2D game character assets compiled by `img2game2d`.

---

## 1. Core Principles

1. **Engine Neutrality:** AssetIR does not favor Godot, Unity, Spine, Bevy, or Unreal. Target engine abstractions are handled solely by exporters.
2. **Deterministic & Reproducible:** The same source asset and parameters compile to byte-for-byte identical AssetIR documents.
3. **Lossless Provenance:** Tracks source file hashes, model backend versions, generation timestamps, and human modifications.
4. **Explicit Coordinate Systems:** Units, directions, and origins are mathematically defined. Y-up and Y-down spaces are never mixed implicitly.
5. **Actionable Diagnostics:** Contains a built-in diagnostic log highlighting structural flaws, alignment warnings, and suggested fixes.

---

## 2. Coordinate Systems & Units

### A. Canvas Space (Source & Normalization)
- **Origin $(0, 0)$:** Top-left corner of the character canvas.
- **Axes:** $+X$ right, $+Y$ down.
- **Units:** Integer pixels ($\text{px}$).
- **Usage:** Sprite slicing, raw frame placement, canvas canvas background dimensions.

### B. World Space (Engine-Neutral Canonical)
- **Origin $(0, 0)$:** Ground datum anchor ($X = \text{pivot}_x$, $Y = \text{ground}_y$).
- **Axes:** $+X$ right, $+Y$ up.
- **Units:** Normalized float units ($\text{world units}$ where character height is normalized).
- **Usage:** Skeletal physics, IK solvers, hitbox/hurtbox collisions, multi-engine scene graphs.

### C. Spine Space
- **Origin $(0, 0)$:** Root bone on ground plane.
- **Axes:** $+X$ right, $+Y$ up.
- **Units:** Pixels ($\text{px}$).
- **Usage:** Spine 2D `skeleton.json` and LibGDX `.atlas` compatibility.

### D. Normalized UV Space
- **Origin $(0, 0)$:** Top-left of texture atlas.
- **Axes:** $+U$ right $[0.0, 1.0]$, $+V$ down $[0.0, 1.0]$.
- **Units:** Dimensionless ratio.

### E. Rotations & Angles
- **Internal representation:** Radians, counter-clockwise positive.
- **Serialized representation:** Radians internally; degrees permitted in specific legacy format exporters with explicit unit documentation.

---

## 3. Mathematical Transforms

Given a canvas of width $W$, height $H$, with ground plane at $Y = G$ and horizontal pivot at $X = P$:

### Canvas to World:
$$\begin{aligned}
x_{\text{world}} &= \frac{x_{\text{canvas}} - P}{H} \\
y_{\text{world}} &= \frac{G - y_{\text{canvas}}}{H}
\end{aligned}$$

### World to Canvas:
$$\begin{aligned}
x_{\text{canvas}} &= x_{\text{world}} \cdot H + P \\
y_{\text{canvas}} &= G - y_{\text{world}} \cdot H
\end{aligned}$$

### Canvas to Spine:
$$\begin{aligned}
x_{\text{spine}} &= x_{\text{canvas}} - P \\
y_{\text{spine}} &= G - y_{\text{canvas}}
\end{aligned}$$

### Spine to Canvas:
$$\begin{aligned}
x_{\text{canvas}} &= x_{\text{spine}} + P \\
y_{\text{canvas}} &= G - y_{\text{spine}}
\end{aligned}$$

---

## 4. Schema Definition

```typescript
export interface AssetIR {
  schemaVersion: '3.0.0';

  asset: {
    id: string;
    name: string;
    sourceHash: string;
    tags?: string[];
  };

  source: {
    width: number;
    height: number;
    colorSpace: 'sRGB' | 'Linear';
    hasAlpha: boolean;
    format: string;
  };

  canvas: {
    width: number;
    height: number;
    pivotX: number;
    groundY: number;
  };

  views: ViewIR[];
  layers: LayerIR[];
  frames: FrameIR[];
  animations: AnimationClipIR[];

  skeleton?: SkeletonIR;
  meshes?: MeshIR[];
  colliders?: ColliderIR[];
  materials?: MaterialIR;
  atlas?: AtlasIR;

  diagnostics: DiagnosticIR[];
  provenance: ProvenanceIR;
}

export interface ViewIR {
  id: string;
  name: string;
  yawDegrees: number;
  pitchDegrees: number;
  landmarks2D: Record<string, { x: number; y: number; confidence: number }>;
}

export interface LayerIR {
  id: string;
  name: string;
  semanticRole:
    | 'head'
    | 'neck'
    | 'chest'
    | 'spine'
    | 'pelvis'
    | 'upper_arm_L'
    | 'lower_arm_L'
    | 'hand_L'
    | 'upper_arm_R'
    | 'lower_arm_R'
    | 'hand_R'
    | 'thigh_L'
    | 'shin_L'
    | 'foot_L'
    | 'thigh_R'
    | 'shin_R'
    | 'foot_R'
    | 'weapon'
    | 'shield'
    | 'accessory'
    | 'custom';
  zIndex: number;
  opacity: number;
  visible: boolean;
}

export interface FrameIR {
  id: string;
  animation: string;
  index: number;
  durationMs: number;
  
  // Canvas placement (px)
  canvasRect: { x: number; y: number; w: number; h: number };
  
  // Tight cropped bounds within atlas (px)
  atlasRect?: { x: number; y: number; w: number; h: number };
  
  // Normalized UV coordinates [0..1]
  uvRect?: { u0: number; v0: number; u1: number; v1: number };
  
  pivot: { x: number; y: number };
  groundAnchor: boolean;
  deltaY: number;
}

export interface AnimationClipIR {
  id: string;
  name: string;
  fps: number;
  loop: boolean;
  frameIds: string[];
  curves?: Record<string, AnimationCurveIR>;
}

export interface AnimationCurveIR {
  property: string;
  targetId: string;
  keyframes: {
    timeSec: number;
    value: number;
    inTangent?: number;
    outTangent?: number;
    interpolation: 'linear' | 'step' | 'bezier';
  }[];
}

export interface SkeletonIR {
  rootBoneId: string;
  bones: BoneIR[];
  constraints?: BoneConstraintIR[];
}

export interface BoneIR {
  id: string;
  name: string;
  parentId: string | null;
  length: number;
  
  // Rest transform in parent space
  rest: {
    x: number;
    y: number;
    rotationRad: number;
    scaleX: number;
    scaleY: number;
  };
  
  colorHex?: string;
}

export interface BoneConstraintIR {
  id: string;
  type: 'two_bone_ik' | 'foot_lock' | 'aim';
  targetBoneId: string;
  rootBoneId?: string;
  midBoneId?: string;
  poleTarget?: { x: number; y: number };
  bendPositive?: boolean;
  minAngleRad?: number;
  maxAngleRad?: number;
  weight: number;
}

export interface MeshIR {
  id: string;
  layerId: string;
  vertices: number[];       // [x0, y0, x1, y1, ...] in canvas coordinates
  triangles: number[];      // [i0, i1, i2, ...]
  uvs: number[];            // [u0, v0, u1, v1, ...]
  weights: {
    boneId: string;
    weight: number;
  }[][];                    // Per-vertex list of bone weights, must sum to 1.0
}

export interface ColliderIR {
  id: string;
  name: string;
  type: 'hitbox' | 'hurtbox' | 'body' | 'foot' | 'interaction';
  shape: 'box' | 'circle' | 'capsule' | 'polygon';
  offset: { x: number; y: number };
  size: { w: number; h: number };
  radius?: number;
  points?: { x: number; y: number }[];
  attachedBoneId?: string;
}

export interface MaterialIR {
  diffuseMap: string;
  normalMap?: string;
  emissionMap?: string;
  heightMap?: string;
  normalStrength: number;
  bloomEmission: boolean;
  lumThreshold: number;
  satThreshold: number;
}

export interface AtlasIR {
  imagePath: string;
  width: number;
  height: number;
  padding: number;
  powerOfTwo: boolean;
  occupancyRatio: number;
  wastedPixels: number;
}

export interface DiagnosticIR {
  severity: 'info' | 'warning' | 'error';
  code: string;
  message: string;
  assetId?: string;
  objectId?: string;
  location?: {
    x?: number;
    y?: number;
    frame?: number;
  };
  suggestedFix?: string;
}

export interface ProvenanceIR {
  generator: string;
  version: string;
  timestampUtc: string;
  pipelineStages: string[];
  parameters: Record<string, any>;
}
```

---

## 5. Diagnostic Severity & Standard Codes

| Code | Severity | Description | Suggested Fix |
|---|---|---|---|
| `EMPTY_FRAME` | `error` | Sliced frame has 0 width, 0 height, or 0 non-zero alpha pixels. | Adjust crop boundaries or check source alpha. |
| `INVALID_PIVOT` | `error` | Pivot point lies outside canonical canvas dimensions. | Reposition pivot to within $[0, W] \times [0, H]$. |
| `GROUND_DRIFT` | `warning` | Ground contact point shifted $> 4\text{ px}$ between planted frames. | Enable foot locking or auto-realign feet. |
| `UV_OUT_OF_RANGE` | `error` | UV coordinate $< 0.0$ or $> 1.0$. | Re-pack atlas with proper boundary margins. |
| `ATLAS_OVERLAP` | `error` | Two packed frames intersect inside texture atlas. | Increase atlas dimensions or reduce padding. |
| `MISSING_PARENT_BONE` | `error` | A bone references a parent ID that is absent in the skeleton. | Correct parent bone reference. |
| `BONE_CYCLE_DETECTED` | `error` | Bone hierarchy contains circular dependency. | Re-parent bone to valid ancestor. |
| `WEIGHT_SUM_INVALID` | `error` | Vertex bone weights do not sum to $1.0 \pm 10^{-4}$. | Re-normalize vertex weight vectors. |
| `ALPHA_HALO_RISK` | `warning` | Frame boundary pixels have high luminance and low alpha. | Run dual-contour de-matting filter. |
| `FOOT_SLIDE_ERROR` | `warning` | Planted foot moves in world space while locked. | Apply FootPlantConstraint solver. |
