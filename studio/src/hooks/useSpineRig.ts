/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Spine 2D Skeletal Hierarchy & Forward Kinematics Hook
 * 
 * Dynamically computes forward kinematics, 2D affine matrix transformations,
 * hierarchical tree traversal, canvas hit-testing for interactive bone selection,
 * and live runtime export specifications directly from loaded Spine 2D asset data.
 * Zero hardcoded bone coordinates: all data is loaded and derived from pipeline assets.
 */

import { useState, useMemo, useCallback, useEffect } from 'react';
import {
  CharacterRuntimeAsset,
  SpineBoneSpec,
  SpineSlotSpec,
  SpineInspectorState,
  ComputedWorldBone,
  Vec2
} from '../types';
import { audio } from '../lib/audio';

/**
 * 2D Affine Transformation Matrix [a, b, c, d, tx, ty]
 * Used for forward kinematics composition:
 * [ x' ]   [ a  c  tx ] [ x ]
 * [ y' ] = [ b  d  ty ] [ y ]
 * [ 1  ]   [ 0  0   1 ] [ 1 ]
 */
export interface Matrix2D {
  a: number;
  b: number;
  c: number;
  d: number;
  tx: number;
  ty: number;
}

/**
 * Creates identity matrix
 */
export function createIdentityMatrix(): Matrix2D {
  return { a: 1, b: 0, c: 0, d: 1, tx: 0, ty: 0 };
}

/**
 * Multiplies two 2D affine matrices (m1 * m2)
 */
export function multiplyMatrices(m1: Matrix2D, m2: Matrix2D): Matrix2D {
  return {
    a: m1.a * m2.a + m1.c * m2.b,
    b: m1.b * m2.a + m1.d * m2.b,
    c: m1.a * m2.c + m1.c * m2.d,
    d: m1.b * m2.c + m1.d * m2.d,
    tx: m1.a * m2.tx + m1.c * m2.ty + m1.tx,
    ty: m1.b * m2.tx + m1.d * m2.ty + m1.ty
  };
}

/**
 * Creates affine transformation matrix from Spine translation, rotation (degrees), and scale
 */
export function createTransformMatrix(
  x: number,
  y: number,
  rotationDeg: number,
  scaleX: number = 1.0,
  scaleY: number = 1.0
): Matrix2D {
  const rad = (rotationDeg * Math.PI) / 180.0;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);

  return {
    a: cos * scaleX,
    b: sin * scaleX,
    c: -sin * scaleY,
    d: cos * scaleY,
    tx: x,
    ty: y
  };
}

/**
 * Transforms a 2D point using an affine matrix
 */
export function transformPoint(m: Matrix2D, point: Vec2): Vec2 {
  return {
    x: m.a * point.x + m.c * point.y + m.tx,
    y: m.b * point.x + m.d * point.y + m.ty
  };
}

/**
 * Normalizes angle to range [-180, 180] degrees
 */
export function normalizeAngleDegrees(degrees: number): number {
  let normalized = degrees % 360;
  if (normalized > 180) normalized -= 360;
  if (normalized < -180) normalized += 360;
  return normalized;
}

/**
 * Decomposes 2D matrix into translation, rotation (degrees), and scale
 */
export function decomposeMatrix(m: Matrix2D): { x: number; y: number; rotation: number; scaleX: number; scaleY: number } {
  const x = m.tx;
  const y = m.ty;
  const scaleX = Math.hypot(m.a, m.b);
  const scaleY = Math.hypot(m.c, m.d);
  const rotation = (Math.atan2(m.b, m.a) * 180.0) / Math.PI;

  return {
    x,
    y,
    rotation: normalizeAngleDegrees(rotation),
    scaleX,
    scaleY
  };
}

/**
 * Hook for managing interactive Spine 2D skeletal rig, forward kinematics,
 * hierarchical bone inspection, and runtime specification generation.
 */
export function useSpineRig(char: CharacterRuntimeAsset) {
  const [inspectorState, setInspectorState] = useState<SpineInspectorState>({
    selectedBoneName: '',
    hoveredBoneName: null,
    showBones: true,
    showJointNodes: true,
    showSlotBounds: true,
    wireframeOnly: false,
    previewRotationOffset: 0,
    activeSpecTab: 'skeleton_json'
  });

  /**
   * Resolved bone list derived directly from character Spine data
   * Zero hardcoding: pure dynamic reading from the active character's spineData
   */
  const rawBones = useMemo<SpineBoneSpec[]>(() => {
    if (char.spineData && Array.isArray(char.spineData.bones)) {
      return char.spineData.bones;
    }
    return [];
  }, [char.spineData]);

  /**
   * Resolved slot list derived directly from character Spine data
   */
  const rawSlots = useMemo<SpineSlotSpec[]>(() => {
    if (char.spineData && Array.isArray(char.spineData.slots)) {
      return char.spineData.slots;
    }
    return [];
  }, [char.spineData]);

  /**
   * Automatically select first primary non-root bone when bones are loaded
   */
  useEffect(() => {
    if (rawBones.length === 0) return;

    // If no bone selected or current selection is not in the active bone set, pick intelligent default
    const hasSelection = rawBones.some((b) => b.name === inspectorState.selectedBoneName);
    if (!hasSelection || inspectorState.selectedBoneName === 'root') {
      const preferredDefaults = ['chest', 'spine', 'pelvis', 'body'];
      let chosenBone = rawBones.find((b) => preferredDefaults.includes(b.name))?.name;
      if (!chosenBone) {
        // Fallback to first bone that is not 'root'
        chosenBone = rawBones.find((b) => b.name !== 'root')?.name || rawBones[0]?.name || '';
      }
      if (chosenBone && chosenBone !== inspectorState.selectedBoneName) {
        setInspectorState((prev) => ({
          ...prev,
          selectedBoneName: chosenBone,
          previewRotationOffset: 0
        }));
      }
    }
  }, [rawBones, inspectorState.selectedBoneName]);

  /**
   * Forward Kinematics Solver:
   * Traverses bone parent-child hierarchy in Spine 2D Cartesian space (Y-up)
   * and maps coordinates to HTML5 Canvas 2D space (Y-down).
   */
  const computedBones = useMemo<ComputedWorldBone[]>(() => {
    if (rawBones.length === 0) return [];

    const result: ComputedWorldBone[] = [];
    const boneMap = new Map<string, SpineBoneSpec>();
    rawBones.forEach((b) => boneMap.set(b.name, b));

    // World transform cache in Spine Cartesian space { x, y, rot }
    const spineWorldTransforms = new Map<string, { x: number; y: number; rot: number }>();

    // Baseline canvas datum position (feet ground level)
    const datumX = 288.0;
    const datumY = 460.0;

    /**
     * Helper: Recursively compute world transform in Spine Cartesian coordinates
     */
    const computeSpineWorldTransform = (bName: string): { x: number; y: number; rot: number } => {
      if (spineWorldTransforms.has(bName)) {
        return spineWorldTransforms.get(bName)!;
      }

      const bone = boneMap.get(bName);
      if (!bone) {
        return { x: 0, y: 0, rot: 0 };
      }

      let extraRot = 0;
      if (bone.name === inspectorState.selectedBoneName) {
        extraRot = inspectorState.previewRotationOffset;
      }

      // Root bone or bone without valid parent
      if (!bone.parent || !boneMap.has(bone.parent)) {
        const rootTransform = {
          x: bone.x || 0,
          y: bone.y || 0,
          rot: (bone.rotation || 0) + extraRot
        };
        spineWorldTransforms.set(bName, rootTransform);
        return rootTransform;
      }

      // Compute parent world transform
      const parentTransform = computeSpineWorldTransform(bone.parent);
      const parentRad = (parentTransform.rot * Math.PI) / 180.0;
      const cosP = Math.cos(parentRad);
      const sinP = Math.sin(parentRad);

      const localX = bone.x || 0;
      const localY = bone.y || 0;

      // Rotate local translation by parent rotation
      const worldX = parentTransform.x + localX * cosP - localY * sinP;
      const worldY = parentTransform.y + localX * sinP + localY * cosP;
      const worldRot = parentTransform.rot + (bone.rotation || 0) + extraRot;

      const res = { x: worldX, y: worldY, rot: worldRot };
      spineWorldTransforms.set(bName, res);
      return res;
    };

    // Calculate canvas coordinates for all bones
    rawBones.forEach((b) => {
      const spineTrans = computeSpineWorldTransform(b.name);
      const len = b.length || 0;
      const rad = (spineTrans.rot * Math.PI) / 180.0;

      // Transform from Spine Cartesian space (Y-up, origin at ground) to Canvas 2D space (Y-down)
      const startX = datumX + spineTrans.x;
      const startY = datumY - spineTrans.y;

      // In Canvas space, a vector pointing along angle θ has:
      // dx = L * cos(θ)
      // dy = -L * sin(θ) (since Canvas +Y points down)
      const endX = len > 0 ? startX + len * Math.cos(rad) : startX;
      const endY = len > 0 ? startY - len * Math.sin(rad) : startY;

      result.push({
        name: b.name,
        parentName: b.parent || null,
        startX,
        startY,
        endX,
        endY,
        worldRotation: spineTrans.rot,
        length: len,
        color: b.color ? `#${b.color}` : '#6366f1',
        isSelected: b.name === inspectorState.selectedBoneName,
        isHovered: b.name === inspectorState.hoveredBoneName
      });
    });

    return result;
  }, [rawBones, inspectorState.selectedBoneName, inspectorState.hoveredBoneName, inspectorState.previewRotationOffset]);

  /**
   * Select bone by name
   */
  const selectBone = useCallback((boneName: string) => {
    setInspectorState((prev) => ({
      ...prev,
      selectedBoneName: boneName,
      previewRotationOffset: 0
    }));
    audio.play('ui_click');
  }, []);

  /**
   * Set bone hover state
   */
  const setHoveredBone = useCallback((boneName: string | null) => {
    setInspectorState((prev) => ({ ...prev, hoveredBoneName: boneName }));
  }, []);

  /**
   * Hit test canvas coordinate against bones to find clicked/hovered bone
   */
  const hitTestBone = useCallback((canvasX: number, canvasY: number): string | null => {
    let closestBone: string | null = null;
    let minDistance = 22.0;

    for (let i = 0; i < computedBones.length; i++) {
      const b = computedBones[i];

      // Test distance to start joint node
      const dStart = Math.hypot(canvasX - b.startX, canvasY - b.startY);
      if (dStart < minDistance) {
        minDistance = dStart;
        closestBone = b.name;
      }

      // Test distance to bone line segment
      if (b.length > 5) {
        const dx = b.endX - b.startX;
        const dy = b.endY - b.startY;
        const lenSq = dx * dx + dy * dy;

        if (lenSq > 0) {
          const t = Math.max(0, Math.min(1, ((canvasX - b.startX) * dx + (canvasY - b.startY) * dy) / lenSq));
          const projX = b.startX + t * dx;
          const projY = b.startY + t * dy;
          const dLine = Math.hypot(canvasX - projX, canvasY - projY);

          if (dLine < minDistance) {
            minDistance = dLine;
            closestBone = b.name;
          }
        }
      }
    }

    return closestBone;
  }, [computedBones]);

  /**
   * Toggle visual inspector display flags
   */
  const toggleSetting = useCallback((setting: keyof Pick<SpineInspectorState, 'showBones' | 'showJointNodes' | 'showSlotBounds' | 'wireframeOnly'>) => {
    setInspectorState((prev) => ({
      ...prev,
      [setting]: !prev[setting]
    }));
    audio.play('ui_click');
  }, []);

  /**
   * Update live rotation preview offset for selected bone
   */
  const setPreviewRotationOffset = useCallback((offset: number) => {
    setInspectorState((prev) => ({
      ...prev,
      previewRotationOffset: offset
    }));
  }, []);

  /**
   * Set active specification tab
   */
  const setActiveSpecTab = useCallback((tab: 'skeleton_json' | 'libgdx_atlas' | 'runtime_code') => {
    setInspectorState((prev) => ({
      ...prev,
      activeSpecTab: tab
    }));
    audio.play('ui_click');
  }, []);

  /**
   * Render 2D Skeletal Bones and Joint Nodes onto target Canvas context
   */
  const renderSkeletalOverlay = useCallback((
    ctx: CanvasRenderingContext2D,
    _originPivot: Vec2
  ) => {
    if (!inspectorState.showBones && !inspectorState.showJointNodes) return;

    ctx.save();

    // 1. Render Bone vectors
    if (inspectorState.showBones) {
      computedBones.forEach((bone) => {
        // Skip zero-length root bone in polygon pass
        if (bone.length <= 5) return;

        const isSelected = bone.isSelected;
        const isHovered = bone.isHovered;

        ctx.strokeStyle = isSelected
          ? '#00f0ff'
          : isHovered
          ? '#a855f7'
          : 'rgba(99, 102, 241, 0.75)';

        ctx.fillStyle = isSelected
          ? 'rgba(0, 240, 255, 0.3)'
          : isHovered
          ? 'rgba(168, 85, 247, 0.22)'
          : 'rgba(99, 102, 241, 0.12)';

        ctx.lineWidth = isSelected ? 2.5 : 1.5;

        // Draw tapered skeletal bone polygon in canvas space
        const dx = bone.endX - bone.startX;
        const dy = bone.endY - bone.startY;
        const boneAngle = Math.atan2(dy, dx);
        const perpAngle = boneAngle + Math.PI / 2.0;

        const perpX = Math.cos(perpAngle);
        const perpY = Math.sin(perpAngle);
        const headWidth = Math.min(9, bone.length * 0.18);

        const midX = bone.startX + dx * 0.25;
        const midY = bone.startY + dy * 0.25;

        ctx.beginPath();
        ctx.moveTo(bone.startX, bone.startY);
        ctx.lineTo(midX + perpX * headWidth, midY + perpY * headWidth);
        ctx.lineTo(bone.endX, bone.endY);
        ctx.lineTo(midX - perpX * headWidth, midY - perpY * headWidth);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      });
    }

    // 2. Render Joint Nodes
    if (inspectorState.showJointNodes) {
      computedBones.forEach((bone) => {
        // Render root as ground baseline datum crosshair
        if (bone.name === 'root') {
          ctx.save();
          ctx.strokeStyle = 'rgba(148, 163, 184, 0.45)';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(bone.startX, bone.startY, 4, 0, Math.PI * 2);
          ctx.stroke();
          ctx.moveTo(bone.startX - 8, bone.startY);
          ctx.lineTo(bone.startX + 8, bone.startY);
          ctx.moveTo(bone.startX, bone.startY - 8);
          ctx.lineTo(bone.startX, bone.startY + 8);
          ctx.stroke();
          ctx.restore();
          return;
        }

        const isSelected = bone.isSelected;
        ctx.fillStyle = isSelected ? '#00f0ff' : '#ffffff';
        ctx.strokeStyle = isSelected ? '#ffffff' : '#4f46e5';
        ctx.lineWidth = isSelected ? 2 : 1.5;

        ctx.beginPath();
        ctx.arc(bone.startX, bone.startY, isSelected ? 5.5 : 3.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // High-contrast HUD pill label for selected bone
        if (isSelected) {
          ctx.save();
          const labelText = `${bone.name.toUpperCase()} (${bone.length.toFixed(0)}px)`;
          ctx.font = '600 11px Inter, sans-serif';
          const textMetrics = ctx.measureText(labelText);
          const badgeW = textMetrics.width + 16;
          const badgeH = 22;
          const badgeX = bone.startX + 12;
          const badgeY = bone.startY - 26;

          // Background pill
          ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
          ctx.strokeStyle = '#00f0ff';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 6);
          ctx.fill();
          ctx.stroke();

          // Text label
          ctx.fillStyle = '#00f0ff';
          ctx.fillText(labelText, badgeX + 8, badgeY + 15);
          ctx.restore();
        }
      });
    }

    ctx.restore();
  }, [computedBones, inspectorState.showBones, inspectorState.showJointNodes]);

  /**
   * Currently active selected bone details
   */
  const selectedBone = useMemo(() => {
    return computedBones.find((b) => b.name === inspectorState.selectedBoneName) || computedBones[0] || null;
  }, [computedBones, inspectorState.selectedBoneName]);

  /**
   * Helper: Resolve slot attachment details for selected bone
   */
  const selectedBoneSlots = useMemo(() => {
    if (!inspectorState.selectedBoneName) return [];
    return rawSlots.filter((s) => s.bone === inspectorState.selectedBoneName);
  }, [rawSlots, inspectorState.selectedBoneName]);

  /**
   * Export JSON string for active skeleton
   */
  const exportSkeletonJson = useCallback((): string => {
    return JSON.stringify(
      {
        skeleton: char.spineData?.skeleton || {
          spine: '3.8.99',
          x: -150,
          y: 0,
          width: 300,
          height: 480
        },
        bones: rawBones,
        slots: rawSlots
      },
      null,
      2
    );
  }, [char.spineData, rawBones, rawSlots]);

  /**
   * Retrieves array of ancestor bone names from given bone to root
   */
  const getBoneAncestors = useCallback((boneName: string): string[] => {
    const ancestors: string[] = [];
    const map = new Map<string, SpineBoneSpec>();
    rawBones.forEach((b) => map.set(b.name, b));

    let current = map.get(boneName);
    while (current && current.parent && map.has(current.parent)) {
      ancestors.push(current.parent);
      current = map.get(current.parent);
    }
    return ancestors;
  }, [rawBones]);

  /**
   * Retrieves array of child bone names directly parenting to given bone
   */
  const getDirectChildren = useCallback((boneName: string): string[] => {
    return rawBones.filter((b) => b.parent === boneName).map((b) => b.name);
  }, [rawBones]);

  return {
    rawBones,
    rawSlots,
    computedBones,
    selectedBone,
    selectedBoneSlots,
    inspectorState,
    selectBone,
    setHoveredBone,
    hitTestBone,
    toggleSetting,
    setRotationOffset: setPreviewRotationOffset,
    setPreviewRotationOffset,
    setActiveSpecTab,
    onSelectBone: selectBone,
    onHoverBone: setHoveredBone,
    onHitTestBone: hitTestBone,
    onToggleSetting: toggleSetting,
    onSetPreviewRotationOffset: setPreviewRotationOffset,
    onSetActiveSpecTab: setActiveSpecTab,
    renderSkeletalOverlay,
    exportSkeletonJson,
    getBoneAncestors,
    getDirectChildren
  };
}
