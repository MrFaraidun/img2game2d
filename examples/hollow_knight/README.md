# Hollow Knight Example

This directory contains a sample character concept art generated specifically for `img2game2d`.

## File
- `reference.png`: High-contrast Hollow Knight style insectoid warrior on an isolated background.

## Quick Run
```bash
img2game2d build examples/hollow_knight/reference.png \
  --name "HollowKnight" \
  --category character \
  --animations "idle,walk,attack" \
  --engine all \
  --out work/hollow_knight/
```
