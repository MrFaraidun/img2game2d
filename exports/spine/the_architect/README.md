# the_architect — Spine 2D Asset Package

Exported with **img2game2d** Spine 2D Exporter.

## Included Files
- `the_architect_skeleton.json` — Official Spine 2D skeleton, 19 articulated bones, slot attachments & frame timelines.
- `the_architect.atlas` — LibGDX/Spine texture atlas mapping.
- `the_architect_atlas.png` — Main RGBA diffuse texture.
- `the_architect_atlas_normal.png` — Tangent-space normal map for dynamic 2D lights.
- `the_architect_atlas_emission.png` — Emission/glow map for post-processing bloom.

## How to Import
### Unity (`spine-unity`)
1. Ensure the `spine-unity` runtime package is installed in your Unity project.
2. Drag `the_architect_skeleton.json`, `the_architect.atlas`, and `the_architect_atlas.png` into any folder in `Assets/`.
3. Unity will automatically generate a `SkeletonDataAsset`.
4. Drag the `SkeletonDataAsset` into your scene or hierarchy to create a `SkeletonAnimation` Game Object.

### Godot 4 (`spine-godot`)
1. Ensure the `spine-godot` GDExtension or custom engine build is loaded.
2. Place `the_architect_skeleton.json` and `the_architect.atlas` into `res://assets/`.
3. Create a `SpineSprite` node and assign the `SpineSkeletonDataResource`.

### Unreal Engine (`spine-ue4`)
1. Import the `.json` and `.atlas` files into the Content Browser.
2. Assign the generated Spine Skeleton Component to your 2D Paper/Pawn Actor.
