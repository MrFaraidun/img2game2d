/**
 * img2game2d Studio v2.0 Enterprise Architecture
 * Procedural Web Audio Synthesizer Engine
 * 
 * Generates zero-dependency procedural game audio for character actions,
 * UI micro-interactions, combat impacts, and ambient stage lighting feedback.
 * Operates purely via Web Audio API oscillators, biquad filters, and gain nodes.
 */

import { SoundEffectId, SynthVoiceConfig } from '../types';

class SoundEngine {
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private isMuted: boolean = false;
  private masterVolume: number = 0.7;
  private isInitialized: boolean = false;

  constructor() {
    // Lazy initialization on first user interaction to satisfy browser autoplay policies
  }

  /**
   * Initializes the Web Audio context if not already created
   */
  public init(): boolean {
    if (this.isInitialized && this.ctx && this.ctx.state !== 'closed') {
      if (this.ctx.state === 'suspended') {
        this.ctx.resume().catch((err) => console.warn('AudioContext resume error:', err));
      }
      return true;
    }

    try {
      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!AudioCtxClass) {
        console.warn('Web Audio API is not supported in this environment');
        return false;
      }

      this.ctx = new AudioCtxClass();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(this.isMuted ? 0 : this.masterVolume, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);
      this.isInitialized = true;
      return true;
    } catch (e) {
      console.warn('Failed to initialize AudioContext:', e);
      return false;
    }
  }

  /**
   * Get active audio context instance
   */
  public getContext(): AudioContext | null {
    if (!this.isInitialized) {
      this.init();
    }
    return this.ctx;
  }

  /**
   * Check if sound engine is currently enabled
   */
  public isEnabled(): boolean {
    return !this.isMuted && this.isInitialized && this.ctx !== null;
  }

  /**
   * Toggle mute state globally
   */
  public toggleMute(): boolean {
    this.isMuted = !this.isMuted;
    if (this.masterGain && this.ctx) {
      const now = this.ctx.currentTime;
      this.masterGain.gain.cancelScheduledValues(now);
      this.masterGain.gain.setValueAtTime(this.masterGain.gain.value, now);
      this.masterGain.gain.linearRampToValueAtTime(this.isMuted ? 0 : this.masterVolume, now + 0.05);
    }
    return !this.isMuted;
  }

  /**
   * Set global master volume (0.0 to 1.0)
   */
  public setVolume(vol: number): void {
    this.masterVolume = Math.max(0, Math.min(1, vol));
    if (this.masterGain && this.ctx && !this.isMuted) {
      const now = this.ctx.currentTime;
      this.masterGain.gain.cancelScheduledValues(now);
      this.masterGain.gain.linearRampToValueAtTime(this.masterVolume, now + 0.05);
    }
  }

  /**
   * Get current master volume
   */
  public getVolume(): number {
    return this.masterVolume;
  }

  /**
   * Get current mute status
   */
  public getMuted(): boolean {
    return this.isMuted;
  }

  /**
   * Trigger procedural sound effect by ID
   */
  public play(sfxId: SoundEffectId): void {
    if (this.isMuted) return;
    if (!this.init()) return;
    if (!this.ctx || !this.masterGain) return;

    try {
      switch (sfxId) {
        case 'ui_click':
          this.synthesizeUiClick();
          break;
        case 'ui_tab':
          this.synthesizeUiTab();
          break;
        case 'step_run':
          this.synthesizeStep();
          break;
        case 'attack_slash':
          this.synthesizeSlash();
          break;
        case 'defend_shield':
          this.synthesizeShieldBlock();
          break;
        case 'jump_ascend':
          this.synthesizeJump();
          break;
        case 'hurt_impact':
          this.synthesizeHurt();
          break;
        case 'torch_light':
          this.synthesizeTorchHum();
          break;
        case 'export_complete':
          this.synthesizeChime();
          break;
        default:
          this.synthesizeUiClick();
      }
    } catch (err) {
      console.warn(`Error synthesizing audio [${sfxId}]:`, err);
    }
  }

  // ==========================================================================
  // Internal Voice Synthesizers
  // ==========================================================================

  /**
   * UI Micro-click (High-frequency transient tick)
   */
  private synthesizeUiClick(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;
    
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(1400, now);
    osc.frequency.exponentialRampToValueAtTime(400, now + 0.04);

    gain.gain.setValueAtTime(0.12, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.04);
  }

  /**
   * Tab Navigation Swoosh (Smooth dual-tone transition)
   */
  private synthesizeUiTab(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;

    const osc = this.ctx.createOscillator();
    const filter = this.ctx.createBiquadFilter();
    const gain = this.ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(280, now);
    osc.frequency.exponentialRampToValueAtTime(620, now + 0.08);

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(1200, now);

    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.08);
  }

  /**
   * Locomotion Footstep (Filtered low thump with rapid decay)
   */
  private synthesizeStep(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;

    // Sub-bass thump
    const osc = this.ctx.createOscillator();
    const oscGain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(120, now);
    osc.frequency.exponentialRampToValueAtTime(35, now + 0.07);

    oscGain.gain.setValueAtTime(0.22, now);
    oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);

    osc.connect(oscGain);
    oscGain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.07);

    // Friction transient
    this.synthesizeNoiseBurst(0.03, 0.06, 800);
  }

  /**
   * Cyberblade Slash / Attack (Sweeping sawtooth with resonant filter)
   */
  private synthesizeSlash(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;

    const osc = this.ctx.createOscillator();
    const filter = this.ctx.createBiquadFilter();
    const gain = this.ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(420, now);
    osc.frequency.exponentialRampToValueAtTime(65, now + 0.18);

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(2400, now);
    filter.frequency.exponentialRampToValueAtTime(300, now + 0.18);
    filter.Q.setValueAtTime(3.5, now);

    gain.gain.setValueAtTime(0.28, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.18);

    // Aerodynamic whoosh noise
    this.synthesizeNoiseBurst(0.14, 0.12, 1800);
  }

  /**
   * Shield Block / Defend (Metallic resonant ping + damping body)
   */
  private synthesizeShieldBlock(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;

    // Metallic ring
    const osc1 = this.ctx.createOscillator();
    const gain1 = this.ctx.createGain();

    osc1.type = 'triangle';
    osc1.frequency.setValueAtTime(680, now);
    osc1.frequency.linearRampToValueAtTime(640, now + 0.28);

    gain1.gain.setValueAtTime(0.25, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.28);

    osc1.connect(gain1);
    gain1.connect(this.masterGain);

    osc1.start(now);
    osc1.stop(now + 0.28);

    // Overtone ping
    const osc2 = this.ctx.createOscillator();
    const gain2 = this.ctx.createGain();

    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(1420, now);
    osc2.frequency.exponentialRampToValueAtTime(900, now + 0.15);

    gain2.gain.setValueAtTime(0.18, now);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

    osc2.connect(gain2);
    gain2.connect(this.masterGain);

    osc2.start(now);
    osc2.stop(now + 0.15);

    // Solid body thud
    const subOsc = this.ctx.createOscillator();
    const subGain = this.ctx.createGain();

    subOsc.type = 'sine';
    subOsc.frequency.setValueAtTime(160, now);
    subOsc.frequency.exponentialRampToValueAtTime(45, now + 0.12);

    subGain.gain.setValueAtTime(0.3, now);
    subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

    subOsc.connect(subGain);
    subGain.connect(this.masterGain);

    subOsc.start(now);
    subOsc.stop(now + 0.12);
  }

  /**
   * Jump Ascend (Smooth frequency lift)
   */
  private synthesizeJump(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(150, now);
    osc.frequency.exponentialRampToValueAtTime(480, now + 0.22);

    gain.gain.setValueAtTime(0.2, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.22);
  }

  /**
   * Hurt / Damage Impact (Distorted pitch dive with heavy noise)
   */
  private synthesizeHurt(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(260, now);
    osc.frequency.exponentialRampToValueAtTime(40, now + 0.24);

    gain.gain.setValueAtTime(0.32, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.24);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.24);

    this.synthesizeNoiseBurst(0.18, 0.22, 900);
  }

  /**
   * Torch Light Dynamic Hum
   */
  private synthesizeTorchHum(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;

    const osc = this.ctx.createOscillator();
    const filter = this.ctx.createBiquadFilter();
    const gain = this.ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(180, now);
    osc.frequency.linearRampToValueAtTime(240, now + 0.15);

    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(400, now);
    filter.Q.setValueAtTime(2.0, now);

    gain.gain.setValueAtTime(0.14, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.15);
  }

  /**
   * Export Complete Chime (Harmonic Major Chord)
   */
  private synthesizeChime(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;

    // Frequencies for C-Major triad: C5 (523.25), E5 (659.25), G5 (783.99), C6 (1046.50)
    const notes = [523.25, 659.25, 783.99, 1046.50];

    notes.forEach((freq, index) => {
      if (!this.ctx || !this.masterGain) return;
      const noteTime = now + index * 0.05;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, noteTime);

      gain.gain.setValueAtTime(0.15, noteTime);
      gain.gain.exponentialRampToValueAtTime(0.001, noteTime + 0.45);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(noteTime);
      osc.stop(noteTime + 0.45);
    });
  }

  /**
   * Helper: Generate bandpass-filtered noise burst for physical texture
   */
  private synthesizeNoiseBurst(durationSec: number, gainLevel: number, centerFreq: number): void {
    if (!this.ctx || !this.masterGain) return;
    const bufferSize = Math.floor(this.ctx.sampleRate * durationSec);
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);

    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }

    const noiseSource = this.ctx.createBufferSource();
    noiseSource.buffer = buffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(centerFreq, this.ctx.currentTime);
    filter.Q.setValueAtTime(1.5, this.ctx.currentTime);

    const gain = this.ctx.createGain();
    const now = this.ctx.currentTime;
    gain.gain.setValueAtTime(gainLevel, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + durationSec);

    noiseSource.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    noiseSource.start(now);
    noiseSource.stop(now + durationSec);
  }
}

// Global singleton instance
export const audio = new SoundEngine();
