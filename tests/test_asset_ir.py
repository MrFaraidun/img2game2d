"""
Unit tests for canonical AssetIR serialization, deserialization, and validation.
"""
import unittest
from core.asset_ir import (
    AnimationClipIR,
    AssetIR,
    AssetMetaIR,
    AtlasIR,
    BoneIR,
    BoneRestIR,
    CanvasMetaIR,
    ColliderIR,
    DiagnosticIR,
    FrameIR,
    MaterialIR,
    MeshIR,
    SkeletonIR,
    SourceMetaIR,
    VertexWeightIR,
    deserialize_asset_ir,
    serialize_asset_ir,
    validate_asset_ir,
)


class TestAssetIR(unittest.TestCase):
    def setUp(self):
        self.canvas = CanvasMetaIR(width=576, height=512, pivot_x=288, ground_y=460)
        self.source = SourceMetaIR(width=576, height=512)
        self.asset_meta = AssetMetaIR(id="test_hero", name="Test Hero", source_hash="abc123hash")
        self.frames = [
            FrameIR(
                id="test_hero_idle_00",
                animation="idle",
                index=0,
                duration_ms=166,
                canvas_rect={"x": 188, "y": 160, "w": 200, "h": 300},
                atlas_rect={"x": 2, "y": 2, "w": 200, "h": 300},
                uv_rect={"u0": 0.001, "v0": 0.001, "u1": 0.1, "v1": 0.15},
                pivot={"x": 0.5, "y": 0.9},
                ground_anchor=True,
                delta_y=0,
            )
        ]
        self.anims = [
            AnimationClipIR(
                id="test_hero_idle",
                name="idle",
                fps=6,
                loop=True,
                frame_ids=["test_hero_idle_00"],
            )
        ]
        self.skeleton = SkeletonIR(
            root_bone_id="root",
            bones=[
                BoneIR(
                    id="root",
                    name="root",
                    parent_id=None,
                    length=0.0,
                    rest=BoneRestIR(x=0.0, y=0.0, rotation_rad=0.0),
                ),
                BoneIR(
                    id="pelvis",
                    name="pelvis",
                    parent_id="root",
                    length=50.0,
                    rest=BoneRestIR(x=0.0, y=100.0, rotation_rad=1.57),
                ),
            ],
        )

    def test_round_trip_serialization(self):
        asset = AssetIR(
            schema_version="3.0.0",
            asset=self.asset_meta,
            source=self.source,
            canvas=self.canvas,
            frames=self.frames,
            animations=self.anims,
            skeleton=self.skeleton,
        )
        json_str = serialize_asset_ir(asset)
        restored = deserialize_asset_ir(json_str)

        self.assertEqual(restored.schema_version, asset.schema_version)
        self.assertEqual(restored.asset.id, asset.asset.id)
        self.assertEqual(restored.canvas.width, 576)
        self.assertEqual(len(restored.frames), 1)
        self.assertEqual(restored.frames[0].id, "test_hero_idle_00")
        self.assertEqual(len(restored.animations), 1)
        self.assertIsNotNone(restored.skeleton)
        self.assertEqual(len(restored.skeleton.bones), 2)

    def test_valid_asset_passes_validation(self):
        asset = AssetIR(
            schema_version="3.0.0",
            asset=self.asset_meta,
            source=self.source,
            canvas=self.canvas,
            frames=self.frames,
            animations=self.anims,
            skeleton=self.skeleton,
        )
        diagnostics = validate_asset_ir(asset)
        errors = [d for d in diagnostics if d.severity == "error"]
        self.assertEqual(len(errors), 0, f"Unexpected validation errors: {errors}")

    def test_empty_frame_diagnostic(self):
        broken_frame = FrameIR(
            id="broken_f",
            animation="idle",
            index=1,
            duration_ms=100,
            canvas_rect={"x": 0, "y": 0, "w": 0, "h": 0},  # Empty!
        )
        asset = AssetIR(
            schema_version="3.0.0",
            asset=self.asset_meta,
            source=self.source,
            canvas=self.canvas,
            frames=[broken_frame],
            animations=[
                AnimationClipIR(id="anim_1", name="idle", fps=10, loop=True, frame_ids=["broken_f"])
            ],
        )
        diagnostics = validate_asset_ir(asset)
        codes = [d.code for d in diagnostics]
        self.assertIn("EMPTY_FRAME", codes)

    def test_uv_out_of_range_diagnostic(self):
        frame = FrameIR(
            id="uv_err_f",
            animation="idle",
            index=0,
            duration_ms=100,
            canvas_rect={"x": 10, "y": 10, "w": 50, "h": 50},
            uv_rect={"u0": -0.2, "v0": 0.0, "u1": 1.5, "v1": 1.0},  # Out of range!
        )
        asset = AssetIR(
            schema_version="3.0.0",
            asset=self.asset_meta,
            source=self.source,
            canvas=self.canvas,
            frames=[frame],
            animations=[
                AnimationClipIR(id="a", name="idle", fps=10, loop=True, frame_ids=["uv_err_f"])
            ],
        )
        diagnostics = validate_asset_ir(asset)
        codes = [d.code for d in diagnostics]
        self.assertIn("UV_OUT_OF_RANGE", codes)

    def test_missing_parent_bone_diagnostic(self):
        broken_skeleton = SkeletonIR(
            root_bone_id="root",
            bones=[
                BoneIR(
                    id="root",
                    name="root",
                    parent_id=None,
                    length=0.0,
                    rest=BoneRestIR(x=0.0, y=0.0),
                ),
                BoneIR(
                    id="arm",
                    name="arm",
                    parent_id="non_existent_chest",  # Missing parent!
                    length=30.0,
                    rest=BoneRestIR(x=0.0, y=50.0),
                ),
            ],
        )
        asset = AssetIR(
            schema_version="3.0.0",
            asset=self.asset_meta,
            source=self.source,
            canvas=self.canvas,
            frames=self.frames,
            animations=self.anims,
            skeleton=broken_skeleton,
        )
        diagnostics = validate_asset_ir(asset)
        codes = [d.code for d in diagnostics]
        self.assertIn("MISSING_PARENT_BONE", codes)

    def test_bone_cycle_diagnostic(self):
        # A -> B -> A cycle
        cyclic_skeleton = SkeletonIR(
            root_bone_id="bone_a",
            bones=[
                BoneIR(id="bone_a", name="A", parent_id="bone_b", length=10.0, rest=BoneRestIR(x=0, y=0)),
                BoneIR(id="bone_b", name="B", parent_id="bone_a", length=10.0, rest=BoneRestIR(x=0, y=0)),
            ],
        )
        asset = AssetIR(
            schema_version="3.0.0",
            asset=self.asset_meta,
            source=self.source,
            canvas=self.canvas,
            frames=self.frames,
            animations=self.anims,
            skeleton=cyclic_skeleton,
        )
        diagnostics = validate_asset_ir(asset)
        codes = [d.code for d in diagnostics]
        self.assertIn("BONE_CYCLE_DETECTED", codes)

    def test_mesh_weight_sum_diagnostic(self):
        broken_mesh = MeshIR(
            id="mesh_1",
            layer_id="body",
            vertices=[0.0, 0.0, 10.0, 0.0, 10.0, 10.0],
            triangles=[0, 1, 2],
            uvs=[0.0, 0.0, 1.0, 0.0, 1.0, 1.0],
            weights=[
                [VertexWeightIR(bone_id="root", weight=0.5)],  # Sums to 0.5, invalid!
                [VertexWeightIR(bone_id="root", weight=1.0)],
                [VertexWeightIR(bone_id="root", weight=1.0)],
            ],
        )
        asset = AssetIR(
            schema_version="3.0.0",
            asset=self.asset_meta,
            source=self.source,
            canvas=self.canvas,
            frames=self.frames,
            animations=self.anims,
            skeleton=self.skeleton,
            meshes=[broken_mesh],
        )
        diagnostics = validate_asset_ir(asset)
        codes = [d.code for d in diagnostics]
        self.assertIn("WEIGHT_SUM_INVALID", codes)


if __name__ == "__main__":
    unittest.main()
