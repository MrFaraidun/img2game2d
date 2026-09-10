/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Multi-Engine Real-Time Integration Code Generators
 * 
 * Produces production-ready, fully commented, idiomatic source code
 * and scene configurations for Godot 4.x, Unity 2022+ URP, Phaser 3, and PixiJS.
 */

import {
  CharacterId,
  EngineTarget,
  GodotExportConfig,
  UnityExportConfig,
  PhaserExportConfig,
  PixiExportConfig,
  CharacterMetadata
} from '../types';

// ============================================================================
// 1. Godot 4.x Code Generators
// ============================================================================

/**
 * Generates production-ready Godot 4.x GDScript character controller
 */
export function generateGodotScript(
  charId: CharacterId,
  charMeta: CharacterMetadata | null,
  config: GodotExportConfig
): string {
  const charName = charId === 'the_architect' ? 'TheArchitect' : 'TheGuardian';
  const anims = charMeta ? Object.keys(charMeta.animations) : ['idle', 'run', 'jump', 'attack', 'defend', 'hurt'];

  return `class_name ${charName}
extends ${config.targetNode === 'CharacterBody2D' ? 'CharacterBody2D' : 'Node2D'}
## img2game2d v2.0 Autonomous Game Character Controller
## Generated for Godot 4.x with Tangent-Space 2D Normal Map Lighting Support

# Physics Parameters
@export var movement_speed: float = 300.0
@export var jump_velocity: float = -480.0
@export var acceleration: float = 1200.0
@export var friction: float = 1500.0

# Engine Node References
@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var collision_shape: CollisionShape2D = $CollisionShape2D
${config.useNormalMapMaterial ? '@onready var light_occluder: LightOccluder2D = $LightOccluder2D' : ''}

# State Machine
enum State {
\t${anims.map(a => `${a.toUpperCase()}`).join(',\n\t')}
}

var current_state: State = State.IDLE
var is_facing_right: bool = true
var gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")

func _ready() -> void:
\tprint("[${charName}] Initialized via img2game2d v2.0 runtime.")
\t_setup_lighting_material()
\t_play_animation("idle")

func _physics_process(delta: float) -> void:
\t# Gravity application
\tif not is_on_floor():
\t\tvelocity.y += gravity * delta

\t# Handle horizontal input
\tvar input_dir: float = Input.get_axis("ui_left", "ui_right")
\tif input_dir != 0.0:
\t\tvelocity.x = move_toward(velocity.x, input_dir * movement_speed, acceleration * delta)
\t\t_set_facing(input_dir > 0.0)
\telse:
\t\tvelocity.x = move_toward(velocity.x, 0.0, friction * delta)

\t# Handle jump input
\tif Input.is_action_just_pressed("ui_accept") and is_on_floor():
\t\tvelocity.y = jump_velocity
\t\t_change_state(State.JUMP)

\t# Handle combat triggers
\tif Input.is_action_just_pressed("attack") and current_state != State.ATTACK:
\t\t_change_state(State.ATTACK)
\telif Input.is_action_pressed("defend"):
\t\t_change_state(State.DEFEND)

\tmove_and_slide()
\t_update_animation_state()

func _update_animation_state() -> void:
\tif current_state == State.ATTACK or current_state == State.DEFEND or current_state == State.HURT:
\t\treturn # Lock state until action sequence finishes

\tif not is_on_floor():
\t\t_change_state(State.JUMP)
\telif abs(velocity.x) > 10.0:
\t\t_change_state(State.RUN)
\telse:
\t\t_change_state(State.IDLE)

func _change_state(new_state: State) -> void:
\tif current_state == new_state:
\t\treturn
\tcurrent_state = new_state
\tmatch current_state:
${anims.map(a => `\t\tState.${a.toUpperCase()}:\n\t\t\t_play_animation("${a}")`).join('\n')}

func _play_animation(anim_name: String) -> void:
\tif sprite and sprite.sprite_frames and sprite.sprite_frames.has_animation(anim_name):
\t\tsprite.play(anim_name)

func _set_facing(facing_right: bool) -> void:
\tif is_facing_right != facing_right:
\t\tis_facing_right = facing_right
\t\tif sprite:
\t\t\tsprite.flip_h = not is_facing_right

func _setup_lighting_material() -> void:
${config.useNormalMapMaterial ? `\t# Assign 2D Tangent Space Normal Map CanvasItemMaterial
\tvar mat := CanvasItemMaterial.new()
\tmat.light_mode = CanvasItemMaterial.LIGHT_MODE_NORMAL
\tif sprite:
\t\tsprite.material = mat
\t\tprint("[${charName}] 2D Normal Map Shader pipeline engaged.")` : `\t# Standard unlit / diffuse material
\tif sprite:
\t\tsprite.material = null`}

func _on_animated_sprite_2d_animation_finished() -> void:
\tif current_state == State.ATTACK or current_state == State.HURT:
\t\t_change_state(State.IDLE)
`;
}

/**
 * Generates Godot 4.x .tscn declarative scene tree file
 */
export function generateGodotScene(
  charId: CharacterId,
  config: GodotExportConfig
): string {
  const charName = charId === 'the_architect' ? 'TheArchitect' : 'TheGuardian';
  
  return `[gd_scene load_steps=4 format=3 uid="uid://${charId}v200"]

[ext_resource type="Script" path="res://${charId}.gd" id="1_script"]
[ext_resource type="SpriteFrames" path="res://${charId}_frames.tres" id="2_frames"]

[sub_resource type="CapsuleShape2D" id="CapsuleShape2D_1"]
radius = 24.0
height = 96.0

[node name="${charName}" type="${config.targetNode}"]
script = ExtResource("1_script")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
texture_filter = ${config.textureFilter === 'nearest' ? '0' : '1'}
sprite_frames = ExtResource("2_frames")
animation = &"idle"
autoplay = "idle"
centered = true
offset = Vector2(0, -48)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
position = Vector2(0, -48)
shape = SubResource("CapsuleShape2D_1")

[node name="PointLight2D" type="PointLight2D" parent="."]
position = Vector2(0, -64)
energy = 1.2
texture_scale = 1.5
`;
}

// ============================================================================
// 2. Unity 2022+ URP Code Generators
// ============================================================================

/**
 * Generates Unity 2D C# Player Controller with URP Normal Map support
 */
export function generateUnityScript(
  charId: CharacterId,
  charMeta: CharacterMetadata | null,
  config: UnityExportConfig
): string {
  const charName = charId === 'the_architect' ? 'TheArchitectController' : 'TheGuardianController';

  return `using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Img2Game2D.Runtimes
{
    /// <summary>
    /// img2game2d v2.0 Universal Character Controller for Unity 2022+ URP
    /// Handles 2D Rigidbody physics, Animator parameters, and URP 2D Lit Sprite Normal Maps.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    [RequireComponent(typeof(SpriteRenderer))]
    [RequireComponent(typeof(Animator))]
    public class ${charName} : MonoBehaviour
    {
        [Header("Movement Configuration")]
        [SerializeField] private float moveSpeed = 8.0f;
        [SerializeField] private float jumpForce = 14.0f;
        [SerializeField] private LayerMask groundLayer;
        [SerializeField] private Transform groundCheckPoint;

        [Header("URP 2D Lighting")]
        [SerializeField] private Material litSpriteMaterial;
        [SerializeField] private Texture2D normalMapTexture;
        [SerializeField] private Texture2D emissionMapTexture;

        // Cached Component References
        private Rigidbody2D rb;
        private SpriteRenderer spriteRenderer;
        private Animator animator;

        // Internal State
        private float horizontalInput;
        private bool isGrounded;
        private bool isFacingRight = true;

        // Animator Parameter Hashes
        private static readonly int SpeedHash = Animator.StringToHash("Speed");
        private static readonly int IsGroundedHash = Animator.StringToHash("IsGrounded");
        private static readonly int JumpTriggerHash = Animator.StringToHash("Jump");
        private static readonly int AttackTriggerHash = Animator.StringToHash("Attack");
        private static readonly int DefendBoolHash = Animator.StringToHash("IsDefending");

        private void Awake()
        {
            rb = GetComponent<Rigidbody2D>();
            spriteRenderer = GetComponent<SpriteRenderer>();
            animator = GetComponent<Animator>();

            ConfigureUrpMaterial();
        }

        private void Update()
        {
            // Read input
            horizontalInput = Input.GetAxisRaw("Horizontal");

            // Ground check probe
            if (groundCheckPoint != null)
            {
                isGrounded = Physics2D.OverlapCircle(groundCheckPoint.position, 0.2f, groundLayer);
            }
            else
            {
                isGrounded = Mathf.Abs(rb.velocity.y) < 0.01f;
            }

            // Jump command
            if (Input.GetButtonDown("Jump") && isGrounded)
            {
                rb.velocity = new Vector2(rb.velocity.x, jumpForce);
                animator.SetTrigger(JumpTriggerHash);
            }

            // Combat commands
            if (Input.GetButtonDown("Fire1"))
            {
                animator.SetTrigger(AttackTriggerHash);
            }

            bool isDefending = Input.GetButton("Fire2");
            animator.SetBool(DefendBoolHash, isDefending);

            // Update facing direction
            if (horizontalInput > 0.01f && !isFacingRight)
            {
                Flip();
            }
            else if (horizontalInput < -0.01f && isFacingRight)
            {
                Flip();
            }

            // Sync Animator parameters
            animator.SetFloat(SpeedHash, Mathf.Abs(horizontalInput));
            animator.SetBool(IsGroundedHash, isGrounded);
        }

        private void FixedUpdate()
        {
            rb.velocity = new Vector2(horizontalInput * moveSpeed, rb.velocity.y);
        }

        private void Flip()
        {
            isFacingRight = !isFacingRight;
            spriteRenderer.flipX = !isFacingRight;
        }

        private void ConfigureUrpMaterial()
        {
            if (litSpriteMaterial != null)
            {
                Material instanceMat = new Material(litSpriteMaterial);
                if (normalMapTexture != null)
                {
                    instanceMat.SetTexture("_NormalMap", normalMapTexture);
                }
                if (emissionMapTexture != null)
                {
                    instanceMat.SetTexture("_MaskTex", emissionMapTexture);
                }
                spriteRenderer.material = instanceMat;
                Debug.Log($"[{name}] Configured with URP 2D Lit Sprite Material (PPU: ${config.pixelsPerUnit}).");
            }
        }
    }
}
`;
}

// ============================================================================
// 3. Phaser 3 Code Generators
// ============================================================================

/**
 * Generates Phaser 3 TypeScript Scene class with Light2D pipeline support
 */
export function generatePhaserScript(
  charId: CharacterId,
  charMeta: CharacterMetadata | null,
  config: PhaserExportConfig
): string {
  const className = charId === 'the_architect' ? 'TheArchitectScene' : 'TheGuardianScene';
  const anims = charMeta ? Object.keys(charMeta.animations) : ['idle', 'run', 'jump', 'attack', 'defend', 'hurt'];

  return `import Phaser from 'phaser';

/**
 * img2game2d v2.0 Phaser 3 Game Scene Integration
 * Demonstrates TexturePacker JSON Hash atlas animation and dynamic 2D Light pipeline.
 */
export class ${className} extends Phaser.Scene {
  private player!: Phaser.Types.Physics.Arcade.SpriteWithDynamicBody;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private torchLight!: Phaser.GameObjects.Light;

  constructor() {
    super({ key: '${className}' });
  }

  preload(): void {
    // Load TexturePacker Atlas & Normal Maps
    this.load.atlas(
      '${charId}',
      '/assets/${charId}_atlas.png',
      '/assets/${charId}_atlas.json'
    );

    ${config.enableLight2DPipeline ? `// Load Normal Map for 2D Tangent Space Light Pipeline
    this.load.image('${charId}_normal', '/assets/${charId}_atlas_normal.png');` : ''}
  }

  create(): void {
    ${config.enableLight2DPipeline ? `// Enable 2D Lighting Engine
    this.lights.enable();
    this.lights.setAmbientColor(0x334155);

    // Dynamic mouse-following point light
    this.torchLight = this.lights.addLight(400, 300, 350, 0x00f0ff, 2.0);
    this.input.on('pointermove', (pointer: Phaser.Input.Pointer) => {
      this.torchLight.setPosition(pointer.x, pointer.y);
    });` : ''}

    // Register animations from extracted atlas frames
    ${anims.map(a => {
      const aMeta = charMeta?.animations[a];
      const count = aMeta?.frame_count || 4;
      const fps = aMeta?.fps || config.frameRate;
      return `this.anims.create({
      key: '${a}',
      frames: this.anims.generateFrameNames('${charId}', {
        prefix: '${a}_',
        start: 0,
        end: ${count - 1},
        zeroPad: 2,
        suffix: '.png'
      }),
      frameRate: ${fps},
      repeat: ${a === 'idle' || a === 'run' ? -1 : 0}
    });`;
    }).join('\n\n    ')}

    // Spawn Player Sprite
    this.player = this.physics.add.sprite(400, 400, '${charId}', 'idle_00.png');
    this.player.setCollideWorldBounds(true);
    this.player.play('idle');

    ${config.enableLight2DPipeline ? `// Attach 2D Light Pipeline
    this.player.setPipeline('Light2D');` : ''}

    // Keyboard bindings
    if (this.input.keyboard) {
      this.cursors = this.input.keyboard.createCursorKeys();
    }
  }

  update(): void {
    if (!this.cursors || !this.player) return;

    const speed = 260;
    const isMoving = this.cursors.left.isDown || this.cursors.right.isDown;

    if (this.cursors.left.isDown) {
      this.player.setVelocityX(-speed);
      this.player.setFlipX(true);
      if (this.player.anims.currentAnim?.key !== 'run') {
        this.player.play('run', true);
      }
    } else if (this.cursors.right.isDown) {
      this.player.setVelocityX(speed);
      this.player.setFlipX(false);
      if (this.player.anims.currentAnim?.key !== 'run') {
        this.player.play('run', true);
      }
    } else {
      this.player.setVelocityX(0);
      if (this.player.anims.currentAnim?.key !== 'idle' && !this.player.anims.isPlaying) {
        this.player.play('idle', true);
      }
    }

    if (this.cursors.space.isDown && this.player.body.touching.down) {
      this.player.setVelocityY(-450);
      this.player.play('jump', true);
    }
  }
}
`;
}

// ============================================================================
// 4. PixiJS Code Generators
// ============================================================================

/**
 * Generates PixiJS TypeScript setup with AnimatedSprite
 */
export function generatePixiScript(
  charId: CharacterId,
  charMeta: CharacterMetadata | null,
  config: PixiExportConfig
): string {
  const anims = charMeta ? Object.keys(charMeta.animations) : ['idle', 'run', 'jump'];

  return `import * as PIXI from 'pixi.js';

/**
 * img2game2d v2.0 PixiJS WebGL Integration
 * Initializes PIXI.Application and loads TexturePacker atlas AnimatedSprite.
 */
export async function initCharacterStage(containerId: string) {
  const app = new PIXI.Application();
  
  await app.init({
    width: 800,
    height: 600,
    backgroundColor: 0x0f172a,
    resolution: window.devicePixelRatio || 1,
    autoDensity: true
  });

  const container = document.getElementById(containerId);
  if (container) {
    container.appendChild(app.canvas);
  }

  // Load Spritesheet Atlas JSON
  const sheet = await PIXI.Assets.load('/assets/${charId}_atlas.json');
  console.log('[PixiJS] Loaded spritesheet:', sheet);

  // Extract animation frame textures
  const animations: Record<string, PIXI.Texture[]> = {};
  ${anims.map(a => {
    return `animations['${a}'] = sheet.data.animations?.['${a}'] 
    ? sheet.animations['${a}'] 
    : Object.keys(sheet.textures)
        .filter(k => k.startsWith('${a}_'))
        .map(k => sheet.textures[k]);`;
  }).join('\n  ')}

  // Create AnimatedSprite with Idle sequence
  const character = new PIXI.AnimatedSprite(animations['idle'] || []);
  character.anchor.set(${config.anchorX}, ${config.anchorY});
  character.x = app.screen.width / 2;
  character.y = app.screen.height * 0.8;
  character.animationSpeed = ${config.animationSpeed};
  character.play();

  app.stage.addChild(character);

  // Animation switcher API
  return {
    app,
    character,
    playAnimation: (animName: string) => {
      if (animations[animName]) {
        character.textures = animations[animName];
        character.loop = animName === 'idle' || animName === 'run';
        character.play();
      }
    }
  };
}
`;
}
