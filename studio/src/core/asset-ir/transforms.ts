/**
 * Mathematical coordinate transformations for AssetIR in Studio.
 * Implements strict, lossless conversions between Canvas, World, Spine, and UV spaces.
 */

export interface Point2D {
  x: number;
  y: number;
}

export function canvasToWorld(
  canvasPt: Point2D,
  canvasH: number,
  groundY: number,
  pivotX: number
): Point2D {
  if (canvasH <= 0) throw new Error('canvasH must be strictly positive');
  return {
    x: (canvasPt.x - pivotX) / canvasH,
    y: (groundY - canvasPt.y) / canvasH,
  };
}

export function worldToCanvas(
  worldPt: Point2D,
  canvasH: number,
  groundY: number,
  pivotX: number
): Point2D {
  return {
    x: worldPt.x * canvasH + pivotX,
    y: groundY - worldPt.y * canvasH,
  };
}

export function canvasToSpine(
  canvasPt: Point2D,
  groundY: number,
  pivotX: number
): Point2D {
  return {
    x: canvasPt.x - pivotX,
    y: groundY - canvasPt.y,
  };
}

export function spineToCanvas(
  spinePt: Point2D,
  groundY: number,
  pivotX: number
): Point2D {
  return {
    x: spinePt.x + pivotX,
    y: groundY - spinePt.y,
  };
}

export function uvToCanvas(
  u: number,
  v: number,
  atlasW: number,
  atlasH: number
): Point2D {
  return {
    x: u * atlasW,
    y: v * atlasH,
  };
}

export function canvasToUv(
  pxX: number,
  pxY: number,
  atlasW: number,
  atlasH: number
): { u: number; v: number } {
  if (atlasW <= 0 || atlasH <= 0) throw new Error('Atlas dimensions must be positive');
  return {
    u: pxX / atlasW,
    v: pxY / atlasH,
  };
}

export function degToRad(deg: number): number {
  return (deg * Math.PI) / 180.0;
}

export function radToDeg(rad: number): number {
  return (rad * 180.0) / Math.PI;
}

export function normalizeAngleRad(angleRad: number): number {
  let ang = ((angleRad + Math.PI) % (2.0 * Math.PI)) - Math.PI;
  if (ang <= -Math.PI + 1e-9) {
    ang += 2.0 * Math.PI;
  }
  return ang;
}
