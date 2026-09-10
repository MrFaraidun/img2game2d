"""
Explicit coordinate transformations for img2game2d AssetIR.

Maintains mathematical precision between:
- Canvas Space: pixels, origin top-left (0, 0), +X right, +Y down
- World Space: float units, origin at ground datum anchor (pivot_x, ground_y), +X right, +Y up
- Spine Space: pixels, origin at root ground datum (pivot_x, ground_y), +X right, +Y up
- Normalized UV Space: [0..1], origin top-left (0, 0), +U right, +V down
"""
from __future__ import annotations

import math
from typing import Dict, Tuple


def canvas_to_world(
    canvas_x: float,
    canvas_y: float,
    canvas_h: float,
    ground_y: float,
    pivot_x: float,
) -> Tuple[float, float]:
    """Converts Canvas (px, Y-down) to World (normalized float units, Y-up)."""
    if canvas_h <= 0:
        raise ValueError("canvas_h must be strictly positive")
    world_x = (canvas_x - pivot_x) / canvas_h
    world_y = (ground_y - canvas_y) / canvas_h
    return world_x, world_y


def world_to_canvas(
    world_x: float,
    world_y: float,
    canvas_h: float,
    ground_y: float,
    pivot_x: float,
) -> Tuple[float, float]:
    """Converts World (normalized float units, Y-up) to Canvas (px, Y-down)."""
    canvas_x = world_x * canvas_h + pivot_x
    canvas_y = ground_y - world_y * canvas_h
    return canvas_x, canvas_y


def canvas_to_spine(
    canvas_x: float,
    canvas_y: float,
    ground_y: float,
    pivot_x: float,
) -> Tuple[float, float]:
    """Converts Canvas (px, Y-down) to Spine (px, Y-up)."""
    spine_x = canvas_x - pivot_x
    spine_y = ground_y - canvas_y
    return spine_x, spine_y


def spine_to_canvas(
    spine_x: float,
    spine_y: float,
    ground_y: float,
    pivot_x: float,
) -> Tuple[float, float]:
    """Converts Spine (px, Y-up) to Canvas (px, Y-down)."""
    canvas_x = spine_x + pivot_x
    canvas_y = ground_y - spine_y
    return canvas_x, canvas_y


def uv_to_canvas(
    u: float,
    v: float,
    atlas_w: float,
    atlas_h: float,
) -> Tuple[float, float]:
    """Converts normalized UV [0..1] to pixel atlas coordinates."""
    return u * atlas_w, v * atlas_h


def canvas_to_uv(
    px_x: float,
    px_y: float,
    atlas_w: float,
    atlas_h: float,
) -> Tuple[float, float]:
    """Converts pixel atlas coordinates to normalized UV [0..1]."""
    if atlas_w <= 0 or atlas_h <= 0:
        raise ValueError("Atlas dimensions must be strictly positive")
    return px_x / atlas_w, px_y / atlas_h


def normalize_angle_rad(angle_rad: float) -> float:
    """Normalizes an angle to range (-pi, pi]."""
    ang = (angle_rad + math.pi) % (2.0 * math.pi) - math.pi
    if ang <= -math.pi + 1e-9:
        ang += 2.0 * math.pi
    return ang


def deg_to_rad(deg: float) -> float:
    """Converts degrees to radians."""
    return deg * math.pi / 180.0


def rad_to_deg(rad: float) -> float:
    """Converts radians to degrees."""
    return rad * 180.0 / math.pi
