/**
 * img2game2d Production 2D Character QA Viewer
 * High-performance Canvas 2D engine with procedural Web Audio synthesizer.
 */

// Application State
const state = {
  activeChar: 'the_architect', // 'the_architect' | 'the_guardian'
  activeAnim: 'idle',
  currentFrameIdx: 0,
  isPlaying: true,
  playbackSpeed: 1.0,
  zoom: 0.85,
  atlasRes: '4k',
  audioEnabled: true,
  
  // Overlays
  showHitbox: true,
  showPivot: true,
  showGroundLine: true,
  showFrameBox: false,

  // Loaded Assets Cache
  characters: {
    the_architect: { meta: null, atlasJson: null, atlasImg: null, loaded: false },
    the_guardian: { meta: null, atlasJson: null, atlasImg: null, loaded: false }
  },

  // Internal Timing
  lastTime: 0,
  frameTimer: 0,
  currentAnimDuration: 0,
  elapsedAnimTime: 0
};

// Canvas references
const canvas = document.getElementById('stageCanvas');
const ctx = canvas.getContext('2d');
const canvasWrapper = document.getElementById('canvasWrapper');

// UI references
const btnPlayPause = document.getElementById('btnPlayPause');
const btnPrevFrame = document.getElementById('btnPrevFrame');
const btnNextFrame = document.getElementById('btnNextFrame');
const btnAudioToggle = document.getElementById('btnAudioToggle');
const speedSlider = document.getElementById('speedSlider');
const speedLabel = document.getElementById('speedLabel');
const frameCounter = document.getElementById('frameCounter');
const timingInfo = document.getElementById('timingInfo');
const timelineProgress = document.getElementById('timelineProgress');
const timelineTrack = document.getElementById('timelineTrack');
const animButtonsContainer = document.getElementById('animationButtons');
const animFpsBadge = document.getElementById('animFpsBadge');
const frameMetaDump = document.getElementById('frameMetaDump');
const engineStatus = document.getElementById('engineStatus');

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
    // Attack slash sound (frequency sweep + noise)
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
    // Energy shield deploy / block pulse
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
    // Footstep run thump
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(90, now);
    osc.frequency.exponentialRampToValueAtTime(30, now + 0.08);
    gain.gain.setValueAtTime(0.18, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.08);
  } else if (type === 'land') {
    // Heavy jump landing impact
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(180, now);
    osc.frequency.exponentialRampToValueAtTime(35, now + 0.3);
    gain.gain.setValueAtTime(0.4, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.3);
  }
}

// Load Character Data
async function loadCharacter(charId, forceReload = false) {
  const char = state.characters[charId];
  const isFhd = state.atlasRes === 'fhd';
  const atlasSuffix = isFhd ? '_atlas_fhd' : '_atlas';

  if (char.loaded && !forceReload && char.currentRes === state.atlasRes) return;

  engineStatus.textContent = `Loading ${charId} (${state.atlasRes.toUpperCase()})...`;

  try {
    const [metaRes, atlasRes] = await Promise.all([
      fetch(`assets/${charId}_meta.json`),
      fetch(`assets/${charId}${atlasSuffix}.json`)
    ]);

    char.meta = await metaRes.json();
    char.atlasJson = await atlasRes.json();
    char.currentRes = state.atlasRes;

    // Update canvas base dimensions
    if (isFhd) {
      canvas.width = 288;
      canvas.height = 256;
    } else {
      canvas.width = 576;
      canvas.height = 512;
    }

    await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        char.atlasImg = img;
        char.loaded = true;
        resolve();
      };
      img.onerror = reject;
      img.src = `assets/${charId}${atlasSuffix}.png`;
    });

    engineStatus.textContent = `Ready (${isFhd ? '1024x1024 FHD' : '2048x2048 4K'} Atlas)`;
  } catch (err) {
    console.error(`Failed to load ${charId}:`, err);
    engineStatus.textContent = `Error loading ${charId}`;
  }
}

// Switch Active Character
async function setCharacter(charId) {
  state.activeChar = charId;
  await loadCharacter(charId);

  // Update Character selector buttons
  document.getElementById('btnCharArchitect').classList.toggle('active', charId === 'the_architect');
  document.getElementById('btnCharGuardian').classList.toggle('active', charId === 'the_guardian');

  // Build animation list
  const char = state.characters[charId];
  const anims = Object.keys(char.meta.animations);

  animButtonsContainer.innerHTML = '';
  anims.forEach((anim, idx) => {
    const aInfo = char.meta.animations[anim];
    const btn = document.createElement('button');
    btn.className = `anim-btn ${anim === state.activeAnim ? 'active' : ''}`;
    btn.innerHTML = `<span>${anim}</span><span class="anim-frame-count">${aInfo.frame_count}f</span>`;
    btn.onclick = () => setAnimation(anim);
    animButtonsContainer.appendChild(btn);
  });

  if (!anims.includes(state.activeAnim)) {
    state.activeAnim = anims[0];
  }

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

  animFpsBadge.textContent = `${animInfo.fps} FPS`;

  // Update buttons
  const btns = animButtonsContainer.querySelectorAll('.anim-btn');
  btns.forEach(btn => {
    btn.classList.toggle('active', btn.querySelector('span').textContent === animName);
  });

  updateTimeline();
  drawStage();
}

// Animation Loop
function updateAnimation(dt) {
  const char = state.characters[state.activeChar];
  if (!char || !char.loaded) return;

  const animInfo = char.meta.animations[state.activeAnim];
  if (!animInfo || animInfo.frame_count === 0) return;

  const frameDuration = (1.0 / animInfo.fps) / state.playbackSpeed;
  state.currentAnimDuration = frameDuration * animInfo.frame_count;

  if (state.isPlaying) {
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
          btnPlayPause.textContent = '▶';
        }
      }

      // Trigger SFX on keyframe transitions
      if (prevIdx !== state.currentFrameIdx) {
        onFrameChanged(state.currentFrameIdx);
      }

      updateTimeline();
    }
  }
}

function onFrameChanged(frameIdx) {
  const anim = state.activeAnim;
  if (anim === 'attack') {
    if (frameIdx === 1 || frameIdx === 2) playSound('whoosh');
  } else if (anim === 'defend') {
    if (frameIdx === 1) playSound('shield');
  } else if (anim === 'run') {
    if (frameIdx === 1 || frameIdx === 5) playSound('step');
  } else if (anim === 'jump') {
    if (frameIdx === 2) playSound('land');
  }
}

// Draw Frame and Overlays
function drawStage() {
  try {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const char = state.characters[state.activeChar];
    if (!char || !char.loaded || !char.atlasJson) return;

    const frameKey = `${state.activeAnim}_${String(state.currentFrameIdx).padStart(2, '0')}.png`;
    const frameData = char.atlasJson.frames[frameKey];

    if (!frameData) {
      return;
    }

    const { frame, spriteSourceSize } = frameData;
    const isFhd = state.atlasRes === 'fhd';
    const scale = isFhd ? 0.5 : 1.0;
    const groundY = 460 * scale;
    const pivotX = 288 * scale;

    // 1. Draw Frame Canvas Bounds
    if (state.showFrameBox) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
      ctx.lineWidth = 1;
      ctx.strokeRect(0, 0, canvas.width, canvas.height);
    }

    // 2. Draw Ground Baseline
    if (state.showGroundLine) {
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
      ctx.setLineDash([6, 4]);
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(0, groundY + 0.5);
      ctx.lineTo(canvas.width, groundY + 0.5);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = 'rgba(0, 240, 255, 0.7)';
      ctx.font = '10px "JetBrains Mono"';
      ctx.fillText(`GROUND (Y=${Math.round(groundY)})`, 10, groundY - 5);
    }

    // 3. Draw Character Sprite from Atlas
    if (char.atlasImg && char.atlasImg.complete && char.atlasImg.naturalWidth > 0 && frame && spriteSourceSize) {
      ctx.drawImage(
        char.atlasImg,
        Math.round(frame.x), Math.round(frame.y), Math.round(frame.w), Math.round(frame.h),
        Math.round(spriteSourceSize.x), Math.round(spriteSourceSize.y), Math.round(spriteSourceSize.w), Math.round(spriteSourceSize.h)
      );
    }

    // 4. Draw Hitbox
    if (state.showHitbox && char.meta && char.meta.hitbox) {
      const hb = char.meta.hitbox;
      const px = (288 + hb.offset_x) * scale;
      const py = (460 + hb.offset_y) * scale;
      const pw = hb.width * scale;
      const ph = hb.height * scale;

      ctx.strokeStyle = 'rgba(0, 255, 136, 0.85)';
      ctx.fillStyle = 'rgba(0, 255, 136, 0.1)';
      ctx.lineWidth = 2;
      ctx.fillRect(px, py, pw, ph);
      ctx.strokeRect(px, py, pw, ph);

      // Hitbox label
      ctx.fillStyle = 'rgba(0, 255, 136, 0.9)';
      ctx.font = '10px "JetBrains Mono"';
      ctx.fillText('HURTBOX', px + 4, py + 14);
    }

    // 5. Draw Ground Pivot Marker
    if (state.showPivot) {
      const px = pivotX;
      const py = groundY;

      // Crosshair
      ctx.strokeStyle = '#ff3366';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(px - 10, py);
      ctx.lineTo(px + 10, py);
      ctx.moveTo(px, py - 10);
      ctx.lineTo(px, py + 10);
      ctx.stroke();

      ctx.fillStyle = '#ff3366';
      ctx.beginPath();
      ctx.arc(px, py, 3, 0, Math.PI * 2);
      ctx.fill();

      ctx.font = '10px "JetBrains Mono"';
      ctx.fillText(`PIVOT (${Math.round(px)}, ${Math.round(py)})`, px + 6, py - 6);
    }

    // Update Inspector Meta Dump
    if (frameMetaDump && char.meta) {
      frameMetaDump.textContent = JSON.stringify({
        character: char.meta.name,
        animation: state.activeAnim,
        frame: state.currentFrameIdx,
        atlas_source: frameKey,
        atlas_rect: frame,
        canvas_placement: spriteSourceSize,
        pivot_normalized: frameData.pivot
      }, null, 2);
    }
  } catch (renderErr) {
    console.error("Render loop error in drawStage:", renderErr);
    if (frameMetaDump) {
      frameMetaDump.textContent = "Render Error: " + renderErr.message;
    }
  }
}

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

// UI Event Handlers
btnPlayPause.onclick = () => {
  state.isPlaying = !state.isPlaying;
  btnPlayPause.textContent = state.isPlaying ? '⏸' : '▶';
};

btnPrevFrame.onclick = () => {
  state.isPlaying = false;
  btnPlayPause.textContent = '▶';
  const char = state.characters[state.activeChar];
  const count = char.meta.animations[state.activeAnim].frame_count;
  state.currentFrameIdx = (state.currentFrameIdx - 1 + count) % count;
  updateTimeline();
  drawStage();
};

btnNextFrame.onclick = () => {
  state.isPlaying = false;
  btnPlayPause.textContent = '▶';
  const char = state.characters[state.activeChar];
  const count = char.meta.animations[state.activeAnim].frame_count;
  state.currentFrameIdx = (state.currentFrameIdx + 1) % count;
  updateTimeline();
  drawStage();
};

btnAudioToggle.onclick = () => {
  state.audioEnabled = !state.audioEnabled;
  btnAudioToggle.textContent = state.audioEnabled ? '🔊 SFX ON' : '🔇 SFX OFF';
  btnAudioToggle.classList.toggle('active', state.audioEnabled);
  if (state.audioEnabled) initAudio();
};

speedSlider.oninput = (e) => {
  state.playbackSpeed = parseFloat(e.target.value);
  speedLabel.textContent = `${state.playbackSpeed.toFixed(2)}x`;
};

timelineTrack.onclick = (e) => {
  const rect = timelineTrack.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  const char = state.characters[state.activeChar];
  const count = char.meta.animations[state.activeAnim].frame_count;
  state.currentFrameIdx = Math.min(Math.floor(ratio * count), count - 1);
  state.isPlaying = false;
  btnPlayPause.textContent = '▶';
  updateTimeline();
  drawStage();
};

// Character Switchers
document.getElementById('btnCharArchitect').onclick = () => setCharacter('the_architect');
document.getElementById('btnCharGuardian').onclick = () => setCharacter('the_guardian');

// Inspector Toggles
document.getElementById('chkHitbox').onchange = (e) => { state.showHitbox = e.target.checked; drawStage(); };
document.getElementById('chkPivot').onchange = (e) => { state.showPivot = e.target.checked; drawStage(); };
document.getElementById('chkGroundLine').onchange = (e) => { state.showGroundLine = e.target.checked; drawStage(); };
document.getElementById('chkFrameBox').onchange = (e) => { state.showFrameBox = e.target.checked; drawStage(); };

// Background Buttons
document.querySelectorAll('.bg-btn').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.bg-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    canvasWrapper.className = `canvas-wrapper bg-${btn.dataset.bg}`;
  };
});

// Zoom & Pan System
state.panX = 0;
state.panY = 20;
state.isDragging = false;
state.dragStartX = 0;
state.dragStartY = 0;

function updateTransform() {
  canvas.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${state.zoom})`;
}

function setZoom(scale, activeBtnId = null) {
  state.zoom = Math.max(0.35, Math.min(3.0, scale));
  updateTransform();

  document.querySelectorAll('.zoom-btn').forEach(b => b.classList.remove('active'));
  if (activeBtnId) {
    const el = document.getElementById(activeBtnId);
    if (el) el.classList.add('active');
  }
}

function fitToViewport() {
  const rect = canvasWrapper.getBoundingClientRect();
  const wrapperHeight = rect.height || 560;
  const wrapperWidth = rect.width || 800;

  // Fit active canvas with 15% margin
  const baseW = canvas.width || 576;
  const baseH = canvas.height || 512;
  const scaleY = (wrapperHeight * 0.85) / baseH;
  const scaleX = (wrapperWidth * 0.85) / baseW;
  const optimalScale = Math.min(scaleX, scaleY, state.atlasRes === 'fhd' ? 2.0 : 1.0);

  state.panX = 0;
  state.panY = 15;
  setZoom(optimalScale, 'btnZoomFit');
}

// Mouse Wheel Zoom
canvasWrapper.addEventListener('wheel', (e) => {
  e.preventDefault();
  const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
  setZoom(state.zoom * zoomFactor);
}, { passive: false });

// Drag to Pan
canvasWrapper.addEventListener('mousedown', (e) => {
  if (e.button !== 0) return; // Left click only
  state.isDragging = true;
  state.dragStartX = e.clientX - state.panX;
  state.dragStartY = e.clientY - state.panY;
  canvasWrapper.classList.add('dragging');
});

window.addEventListener('mousemove', (e) => {
  if (!state.isDragging) return;
  state.panX = e.clientX - state.dragStartX;
  state.panY = e.clientY - state.dragStartY;
  updateTransform();
});

window.addEventListener('mouseup', () => {
  if (state.isDragging) {
    state.isDragging = false;
    canvasWrapper.classList.remove('dragging');
  }
});

// Zoom Preset Buttons
document.getElementById('btnZoomFit').onclick = () => fitToViewport();
document.getElementById('btnZoom05').onclick = () => { state.panX = 0; state.panY = 0; setZoom(0.5, 'btnZoom05'); };
document.getElementById('btnZoom075').onclick = () => { state.panX = 0; state.panY = 15; setZoom(0.75, 'btnZoom075'); };
document.getElementById('btnZoom1').onclick = () => { state.panX = 0; state.panY = 15; setZoom(1.0, 'btnZoom1'); };
document.getElementById('btnZoom15').onclick = () => { state.panX = 0; state.panY = 15; setZoom(1.5, 'btnZoom15'); };

// Resolution Switchers
document.getElementById('btnRes4k').onclick = async () => {
  if (state.atlasRes === '4k') return;
  state.atlasRes = '4k';
  document.getElementById('btnRes4k').classList.add('active');
  document.getElementById('btnResFhd').classList.remove('active');
  await loadCharacter(state.activeChar, true);
  fitToViewport();
  drawStage();
};

document.getElementById('btnResFhd').onclick = async () => {
  if (state.atlasRes === 'fhd') return;
  state.atlasRes = 'fhd';
  document.getElementById('btnResFhd').classList.add('active');
  document.getElementById('btnRes4k').classList.remove('active');
  await loadCharacter(state.activeChar, true);
  fitToViewport();
  drawStage();
};

window.addEventListener('resize', () => {
  if (document.getElementById('btnZoomFit').classList.contains('active')) {
    fitToViewport();
  }
});

// Keyboard Hotkeys
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;

  if (e.code === 'Space') {
    e.preventDefault();
    btnPlayPause.click();
  } else if (e.code === 'ArrowLeft') {
    btnPrevFrame.click();
  } else if (e.code === 'ArrowRight') {
    btnNextFrame.click();
  } else if (e.key === 'c' || e.key === 'C') {
    const nextChar = state.activeChar === 'the_architect' ? 'the_guardian' : 'the_architect';
    setCharacter(nextChar);
  } else if (e.key >= '1' && e.key <= '6') {
    const btns = animButtonsContainer.querySelectorAll('.anim-btn');
    const idx = parseInt(e.key) - 1;
    if (btns[idx]) btns[idx].click();
  } else if (e.key === '0') {
    fitToViewport();
  }
});

// Initialization
async function init() {
  await setCharacter('the_architect');
  fitToViewport();
  requestAnimationFrame(loop);
}

init();
