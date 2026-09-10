/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Master Application Orchestrator & Workstation Router
 * 
 * Synchronizes multi-tab workstations, character pipelines, dynamic normal lighting,
 * Spine skeletal rigs, multi-engine exports, theme systems, and global keyboard shortcuts.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  StudioTab,
  ThemeMode,
  CharacterId
} from './types';
import { useCharacter } from './hooks/useCharacter';
import { useNormalLighting } from './hooks/useNormalLighting';
import { useSpineRig } from './hooks/useSpineRig';
import { Header } from './components/layout/Header';
import { StudioWorkstation } from './components/studio/StudioWorkstation';
import { LightingWorkstation } from './components/lighting/LightingWorkstation';
import { SpineWorkstation } from './components/spine/SpineWorkstation';
import { ExportsWorkstation } from './components/exports/ExportsWorkstation';
import { audio } from './lib/audio';
import { Keyboard, Command, HelpCircle } from 'lucide-react';

export function App() {
  // Theme state with local storage persistence
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem('img2game2d_theme');
    if (saved === 'dark' || saved === 'light') return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  // Active Workstation Tab
  const [activeTab, setActiveTab] = useState<StudioTab>(() => {
    const hash = window.location.hash.replace('#', '') as StudioTab;
    if (['studio', 'lighting', 'spine', 'exports'].includes(hash)) {
      return hash;
    }
    return 'studio';
  });

  // Keyboard Shortcuts Drawer Toggle
  const [showShortcutsModal, setShowShortcutsModal] = useState<boolean>(false);

  // Core Hooks
  const characterHook = useCharacter();
  const lightingHook = useNormalLighting();
  const spineHook = useSpineRig(characterHook.activeChar);

  /**
   * Theme Sync to DOM
   */
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('img2game2d_theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  /**
   * Tab Switching with hash routing
   */
  const handleSelectTab = useCallback((tab: StudioTab) => {
    setActiveTab(tab);
    window.location.hash = tab;
  }, []);

  /**
   * Character Switching handler
   */
  const handleSelectCharacter = useCallback((charId: CharacterId) => {
    characterHook.selectCharacter(charId);
  }, [characterHook]);

  /**
   * Global Keyboard Shortcuts Listener
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if active element is an input or textarea
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        characterHook.togglePlayPause();
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        characterHook.stepBackward();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        characterHook.stepForward();
      } else if (e.code === 'Digit1') {
        handleSelectTab('studio');
      } else if (e.code === 'Digit2') {
        handleSelectTab('lighting');
      } else if (e.code === 'Digit3') {
        handleSelectTab('spine');
      } else if (e.code === 'Digit4') {
        handleSelectTab('exports');
      } else if (e.code === 'KeyD') {
        lightingHook.setViewMode('diffuse_only');
      } else if (e.code === 'KeyN') {
        lightingHook.setViewMode('normal_only');
      } else if (e.code === 'KeyE') {
        lightingHook.setViewMode('emission_only');
      } else if (e.code === 'KeyC') {
        lightingHook.setViewMode('composite');
      } else if (e.code === 'KeyS') {
        lightingHook.setViewMode('split');
      } else if (e.code === 'Slash' && (e.metaKey || e.ctrlKey)) {
        setShowShortcutsModal((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [characterHook, handleSelectTab, lightingHook]);

  return (
    <div className="studio-root-container">
      {/* Top Application Header & Compact Telemetry Ribbon */}
      <Header
        activeTab={activeTab}
        theme={theme}
        activeChar={characterHook.activeChar}
        telemetry={characterHook.telemetry}
        onSelectTab={handleSelectTab}
        onToggleTheme={toggleTheme}
        onSelectCharacter={handleSelectCharacter}
      />

      {/* Main Workstation View Router */}
      <main className="main-workstation-body">
        {/* TAB 1: STUDIO CANVAS WORKSTATION */}
        {activeTab === 'studio' && (
          <StudioWorkstation
            activeChar={characterHook.activeChar}
            activeAnim={characterHook.activeAnim}
            currentFrameIdx={characterHook.currentFrameIdx}
            isPlaying={characterHook.isPlaying}
            playbackSpeed={characterHook.playbackSpeed}
            totalFrames={characterHook.totalFrames}
            currentFps={characterHook.currentFps}
            telemetry={characterHook.telemetry}
            currentFrameCoordinates={characterHook.currentFrameCoordinates}
            filmstripFrames={characterHook.filmstripFrames}
            onSelectCharacter={characterHook.selectCharacter}
            onSelectAnimation={characterHook.selectAnimation}
            onTogglePlayPause={characterHook.togglePlayPause}
            onStepForward={characterHook.stepForward}
            onStepBackward={characterHook.stepBackward}
            onSeekFrame={characterHook.seekFrame}
            onChangeSpeed={characterHook.changePlaybackSpeed}
            getResolvedFrame={characterHook.getResolvedFrame}
          />
        )}

        {/* TAB 2: DYNAMIC LIGHTING STAGE WORKSTATION */}
        {activeTab === 'lighting' && (
          <LightingWorkstation
            activeChar={characterHook.activeChar}
            currentFrameCoordinates={characterHook.currentFrameCoordinates}
            lightingState={lightingHook.lightingState}
            onSetViewMode={lightingHook.setViewMode}
            onApplyPreset={lightingHook.applyPreset}
            onSetPrimaryLightPosition={lightingHook.setPrimaryLightPosition}
            onUpdateActiveLight={lightingHook.updateActiveLight}
            onSetAmbientLevel={lightingHook.setAmbientLevel}
            onSetBloomBoost={lightingHook.setBloomBoost}
            onSetSplitRatio={lightingHook.setSplitRatio}
            renderLightingScene={lightingHook.renderLightingScene}
          />
        )}

        {/* TAB 3: SPINE 2D SKELETAL WORKSTATION */}
        {activeTab === 'spine' && (
          <SpineWorkstation
            activeChar={characterHook.activeChar}
            currentFrameCoordinates={characterHook.currentFrameCoordinates}
            rawBones={spineHook.rawBones}
            rawSlots={spineHook.rawSlots}
            computedBones={spineHook.computedBones}
            selectedBone={spineHook.selectedBone}
            selectedBoneSlots={spineHook.selectedBoneSlots}
            inspectorState={spineHook.inspectorState}
            onSelectBone={spineHook.selectBone}
            onHoverBone={spineHook.setHoveredBone}
            onHitTestBone={spineHook.hitTestBone}
            onToggleSetting={spineHook.toggleSetting}
            onSetRotationOffset={spineHook.setRotationOffset}
            onSetActiveSpecTab={spineHook.setActiveSpecTab}
            renderSkeletalOverlay={spineHook.renderSkeletalOverlay}
            exportSkeletonJson={spineHook.exportSkeletonJson}
          />
        )}

        {/* TAB 4: ENGINE EXPORTS & CODE GENERATOR WORKSTATION */}
        {activeTab === 'exports' && (
          <ExportsWorkstation
            activeChar={characterHook.activeChar}
          />
        )}
      </main>

      {/* Persistent Bottom Utility Bar */}
      <footer className="studio-footer-status">
        <div className="footer-left-info">
          <span className="footer-dot-live" />
          <span className="footer-status-text">
            img2game2d v2.0 Studio Engine • Enterprise Edition
          </span>
        </div>

        <div className="footer-right-actions">
          <button
            className="footer-shortcut-btn"
            onClick={() => setShowShortcutsModal(true)}
            title="Keyboard Shortcuts"
          >
            <Keyboard className="footer-icon-sm" />
            <span>Shortcuts</span>
          </button>
        </div>
      </footer>

      {/* Command Palette Modal (Cmd+K / Ctrl+K) */}
      {showShortcutsModal && (
        <div
          className="export-modal-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowShortcutsModal(false);
          }}
        >
          <div className="export-modal-dialog" style={{ maxWidth: '620px' }}>
            <div className="modal-head">
              <div className="modal-title-group">
                <span className="modal-kicker">KEYBOARD COMMAND PALETTE</span>
                <h3 className="modal-heading">Workstation Navigation & Shortcuts</h3>
                <p className="modal-sub">Fast keyboard triggers for power developers and game animators</p>
              </div>
              <button
                className="modal-close-btn"
                onClick={() => setShowShortcutsModal(false)}
              >
                ✕
              </button>
            </div>

            <div className="shortcuts-table-container">
              <table className="manifest-table">
                <thead>
                  <tr>
                    <th>Command</th>
                    <th>Hotkeys</th>
                    <th>Scope</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Play / Pause</strong></td>
                    <td><kbd className="key-cap">Space</kbd></td>
                    <td>Studio</td>
                    <td>Toggles real-time RAF frame playback clock</td>
                  </tr>
                  <tr>
                    <td><strong>Step Backward</strong></td>
                    <td><kbd className="key-cap">←</kbd></td>
                    <td>Studio</td>
                    <td>Step back by 1 animation frame</td>
                  </tr>
                  <tr>
                    <td><strong>Step Forward</strong></td>
                    <td><kbd className="key-cap">→</kbd></td>
                    <td>Studio</td>
                    <td>Step forward by 1 animation frame</td>
                  </tr>
                  <tr>
                    <td><strong>Canvas Studio</strong></td>
                    <td><kbd className="key-cap">1</kbd></td>
                    <td>Global</td>
                    <td>Switch to Animation Workstation</td>
                  </tr>
                  <tr>
                    <td><strong>Lighting Lab</strong></td>
                    <td><kbd className="key-cap">2</kbd></td>
                    <td>Global</td>
                    <td>Switch to Dynamic 2D Shading Stage</td>
                  </tr>
                  <tr>
                    <td><strong>Spine 2D Rig</strong></td>
                    <td><kbd className="key-cap">3</kbd></td>
                    <td>Global</td>
                    <td>Switch to Skeletal Rigging Visualizer</td>
                  </tr>
                  <tr>
                    <td><strong>Engine Exporter</strong></td>
                    <td><kbd className="key-cap">4</kbd></td>
                    <td>Global</td>
                    <td>Switch to Engine Packages & Code Gen</td>
                  </tr>
                  <tr>
                    <td><strong>Composite Lit</strong></td>
                    <td><kbd className="key-cap">C</kbd></td>
                    <td>Lighting</td>
                    <td>Full dynamic 2D tangent normal shading</td>
                  </tr>
                  <tr>
                    <td><strong>A/B Split View</strong></td>
                    <td><kbd className="key-cap">S</kbd></td>
                    <td>Lighting</td>
                    <td>Compare unlit albedo vs dynamic lit</td>
                  </tr>
                  <tr>
                    <td><strong>Diffuse Channel</strong></td>
                    <td><kbd className="key-cap">D</kbd></td>
                    <td>Lighting</td>
                    <td>Isolate raw diffuse albedo texture</td>
                  </tr>
                  <tr>
                    <td><strong>Normal Channel</strong></td>
                    <td><kbd className="key-cap">N</kbd></td>
                    <td>Lighting</td>
                    <td>Isolate tangent space normal vectors</td>
                  </tr>
                  <tr>
                    <td><strong>Bloom Emission</strong></td>
                    <td><kbd className="key-cap">E</kbd></td>
                    <td>Lighting</td>
                    <td>Isolate additive HDR glow visor/swords</td>
                  </tr>
                  <tr>
                    <td><strong>Switch Character</strong></td>
                    <td><kbd className="key-cap">Tab</kbd></td>
                    <td>Global</td>
                    <td>Toggle Architect / Guardian</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="modal-cli-box">
              <span className="cli-hint-label">Tip:</span>
              <span className="cli-code-inline">Press 1-4 anytime to switch active workstations with zero mouse clicks.</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
