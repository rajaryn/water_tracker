/**
 * Glass Vessel Visualizer & Drinking Animation Component
 */

import { soundFx } from './audio.js';

export class WaterGlass {
  constructor(containerId, options = {}) {
    this.container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    this.volumeMl = options.volumeMl || 250;
    this.onDrinkGlass = options.onDrinkGlass || null;
    this.isDrinking = false;

    this.render();
  }

  setVolume(volumeMl) {
    this.volumeMl = volumeMl;
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
        <div class="glass-visual">
          <svg viewBox="0 0 100 120" class="glass-svg">
            <!-- Glass Body outline -->
            <path d="M 25 15 L 75 15 L 68 100 Q 67 105 50 105 Q 33 105 32 100 Z" 
                  fill="rgba(255, 255, 255, 0.08)" stroke="rgba(255, 255, 255, 0.3)" stroke-width="2" />
            
            <!-- Glass Liquid Clip -->
            <clipPath id="glassClip">
              <path d="M 26 17 L 74 17 L 67 99 Q 66 103 50 103 Q 34 103 33 99 Z" />
            </clipPath>

            <!-- Glass Liquid Fill -->
            <g clip-path="url(#glassClip)">
              <rect class="glass-fill" x="20" y="35" width="60" height="70" fill="#38bdf8" />
            </g>
          </svg>
        </div>
        <div class="glass-details">
          <span class="glass-amount">${this.volumeMl} ml</span>
          <span class="glass-label">Glass of Water (Independent of Bottle)</span>
        </div>
        <button class="btn btn-secondary drink-glass-btn">
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
