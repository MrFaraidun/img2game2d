/**
 * img2game2d v3 Canonical AssetIR TypeScript Definitions.
 * Engine-neutral, local-first intermediate representation for 2D game assets.
 */

export interface AssetMetaIR {
  id: string;
  name: string;
  sourceHash: string;
  tags?: string[];
}

export interface SourceMetaIR {
  width: number;
  height: number;
  colorSpace: 'sRGB' | 'Linear';
  hasAlpha: boolean;
  format: string;
}

export interface CanvasMetaIR {
  width: number;
  height: number;
  pivotX: number;
  groundY: number;
}

export interface ViewIR {
  id: string;
  name: string;
  yawDegrees: number;
  pitchDegrees: number;
  landmarks2D?: Record<string, { x: number; y: number; confidence: number }>;
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
  canvasRect: { x: number; y: number; w: number; h: number };
  atlasRect?: { x: number; y: number; w: number; h: number };
  uvRect?: { u0: number; v0: number; u1: number; v1: number };
  pivot: { x: number; y: number };
  groundAnchor: boolean;
  deltaY: number;
}

export interface KeyframeIR {
  timeSec: number;
  value: number;
  inTangent?: number;
  outTangent?: number;
  interpolation: 'linear' | 'step' | 'bezier';
}

export interface AnimationCurveIR {
  property: string;
  targetId: string;
  keyframes: KeyframeIR[];
}

export interface AnimationClipIR {
  id: string;
  name: string;
  fps: number;
  loop: boolean;
  frameIds: string[];
  curves?: Record<string, AnimationCurveIR>;
}

export interface BoneRestIR {
  x: number;
  y: number;
  rotationRad: number;
  scaleX: number;
  scaleY: number;
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

export interface BoneIR {
  id: string;
  name: string;
  parentId: string | null;
  length: number;
  rest: BoneRestIR;
  colorHex?: string;
}

export interface SkeletonIR {
  rootBoneId: string;
  bones: BoneIR[];
  constraints?: BoneConstraintIR[];
}

export interface VertexWeightIR {
  boneId: string;
  weight: number;
}

export interface MeshIR {
  id: string;
  layerId: string;
  vertices: number[]; // [x0, y0, x1, y1, ...]
  triangles: number[]; // [i0, i1, i2, ...]
  uvs: number[]; // [u0, v0, u1, v1, ...]
  weights: VertexWeightIR[][]; // per-vertex weight list, sums to 1.0
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

export interface AssetIR {
  schemaVersion: '3.0.0';
  asset: AssetMetaIR;
  source: SourceMetaIR;
  canvas: CanvasMetaIR;
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
  provenance?: ProvenanceIR;
}
