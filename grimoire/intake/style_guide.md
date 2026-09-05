# Style Classification Guide

## When to read this
Read at Stage 1 (Intake) to classify the visual art style of the reference image.

---

## Why Style Matters
The detected style determines:
1. **Generation prompt language** — "pixel art sprite" vs "anime character"
2. **Post-processing filters** — pixel-perfect rendering vs smooth edges
3. **Atlas padding** — pixel art: 0–1px; painted: 2–4px
4. **Export settings** — texture filtering (nearest vs linear)

---

## Style Categories

### `pixel_art`
- Low resolution (≤ 64px recommended frame size)
- Hard edges, no anti-aliasing
- Highly limited palette (≤ 64 unique colors typical)
- Visible pixel grid
- **Engine setting**: texture filtering = `Nearest`

### `anime`
- Clean outlines (1–3px thick, dark)
- Flat color fills with minimal gradient
- Large eyes, stylized proportions
- Limited shadow regions (cel-shading)
- **Engine setting**: texture filtering = `Linear`

### `cartoon`
- Bold black outlines
- Saturated flat colors
- Exaggerated proportions
- **Engine setting**: `Linear`

### `comic`
- Ink-style hatching or cross-hatching
- Black/white with spot color OR full color with ink outline
- High contrast

### `painted`
- Painterly brushstrokes, visible texture
- Soft edges, gradients
- Rich detail and shading
- **Engine setting**: `Linear`

### `3d_rendered`
- 3D software rendered to 2D sprites (pre-rendered)
- Very smooth shading, specular highlights
- Slightly uncanny proportions

### `low_poly`
- Visible polygon faces, flat-shaded
- Geometric, angular forms

### `vector`
- SVG-style crisp edges at any resolution
- Clean fills, no raster artifacts

### `stylized`
- A unique style that doesn't fit the above cleanly
- Describe in `style_notes` field

### `realistic`
- Photo-realistic or near-photorealistic rendering

---

## How to Override the Script

`detect_style.py` uses heuristics — it can be wrong.

After running it, visually inspect the image and override if needed:
```json
// In analysis.json:
"visual_style": "anime",
"style_confidence": 0.9,
"style_override": true,
"style_notes": "Script guessed pixel_art due to low resolution but image is clearly anime-styled."
```

---

## Style → Frame Generation Prompt Modifiers

When generating animation frames (Stage 3), the style sets the prompt tone:

| Style | Prompt modifier |
|-------|----------------|
| `pixel_art` | "pixel art sprite, 16-bit style, hard pixel edges, limited palette" |
| `anime` | "anime 2D character sprite, cel-shaded, clean line art, flat colors" |
| `painted` | "hand-painted 2D sprite, painterly, detailed, digital illustration" |
| `cartoon` | "cartoon character sprite, bold outlines, vibrant flat colors" |
| `3d_rendered` | "pre-rendered 3D sprite, smooth shading, specular highlights" |
