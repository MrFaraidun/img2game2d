# Rig Contract

## When to read this
Read at Stage 2 (Spec) before building or editing `rig.json`.

---

## What is the Rig?
The **rig** is a hierarchical bone structure that maps to the layer tree. Each bone:
- Corresponds to one layer
- Has a parent (except the root)
- Has a pivot point (world-space pixel coordinate)
- Has rotation constraints
- Controls which layers it drives

The rig enables skeletal animation: rotating a bone moves all child bones with it.

---

## Bone Naming Convention
```
bone_<layer_id>
```
Examples: `bone_head`, `bone_left_arm`, `bone_torso`

The root bone is either `bone_torso` or a virtual `bone_root`.

---

## Bone Hierarchy

Standard humanoid rig hierarchy:
```
bone_root
  └── bone_torso
        ├── bone_head
        │     ├── bone_hair
        │     ├── bone_mask
        │     └── bone_eyes
        ├── bone_neck
        ├── bone_left_arm
        │     └── bone_left_forearm
        │           └── bone_left_hand
        ├── bone_right_arm
        │     └── bone_right_forearm
        │           └── bone_right_hand
        ├── bone_left_leg
        │     └── bone_left_lower_leg
        │           └── bone_left_foot
        ├── bone_right_leg
        │     └── bone_right_lower_leg
        │           └── bone_right_foot
        ├── bone_cloak
        └── bone_weapon
```

---

## Rotation Constraints

| Bone | Min (°) | Max (°) | Notes |
|------|---------|---------|-------|
| head | -45 | +45 | Side-to-side |
| arm | -180 | +180 | Full rotation |
| forearm | -135 | 0 | Elbow only bends one way |
| hand | -45 | +45 | Wrist flex |
| leg | -45 | +90 | Forward/back |
| lower_leg | -120 | 0 | Knee only bends backward |
| foot | -45 | +60 | Ankle flex |
| tail | -60 | +60 | Side sway |
| cloak | -20 | +20 | Wind effect range |

---

## Bone Length
Bone length is used for IK (inverse kinematics) calculations.
For 2D sprites it's usually the height of the bounding box.

---

## Rig Validation Checklist
Before marking Stage 2 rig complete:
- [ ] All layers have a corresponding bone
- [ ] No cycles in parent chain
- [ ] Root bone identified (no parent or parent = null)
- [ ] All pivots are in pixel coordinates (not normalized)
- [ ] Rotation constraints make anatomical sense
- [ ] `bone_count` matches `layer_count` in layer-spec.json

---

## Using the Rig Builder
```bash
python3 forge/stage2_spec/build_rig.py layers/layer-spec.json --out metadata/rig.json
```
Then validate: `python3 forge/stage2_spec/validate_asset_spec.py metadata/rig.json`
(validate with rig schema — or run `python3 -c "from forge._shared.schema_utils import validate; ..."`)
