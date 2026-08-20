/**
 * Glass Vessel Visualizer & Drinking Animation Component
 * Compliant with Theme Atmosphere System
 */

import { soundFx } from './audio.js';

export class WaterGlass {
  constructor(containerId, options = {}) {
    this.container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    this.volumeMl = options.volumeMl || 250;
    this.theme = options.theme || 'ocean_mist';
    this.onDrinkGlass = options.onDrinkGlass || null;
    this.isDrinking = false;

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

  animateDrink(callback) {
    if (this.isDrinking) return;
    this.isDrinking = true;

    soundFx.playGlassSound();

    const glassFill = this.container.querySelector('.glass-fill');
    if (glassFill) {
      glassFill.style.transition = 'height 0.8s ease-in-out, opacity 0.8s ease-in-out';
      glassFill.style.height = '0%';
      glassFill.style.opacity = '0.3';
    }

    setTimeout(() => {
      if (callback) callback(this.volumeMl);
      
      // Reset glass after animation
      setTimeout(() => {
        if (glassFill) {
          glassFill.style.transition = 'height 0.4s ease-out, opacity 0.4s ease-out';
          glassFill.style.height = '75%';
          glassFill.style.opacity = '1';
        }
        this.isDrinking = false;
      }, 500);
    }, 850);
  }

  render() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="glass-card">
        <div class="glass-left">
          <div class="glass-visual">
            <svg viewBox="0 0 100 120" class="glass-svg" aria-label="Glass of water">
              <defs>
                <linearGradient id="glassLiquidGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="var(--bottle-grad-start, #8ACFDF)" />
                  <stop offset="100%" stop-color="var(--bottle-grad-end, #4C98B1)" />
                </linearGradient>
              </defs>

              <!-- Glass Body outline -->
              <path d="M 25 15 L 75 15 L 68 100 Q 67 105 50 105 Q 33 105 32 100 Z" 
                    fill="var(--color-surface-subtle, rgba(0, 0, 0, 0.04))" 
                    stroke="var(--color-surface-border, rgba(0, 0, 0, 0.15))" 
                    stroke-width="2" />
              
              <!-- Glass Liquid Clip -->
              <clipPath id="glassClip">
                <path d="M 26 17 L 74 17 L 67 99 Q 66 103 50 103 Q 34 103 33 99 Z" />
              </clipPath>

              <!-- Glass Liquid Fill -->
              <g clip-path="url(#glassClip)">
                <rect class="glass-fill" x="20" y="35" width="60" height="70" fill="url(#glassLiquidGrad)" />
              </g>

              <!-- Glass Reflection Accent -->
              <path d="M 30 22 L 28 92 Q 33 96 36 96 L 38 22 Z" fill="rgba(255, 255, 255, 0.3)" />
            </svg>
          </div>
          <div class="glass-details">
            <span class="glass-amount">${this.volumeMl} ml</span>
            <span class="glass-label">Glass of Water</span>
          </div>
        </div>
        <button class="btn btn-secondary glass-action-btn drink-glass-btn">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12l-1.5 15a3 3 0 0 1-3 3h-3a3 3 0 0 1-3-3L6 3z"/></svg>
          <span>Drink Glass</span>
        </button>
      </div>
    `;

    const btn = this.container.querySelector('.drink-glass-btn');
    if (btn) {
      btn.addEventListener('click', () => {
        this.animateDrink((vol) => {
          if (this.onDrinkGlass) this.onDrinkGlass(vol);
        });
      });
    }
  }
}
