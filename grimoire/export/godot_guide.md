# Godot 4 Integration Guide

## What the Exporter Produces
- `<Name>.tscn` — Scene file with an `AnimatedSprite2D` node pre-configured
- `<Name>_frames.tres` — `SpriteFrames` resource with all animation clips and textures
- `README.md` — Setup instructions

## How to Import into Godot 4
1. Copy the entire `exports/godot/` folder into your Godot project under `res://characters/<name>/`
2. In FileSystem dock, the `.tscn` and `.tres` should appear automatically
3. Open `<Name>.tscn` — the `AnimatedSprite2D` is pre-configured with all clips
4. The default animation (`idle`) will auto-play

## Script Example
```gdscript
extends CharacterBody2D

@onready var sprite := $AnimatedSprite2D

func _ready() -> void:
    sprite.play("idle")

func play_walk() -> void:
    sprite.play("walk")

func play_attack() -> void:
    sprite.play("attack")
    await sprite.animation_finished
    sprite.play("idle")
```

## Texture Filtering
For pixel art: set each atlas texture to **Nearest** filtering in the Import dock.
For smooth sprites: use **Linear**.

## AnimatedSprite2D vs Sprite2D
The exporter uses `AnimatedSprite2D` for multi-frame animations.
For a static character with manual skeletal animation, use the `SpriteFrames` resource with individual `Sprite2D` nodes per layer.
