/**
 * img2game2d v2.0 Framework Web Studio Engine
 * High-performance Canvas 2D engine with real-time dynamic 2D normal-map lighting,
 * bloom emission shaders, procedural audio synthesis, and Finnova Bento controls.
 * Zero-Emoji Clean Architecture • Multi-Tab Router • Dual-Theme Engine
 */

// Application State
const state = {
  activeTab: 'studio', // 'studio' | 'lighting' | 'spine' | 'engines'
  theme: 'light',
  activeChar: 'the_architect', // 'the_architect' | 'the_guardian'
  activeAnim: 'idle',
  currentFrameIdx: 0,
  isPlaying: true,
  playbackSpeed: 1.0,
  zoom: 1.0,
  audioEnabled: true,

  // Channel View Mode: 'diffuse' | 'normal' | 'emission' | 'torch'
  viewMode: 'diffuse',

  // 2D Torchlight Parameters
  torch: {
    x: 288,
    y: 200,
    intensity: 1.8,
    ambient: 0.35,
    radius: 350,
    zDepth: 45,
    bloomBoost: 1.4,
    preset: 'neon'
  },

  // Overlays
  showHitbox: true,
  showPivot: true,
  showGroundLine: true,
  showFrameBox: false,

  // Character Data Store
  characters: {
    the_architect: {
      name: 'The Architect',
      metaUrl: 'assets/the_architect_meta.json',
      atlasUrl: 'assets/the_architect_atlas.png',
      normalUrl: 'assets/the_architect_atlas_normal.png',
      emissionUrl: 'assets/the_architect_atlas_emission.png',
      spineJsonUrl: '/exports/spine/the_architect/the_architect_skeleton.json',
      spineAtlasUrl: '/exports/spine/the_architect/the_architect.atlas',
      meta: null,
      atlasImg: null,
      normalImg: null,
      emissionImg: null,
      spineData: null
    },
    the_guardian: {
      name: 'The Guardian',
      metaUrl: 'assets/the_guardian_meta.json',
      atlasUrl: 'assets/the_guardian_atlas.png',
      normalUrl: 'assets/the_guardian_atlas_normal.png',
      emissionUrl: 'assets/the_guardian_atlas_emission.png',
      spineJsonUrl: '/exports/spine/the_guardian/the_guardian_skeleton.json',
      spineAtlasUrl: '/exports/spine/the_guardian/the_guardian.atlas',
      meta: null,
      atlasImg: null,
      normalImg: null,
      emissionImg: null,
      spineData: null
    }
  }
};

// DOM References
const canvas = document.getElementById('stageCanvas');
const ctx = canvas.getContext('2d', { willReadFrequently: true });
const canvasWrapper = document.getElementById('canvasWrapper');
const torchCursor = document.getElementById('torchCursor');
const floatingModeBadge = document.getElementById('floatingModeBadge');
const actionButtonsContainer = document.getElementById('actionButtons');

// Playback DOM
const btnPlayPause = document.getElementById('btnPlayPause');
const btnPrevFrame = document.getElementById('btnPrevFrame');
const btnNextFrame = document.getElementById('btnNextFrame');
const btnAudioToggle = document.getElementById('btnAudioToggle');
const frameCounter = document.getElementById('frameCounter');
const timingInfo = document.getElementById('timingInfo');
const timelineTrack = document.getElementById('timelineTrack');
const timelineProgress = document.getElementById('timelineProgress');
const timelineScrubber = document.getElementById('timelineScrubber');
const playIcon = document.getElementById('playIcon');

// Channel Buttons
const channelBtns = {
  diffuse: document.getElementById('btnChannelDiffuse'),
  normal: document.getElementById('btnChannelNormal'),
  emission: document.getElementById('btnChannelEmission'),
  torch: document.getElementById('btnChannelTorch')
};

// Normal Light Processing Buffers
const offscreenCanvas = document.createElement('canvas');
offscreenCanvas.width = 576;
offscreenCanvas.height = 512;
const offscreenCtx = offscreenCanvas.getContext('2d', { willReadFrequently: true });

// Web Audio API Synthesizer
let audioCtx = null;
function getAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

function playActionSFX(action) {
  if (!state.audioEnabled) return;
  try {
    const actx = getAudioContext();
    const now = actx.currentTime;
    const osc = actx.createOscillator();
    const gain = actx.createGain();
    osc.connect(gain);
    gain.connect(actx.destination);

    if (action === 'attack') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(320, now);
      osc.frequency.exponentialRampToValueAtTime(70, now + 0.18);
      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
      osc.start(now);
      osc.stop(now + 0.18);
    } else if (action === 'jump') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(140, now);
      osc.frequency.exponentialRampToValueAtTime(420, now + 0.22);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now);
      osc.stop(now + 0.22);
    } else if (action === 'defend') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(120, now);
      osc.frequency.linearRampToValueAtTime(80, now + 0.25);
      gain.gain.setValueAtTime(0.35, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    } else if (action === 'run' || action === 'walk') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(90, now);
      osc.frequency.exponentialRampToValueAtTime(40, now + 0.08);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now);
      osc.stop(now + 0.08);
    }
  } catch (e) {}
}

// Image Loader Helper
function loadImage(url) {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => {
      console.warn(`Failed loading image: ${url}`);
      resolve(null);
    };
    img.src = url;
  });
}

// Load Character Data
async function loadCharacter(charId) {
  const char = state.characters[charId];
  if (!char) return;

  if (!char.meta) {
    try {
      const res = await fetch(char.metaUrl);
      char.meta = await res.json();
    } catch (e) {
      console.error('Error fetching character metadata:', e);
    }
  }

  if (!char.atlasImg) char.atlasImg = await loadImage(char.atlasUrl);
  if (!char.normalImg) char.normalImg = await loadImage(char.normalUrl);
  if (!char.emissionImg) char.emissionImg = await loadImage(char.emissionUrl);

  // Pre-load Spine skeleton JSON
  if (!char.spineData) {
    try {
      const sRes = await fetch(char.spineJsonUrl);
      if (sRes.ok) {
        char.spineData = await sRes.json();
      }
    } catch (e) {
      console.warn('Spine data not loaded yet:', e);
    }
  }
}

// Set Character
async function setCharacter(charId) {
  state.activeChar = charId;
  await loadCharacter(charId);

  // Update Character selector buttons
  const btnArch = document.getElementById('btnCharArchitect');
  const btnGuard = document.getElementById('btnCharGuardian');
  if (btnArch) btnArch.classList.toggle('active', charId === 'the_architect');
  if (btnGuard) btnGuard.classList.toggle('active', charId === 'the_guardian');

  // Build animation list
  const char = state.characters[charId];
  if (!char || !char.meta) return;
  const anims = Object.keys(char.meta.animations);

  if (actionButtonsContainer) {
    actionButtonsContainer.innerHTML = '';
    anims.forEach((anim) => {
      const aInfo = char.meta.animations[anim];
      const btn = document.createElement('button');
      btn.className = `action-pill ${anim === state.activeAnim ? 'active' : ''}`;
      btn.innerHTML = `<span>${anim.toUpperCase()}</span><span class="action-fcount">${aInfo.frame_count}f</span>`;
      btn.onclick = () => setAnimation(anim);
      actionButtonsContainer.appendChild(btn);
    });
  }

  if (!anims.includes(state.activeAnim)) {
    state.activeAnim = anims[0] || 'idle';
  }

  // Update Map preview images in Lighting tab
  const mapDiff = document.getElementById('mapPreviewDiffuse');
  const mapNorm = document.getElementById('mapPreviewNormal');
  const mapEmis = document.getElementById('mapPreviewEmission');
  if (mapDiff) mapDiff.src = char.atlasUrl;
  if (mapNorm) mapNorm.src = char.normalUrl;
  if (mapEmis) mapEmis.src = char.emissionUrl;

  updateSpineInspector();
  updateEngineExportsView();
  updateExportModalFiles();
  setAnimation(state.activeAnim);
}

// Set Animation Sequence
function setAnimation(animName) {
  state.activeAnim = animName;
  state.currentFrameIdx = 0;

  if (actionButtonsContainer) {
    const btns = actionButtonsContainer.querySelectorAll('.action-pill');
    btns.forEach((b) => {
      const name = b.querySelector('span').textContent.toLowerCase();
      b.classList.toggle('active', name === animName);
    });
  }

  const char = state.characters[state.activeChar];
  if (char && char.meta && char.meta.animations[animName]) {
    const fps = char.meta.animations[animName].fps || 12;
    const fpsLabel = document.getElementById('actionFpsVal');
    if (fpsLabel) fpsLabel.textContent = `${fps} FPS`;
  }

  playActionSFX(animName);
  drawStage();
}

// Animation Loop Variables
let lastFrameTime = 0;
function loop(timestamp) {
  if (!lastFrameTime) lastFrameTime = timestamp;
  const elapsed = timestamp - lastFrameTime;

  const char = state.characters[state.activeChar];
  if (char && char.meta && char.meta.animations[state.activeAnim]) {
    const anim = char.meta.animations[state.activeAnim];
    const frameInterval = (1000 / (anim.fps || 12)) / state.playbackSpeed;

    if (state.isPlaying && elapsed >= frameInterval) {
      const frameCount = anim.frame_count || 1;
      const prevFrame = state.currentFrameIdx;
      state.currentFrameIdx = (state.currentFrameIdx + 1) % frameCount;
      lastFrameTime = timestamp;

      if (state.currentFrameIdx === 0 && prevFrame !== 0) {
        playActionSFX(state.activeAnim);
      }
      drawStage();
    }
  }

  requestAnimationFrame(loop);
}

// Draw Frame on Main Canvas
function drawStage() {
  const char = state.characters[state.activeChar];
  if (!char || !char.meta || !char.atlasImg) return;

  const anim = char.meta.animations[state.activeAnim];
  if (!anim) return;

  const frameIdx = state.currentFrameIdx;
  const frameInfo = anim.frames[frameIdx];
  if (!frameInfo) return;

  // Clear Canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const { x, y, width: w, height: h } = frameInfo.frame;
  const destX = 0;
  const destY = 0;
  const destW = canvas.width;
  const destH = canvas.height;

  // Render Based on View Mode
  if (state.viewMode === 'diffuse') {
    ctx.drawImage(char.atlasImg, x, y, w, h, destX, destY, destW, destH);
  } else if (state.viewMode === 'normal' && char.normalImg) {
    ctx.drawImage(char.normalImg, x, y, w, h, destX, destY, destW, destH);
  } else if (state.viewMode === 'emission' && char.emissionImg) {
    ctx.drawImage(char.emissionImg, x, y, w, h, destX, destY, destW, destH);
  } else if (state.viewMode === 'torch') {
    renderDynamicTorch(char, x, y, w, h, destX, destY, destW, destH);
  }

  // Draw Overlays (Gizmos)
  if (state.showHitbox) drawHitbox();
  if (state.showPivot) drawPivot();
  if (state.showGroundLine) drawGroundBaseline();
  if (state.showFrameBox) drawFrameBoundary();

  updatePlaybackTimeline(anim);
}

// Dynamic 2D Tangent Space Normal-Map Lighting Renderer
function renderDynamicTorch(char, srcX, srcY, srcW, srcH, destX, destY, destW, destH) {
  offscreenCtx.clearRect(0, 0, offscreenCanvas.width, offscreenCanvas.height);
  offscreenCtx.drawImage(char.atlasImg, srcX, srcY, srcW, srcH, destX, destY, destW, destH);
  const diffImgData = offscreenCtx.getImageData(0, 0, offscreenCanvas.width, offscreenCanvas.height);
  const diffData = diffImgData.data;

  let normData = null;
  if (char.normalImg) {
    offscreenCtx.clearRect(0, 0, offscreenCanvas.width, offscreenCanvas.height);
    offscreenCtx.drawImage(char.normalImg, srcX, srcY, srcW, srcH, destX, destY, destW, destH);
    normData = offscreenCtx.getImageData(0, 0, offscreenCanvas.width, offscreenCanvas.height).data;
  }

  let emisData = null;
  if (char.emissionImg) {
    offscreenCtx.clearRect(0, 0, offscreenCanvas.width, offscreenCanvas.height);
    offscreenCtx.drawImage(char.emissionImg, srcX, srcY, srcW, srcH, destX, destY, destW, destH);
    emisData = offscreenCtx.getImageData(0, 0, offscreenCanvas.width, offscreenCanvas.height).data;
  }

  const outImgData = ctx.createImageData(canvas.width, canvas.height);
  const outData = outImgData.data;

  const lightX = state.torch.x;
  const lightY = state.torch.y;
  const lightZ = state.torch.zDepth;
  const lightIntensity = state.torch.intensity;
  const lightRadius = state.torch.radius;
  const ambient = state.torch.ambient;
  const bloom = state.torch.bloomBoost;

  const width = canvas.width;
  const height = canvas.height;

  for (let py = 0; py < height; py++) {
    for (let px = 0; px < width; px++) {
      const idx = (py * width + px) * 4;
      const alpha = diffData[idx + 3];
      if (alpha < 10) continue;

      const dr = diffData[idx];
      const dg = diffData[idx + 1];
      const db = diffData[idx + 2];

      const dx = lightX - px;
      const dy = lightY - py;
      const dist2D = Math.sqrt(dx * dx + dy * dy);

      let attenuation = 0;
      if (dist2D < lightRadius) {
        attenuation = Math.pow(1 - dist2D / lightRadius, 1.8);
      }

      let dot = 1.0;
      if (normData) {
        const nx = (normData[idx] / 255) * 2 - 1;
        const ny = (normData[idx + 1] / 255) * 2 - 1;
        const nz = (normData[idx + 2] / 255) * 2 - 1;

        const dist3D = Math.sqrt(dx * dx + dy * dy + lightZ * lightZ);
        const lx = dx / dist3D;
        const ly = -dy / dist3D; // OpenGL Y inversion
        const lz = lightZ / dist3D;

        dot = Math.max(0, nx * lx + ny * ly + nz * lz);
      }

      const lightFactor = ambient + dot * attenuation * lightIntensity;

      let er = 0, eg = 0, eb = 0;
      if (emisData) {
        er = emisData[idx] * bloom;
        eg = emisData[idx + 1] * bloom;
        eb = emisData[idx + 2] * bloom;
      }

      outData[idx] = Math.min(255, dr * lightFactor + er);
      outData[idx + 1] = Math.min(255, dg * lightFactor + eg);
      outData[idx + 2] = Math.min(255, db * lightFactor + eb);
      outData[idx + 3] = alpha;
    }
  }

  ctx.putImageData(outImgData, 0, 0);
}

// Gizmo Drawings
function drawHitbox() {
  ctx.save();
  ctx.strokeStyle = 'rgba(239, 68, 68, 0.85)';
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 4]);
  ctx.strokeRect(180, 100, 216, 360);
  ctx.fillStyle = 'rgba(239, 68, 68, 0.08)';
  ctx.fillRect(180, 100, 216, 360);
  ctx.restore();
}

function drawPivot() {
  const px = canvas.width * 0.5;
  const py = canvas.height * 0.90;
  ctx.save();
  ctx.strokeStyle = 'rgba(56, 189, 248, 0.9)';
  ctx.fillStyle = 'rgba(56, 189, 248, 0.3)';
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

function drawGroundBaseline() {
  const gy = 460;
  ctx.save();
  ctx.strokeStyle = 'rgba(16, 185, 129, 0.7)';
  ctx.lineWidth = 1.5;
  ctx.setLineDash([6, 6]);
  ctx.beginPath();
  ctx.moveTo(40, gy);
  ctx.lineTo(canvas.width - 40, gy);
  ctx.stroke();
  ctx.restore();
}

function drawFrameBoundary() {
  ctx.save();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
  ctx.lineWidth = 1;
  ctx.strokeRect(1, 1, canvas.width - 2, canvas.height - 2);
  ctx.restore();
}

function updatePlaybackTimeline(anim) {
  const frameCount = anim.frame_count || 1;
  const fps = anim.fps || 12;
  if (frameCounter) frameCounter.textContent = `Frame: ${state.currentFrameIdx + 1} / ${frameCount}`;

  const curSec = (state.currentFrameIdx / fps).toFixed(2);
  const totSec = (frameCount / fps).toFixed(2);
  if (timingInfo) timingInfo.textContent = `${curSec}s / ${totSec}s`;

  const percent = ((state.currentFrameIdx + 1) / frameCount) * 100;
  if (timelineProgress) timelineProgress.style.width = `${percent}%`;
  if (timelineScrubber) timelineScrubber.style.left = `${percent}%`;
}

// --------------------------------------------------------------------------
// THEME MANAGER (Light & Dark)
// --------------------------------------------------------------------------
function initTheme() {
  const saved = localStorage.getItem('img2game2d_theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialTheme = saved || (prefersDark ? 'dark' : 'light');
  setTheme(initialTheme);

  const toggleBtn = document.getElementById('btnThemeToggle');
  if (toggleBtn) {
    toggleBtn.onclick = () => {
      const nextTheme = state.theme === 'dark' ? 'light' : 'dark';
      setTheme(nextTheme);
    };
  }
}

function setTheme(theme) {
  state.theme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('img2game2d_theme', theme);

  const label = document.getElementById('themeLabel');
  if (label) {
    label.textContent = theme === 'dark' ? 'Dark' : 'Light';
  }
}

// --------------------------------------------------------------------------
// TAB ROUTER
// --------------------------------------------------------------------------
const viewHeadings = {
  studio: {
    title: 'Character Studio & Diagnostics',
    sub: 'Real-time animation inspector, dynamic normal map torchlight, and skeletal previewer'
  },
  lighting: {
    title: '2D Tangent Space Lighting Lab',
    sub: 'Dynamic per-pixel normal map torchlight, specular bevels, and bloom emission composition'
  },
  spine: {
    title: 'Spine 2D Skeletal Inspector',
    sub: 'Live bone hierarchy tree, coordinate transforms, and libGDX atlas slot mappings'
  },
  engines: {
    title: 'Production Engine Package Hub',
    sub: 'Pre-packaged runtime bundles for Godot 4, Unity URP, Spine 2D, and Phaser / PixiJS'
  }
};

function initTabRouter() {
  const navPills = document.querySelectorAll('.nav-pill[data-tab]');
  navPills.forEach((pill) => {
    pill.onclick = () => {
      const tab = pill.dataset.tab;
      switchTab(tab);
    };
  });

  // Support URL hash routing
  const hash = window.location.hash.replace('#', '');
  if (['studio', 'lighting', 'spine', 'engines'].includes(hash)) {
    switchTab(hash);
  }
}

function switchTab(tabId) {
  state.activeTab = tabId;

  // Update pills
  document.querySelectorAll('.nav-pill[data-tab]').forEach((p) => {
    p.classList.toggle('active', p.dataset.tab === tabId);
  });

  // Update view containers
  document.querySelectorAll('.tab-view').forEach((view) => {
    view.classList.remove('active');
  });

  const activeView = document.getElementById(`view-${tabId}`);
  if (activeView) activeView.classList.add('active');

  // Update global headings
  const hInfo = viewHeadings[tabId];
  if (hInfo) {
    const headingEl = document.getElementById('viewHeading');
    const subEl = document.getElementById('viewSubheading');
    if (headingEl) headingEl.textContent = hInfo.title;
    if (subEl) subEl.textContent = hInfo.sub;
  }

  // Update Channel pills visibility
  const channelGroup = document.getElementById('channelPillsGroup');
  if (channelGroup) {
    channelGroup.style.display = (tabId === 'studio' || tabId === 'lighting') ? 'flex' : 'none';
  }

  // Trigger tab-specific refresh
  if (tabId === 'spine') updateSpineInspector();
  if (tabId === 'engines') updateEngineExportsView();

  window.location.hash = tabId;
}

// --------------------------------------------------------------------------
// SPINE 2D SKELETAL INSPECTOR
// --------------------------------------------------------------------------
async function updateSpineInspector() {
  const char = state.characters[state.activeChar];
  if (!char) return;

  const treeContainer = document.getElementById('spineBoneTree');
  const slotsBody = document.getElementById('spineSlotsBody');
  const boneCountBadge = document.getElementById('spineBoneCount');

  // Fallback / default bone structure if skeleton.json is fetching
  let bones = [
    { name: 'root', parent: null, length: 0, x: 0, y: 0, rotation: 0 },
    { name: 'hip', parent: 'root', length: 42, x: 0, y: 120, rotation: 0 },
    { name: 'torso', parent: 'hip', length: 58, x: 0, y: 45, rotation: 0 },
    { name: 'head', parent: 'torso', length: 35, x: 0, y: 60, rotation: 0 },
    { name: 'arm_l', parent: 'torso', length: 48, x: -28, y: 50, rotation: -20 },
    { name: 'arm_r', parent: 'torso', length: 48, x: 28, y: 50, rotation: 20 },
    { name: 'leg_l', parent: 'hip', length: 54, x: -16, y: -10, rotation: 5 },
    { name: 'leg_r', parent: 'hip', length: 54, x: 16, y: -10, rotation: -5 }
  ];

  let slots = [
    { name: 'head_slot', bone: 'head', attachment: `${state.activeChar}_head`, region: '0, 0, 120, 120' },
    { name: 'torso_slot', bone: 'torso', attachment: `${state.activeChar}_torso`, region: '120, 0, 140, 160' },
    { name: 'blade_slot', bone: 'arm_r', attachment: `${state.activeChar}_weapon`, region: '260, 0, 180, 80' },
    { name: 'legs_slot', bone: 'hip', attachment: `${state.activeChar}_legs`, region: '0, 160, 200, 180' }
  ];

  if (char.spineData && char.spineData.bones) {
    bones = char.spineData.bones;
    if (char.spineData.slots) slots = char.spineData.slots;
  }

  if (boneCountBadge) boneCountBadge.textContent = `${bones.length} Bones`;

  // Render Bone Tree
  if (treeContainer) {
    treeContainer.innerHTML = '';
    bones.forEach((bone, idx) => {
      const node = document.createElement('div');
      node.className = `tree-node ${idx === 0 ? 'active' : ''}`;
      node.innerHTML = `
        <svg class="tree-icon" viewBox="0 0 24 24" fill="none" stroke-width="2"><circle cx="12" cy="5" r="3"/><circle cx="5" cy="19" r="3"/><circle cx="19" cy="19" r="3"/><line x1="12" y1="8" x2="5" y2="16"/><line x1="12" y1="8" x2="19" y2="16"/></svg>
        <span>${bone.name}</span>
        ${bone.parent ? `<span style="font-size: 10px; opacity: 0.6; margin-left: auto;">↳ ${bone.parent}</span>` : ''}
      `;
      node.onclick = () => {
        treeContainer.querySelectorAll('.tree-node').forEach(n => n.classList.remove('active'));
        node.classList.add('active');
        selectSpineBone(bone);
      };
      treeContainer.appendChild(node);
    });
  }

  // Select Root by default
  if (bones[0]) selectSpineBone(bones[0]);

  // Render Slots Table
  if (slotsBody) {
    slotsBody.innerHTML = '';
    slots.forEach((s) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="color: var(--wb-text-light); font-weight: 600;">${s.name}</td>
        <td><span class="tag-pill">${s.bone}</span></td>
        <td>${s.attachment || 'none'}</td>
        <td style="color: var(--accent-cyan);">${s.region || 'atlas POT'}</td>
      `;
      slotsBody.appendChild(tr);
    });
  }

  // Update TypeScript Snippet
  const snippetEl = document.getElementById('spineSnippetCode');
  if (snippetEl) {
    snippetEl.textContent = `// Spine 2D TypeScript Runtime Integration
import { SpinePlayer } from "@esotericsoftware/spine-player";

new SpinePlayer("player-container", {
  jsonUrl: "/exports/spine/${state.activeChar}/${state.activeChar}_skeleton.json",
  atlasUrl: "/exports/spine/${state.activeChar}/${state.activeChar}.atlas",
  animation: "idle",
  premultipliedAlpha: false,
  showControls: true
});`;
  }
}

function selectSpineBone(bone) {
  const nameEl = document.getElementById('selectedBoneName');
  const parentEl = document.getElementById('propBoneParent');
  const lenEl = document.getElementById('propBoneLength');
  const posEl = document.getElementById('propBonePos');
  const rotEl = document.getElementById('propBoneRot');

  if (nameEl) nameEl.textContent = bone.name;
  if (parentEl) parentEl.textContent = bone.parent || 'none (root)';
  if (lenEl) lenEl.textContent = `${bone.length || 0} px`;
  const bx = (bone.x || 0).toFixed(1);
  const by = (bone.y || 0).toFixed(1);
  if (posEl) posEl.textContent = `${bx}, ${by}`;
  if (rotEl) rotEl.textContent = `${(bone.rotation || 0).toFixed(1)}°`;
}

// --------------------------------------------------------------------------
// ENGINE EXPORTS DASHBOARD
// --------------------------------------------------------------------------
function updateEngineExportsView() {
  const char = state.activeChar || 'the_architect';

  // Spine
  const spineEl = document.getElementById('engineSpineFiles');
  if (spineEl) {
    spineEl.innerHTML = `
      <a href="/exports/spine/${char}/${char}_skeleton.json" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}_skeleton.json
      </a>
      <a href="/exports/spine/${char}/${char}.atlas" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}.atlas
      </a>
      <a href="/exports/spine/${char}/${char}_atlas.png" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}_atlas.png
      </a>
      <a href="/exports/spine/${char}/${char}_atlas_normal.png" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        normal.png
      </a>
      <a href="/exports/spine/${char}/${char}_atlas_emission.png" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        emission.png
      </a>
    `;
  }

  // Godot
  const godotEl = document.getElementById('engineGodotFiles');
  if (godotEl) {
    godotEl.innerHTML = `
      <a href="/exports/godot/${char}/${char}.tscn" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}.tscn
      </a>
      <a href="/exports/godot/${char}/${char}_frames.tres" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}_frames.tres
      </a>
      <a href="/exports/godot/${char}/${char}_atlas.png" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}_atlas.png
      </a>
    `;
  }

  // Unity
  const unityEl = document.getElementById('engineUnityFiles');
  if (unityEl) {
    unityEl.innerHTML = `
      <a href="/exports/unity/${char}/unity_prefab_spec.json" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        unity_prefab_spec.json
      </a>
      <a href="/exports/unity/${char}/${char}_atlas.png" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}_atlas.png
      </a>
      <a href="/exports/unity/${char}_sprites/" target="_blank" class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        Sliced Sprites Folder
      </a>
    `;
  }

  // Phaser
  const phaserEl = document.getElementById('enginePhaserFiles');
  if (phaserEl) {
    phaserEl.innerHTML = `
      <a href="/exports/phaser/${char}_atlas.json" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}_atlas.json
      </a>
      <a href="/exports/phaser/${char}_atlas_fhd.json" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}_atlas_fhd.json
      </a>
      <a href="/exports/phaser/${char}_atlas.png" download class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        ${char}_atlas.png
      </a>
    `;
  }
}

// --------------------------------------------------------------------------
// EXPORT MODAL LAUNCHER
// --------------------------------------------------------------------------
const exportModalBackdrop = document.getElementById('exportModalBackdrop');
const btnCloseModal = document.getElementById('btnCloseModal');
const modalActiveChar = document.getElementById('modalActiveChar');

function updateExportModalFiles() {
  const char = state.activeChar || 'the_architect';
  const charTitle = char === 'the_architect' ? 'The Architect' : 'The Guardian';
  if (modalActiveChar) modalActiveChar.textContent = charTitle;

  const spineList = document.getElementById('spineFileList');
  if (spineList) {
    spineList.innerHTML = `
      <a href="/exports/spine/${char}/${char}_skeleton.json" download class="file-chip">${char}_skeleton.json</a>
      <a href="/exports/spine/${char}/${char}.atlas" download class="file-chip">${char}.atlas</a>
      <a href="/exports/spine/${char}/${char}_atlas.png" download class="file-chip">${char}_atlas.png</a>
      <a href="/exports/spine/${char}/${char}_atlas_normal.png" download class="file-chip">normal.png</a>
    `;
  }

  const godotList = document.getElementById('godotFileList');
  if (godotList) {
    godotList.innerHTML = `
      <a href="/exports/godot/${char}/${char}.tscn" download class="file-chip">${char}.tscn</a>
      <a href="/exports/godot/${char}/${char}_frames.tres" download class="file-chip">${char}_frames.tres</a>
      <a href="/exports/godot/${char}/${char}_atlas.png" download class="file-chip">${char}_atlas.png</a>
    `;
  }

  const unityList = document.getElementById('unityFileList');
  if (unityList) {
    unityList.innerHTML = `
      <a href="/exports/unity/${char}/unity_prefab_spec.json" download class="file-chip">unity_prefab_spec.json</a>
      <a href="/exports/unity/${char}/${char}_atlas.png" download class="file-chip">${char}_atlas.png</a>
      <a href="/exports/unity/${char}_sprites/" target="_blank" class="file-chip">Sliced Sprites</a>
    `;
  }

  const phaserList = document.getElementById('phaserFileList');
  if (phaserList) {
    phaserList.innerHTML = `
      <a href="/exports/phaser/${char}_atlas.json" download class="file-chip">${char}_atlas.json</a>
      <a href="/exports/phaser/${char}_atlas_fhd.json" download class="file-chip">${char}_atlas_fhd.json</a>
      <a href="/exports/phaser/${char}_atlas.png" download class="file-chip">${char}_atlas.png</a>
    `;
  }
}

function openExportModal() {
  updateExportModalFiles();
  if (exportModalBackdrop) exportModalBackdrop.classList.add('active');
}

function closeExportModal() {
  if (exportModalBackdrop) exportModalBackdrop.classList.remove('active');
}

// --------------------------------------------------------------------------
// EVENT LISTENERS INITIALIZATION
// --------------------------------------------------------------------------
function setupEventListeners() {
  // Play / Pause
  if (btnPlayPause) {
    btnPlayPause.onclick = () => {
      state.isPlaying = !state.isPlaying;
      playIcon.innerHTML = state.isPlaying
        ? '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>'
        : '<path d="M8 5v14l11-7z"/>';
    };
  }

  // Prev Frame
  if (btnPrevFrame) {
    btnPrevFrame.onclick = () => {
      state.isPlaying = false;
      const char = state.characters[state.activeChar];
      if (char && char.meta && char.meta.animations[state.activeAnim]) {
        const frameCount = char.meta.animations[state.activeAnim].frame_count || 1;
        state.currentFrameIdx = (state.currentFrameIdx - 1 + frameCount) % frameCount;
        drawStage();
      }
    };
  }

  // Next Frame
  if (btnNextFrame) {
    btnNextFrame.onclick = () => {
      state.isPlaying = false;
      const char = state.characters[state.activeChar];
      if (char && char.meta && char.meta.animations[state.activeAnim]) {
        const frameCount = char.meta.animations[state.activeAnim].frame_count || 1;
        state.currentFrameIdx = (state.currentFrameIdx + 1) % frameCount;
        drawStage();
      }
    };
  }

  // Audio Toggle
  if (btnAudioToggle) {
    btnAudioToggle.onclick = () => {
      state.audioEnabled = !state.audioEnabled;
      btnAudioToggle.classList.toggle('active', state.audioEnabled);
      btnAudioToggle.querySelector('span').textContent = state.audioEnabled ? 'SFX Active' : 'SFX Muted';
    };
  }

  // Speed Pills
  document.querySelectorAll('.spd-pill').forEach((btn) => {
    btn.onclick = () => {
      document.querySelectorAll('.spd-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.playbackSpeed = parseFloat(btn.dataset.spd);
    };
  });

  // Zoom Pills
  const btnZoomFit = document.getElementById('btnZoomFit');
  const btnZoom1 = document.getElementById('btnZoom1');
  const btnZoom15 = document.getElementById('btnZoom15');

  if (btnZoomFit) {
    btnZoomFit.onclick = () => {
      [btnZoomFit, btnZoom1, btnZoom15].forEach(b => b && b.classList.remove('active'));
      btnZoomFit.classList.add('active');
      canvas.style.transform = 'scale(1.0)';
    };
  }
  if (btnZoom1) {
    btnZoom1.onclick = () => {
      [btnZoomFit, btnZoom1, btnZoom15].forEach(b => b && b.classList.remove('active'));
      btnZoom1.classList.add('active');
      canvas.style.transform = 'scale(1.0)';
    };
  }
  if (btnZoom15) {
    btnZoom15.onclick = () => {
      [btnZoomFit, btnZoom1, btnZoom15].forEach(b => b && b.classList.remove('active'));
      btnZoom15.classList.add('active');
      canvas.style.transform = 'scale(1.4)';
    };
  }

  // Timeline Click Scrubbing
  if (timelineTrack) {
    timelineTrack.onclick = (e) => {
      const rect = timelineTrack.getBoundingClientRect();
      const clickRatio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const char = state.characters[state.activeChar];
      if (char && char.meta && char.meta.animations[state.activeAnim]) {
        const frameCount = char.meta.animations[state.activeAnim].frame_count || 1;
        state.currentFrameIdx = Math.floor(clickRatio * frameCount) % frameCount;
        drawStage();
      }
    };
  }

  // Channel View Mode Buttons
  Object.entries(channelBtns).forEach(([mode, btn]) => {
    if (!btn) return;
    btn.onclick = () => {
      Object.values(channelBtns).forEach(b => b && b.classList.remove('active'));
      btn.classList.add('active');
      state.viewMode = mode;
      if (floatingModeBadge) floatingModeBadge.textContent = `Channel: ${mode.toUpperCase()}`;
      if (torchCursor) torchCursor.style.display = mode === 'torch' ? 'block' : 'none';
      drawStage();
    };
  });

  // Interactive Torch Mouse Tracking
  if (canvasWrapper) {
    canvasWrapper.addEventListener('mousemove', (e) => {
      if (state.viewMode !== 'torch') return;
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;

      state.torch.x = (e.clientX - rect.left) * scaleX;
      state.torch.y = (e.clientY - rect.top) * scaleY;

      const wrapRect = canvasWrapper.getBoundingClientRect();
      if (torchCursor) {
        torchCursor.style.left = `${e.clientX - wrapRect.left}px`;
        torchCursor.style.top = `${e.clientY - wrapRect.top}px`;
      }
      drawStage();
    });
  }

  // Torch Sliders
  const torchIntensity = document.getElementById('torchIntensity');
  if (torchIntensity) {
    torchIntensity.oninput = (e) => {
      state.torch.intensity = parseFloat(e.target.value);
      const valEl = document.getElementById('torchIntensityVal');
      if (valEl) valEl.textContent = `${state.torch.intensity}x`;
      if (state.viewMode === 'torch') drawStage();
    };
  }

  const torchAmbient = document.getElementById('torchAmbient');
  if (torchAmbient) {
    torchAmbient.oninput = (e) => {
      state.torch.ambient = parseFloat(e.target.value);
      const valEl = document.getElementById('torchAmbientVal');
      if (valEl) valEl.textContent = `${state.torch.ambient}`;
      if (state.viewMode === 'torch') drawStage();
    };
  }

  // Lighting Tab Sliders
  const lightRadius = document.getElementById('lightRadius');
  if (lightRadius) {
    lightRadius.oninput = (e) => {
      state.torch.radius = parseFloat(e.target.value);
      const valEl = document.getElementById('lightRadiusVal');
      if (valEl) valEl.textContent = `${state.torch.radius}px`;
      if (state.viewMode === 'torch') drawStage();
    };
  }

  const lightZ = document.getElementById('lightZ');
  if (lightZ) {
    lightZ.oninput = (e) => {
      state.torch.zDepth = parseFloat(e.target.value);
      const valEl = document.getElementById('lightZVal');
      if (valEl) valEl.textContent = `${state.torch.zDepth}px`;
      if (state.viewMode === 'torch') drawStage();
    };
  }

  const bloomBoost = document.getElementById('bloomBoost');
  if (bloomBoost) {
    bloomBoost.oninput = (e) => {
      state.torch.bloomBoost = parseFloat(e.target.value);
      const valEl = document.getElementById('bloomBoostVal');
      if (valEl) valEl.textContent = `${state.torch.bloomBoost}x`;
      if (state.viewMode === 'torch') drawStage();
    };
  }

  // Lighting Presets
  document.querySelectorAll('[data-preset]').forEach((btn) => {
    btn.onclick = () => {
      document.querySelectorAll('[data-preset]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const p = btn.dataset.preset;
      if (p === 'neon') {
        state.torch.intensity = 2.4;
        state.torch.ambient = 0.25;
        state.torch.bloomBoost = 2.0;
      } else if (p === 'torch') {
        state.torch.intensity = 1.6;
        state.torch.ambient = 0.15;
        state.torch.bloomBoost = 0.8;
      } else if (p === 'sun') {
        state.torch.intensity = 1.2;
        state.torch.ambient = 0.6;
        state.torch.bloomBoost = 1.0;
      }
      if (state.viewMode === 'torch') drawStage();
    };
  });

  // Background Pills
  document.querySelectorAll('.stage-bg-pill').forEach((btn) => {
    btn.onclick = () => {
      document.querySelectorAll('.stage-bg-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      if (canvasWrapper) canvasWrapper.className = `canvas-stage-wrapper bg-${btn.dataset.bg}`;
    };
  });

  // Character Buttons
  const btnArch = document.getElementById('btnCharArchitect');
  const btnGuard = document.getElementById('btnCharGuardian');
  if (btnArch) btnArch.onclick = () => setCharacter('the_architect');
  if (btnGuard) btnGuard.onclick = () => setCharacter('the_guardian');

  // Overlays Toggles
  const chkHitbox = document.getElementById('chkHitbox');
  const chkPivot = document.getElementById('chkPivot');
  const chkGroundLine = document.getElementById('chkGroundLine');
  const chkFrameBox = document.getElementById('chkFrameBox');
  if (chkHitbox) chkHitbox.onchange = (e) => { state.showHitbox = e.target.checked; drawStage(); };
  if (chkPivot) chkPivot.onchange = (e) => { state.showPivot = e.target.checked; drawStage(); };
  if (chkGroundLine) chkGroundLine.onchange = (e) => { state.showGroundLine = e.target.checked; drawStage(); };
  if (chkFrameBox) chkFrameBox.onchange = (e) => { state.showFrameBox = e.target.checked; drawStage(); };

  // Export Modal Triggers
  const btnExportAll = document.getElementById('btnExportAll');
  if (btnExportAll) btnExportAll.onclick = openExportModal;
  if (btnCloseModal) btnCloseModal.onclick = closeExportModal;
  if (exportModalBackdrop) {
    exportModalBackdrop.onclick = (e) => {
      if (e.target === exportModalBackdrop) closeExportModal();
    };
  }

  // Copy Spine Snippet Button
  const btnCopySpine = document.getElementById('btnCopySpineSnippet');
  if (btnCopySpine) {
    btnCopySpine.onclick = () => {
      const code = document.getElementById('spineSnippetCode');
      if (code) {
        navigator.clipboard.writeText(code.textContent);
        btnCopySpine.textContent = 'Copied!';
        setTimeout(() => { btnCopySpine.textContent = 'Copy Spec'; }, 2000);
      }
    };
  }

  // Global Keyboard Shortcuts
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space') {
      e.preventDefault();
      if (btnPlayPause) btnPlayPause.click();
    } else if (e.code === 'ArrowLeft') {
      if (btnPrevFrame) btnPrevFrame.click();
    } else if (e.code === 'ArrowRight') {
      if (btnNextFrame) btnNextFrame.click();
    } else if (e.code === 'KeyD') {
      if (channelBtns.diffuse) channelBtns.diffuse.click();
    } else if (e.code === 'KeyN') {
      if (channelBtns.normal) channelBtns.normal.click();
    } else if (e.code === 'KeyE') {
      if (channelBtns.emission) channelBtns.emission.click();
    } else if (e.code === 'KeyT') {
      if (channelBtns.torch) channelBtns.torch.click();
    }
  });
}

// Boot Studio Application
(async function boot() {
  initTheme();
  initTabRouter();
  setupEventListeners();
  await setCharacter('the_architect');
  requestAnimationFrame(loop);
})();
