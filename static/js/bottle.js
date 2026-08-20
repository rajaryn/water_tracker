import { soundFx } from './audio.js';

export class WaterBottle {
  constructor(containerId, options = {}) {
    this.container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    this.capacityMl = options.capacityMl || 750;
    this.currentVolumeMl = options.currentVolumeMl !== undefined ? options.currentVolumeMl : 750;
    this.theme = options.theme || 'ocean_blue';
    this.onRefill = options.onRefill || null;
    this.onDrink = options.onDrink || null;

    this.render();
  }

  update(currentVolumeMl, capacityMl, theme) {
    const capacityChanged = capacityMl !== undefined && capacityMl !== this.capacityMl;
    const themeChanged = theme !== undefined && theme !== this.theme;

    if (capacityMl) this.capacityMl = capacityMl;
    if (currentVolumeMl !== undefined) this.currentVolumeMl = Math.max(0, Math.min(currentVolumeMl, this.capacityMl));
    if (theme) this.theme = theme;

    if (capacityChanged || themeChanged) {
      this.render();
    } else {
      this.updateLiquidLevel();
    }
  }

  getFillPercentage() {
    if (this.capacityMl <= 0) return 0;
    return Math.round((this.currentVolumeMl / this.capacityMl) * 100);
  }

  getThemeColors() {
    const themes = {
      ocean_mist: {
        liquidGradStart: '#8ACFDF',
        liquidGradEnd: '#4C98B1',
        waveColor: 'rgba(138, 207, 223, 0.55)',
        glow: 'rgba(103, 175, 196, 0.2)'
      },
      clear_blue: {
        liquidGradStart: '#8ACFDF',
        liquidGradEnd: '#4C98B1',
        waveColor: 'rgba(138, 207, 223, 0.55)',
        glow: 'rgba(103, 175, 196, 0.2)'
      },
      ocean_blue: {
        liquidGradStart: '#8ACFDF',
        liquidGradEnd: '#4C98B1',
        waveColor: 'rgba(138, 207, 223, 0.55)',
        glow: 'rgba(103, 175, 196, 0.2)'
      },
      sage_morning: {
        liquidGradStart: '#A4D1C0',
        liquidGradEnd: '#5E9B89',
        waveColor: 'rgba(164, 209, 192, 0.55)',
        glow: 'rgba(112, 169, 154, 0.2)'
      },
      mint_glass: {
        liquidGradStart: '#A4D1C0',
        liquidGradEnd: '#5E9B89',
        waveColor: 'rgba(164, 209, 192, 0.55)',
        glow: 'rgba(112, 169, 154, 0.2)'
      },
      rose_water: {
        liquidGradStart: '#E7B9BF',
        liquidGradEnd: '#B87380',
        waveColor: 'rgba(231, 185, 191, 0.55)',
        glow: 'rgba(200, 137, 148, 0.2)'
      },
      rose_glass: {
        liquidGradStart: '#E7B9BF',
        liquidGradEnd: '#B87380',
        waveColor: 'rgba(231, 185, 191, 0.55)',
        glow: 'rgba(200, 137, 148, 0.2)'
      },
      warm_sand: {
        liquidGradStart: '#9BC6CC',
        liquidGradEnd: '#578B96',
        waveColor: 'rgba(155, 198, 204, 0.55)',
        glow: 'rgba(103, 151, 160, 0.2)'
      },
      midnight_pool: {
        liquidGradStart: '#82C7D6',
        liquidGradEnd: '#438A9F',
        waveColor: 'rgba(130, 199, 214, 0.55)',
        glow: 'rgba(118, 191, 208, 0.2)'
      },
      midnight_glass: {
        liquidGradStart: '#82C7D6',
        liquidGradEnd: '#438A9F',
        waveColor: 'rgba(130, 199, 214, 0.55)',
        glow: 'rgba(118, 191, 208, 0.2)'
      }
    };
    return themes[this.theme] || themes.ocean_mist;
  }

  render() {
    if (!this.container) return;

    const colors = this.getThemeColors();
    const fillPct = this.getFillPercentage();
    
    // Y-coordinate mapping for liquid in bottle SVG (bottle body spans Y=100 to Y=320)
    // 0% fill -> Y=320, 100% fill -> Y=110
    const bodyHeight = 210;
    const minY = 110;
    const maxY = 320;
    const liquidY = maxY - (bodyHeight * (fillPct / 100));
    const isEmp = (fillPct === 0);

    this.container.innerHTML = `
      <div class="bottle-wrapper ${isEmp ? 'empty-bottle' : ''}">
        <svg viewBox="0 0 200 400" class="bottle-svg" aria-label="Physical Water Bottle Visualization">
          <defs>
            <linearGradient id="liquidGrad-${this.theme}" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="${colors.liquidGradStart}" />
              <stop offset="100%" stop-color="${colors.liquidGradEnd}" />
            </linearGradient>

            <filter id="bottleGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="${colors.glow}" />
            </filter>

            <!-- Bottle Body Shape Clip Path -->
            <clipPath id="bottleBodyClip">
              <path d="
                M 85 45 
                L 115 45 
                Q 120 45 120 50 
                L 120 70 
                Q 120 90 145 105 
                Q 155 112 155 125 
                L 155 315 
                Q 155 335 135 335 
                L 65 335 
                Q 45 335 45 315 
                L 45 125 
                Q 45 112 55 105 
                Q 80 90 80 70 
                L 80 50 
                Q 80 45 85 45 Z" />
            </clipPath>
          </defs>

          <!-- Bottle Shadow & Background Shell -->
          <path d="
            M 85 45 L 115 45 Q 120 45 120 50 L 120 70 Q 120 90 145 105 Q 155 112 155 125 L 155 315 Q 155 335 135 335 L 65 335 Q 45 335 45 315 L 45 125 Q 45 112 55 105 Q 80 90 80 70 L 80 50 Q 80 45 85 45 Z" 
            fill="rgba(255, 255, 255, 0.08)" 
            stroke="rgba(255, 255, 255, 0.25)" 
            stroke-width="2.5" 
            filter="url(#bottleGlow)" />

          <!-- Liquid Container Group clipped by Bottle Body -->
          <g clip-path="url(#bottleBodyClip)">
            <!-- Animated Liquid Fill Rect -->
            <rect id="liquidRect" x="40" y="${liquidY}" width="120" height="${maxY - liquidY + 20}" 
                  fill="url(#liquidGrad-${this.theme})" class="liquid-rect" />

            <!-- Wave overlay SVG -->
            <path id="wavePath" class="wave-animation" 
                  d="M 40 ${liquidY} Q 70 ${liquidY - 6} 100 ${liquidY} T 160 ${liquidY} L 160 340 L 40 340 Z" 
                  fill="${colors.waveColor}" />
          </g>

          <!-- Stainless / Glass Cap -->
          <rect x="80" y="25" width="40" height="20" rx="4" fill="#94a3b8" stroke="#64748b" stroke-width="1.5" />
          <rect x="85" y="20" width="30" height="6" rx="2" fill="#cbd5e1" />

          <!-- Measurement Scale Markings -->
          <line x1="150" y1="140" x2="142" y2="140" stroke="rgba(255,255,255,0.4)" stroke-width="1.5" />
          <text x="138" y="143" font-size="9" fill="rgba(255,255,255,0.6)" text-anchor="end">${this.capacityMl}ml</text>

          <line x1="150" y1="220" x2="144" y2="220" stroke="rgba(255,255,255,0.3)" stroke-width="1.5" />
          <text x="140" y="223" font-size="9" fill="rgba(255,255,255,0.5)" text-anchor="end">${Math.round(this.capacityMl / 2)}ml</text>

          <line x1="150" y1="300" x2="144" y2="300" stroke="rgba(255,255,255,0.3)" stroke-width="1.5" />

          <!-- Glass Highlight Overlay reflection -->
          <path d="M 52 130 L 52 300 Q 52 320 62 320 L 58 320 Q 48 320 48 300 L 48 130 Z" fill="rgba(255,255,255,0.18)" />
        </svg>

        <div class="bottle-status-badge">
          <span class="bottle-volume-value">${this.currentVolumeMl}</span>
          <span class="bottle-volume-unit"> / ${this.capacityMl} ml</span>
          <div class="bottle-state-label ${isEmp ? 'tap-hint' : ''}">${this.getStatusText()}</div>
        </div>
      </div>
    `;

    const wrapper = this.container.querySelector('.bottle-wrapper');
    if (wrapper) {
      wrapper.addEventListener('click', () => {
        // Allow tap-to-refill when empty or anytime user taps physical bottle
        if (this.currentVolumeMl === 0 || this.currentVolumeMl < this.capacityMl) {
          if (this.onRefill) this.onRefill();
        }
      });
    }
  }

  getStatusText() {
    const pct = this.getFillPercentage();
    if (pct >= 90) return 'Bottle Full';
    if (pct >= 50) return 'Half Full';
    if (pct >= 15) return 'Low Water';
    if (pct > 0) return 'Almost Empty';
    return 'Empty - Tap Bottle to Refill';
  }

  updateLiquidLevel() {
    const fillPct = this.getFillPercentage();
    const bodyHeight = 210;
    const maxY = 320;
    const liquidY = maxY - (bodyHeight * (fillPct / 100));

    const liquidRect = this.container.querySelector('#liquidRect');
    const wavePath = this.container.querySelector('#wavePath');
    const volumeVal = this.container.querySelector('.bottle-volume-value');
    const volumeUnit = this.container.querySelector('.bottle-volume-unit');
    const stateLabel = this.container.querySelector('.bottle-state-label');
    const wrapper = this.container.querySelector('.bottle-wrapper');

    if (liquidRect) {
      liquidRect.setAttribute('y', liquidY);
      liquidRect.setAttribute('height', maxY - liquidY + 20);
    }
    if (wavePath) {
      wavePath.setAttribute('d', `M 40 ${liquidY} Q 70 ${liquidY - 6} 100 ${liquidY} T 160 ${liquidY} L 160 340 L 40 340 Z`);
    }
    if (volumeVal) volumeVal.textContent = this.currentVolumeMl;
    if (volumeUnit) volumeUnit.textContent = ` / ${this.capacityMl} ml`;
    if (stateLabel) {
      stateLabel.textContent = this.getStatusText();
      if (fillPct === 0) {
        stateLabel.classList.add('tap-hint');
      } else {
        stateLabel.classList.remove('tap-hint');
      }
    }

    if (wrapper) {
      if (fillPct === 0) {
        wrapper.classList.add('empty-bottle');
      } else {
        wrapper.classList.remove('empty-bottle');
      }
    }
  }
}
