/**
 * Water Gulp Visualizer, Drop Animation & Web Audio Sound Component
 * Compliant with Theme Atmosphere System
 */

export class WaterGulp {
  constructor(containerId, options = {}) {
    this.container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    this.volumeMl = options.volumeMl || 50;
    this.theme = options.theme || 'ocean_mist';
    this.onTakeGulp = options.onTakeGulp || null;
    this.isDrinking = false;
    this.audioCtx = null;

    this.render();
  }

  setVolume(volumeMl) {
    this.volumeMl = volumeMl;
    this.render();
  }

  updateTheme(theme) {
    this.theme = theme;
    this.render();
  }

  initAudio() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.audioCtx = new AudioContext();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  playGulpSound() {
    try {
      this.initAudio();
      if (!this.audioCtx) return;

      const now = this.audioCtx.currentTime;

      // 1. Water Drop / Gulp Resonance Pitch Oscillator
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'sine';
      // Pitch bend down simulating gulp swallowing sound (380 Hz -> 140 Hz)
      osc.frequency.setValueAtTime(380, now);
      osc.frequency.exponentialRampToValueAtTime(140, now + 0.18);

      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(now);
      osc.stop(now + 0.2);

      // 2. Secondary soft bubble pop (after 120ms)
      const osc2 = this.audioCtx.createOscillator();
      const gain2 = this.audioCtx.createGain();

      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(450, now + 0.12);
      osc2.frequency.exponentialRampToValueAtTime(620, now + 0.22);

      gain2.gain.setValueAtTime(0.01, now + 0.12);
      gain2.gain.linearRampToValueAtTime(0.2, now + 0.15);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.26);

      osc2.connect(gain2);
      gain2.connect(this.audioCtx.destination);

      osc2.start(now + 0.12);
      osc2.stop(now + 0.26);
    } catch (e) {
      console.warn('[Audio] Gulp sound playback failed:', e);
    }
  }

  animateGulp(callback) {
    if (this.isDrinking) return;
    this.isDrinking = true;

    this.playGulpSound();

    const drop = this.container.querySelector('.gulp-drop');
    const ripple = this.container.querySelector('.gulp-ripple');

    if (drop) drop.classList.add('animating-drop');
    if (ripple) ripple.classList.add('animating-ripple');

    setTimeout(() => {
      if (callback) callback(this.volumeMl);

      setTimeout(() => {
        if (drop) drop.classList.remove('animating-drop');
        if (ripple) ripple.classList.remove('animating-ripple');
        this.isDrinking = false;
      }, 350);
    }, 450);
  }

  render() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="glass-card gulp-card">
        <div class="glass-left">
          <div class="glass-visual gulp-visual">
            <svg viewBox="0 0 100 120" class="glass-svg gulp-svg" aria-label="Sip of water">
              <defs>
                <linearGradient id="gulpDropGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="var(--bottle-grad-start, #8ACFDF)" />
                  <stop offset="100%" stop-color="var(--bottle-grad-end, #4C98B1)" />
                </linearGradient>
              </defs>

              <!-- Splash Ripple Circle -->
              <circle class="gulp-ripple" cx="50" cy="85" r="8" fill="none" stroke="var(--color-primary, #67AFC4)" stroke-width="2" opacity="0" />

              <!-- Water Drop Graphic -->
              <g class="gulp-drop">
                <path d="M 50 20 Q 30 55 30 70 A 20 20 0 0 0 70 70 Q 70 55 50 20 Z" 
                      fill="url(#gulpDropGrad)" />
                <ellipse cx="44" cy="55" rx="4" ry="8" fill="rgba(255,255,255,0.4)" transform="rotate(-20 44 55)" />
              </g>
            </svg>
          </div>
          <div class="glass-details">
            <span class="glass-amount">${this.volumeMl} ml</span>
            <span class="glass-label">Sip of Water</span>
          </div>
        </div>
        <button class="btn btn-secondary glass-action-btn take-gulp-btn">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
          <span>Take a Gulp</span>
        </button>
      </div>
    `;

    const btn = this.container.querySelector('.take-gulp-btn');
    if (btn) {
      btn.addEventListener('click', () => {
        this.animateGulp((vol) => {
          if (this.onTakeGulp) this.onTakeGulp(vol);
        });
      });
    }
  }
}
