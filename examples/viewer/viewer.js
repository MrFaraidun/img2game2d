/**
 * img2game2d v2.0 Framework Web Studio Engine
 * High-performance Canvas 2D engine with real-time dynamic 2D normal-map lighting,
 * bloom emission shaders, procedural audio synthesis, and Finnova Bento controls.
 */

// Application State
const state = {
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
    active: false
  },

  // Inspector Overlays
  showHitbox: true,
  showPivot: true,
  showGroundLine: true,
  showFrameBox: false,

  // Loaded Assets Cache
  characters: {
    the_architect: {
      meta: null,
      atlasJson: null,
      atlasImg: null,
      normalImg: null,
      emissionImg: null,
      loaded: false
    },
    the_guardian: {
      meta: null,
      atlasJson: null,
      atlasImg: null,
      normalImg: null,
      emissionImg: null,
      loaded: false
    }
  },

  // Timing
  lastTime: 0,
  frameTimer: 0,
  currentAnimDuration: 0,
  elapsedAnimTime: 0
};

// Canvas references
const canvas = document.getElementById('stageCanvas');
const ctx = canvas.getContext('2d', { willReadFrequently: true });
const canvasWrapper = document.getElementById('canvasWrapper');

// Offscreen canvases for lighting calculations
const offCanvas = document.createElement('canvas');
const offCtx = offCanvas.getContext('2d', { willReadFrequently: true });
const normCanvas = document.createElement('canvas');
const normCtx = normCanvas.getContext('2d', { willReadFrequently: true });

// UI References
const btnPlayPause = document.getElementById('btnPlayPause');
const btnPrevFrame = document.getElementById('btnPrevFrame');
const btnNextFrame = document.getElementById('btnNextFrame');
const btnAudioToggle = document.getElementById('btnAudioToggle');
const frameCounter = document.getElementById('frameCounter');
const timingInfo = document.getElementById('timingInfo');
const timelineProgress = document.getElementById('timelineProgress');
const timelineTrack = document.getElementById('timelineTrack');
const animButtonsContainer = document.getElementById('animationButtons');
const animFpsBadge = document.getElementById('animFpsBadge');
const floatingModeBadge = document.getElementById('floatingModeBadge');
const torchCursor = document.getElementById('torchCursor');

// Web Audio Synthesizer
let audioCtx = null;

function initAudio() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      audioCtx = new AudioContext();
    }
  }
}

function playSound(type) {
  if (!state.audioEnabled) return;
  initAudio();
  if (!audioCtx) return;
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }

  const now = audioCtx.currentTime;

  if (type === 'whoosh') {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(600, now);
    osc.frequency.exponentialRampToValueAtTime(80, now + 0.18);
    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.18);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.18);
  } else if (type === 'shield') {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(140, now);
    osc.frequency.exponentialRampToValueAtTime(45, now + 0.25);
    gain.gain.setValueAtTime(0.45, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.25);
  } else if (type === 'step') {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(100, now);
    osc.frequency.exponentialRampToValueAtTime(30, now + 0.08);
    gain.gain.setValueAtTime(0.2, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.08);
  }
}

// Image Loader Helper
function loadImage(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => {
      console.warn("Optional texture not found or failed:", src);
      resolve(null);
    };
    img.src = src;
  });
}

// Load Character Data
async function loadCharacter(charId, forceReload = false) {
  const char = state.characters[charId];
  if (char.loaded && !forceReload) return;

  try {
    const [metaRes, atlasRes] = await Promise.all([
      fetch(`assets/${charId}_meta.json`),
      fetch(`assets/${charId}_atlas.json`)
    ]);

    char.meta = await metaRes.json();
    char.atlasJson = await atlasRes.json();

    canvas.width = 576;
    canvas.height = 512;
    offCanvas.width = 576;
    offCanvas.height = 512;
    normCanvas.width = 576;
    normCanvas.height = 512;

    const [atlasImg, normImg, emisImg] = await Promise.all([
      loadImage(`assets/${charId}_atlas.png`),
      loadImage(`assets/${charId}_atlas_normal.png`),
      loadImage(`assets/${charId}_atlas_emission.png`)
    ]);

    char.atlasImg = atlasImg;
    char.normalImg = normImg;
    char.emissionImg = emisImg;
    char.loaded = true;

    // Update KPI Frame Count
    const kpiCount = document.getElementById('kpiFrameCount');
    if (kpiCount && char.meta && char.meta.animations) {
      let totalF = 0;
      Object.values(char.meta.animations).forEach(a => totalF += (a.frame_count || 0));
      kpiCount.innerHTML = `${totalF} <span class="kpi-unit">Frames</span>`;
    }
  } catch (err) {
    console.error(`Failed to load ${charId}:`, err);
  }
}

// Switch Active Character
async function setCharacter(charId) {
  state.activeChar = charId;
  await loadCharacter(charId);

  // Update Character buttons
  document.getElementById('btnCharArchitect').classList.toggle('active', charId === 'the_architect');
  document.getElementById('btnCharGuardian').classList.toggle('active', charId === 'the_guardian');

  // Build animation list
  const char = state.characters[charId];
  const anims = Object.keys(char.meta.animations);

  animButtonsContainer.innerHTML = '';
  anims.forEach((anim) => {
    const aInfo = char.meta.animations[anim];
    const btn = document.createElement('button');
    btn.className = `action-pill ${anim === state.activeAnim ? 'active' : ''}`;
    btn.innerHTML = `<span>${anim.toUpperCase()}</span><span class="action-fcount">${aInfo.frame_count}f</span>`;
    btn.onclick = () => setAnimation(anim);
    animButtonsContainer.appendChild(btn);
  });

  if (!anims.includes(state.activeAnim)) {
    state.activeAnim = anims[0];
  }
  updateExportModalFiles();
  setAnimation(state.activeAnim);
}

// Switch Active Animation
function setAnimation(animName) {
  state.activeAnim = animName;
  state.currentFrameIdx = 0;
  state.frameTimer = 0;
  state.elapsedAnimTime = 0;

  const char = state.characters[state.activeChar];
  const animInfo = char.meta.animations[animName];

  if (animFpsBadge) {
    animFpsBadge.textContent = `${animInfo.fps} FPS`;
  }

  const buttons = animButtonsContainer.querySelectorAll('.action-pill');
  buttons.forEach((btn) => {
    btn.classList.toggle('active', btn.textContent.toLowerCase().includes(animName.toLowerCase()));
  });

  updateTimeline();
  drawStage();

  if (animName === 'attack') playSound('whoosh');
  else if (animName === 'defend') playSound('shield');
}

// Update Animation Timing
function updateAnimation(dt) {
  if (!state.isPlaying) return;

  const char = state.characters[state.activeChar];
  if (!char || !char.loaded) return;

  const animInfo = char.meta.animations[state.activeAnim];
  if (!animInfo) return;

  const effectiveFps = animInfo.fps * state.playbackSpeed;
  const frameDuration = 1.0 / effectiveFps;

  state.frameTimer += dt;
  state.elapsedAnimTime += dt;

  if (state.frameTimer >= frameDuration) {
    state.frameTimer -= frameDuration;
    const prevIdx = state.currentFrameIdx;
    state.currentFrameIdx++;

    if (state.currentFrameIdx >= animInfo.frame_count) {
      if (animInfo.loop) {
        state.currentFrameIdx = 0;
        state.elapsedAnimTime = 0;
      } else {
        state.currentFrameIdx = animInfo.frame_count - 1;
        state.isPlaying = false;
        btnPlayPause.querySelector('svg').innerHTML = '<polygon points="5 3 19 12 5 21 5 3"/>';
      }
    }

    if (prevIdx !== state.currentFrameIdx) {
      if (state.activeAnim === 'run' && (state.currentFrameIdx === 1 || state.currentFrameIdx === 5)) {
        playSound('step');
      } else if (state.activeAnim === 'attack' && state.currentFrameIdx === 1) {
        playSound('whoosh');
      }
    }

    updateTimeline();
  }
}

// Render Stage Frame
function drawStage() {
  const char = state.characters[state.activeChar];
  if (!char || !char.loaded) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const animInfo = char.meta.animations[state.activeAnim];
  if (!animInfo) return;

  const frameNumStr = String(state.currentFrameIdx).padStart(2, '0');
  const frameKey = `${state.activeAnim}_${frameNumStr}.png`;
  const frameData = char.atlasJson.frames[frameKey];
  if (!frameData) return;

  const { frame, spriteSourceSize } = frameData;
  const groundY = 460;
  const pivotX = 288;

  // 1. Frame Canvas Bounds
  if (state.showFrameBox) {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);
  }

  // 2. Ground Baseline
  if (state.showGroundLine) {
    ctx.strokeStyle = 'rgba(79, 70, 229, 0.5)';
    ctx.setLineDash([6, 4]);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(0, groundY + 0.5);
    ctx.lineTo(canvas.width, groundY + 0.5);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = 'rgba(129, 140, 248, 0.8)';
    ctx.font = '10px "JetBrains Mono"';
    ctx.fillText(`GROUND (Y=${groundY})`, 12, groundY - 6);
  }

  // 3. Draw Character by Mode
  if (frame && spriteSourceSize) {
    const sx = Math.round(frame.x);
    const sy = Math.round(frame.y);
    const sw = Math.round(frame.w);
    const sh = Math.round(frame.h);
    const dx = Math.round(spriteSourceSize.x);
    const dy = Math.round(spriteSourceSize.y);
    const dw = Math.round(spriteSourceSize.w);
    const dh = Math.round(spriteSourceSize.h);

    if (state.viewMode === 'normal' && char.normalImg) {
      // Direct normal map channel
      ctx.drawImage(char.normalImg, sx, sy, sw, sh, dx, dy, dw, dh);
    } else if (state.viewMode === 'emission' && char.emissionImg) {
      // Direct emission bloom channel
      ctx.drawImage(char.emissionImg, sx, sy, sw, sh, dx, dy, dw, dh);
    } else if (state.viewMode === 'torch' && char.atlasImg && char.normalImg) {
      // Dynamic 2D Lighting Torch Mode!
      renderTorchlight(char, sx, sy, sw, sh, dx, dy, dw, dh);
    } else if (char.atlasImg) {
      // Standard Diffuse channel
      ctx.drawImage(char.atlasImg, sx, sy, sw, sh, dx, dy, dw, dh);
    }
  }

  // 4. Draw Combat Hitbox
  if (state.showHitbox && char.meta && char.meta.hitbox) {
    const hb = char.meta.hitbox;
    const px = 288 + hb.offset_x;
    const py = 460 + hb.offset_y;
    const pw = hb.width;
    const ph = hb.height;

    ctx.strokeStyle = 'rgba(16, 185, 129, 0.85)';
    ctx.fillStyle = 'rgba(16, 185, 129, 0.08)';
    ctx.lineWidth = 2;
    ctx.fillRect(px, py, pw, ph);
    ctx.strokeRect(px, py, pw, ph);

    ctx.fillStyle = 'rgba(16, 185, 129, 0.9)';
    ctx.font = '10px "JetBrains Mono"';
    ctx.fillText('HURTBOX', px + 4, py + 14);
  }

  // 5. Draw Ground Pivot Marker
  if (state.showPivot) {
    ctx.strokeStyle = '#ec4899';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(pivotX - 10, groundY);
    ctx.lineTo(pivotX + 10, groundY);
    ctx.moveTo(pivotX, groundY - 10);
    ctx.lineTo(pivotX, groundY + 10);
    ctx.stroke();

    ctx.fillStyle = '#ec4899';
    ctx.beginPath();
    ctx.arc(pivotX, groundY, 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.font = '10px "JetBrains Mono"';
    ctx.fillText(`PIVOT (${pivotX}, ${groundY})`, pivotX + 6, groundY - 6);
  }
}

// 2D Dynamic Point Light Calculation on Normal Maps
function renderTorchlight(char, sx, sy, sw, sh, dx, dy, dw, dh) {
  // Clear offscreens
  offCtx.clearRect(0, 0, 576, 512);
  normCtx.clearRect(0, 0, 576, 512);

  // Draw diffuse and normal into offscreens
  offCtx.drawImage(char.atlasImg, sx, sy, sw, sh, dx, dy, dw, dh);
  normCtx.drawImage(char.normalImg, sx, sy, sw, sh, dx, dy, dw, dh);

  const diffData = offCtx.getImageData(dx, dy, dw, dh);
  const normData = normCtx.getImageData(dx, dy, dw, dh);

  const dPix = diffData.data;
  const nPix = normData.data;

  const lx = state.torch.x - dx;
  const ly = state.torch.y - dy;
  const lz = 120; // light height in front of 2D plane
  const intensity = state.torch.intensity;
  const ambient = state.torch.ambient;

  // Process per-pixel Lambertian lighting: (N dot L)
  for (let i = 0; i < dPix.length; i += 4) {
    const alpha = dPix[i + 3];
    if (alpha < 10) continue;

    const px = (i / 4) % dw;
    const py = Math.floor((i / 4) / dw);

    // Vector from pixel to light source
    const dirX = lx - px;
    const dirY = ly - py;
    const dirZ = lz;
    const dist = Math.sqrt(dirX * dirX + dirY * dirY + dirZ * dirZ);

    if (dist > state.torch.radius) {
      // Beyond light radius: apply ambient only
      dPix[i] = Math.round(dPix[i] * ambient);
      dPix[i + 1] = Math.round(dPix[i + 1] * ambient);
      dPix[i + 2] = Math.round(dPix[i + 2] * ambient);
      continue;
    }

    const invDist = 1.0 / Math.max(1, dist);
    const nDirX = dirX * invDist;
    const nDirY = dirY * invDist;
    const nDirZ = dirZ * invDist;

    // Normal vector from [0..255] to [-1..1]
    const nx = (nPix[i] / 255.0) * 2.0 - 1.0;
    const ny = (nPix[i + 1] / 255.0) * 2.0 - 1.0;
    const nz = (nPix[i + 2] / 255.0) * 2.0 - 1.0;

    // Dot product: N dot L
    const dot = Math.max(0.0, nx * nDirX + ny * nDirY + nz * nDirZ);

    // Attenuation factor
    const atten = Math.max(0.0, 1.0 - dist / state.torch.radius);
    const factor = Math.min(2.5, ambient + dot * intensity * atten);

    dPix[i] = Math.min(255, Math.round(dPix[i] * factor));
    dPix[i + 1] = Math.min(255, Math.round(dPix[i + 1] * factor));
    dPix[i + 2] = Math.min(255, Math.round(dPix[i + 2] * factor));
  }

  offCtx.putImageData(diffData, dx, dy);
  ctx.drawImage(offCanvas, 0, 0);

  // Additive blend emission on top for vibrant cyber glow!
  if (char.emissionImg) {
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    ctx.drawImage(char.emissionImg, sx, sy, sw, sh, dx, dy, dw, dh);
    ctx.restore();
  }
}

// Update Timeline scrubber
function updateTimeline() {
  const char = state.characters[state.activeChar];
  if (!char || !char.loaded) return;

  const animInfo = char.meta.animations[state.activeAnim];
  if (!animInfo) return;

  frameCounter.textContent = `Frame: ${state.currentFrameIdx + 1} / ${animInfo.frame_count}`;

  const progress = animInfo.frame_count > 1
    ? (state.currentFrameIdx / (animInfo.frame_count - 1)) * 100
    : 100;
  timelineProgress.style.width = `${progress}%`;

  const totalTime = animInfo.frame_count / animInfo.fps;
  const curTime = (state.currentFrameIdx / animInfo.fps);
  timingInfo.textContent = `${curTime.toFixed(2)}s / ${totalTime.toFixed(2)}s`;
}

// Engine Loop
function loop(timestamp) {
  if (!state.lastTime) state.lastTime = timestamp;
  const dt = Math.min((timestamp - state.lastTime) / 1000, 0.1);
  state.lastTime = timestamp;

  updateAnimation(dt);
  drawStage();

  requestAnimationFrame(loop);
}

// Event Listeners: Playback Controls
btnPlayPause.onclick = () => {
  state.isPlaying = !state.isPlaying;
  btnPlayPause.querySelector('svg').innerHTML = state.isPlaying
    ? '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>'
    : '<polygon points="5 3 19 12 5 21 5 3"/>';
};

btnPrevFrame.onclick = () => {
  state.isPlaying = false;
  btnPlayPause.querySelector('svg').innerHTML = '<polygon points="5 3 19 12 5 21 5 3"/>';
  const char = state.characters[state.activeChar];
  const count = char.meta.animations[state.activeAnim].frame_count;
  state.currentFrameIdx = (state.currentFrameIdx - 1 + count) % count;
  updateTimeline();
  drawStage();
};

btnNextFrame.onclick = () => {
  state.isPlaying = false;
  btnPlayPause.querySelector('svg').innerHTML = '<polygon points="5 3 19 12 5 21 5 3"/>';
  const char = state.characters[state.activeChar];
  const count = char.meta.animations[state.activeAnim].frame_count;
  state.currentFrameIdx = (state.currentFrameIdx + 1) % count;
  updateTimeline();
  drawStage();
};

btnAudioToggle.onclick = () => {
  state.audioEnabled = !state.audioEnabled;
  btnAudioToggle.classList.toggle('active', state.audioEnabled);
  btnAudioToggle.querySelector('span').textContent = state.audioEnabled ? 'SFX Active' : 'SFX Muted';
};

// Timeline Click to Scrub
timelineTrack.onclick = (e) => {
  const char = state.characters[state.activeChar];
  if (!char || !char.loaded) return;

  const rect = timelineTrack.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const ratio = Math.max(0, Math.min(1, clickX / rect.width));

  const animInfo = char.meta.animations[state.activeAnim];
  state.currentFrameIdx = Math.round(ratio * (animInfo.frame_count - 1));
  state.frameTimer = 0;
  updateTimeline();
  drawStage();
};

// Speed Pills
document.querySelectorAll('.spd-pill').forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll('.spd-pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.playbackSpeed = parseFloat(btn.dataset.spd);
  };
});

// Channel Pills
const channelBtns = {
  diffuse: document.getElementById('btnChannelDiffuse'),
  normal: document.getElementById('btnChannelNormal'),
  emission: document.getElementById('btnChannelEmission'),
  torch: document.getElementById('btnChannelTorch')
};

Object.entries(channelBtns).forEach(([mode, btn]) => {
  if (!btn) return;
  btn.onclick = () => {
    Object.values(channelBtns).forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.viewMode = mode;
    floatingModeBadge.textContent = `Channel: ${mode.toUpperCase()}`;
    torchCursor.style.display = mode === 'torch' ? 'block' : 'none';
    drawStage();
  };
});

// Interactive Torchlight Mouse Move
canvasWrapper.addEventListener('mousemove', (e) => {
  if (state.viewMode !== 'torch') return;
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;

  const mouseX = (e.clientX - rect.left) * scaleX;
  const mouseY = (e.clientY - rect.top) * scaleY;

  state.torch.x = mouseX;
  state.torch.y = mouseY;

  const wrapRect = canvasWrapper.getBoundingClientRect();
  torchCursor.style.left = `${e.clientX - wrapRect.left}px`;
  torchCursor.style.top = `${e.clientY - wrapRect.top}px`;

  drawStage();
});

// Torch Slider Adjustments
const torchIntensitySlider = document.getElementById('torchIntensity');
if (torchIntensitySlider) {
  torchIntensitySlider.oninput = (e) => {
    state.torch.intensity = parseFloat(e.target.value);
    document.getElementById('torchIntensityVal').textContent = `${state.torch.intensity}x`;
    if (state.viewMode === 'torch') drawStage();
  };
}

const torchAmbientSlider = document.getElementById('torchAmbient');
if (torchAmbientSlider) {
  torchAmbientSlider.oninput = (e) => {
    state.torch.ambient = parseFloat(e.target.value);
    document.getElementById('torchAmbientVal').textContent = `${state.torch.ambient}`;
    if (state.viewMode === 'torch') drawStage();
  };
}

// Background Pills
document.querySelectorAll('.stage-bg-pill').forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll('.stage-bg-pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    canvasWrapper.className = `canvas-stage-wrapper bg-${btn.dataset.bg}`;
  };
});

// Character Buttons
document.getElementById('btnCharArchitect').onclick = () => setCharacter('the_architect');
document.getElementById('btnCharGuardian').onclick = () => setCharacter('the_guardian');

// Overlays Toggles
document.getElementById('chkHitbox').onchange = (e) => { state.showHitbox = e.target.checked; drawStage(); };
document.getElementById('chkPivot').onchange = (e) => { state.showPivot = e.target.checked; drawStage(); };
document.getElementById('chkGroundLine').onchange = (e) => { state.showGroundLine = e.target.checked; drawStage(); };
document.getElementById('chkFrameBox').onchange = (e) => { state.showFrameBox = e.target.checked; drawStage(); };

// Export Modal Controller
const exportModalBackdrop = document.getElementById('exportModalBackdrop');
const btnCloseModal = document.getElementById('btnCloseModal');
const modalActiveChar = document.getElementById('modalActiveChar');

function updateExportModalFiles() {
  const char = state.activeChar || 'the_architect';
  const charTitle = char === 'the_architect' ? 'The Architect' : 'The Guardian';
  if (modalActiveChar) modalActiveChar.textContent = charTitle;

  // Spine
  const spineList = document.getElementById('spineFileList');
  if (spineList) {
    spineList.innerHTML = `
      <a href="/exports/spine/${char}/${char}_skeleton.json" download class="file-chip">📄 ${char}_skeleton.json</a>
      <a href="/exports/spine/${char}/${char}.atlas" download class="file-chip">📜 ${char}.atlas</a>
      <a href="/exports/spine/${char}/${char}_atlas.png" download class="file-chip">🖼️ ${char}_atlas.png</a>
      <a href="/exports/spine/${char}/${char}_atlas_normal.png" download class="file-chip">🔮 normal.png</a>
      <a href="/exports/spine/${char}/${char}_atlas_emission.png" download class="file-chip">✨ emission.png</a>
    `;
  }

  // Godot
  const godotList = document.getElementById('godotFileList');
  if (godotList) {
    godotList.innerHTML = `
      <a href="/exports/godot/${char}/CharacterBody2D.tscn" download class="file-chip">🎮 CharacterBody2D.tscn</a>
      <a href="/exports/godot/${char}/SpriteFrames.tres" download class="file-chip">🎬 SpriteFrames.tres</a>
      <a href="/exports/godot/${char}/LightingMaterial.tres" download class="file-chip">💡 LightingMaterial.tres</a>
    `;
  }

  // Unity
  const unityList = document.getElementById('unityFileList');
  if (unityList) {
    unityList.innerHTML = `
      <a href="/exports/unity/${char}/${char}_atlas.png" download class="file-chip">⚡ ${char}_atlas.png</a>
      <a href="/exports/unity/${char}/${char}.prefab" download class="file-chip">📦 ${char}.prefab</a>
      <a href="/exports/unity/${char}_sprites/" target="_blank" class="file-chip">📂 Sliced Sprites (24)</a>
    `;
  }

  // Phaser
  const phaserList = document.getElementById('phaserFileList');
  if (phaserList) {
    phaserList.innerHTML = `
      <a href="/exports/phaser/${char}_atlas.json" download class="file-chip">📊 ${char}_atlas.json</a>
      <a href="/exports/phaser/${char}_atlas.png" download class="file-chip">🖼️ ${char}_atlas.png</a>
      <a href="/exports/phaser/${char}_atlas_fhd.json" download class="file-chip">🖥️ ${char}_atlas_fhd.json</a>
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

const btnExportAll = document.getElementById('btnExportAll');
if (btnExportAll) {
  btnExportAll.onclick = openExportModal;
}

if (btnCloseModal) {
  btnCloseModal.onclick = closeExportModal;
}

if (exportModalBackdrop) {
  exportModalBackdrop.onclick = (e) => {
    if (e.target === exportModalBackdrop) closeExportModal();
  };
}

// Keyboard Shortcuts
window.addEventListener('keydown', (e) => {
  if (e.code === 'Space') {
    e.preventDefault();
    btnPlayPause.click();
  } else if (e.code === 'ArrowLeft') {
    btnPrevFrame.click();
  } else if (e.code === 'ArrowRight') {
    btnNextFrame.click();
  } else if (e.code === 'KeyD') {
    channelBtns.diffuse.click();
  } else if (e.code === 'KeyN') {
    channelBtns.normal.click();
  } else if (e.code === 'KeyE') {
    channelBtns.emission.click();
  } else if (e.code === 'KeyT') {
    channelBtns.torch.click();
  }
});

// Boot Studio
(async function boot() {
  await setCharacter('the_architect');
  requestAnimationFrame(loop);
})();
