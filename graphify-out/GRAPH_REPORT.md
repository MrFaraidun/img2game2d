# Graph Report - 3d-model  (2026-09-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1831 nodes · 5898 edges · 53 communities (47 shown, 6 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 654 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- index-DASOYbuK.js
- index-vPSBVH-H.js
- index-BjO_mgfa.js
- types/index.ts
- n
- n
- r
- i
- hl
- i
- i
- viewer.js
- n
- np
- np
- hl
- hl
- fpsDefaults
- Pd
- Pd
- asset_ir/__init__.py
- qd
- types.ts
- ou
- ou
- package.json
- forge/cli.py
- rc
- transforms.py
- h
- xl
- xl
- xl
- validate_asset_ir
- SoundEngine
- compilerOptions
- validation.py
- qd
- qd
- pipeline.py
- compilerOptions
- export_spine.py
- generate_lighting_pack
- process_character
- versioning.py
- Yi
- extract_alpha_demat
- .oxlintrc.json
- tsconfig.json
- core/__init__.py
- tests/__init__.py
- charatcer 1.jpeg
- charatcer 2.jpeg

## God Nodes (most connected - your core abstractions)
1. `i()` - 79 edges
2. `i()` - 79 edges
3. `i()` - 74 edges
4. `n()` - 60 edges
5. `n()` - 60 edges
6. `n()` - 59 edges
7. `t()` - 54 edges
8. `t()` - 54 edges
9. `t()` - 51 edges
10. `hl()` - 42 edges

## Surprising Connections (you probably didn't know these)
- `cmd_convert()` --calls--> `convert_legacy_character_to_asset_ir()`  [EXTRACTED]
  forge/cli.py → core/asset_ir/converter.py
- `resolve_asset_ir()` --calls--> `convert_legacy_character_to_asset_ir()`  [EXTRACTED]
  forge/cli.py → core/asset_ir/converter.py
- `resolve_asset_ir()` --calls--> `deserialize_asset_ir()`  [EXTRACTED]
  forge/cli.py → core/asset_ir/schema.py
- `cmd_convert()` --calls--> `serialize_asset_ir()`  [EXTRACTED]
  forge/cli.py → core/asset_ir/schema.py
- `cmd_validate()` --calls--> `validate_asset_ir()`  [EXTRACTED]
  forge/cli.py → core/asset_ir/validation.py

## Import Cycles
- None detected.

## Communities (53 total, 6 thin omitted)

### Community 0 - "index-DASOYbuK.js"
Cohesion: 0.03
Nodes (103): a(), af(), ah(), ap(), Ar(), bh(), bn(), bu() (+95 more)

### Community 1 - "index-vPSBVH-H.js"
Cohesion: 0.03
Nodes (103): a(), af(), ah(), ap(), Ar(), bh(), bn(), bu() (+95 more)

### Community 2 - "index-BjO_mgfa.js"
Cohesion: 0.04
Nodes (76): ah(), ap(), Ar(), at(), Be(), bn(), bs(), bu() (+68 more)

### Community 3 - "types/index.ts"
Cohesion: 0.07
Nodes (66): lucide-react, react, App(), ExportsWorkstation(), ExportsWorkstationProps, Header(), HeaderProps, LightingWorkstation() (+58 more)

### Community 4 - "n"
Cohesion: 0.10
Nodes (66): aa(), b(), c(), ce(), de(), dn(), E(), ee() (+58 more)

### Community 5 - "n"
Cohesion: 0.10
Nodes (66): aa(), b(), c(), ce(), de(), dn(), E(), ee() (+58 more)

### Community 6 - "r"
Cohesion: 0.10
Nodes (62): ae(), am(), bm(), ce(), d(), E(), fh(), Gi() (+54 more)

### Community 7 - "i"
Cohesion: 0.06
Nodes (55): ao(), as(), au(), co(), Cp(), Da(), ds(), Du() (+47 more)

### Community 8 - "hl"
Cohesion: 0.08
Nodes (54): a(), al(), ba(), Bc(), Bi(), bo(), dl(), dm() (+46 more)

### Community 9 - "i"
Cohesion: 0.07
Nodes (52): ao(), as(), at(), Be(), bs(), bt(), cc(), cs() (+44 more)

### Community 10 - "i"
Cohesion: 0.07
Nodes (52): ao(), as(), at(), Be(), bs(), bt(), cc(), cs() (+44 more)

### Community 11 - "viewer.js"
Cohesion: 0.06
Nodes (51): actionButtonsContainer, btnAudioToggle, btnCloseModal, btnNextFrame, btnPlayPause, btnPrevFrame, canvas, canvasWrapper (+43 more)

### Community 12 - "n"
Cohesion: 0.07
Nodes (45): af(), an(), c(), cc(), cf(), dc(), df(), dn() (+37 more)

### Community 13 - "np"
Cohesion: 0.10
Nodes (35): am(), bm(), Bp(), cm(), em(), en(), fp(), jm() (+27 more)

### Community 14 - "np"
Cohesion: 0.10
Nodes (35): am(), bm(), Bp(), cm(), em(), en(), fp(), jm() (+27 more)

### Community 15 - "hl"
Cohesion: 0.11
Nodes (39): al(), Bc(), Bi(), bo(), dl(), Do(), dp(), el() (+31 more)

### Community 16 - "hl"
Cohesion: 0.11
Nodes (39): al(), Bc(), Bi(), bo(), dl(), Do(), dp(), el() (+31 more)

### Community 17 - "fpsDefaults"
Cohesion: 0.05
Nodes (38): animations, fpsDefaults, loopDefaults, atlas, maxHeight, maxWidth, padding, powerOfTwo (+30 more)

### Community 18 - "Pd"
Cohesion: 0.09
Nodes (38): ac(), ba(), co(), Ct(), dc(), dh(), fc(), gc() (+30 more)

### Community 19 - "Pd"
Cohesion: 0.09
Nodes (38): ac(), ba(), co(), Ct(), dc(), dh(), fc(), gc() (+30 more)

### Community 20 - "asset_ir/__init__.py"
Cohesion: 0.21
Nodes (31): convert_legacy_character_to_asset_ir(), AssetIR, Path, Converts legacy character metadata and TexturePacker atlases into canonical…, Ingests legacy character directory containing: - metadata/character.json -…, img2game2d Canonical AssetIR (Intermediate Representation) Package., deserialize_asset_ir(), AssetIR (+23 more)

### Community 21 - "qd"
Cohesion: 0.10
Nodes (36): Bd(), bh(), constructor(), cs(), ef(), Fd(), Gd(), gt() (+28 more)

### Community 22 - "types.ts"
Cohesion: 0.06
Nodes (22): Point2D, AnimationClipIR, AnimationCurveIR, AssetIR, AssetMetaIR, AtlasIR, BoneConstraintIR, BoneIR (+14 more)

### Community 23 - "ou"
Cohesion: 0.09
Nodes (35): au(), bl(), Cp(), Du(), eu(), Fu(), gm(), Hu() (+27 more)

### Community 24 - "ou"
Cohesion: 0.09
Nodes (35): au(), bl(), Cp(), Du(), eu(), Fu(), gm(), Hu() (+27 more)

### Community 25 - "package.json"
Cohesion: 0.06
Nodes (29): oxlint, react-dom, @types/node, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react (+21 more)

### Community 26 - "forge/cli.py"
Cohesion: 0.11
Nodes (24): Root CLI entrypoint for img2game2d., ProjectManifest, Path, Project Manifest management (*.img2game2d.json) for img2game2d projects., cmd_build(), cmd_convert(), cmd_dev(), cmd_inspect() (+16 more)

### Community 27 - "rc"
Cohesion: 0.10
Nodes (29): aa(), ac(), Ct(), dh(), Dt(), Es(), fc(), gc() (+21 more)

### Community 28 - "transforms.py"
Cohesion: 0.12
Nodes (21): canvas_to_spine(), canvas_to_uv(), canvas_to_world(), deg_to_rad(), normalize_angle_rad(), rad_to_deg(), Explicit coordinate transformations for img2game2d AssetIR. Maintains…, Converts radians to degrees. (+13 more)

### Community 29 - "h"
Cohesion: 0.13
Nodes (20): b(), Bp(), cm(), em(), en(), fp(), h(), Gp() (+12 more)

### Community 30 - "xl"
Cohesion: 0.12
Nodes (24): an(), ca(), cl(), ep(), fn(), Fo(), gl(), gn() (+16 more)

### Community 31 - "xl"
Cohesion: 0.12
Nodes (24): an(), ca(), cl(), ep(), fn(), Fo(), gl(), gn() (+16 more)

### Community 32 - "xl"
Cohesion: 0.12
Nodes (23): bl(), ca(), cl(), ep(), fn(), Fo(), gl(), gn() (+15 more)

### Community 33 - "validate_asset_ir"
Cohesion: 0.18
Nodes (11): asset_ir_to_dict(), Any, Serializes an AssetIR instance into a deterministic JSON string., Converts an AssetIR instance to a pure Python dictionary., serialize_asset_ir(), AssetIR, Runs all structural and semantic validators on an AssetIR document., validate_asset_ir() (+3 more)

### Community 35 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 36 - "validation.py"
Cohesion: 0.18
Nodes (16): DiagnosticIR, Any, Validation engine for img2game2d AssetIR. Produces structured, actionable…, Validates bone hierarchy, cycles, and parent references., Validates atlas dimensions, POT compliance, and frame rect overlaps., Validates vertex weight normalization sum(w) == 1.0 and triangle index…, Validates hitbox and collision bounds., Validates material maps and shader parameters. (+8 more)

### Community 37 - "qd"
Cohesion: 0.18
Nodes (18): ae(), Bd(), d(), ef(), Gd(), hf(), Hi(), io() (+10 more)

### Community 38 - "qd"
Cohesion: 0.18
Nodes (18): ae(), Bd(), d(), ef(), Gd(), hf(), Hi(), io() (+10 more)

### Community 39 - "pipeline.py"
Cohesion: 0.16
Nodes (17): export_godot(), export_phaser(), export_spine(), export_unity(), export_web_viewer(), generate_all_engine_exports(), generate_all_lighting_maps(), img2game2d Production Asset Pipeline & Multi-Character Exporter. Converts… (+9 more)

### Community 40 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 41 - "export_spine.py"
Cohesion: 0.17
Nodes (13): build_procedural_skeleton_rig(), export_character_to_spine(), main(), Any, Path, Spine 2D Exporter for img2game2d & Game Engines. Generates: 1. Official Spine…, Exports sprite atlases and animation manifests to official Spine 2D compatible…, Performs full export of character atlas to Spine 2D directory. (+5 more)

### Community 42 - "generate_lighting_pack"
Cohesion: 0.27
Nodes (10): compute_emission_map(), compute_normal_map(), generate_lighting_pack(), main(), Image, Path, Generates both normal and emission maps and writes them to output_dir., 2D Dynamic Lighting Map Generator for img2game2d & Game Engines. Generates: 1.… (+2 more)

### Community 43 - "process_character"
Cohesion: 0.31
Nodes (10): generate_strip_sheets(), pack_texture_atlas(), process_character(), Any, Path, Runs extraction, normalization, atlas packing, and metadata generation for a…, Packs raw frames into a Power-of-Two (POT) atlas with 2px bleeding padding., Generates standard horizontal sprite sheet strips for each individual animation. (+2 more)

### Community 44 - "versioning.py"
Cohesion: 0.25
Nodes (8): is_compatible(), migrate_to_v3(), parse_semver(), Any, Schema versioning and migration engine for img2game2d AssetIR., Parses SemVer string into (major, minor, patch) integer tuple., Checks if a schema version is compatible with current engine., Migrates a legacy or unversioned asset dictionary to canonical AssetIR v3.0.0…

### Community 45 - "Yi"
Cohesion: 0.28
Nodes (9): bt(), _f(), gf(), pf(), vf(), vt(), Yi(), yl() (+1 more)

### Community 46 - "extract_alpha_demat"
Cohesion: 0.29
Nodes (7): extract_alpha_demat(), Image, Localized unit test assertions for dematting functions., Zero-Halo Sub-Pixel Alpha De-Matting & Edge Defringing Engine. Complies with…, Extracts an RGBA image from an RGB array against a solid background color,…, run_unit_tests(), ndarray

### Community 47 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

## Knowledge Gaps
- **149 isolated node(s):** `Point2D`, `AnimationClipIR`, `AnimationCurveIR`, `AssetMetaIR`, `AtlasIR` (+144 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 308 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `go()` connect `r` to `index-BjO_mgfa.js`, `n`, `h`, `i`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **Why does `fp()` connect `np` to `index-DASOYbuK.js`, `n`, `xl`, `hl`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **Why does `validate_asset_ir()` connect `validate_asset_ir` to `forge/cli.py`, `asset_ir/__init__.py`, `validation.py`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `i()` (e.g. with `au()` and `b()`) actually correct?**
  _`i()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `i()` (e.g. with `au()` and `b()`) actually correct?**
  _`i()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `i()` (e.g. with `au()` and `b()`) actually correct?**
  _`i()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `n()` (e.g. with `bs()` and `c()`) actually correct?**
  _`n()` has 37 INFERRED edges - model-reasoned connections that need verification._