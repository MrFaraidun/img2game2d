/**
 * Client-side validation and diagnostics engine for Studio AssetIR.
 */
import { AssetIR, DiagnosticIR } from './types';

export function validateAssetIR(asset: AssetIR): DiagnosticIR[] {
  const diagnostics: DiagnosticIR[] = [];

  // 1. Schema version
  if (!asset.schemaVersion.startsWith('3.')) {
    diagnostics.push({
      severity: 'error',
      code: 'INVALID_SCHEMA_VERSION',
      message: `Unsupported schema version '${asset.schemaVersion}', expected '3.x.x'`,
      suggestedFix: 'Update AssetIR version to 3.0.0',
    });
  }

  // 2. Frames validation
  const frameIds = new Set(asset.frames.map((f) => f.id));
  for (const f of asset.frames) {
    if (f.canvasRect.w <= 0 || f.canvasRect.h <= 0) {
      diagnostics.push({
        severity: 'error',
        code: 'EMPTY_FRAME',
        message: `Frame '${f.id}' has zero or negative dimension.`,
        objectId: f.id,
        suggestedFix: 'Adjust crop boundaries in sprite sheet.',
      });
    }

    if (f.uvRect) {
      const { u0, v0, u1, v1 } = f.uvRect;
      if (Math.min(u0, v0, u1, v1) < 0.0 || Math.max(u0, v0, u1, v1) > 1.0001) {
        diagnostics.push({
          severity: 'error',
          code: 'UV_OUT_OF_RANGE',
          message: `Frame '${f.id}' has UV out of [0..1] range.`,
          objectId: f.id,
          suggestedFix: 'Re-pack texture atlas.',
        });
      }
    }
  }

  // 3. Animation frame reference check
  for (const anim of asset.animations) {
    if (anim.frameIds.length === 0) {
      diagnostics.push({
        severity: 'warning',
        code: 'EMPTY_ANIMATION',
        message: `Animation '${anim.name}' contains no frames.`,
        objectId: anim.id,
      });
    }
    for (const fId of anim.frameIds) {
      if (!frameIds.has(fId)) {
        diagnostics.push({
          severity: 'error',
          code: 'DANGLING_FRAME_REF',
          message: `Animation '${anim.name}' references non-existent frame '${fId}'.`,
          objectId: anim.id,
        });
      }
    }
  }

  // 4. Skeleton validation
  if (asset.skeleton) {
    const boneIds = new Set(asset.skeleton.bones.map((b) => b.id));
    if (!boneIds.has(asset.skeleton.rootBoneId)) {
      diagnostics.push({
        severity: 'error',
        code: 'MISSING_PARENT_BONE',
        message: `Root bone ID '${asset.skeleton.rootBoneId}' does not exist in skeleton.`,
      });
    }
    for (const b of asset.skeleton.bones) {
      if (b.parentId && !boneIds.has(b.parentId)) {
        diagnostics.push({
          severity: 'error',
          code: 'MISSING_PARENT_BONE',
          message: `Bone '${b.name}' references missing parent '${b.parentId}'.`,
          objectId: b.id,
        });
      }
    }
  }

  // 5. Mesh weight sum validation
  if (asset.meshes) {
    for (const m of asset.meshes) {
      m.weights.forEach((vWeights, vIdx) => {
        const sum = vWeights.reduce((acc, w) => acc + w.weight, 0);
        if (Math.abs(sum - 1.0) > 1e-3) {
          diagnostics.push({
            severity: 'error',
            code: 'WEIGHT_SUM_INVALID',
            message: `Mesh '${m.id}' vertex ${vIdx} weights sum to ${sum.toFixed(4)}, expected 1.0.`,
            objectId: m.id,
            suggestedFix: 'Normalize vertex bone weights.',
          });
        }
      });
    }
  }

  return diagnostics;
}
