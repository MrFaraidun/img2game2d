/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Core Type Definitions & Data Contracts
 * 
 * Strict typing across Character pipelines, 2D Tangent Space Shading,
 * Spine 2.x/3.x/4.x Skeletal rigs, Multi-engine runtime configurations,
 * and Studio Workstation state.
 */

// ============================================================================
// 1. Studio Workspace & Routing Types
// ============================================================================

/** Active Workstation tab identifier */
export type StudioTab = 'studio' | 'lighting' | 'spine' | 'exports';

/** Theme visual token mode */
export type ThemeMode = 'light' | 'dark';

/** Canvas visual background pattern */
export type StageBackgroundMode = 'grid-dark' | 'grid-slate' | 'checker' | 'pitch';

/** Viewport zoom scale level */
export type ZoomScale = 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 2.0;

/** Status telemetry snapshot for top ribbon */
export interface TelemetryState {
  characterName: string;
  animationName: string;
  currentFrameIdx: number;
  totalFrames: number;
  currentFps: number;
  playbackSec: number;
  durationSec: number;
  frameWidth: number;
  frameHeight: number;
  canvasWidth: number;
  canvasHeight: number;
  atlasResolution: string;
  lightingConvention: string;
  memoryUsageMb: number;
  renderTimeMs: number;
}

/** Visual Gizmo overlay toggles */
export interface GizmoSettings {
  showHitbox: boolean;
  showPivot: boolean;
  showGroundLine: boolean;
  showFrameBox: boolean;
  showOnionSkin: boolean;
  onionSkinFrames: number;
  onionSkinAlpha: number;
  groundBaselineY: number;
  hitboxBounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

// ============================================================================
// 2. Character & Animation Pipeline Types
// ============================================================================

/** Supported Character IDs in project */
export type CharacterId = 'the_architect' | 'the_guardian';

/** 2D Point coordinate vector */
export interface Vec2 {
  x: number;
  y: number;
}

/** 3D Vector for lighting coordinates and tangent vectors */
export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

/** 4D Vector for RGBA colors or quaternion rotations */
export interface Vec4 {
  x: number;
  y: number;
  z: number;
  w: number;
}

/** Dimension rectangle */
export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** Single animation sequence metadata */
export interface AnimationSequenceMeta {
  frame_count: number;
  fps: number;
  loop: boolean;
  category?: 'locomotion' | 'combat' | 'reaction' | 'passive';
  tags?: string[];
  eventTriggers?: {
    frame: number;
    name: 'hit' | 'footstep' | 'cast' | 'land';
    sfx?: string;
  }[];
}

/** Character metadata JSON format */
export interface CharacterMetadata {
  name: string;
  character_id: CharacterId;
  version: string;
  class_title: string;
  canvas_size: {
    width: number;
    height: number;
  };
  ground_baseline: number;
  default_pivot: Vec2;
  animations: Record<string, AnimationSequenceMeta>;
}

/** Sliced atlas frame specification following TexturePacker JSON Hash */
export interface AtlasFrameData {
  frame: Rect;
  rotated: boolean;
  trimmed: boolean;
  spriteSourceSize: Rect;
  sourceSize: {
    w: number;
    h: number;
  };
  pivot?: Vec2;
}

/** Full TexturePacker Atlas JSON structure */
export interface TexturePackerAtlas {
  frames: Record<string, AtlasFrameData>;
  meta: {
    app: string;
    version: string;
    image: string;
    format: string;
    size: {
      w: number;
      h: number;
    };
    scale: string;
    smartupdate?: string;
    normalMap?: string;
    emissionMap?: string;
  };
}

/** Runtime loaded character assets container */
export interface CharacterRuntimeAsset {
  id: CharacterId;
  name: string;
  subtitle: string;
  metaUrl: string;
  atlasJsonUrl: string;
  atlasUrl: string;
  normalUrl: string;
  emissionUrl: string;
  spineJsonUrl: string;
  spineAtlasUrl: string;
  
  // Loaded memory references
  meta: CharacterMetadata | null;
  atlasData: TexturePackerAtlas | null;
  atlasImg: HTMLImageElement | null;
  normalImg: HTMLImageElement | null;
  emissionImg: HTMLImageElement | null;
  spineData: SpineSkeletonData | null;
  isLoaded: boolean;
  loadError: string | null;
}

/** Extracted frame coordinate mapping for canvas rendering */
export interface ResolvedFrameCoordinates {
  frameKey: string;
  source: Rect;
  dest: Rect;
  canvasSize: { w: number; h: number };
  pivot: Vec2;
  normalizedFrameIdx: number;
}

// ============================================================================
// 3. Dynamic 2D Tangent Space Lighting Types
// ============================================================================

/** Lighting view mode selector */
export type LightingViewMode = 'composite' | 'split' | 'diffuse_only' | 'normal_only' | 'emission_only';

/** Light source category */
export type LightSourceType = 'point' | 'spot' | 'ambient' | 'directional';

/** Single configurable light source */
export interface DynamicLightSource {
  id: string;
  name: string;
  type: LightSourceType;
  x: number;
  y: number;
  zDepth: number;
  intensity: number;
  radius: number;
  colorHex: string;
  colorRgb: { r: number; g: number; b: number };
  specularPower: number;
  specularShininess: number;
  enabled: boolean;
  isDraggable: boolean;
}

/** Preset configuration bundle for lighting conditions */
export interface LightingPresetConfig {
  id: string;
  name: string;
  subtitle: string;
  description: string;
  ambientIntensity: number;
  ambientColorHex: string;
  mainLight: {
    intensity: number;
    radius: number;
    zDepth: number;
    colorHex: string;
    specularPower: number;
  };
  bloomBoost: number;
  bloomThreshold: number;
  toneMapping: 'aces' | 'reinhard' | 'linear';
}

/** Complete state of the Dynamic Lighting Workstation */
export interface LightingEngineState {
  viewMode: LightingViewMode;
  splitPositionRatio: number; // 0.0 to 1.0
  activePresetId: string;
  ambientBaseLevel: number;
  ambientColorHex: string;
  bloomBoost: number;
  bloomThreshold: number;
  lights: DynamicLightSource[];
  activeLightId: string;
  useInvertedY: boolean; // OpenGL (+Y) vs DirectX (-Y)
  specularEnabled: boolean;
  specularShininess: number;
}

// ============================================================================
// 4. Spine 2D Skeletal Hierarchy & Rigging Types
// ============================================================================

/** Individual skeletal bone definition */
export interface SpineBoneSpec {
  name: string;
  parent?: string | null;
  length?: number;
  x: number;
  y: number;
  rotation: number;
  scaleX?: number;
  scaleY?: number;
  shearX?: number;
  shearY?: number;
  transformRule?: 'normal' | 'onlyTranslation' | 'noRotationOrReflection' | 'noScale';
  color?: string;
}

/** Computed world-space bone transform for rendering on canvas */
export interface ComputedWorldBone {
  name: string;
  parentName: string | null;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  worldRotation: number;
  length: number;
  color: string;
  isSelected: boolean;
  isHovered: boolean;
}

/** Attachment slot in a Spine skeleton */
export interface SpineSlotSpec {
  name: string;
  bone: string;
  attachment?: string;
  color?: string;
  darkColor?: string;
  blend?: 'normal' | 'additive' | 'multiply' | 'screen';
}

/** Skin attachment mapping item */
export interface SpineSkinItem {
  slotName: string;
  attachmentName: string;
  path?: string;
  x?: number;
  y?: number;
  scaleX?: number;
  scaleY?: number;
  rotation?: number;
  width?: number;
  height?: number;
  regionCoords?: string;
}

/** Skeleton root container JSON */
export interface SpineSkeletonData {
  skeleton: {
    hash?: string;
    spine: string;
    x: number;
    y: number;
    width: number;
    height: number;
    images?: string;
    audio?: string;
  };
  bones: SpineBoneSpec[];
  slots: SpineSlotSpec[];
  skins?: {
    default?: Record<string, Record<string, SpineSkinItem>>;
    [skinName: string]: any;
  };
  animations?: Record<string, any>;
}

/** Skeletal Inspector UI state */
export interface SpineInspectorState {
  selectedBoneName: string;
  hoveredBoneName: string | null;
  showBones: boolean;
  showJointNodes: boolean;
  showSlotBounds: boolean;
  wireframeOnly: boolean;
  previewRotationOffset: number;
  activeSpecTab: 'skeleton_json' | 'libgdx_atlas' | 'runtime_code';
}

// ============================================================================
// 5. Multi-Engine Export & Integration Types
// ============================================================================

/** Supported game engine target */
export type EngineTarget = 'godot' | 'unity' | 'phaser' | 'pixijs';

/** Godot 4.x specific export options */
export interface GodotExportConfig {
  targetNode: 'CharacterBody2D' | 'AnimatedSprite2D' | 'AnimationPlayer';
  textureFilter: 'nearest' | 'linear';
  useNormalMapMaterial: boolean;
  addCollisionShape: boolean;
  collisionType: 'capsule' | 'rectangle';
  generateSceneTscn: boolean;
  generateSpriteFramesTres: boolean;
  generateGdScript: boolean;
}

/** Unity 2D URP export options */
export interface UnityExportConfig {
  pixelsPerUnit: 16 | 32 | 64 | 100 | 128;
  spriteMode: 'Single' | 'Multiple';
  materialType: 'Sprite-Lit-Default' | 'Sprites-Default' | 'CustomShaderGraph';
  generatePrefab: boolean;
  generateAnimatorController: boolean;
  generateCSharpController: boolean;
  alphaIsTransparency: boolean;
}

/** Phaser 3 export options */
export interface PhaserExportConfig {
  physicsEngine: 'arcade' | 'matter' | 'none';
  frameRate: number;
  enableLight2DPipeline: boolean;
  generateSceneClass: boolean;
  language: 'typescript' | 'javascript';
  atlasFormat: 'jsonHash' | 'jsonArray';
}

/** PixiJS export options */
export interface PixiExportConfig {
  animationSpeed: number;
  anchorX: number;
  anchorY: number;
  autoPlay: boolean;
  enableFilters: boolean;
  moduleFormat: 'esm' | 'cjs';
  language: 'typescript' | 'javascript';
}

/** Master configuration state for all engine targets */
export interface EnginePlaygroundState {
  activeEngine: EngineTarget;
  godot: GodotExportConfig;
  unity: UnityExportConfig;
  phaser: PhaserExportConfig;
  pixi: PixiExportConfig;
}

/** Export manifest file item with download action */
export interface ExportManifestItem {
  id: string;
  name: string;
  engine: EngineTarget;
  category: 'scene' | 'resource' | 'atlas' | 'shader' | 'script';
  relativePath: string;
  sizeBytes: number;
  downloadUrl: string;
  description: string;
}

// ============================================================================
// 6. Sound Effects & Web Audio Synthesizer Types
// ============================================================================

/** Procedural sound effect identifier */
export type SoundEffectId = 
  | 'ui_click'
  | 'ui_tab'
  | 'step_run'
  | 'attack_slash'
  | 'defend_shield'
  | 'jump_ascend'
  | 'hurt_impact'
  | 'torch_light'
  | 'export_complete';

/** Audio synthesizer voice configuration */
export interface SynthVoiceConfig {
  type: OscillatorType;
  startFreq: number;
  endFreq: number;
  durationSec: number;
  gain: number;
  filterFreq?: number;
  filterType?: BiquadFilterType;
}
