/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Spine 2D Skeletal Workstation Component
 * 
 * Interactive 2D Bone Rig Visualizer on Canvas, Forward Kinematics,
 * Bone Selection & Rotation Test, Attachment Slots, and Spine Spec Exporters.
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Bone,
  GitBranch,
  Sliders,
  Code,
  Copy,
  Download,
  Eye,
  EyeOff,
  Crosshair,
  FileJson,
  Check,
  RotateCcw
} from 'lucide-react';
import {
  CharacterRuntimeAsset,
  ResolvedFrameCoordinates,
  SpineInspectorState,
  SpineBoneSpec,
  SpineSlotSpec,
  ComputedWorldBone
} from '../../types';
import { audio } from '../../lib/audio';

interface SpineWorkstationProps {
  activeChar: CharacterRuntimeAsset;
  currentFrameCoordinates: ResolvedFrameCoordinates | null;
  rawBones: SpineBoneSpec[];
  rawSlots: SpineSlotSpec[];
  computedBones: ComputedWorldBone[];
  selectedBone: ComputedWorldBone | null;
  selectedBoneSlots: SpineSlotSpec[];
  inspectorState: SpineInspectorState;
  onSelectBone: (boneName: string) => void;
  onHoverBone: (boneName: string | null) => void;
  onHitTestBone: (canvasX: number, canvasY: number) => string | null;
  onToggleSetting: (setting: keyof Pick<SpineInspectorState, 'showBones' | 'showJointNodes' | 'showSlotBounds' | 'wireframeOnly'>) => void;
  onSetRotationOffset: (degrees: number) => void;
  onSetActiveSpecTab: (tab: 'skeleton_json' | 'libgdx_atlas' | 'runtime_code') => void;
  renderSkeletalOverlay: (ctx: CanvasRenderingContext2D, pivot: { x: number; y: number }) => void;
  exportSkeletonJson: () => string;
}

export const SpineWorkstation: React.FC<SpineWorkstationProps> = ({
  activeChar,
  currentFrameCoordinates,
  rawBones,
  rawSlots,
  computedBones,
  selectedBone,
  selectedBoneSlots,
  inspectorState,
  onSelectBone,
  onHoverBone,
  onHitTestBone,
  onToggleSetting,
  onSetRotationOffset,
  onSetActiveSpecTab,
  renderSkeletalOverlay,
  exportSkeletonJson
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  /**
   * Render Character Sprite Frame + Dynamic Skeletal Rig Overlay
   */
  const drawSpineScene = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    // 1. Draw character frame (unless Wireframe Only is engaged)
    if (!inspectorState.wireframeOnly && activeChar.atlasImg && currentFrameCoordinates) {
      const { source: s, dest: d } = currentFrameCoordinates;
      ctx.drawImage(activeChar.atlasImg, s.x, s.y, s.w, s.h, d.x, d.y, d.w, d.h);
    } else if (inspectorState.wireframeOnly) {
      // Draw subtle phantom silhouette in wireframe mode
      if (activeChar.atlasImg && currentFrameCoordinates) {
        ctx.save();
        ctx.globalAlpha = 0.15;
        const { source: s, dest: d } = currentFrameCoordinates;
        ctx.drawImage(activeChar.atlasImg, s.x, s.y, s.w, s.h, d.x, d.y, d.w, d.h);
        ctx.restore();
      }
    }

    // 2. Draw 2D Skeletal Rig (Bones and Joint Nodes)
    renderSkeletalOverlay(ctx, currentFrameCoordinates?.pivot || { x: 0.5, y: 0.90 });
  }, [activeChar, currentFrameCoordinates, inspectorState.wireframeOnly, renderSkeletalOverlay]);

  useEffect(() => {
    drawSpineScene();
  }, [drawSpineScene]);

  /**
   * Handle canvas click to select clicked bone
   */
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const canvasX = (e.clientX - rect.left) * scaleX;
    const canvasY = (e.clientY - rect.top) * scaleY;

    const hitBone = onHitTestBone(canvasX, canvasY);
    if (hitBone) {
      onSelectBone(hitBone);
    }
  };

  /**
   * Handle canvas hover to highlight hovered bone
   */
  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const canvasX = (e.clientX - rect.left) * scaleX;
    const canvasY = (e.clientY - rect.top) * scaleY;

    const hitBone = onHitTestBone(canvasX, canvasY);
    onHoverBone(hitBone);
  };

  /**
   * Copy spec content to clipboard
   */
  const handleCopySpec = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    audio.play('ui_click');
    setTimeout(() => setCopied(false), 2000);
  };

  // Content for active specification tab
  const activeSpecCode = inspectorState.activeSpecTab === 'skeleton_json'
    ? exportSkeletonJson()
    : inspectorState.activeSpecTab === 'libgdx_atlas'
    ? `${activeChar.name}_atlas.png\nsize: 2048,2048\nformat: RGBA8888\nfilter: Linear,Linear\nrepeat: none\n${rawSlots.map(s => `${s.name}\n  rotate: false\n  xy: 0, 0\n  size: 120, 120\n  orig: 120, 120\n  offset: 0, 0\n  index: -1`).join('\n')}`
    : `// Spine 2D TypeScript Runtime Initialization
import { SpinePlayer } from "@esotericsoftware/spine-player";

const player = new SpinePlayer("spine-player-container", {
  jsonUrl: "${activeChar.spineJsonUrl}",
  atlasUrl: "${activeChar.spineAtlasUrl}",
  animation: "idle",
  premultipliedAlpha: false,
  backgroundColor: "#00000000",
  showControls: true
});`;

  return (
    <div className="spine-workstation-layout">
      {/* ====================================================================
          LEFT COLUMN: BONE HIERARCHY TREE & TRANSFORM INSPECTOR
          ==================================================================== */}
      <aside className="spine-sidebar">
        {/* Bone Hierarchy Tree */}
        <div className="wb-panel-card">
          <div className="panel-head">
            <span className="panel-label">SKELETAL BONE TREE</span>
            <span className="tag-pill">{rawBones.length} Bones</span>
          </div>

          <div className="spine-bone-tree-list">
            {rawBones.map((bone) => {
              const isSelected = bone.name === inspectorState.selectedBoneName;
              return (
                <div
                  key={bone.name}
                  className={`tree-node-item ${isSelected ? 'active' : ''}`}
                  onClick={() => onSelectBone(bone.name)}
                >
                  <Bone className="tree-node-icon" />
                  <span className="tree-node-name">{bone.name}</span>
                  {bone.parent && (
                    <span className="tree-node-parent-badge">↳ {bone.parent}</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Bone Transform Diagnostics */}
        <div className="wb-panel-card">
          <div className="panel-head">
            <span className="panel-label">TRANSFORM DIAGNOSTICS</span>
            <span className="live-dot text-cyan">{selectedBone?.name || 'none'}</span>
          </div>

          <div className="bone-props-matrix">
            <div className="bone-prop-cell">
              <span className="cell-label">Parent Bone:</span>
              <strong className="cell-value">{selectedBone?.parentName || 'none (root)'}</strong>
            </div>
            <div className="bone-prop-cell">
              <span className="cell-label">Length:</span>
              <strong className="cell-value">{selectedBone?.length.toFixed(1)} px</strong>
            </div>
            <div className="bone-prop-cell">
              <span className="cell-label">World Origin:</span>
              <strong className="cell-value">
                ({selectedBone?.startX.toFixed(0)}, {selectedBone?.startY.toFixed(0)})
              </strong>
            </div>
            <div className="bone-prop-cell">
              <span className="cell-label">Rotation Angle:</span>
              <strong className="cell-value">{selectedBone?.worldRotation.toFixed(1)}°</strong>
            </div>
          </div>

          {/* Interactive Live Bone Rotation Offset Slider */}
          <div className="slider-control-group" style={{ marginTop: '12px' }}>
            <div className="slider-header-row">
              <span>Pose Rotation Offset</span>
              <span className="slider-val-badge">
                {inspectorState.previewRotationOffset > 0 ? `+${inspectorState.previewRotationOffset}°` : `${inspectorState.previewRotationOffset}°`}
              </span>
            </div>
            <input
              type="range"
              min={-90}
              max={90}
              step={1}
              value={inspectorState.previewRotationOffset}
              onChange={(e) => onSetRotationOffset(Number(e.target.value))}
              className="apple-range"
            />
          </div>

          {/* Reset Rotation Button */}
          {inspectorState.previewRotationOffset !== 0 && (
            <button
              className="secondary-action-btn"
              onClick={() => onSetRotationOffset(0)}
              style={{ marginTop: '8px' }}
            >
              <RotateCcw className="btn-icon-xs" /> Reset Rotation Offset
            </button>
          )}
        </div>

        {/* Rigging Visual Display Toggles */}
        <div className="wb-panel-card">
          <div className="panel-head">
            <span className="panel-label">RIGGING OVERLAYS</span>
            <Crosshair className="panel-icon-sm" />
          </div>

          <div className="gizmo-toggles">
            <label className="switch-row">
              <span className="switch-label">Draw Skeletal Bones</span>
              <input
                type="checkbox"
                checked={inspectorState.showBones}
                onChange={() => onToggleSetting('showBones')}
                className="apple-toggle"
              />
            </label>

            <label className="switch-row">
              <span className="switch-label">Draw Joint Anchor Nodes</span>
              <input
                type="checkbox"
                checked={inspectorState.showJointNodes}
                onChange={() => onToggleSetting('showJointNodes')}
                className="apple-toggle"
              />
            </label>

            <label className="switch-row">
              <span className="switch-label">Wireframe Only (Hide Sprite)</span>
              <input
                type="checkbox"
                checked={inspectorState.wireframeOnly}
                onChange={() => onToggleSetting('wireframeOnly')}
                className="apple-toggle"
              />
            </label>
          </div>
        </div>
      </aside>

      {/* ====================================================================
          CENTER COLUMN: LIVE SKELETAL CANVAS & SPEC VIEWER
          ==================================================================== */}
      <section className="spine-viewport-column">
        <div className="viewport-stage-container">
          {/* Stage Top Controls */}
          <div className="stage-top-controls">
            <div className="stage-sequence-info">
              <span className="seq-badge spine">SPINE 2D</span>
              <strong className="seq-title">
                {activeChar.name} Rig (Click any bone or joint on canvas to inspect)
              </strong>
            </div>

            <div className="stage-utility-group">
              <span className="telemetry-pill">
                Active Bone: <strong>{selectedBone?.name}</strong>
              </span>
            </div>
          </div>

          {/* Canvas Viewport */}
          <div className="canvas-stage-wrapper bg-grid-dark spine-canvas-wrapper">
            <canvas
              ref={canvasRef}
              width={576}
              height={512}
              onClick={handleCanvasClick}
              onMouseMove={handleCanvasMouseMove}
              className="stage-canvas-element"
            />
          </div>
        </div>

        {/* ====================================================================
            BOTTOM SECTION: ATTACHMENT SLOTS & SPEC EXPORTER
            ==================================================================== */}
        <div className="spine-spec-panel-card">
          <div className="panel-head">
            <div className="segmented-group">
              <button
                className={`segment-btn ${inspectorState.activeSpecTab === 'skeleton_json' ? 'active' : ''}`}
                onClick={() => onSetActiveSpecTab('skeleton_json')}
              >
                <FileJson className="btn-icon-xs" /> Skeleton JSON (3.8)
              </button>
              <button
                className={`segment-btn ${inspectorState.activeSpecTab === 'libgdx_atlas' ? 'active' : ''}`}
                onClick={() => onSetActiveSpecTab('libgdx_atlas')}
              >
                <GitBranch className="btn-icon-xs" /> libGDX .atlas
              </button>
              <button
                className={`segment-btn ${inspectorState.activeSpecTab === 'runtime_code' ? 'active' : ''}`}
                onClick={() => onSetActiveSpecTab('runtime_code')}
              >
                <Code className="btn-icon-xs" /> Web Player TS
              </button>
            </div>

            <div className="spec-actions-cluster">
              <button
                className="spec-copy-btn"
                onClick={() => handleCopySpec(activeSpecCode)}
              >
                {copied ? <Check className="btn-icon-xs" /> : <Copy className="btn-icon-xs" />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
              <a
                href={activeChar.spineJsonUrl}
                download={`${activeChar.id}_skeleton.json`}
                className="spec-download-btn"
              >
                <Download className="btn-icon-xs" /> Download
              </a>
            </div>
          </div>

          {/* Code Viewer */}
          <div className="code-viewer-container">
            <pre className="code-block">
              <code>{activeSpecCode}</code>
            </pre>
          </div>
        </div>
      </section>
    </div>
  );
};
