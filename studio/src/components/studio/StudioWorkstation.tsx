/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Studio Workstation Component (Animation & Asset Workstation)
 * 
 * High-DPI Canvas Viewport, Precision Playback Bar, Onion Skinning,
 * Interactive Filmstrip, Visual Combat Gizmos, and Real-time Telemetry.
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  Crosshair,
  Maximize2,
  Shield,
  Layers,
  ZoomIn,
  CheckCircle2,
  Info
} from 'lucide-react';
import {
  CharacterRuntimeAsset,
  ResolvedFrameCoordinates,
  GizmoSettings,
  StageBackgroundMode,
  TelemetryState
} from '../../types';
import { audio } from '../../lib/audio';

interface StudioWorkstationProps {
  activeChar: CharacterRuntimeAsset;
  activeAnim: string;
  currentFrameIdx: number;
  isPlaying: boolean;
  playbackSpeed: number;
  totalFrames: number;
  currentFps: number;
  telemetry: TelemetryState;
  currentFrameCoordinates: ResolvedFrameCoordinates | null;
  filmstripFrames: ResolvedFrameCoordinates[];
  onSelectCharacter: (charId: 'the_architect' | 'the_guardian') => void;
  onSelectAnimation: (animName: string) => void;
  onTogglePlayPause: () => void;
  onStepForward: () => void;
  onStepBackward: () => void;
  onSeekFrame: (idx: number) => void;
  onChangeSpeed: (speed: number) => void;
  getResolvedFrame: (char: CharacterRuntimeAsset, anim: string, idx: number) => ResolvedFrameCoordinates | null;
}

export const StudioWorkstation: React.FC<StudioWorkstationProps> = ({
  activeChar,
  activeAnim,
  currentFrameIdx,
  isPlaying,
  playbackSpeed,
  totalFrames,
  currentFps,
  telemetry,
  currentFrameCoordinates,
  filmstripFrames,
  onSelectCharacter,
  onSelectAnimation,
  onTogglePlayPause,
  onStepForward,
  onStepBackward,
  onSeekFrame,
  onChangeSpeed,
  getResolvedFrame
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [bgMode, setBgMode] = useState<StageBackgroundMode>('grid-dark');
  const [zoomScale, setZoomScale] = useState<number>(1.0);
  const [sfxEnabled, setSfxEnabled] = useState<boolean>(true);

  // Gizmos state
  const [gizmos, setGizmos] = useState<GizmoSettings>({
    showHitbox: true,
    showPivot: true,
    showGroundLine: true,
    showFrameBox: false,
    showOnionSkin: false,
    onionSkinFrames: 2,
    onionSkinAlpha: 0.25,
    groundBaselineY: 460,
    hitboxBounds: { x: 180, y: 100, width: 216, height: 360 }
  });

  /**
   * Toggle individual gizmo
   */
  const toggleGizmo = (key: keyof Pick<GizmoSettings, 'showHitbox' | 'showPivot' | 'showGroundLine' | 'showFrameBox' | 'showOnionSkin'>) => {
    setGizmos((prev) => ({ ...prev, [key]: !prev[key] }));
    audio.play('ui_click');
  };

  /**
   * Toggle procedural audio effects
   */
  const handleToggleAudio = () => {
    const next = audio.toggleMute();
    setSfxEnabled(next);
  };

  /**
   * Canvas Rendering Pipeline: Sprite + Onion Skin + Visual Gizmos
   */
  const drawScene = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !activeChar.atlasImg || !currentFrameCoordinates) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear viewport
    ctx.clearRect(0, 0, width, height);

    // 1. Render Onion Skinning (Past frames with translucent ghosting)
    if (gizmos.showOnionSkin && totalFrames > 1) {
      for (let offset = gizmos.onionSkinFrames; offset >= 1; offset--) {
        const pastIdx = (currentFrameIdx - offset + totalFrames) % totalFrames;
        const pastCoords = getResolvedFrame(activeChar, activeAnim, pastIdx);
        if (pastCoords) {
          ctx.save();
          ctx.globalAlpha = gizmos.onionSkinAlpha / offset;
          ctx.filter = 'hue-rotate(180deg) saturate(200%)';
          const { source: ps, dest: pd } = pastCoords;
          ctx.drawImage(activeChar.atlasImg, ps.x, ps.y, ps.w, ps.h, pd.x, pd.y, pd.w, pd.h);
          ctx.restore();
        }
      }
    }

    // 2. Render Active Sprite Frame
    const { source: s, dest: d } = currentFrameCoordinates;
    ctx.drawImage(activeChar.atlasImg, s.x, s.y, s.w, s.h, d.x, d.y, d.w, d.h);

    // 3. Render Combat Hurtbox Gizmo
    if (gizmos.showHitbox) {
      ctx.save();
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.85)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(gizmos.hitboxBounds.x, gizmos.hitboxBounds.y, gizmos.hitboxBounds.width, gizmos.hitboxBounds.height);
      ctx.fillStyle = 'rgba(239, 68, 68, 0.08)';
      ctx.fillRect(gizmos.hitboxBounds.x, gizmos.hitboxBounds.y, gizmos.hitboxBounds.width, gizmos.hitboxBounds.height);
      ctx.restore();
    }

    // 4. Render Ground Baseline Gizmo (Y = 460)
    if (gizmos.showGroundLine) {
      ctx.save();
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.75)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 6]);
      ctx.beginPath();
      ctx.moveTo(32, gizmos.groundBaselineY);
      ctx.lineTo(width - 32, gizmos.groundBaselineY);
      ctx.stroke();

      ctx.fillStyle = 'rgba(16, 185, 129, 0.9)';
      ctx.font = '10px JetBrains Mono, monospace';
      ctx.fillText(`BASELINE Y=${gizmos.groundBaselineY}`, 36, gizmos.groundBaselineY - 6);
      ctx.restore();
    }

    // 5. Render Ground Pivot Gizmo (0.5, 0.90)
    if (gizmos.showPivot) {
      const px = width * (currentFrameCoordinates.pivot?.x || 0.5);
      const py = height * (currentFrameCoordinates.pivot?.y || 0.90);

      ctx.save();
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.95)';
      ctx.fillStyle = 'rgba(56, 189, 248, 0.25)';
      ctx.lineWidth = 2;

      ctx.beginPath();
      ctx.arc(px, py, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(px - 10, py);
      ctx.lineTo(px + 10, py);
      ctx.moveTo(px, py - 10);
      ctx.lineTo(px, py + 10);
      ctx.stroke();
      ctx.restore();
    }

    // 6. Render Canvas Frame Boundary (576x512)
    if (gizmos.showFrameBox) {
      ctx.save();
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
      ctx.lineWidth = 1;
      ctx.strokeRect(1, 1, width - 2, height - 2);
      ctx.restore();
    }
  }, [
    activeChar,
    activeAnim,
    currentFrameIdx,
    currentFrameCoordinates,
    gizmos,
    totalFrames,
    getResolvedFrame
  ]);

  // Redraw whenever frame or gizmos change
  useEffect(() => {
    drawScene();
  }, [drawScene]);

  // Timeline progress percentage
  const progressPercent = totalFrames > 0 ? ((currentFrameIdx + 1) / totalFrames) * 100 : 0;

  // Available animation names from metadata
  const availableAnimations = activeChar.meta ? Object.keys(activeChar.meta.animations) : ['idle', 'run', 'jump'];

  return (
    <div className="studio-workstation-layout">
      {/* ====================================================================
          LEFT COLUMN: CHARACTER & WORKSTATION CONTROLS
          ==================================================================== */}
      <aside className="studio-sidebar">
        {/* Character Switcher Panel */}
        <div className="wb-panel-card">
          <div className="panel-head">
            <span className="panel-label">ACTIVE CHARACTER</span>
            <span className="live-dot">v2.0 Native</span>
          </div>

          <div className="char-picker">
            <button
              className={`char-pill-btn ${activeChar.id === 'the_architect' ? 'active' : ''}`}
              onClick={() => onSelectCharacter('the_architect')}
            >
              <div className="char-avatar avatar-arch" />
              <div className="char-pill-text">
                <div className="char-title">The Architect</div>
                <div className="char-spec">Cyberblade • 24 frames</div>
              </div>
              <CheckCircle2 className="char-check-icon" />
            </button>

            <button
              className={`char-pill-btn ${activeChar.id === 'the_guardian' ? 'active' : ''}`}
              onClick={() => onSelectCharacter('the_guardian')}
            >
              <div className="char-avatar avatar-guard" />
              <div className="char-pill-text">
                <div className="char-title">The Guardian</div>
                <div className="char-spec">Armored Heavy • 24 frames</div>
              </div>
              <CheckCircle2 className="char-check-icon" />
            </button>
          </div>
        </div>

        {/* Action Sequences Panel */}
        <div className="wb-panel-card">
          <div className="panel-head">
            <span className="panel-label">ACTION SEQUENCES</span>
            <span className="live-dot">{currentFps} FPS</span>
          </div>

          <div className="actions-grid">
            {availableAnimations.map((animName) => {
              const info = activeChar.meta?.animations[animName];
              const isSelected = animName === activeAnim;
              return (
                <button
                  key={animName}
                  className={`action-pill ${isSelected ? 'active' : ''}`}
                  onClick={() => onSelectAnimation(animName)}
                >
                  <span>{animName.toUpperCase()}</span>
                  <span className="action-fcount">{info?.frame_count || 4}f</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Visual Gizmo Toggles Panel */}
        <div className="wb-panel-card">
          <div className="panel-head">
            <span className="panel-label">VISUAL GIZMOS</span>
            <Shield className="panel-icon-sm" />
          </div>

          <div className="gizmo-toggles">
            <label className="switch-row">
              <span className="switch-label">
                <Crosshair className="gizmo-icon" /> Combat Hurtbox
              </span>
              <input
                type="checkbox"
                checked={gizmos.showHitbox}
                onChange={() => toggleGizmo('showHitbox')}
                className="apple-toggle"
              />
            </label>

            <label className="switch-row">
              <span className="switch-label">
                <Layers className="gizmo-icon" /> Ground Pivot (0.5, 0.90)
              </span>
              <input
                type="checkbox"
                checked={gizmos.showPivot}
                onChange={() => toggleGizmo('showPivot')}
                className="apple-toggle"
              />
            </label>

            <label className="switch-row">
              <span className="switch-label">
                <Maximize2 className="gizmo-icon" /> Ground Baseline (Y=460)
              </span>
              <input
                type="checkbox"
                checked={gizmos.showGroundLine}
                onChange={() => toggleGizmo('showGroundLine')}
                className="apple-toggle"
              />
            </label>

            <label className="switch-row">
              <span className="switch-label">
                <ZoomIn className="gizmo-icon" /> Canvas Box (576×512)
              </span>
              <input
                type="checkbox"
                checked={gizmos.showFrameBox}
                onChange={() => toggleGizmo('showFrameBox')}
                className="apple-toggle"
              />
            </label>

            <label className="switch-row">
              <span className="switch-label">
                <Layers className="gizmo-icon" /> Onion Skinning (Ghost)
              </span>
              <input
                type="checkbox"
                checked={gizmos.showOnionSkin}
                onChange={() => toggleGizmo('showOnionSkin')}
                className="apple-toggle"
              />
            </label>
          </div>
        </div>

        {/* Real-Time Frame Telemetry Panel */}
        <div className="wb-panel-card telemetry-card">
          <div className="panel-head">
            <span className="panel-label">FRAME TELEMETRY</span>
            <Info className="panel-icon-sm" />
          </div>

          <div className="telemetry-grid">
            <div className="telemetry-item">
              <span className="telemetry-label">Trimmed Bounds:</span>
              <strong className="telemetry-value">
                {telemetry.frameWidth}×{telemetry.frameHeight} px
              </strong>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-label">Canvas Placement:</span>
              <strong className="telemetry-value">
                ({currentFrameCoordinates?.dest.x || 0}, {currentFrameCoordinates?.dest.y || 0})
              </strong>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-label">Pivot Anchor:</span>
              <strong className="telemetry-value">(288, 460)</strong>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-label">Alpha Trimming:</span>
              <strong className="telemetry-value text-emerald">Zero-Halo Defringed</strong>
            </div>
          </div>
        </div>
      </aside>

      {/* ====================================================================
          CENTER COLUMN: HIGH-DPI CANVAS VIEWPORT & TIMELINE CONTROLS
          ==================================================================== */}
      <section className="studio-viewport-column">
        {/* Stage Container */}
        <div className="viewport-stage-container">
          {/* Top Stage Control Header */}
          <div className="stage-top-controls">
            <div className="stage-sequence-info">
              <span className="seq-badge">ACTION</span>
              <strong className="seq-title">
                {activeAnim.toUpperCase()} ({totalFrames}f @ {currentFps}fps)
              </strong>
            </div>

            <div className="stage-utility-group">
              {/* Zoom Buttons */}
              <div className="segmented-group">
                <button
                  className={`segment-btn ${zoomScale === 1.0 ? 'active' : ''}`}
                  onClick={() => setZoomScale(1.0)}
                >
                  1x
                </button>
                <button
                  className={`segment-btn ${zoomScale === 1.4 ? 'active' : ''}`}
                  onClick={() => setZoomScale(1.4)}
                >
                  1.4x
                </button>
              </div>

              {/* Stage Background Patterns */}
              <div className="segmented-group">
                <button
                  className={`segment-btn ${bgMode === 'grid-dark' ? 'active' : ''}`}
                  onClick={() => setBgMode('grid-dark')}
                  title="Dark Grid"
                >
                  Grid
                </button>
                <button
                  className={`segment-btn ${bgMode === 'grid-slate' ? 'active' : ''}`}
                  onClick={() => setBgMode('grid-slate')}
                  title="Slate"
                >
                  Slate
                </button>
                <button
                  className={`segment-btn ${bgMode === 'checker' ? 'active' : ''}`}
                  onClick={() => setBgMode('checker')}
                  title="Checkerboard"
                >
                  Alpha
                </button>
              </div>
            </div>
          </div>

          {/* HTML5 Canvas Viewport */}
          <div className={`canvas-stage-wrapper bg-${bgMode}`}>
            <canvas
              ref={canvasRef}
              width={576}
              height={512}
              className="stage-canvas-element"
              style={{ transform: `scale(${zoomScale})` }}
            />
          </div>

          {/* Precision Playback Bar */}
          <div className="playback-toolbar">
            <div className="playback-controls-cluster">
              <button
                className="playback-btn"
                onClick={onStepBackward}
                title="Previous Frame (Left Arrow)"
              >
                <SkipBack className="playback-icon" />
              </button>

              <button
                className="playback-btn primary"
                onClick={onTogglePlayPause}
                title="Play / Pause (Space)"
              >
                {isPlaying ? <Pause className="playback-icon" /> : <Play className="playback-icon" />}
              </button>

              <button
                className="playback-btn"
                onClick={onStepForward}
                title="Next Frame (Right Arrow)"
              >
                <SkipForward className="playback-icon" />
              </button>

              <button
                className={`playback-btn ${sfxEnabled ? 'active' : ''}`}
                onClick={handleToggleAudio}
                title="Toggle SFX Audio"
              >
                {sfxEnabled ? <Volume2 className="playback-icon" /> : <VolumeX className="playback-icon" />}
              </button>
            </div>

            {/* Interactive Timeline Scrubber */}
            <div className="timeline-cluster">
              <div className="timeline-readouts">
                <span className="timeline-frame-counter">
                  Frame: <strong>{currentFrameIdx + 1}</strong> / {totalFrames}
                </span>
                <span className="timeline-seconds-counter">
                  {telemetry.playbackSec}s / {telemetry.durationSec}s
                </span>
              </div>

              <div
                className="timeline-scrubber-track"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
                  onSeekFrame(Math.floor(ratio * totalFrames));
                }}
              >
                <div
                  className="timeline-scrubber-fill"
                  style={{ width: `${progressPercent}%` }}
                />
                <div
                  className="timeline-scrubber-handle"
                  style={{ left: `${progressPercent}%` }}
                />
              </div>
            </div>

            {/* Playback Speed Multipliers */}
            <div className="speed-pills-cluster">
              {[0.25, 0.5, 1.0, 2.0].map((spd) => (
                <button
                  key={spd}
                  className={`spd-pill ${playbackSpeed === spd ? 'active' : ''}`}
                  onClick={() => onChangeSpeed(spd)}
                >
                  {spd}x
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ====================================================================
            BOTTOM SECTION: INTERACTIVE FILMSTRIP INSPECTOR
            ==================================================================== */}
        <div className="filmstrip-panel-card">
          <div className="panel-head">
            <div className="filmstrip-title-wrap">
              <Layers className="panel-icon-sm" />
              <span className="panel-label">SEQUENCE FILMSTRIP</span>
            </div>
            <span className="filmstrip-meta-desc">
              Click frame thumbnail to inspect slice coordinates and canvas offset
            </span>
          </div>

          <div className="filmstrip-track-scroller">
            {filmstripFrames.map((frameCoords, idx) => {
              const isSelected = idx === currentFrameIdx;
              return (
                <div
                  key={frameCoords.frameKey}
                  className={`filmstrip-frame-card ${isSelected ? 'active' : ''}`}
                  onClick={() => onSeekFrame(idx)}
                  title={`Frame ${idx}: ${frameCoords.frameKey}`}
                >
                  <div className="filmstrip-frame-header">
                    <span className="filmstrip-frame-index">#{idx}</span>
                    <span className="filmstrip-frame-dim">
                      {frameCoords.dest.w}×{frameCoords.dest.h}
                    </span>
                  </div>

                  {/* Thumbnail Box */}
                  <div className="filmstrip-thumbnail-box">
                    {activeChar.atlasImg && (
                      <div
                        className="filmstrip-sprite-preview"
                        style={{
                          backgroundImage: `url(${activeChar.atlasUrl})`,
                          backgroundPosition: `-${frameCoords.source.x * 0.15}px -${frameCoords.source.y * 0.15}px`,
                          backgroundSize: `${2048 * 0.15}px ${2048 * 0.15}px`,
                          width: `${frameCoords.source.w * 0.15}px`,
                          height: `${frameCoords.source.h * 0.15}px`
                        }}
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
};
