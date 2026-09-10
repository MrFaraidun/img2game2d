/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Top Navigation Header & Compact Telemetry Ribbon
 * 
 * Includes Pill Navigation, Character Quick-Switcher, Dual Theme Toggle,
 * 34px Telemetry Ribbon, and Global Export Modal.
 */

import React, { useState } from 'react';
import {
  Layers,
  Sun,
  Moon,
  Download,
  Share2,
  Sparkles,
  Zap,
  Bone,
  Cpu,
  Package,
  X,
  CheckCircle2,
  Activity,
  Box
} from 'lucide-react';
import {
  StudioTab,
  ThemeMode,
  CharacterRuntimeAsset,
  TelemetryState
} from '../../types';
import { audio } from '../../lib/audio';

interface HeaderProps {
  activeTab: StudioTab;
  theme: ThemeMode;
  activeChar: CharacterRuntimeAsset;
  telemetry: TelemetryState;
  onSelectTab: (tab: StudioTab) => void;
  onToggleTheme: () => void;
  onSelectCharacter: (charId: 'the_architect' | 'the_guardian') => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  theme,
  activeChar,
  telemetry,
  onSelectTab,
  onToggleTheme,
  onSelectCharacter
}) => {
  const [isExportModalOpen, setIsExportModalOpen] = useState<boolean>(false);

  const handleTabClick = (tab: StudioTab) => {
    onSelectTab(tab);
    audio.play('ui_tab');
  };

  const handleThemeClick = () => {
    onToggleTheme();
    audio.play('ui_click');
  };

  const handleOpenExportModal = () => {
    setIsExportModalOpen(true);
    audio.play('ui_click');
  };

  const handleCloseExportModal = () => {
    setIsExportModalOpen(false);
    audio.play('ui_click');
  };

  return (
    <header className="header-wrapper">
      {/* ====================================================================
          TOP NAVIGATION BAR
          ==================================================================== */}
      <div className="top-nav-bar">
        {/* Brand Group */}
        <div className="brand-group">
          <div className="brand-logo-wrap">
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="url(#brandGrad)" />
              <path d="M10 22L16 10L22 22H18L16 16L14 22H10Z" fill="white" />
              <defs>
                <linearGradient id="brandGrad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#4f46e5" />
                  <stop offset="1" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <div className="brand-titles">
            <div className="brand-name">
              img2game2d <span className="version-pill">v2.0 Framework</span>
            </div>
            <div className="brand-sub">Autonomous 2D Game Asset & Pipeline Studio</div>
          </div>
        </div>

        {/* Center Pill Navigation */}
        <nav className="pill-nav">
          <button
            className={`nav-pill ${activeTab === 'studio' ? 'active' : ''}`}
            onClick={() => handleTabClick('studio')}
          >
            <Layers className="nav-icon" />
            <span>Studio Canvas</span>
          </button>

          <button
            className={`nav-pill ${activeTab === 'lighting' ? 'active' : ''}`}
            onClick={() => handleTabClick('lighting')}
          >
            <Zap className="nav-icon" />
            <span>Dynamic Lighting</span>
          </button>

          <button
            className={`nav-pill ${activeTab === 'spine' ? 'active' : ''}`}
            onClick={() => handleTabClick('spine')}
          >
            <Bone className="nav-icon" />
            <span>Spine 2D</span>
          </button>

          <button
            className={`nav-pill ${activeTab === 'exports' ? 'active' : ''}`}
            onClick={() => handleTabClick('exports')}
          >
            <Cpu className="nav-icon" />
            <span>Engine Exports</span>
          </button>
        </nav>

        {/* Right Actions Cluster */}
        <div className="nav-actions">
          {/* Theme Switcher Button */}
          <button
            className="theme-toggle-btn"
            onClick={handleThemeClick}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          >
            {theme === 'dark' ? (
              <Sun className="theme-icon" />
            ) : (
              <Moon className="theme-icon" />
            )}
            <span className="theme-label">{theme === 'dark' ? 'Dark' : 'Light'}</span>
          </button>

          {/* GitHub Repo Link */}
          <a
            href="https://github.com/MrFaraidun/img2game2d"
            target="_blank"
            rel="noopener noreferrer"
            className="action-circle-btn"
            title="View on GitHub"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
          </a>

          {/* Export Packages Button */}
          <button
            className="primary-pill-btn"
            onClick={handleOpenExportModal}
          >
            <Download className="btn-icon-xs" />
            <span>Export Assets</span>
          </button>
        </div>
      </div>

      {/* ====================================================================
          SLEEK 34PX STATUS TELEMETRY RIBBON
          ==================================================================== */}
      <div className="studio-status-ribbon">
        <div className="ribbon-cluster left">
          <div className="ribbon-item">
            <span className="status-indicator-dot online" />
            <span className="ribbon-label">Character:</span>
            <strong className="ribbon-val">{activeChar.name}</strong>
          </div>

          <div className="ribbon-item">
            <span className="ribbon-label">Sequence:</span>
            <strong className="ribbon-val">
              {telemetry.animationName} ({telemetry.totalFrames}f @ {telemetry.currentFps}fps)
            </strong>
          </div>

          <div className="ribbon-item">
            <span className="ribbon-label">Atlas:</span>
            <strong className="ribbon-val">{telemetry.atlasResolution}</strong>
          </div>
        </div>

        <div className="ribbon-cluster right">
          <div className="ribbon-item">
            <span className="ribbon-label">Shading:</span>
            <strong className="ribbon-val">{telemetry.lightingConvention}</strong>
          </div>

          <div className="ribbon-item engine-badges-group">
            <span className="ribbon-label">Targets:</span>
            <span className="engine-micro-tag">Spine</span>
            <span className="engine-micro-tag">Godot</span>
            <span className="engine-micro-tag">Unity</span>
            <span className="engine-micro-tag">Phaser</span>
          </div>

          <div className="ribbon-item memory-item">
            <Activity className="ribbon-icon-micro" />
            <span className="ribbon-val-dim">{telemetry.renderTimeMs.toFixed(1)}ms</span>
          </div>
        </div>
      </div>

      {/* ====================================================================
          GLOBAL EXPORT PACKAGES MODAL OVERLAY
          ==================================================================== */}
      {isExportModalOpen && (
        <div
          className="export-modal-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget) handleCloseExportModal();
          }}
        >
          <div className="export-modal-dialog">
            <div className="modal-head">
              <div className="modal-title-group">
                <span className="modal-kicker">PRODUCTION RUNTIMES</span>
                <h3 className="modal-heading">Export Asset Packages</h3>
                <p className="modal-sub">
                  Target Character: <strong>{activeChar.name}</strong> (img2game2d v2.0 Framework)
                </p>
              </div>

              <button
                className="modal-close-btn"
                onClick={handleCloseExportModal}
                title="Close Modal"
              >
                <X className="btn-icon-sm" />
              </button>
            </div>

            <div className="modal-body">
              <div className="modal-packages-grid">
                {/* Spine 2D Card */}
                <div className="modal-package-card">
                  <div className="pkg-card-top">
                    <span className="pkg-badge spine">Spine 2D</span>
                    <a
                      href={`/exports/spine/${activeChar.id}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="pkg-external-link"
                    >
                      Browse ↗
                    </a>
                  </div>
                  <p className="pkg-text">
                    Skeleton JSON, libGDX atlas definitions, Tangent Normal & Bloom Emission textures.
                  </p>
                  <div className="pkg-action-buttons">
                    <a
                      href={`/exports/spine/${activeChar.id}/${activeChar.id}_skeleton.json`}
                      download
                      className="pkg-file-chip"
                    >
                      <Download className="btn-icon-micro" /> skeleton.json
                    </a>
                    <a
                      href={`/exports/spine/${activeChar.id}/${activeChar.id}.atlas`}
                      download
                      className="pkg-file-chip"
                    >
                      <Download className="btn-icon-micro" /> {activeChar.id}.atlas
                    </a>
                  </div>
                </div>

                {/* Godot 4.x Card */}
                <div className="modal-package-card">
                  <div className="pkg-card-top">
                    <span className="pkg-badge godot">Godot 4.x</span>
                    <a
                      href={`/exports/godot/${activeChar.id}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="pkg-external-link"
                    >
                      Browse ↗
                    </a>
                  </div>
                  <p className="pkg-text">
                    CharacterBody2D .tscn scene tree, SpriteFrames .tres, and normal lighting materials.
                  </p>
                  <div className="pkg-action-buttons">
                    <a
                      href={`/exports/godot/${activeChar.id}/${activeChar.id}.tscn`}
                      download
                      className="pkg-file-chip"
                    >
                      <Download className="btn-icon-micro" /> {activeChar.id}.tscn
                    </a>
                    <a
                      href={`/exports/godot/${activeChar.id}/${activeChar.id}_frames.tres`}
                      download
                      className="pkg-file-chip"
                    >
                      <Download className="btn-icon-micro" /> frames.tres
                    </a>
                  </div>
                </div>

                {/* Unity 2022+ Card */}
                <div className="modal-package-card">
                  <div className="pkg-card-top">
                    <span className="pkg-badge unity">Unity 2022+ URP</span>
                    <a
                      href={`/exports/unity/${activeChar.id}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="pkg-external-link"
                    >
                      Browse ↗
                    </a>
                  </div>
                  <p className="pkg-text">
                    Sprite-Lit-Default URP materials, multiple-sprite atlas slices, and prefab configs.
                  </p>
                  <div className="pkg-action-buttons">
                    <a
                      href={`/exports/unity/${activeChar.id}/unity_prefab_spec.json`}
                      download
                      className="pkg-file-chip"
                    >
                      <Download className="btn-icon-micro" /> prefab_spec.json
                    </a>
                    <a
                      href={`/exports/unity/${activeChar.id}/${activeChar.id}_atlas.png`}
                      download
                      className="pkg-file-chip"
                    >
                      <Download className="btn-icon-micro" /> atlas.png
                    </a>
                  </div>
                </div>

                {/* Phaser 3 / PixiJS Card */}
                <div className="modal-package-card">
                  <div className="pkg-card-top">
                    <span className="pkg-badge phaser">Phaser 3 / PixiJS</span>
                    <a
                      href={`/exports/phaser/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="pkg-external-link"
                    >
                      Browse ↗
                    </a>
                  </div>
                  <p className="pkg-text">
                    Standard & FHD TexturePacker JSON Hash with trimmed bounds for HTML5 WebGL engines.
                  </p>
                  <div className="pkg-action-buttons">
                    <a
                      href={`/exports/phaser/${activeChar.id}_atlas.json`}
                      download
                      className="pkg-file-chip"
                    >
                      <Download className="btn-icon-micro" /> atlas.json
                    </a>
                    <a
                      href={`/exports/phaser/${activeChar.id}_atlas_fhd.json`}
                      download
                      className="pkg-file-chip"
                    >
                      <Download className="btn-icon-micro" /> atlas_fhd.json
                    </a>
                  </div>
                </div>
              </div>

              {/* CLI Command Helper Box */}
              <div className="modal-cli-box">
                <span className="cli-hint-label">Terminal CLI Generation:</span>
                <code className="cli-code-inline">img2game2d build "characters/{activeChar.id}.png" --engine all</code>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
