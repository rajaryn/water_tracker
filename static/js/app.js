/**
 * Hydration Tracker PWA Main Application Coordinator
 */

import { initDB, getLocalData, saveLocalData, addToSyncQueue, getSyncQueue, clearSyncQueue, deleteLocalData } from './db.js';
import { calculateHydrationTarget, CALCULATION_VERSION, RESEARCH_BASIS } from './recommendation.js';
import { WaterBottle } from './bottle.js';
import { WaterGlass } from './glass.js';
import { WaterGulp } from './gulp.js';
import { NotificationEngine } from './notifications.js';

class App {
  constructor() {
    this.user = null;
    this.bottle = null;
    this.target = null;
    this.todayEvents = [];
    this.bottleWidget = null;
    this.glassWidget = null;
    this.gulpWidget = null;
    this.notificationEngine = new NotificationEngine();

    this.init();
  }

  async init() {
    await initDB();
    await this.registerServiceWorker();
    await this.loadState();

    this.setupEventListeners();
    this.setupNetworkSync();

    if (!this.user || !this.user.completed_onboarding) {
      this.showScreen('onboarding');
      this.initOnboarding();
    } else {
      this.showScreen('home');
      this.renderHomeScreen();
    }
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('[App] Service Worker registered:', registration.scope);

        navigator.serviceWorker.addEventListener('message', (event) => {
          if (event.data && event.data.type === 'TRIGGER_SYNC') {
            this.syncOfflineQueue();
          }
        });
      } catch (err) {
        console.warn('[App] SW registration failed:', err);
      }
    }
  }

  async loadState() {
    const user = await getLocalData('profile', 'current_user');
    const bottle = await getLocalData('bottle', 'current_bottle');
    const target = await getLocalData('hydration_target', 'current_target');

    if (user) this.user = user;
    if (bottle) this.bottle = bottle;
    if (target) this.target = target;

    // Load today's events from IndexedDB
    const allDrinks = await getLocalData('drink_events') || [];
    const todayStr = new Date().toISOString().split('T')[0];
    this.todayEvents = allDrinks.filter(d => d.timestamp && d.timestamp.startsWith(todayStr));
  }

  setupEventListeners() {
    // Bottom Navigation
    document.querySelectorAll('.nav-item').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const targetScreen = btn.dataset.screen;
        if (targetScreen) {
          this.showScreen(targetScreen);
        }
      });
    });

    // Quick Drink Buttons
    document.querySelectorAll('.btn-drink').forEach(btn => {
      btn.addEventListener('click', () => {
        const amount = parseInt(btn.dataset.amount, 10);
        if (amount) this.logDrink(amount, 'quick_add');
      });
    });

    // Gulp Drink Button
    const gulpBtn = document.getElementById('gulpDrinkBtn');
    if (gulpBtn) {
      gulpBtn.addEventListener('click', () => {
        this.logDrink(50, 'gulp');
      });
    }

    // Custom Drink Button
    const customBtn = document.getElementById('customDrinkBtn');
    if (customBtn) {
      customBtn.addEventListener('click', () => {
        const input = prompt('Enter water amount in ml:', '350');
        if (input) {
          const val = parseInt(input, 10);
          if (val > 0) this.logDrink(val, 'custom');
        }
      });
    }

    // Refill Bottle Button
    const refillBtn = document.getElementById('refillBottleBtn');
    if (refillBtn) {
      refillBtn.addEventListener('click', () => this.logRefill());
    }

    // Notification Opt-in Prompt Button
    const notifPromptBtn = document.getElementById('enableNotifBtn');
    if (notifPromptBtn) {
      notifPromptBtn.addEventListener('click', async () => {
        const granted = await this.notificationEngine.requestPermission();
        if (granted) {
          alert('Notifications enabled! Gentle reminders will be sent when you fall behind your target pacing.');
          document.getElementById('notifPromptBanner').style.display = 'none';
        }
      });
    }
  }

  showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const targetEl = document.getElementById(`screen-${screenId}`);
    if (targetEl) targetEl.classList.add('active');

    const navEl = document.querySelector(`.nav-item[data-screen="${screenId}"]`);
    if (navEl) navEl.classList.add('active');

    // Trigger screen-specific rendering
    if (screenId === 'home') this.renderHomeScreen();
    if (screenId === 'history') this.renderHistoryScreen();
    if (screenId === 'stats') this.renderStatsScreen();
    if (screenId === 'methodology') this.renderMethodologyScreen();
    if (screenId === 'settings') this.renderSettingsScreen();
  }

  // --- Onboarding Flow ---
  initOnboarding() {
    let step = 1;
    const onboardState = {
      age: 28,
      sex: 'female',
      activity_level: 'moderately_active',
      environment: 'indoors',
      pregnancy_status: 'neither',
      bottle_capacity_ml: 750
    };

    const renderStep = () => {
      const card = document.getElementById('onboardingCardContainer');
      if (!card) return;

      if (step === 1) {
        card.innerHTML = `
          <div class="onboarding-card">
            <h2 class="onboarding-title">Meet your hydration companion.</h2>
            <p class="onboarding-subtitle">
              Track your water intake like bringing a physical water bottle to life. Designed for adult health & research-based targets.
            </p>
            <button class="btn btn-primary" id="onboardNext1" style="width:100%">
              <span>Get Started</span>
              <svg class="btn-icon-right" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
          </div>
        `;
        document.getElementById('onboardNext1').onclick = () => { step = 2; renderStep(); };
      } else if (step === 2) {
        card.innerHTML = `
          <div class="onboarding-card">
            <h2 class="onboarding-title">Age & Sex</h2>
            <p class="onboarding-subtitle">Research reference values adapt to physiological water needs.</p>
            
            <div class="form-group">
              <label class="form-label">How old are you? (18+)</label>
              <input type="number" id="onboardAge" class="input-control" value="${onboardState.age}" min="18" max="100" />
            </div>

            <div class="form-group">
              <label class="form-label">What is your biological sex?</label>
              <div class="option-cards-grid">
                <div class="option-card ${onboardState.sex === 'male' ? 'selected' : ''}" data-val="male">
                  <div class="option-card-title">Male</div>
                  <div class="option-card-desc">IOM 3.7L Ref</div>
                </div>
                <div class="option-card ${onboardState.sex === 'female' ? 'selected' : ''}" data-val="female">
                  <div class="option-card-title">Female</div>
                  <div class="option-card-desc">IOM 2.7L Ref</div>
                </div>
              </div>
            </div>

            <button class="btn btn-primary" id="onboardNext2" style="width:100%">
              <span>Continue</span>
              <svg class="btn-icon-right" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
          </div>
        `;

        card.querySelectorAll('.option-card').forEach(opt => {
          opt.onclick = () => {
            card.querySelectorAll('.option-card').forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            onboardState.sex = opt.dataset.val;
          };
        });

        document.getElementById('onboardNext2').onclick = () => {
          const ageInput = parseInt(document.getElementById('onboardAge').value, 10);
          onboardState.age = ageInput || 25;
          step = 3;
          renderStep();
        };
      } else if (step === 3) {
        card.innerHTML = `
          <div class="onboarding-card">
            <h2 class="onboarding-title">Activity & Environment</h2>
            <p class="onboarding-subtitle">Physical movement and outdoor exposure increase fluid loss.</p>

            <div class="form-group">
              <label class="form-label">Daily Activity</label>
              <select id="onboardActivity" class="input-control">
                <option value="sedentary">Mostly Sedentary (Sitting, little exercise)</option>
                <option value="lightly_active" selected>Lightly Active (Walking, occasional movement)</option>
                <option value="moderately_active">Moderately Active (Regular exercise)</option>
                <option value="highly_active">Highly Active (Intense workouts / physical labor)</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Typical Day Environment</label>
              <select id="onboardEnv" class="input-control">
                <option value="indoors" selected>Mostly Indoors (AC / Heated)</option>
                <option value="mixed">Mixed Indoor & Outdoor</option>
                <option value="outdoors">Mostly Outdoors (Sun / Heat)</option>
              </select>
            </div>

            <button class="btn btn-primary" id="onboardNext3" style="width:100%">
              <span>Bottle Setup</span>
              <svg class="btn-icon-right" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
          </div>
        `;

        document.getElementById('onboardNext3').onclick = () => {
          onboardState.activity_level = document.getElementById('onboardActivity').value;
          onboardState.environment = document.getElementById('onboardEnv').value;
          step = 4;
          renderStep();
        };
      } else if (step === 4) {
        const isCustomInitially = ![500, 750, 1000, 1500].includes(onboardState.bottle_capacity_ml);
        card.innerHTML = `
          <div class="onboarding-card">
            <h2 class="onboarding-title">Your Water Bottle</h2>
            <p class="onboarding-subtitle">How much water does your physical bottle hold?</p>

            <div class="option-cards-grid bottle-cap-grid">
              <div class="option-card ${onboardState.bottle_capacity_ml === 500 && !isCustomInitially ? 'selected' : ''}" data-cap="500">500 ml</div>
              <div class="option-card ${onboardState.bottle_capacity_ml === 750 && !isCustomInitially ? 'selected' : ''}" data-cap="750">750 ml</div>
              <div class="option-card ${onboardState.bottle_capacity_ml === 1000 && !isCustomInitially ? 'selected' : ''}" data-cap="1000">1.0 L (1000ml)</div>
              <div class="option-card ${onboardState.bottle_capacity_ml === 1500 && !isCustomInitially ? 'selected' : ''}" data-cap="1500">1.5 L (1500ml)</div>
              <div class="option-card bottle-cap-custom-card ${isCustomInitially ? 'selected' : ''}" data-cap="custom">
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                <span>Custom Quantity</span>
              </div>
            </div>

            <div id="customBottleWrapper" class="form-group" style="display: ${isCustomInitially ? 'block' : 'none'}; margin-bottom: 20px;">
              <label class="form-label" for="onboardCustomCap">Enter Custom Capacity (ml)</label>
              <div class="custom-cap-input-group">
                <input type="number" id="onboardCustomCap" class="input-control" placeholder="e.g. 400" min="50" max="10000" step="10" value="${isCustomInitially ? onboardState.bottle_capacity_ml : ''}" />
                <span class="custom-cap-unit">ml</span>
              </div>
            </div>

            <button class="btn btn-primary" id="onboardFinish" style="width:100%">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              <span>Complete Setup</span>
            </button>
          </div>
        `;

        let isCustom = isCustomInitially;
        const customWrapper = document.getElementById('customBottleWrapper');
        const customInput = document.getElementById('onboardCustomCap');

        card.querySelectorAll('.bottle-cap-grid .option-card').forEach(opt => {
          opt.onclick = () => {
            card.querySelectorAll('.bottle-cap-grid .option-card').forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');

            if (opt.dataset.cap === 'custom') {
              isCustom = true;
              if (customWrapper) customWrapper.style.display = 'block';
              if (customInput) {
                customInput.focus();
                const val = parseInt(customInput.value, 10);
                if (val > 0) onboardState.bottle_capacity_ml = val;
              }
            } else {
              isCustom = false;
              if (customWrapper) customWrapper.style.display = 'none';
              onboardState.bottle_capacity_ml = parseInt(opt.dataset.cap, 10);
            }
          };
        });

        if (customInput) {
          customInput.oninput = () => {
            const val = parseInt(customInput.value, 10);
            if (val > 0) {
              onboardState.bottle_capacity_ml = val;
            }
          };
        }

        document.getElementById('onboardFinish').onclick = async () => {
          if (isCustom) {
            const val = parseInt(customInput.value, 10);
            if (!val || val <= 0) {
              alert('Please enter a valid bottle capacity in ml (e.g. 400 ml).');
              customInput.focus();
              return;
            }
            if (val > 10000) {
              alert('Please enter a realistic bottle capacity (up to 10,000 ml).');
              customInput.focus();
              return;
            }
            onboardState.bottle_capacity_ml = val;
          }
          await this.completeOnboarding(onboardState);
        };
      }
    };

    renderStep();
  }

  async completeOnboarding(state) {
    const userId = 'usr_' + Date.now();
    const recommendation = calculateHydrationTarget(state);

    this.user = {
      id: userId,
      completed_onboarding: true,
      ...state
    };
    this.bottle = {
      id: 'btl_' + Date.now(),
      user_id: userId,
      capacity_ml: state.bottle_capacity_ml,
      current_volume_ml: state.bottle_capacity_ml,
      name: 'My Water Bottle',
      theme: 'ocean_blue'
    };
    this.target = {
      id: 'tgt_' + Date.now(),
      user_id: userId,
      target_ml: recommendation.target_ml,
      calculation_version: CALCULATION_VERSION,
      research_basis: RESEARCH_BASIS,
      profile_snapshot: recommendation.profile_snapshot
    };

    await saveLocalData('profile', { id: 'current_user', ...this.user });
    await saveLocalData('bottle', { id: 'current_bottle', ...this.bottle });
    await saveLocalData('hydration_target', { id: 'current_target', ...this.target });

    // Sync with server if online
    this.syncOfflineQueue();

    this.showScreen('home');
    this.renderHomeScreen();
  }

  // --- Home Screen & Core Interactions ---
  renderHomeScreen() {
    if (!this.user || !this.bottle || !this.target) return;

    // Render Hero Water Bottle Widget
    if (!this.bottleWidget) {
      this.bottleWidget = new WaterBottle('bottleWidgetContainer', {
        capacityMl: this.bottle.capacity_ml,
        currentVolumeMl: this.bottle.current_volume_ml,
        theme: this.bottle.theme,
        onRefill: () => this.logRefill()
      });
    } else {
      this.bottleWidget.update(this.bottle.current_volume_ml, this.bottle.capacity_ml, this.bottle.theme);
    }

    // Render Gulp Vessel Widget
    if (!this.gulpWidget) {
      this.gulpWidget = new WaterGulp('gulpWidgetContainer', {
        volumeMl: 50,
        onTakeGulp: (vol) => this.logDrink(vol, 'gulp')
      });
    }

    // Render Secondary Glass Vessel Widget
    if (!this.glassWidget) {
      this.glassWidget = new WaterGlass('glassWidgetContainer', {
        volumeMl: 250,
        onDrinkGlass: (vol) => this.logDrink(vol, 'glass')
      });
    }

    // Calculate Daily Consumption Total
    const consumedTodayMl = this.todayEvents.reduce((sum, ev) => sum + ev.amount_ml, 0);
    const targetMl = this.target.target_ml || 2500;
    const progressPct = Math.min(100, Math.round((consumedTodayMl / targetMl) * 100));

    // Update Text & Linear Progress Elements
    const consumedEl = document.getElementById('homeConsumedVal');
    const targetEl = document.getElementById('homeTargetVal');
    const progressBarEl = document.getElementById('homeProgressBar');

    if (consumedEl) consumedEl.textContent = (consumedTodayMl / 1000).toFixed(2) + ' L';
    if (targetEl) targetEl.textContent = (targetMl / 1000).toFixed(2) + ' L';
    if (progressBarEl) progressBarEl.style.width = `${progressPct}%`;

    // Evaluate Notification Pacing
    this.notificationEngine.evaluateAndNotify({
      consumedMl: consumedTodayMl,
      targetMl: targetMl,
      bottleVolumeMl: this.bottle.current_volume_ml,
      bottleCapacityMl: this.bottle.capacity_ml
    });
  }

  async logDrink(amountMl, source = 'quick_add') {
    if (!this.bottle) return;

    let actualDrinkMl = amountMl;
    const isExternalVessel = (source === 'glass' || source === 'gulp' || source === 'external');

    // Only check & decrement physical bottle volume if drinking directly from bottle!
    if (!isExternalVessel) {
      if (this.bottle.current_volume_ml < amountMl) {
        if (this.bottle.current_volume_ml === 0) {
          alert('Your physical bottle is empty! Tap the bottle or "Refill Bottle" first.');
          return;
        }
        const choice = confirm(`Your bottle only has ${this.bottle.current_volume_ml} ml left. Log ${this.bottle.current_volume_ml} ml and prompt refill?`);
        if (choice) {
          actualDrinkMl = this.bottle.current_volume_ml;
        } else {
          return;
        }
      }

      this.bottle.current_volume_ml = Math.max(0, this.bottle.current_volume_ml - actualDrinkMl);
      await saveLocalData('bottle', { id: 'current_bottle', ...this.bottle });
    }

    // Record Drink Event
    const drinkEvent = {
      id: 'drk_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
      user_id: this.user.id,
      bottle_id: this.bottle.id,
      amount_ml: actualDrinkMl,
      source: source,
      timestamp: new Date().toISOString()
    };

    await saveLocalData('drink_events', drinkEvent);
    await addToSyncQueue({ type: 'drink_event', payload: drinkEvent });

    this.todayEvents.push(drinkEvent);

    // Haptic feedback if supported
    if ('vibrate' in navigator) navigator.vibrate(40);

    this.renderHomeScreen();
    this.syncOfflineQueue();
  }

  async logRefill() {
    if (!this.bottle) return;

    const amountAdded = this.bottle.capacity_ml - this.bottle.current_volume_ml;
    this.bottle.current_volume_ml = this.bottle.capacity_ml;
    await saveLocalData('bottle', { id: 'current_bottle', ...this.bottle });

    const refillEvent = {
      id: 'rfl_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
      user_id: this.user.id,
      bottle_id: this.bottle.id,
      amount_added_ml: amountAdded,
      timestamp: new Date().toISOString()
    };

    await saveLocalData('refill_events', refillEvent);
    await addToSyncQueue({ type: 'refill_event', payload: refillEvent });

    if ('vibrate' in navigator) navigator.vibrate([30, 50, 30]);

    this.renderHomeScreen();
    this.syncOfflineQueue();
  }

  // --- History Screen ---
  async renderHistoryScreen() {
    const container = document.getElementById('historyContainer');
    if (!container) return;

    const allDrinks = await getLocalData('drink_events') || [];
    const allRefills = await getLocalData('refill_events') || [];

    if (allDrinks.length === 0 && allRefills.length === 0) {
      container.innerHTML = `<div class="history-day-card" style="text-align:center;">No drinking events logged yet today!</div>`;
      return;
    }

    // Group events by ISO date
    const grouped = {};
    allDrinks.forEach(d => {
      const dateKey = d.timestamp ? d.timestamp.split('T')[0] : 'Today';
      if (!grouped[dateKey]) grouped[dateKey] = { totalMl: 0, items: [] };
      grouped[dateKey].totalMl += d.amount_ml;
      grouped[dateKey].items.push({ ...d, type: 'drink' });
    });

    allRefills.forEach(r => {
      const dateKey = r.timestamp ? r.timestamp.split('T')[0] : 'Today';
      if (!grouped[dateKey]) grouped[dateKey] = { totalMl: 0, items: [] };
      grouped[dateKey].items.push({ ...r, type: 'refill' });
    });

    let html = '';
    const sortedDates = Object.keys(grouped).sort().reverse();

    sortedDates.forEach(dateKey => {
      const group = grouped[dateKey];
      group.items.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

      html += `
        <div class="history-day-card">
          <div class="history-day-header">
            <span class="history-date">${dateKey}</span>
            <span class="history-day-total">Total: ${group.totalMl} ml</span>
          </div>
          <div class="history-items-list">
            ${group.items.map(item => `
              <div class="history-item">
                <div style="display:flex; align-items:center;">
                  <span class="history-item-icon">
                    ${item.type === 'drink' 
                      ? '<svg class="history-svg-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>' 
                      : '<svg class="history-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>'}
                  </span>
                  <span>${item.type === 'drink' ? `Drank ${item.amount_ml} ml` : `Refilled bottle (+${item.amount_added_ml} ml)`}</span>
                </div>
                <span style="color:var(--color-text-subtle); font-size:0.8rem;">
                  ${item.timestamp ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                </span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  }

  // --- Statistics Screen ---
  async renderStatsScreen() {
    const container = document.getElementById('statsContainer');
    if (!container) return;

    const allDrinks = await getLocalData('drink_events') || [];
    const targetMl = this.target ? this.target.target_ml : 2500;

    // Group by last 7 days
    const today = new Date();
    const chartBars = [];
    let last7Total = 0;
    let daysMetTarget = 0;

    for (let i = 6; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      const dateStr = d.toISOString().split('T')[0];
      const dayName = d.toLocaleDateString('en-US', { weekday: 'short' });

      const dayConsumed = allDrinks
        .filter(ev => ev.timestamp && ev.timestamp.startsWith(dateStr))
        .reduce((sum, ev) => sum + ev.amount_ml, 0);

      last7Total += dayConsumed;
      if (dayConsumed >= targetMl) daysMetTarget++;

      const fillPct = Math.min(100, Math.round((dayConsumed / targetMl) * 100));

      chartBars.push({
        dayName,
        consumed: dayConsumed,
        fillPct,
        reached: dayConsumed >= targetMl
      });
    }

    const avg7Days = Math.round(last7Total / 7);
    const completionPct = Math.round((daysMetTarget / 7) * 100);

    const consumedTodayMl = this.todayEvents.reduce((sum, ev) => sum + ev.amount_ml, 0);
    const todayPct = Math.min(100, Math.round((consumedTodayMl / targetMl) * 100));
    const circumference = 2 * Math.PI * 24;
    const strokeOffset = circumference - (circumference * (todayPct / 100));

    container.innerHTML = `
      <div class="progress-ring-container" style="margin-bottom:20px;">
        <svg class="ring-svg" viewBox="0 0 60 60">
          <circle class="ring-bg" cx="30" cy="30" r="24" stroke-width="6" fill="none" />
          <circle class="ring-fill" cx="30" cy="30" r="24" stroke-width="6" fill="none" stroke-linecap="round"
                  style="stroke-dasharray:${circumference}; stroke-dashoffset:${strokeOffset};" />
        </svg>
        <div class="ring-info">
          <div class="ring-pct-title">${todayPct}%</div>
          <div class="ring-subtitle">Today's Target Progress</div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-metric-card">
          <div class="stat-value">${(avg7Days / 1000).toFixed(2)} L</div>
          <div class="stat-label">7-Day Average</div>
        </div>
        <div class="stat-metric-card">
          <div class="stat-value">${completionPct}%</div>
          <div class="stat-label">Goal Completion Rate</div>
        </div>
      </div>

      <div class="bar-chart-container">
        <h3 style="font-size:0.95rem; font-weight:700; margin-bottom:12px;">7-Day Hydration Pacing</h3>
        <div class="chart-bars">
          ${chartBars.map(b => `
            <div class="chart-bar-col">
              <div class="chart-bar-fill ${b.reached ? 'reached' : ''}" style="height:${Math.max(6, b.fillPct)}%"></div>
              <div class="chart-bar-label">${b.dayName}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  // --- "Why this target?" Methodology Screen ---
  renderMethodologyScreen() {
    const container = document.getElementById('methodologyContainer');
    if (!container || !this.user) return;

    const recommendation = calculateHydrationTarget(this.user);

    container.innerHTML = `
      <div class="transparency-card">
        <h2 class="transparency-title">Why this target?</h2>
        <p style="font-size:1.8rem; font-weight:800; color:var(--color-primary-light); margin:8px 0;">
          ${recommendation.target_l} L / day
        </p>
        <p style="font-size:0.85rem; color:var(--color-text-muted); line-height:1.5;">
          ${recommendation.disclaimer}
        </p>
      </div>

      <div class="transparency-card">
        <h3 style="font-size:1rem; font-weight:700; margin-bottom:10px;">Target Calculation Breakdown</h3>
        <ul class="breakdown-list">
          ${recommendation.adjustments_breakdown.map(adj => `
            <li class="breakdown-item">
              <div>
                <div class="breakdown-label">${adj.factor}</div>
                <div class="breakdown-desc">${adj.details}</div>
              </div>
              <span class="breakdown-val">${adj.change}</span>
            </li>
          `).join('')}
        </ul>
      </div>

      <div class="transparency-card">
        <h3 style="font-size:1rem; font-weight:700; margin-bottom:8px;">Scientific References</h3>
        <p style="font-size:0.85rem; color:var(--color-text-muted); line-height:1.5; margin-bottom:10px;">
          Primary dietary reference values used by this system:
        </p>
        <ul style="font-size:0.8rem; color:var(--color-text-muted); padding-left:18px; line-height:1.6;">
          <li><strong>Institute of Medicine (IOM / National Academies)</strong>: Dietary Reference Intakes for Water (Men 3.7L, Women 2.7L total water).</li>
          <li><strong>EFSA (European Food Safety Authority)</strong>: DRVs for Water Intake.</li>
          <li><strong>WHO Guidelines</strong>: Physical workload and environmental fluid loss adjustments.</li>
        </ul>
      </div>
    `;
  }

  // --- Settings Screen ---
  renderSettingsScreen() {
    const container = document.getElementById('settingsContainer');
    if (!container || !this.bottle) return;

    container.innerHTML = `
      <div class="transparency-card">
        <h3 style="font-size:1rem; font-weight:700; margin-bottom:12px;">Bottle Configuration</h3>
        
        <div class="form-group">
          <label class="form-label">Bottle Capacity (ml)</label>
          <div class="setting-cap-presets">
            <button type="button" class="setting-cap-preset ${this.bottle.capacity_ml === 400 ? 'active' : ''}" data-cap="400">400 ml</button>
            <button type="button" class="setting-cap-preset ${this.bottle.capacity_ml === 500 ? 'active' : ''}" data-cap="500">500 ml</button>
            <button type="button" class="setting-cap-preset ${this.bottle.capacity_ml === 750 ? 'active' : ''}" data-cap="750">750 ml</button>
            <button type="button" class="setting-cap-preset ${this.bottle.capacity_ml === 1000 ? 'active' : ''}" data-cap="1000">1.0 L</button>
            <button type="button" class="setting-cap-preset ${this.bottle.capacity_ml === 1500 ? 'active' : ''}" data-cap="1500">1.5 L</button>
          </div>
          <div class="custom-cap-input-group">
            <input type="number" id="settingBottleCap" class="input-control" value="${this.bottle.capacity_ml}" placeholder="e.g. 400" min="50" max="10000" step="10" />
            <span class="custom-cap-unit">ml</span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Bottle Color Theme</label>
          <select id="settingBottleTheme" class="input-control">
            <option value="ocean_blue" ${this.bottle.theme === 'ocean_blue' ? 'selected' : ''}>Ocean Blue</option>
            <option value="emerald_mint" ${this.bottle.theme === 'emerald_mint' ? 'selected' : ''}>Emerald Mint</option>
            <option value="sunset_coral" ${this.bottle.theme === 'sunset_coral' ? 'selected' : ''}>Sunset Coral</option>
            <option value="midnight_obsidian" ${this.bottle.theme === 'midnight_obsidian' ? 'selected' : ''}>Midnight Obsidian</option>
          </select>
        </div>

        <button class="btn btn-primary" id="saveBottleSettingsBtn" style="width:100%;">Save Bottle Settings</button>
      </div>

      <div class="transparency-card" style="margin-top:16px;">
        <h3 style="font-size:1rem; font-weight:700; margin-bottom:12px;">Hydration Reminders</h3>
        <p style="font-size:0.8rem; color:var(--color-text-muted); margin-bottom:12px;">
          Receive gentle notifications when falling behind your expected daily hydration pacing.
        </p>
        
        <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(15,23,42,0.6); padding:12px 16px; border-radius:var(--radius-md); border:1px solid var(--color-surface-border);">
          <div>
            <div style="font-weight:700; font-size:0.9rem;">Enable Gentle Reminders</div>
            <div style="font-size:0.75rem; color:var(--color-text-subtle);" id="notifStatusText">
              Status: ${this.notificationEngine.getPermissionState() === 'granted' && this.notificationEngine.enabled ? 'Active' : 'Disabled'}
            </div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="settingNotifToggle" ${this.notificationEngine.getPermissionState() === 'granted' && this.notificationEngine.enabled ? 'checked' : ''}>
            <span class="slider"></span>
          </label>
        </div>
      </div>

      <div class="transparency-card" style="margin-top:16px;">
        <h3 style="font-size:1rem; font-weight:700; margin-bottom:12px;">Data Management</h3>
        <button class="btn btn-secondary" id="exportDataBtn" style="width:100%; margin-bottom:10px;">Export Data (JSON)</button>
        <button class="btn btn-secondary" id="resetDataBtn" style="width:100%; color:#ef4444; border-color:rgba(239,68,68,0.3);">Reset Local Data</button>
      </div>
    `;

    // Preset buttons in settings
    const capInput = document.getElementById('settingBottleCap');
    const presetBtns = container.querySelectorAll('.setting-cap-preset');
    presetBtns.forEach(btn => {
      btn.onclick = () => {
        const capVal = btn.dataset.cap;
        if (capInput) {
          capInput.value = capVal;
        }
        presetBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      };
    });

    if (capInput) {
      capInput.oninput = () => {
        const currentVal = parseInt(capInput.value, 10);
        presetBtns.forEach(b => {
          if (parseInt(b.dataset.cap, 10) === currentVal) {
            b.classList.add('active');
          } else {
            b.classList.remove('active');
          }
        });
      };
    }

    const notifToggle = document.getElementById('settingNotifToggle');
    const notifStatusText = document.getElementById('notifStatusText');
    if (notifToggle) {
      notifToggle.onchange = async () => {
        if (notifToggle.checked) {
          const granted = await this.notificationEngine.requestPermission();
          if (granted) {
            this.notificationEngine.enabled = true;
            if (notifStatusText) notifStatusText.textContent = 'Status: Active';
          } else {
            notifToggle.checked = false;
            this.notificationEngine.enabled = false;
            alert('Notification permission was not granted by your browser.');
            if (notifStatusText) notifStatusText.textContent = 'Status: Disabled';
          }
        } else {
          this.notificationEngine.enabled = false;
          if (notifStatusText) notifStatusText.textContent = 'Status: Disabled';
        }
      };
    }

    document.getElementById('saveBottleSettingsBtn').onclick = async () => {
      const cap = parseInt(document.getElementById('settingBottleCap').value, 10);
      const theme = document.getElementById('settingBottleTheme').value;
      if (!cap || cap <= 0) {
        alert('Please enter a valid bottle capacity in ml (e.g. 400).');
        return;
      }
      if (cap > 10000) {
        alert('Please enter a realistic bottle capacity (up to 10,000 ml).');
        return;
      }

      this.bottle.capacity_ml = cap;
      this.bottle.theme = theme;
      if (this.bottle.current_volume_ml > cap) this.bottle.current_volume_ml = cap;

      await saveLocalData('bottle', { id: 'current_bottle', ...this.bottle });
      alert('Bottle settings saved!');
      this.renderHomeScreen();
    };

    document.getElementById('exportDataBtn').onclick = async () => {
      const drinks = await getLocalData('drink_events') || [];
      const refills = await getLocalData('refill_events') || [];
      const dataStr = JSON.stringify({ user: this.user, bottle: this.bottle, target: this.target, drinks, refills }, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'hydration_tracker_backup.json';
      a.click();
    };

    document.getElementById('resetDataBtn').onclick = async () => {
      if (confirm('Are you sure you want to reset all profile and drinking data?')) {
        indexedDB.deleteDatabase('HydrationTrackerDB');
        location.reload();
      }
    };
  }

  // --- Background Synchronization ---
  async setupNetworkSync() {
    window.addEventListener('online', () => this.syncOfflineQueue());
    this.syncOfflineQueue();
  }

  async syncOfflineQueue() {
    if (!navigator.onLine) return;

    try {
      const queue = await getSyncQueue();
      if (!queue || queue.length === 0) return;

      const drinks = queue.filter(i => i.type === 'drink_event').map(i => i.payload);
      const refills = queue.filter(i => i.type === 'refill_event').map(i => i.payload);

      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: this.user ? this.user.id : null,
          user: this.user,
          bottle: this.bottle,
          drink_events: drinks,
          refill_events: refills
        })
      });

      if (res.ok) {
        await clearSyncQueue();
        console.log('[Sync] Offline queue successfully synced to server');
      }
    } catch (err) {
      console.warn('[Sync] Offline sync attempt error:', err);
    }
  }
}

// Initialize application on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});
