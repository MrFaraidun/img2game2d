#!/usr/bin/env python3
"""
img2game2d test suite.
Tests schemas, intake scripts, atlas packer, exporters, and end-to-end pipeline.

Run:
    cd /home/faraidun/.gemini/config/skills/img2game2d
    python3 -m pytest forge/tests/ -v
"""
import json
import os
import sys
import tempfile
from pathlib import Path

from contextlib import contextmanager

try:
    import pytest
except ImportError:
    class _PytestShim:
        @staticmethod
        def fixture(*args, **kwargs):
            return lambda f: f
        @staticmethod
        def skip(msg=""):
            pass
        @staticmethod
        @contextmanager
        def raises(expected):
            try:
                yield
            except expected:
                return
            except Exception as e:
                raise AssertionError(f"Expected {expected.__name__}, got {type(e).__name__}: {e}")
            raise AssertionError(f"Expected {expected.__name__} but nothing was raised")
    pytest = _PytestShim()

# Add forge to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def test_image():
    """Create a minimal valid RGBA test image."""
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        pytest.skip("Pillow/NumPy not installed")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img_path = f.name

    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    arr = np.array(img)
    # Draw simple character silhouette
    import math
    for y in range(256):
        for x in range(256):
            if ((x - 128) ** 2 + (y - 64) ** 2) < 35 ** 2:  # head
                arr[y, x] = [200, 150, 100, 255]
            elif ((x - 128) ** 2 / 50 ** 2 + (y - 150) ** 2 / 80 ** 2) < 1:  # torso
                arr[y, x] = [100, 100, 200, 255]

    from PIL import Image as PILImage
    PILImage.fromarray(arr).save(img_path, "PNG")
    yield img_path
    os.unlink(img_path)


@pytest.fixture(scope="session")
def minimal_analysis():
    return {
        "asset_id": "test_char",
        "name": "Test Character",
        "asset_type": "character",
        "character_type": "humanoid",
        "source_image": "source/original.png",
        "views_detected": ["front"],
        "resolution": {"width": 256, "height": 256},
        "bounding_box": {"x": 0, "y": 0, "width": 256, "height": 256},
        "parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"],
        "colors": [{"hex": "#c89664", "role": "skin"}, {"hex": "#6464c8", "role": "armor"}],
        "symmetry": "symmetric",
        "animations": ["idle", "walk"],
    }


# ── Schema tests ──────────────────────────────────────────────────────────────


class TestSchemas:
    def test_asset_schema_loads(self):
        from _shared.schema_utils import load_schema
        schema = load_schema("asset")
        assert schema["title"] == "Asset"
        assert "required" in schema

    def test_layer_schema_loads(self):
        from _shared.schema_utils import load_schema
        schema = load_schema("layer")
        assert schema["title"] == "Layer"

    def test_rig_schema_loads(self):
        from _shared.schema_utils import load_schema
        schema = load_schema("rig")
        assert schema["title"] == "Rig"

    def test_animation_schema_loads(self):
        from _shared.schema_utils import load_schema
        schema = load_schema("animation")
        assert schema["title"] == "Animation"

    def test_project_schema_loads(self):
        from _shared.schema_utils import load_schema
        schema = load_schema("project")
        assert schema["title"] == "Project"

    def test_valid_animation_passes(self):
        from _shared.schema_utils import validate
        anim = {"name": "idle", "fps": 8, "loop": True, "frames": ["000.png", "001.png"], "frame_count": 2}
        errors = validate(anim, "animation")
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_invalid_animation_fails(self):
        from _shared.schema_utils import validate
        anim = {"name": "idle"}  # Missing required fields
        errors = validate(anim, "animation")
        assert len(errors) > 0

    def test_valid_layer_passes(self):
        from _shared.schema_utils import validate
        layer = {
            "id": "head", "name": "Head", "type": "head",
            "z_index": 20, "pivot": {"x": 0.5, "y": 1.0},
        }
        errors = validate(layer, "layer")
        assert errors == [], f"Unexpected errors: {errors}"


# ── Intake tests ──────────────────────────────────────────────────────────────


class TestIntake:
    def test_probe_image(self, test_image):
        from stage1_intake.probe_image import probe
        result = probe(test_image)
        assert result["width"] == 256
        assert result["height"] == 256
        assert result["has_alpha"] is True
        assert result["suitable"] is True

    def test_probe_missing_image(self):
        from stage1_intake.probe_image import probe
        with pytest.raises(FileNotFoundError):
            probe("/nonexistent/image.png")

    def test_detect_style(self, test_image):
        from stage1_intake.detect_style import detect_style
        result = detect_style(test_image)
        assert "detected_style" in result
        assert "confidence" in result
        assert result["detected_style"] in [
            "pixel_art", "hand_drawn", "anime", "cartoon", "comic",
            "vector", "painted", "3d_rendered", "low_poly", "stylized", "realistic"
        ]
        assert 0.0 <= result["confidence"] <= 1.0

    def test_detect_views_single(self, test_image):
        from stage1_intake.detect_views import detect_views
        result = detect_views(test_image)
        assert result["view_count"] >= 1
        assert len(result["views"]) >= 1
        assert "label" in result["views"][0]
        # Should detect as single view (character on transparent bg)
        assert not result["multi_view"]

    def test_remove_background_existing_alpha(self, test_image):
        from stage1_intake.remove_background import remove_background
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            out = f.name
        try:
            result = remove_background(test_image, out, method="existing_alpha")
            assert result["method_used"] == "existing_alpha"
            assert Path(out).exists()
        finally:
            if Path(out).exists():
                os.unlink(out)


# ── Spec tests ────────────────────────────────────────────────────────────────


class TestSpec:
    def test_new_asset_spec(self, minimal_analysis, tmp_path):
        from stage2_spec.new_asset_spec import build_asset_spec
        spec = build_asset_spec(minimal_analysis)
        assert spec["asset_id"] == "test_char"
        assert spec["asset_type"] == "character"
        assert len(spec["layers"]) == 6
        assert "idle" in spec["animations"]
        assert "walk" in spec["animations"]

    def test_validate_asset_spec_valid(self, minimal_analysis, tmp_path):
        from stage2_spec.new_asset_spec import build_asset_spec
        from stage2_spec.validate_asset_spec import validate_asset
        spec = build_asset_spec(minimal_analysis)
        spec_path = tmp_path / "asset.json"
        spec_path.write_text(json.dumps(spec))
        passed, errors = validate_asset(str(spec_path))
        assert passed, f"Validation errors: {errors}"

    def test_layer_decompose(self, minimal_analysis, tmp_path):
        from stage2_spec.new_asset_spec import build_asset_spec
        from stage2_spec.layer_decompose import decompose_layers
        spec = build_asset_spec(minimal_analysis)
        layer_spec = decompose_layers(spec)
        assert layer_spec["layer_count"] == 6
        assert "head" in layer_spec["layers"]
        assert len(layer_spec["depth_order"]) == 6

    def test_build_rig(self, minimal_analysis, tmp_path):
        from stage2_spec.new_asset_spec import build_asset_spec
        from stage2_spec.layer_decompose import decompose_layers
        from stage2_spec.build_rig import build_rig
        from _shared.schema_utils import validate

        spec = build_asset_spec(minimal_analysis)
        layer_spec = decompose_layers(spec)
        rig = build_rig(layer_spec)

        assert rig["bone_count"] >= 6
        errors = validate(rig, "rig")
        assert errors == [], f"Rig schema errors: {errors}"


# ── Atlas tests ───────────────────────────────────────────────────────────────


class TestAtlas:
    def test_pack_atlas(self, test_image, tmp_path):
        from stage3_build.generate_frames import generate_animation_frames
        from stage5_atlas.pack_atlas import pack_atlas
        from _shared.schema_utils import load_json

        # Generate stub frames first
        anim_dir = tmp_path / "animations"
        spec = {"asset_id": "test", "name": "Test", "animations": {"idle": {"fps": 8, "loop": True}}, "colors": []}
        results = generate_animation_frames(test_image, spec, ["idle"], str(anim_dir), "stub")
        assert "idle" in results

        # Pack atlas
        out_dir = tmp_path / "atlases"
        atlas_results = pack_atlas(str(anim_dir), str(out_dir), padding=2, power_of_two=True)
        assert "idle" in atlas_results
        assert Path(atlas_results["idle"]["atlas_path"]).exists()
        assert Path(atlas_results["idle"]["json_path"]).exists()

        # Validate atlas JSON
        atlas_data = load_json(atlas_results["idle"]["json_path"])
        assert "meta" in atlas_data
        assert "frames" in atlas_data
        assert len(atlas_data["frames"]) == 4  # stub generates 4 idle frames

    def test_atlas_power_of_two(self, test_image, tmp_path):
        from stage3_build.generate_frames import generate_animation_frames
        from stage5_atlas.pack_atlas import pack_atlas
        import math

        anim_dir = tmp_path / "animations"
        spec = {"asset_id": "test", "name": "Test", "animations": {"idle": {"fps": 8, "loop": True}}, "colors": []}
        generate_animation_frames(test_image, spec, ["idle"], str(anim_dir), "stub")
        out_dir = tmp_path / "atlases"
        pack_atlas(str(anim_dir), str(out_dir), padding=2, power_of_two=True)

        from _shared.schema_utils import load_json
        summary = load_json(str(out_dir / "atlas_summary.json"))
        w, h = summary["idle"]["atlas_size"]
        # Both dimensions should be power of 2
        assert w == 2 ** math.ceil(math.log2(w))
        assert h == 2 ** math.ceil(math.log2(h))


# ── Exporter tests ────────────────────────────────────────────────────────────


class TestExporters:
    @pytest.fixture
    def populated_asset(self, minimal_analysis):
        from stage2_spec.new_asset_spec import build_asset_spec
        return build_asset_spec(minimal_analysis)

    @pytest.fixture
    def populated_atlases(self, test_image, tmp_path, populated_asset):
        from stage3_build.generate_frames import generate_animation_frames
        from stage5_atlas.pack_atlas import pack_atlas

        anim_dir = tmp_path / "animations"
        generate_animation_frames(test_image, populated_asset, ["idle", "walk"], str(anim_dir), "stub")
        out_dir = tmp_path / "atlases"
        pack_atlas(str(anim_dir), str(out_dir), padding=2, power_of_two=True)
        return str(out_dir)

    def test_godot_exporter(self, populated_asset, populated_atlases, tmp_path):
        from stage6_export.godot_exporter import GodotExporter
        out = tmp_path / "godot"
        result = GodotExporter().export(populated_asset, populated_atlases, str(out))
        assert Path(result["scene"]).exists()
        assert Path(result["sprite_frames"]).exists()
        tscn = Path(result["scene"]).read_text()
        assert "AnimatedSprite2D" in tscn
        assert "SpriteFrames" in tscn

    def test_unity_exporter(self, populated_asset, populated_atlases, tmp_path):
        from stage6_export.unity_exporter import UnityExporter
        out = tmp_path / "unity"
        result = UnityExporter().export(populated_asset, populated_atlases, str(out))
        assert Path(result["atlas_json"]).exists()
        assert Path(result["animator"]).exists()
        data = json.loads(Path(result["atlas_json"]).read_text())
        assert "animations" in data

    def test_phaser_exporter(self, populated_asset, populated_atlases, tmp_path):
        from stage6_export.phaser_exporter import PhaserExporter
        out = tmp_path / "phaser"
        result = PhaserExporter().export(populated_asset, populated_atlases, str(out))
        assert Path(result["atlas_json"]).exists()
        assert Path(result["typescript"]).exists()
        ts = Path(result["typescript"]).read_text()
        assert "preload" in ts
        assert "animations" in ts.lower() or "ANIMATIONS" in ts

    def test_pixijs_exporter(self, populated_asset, populated_atlases, tmp_path):
        from stage6_export.pixijs_exporter import PixiJSExporter
        out = tmp_path / "pixijs"
        result = PixiJSExporter().export(populated_asset, populated_atlases, str(out))
        assert Path(result["typescript"]).exists()
        ts = Path(result["typescript"]).read_text()
        assert "AnimatedSprite" in ts
        assert result["clip_count"] >= 1


# ── Cache tests ───────────────────────────────────────────────────────────────


class TestCache:
    def test_cache_hit_miss(self, test_image, tmp_path):
        from _shared.cache import Cache
        cache = Cache(str(tmp_path / "cache"))
        h = cache.file_hash(test_image)
        assert not cache.is_cached("test.step", h)
        # Use the real test_image path so file-existence check passes
        cache.record("test.step", h, [test_image])
        assert cache.is_cached("test.step", h)

    def test_cache_invalidate(self, test_image, tmp_path):
        from _shared.cache import Cache
        cache = Cache(str(tmp_path / "cache"))
        h = cache.file_hash(test_image)
        cache.record("test.step", h, [test_image])
        assert cache.is_cached("test.step", h)
        cache.invalidate("test.step")
        assert not cache.is_cached("test.step", h)


class TestV110Enhancements:
    def test_defringe_alpha(self):
        from _shared.image_utils import defringe_alpha
        from PIL import Image
        import numpy as np
        # Create an image with a white fringe at the boundary
        img = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
        arr = np.array(img)
        # Inner solid circle (dark tone)
        arr[15:35, 15:35] = [20, 20, 30, 255]
        # Outer fringe boundary (semi-transparent white)
        arr[10:15, 10:40] = [250, 250, 250, 120]
        test_img = Image.fromarray(arr)
        cleaned = defringe_alpha(test_img)
        cleaned_arr = np.array(cleaned)
        # The white fringe pixels should be shifted away from pure white
        fringe_r = cleaned_arr[12, 25, 0]
        assert fringe_r < 100, f"Expected fringe R to be tone-shifted, got {fringe_r}"

    def test_enhance_image(self, test_image):
        from _shared.image_utils import enhance_image, load_image
        img = load_image(test_image)
        enhanced = enhance_image(img, scale=2.0, clarity_strength=1.2)
        assert enhanced.width == img.width * 2
        assert enhanced.height == img.height * 2

    def test_inverse_affine_math(self):
        from _shared.transforms import get_inverse_affine_matrix
        import math
        matrix = get_inverse_affine_matrix(cx=25.0, cy=25.0, angle_rad=math.pi / 2, dx=10.0, dy=0.0)
        assert len(matrix) == 6
        # Test identity transform produces identity diagonal
        id_matrix = get_inverse_affine_matrix(cx=25.0, cy=25.0, angle_rad=0.0, dx=0.0, dy=0.0, sx=1.0, sy=1.0)
        assert round(id_matrix[0], 2) == 1.0
        assert round(id_matrix[4], 2) == 1.0

    def test_continuous_shear(self, test_image):
        from _shared.transforms import apply_continuous_shear
        from PIL import Image
        img = Image.open(test_image).convert("RGBA")
        sheared = apply_continuous_shear(img, hip_y=img.height * 0.5, stride_pixels=15.0)
        assert sheared.size == img.size

    def test_procedural_animator(self, test_image, tmp_path):
        from stage3_build.procedural_animator import ProceduralAnimator
        animator = ProceduralAnimator(test_image)
        results = animator.build_all(["idle", "attack"], str(tmp_path / "anims"))
        assert "idle" in results
        assert "attack" in results
        assert len(results["idle"]) > 0
        assert len(results["attack"]) > 0
        for p in results["attack"]:
            assert Path(p).exists()

    def test_viewer_exporter(self, populated_asset, tmp_path, test_image):
        from stage3_build.procedural_animator import ProceduralAnimator
        from stage6_export.viewer_exporter import export_viewer
        import json
        animator = ProceduralAnimator(test_image)
        anim_dir = tmp_path / "animations"
        animator.build_all(["idle", "attack"], str(anim_dir))
        viewer_dir = tmp_path / "viewer"
        asset_file = tmp_path / "asset.json"
        asset_file.write_text(json.dumps(populated_asset), encoding="utf-8")
        res = export_viewer(str(asset_file), str(anim_dir), str(viewer_dir))
        assert Path(res["viewer_html"]).exists()
        assert Path(res["viewer_css"]).exists()
        assert Path(res["viewer_js"]).exists()

    def test_assess_quality(self, test_image):
        from stage1_intake.assess_quality import assess_image_quality
        res = assess_image_quality(test_image)
        assert "quality_score" in res
        assert "verdict" in res
        assert "suggested_prompt" in res
        assert "positive" in res["suggested_prompt"]
        assert "midjourney" in res["suggested_prompt"]


if __name__ == "__main__":
    print("Running img2game2d test suite (standalone mode)...")
    import inspect
    import shutil

    # Setup shared session fixtures
    img_gen = test_image()
    t_img = next(img_gen)
    m_analysis = minimal_analysis()

    test_classes = [
        TestSchemas(),
        TestIntake(),
        TestSpec(),
        TestAtlas(),
        TestExporters(),
        TestCache(),
        TestV110Enhancements(),
    ]

    total_run = 0
    total_passed = 0
    total_failed = 0

    for tc in test_classes:
        class_name = tc.__class__.__name__
        print(f"\n── {class_name} ──")
        methods = [m for m in dir(tc) if m.startswith("test_")]
        for m_name in methods:
            func = getattr(tc, m_name)
            sig = inspect.signature(func)
            kwargs = {}
            temp_dir = tempfile.mkdtemp(prefix="test_img2game2d_")
            tmp_p = Path(temp_dir)
            try:
                if "test_image" in sig.parameters:
                    kwargs["test_image"] = t_img
                if "minimal_analysis" in sig.parameters:
                    kwargs["minimal_analysis"] = m_analysis
                if "tmp_path" in sig.parameters:
                    kwargs["tmp_path"] = tmp_p
                if "populated_asset" in sig.parameters:
                    from stage2_spec.new_asset_spec import build_asset_spec
                    kwargs["populated_asset"] = build_asset_spec(m_analysis)
                if "populated_atlases" in sig.parameters:
                    from stage2_spec.new_asset_spec import build_asset_spec
                    from stage3_build.generate_frames import generate_animation_frames
                    from stage5_atlas.pack_atlas import pack_atlas
                    pa = build_asset_spec(m_analysis)
                    anim_dir = tmp_p / "animations"
                    generate_animation_frames(t_img, pa, ["idle", "walk"], str(anim_dir), "stub")
                    out_dir = tmp_p / "atlases"
                    pack_atlas(str(anim_dir), str(out_dir), padding=2, power_of_two=True)
                    kwargs["populated_atlases"] = str(out_dir)

                func(**kwargs)
                total_passed += 1
                print(f"  ✓ {m_name}")
            except Exception as e:
                total_failed += 1
                import traceback
                print(f"  ✗ {m_name}: {e}\n{traceback.format_exc()}")
            finally:
                total_run += 1
                shutil.rmtree(temp_dir, ignore_errors=True)

    try:
        next(img_gen)
    except StopIteration:
        pass

    print(f"\n{'='*40}")
    print(f"Results: {total_passed}/{total_run} passed ({total_failed} failed)")
    print(f"{'='*40}")
    sys.exit(1 if total_failed > 0 else 0)

