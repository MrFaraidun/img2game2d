"""
Unit tests for legacy metadata conversion to canonical AssetIR and project manifest.
"""
import tempfile
import unittest
from pathlib import Path

from core.asset_ir import (
    ProjectManifest,
    convert_legacy_character_to_asset_ir,
    deserialize_asset_ir,
    serialize_asset_ir,
    validate_asset_ir,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestConverter(unittest.TestCase):
    def test_convert_the_architect(self):
        char_dir = PROJECT_ROOT / "characters" / "the_architect"
        self.assertTrue(char_dir.is_dir(), f"Missing character directory: {char_dir}")

        asset = convert_legacy_character_to_asset_ir(char_dir, project_root=PROJECT_ROOT)
        self.assertEqual(asset.asset.id, "the_architect")
        self.assertEqual(asset.canvas.width, 576)
        self.assertEqual(asset.canvas.height, 512)
        self.assertEqual(asset.canvas.pivot_x, 288)
        self.assertEqual(asset.canvas.ground_y, 460)

        self.assertEqual(len(asset.frames), 24)
        self.assertEqual(len(asset.animations), 5)

        # Validate with zero structural errors
        diagnostics = validate_asset_ir(asset)
        errors = [d for d in diagnostics if d.severity == "error"]
        self.assertEqual(len(errors), 0, f"Converted asset has errors: {errors}")

        # Test JSON round-trip
        json_str = serialize_asset_ir(asset)
        restored = deserialize_asset_ir(json_str)
        self.assertEqual(restored.asset.id, "the_architect")
        self.assertEqual(len(restored.frames), 24)

    def test_convert_the_guardian(self):
        char_dir = PROJECT_ROOT / "characters" / "the_guardian"
        self.assertTrue(char_dir.is_dir(), f"Missing character directory: {char_dir}")

        asset = convert_legacy_character_to_asset_ir(char_dir, project_root=PROJECT_ROOT)
        self.assertEqual(asset.asset.id, "the_guardian")
        self.assertEqual(len(asset.frames), 24)
        self.assertEqual(len(asset.animations), 6)

        diagnostics = validate_asset_ir(asset)
        errors = [d for d in diagnostics if d.severity == "error"]
        self.assertEqual(len(errors), 0, f"Converted asset has errors: {errors}")

    def test_project_manifest_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "knight.img2game2d.json"
            manifest = ProjectManifest(
                name="Knight",
                source="source/knight.png",
                asset_ir="knight.assetir.json",
                animations={"idle": "anims/idle.json", "run": "anims/run.json"},
            )
            manifest.save(manifest_path)
            self.assertTrue(manifest_path.exists())

            loaded = ProjectManifest.load(manifest_path)
            self.assertEqual(loaded.name, "Knight")
            self.assertEqual(loaded.source, "source/knight.png")
            self.assertEqual(loaded.animations["idle"], "anims/idle.json")


if __name__ == "__main__":
    unittest.main()
