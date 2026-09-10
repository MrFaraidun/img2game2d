/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Dynamic Lighting Workstation Component
 * 
 * Interactive Multi-Light Stage Canvas, Real-Time Tangent Normal Shading,
 * Draggable Torchlight, A/B Split-Screen Slider, and Full-Res Channel Inspector.
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Sun,
  Flame,
  Zap,
  Split,
  Sliders,
  Sparkles,
  Eye,
  Crosshair,
  Compass,
  Layers,
  Check
} from 'lucide-react';
import {
  CharacterRuntimeAsset,
  ResolvedFrameCoordinates,
  LightingEngineState,
  LightingViewMode,
  DynamicLightSource
} from '../../types';
import { LIGHTING_PRESETS } from '../../hooks/useNormalLighting';
import { audio } from '../../lib/audio';

interface LightingWorkstationProps {
  activeChar: CharacterRuntimeAsset;
  currentFrameCoordinates: ResolvedFrameCoordinates | null;
  lightingState: LightingEngineState;
  onSetViewMode: (mode: LightingViewMode) => void;
  onApplyPreset: (presetId: string) => void;
  onSetPrimaryLightPosition: (x: number, y: number) => void;
  onUpdateActiveLight: (updates: Partial<DynamicLightSource>) => void;
  onSetAmbientLevel: (ambient: number) => void;
  onSetBloomBoost: (boost: number) => void;
  onSetSplitRatio: (ratio: number) => void;
  renderLightingScene: (
    ctx: CanvasRenderingContext2D,
    char: CharacterRuntimeAsset,
    coords: ResolvedFrameCoordinates
  ) => void;
}

export const LightingWorkstation: React.FC<LightingWorkstationProps> = ({
  activeChar,
  currentFrameCoordinates,
  lightingState,
  onSetViewMode,
  onApplyPreset,
  onSetPrimaryLightPosition,
  onUpdateActiveLight,
  onSetAmbientLevel,
  onSetBloomBoost,
  onSetSplitRatio,
  renderLightingScene
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [isDraggingLight, setIsDraggingLight] = useState<boolean>(false);
  const [activeAtlasTab, setActiveAtlasTab] = useState<'diffuse' | 'normal' | 'emission'>('diffuse');

  const activeLight = lightingState.lights.find((l) => l.id === lightingState.activeLightId) || lightingState.lights[0];

  /**
   * Render lighting frame on target canvas
   */
  const drawLighting = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !currentFrameCoordinates) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    renderLightingScene(ctx, activeChar, currentFrameCoordinates);
  }, [activeChar, currentFrameCoordinates, renderLightingScene]);

  useEffect(() => {
    drawLighting();
  }, [drawLighting]);

  /**
   * Handle Mouse Move over Stage Canvas for Interactive Light Position Tracking
   */
  const handleStageMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = Math.max(0, Math.min(canvas.width, (e.clientX - rect.left) * scaleX));
    const y = Math.max(0, Math.min(canvas.height, (e.clientY - rect.top) * scaleY));

    if (isDraggingLight || lightingState.viewMode === 'composite' || lightingState.viewMode === 'split') {
      onSetPrimaryLightPosition(x, y);
    }
  };

  /**
   * Preset Light Colors
   */
  const lightColorOptions = [
    { name: 'Neon Cyan', hex: '#00f0ff' },
    { name: 'Amber Torch', hex: '#f59e0b' },
    { name: 'Emerald Glow', hex: '#10b981' },
    { name: 'Electric Pink', hex: '#ec4899' },
    { name: 'Violet Surge', hex: '#8b5cf6' },
    { name: 'Daylight White', hex: '#ffffff' }
  ];

  return (
    <div className="lighting-workstation-layout">
      {/* ====================================================================
          LEFT COLUMN: LIGHT CONTROLS & PRESET MATRIX
          ==================================================================== */}
      <aside className="lighting-sidebar">
        {/* Preset Selector Card */}
        <div className="wb-panel-card">
          <div className="panel-head">
            <span className="panel-label">LIGHTING PRESETS</span>
            <Sparkles className="panel-icon-sm text-cyan" />
          </div>

          <div className="presets-vertical-list">
            {Object.values(LIGHTING_PRESETS).map((preset) => {
              const isSelected = preset.id === lightingState.activePresetId;
              return (
                <button
                  key={preset.id}
                  className={`preset-select-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => onApplyPreset(preset.id)}
                >
                  <div className="preset-btn-top">
                    <strong className="preset-name">{preset.name}</strong>
                    {isSelected && <Check className="preset-check-icon" />}
                  </div>
                  <p className="preset-desc">{preset.subtitle}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Dynamic Light Parameters Card */}
        <div className="wb-panel-card">
          <div className="panel-head">
            <span className="panel-label">POINT LIGHT INTENSITY</span>
            <span className="live-dot">{activeLight?.intensity.toFixed(1)}x</span>
          </div>

          <div className="slider-control-group">
            <div className="slider-header-row">
              <span>Light Radius</span>
              <span className="slider-val-badge">{activeLight?.radius} px</span>
            </div>
            <input
              type="range"
              min={150}
              max={700}
              step={10}
              value={activeLight?.radius || 350}
              onChange={(e) => onUpdateActiveLight({ radius: Number(e.target.value) })}
              className="apple-range"
            />
          </div>

          <div className="slider-control-group">
            <div className="slider-header-row">
              <span>Elevation (Z-Depth)</span>
              <span className="slider-val-badge">{activeLight?.zDepth} px</span>
            </div>
            <input
              type="range"
              min={10}
              max={150}
              step={5}
              value={activeLight?.zDepth || 45}
              onChange={(e) => onUpdateActiveLight({ zDepth: Number(e.target.value) })}
              className="apple-range"
            />
          </div>

          <div className="slider-control-group">
            <div className="slider-header-row">
              <span>Light Intensity</span>
              <span className="slider-val-badge">{activeLight?.intensity.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min={0.2}
              max={4.0}
              step={0.1}
              value={activeLight?.intensity || 2.0}
              onChange={(e) => onUpdateActiveLight({ intensity: Number(e.target.value) })}
              className="apple-range"
            />
          </div>

          {/* Light Color Swatches */}
          <div className="color-swatches-section">
            <span className="swatches-label">Light Source Color</span>
            <div className="swatches-palette">
              {lightColorOptions.map((c) => (
                <button
                  key={c.hex}
                  className={`color-swatch-dot ${activeLight?.colorHex === c.hex ? 'active' : ''}`}
                  style={{ backgroundColor: c.hex }}
                  onClick={() => onUpdateActiveLight({ colorHex: c.hex })}
                  title={c.name}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Global Ambient & Bloom Emission */}
        <div className="wb-panel-card">
          <div className="panel-head">
            <span className="panel-label">AMBIENT & BLOOM GLOW</span>
            <Sliders className="panel-icon-sm" />
          </div>

          <div className="slider-control-group">
            <div className="slider-header-row">
              <span>Ambient Base Fill</span>
              <span className="slider-val-badge">{lightingState.ambientBaseLevel.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min={0.0}
              max={0.8}
              step={0.05}
              value={lightingState.ambientBaseLevel}
              onChange={(e) => onSetAmbientLevel(Number(e.target.value))}
              className="apple-range"
            />
          </div>

          <div className="slider-control-group">
            <div className="slider-header-row">
              <span>Bloom Mask Amplification</span>
              <span className="slider-val-badge">{lightingState.bloomBoost.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min={0.0}
              max={3.5}
              step={0.1}
              value={lightingState.bloomBoost}
              onChange={(e) => onSetBloomBoost(Number(e.target.value))}
              className="apple-range"
            />
          </div>

          <div className="torch-tip-banner">
            <Compass className="tip-icon" />
            <span>Move your cursor or drag inside the stage to dynamically cast normal tangents.</span>
          </div>
        </div>
      </aside>

      {/* ====================================================================
          CENTER COLUMN: LIVE LIGHTING STAGE & A/B COMPARISON
          ==================================================================== */}
      <section className="lighting-viewport-column">
        <div className="viewport-stage-container">
          {/* Stage Top Controls */}
          <div className="stage-top-controls">
            {/* View Mode Tabs */}
            <div className="segmented-group">
              <button
                className={`segment-btn ${lightingState.viewMode === 'composite' ? 'active' : ''}`}
                onClick={() => onSetViewMode('composite')}
              >
                <Zap className="btn-icon-xs" /> Composite Lit
              </button>
              <button
                className={`segment-btn ${lightingState.viewMode === 'split' ? 'active' : ''}`}
                onClick={() => onSetViewMode('split')}
              >
                <Split className="btn-icon-xs" /> A/B Split View
              </button>
              <button
                className={`segment-btn ${lightingState.viewMode === 'normal_only' ? 'active' : ''}`}
                onClick={() => onSetViewMode('normal_only')}
              >
                <Compass className="btn-icon-xs" /> Tangent Normal
              </button>
              <button
                className={`segment-btn ${lightingState.viewMode === 'emission_only' ? 'active' : ''}`}
                onClick={() => onSetViewMode('emission_only')}
              >
                <Flame className="btn-icon-xs" /> Bloom Glow
              </button>
            </div>

            {/* Split Screen Slider Control (when in split mode) */}
            {lightingState.viewMode === 'split' && (
              <div className="split-ratio-controller">
                <span className="split-label">Split Position:</span>
                <input
                  type="range"
                  min={0.05}
                  max={0.95}
                  step={0.01}
                  value={lightingState.splitPositionRatio}
                  onChange={(e) => onSetSplitRatio(Number(e.target.value))}
                  className="split-slider-mini"
                />
                <span className="split-val">{(lightingState.splitPositionRatio * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>

          {/* Interactive Lighting Canvas Stage */}
          <div
            ref={containerRef}
            className="canvas-stage-wrapper bg-grid-dark lighting-interactive-stage"
            onMouseMove={handleStageMouseMove}
            onMouseDown={() => setIsDraggingLight(true)}
            onMouseUp={() => setIsDraggingLight(false)}
          >
            <canvas
              ref={canvasRef}
              width={576}
              height={512}
              className="stage-canvas-element"
            />

            {/* Floating Point Light Visual Gizmo Node */}
            {(lightingState.viewMode === 'composite' || lightingState.viewMode === 'split') && (
              <div
                className="torch-light-gizmo-node"
                style={{
                  left: `${(activeLight.x / 576) * 100}%`,
                  top: `${(activeLight.y / 512) * 100}%`,
                  boxShadow: `0 0 ${activeLight.radius * 0.25}px ${activeLight.colorHex}`
                }}
              >
                <div
                  className="torch-light-gizmo-center"
                  style={{ backgroundColor: activeLight.colorHex }}
                />
              </div>
            )}
          </div>
        </div>

        {/* ====================================================================
            BOTTOM SECTION: FULL-RESOLUTION ATLAS CHANNEL VIEWER
            ==================================================================== */}
        <div className="atlas-channels-panel-card">
          <div className="panel-head">
            <div className="channels-title-wrap">
              <Layers className="panel-icon-sm text-indigo" />
              <span className="panel-label">TEXTURE ATLAS MAP INSPECTOR</span>
            </div>

            {/* Channel Tabs */}
            <div className="segmented-group">
              <button
                className={`segment-btn ${activeAtlasTab === 'diffuse' ? 'active' : ''}`}
                onClick={() => { setActiveAtlasTab('diffuse'); audio.play('ui_click'); }}
              >
                Albedo Diffuse (2048²)
              </button>
              <button
                className={`segment-btn ${activeAtlasTab === 'normal' ? 'active' : ''}`}
                onClick={() => { setActiveAtlasTab('normal'); audio.play('ui_click'); }}
              >
                Tangent Normal (OpenGL +Y)
              </button>
              <button
                className={`segment-btn ${activeAtlasTab === 'emission' ? 'active' : ''}`}
                onClick={() => { setActiveAtlasTab('emission'); audio.play('ui_click'); }}
              >
                Bloom Emission (HDR Glow)
              </button>
            </div>
          </div>

          <div className="atlas-preview-strip">
            <div className="atlas-image-container">
              {activeAtlasTab === 'diffuse' && (
                <img
                  src={activeChar.atlasUrl}
                  alt="Diffuse Texture Atlas"
                  className="atlas-inspect-img"
                />
              )}
              {activeAtlasTab === 'normal' && (
                <img
                  src={activeChar.normalUrl}
                  alt="Tangent Normal Map Atlas"
                  className="atlas-inspect-img"
                />
              )}
              {activeAtlasTab === 'emission' && (
                <img
                  src={activeChar.emissionUrl}
                  alt="Bloom Emission Mask Atlas"
                  className="atlas-inspect-img"
                />
              )}
            </div>

            <div className="atlas-metadata-sidebar">
              <div className="meta-spec-row">
                <span className="meta-label">Format:</span>
                <strong className="meta-value">RGBA8888 POT</strong>
              </div>
              <div className="meta-spec-row">
                <span className="meta-label">Resolution:</span>
                <strong className="meta-value">2048 × 2048 px</strong>
              </div>
              <div className="meta-spec-row">
                <span className="meta-label">Pipeline:</span>
                <strong className="meta-value">Tangent Space +Y</strong>
              </div>
              <div className="meta-spec-row">
                <span className="meta-label">Alpha Edge:</span>
                <strong className="meta-value text-emerald">Zero-Halo Defringed</strong>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
