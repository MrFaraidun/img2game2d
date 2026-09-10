/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Dynamic 2D Tangent Space Normal Map Lighting Hook
 * 
 * Implements real-time per-pixel normal map deflection, Blinn-Phong specular
 * highlights, HDR bloom emission composition, and draggable multi-light rigs.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  LightingEngineState,
  DynamicLightSource,
  LightingPresetConfig,
  LightingViewMode,
  CharacterRuntimeAsset,
  ResolvedFrameCoordinates
} from '../types';
import { audio } from '../lib/audio';

/** Pre-configured lighting presets */
export const LIGHTING_PRESETS: Record<string, LightingPresetConfig> = {
  neon: {
    id: 'neon',
    name: 'Cyberpunk Neon',
    subtitle: 'High bloom glow + vibrant cyan point light',
    description: 'Deep obsidian ambient with high-contrast specular reflections on blade bevels and visor emissives.',
    ambientIntensity: 0.22,
    ambientColorHex: '#0f172a',
    mainLight: {
      intensity: 2.5,
      radius: 420,
      zDepth: 45,
      colorHex: '#00f0ff',
      specularPower: 1.8
    },
    bloomBoost: 2.2,
    bloomThreshold: 120,
    toneMapping: 'aces'
  },
  torch: {
    id: 'torch',
    name: 'Dungeon Torch',
    subtitle: 'Warm amber glow with steep normal falloff',
    description: 'Organic flickering firelight with steep Lambertian falloff and warm amber specular highlights.',
    ambientIntensity: 0.12,
    ambientColorHex: '#1c1917',
    mainLight: {
      intensity: 1.8,
      radius: 340,
      zDepth: 35,
      colorHex: '#f59e0b',
      specularPower: 1.2
    },
    bloomBoost: 1.1,
    bloomThreshold: 150,
    toneMapping: 'reinhard'
  },
  sun: {
    id: 'sun',
    name: 'Studio Key Light',
    subtitle: 'High Z-depth ambient fill + balanced bevels',
    description: 'Natural directional daylight fill simulating outdoor sunny conditions with crisp micro-shadows.',
    ambientIntensity: 0.55,
    ambientColorHex: '#334155',
    mainLight: {
      intensity: 1.2,
      radius: 650,
      zDepth: 95,
      colorHex: '#ffffff',
      specularPower: 0.8
    },
    bloomBoost: 1.0,
    bloomThreshold: 180,
    toneMapping: 'linear'
  },
  visor_surge: {
    id: 'visor_surge',
    name: 'Visor Surge HDR',
    subtitle: 'Overclocked weapon emission bloom',
    description: 'Supercharged emissive visor and weapon channels with extreme bloom amplification and low ambient.',
    ambientIntensity: 0.15,
    ambientColorHex: '#030712',
    mainLight: {
      intensity: 1.4,
      radius: 380,
      zDepth: 50,
      colorHex: '#8b5cf6',
      specularPower: 2.2
    },
    bloomBoost: 3.0,
    bloomThreshold: 80,
    toneMapping: 'aces'
  }
};

/** Hex to RGB color parser helper */
function hexToRgb(hex: string): { r: number; g: number; b: number } {
  let clean = hex.replace('#', '');
  if (clean.length === 3) {
    clean = clean.split('').map((c) => c + c).join('');
  }
  const num = parseInt(clean, 16);
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255
  };
}

export function useNormalLighting() {
  const [lightingState, setLightingState] = useState<LightingEngineState>({
    viewMode: 'composite',
    splitPositionRatio: 0.5,
    activePresetId: 'neon',
    ambientBaseLevel: 0.25,
    ambientColorHex: '#0f172a',
    bloomBoost: 1.8,
    bloomThreshold: 120,
    useInvertedY: false,
    specularEnabled: true,
    specularShininess: 32.0,
    activeLightId: 'torch_primary',
    lights: [
      {
        id: 'torch_primary',
        name: 'Primary Torchlight',
        type: 'point',
        x: 288,
        y: 200,
        zDepth: 45,
        intensity: 2.2,
        radius: 380,
        colorHex: '#00f0ff',
        colorRgb: { r: 0, g: 240, b: 255 },
        specularPower: 1.6,
        specularShininess: 32.0,
        enabled: true,
        isDraggable: true
      },
      {
        id: 'torch_accent',
        name: 'Rim Accent Light',
        type: 'point',
        x: 420,
        y: 320,
        zDepth: 60,
        intensity: 1.2,
        radius: 280,
        colorHex: '#ec4899',
        colorRgb: { r: 236, g: 72, b: 153 },
        specularPower: 1.0,
        specularShininess: 24.0,
        enabled: false,
        isDraggable: true
      }
    ]
  });

  // Offscreen calculation buffers to avoid layout thrashing
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const offscreenCtxRef = useRef<CanvasRenderingContext2D | null>(null);

  useEffect(() => {
    const offCanvas = document.createElement('canvas');
    offCanvas.width = 576;
    offCanvas.height = 512;
    offscreenCanvasRef.current = offCanvas;
    offscreenCtxRef.current = offCanvas.getContext('2d', { willReadFrequently: true });
  }, []);

  /**
   * Set active lighting view mode (composite, split, diffuse, normal, emission)
   */
  const setViewMode = useCallback((mode: LightingViewMode) => {
    setLightingState((prev) => ({ ...prev, viewMode: mode }));
    audio.play('ui_click');
  }, []);

  /**
   * Apply lighting preset
   */
  const applyPreset = useCallback((presetId: string) => {
    const preset = LIGHTING_PRESETS[presetId];
    if (!preset) return;

    setLightingState((prev) => {
      const updatedLights = prev.lights.map((l) => {
        if (l.id === 'torch_primary') {
          const rgb = hexToRgb(preset.mainLight.colorHex);
          return {
            ...l,
            intensity: preset.mainLight.intensity,
            radius: preset.mainLight.radius,
            zDepth: preset.mainLight.zDepth,
            colorHex: preset.mainLight.colorHex,
            colorRgb: rgb,
            specularPower: preset.mainLight.specularPower
          };
        }
        return l;
      });

      return {
        ...prev,
        activePresetId: presetId,
        ambientBaseLevel: preset.ambientIntensity,
        ambientColorHex: preset.ambientColorHex,
        bloomBoost: preset.bloomBoost,
        bloomThreshold: preset.bloomThreshold,
        lights: updatedLights
      };
    });

    audio.play('torch_light');
  }, []);

  /**
   * Update primary light position (driven by mouse drag or cursor hover)
   */
  const setPrimaryLightPosition = useCallback((x: number, y: number) => {
    setLightingState((prev) => {
      const lights = prev.lights.map((l) => {
        if (l.id === prev.activeLightId) {
          return { ...l, x, y };
        }
        return l;
      });
      return { ...prev, lights };
    });
  }, []);

  /**
   * Update parameters of the active light
   */
  const updateActiveLight = useCallback((updates: Partial<DynamicLightSource>) => {
    setLightingState((prev) => {
      const lights = prev.lights.map((l) => {
        if (l.id === prev.activeLightId) {
          const colorRgb = updates.colorHex ? hexToRgb(updates.colorHex) : l.colorRgb;
          return { ...l, ...updates, colorRgb };
        }
        return l;
      });
      return { ...prev, lights };
    });
  }, []);

  /**
   * Update ambient base fill level
   */
  const setAmbientLevel = useCallback((ambient: number) => {
    setLightingState((prev) => ({ ...prev, ambientBaseLevel: ambient }));
  }, []);

  /**
   * Update bloom emission boost
   */
  const setBloomBoost = useCallback((boost: number) => {
    setLightingState((prev) => ({ ...prev, bloomBoost: boost }));
  }, []);

  /**
   * Update split screen comparison ratio (0.0 to 1.0)
   */
  const setSplitRatio = useCallback((ratio: number) => {
    setLightingState((prev) => ({
      ...prev,
      splitPositionRatio: Math.max(0, Math.min(1, ratio))
    }));
  }, []);

  /**
   * Core Shader Pipeline: Render 2D Tangent Space Lighting on Target Canvas
   */
  const renderLightingScene = useCallback((
    targetCtx: CanvasRenderingContext2D,
    char: CharacterRuntimeAsset,
    coords: ResolvedFrameCoordinates
  ) => {
    const offCanvas = offscreenCanvasRef.current;
    const offCtx = offscreenCtxRef.current;
    if (!offCanvas || !offCtx || !char.atlasImg) return;

    const { source: s, dest: d } = coords;
    const width = targetCtx.canvas.width;
    const height = targetCtx.canvas.height;

    // View Mode Fast-Path: Unlit Diffuse Only
    if (lightingState.viewMode === 'diffuse_only') {
      targetCtx.clearRect(0, 0, width, height);
      targetCtx.drawImage(char.atlasImg, s.x, s.y, s.w, s.h, d.x, d.y, d.w, d.h);
      return;
    }

    // View Mode Fast-Path: Tangent Normal Map Only
    if (lightingState.viewMode === 'normal_only' && char.normalImg) {
      targetCtx.clearRect(0, 0, width, height);
      targetCtx.drawImage(char.normalImg, s.x, s.y, s.w, s.h, d.x, d.y, d.w, d.h);
      return;
    }

    // View Mode Fast-Path: Bloom Emission Glow Only
    if (lightingState.viewMode === 'emission_only' && char.emissionImg) {
      targetCtx.clearRect(0, 0, width, height);
      targetCtx.drawImage(char.emissionImg, s.x, s.y, s.w, s.h, d.x, d.y, d.w, d.h);
      return;
    }

    // Extract Diffuse Channel Pixels
    offCtx.clearRect(0, 0, width, height);
    offCtx.drawImage(char.atlasImg, s.x, s.y, s.w, s.h, d.x, d.y, d.w, d.h);
    const diffImgData = offCtx.getImageData(0, 0, width, height);
    const diffData = diffImgData.data;

    // Extract Normal Channel Pixels
    let normData: Uint8ClampedArray | null = null;
    if (char.normalImg) {
      offCtx.clearRect(0, 0, width, height);
      offCtx.drawImage(char.normalImg, s.x, s.y, s.w, s.h, d.x, d.y, d.w, d.h);
      normData = offCtx.getImageData(0, 0, width, height).data;
    }

    // Extract Bloom Emission Channel Pixels
    let emisData: Uint8ClampedArray | null = null;
    if (char.emissionImg) {
      offCtx.clearRect(0, 0, width, height);
      offCtx.drawImage(char.emissionImg, s.x, s.y, s.w, s.h, d.x, d.y, d.w, d.h);
      emisData = offCtx.getImageData(0, 0, width, height).data;
    }

    // Create Destination Canvas Image Buffer
    const outImgData = targetCtx.createImageData(width, height);
    const outData = outImgData.data;

    const ambient = lightingState.ambientBaseLevel;
    const bloom = lightingState.bloomBoost;
    const splitX = Math.floor(width * lightingState.splitPositionRatio);
    const isSplitMode = lightingState.viewMode === 'split';

    // Active enabled lights
    const activeLights = lightingState.lights.filter((l) => l.enabled);

    // Pixel Processing Loop
    for (let py = 0; py < height; py++) {
      for (let px = 0; px < width; px++) {
        const idx = (py * width + px) * 4;
        const alpha = diffData[idx + 3];
        if (alpha < 8) continue; // Early discard for transparent pixels

        const dr = diffData[idx];
        const dg = diffData[idx + 1];
        const db = diffData[idx + 2];

        // If in Split-View mode and to the left of split divider, render unlit raw albedo
        if (isSplitMode && px < splitX) {
          outData[idx] = dr;
          outData[idx + 1] = dg;
          outData[idx + 2] = db;
          outData[idx + 3] = alpha;
          continue;
        }

        let totalLightR = ambient;
        let totalLightG = ambient;
        let totalLightB = ambient;
        let totalSpecular = 0.0;

        // Normal Vector from Tangent Texture [0..255] -> [-1.0..1.0]
        let nx = 0.0, ny = 0.0, nz = 1.0;
        if (normData) {
          nx = (normData[idx] / 255) * 2 - 1;
          ny = (normData[idx + 1] / 255) * 2 - 1;
          nz = (normData[idx + 2] / 255) * 2 - 1;
        }

        // Accumulate Multi-Light Influences
        for (let li = 0; li < activeLights.length; li++) {
          const light = activeLights[li];
          const dx = light.x - px;
          const dy = light.y - py;
          const dist2D = Math.sqrt(dx * dx + dy * dy);

          if (dist2D >= light.radius) continue;

          // Non-linear smooth attenuation curve
          const attenuation = Math.pow(1 - dist2D / light.radius, 1.8);
          const dist3D = Math.sqrt(dx * dx + dy * dy + light.zDepth * light.zDepth);

          // Normalized Light Direction Vector
          const lx = dx / dist3D;
          const ly = lightingState.useInvertedY ? (dy / dist3D) : (-dy / dist3D); // OpenGL Convention
          const lz = light.zDepth / dist3D;

          // Lambertian Dot Product (N • L)
          const dot = Math.max(0, nx * lx + ny * ly + nz * lz);
          const diffuseFactor = dot * attenuation * light.intensity;

          // Blinn-Phong Specular Reflection
          if (lightingState.specularEnabled) {
            // Halfway vector H between Light L and Eye V (0, 0, 1)
            const hx = lx;
            const hy = ly;
            const hz = lz + 1.0;
            const hLen = Math.sqrt(hx * hx + hy * hy + hz * hz);
            const ndoth = Math.max(0, (nx * hx + ny * hy + nz * hz) / hLen);
            const spec = Math.pow(ndoth, lightingState.specularShininess) * attenuation * light.specularPower;
            totalSpecular += spec * 255;
          }

          const cRgb = light.colorRgb;
          totalLightR += (cRgb.r / 255) * diffuseFactor;
          totalLightG += (cRgb.g / 255) * diffuseFactor;
          totalLightB += (cRgb.b / 255) * diffuseFactor;
        }

        // Additive Bloom Emission Mask
        let er = 0, eg = 0, eb = 0;
        if (emisData) {
          er = emisData[idx] * bloom;
          eg = emisData[idx + 1] * bloom;
          eb = emisData[idx + 2] * bloom;
        }

        outData[idx] = Math.min(255, dr * totalLightR + er + totalSpecular);
        outData[idx + 1] = Math.min(255, dg * totalLightG + eg + totalSpecular);
        outData[idx + 2] = Math.min(255, db * totalLightB + eb + totalSpecular);
        outData[idx + 3] = alpha;
      }
    }

    targetCtx.clearRect(0, 0, width, height);
    targetCtx.putImageData(outImgData, 0, 0);

    // Draw interactive Split-View separator line on canvas
    if (isSplitMode) {
      targetCtx.save();
      targetCtx.strokeStyle = '#00f0ff';
      targetCtx.lineWidth = 2;
      targetCtx.setLineDash([4, 4]);
      targetCtx.beginPath();
      targetCtx.moveTo(splitX, 0);
      targetCtx.lineTo(splitX, height);
      targetCtx.stroke();

      // Split Divider Labels
      targetCtx.fillStyle = '#ffffff';
      targetCtx.font = '10px Inter, sans-serif';
      targetCtx.fillText('UNLIT DIFFUSE', splitX - 85, 20);
      targetCtx.fillText('NORMAL LIT', splitX + 10, 20);
      targetCtx.restore();
    }
  }, [lightingState]);

  return {
    lightingState,
    setViewMode,
    applyPreset,
    setPrimaryLightPosition,
    updateActiveLight,
    setAmbientLevel,
    setBloomBoost,
    setSplitRatio,
    renderLightingScene
  };
}
