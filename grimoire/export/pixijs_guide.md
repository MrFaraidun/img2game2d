# PixiJS Integration Guide

## What the Exporter Produces
- `atlases/` — Atlas PNG files
- `<assetId>_<clip>.json` — Per-clip PixiJS spritesheet JSON
- `<assetId>.ts` — TypeScript loader and `AnimatedSprite` factory
- `README.md` — Setup instructions

## Integration Steps

### 1. Load Sprite Sheets
```typescript
import { loadWarrior, createWarriorSprite } from './warrior';

const app = new PIXI.Application({ width: 800, height: 600 });

// Load sheets
loadWarrior(PIXI.Loader.shared, 'assets/warrior/pixijs');

PIXI.Loader.shared.load(() => {
  // Create an idle sprite
  const sprite = createWarriorSprite('idle');
  sprite.position.set(400, 300);
  app.stage.addChild(sprite);
});
```

### 2. Switch Animations
```typescript
// To switch animation, create a new sprite for the new clip
// (PixiJS AnimatedSprite doesn't support clip switching natively)
function switchAnimation(stage: PIXI.Container, oldSprite: PIXI.AnimatedSprite, clip: string) {
  const pos = oldSprite.position.clone();
  stage.removeChild(oldSprite);
  oldSprite.destroy();

  const newSprite = createWarriorSprite(clip);
  newSprite.position.copyFrom(pos);
  stage.addChild(newSprite);
  return newSprite;
}
```

### 3. Pixel Art Settings
```typescript
// For pixel art — disable smoothing
PIXI.settings.SCALE_MODE = PIXI.SCALE_MODES.NEAREST;
```

## PixiJS v7+ (Assets API)
```typescript
import { Assets, AnimatedSprite, Spritesheet } from 'pixi.js';

await Assets.load('assets/warrior/pixijs/warrior_idle.json');
const sheet = Assets.get<Spritesheet>('warrior_idle');
const sprite = new AnimatedSprite(Object.values(sheet.textures));
sprite.animationSpeed = 12 / 60;
sprite.play();
app.stage.addChild(sprite);
```
