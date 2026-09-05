/**
 * Hollow Knight 2D Asset Studio - Interactive Runtime Viewer
 * Features:
 * - Real-time sprite animation playback with variable frame rates
 * - Web Audio API procedural sound synthesis (nail slash, jump leap, footsteps, hurt hit)
 * - Onion skinning, skeletal rig overlays, and dynamic hitbox visualizer
 * - Keyboard & manual action controls
 * - Multi-engine integration snippets (Godot, Unity, Phaser, PixiJS)
 * - Decomposed layer inspector
 */

(function () {
  'use strict';

  // ── 1. CONFIGURATION & CLIP DEFINITIONS ──
  const CLIPS = {
    idle:   { name: 'IDLE',   frames: 4, fps: 8,  loop: true,  title: 'Idle Stance' },
    walk:   { name: 'WALK',   frames: 8, fps: 12, loop: true,  title: 'Walk Stride' },
    attack: { name: 'ATTACK', frames: 6, fps: 14, loop: false, title: 'Nail Slash' },
    jump:   { name: 'JUMP',   frames: 6, fps: 10, loop: false, title: 'Jump Leap' },
    hurt:   { name: 'HURT',   frames: 4, fps: 10, loop: false, title: 'Damage Recoil' },
  };

  const LAYERS = [
    { name: 'Head & Horns', file: 'head.png', zIndex: 40, desc: 'Pure white mask with distinct crescent horns' },
    { name: 'Nail Blade', file: 'weapon.png', zIndex: 30, desc: 'Sharpened ancient iron nail with wrapped grip' },
    { name: 'Cloak & Torso', file: 'cloak.png', zIndex: 20, desc: 'Flowing charcoal wanderer cloak with sealed pelvis' },
    { name: 'Left Leg', file: 'leg_left.png', zIndex: 10, desc: 'Chitin leg with circular rotation joint cap' },
    { name: 'Right Leg', file: 'leg_right.png', zIndex: 10, desc: 'Chitin leg with circular rotation joint cap' },
  ];

  const ENGINE_SNIPPETS = {
    godot: `# Hollow Knight - Godot 4 GDScript Integration
extends CharacterBody2D

@onready var anim_sprite: AnimatedSprite2D = $AnimatedSprite2D

const SPEED = 240.0
const JUMP_VELOCITY = -420.0
var gravity = ProjectSettings.get_setting("physics/2d/default_gravity")

func _ready():
    # Load TexturePacker JSON or SpriteFrames
    anim_sprite.play("idle")

func _physics_process(delta):
    if not is_on_floor():
        velocity.y += gravity * delta

    if Input.is_action_just_pressed("attack"):
        anim_sprite.play("attack")
    elif Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_VELOCITY
        anim_sprite.play("jump")
    
    var direction = Input.get_axis("ui_left", "ui_right")
    if direction:
        velocity.x = direction * SPEED
        anim_sprite.flip_h = direction < 0
        if is_on_floor() and anim_sprite.animation != "attack":
            anim_sprite.play("walk")
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)
        if is_on_floor() and anim_sprite.animation != "attack" and anim_sprite.animation != "hurt":
            anim_sprite.play("idle")

    move_and_slide()`,

    unity: `// Hollow Knight - Unity 2D (C#) Controller
using UnityEngine;

[RequireComponent(typeof(SpriteRenderer), typeof(Rigidbody2D))]
public class HollowKnightController : MonoBehaviour
{
    [SerializeField] private Animator animator;
    [SerializeField] private float moveSpeed = 6f;
    [SerializeField] private float jumpForce = 12f;

    private Rigidbody2D rb;
    private bool isGrounded;

    void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    void Update()
    {
        float moveX = Input.GetAxisRaw("Horizontal");
        rb.velocity = new Vector2(moveX * moveSpeed, rb.velocity.y);

        if (moveX != 0)
            transform.localScale = new Vector3(Mathf.Sign(moveX), 1, 1);

        if (Input.GetKeyDown(KeyCode.J))
            animator.SetTrigger("Attack");

        if (Input.GetButtonDown("Jump") && isGrounded)
        {
            rb.velocity = new Vector2(rb.velocity.x, jumpForce);
            animator.SetTrigger("Jump");
        }

        animator.SetFloat("Speed", Mathf.Abs(moveX));
    }
}`,

    phaser: `// Hollow Knight - Phaser 3 Scene Preload & Playback
export class KnightScene extends Phaser.Scene {
  constructor() {
    super('KnightScene');
  }

  preload() {
    // Load atlases exported from pipeline
    this.load.atlas('knight_idle', 'atlases/idle.png', 'atlases/idle.json');
    this.load.atlas('knight_walk', 'atlases/walk.png', 'atlases/walk.json');
    this.load.atlas('knight_attack', 'atlases/attack.png', 'atlases/attack.json');
    this.load.atlas('knight_jump', 'atlases/jump.png', 'atlases/jump.json');
    this.load.atlas('knight_hurt', 'atlases/hurt.png', 'atlases/hurt.json');
  }

  create() {
    // Generate animations
    this.anims.create({
      key: 'idle',
      frames: this.anims.generateFrameNames('knight_idle', { prefix: 'idle_', zeroPad: 2, suffix: '.png', start: 0, end: 3 }),
      frameRate: 8,
      repeat: -1
    });

    this.anims.create({
      key: 'attack',
      frames: this.anims.generateFrameNames('knight_attack', { prefix: 'attack_', zeroPad: 2, suffix: '.png', start: 0, end: 5 }),
      frameRate: 14,
      repeat: 0
    });

    const player = this.physics.add.sprite(400, 300, 'knight_idle', 'idle_00.png');
    player.play('idle');
  }
}`,

    pixijs: `// Hollow Knight - PixiJS v8 AnimatedSprite
import { Application, Assets, AnimatedSprite } from 'pixi.js';

const app = new Application();
await app.init({ width: 960, height: 540, backgroundColor: 0x07090e });
document.body.appendChild(app.canvas);

// Load spritesheet asset bundle
const sheet = await Assets.load('exports/pixijs/hollow_knight_attack.json');

// Instantiate animated nail strike
const knight = new AnimatedSprite(sheet.animations['attack']);
knight.anchor.set(0.5, 0.95);
knight.x = app.screen.width / 2;
knight.y = 420;
knight.animationSpeed = 0.23; // 14 fps
knight.loop = false;
knight.play();

app.stage.addChild(knight);`
  };

  // ── 2. STATE ──
  const state = {
    currentClip: 'idle',
    currentFrame: 0,
    isPlaying: true,
    playbackSpeed: 1.0,
    lastFrameTime: 0,
    showHitbox: false,
    showSkeleton: false,
    showOnion: false,
    soundEnabled: true,
    currentEngine: 'godot',
    loadedImages: {}, // clip -> [Image]
    particles: [],
    keysPressed: {},
  };

  // ── 3. DOM ELEMENTS ──
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  const currentActionBadge = document.getElementById('currentActionBadge');
  const btnPlayPause = document.getElementById('btnPlayPause');
  const iconPlay = document.getElementById('iconPlay');
  const iconPause = document.getElementById('iconPause');
  const btnPrevFrame = document.getElementById('btnPrevFrame');
  const btnNextFrame = document.getElementById('btnNextFrame');
  const frameCounter = document.getElementById('frameCounter');
  const frameSlider = document.getElementById('frameSlider');
  const speedButtons = document.querySelectorAll('.speed-selector .btn-chip');
  const clipCards = document.querySelectorAll('.clip-card');
  const toggleHitbox = document.getElementById('toggleHitbox');
  const toggleSkeleton = document.getElementById('toggleSkeleton');
  const toggleOnion = document.getElementById('toggleOnion');
  const toggleMute = document.getElementById('toggleMute');
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  const layerListContainer = document.getElementById('layerListContainer');
  const engineTabButtons = document.querySelectorAll('.engine-tab-btn');
  const engineCodeSnippet = document.getElementById('engineCodeSnippet');

  const btnActionWalk = document.getElementById('btnActionWalk');
  const btnActionJump = document.getElementById('btnActionJump');
  const btnActionAttack = document.getElementById('btnActionAttack');
  const btnActionHurt = document.getElementById('btnActionHurt');

  // ── 4. WEB AUDIO PROCEDURAL SYNTHESIZER ──
  let audioCtx = null;
  function getAudioContext() {
    if (!audioCtx) {
      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      if (AudioCtxClass) {
        audioCtx = new AudioCtxClass();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function playProceduralSound(type) {
    if (!state.soundEnabled) return;
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;

    if (type === 'attack') {
      // 1. White noise swoosh with lowpass filter sweep
      const bufferSize = ctx.sampleRate * 0.22;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = Math.random() * 2 - 1;
      }
      const noise = ctx.createBufferSource();
      noise.buffer = buffer;

      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(2600, now);
      filter.frequency.exponentialRampToValueAtTime(320, now + 0.18);
      filter.Q.setValueAtTime(3.5, now);

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.4, now + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

      noise.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);
      noise.start(now);

      // 2. Metallic Nail Ring Tone
      const osc = ctx.createOscillator();
      const oscGain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(840, now);
      osc.frequency.exponentialRampToValueAtTime(420, now + 0.15);
      oscGain.gain.setValueAtTime(0.18, now);
      oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);

      osc.connect(oscGain);
      oscGain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.18);
    } else if (type === 'jump') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(140, now);
      osc.frequency.exponentialRampToValueAtTime(380, now + 0.16);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.2);
    } else if (type === 'step') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(90, now);
      osc.frequency.exponentialRampToValueAtTime(40, now + 0.05);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.06);
    } else if (type === 'hurt') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(180, now);
      osc.frequency.linearRampToValueAtTime(60, now + 0.15);
      gain.gain.setValueAtTime(0.35, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.2);
    }
  }

  // ── 5. ASSET PRELOADING ──
  function preloadAllAssets() {
    Object.keys(CLIPS).forEach(clipKey => {
      const count = CLIPS[clipKey].frames;
      state.loadedImages[clipKey] = [];
      for (let i = 0; i < count; i++) {
        const img = new Image();
        const numStr = String(i).padStart(2, '0');
        img.src = `../animations/${clipKey}/${clipKey}_${numStr}.png`;
        state.loadedImages[clipKey].push(img);
      }
    });

    // Populate Layers Tab
    layerListContainer.innerHTML = '';
    LAYERS.forEach((layer, idx) => {
      const item = document.createElement('div');
      item.className = 'layer-item';
      item.innerHTML = `
        <img class="layer-thumb" src="../layers/${layer.file}" alt="${layer.name}">
        <div class="layer-info">
          <div class="layer-name">${layer.name}</div>
          <div class="layer-details">${layer.desc}</div>
        </div>
        <div class="layer-zindex">Z-${layer.zIndex}</div>
      `;
      layerListContainer.appendChild(item);
    });

    // Populate Initial Engine Snippet
    updateEngineSnippet('godot');
  }

  // ── 6. PARTICLES (ATMOSPHERIC HALLOWNEST SPORES) ──
  function initParticles() {
    state.particles = [];
    for (let i = 0; i < 30; i++) {
      state.particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 2 + 0.8,
        speedY: -(Math.random() * 0.4 + 0.15),
        speedX: (Math.random() - 0.5) * 0.3,
        alpha: Math.random() * 0.5 + 0.2,
        pulse: Math.random() * Math.PI * 2
      });
    }
  }

  function renderAtmosphere() {
    // 1. Background Gradient
    const bgGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    bgGrad.addColorStop(0, '#04060b');
    bgGrad.addColorStop(0.6, '#080d17');
    bgGrad.addColorStop(1, '#05080e');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 2. Cavern Ambient Glow
    const glowGrad = ctx.createRadialGradient(canvas.width / 2, 380, 50, canvas.width / 2, 380, 480);
    glowGrad.addColorStop(0, 'rgba(112, 214, 255, 0.08)');
    glowGrad.addColorStop(0.5, 'rgba(40, 70, 110, 0.05)');
    glowGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = glowGrad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 3. Floating Spores / Dust
    for (let p of state.particles) {
      p.y += p.speedY;
      p.x += p.speedX;
      p.pulse += 0.03;
      if (p.y < 0) {
        p.y = canvas.height;
        p.x = Math.random() * canvas.width;
      }
      const a = p.alpha * (0.6 + 0.4 * Math.sin(p.pulse));
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(140, 220, 255, ${a})`;
      ctx.shadowColor = 'rgba(112, 214, 255, 0.8)';
      ctx.shadowBlur = 6;
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // 4. Ground Platform
    const groundY = 430;
    // Ground base
    const groundGrad = ctx.createLinearGradient(0, groundY, 0, canvas.height);
    groundGrad.addColorStop(0, '#101622');
    groundGrad.addColorStop(0.2, '#0a0d14');
    groundGrad.addColorStop(1, '#040608');
    ctx.fillStyle = groundGrad;
    ctx.fillRect(80, groundY, canvas.width - 160, canvas.height - groundY);

    // Glowing rim
    ctx.beginPath();
    ctx.moveTo(80, groundY);
    ctx.lineTo(canvas.width - 80, groundY);
    ctx.strokeStyle = 'rgba(112, 214, 255, 0.5)';
    ctx.lineWidth = 2;
    ctx.shadowColor = 'rgba(112, 214, 255, 0.7)';
    ctx.shadowBlur = 10;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Platform Bevel Lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineWidth = 1;
    ctx.strokeRect(80, groundY, canvas.width - 160, canvas.height - groundY);

    // 5. Knight Ground Shadow
    const shadowGrad = ctx.createRadialGradient(480, groundY, 10, 480, groundY, 85);
    shadowGrad.addColorStop(0, 'rgba(0, 0, 0, 0.75)');
    shadowGrad.addColorStop(0.7, 'rgba(0, 0, 0, 0.35)');
    shadowGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = shadowGrad;
    ctx.save();
    ctx.scale(1, 0.28);
    ctx.beginPath();
    ctx.arc(480, groundY / 0.28, 85, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // ── 7. MAIN RENDER LOOP ──
  function render(timestamp) {
    if (!state.lastFrameTime) state.lastFrameTime = timestamp;
    const clip = CLIPS[state.currentClip];
    const frameDuration = (1000 / clip.fps) / state.playbackSpeed;

    if (state.isPlaying && timestamp - state.lastFrameTime >= frameDuration) {
      state.lastFrameTime = timestamp;
      const nextFrame = state.currentFrame + 1;
      if (nextFrame >= clip.frames) {
        if (clip.loop) {
          state.currentFrame = 0;
          if (state.currentClip === 'walk') {
            playProceduralSound('step');
          }
        } else {
          // Non-looping finished, hold last frame or reset
          state.currentFrame = clip.frames - 1;
          state.isPlaying = false;
          updatePlayPauseButton();
        }
      } else {
        state.currentFrame = nextFrame;
        // Audio triggers
        if (state.currentClip === 'attack' && state.currentFrame === 1) {
          playProceduralSound('attack');
        } else if (state.currentClip === 'walk' && (state.currentFrame === 0 || state.currentFrame === 4)) {
          playProceduralSound('step');
        }
      }
      updateTimelineUI();
    }

    // Clear and draw background
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    renderAtmosphere();

    // Knight position on stage
    const drawX = canvas.width / 2;
    const drawY = 430; // Feet grounded on platform
    const targetHeight = 290;
    const scale = targetHeight / 512;
    const drawW = 512 * scale;
    const drawH = 512 * scale;
    const destX = drawX - (216 * scale); // 216 is Knight center X in 512 canvas
    const destY = drawY - (480 * scale); // 480 is Knight foot contact Y in 512 canvas

    // 1. Onion Skinning (if toggled)
    if (state.showOnion && state.currentFrame > 0) {
      const prevIdx = state.currentFrame - 1;
      const prevImg = state.loadedImages[state.currentClip]?.[prevIdx];
      if (prevImg && prevImg.complete) {
        ctx.save();
        ctx.globalAlpha = 0.22;
        ctx.drawImage(prevImg, destX - 4, destY, drawW, drawH);
        ctx.restore();
      }
    }

    // 2. Current Character Frame
    const currentImg = state.loadedImages[state.currentClip]?.[state.currentFrame];
    if (currentImg && currentImg.complete) {
      ctx.drawImage(currentImg, destX, destY, drawW, drawH);
    }

    // 3. Overlays: Hitbox / Bounding Box & Pivot
    if (state.showHitbox) {
      ctx.save();
      // Bounding Box
      const boxW = 190 * scale;
      const boxH = 340 * scale;
      const boxX = drawX - boxW / 2;
      const boxY = drawY - boxH;

      ctx.strokeStyle = '#70d6ff';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(boxX, boxY, boxW, boxH);

      // Hitbox Background Tint
      ctx.fillStyle = 'rgba(112, 214, 255, 0.08)';
      ctx.fillRect(boxX, boxY, boxW, boxH);

      // Pivot Crosshair (Root)
      ctx.setLineDash([]);
      ctx.strokeStyle = '#ffd166';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(drawX - 12, drawY);
      ctx.lineTo(drawX + 12, drawY);
      ctx.moveTo(drawX, drawY - 12);
      ctx.lineTo(drawX, drawY + 12);
      ctx.stroke();

      // Pivot Label
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.fillStyle = '#ffd166';
      ctx.fillText(`PIVOT (${drawX}, ${drawY})`, drawX + 16, drawY + 4);
      ctx.fillText(`BOUNDS: ${Math.round(boxW)} x ${Math.round(boxH)} px`, boxX, boxY - 6);
      ctx.restore();
    }

    // 4. Overlays: Skeletal Rig Bones
    if (state.showSkeleton) {
      ctx.save();
      const rootX = drawX;
      const rootY = drawY;
      const pelvisX = drawX;
      const pelvisY = drawY - 90;
      const chestX = drawX - 6;
      const chestY = drawY - 160;
      const headX = drawX - 10;
      const headY = drawY - 210;
      const legLX = drawX - 25;
      const legRX = drawX + 10;

      // Draw Rig Bones
      ctx.strokeStyle = '#ef476f';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      // Spine
      ctx.moveTo(pelvisX, pelvisY);
      ctx.lineTo(chestX, chestY);
      ctx.lineTo(headX, headY);
      // Left leg
      ctx.moveTo(pelvisX, pelvisY);
      ctx.lineTo(legLX, rootY);
      // Right leg
      ctx.moveTo(pelvisX, pelvisY);
      ctx.lineTo(legRX, rootY);
      ctx.stroke();

      // Draw Rig Nodes
      const joints = [
        { x: rootX, y: rootY, r: 4, name: 'Root' },
        { x: pelvisX, y: pelvisY, r: 5, name: 'Pelvis' },
        { x: chestX, y: chestY, r: 5, name: 'Chest' },
        { x: headX, y: headY, r: 6, name: 'Head' },
        { x: legLX, y: rootY, r: 4, name: 'Foot_L' },
        { x: legRX, y: rootY, r: 4, name: 'Foot_R' },
      ];

      joints.forEach(j => {
        ctx.beginPath();
        ctx.arc(j.x, j.y, j.r, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.strokeStyle = '#ef476f';
        ctx.lineWidth = 2;
        ctx.stroke();
      });

      ctx.restore();
    }

    requestAnimationFrame(render);
  }

  // ── 8. UI & INTERACTION HANDLERS ──
  function setClip(clipKey) {
    if (!CLIPS[clipKey]) return;
    state.currentClip = clipKey;
    state.currentFrame = 0;
    state.isPlaying = true;
    state.lastFrameTime = performance.now();

    // Trigger initial sound
    if (clipKey === 'attack') playProceduralSound('attack');
    else if (clipKey === 'jump') playProceduralSound('jump');
    else if (clipKey === 'hurt') playProceduralSound('hurt');

    // Update active clip card
    clipCards.forEach(card => {
      card.classList.toggle('active', card.dataset.clip === clipKey);
    });

    // Update current action badge
    currentActionBadge.textContent = CLIPS[clipKey].name;

    // Update timeline slider max
    frameSlider.max = CLIPS[clipKey].frames - 1;
    frameSlider.value = 0;

    updatePlayPauseButton();
    updateTimelineUI();
  }

  function updateTimelineUI() {
    const clip = CLIPS[state.currentClip];
    frameCounter.textContent = `Frame ${state.currentFrame + 1} / ${clip.frames}`;
    frameSlider.value = state.currentFrame;
  }

  function updatePlayPauseButton() {
    if (state.isPlaying) {
      iconPlay.style.display = 'none';
      iconPause.style.display = 'block';
      btnPlayPause.title = 'Pause (Space)';
    } else {
      iconPlay.style.display = 'block';
      iconPause.style.display = 'none';
      btnPlayPause.title = 'Play (Space)';
    }
  }

  function updateEngineSnippet(engine) {
    state.currentEngine = engine;
    engineTabButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.engine === engine);
    });
    engineCodeSnippet.textContent = ENGINE_SNIPPETS[engine] || '';
  }

  // ── 9. EVENT LISTENERS SETUP ──
  function setupEventListeners() {
    // Play/Pause
    btnPlayPause.addEventListener('click', () => {
      getAudioContext();
      state.isPlaying = !state.isPlaying;
      updatePlayPauseButton();
    });

    // Frame Step Backward
    btnPrevFrame.addEventListener('click', () => {
      state.isPlaying = false;
      const clip = CLIPS[state.currentClip];
      state.currentFrame = (state.currentFrame - 1 + clip.frames) % clip.frames;
      updatePlayPauseButton();
      updateTimelineUI();
    });

    // Frame Step Forward
    btnNextFrame.addEventListener('click', () => {
      state.isPlaying = false;
      const clip = CLIPS[state.currentClip];
      state.currentFrame = (state.currentFrame + 1) % clip.frames;
      updatePlayPauseButton();
      updateTimelineUI();
    });

    // Scrubber Slider
    frameSlider.addEventListener('input', (e) => {
      state.isPlaying = false;
      state.currentFrame = parseInt(e.target.value, 10);
      updatePlayPauseButton();
      updateTimelineUI();
    });

    // Playback Speed Selector
    speedButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        speedButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.playbackSpeed = parseFloat(btn.dataset.speed);
      });
    });

    // Clip Cards
    clipCards.forEach(card => {
      card.addEventListener('click', () => {
        getAudioContext();
        setClip(card.dataset.clip);
      });
    });

    // Overlays Toggles
    toggleHitbox.addEventListener('change', (e) => state.showHitbox = e.target.checked);
    toggleSkeleton.addEventListener('change', (e) => state.showSkeleton = e.target.checked);
    toggleOnion.addEventListener('change', (e) => state.showOnion = e.target.checked);
    toggleMute.addEventListener('change', (e) => state.soundEnabled = e.target.checked);

    // Action Buttons
    btnActionWalk.addEventListener('click', () => setClip('walk'));
    btnActionJump.addEventListener('click', () => setClip('jump'));
    btnActionAttack.addEventListener('click', () => setClip('attack'));
    btnActionHurt.addEventListener('click', () => setClip('hurt'));

    // Tab Navigation
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        tabButtons.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab${tab.charAt(0).toUpperCase() + tab.slice(1)}`).classList.add('active');
      });
    });

    // Engine Tabs
    engineTabButtons.forEach(btn => {
      btn.addEventListener('click', () => updateEngineSnippet(btn.dataset.engine));
    });

    // Keyboard Controls
    window.addEventListener('keydown', (e) => {
      // Avoid firing if focused on inputs
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
      getAudioContext();

      const key = e.key.toLowerCase();
      state.keysPressed[key] = true;

      if (key === 'a' || key === 'd') {
        if (state.currentClip !== 'walk' && state.currentClip !== 'attack') {
          setClip('walk');
        }
      } else if (key === ' ' || e.code === 'Space') {
        e.preventDefault();
        setClip('jump');
      } else if (key === 'j') {
        setClip('attack');
      } else if (key === 'k') {
        setClip('hurt');
      }
    });

    window.addEventListener('keyup', (e) => {
      const key = e.key.toLowerCase();
      delete state.keysPressed[key];

      if (state.currentClip === 'walk' && !state.keysPressed['a'] && !state.keysPressed['d']) {
        setClip('idle');
      }
    });
  }

  // ── 10. INITIALIZATION ──
  function init() {
    preloadAllAssets();
    initParticles();
    setupEventListeners();
    setClip('idle');
    requestAnimationFrame(render);
    console.log('>>> Hollow Knight Asset Studio initialized successfully.');
  }

  window.addEventListener('DOMContentLoaded', init);
})();
