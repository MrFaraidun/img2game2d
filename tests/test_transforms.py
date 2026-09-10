"""
Unit tests for coordinate transformations in AssetIR.
"""
import math
import unittest
from core.asset_ir.transforms import (
    canvas_to_spine,
    canvas_to_uv,
    canvas_to_world,
    deg_to_rad,
    normalize_angle_rad,
    rad_to_deg,
    spine_to_canvas,
    uv_to_canvas,
    world_to_canvas,
)


class TestTransforms(unittest.TestCase):
    def setUp(self):
        self.canvas_h = 512.0
        self.ground_y = 460.0
        self.pivot_x = 288.0

    def test_canvas_to_world_round_trip(self):
        test_points = [
            (288.0, 460.0),  # Ground anchor (should map to 0, 0 in world)
            (0.0, 0.0),      # Top-left
            (576.0, 512.0),  # Bottom-right
            (200.0, 350.0),
        ]
        for cx, cy in test_points:
            wx, wy = canvas_to_world(cx, cy, self.canvas_h, self.ground_y, self.pivot_x)
            rcx, rcy = world_to_canvas(wx, wy, self.canvas_h, self.ground_y, self.pivot_x)
            self.assertAlmostEqual(cx, rcx, places=6)
            self.assertAlmostEqual(cy, rcy, places=6)

    def test_ground_anchor_world_zero(self):
        wx, wy = canvas_to_world(288.0, 460.0, self.canvas_h, self.ground_y, self.pivot_x)
        self.assertAlmostEqual(wx, 0.0, places=6)
        self.assertAlmostEqual(wy, 0.0, places=6)

    def test_canvas_to_spine_round_trip(self):
        test_points = [(288.0, 460.0), (100.0, 200.0), (450.0, 490.0)]
        for cx, cy in test_points:
            sx, sy = canvas_to_spine(cx, cy, self.ground_y, self.pivot_x)
            rcx, rcy = spine_to_canvas(sx, sy, self.ground_y, self.pivot_x)
            self.assertAlmostEqual(cx, rcx, places=6)
            self.assertAlmostEqual(cy, rcy, places=6)

    def test_uv_round_trip(self):
        atlas_w, atlas_h = 2048.0, 2048.0
        px, py = 512.0, 1024.0
        u, v = canvas_to_uv(px, py, atlas_w, atlas_h)
        self.assertAlmostEqual(u, 0.25, places=6)
        self.assertAlmostEqual(v, 0.5, places=6)
        rpx, rpy = uv_to_canvas(u, v, atlas_w, atlas_h)
        self.assertAlmostEqual(px, rpx, places=6)
        self.assertAlmostEqual(py, rpy, places=6)

    def test_angle_conversions(self):
        self.assertAlmostEqual(deg_to_rad(180.0), math.pi, places=6)
        self.assertAlmostEqual(rad_to_deg(math.pi), 180.0, places=6)
        self.assertAlmostEqual(normalize_angle_rad(3.0 * math.pi), math.pi, places=5)


if __name__ == "__main__":
    unittest.main()
