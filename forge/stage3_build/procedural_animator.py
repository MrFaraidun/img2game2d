#!/usr/bin/env python3
"""
Stage 3 Build: Procedural Animation Engine.
Generates game-ready animation clips (idle, walk, jump, attack, hurt) from
character reference layers using exact inverse-affine kinematics, continuous
lower-body shear deformation, and dynamic crescent slash VFX.

Usage:
    python3 forge/stage3_build/procedural_animator.py \
        --source source/foreground.png \
        --spec layers/layer-spec.json \
        --animations idle,walk,jump,attack,hurt \
        --out animations/
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.image_utils import ensure_rgba, load_image, save_image
from _shared.transforms import (
    apply_continuous_shear,
    get_inverse_affine_matrix,
    inpaint_contact_seam,
    transform_layer,
)
from _shared.schema_utils import load_json

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    pass

try:
    import numpy as np
except ImportError:
    pass


def draw_crescent_slash_vfx(
    canvas_size: Tuple[int, int],
    center: Tuple[int, int],
    radius: int = 150,
    thickness: int = 34,
    start_angle_deg: float = -40,
    end_angle_deg: float = 85,
    glow_color: Tuple[int, int, int] = (190, 235, 255),
    core_color: Tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """
    Generate a dynamic procedural crescent slash effect overlay.
    """
    vfx = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(vfx)

    cx, cy = center
    # Outer glow arc
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.arc(bbox, start=start_angle_deg, end=end_angle_deg,
             fill=(*glow_color, 160), width=thickness + 12)

    # Core sharp arc
    draw.arc(bbox, start=start_angle_deg, end=end_angle_deg,
             fill=(*core_color, 255), width=thickness)

    # Blur for ethereal motion blur glow
    glow = vfx.filter(ImageFilter.GaussianBlur(radius=3))
    # Composite core over glow
    result = Image.alpha_composite(glow, vfx)
    return result


class ProceduralAnimator:
    def __init__(self, foreground_path: str, spec_path: str | None = None):
        self.foreground = load_image(foreground_path)
        self.w, self.h = self.foreground.size
        self.layers: Dict[str, Image.Image] = {}
        self.pivots: Dict[str, Tuple[float, float]] = {}
        self.spec = load_json(spec_path) if spec_path and Path(spec_path).exists() else {}

        self._prepare_layers()

    def _prepare_layers(self) -> None:
        """
        Identify or synthesize active body layers and weapon layers.
        """
        layer_defs = self.spec.get("layers", {})
        if layer_defs:
            for lid, linfo in layer_defs.items():
                p = linfo.get("pivot", {})
                self.pivots[lid] = (
                    p.get("x", self.w * 0.5),
                    p.get("y", self.h * 0.5),
                )
        else:
            # Default humanoid pivots
            self.pivots = {
                "root": (self.w * 0.5, self.h * 0.9),
                "torso": (self.w * 0.5, self.h * 0.55),
                "head": (self.w * 0.5, self.h * 0.28),
                "weapon": (self.w * 0.62, self.h * 0.62),
            }

    def generate_idle(self, frame_count: int = 6) -> List[Image.Image]:
        """
        Subtle breathing and vertical squash/stretch loop.
        """
        frames = []
        root_pivot = self.pivots.get("root", (self.w * 0.5, self.h * 0.9))

        for i in range(frame_count):
            t = (i / frame_count) * (2.0 * math.pi)
            # Breathing cycle: vertical stretch 0.98 to 1.02
            scale_y = 1.0 + 0.02 * math.sin(t)
            scale_x = 1.0 - 0.01 * math.sin(t)
            dy = -2.0 * math.sin(t)

            frame = transform_layer(
                self.foreground,
                pivot=root_pivot,
                angle_rad=0.0,
                dx=0.0,
                dy=dy,
                sx=scale_x,
                sy=scale_y,
            )
            frames.append(frame)
        return frames

    def generate_walk(self, frame_count: int = 8) -> List[Image.Image]:
        """
        Continuous lower-body shear deformation stride loop.
        Never cuts character into separate pieces — smoothly shears legs/cloak.
        """
        frames = []
        hip_y = self.h * 0.55
        stride_max = self.w * 0.06

        for i in range(frame_count):
            t = (i / frame_count) * (2.0 * math.pi)
            # Alternating horizontal stride
            stride = stride_max * math.sin(t)
            # Slight vertical bob
            bob_y = abs(math.sin(t)) * -4.0
            # Slight forward/back tilt
            tilt = 0.03 * math.sin(t)

            # 1. Apply continuous lower body shear
            sheared = apply_continuous_shear(
                self.foreground,
                hip_y=hip_y,
                stride_pixels=stride,
                span=self.h * 0.35,
            )

            # 2. Apply whole-body bob and tilt around root pivot
            root_pivot = (self.w * 0.5, self.h * 0.85)
            frame = transform_layer(
                sheared,
                pivot=root_pivot,
                angle_rad=tilt,
                dx=0.0,
                dy=bob_y,
                sx=1.0,
                sy=1.0,
            )
            frames.append(frame)
        return frames

    def generate_jump(self, frame_count: int = 6) -> List[Image.Image]:
        """
        Jump arc: anticipation squash -> launch stretch -> apex float -> landing.
        """
        frames = []
        root_pivot = (self.w * 0.5, self.h * 0.88)

        phases = [
            {"sy": 0.90, "sx": 1.06, "dy": 8.0, "angle": 0.0},    # 0: Crouch anticipation
            {"sy": 1.08, "sx": 0.94, "dy": -24.0, "angle": 0.03}, # 1: Launch stretch
            {"sy": 1.02, "sx": 0.98, "dy": -46.0, "angle": 0.05}, # 2: Rising
            {"sy": 0.97, "sx": 1.02, "dy": -52.0, "angle": 0.0},  # 3: Apex float
            {"sy": 1.05, "sx": 0.96, "dy": -20.0, "angle": -0.02},# 4: Falling
            {"sy": 0.92, "sx": 1.05, "dy": 4.0, "angle": 0.0},    # 5: Landing compression
        ]

        for p in phases[:frame_count]:
            frame = transform_layer(
                self.foreground,
                pivot=root_pivot,
                angle_rad=p["angle"],
                dx=0.0,
                dy=p["dy"],
                sx=p["sx"],
                sy=p["sy"],
            )
            frames.append(frame)
        return frames

    def generate_attack(self, frame_count: int = 6) -> List[Image.Image]:
        """
        Explosive attack swing with character anticipation lunge and
        dynamic crescent slash VFX.
        """
        frames = []
        root_pivot = (self.w * 0.5, self.h * 0.85)

        # Kinematic poses for character body
        body_poses = [
            {"dx": -14.0, "dy": 4.0, "angle": -0.08, "slash": False}, # Frame 0: Windup / anticipation
            {"dx": 26.0, "dy": 2.0, "angle": 0.06, "slash": False},   # Frame 1: Lunge strike
            {"dx": 44.0, "dy": 0.0, "angle": 0.12, "slash": True},    # Frame 2: Slash impact + VFX
            {"dx": 36.0, "dy": 0.0, "angle": 0.08, "slash": True},    # Frame 3: Follow-through
            {"dx": 18.0, "dy": 2.0, "angle": 0.03, "slash": False},   # Frame 4: Recovery
            {"dx": 0.0, "dy": 0.0, "angle": 0.0, "slash": False},     # Frame 5: Return to rest
        ]

        for i, pose in enumerate(body_poses[:frame_count]):
            # Transform body
            frame = transform_layer(
                self.foreground,
                pivot=root_pivot,
                angle_rad=pose["angle"],
                dx=pose["dx"],
                dy=pose["dy"],
                sx=1.0,
                sy=1.0,
            )

            # Add procedural crescent slash VFX on strike frames
            if pose.get("slash"):
                slash_cx = int(self.w * 0.62 + pose["dx"])
                slash_cy = int(self.h * 0.46)
                radius = int(self.w * 0.32)
                alpha_mult = 1.0 if i == 2 else 0.55
                vfx = draw_crescent_slash_vfx(
                    (self.w, self.h),
                    center=(slash_cx, slash_cy),
                    radius=radius,
                    thickness=int(self.w * 0.06),
                    start_angle_deg=-45 if i == 2 else -20,
                    end_angle_deg=85 if i == 2 else 95,
                )
                if alpha_mult < 1.0:
                    vfx_arr = np.array(vfx)
                    vfx_arr[:, :, 3] = (vfx_arr[:, :, 3].astype(float) * alpha_mult).astype(np.uint8)
                    vfx = Image.fromarray(vfx_arr)
                frame = Image.alpha_composite(frame, vfx)

            frames.append(frame)
        return frames

    def generate_hurt(self, frame_count: int = 4) -> List[Image.Image]:
        """
        Damage recoil animation with knockback tilt and red impact flash.
        """
        frames = []
        root_pivot = (self.w * 0.5, self.h * 0.85)

        recoils = [
            {"dx": -32.0, "dy": -8.0, "angle": -0.15, "flash": True},  # 0: Heavy impact hit
            {"dx": -24.0, "dy": -4.0, "angle": -0.10, "flash": False}, # 1: Mid-recoil
            {"dx": -10.0, "dy": 0.0, "angle": -0.04, "flash": False},  # 2: Recovering
            {"dx": 0.0, "dy": 0.0, "angle": 0.0, "flash": False},      # 3: Settled
        ]

        for r in recoils[:frame_count]:
            frame = transform_layer(
                self.foreground,
                pivot=root_pivot,
                angle_rad=r["angle"],
                dx=r["dx"],
                dy=r["dy"],
                sx=0.96,
                sy=1.02,
            )
            if r.get("flash"):
                arr = np.array(frame).astype(float)
                # Tint red on impact
                arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.35 + 40, 0, 255)
                arr[:, :, 1] = np.clip(arr[:, :, 1] * 0.75, 0, 255)
                arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.75, 0, 255)
                frame = Image.fromarray(arr.astype(np.uint8))

            frames.append(frame)
        return frames

    def build_all(
        self,
        animation_names: List[str],
        out_dir: str,
    ) -> Dict[str, List[str]]:
        """
        Generate frames for all requested animations and save to disk.
        """
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        results: Dict[str, List[str]] = {}

        generators = {
            "idle": self.generate_idle,
            "walk": self.generate_walk,
            "jump": self.generate_jump,
            "attack": self.generate_attack,
            "hurt": self.generate_hurt,
        }

        for anim in animation_names:
            gen_func = generators.get(anim, self.generate_idle)
            frames = gen_func()
            anim_dir = out_path / anim
            anim_dir.mkdir(parents=True, exist_ok=True)

            paths = []
            for idx, f in enumerate(frames):
                file_path = anim_dir / f"{idx:03d}.png"
                save_image(f, str(file_path))
                paths.append(str(file_path))

            results[anim] = paths
            print(f"  Procedural: {anim} -> {len(paths)} frames")

        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Procedural 2D Game Asset Animation Generator")
    parser.add_argument("--source", required=True, help="Path to foreground PNG")
    parser.add_argument("--spec", default=None, help="Path to layer-spec.json or asset.json")
    parser.add_argument("--animations", default="idle,walk,jump,attack,hurt", help="Comma-separated animations")
    parser.add_argument("--out", required=True, help="Output animations directory")

    args = parser.parse_args()
    animator = ProceduralAnimator(args.source, args.spec)
    anims = [a.strip() for a in args.animations.split(",") if a.strip()]
    results = animator.build_all(anims, args.out)
    print(f"\nGenerated {sum(len(v) for v in results.values())} frames across {len(results)} clips in {args.out}")


if __name__ == "__main__":
    main()
