# Phaser 3 Integration Guide

## What the Exporter Produces
- `atlases/` — Atlas PNG files
- `<assetId>.json` — Phaser multi-texture atlas JSON
- `<assetId>.ts` — TypeScript loader and animation factory
- `README.md` — Setup instructions

## Integration Steps

### 1. Copy Files
```
assets/
  <assetId>/
    atlases/        ← copy from exports/phaser/atlases/
    <assetId>.json  ← copy from exports/phaser/
```

### 2. Load in Preload
```typescript
import { preloadWarrior, createWarriorAnimations } from './warrior';

class GameScene extends Phaser.Scene {
  preload() {
    preloadWarrior(this, 'assets/warrior/phaser');
  }

  create() {
    createWarriorAnimations(this);
    const sprite = this.add.sprite(400, 300, 'warrior');
    sprite.play('warrior_idle');
  }
}
```

### 3. Animation Keys
Animation keys are formatted as `<assetId>_<clipName>`:
- `warrior_idle`
- `warrior_walk`
- `warrior_attack`

## Pixel Art Settings
```typescript
// In game config for pixel art
const config: Phaser.Types.Core.GameConfig = {
  render: {
    pixelArt: true,       // Disables antialiasing
    antialias: false,
  }
};
```
