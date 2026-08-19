/**
 * Context-Aware Notification Engine
 * Respects waking hours, user preferences, and hydration pacing.
 */

export class NotificationEngine {
  constructor(options = {}) {
    this.enabled = false;
    this.startTime = options.startTime || "08:00";
    this.endTime = options.endTime || "22:00";
    this.quietHours = options.quietHours !== undefined ? options.quietHours : true;
    this.checkIntervalMinutes = options.checkIntervalMinutes || 60;
    this.timerId = null;
  }

  isSupported() {
    return 'Notification' in window && 'serviceWorker' in navigator;
  }

  getPermissionState() {
    if (!this.isSupported()) return 'unsupported';
    return Notification.permission;
  }

  async requestPermission() {
    if (!this.isSupported()) return false;
    const permission = await Notification.requestPermission();
    this.enabled = (permission === 'granted');
    return this.enabled;
  }

  isInWakingHours() {
    const now = new Date();
    const currentMinutes = now.getHours() * 60 + now.getMinutes();

    const [startH, startM] = this.startTime.split(':').map(Number);
    const [endH, endM] = this.endTime.split(':').map(Number);

    const startMinutes = startH * 60 + startM;
    const endMinutes = endH * 60 + endM;

    return currentMinutes >= startMinutes && currentMinutes <= endMinutes;
  }

  evaluateAndNotify({ consumedMl, targetMl, bottleVolumeMl, bottleCapacityMl, lastDrinkTime }) {
    if (!this.enabled || this.getPermissionState() !== 'granted') return;
    if (this.quietHours && !this.isInWakingHours()) return;

    const now = new Date();
    const currentHour = now.getHours();

    // 1. Target already reached
    if (consumedMl >= targetMl) {
      // Do not send nagging reminders after target is complete
      return;
    }

    // 2. Expected pace by hour of day (Assuming waking day 8am to 10pm = 14 hours)
    const dayProgressRatio = Math.max(0, Math.min(1, (currentHour - 8) / 14));
    const expectedConsumedMl = targetMl * dayProgressRatio;

    // 3. Significantly behind pace (> 400ml behind expected pace)
    if (expectedConsumedMl - consumedMl > 400) {
      this.sendNotification(
        '💧 Hydration Check',
        "You're a little behind today's hydration target. Time for a refreshing glass of water?",
        'behind_pace'
      );
      return;
    }

    // 4. Low bottle warning (< 20% remaining)
    if (bottleCapacityMl > 0 && (bottleVolumeMl / bottleCapacityMl) <= 0.20 && bottleVolumeMl > 0) {
      this.sendNotification(
        '💧 Bottle Almost Empty',
        `Your physical bottle only has ${bottleVolumeMl} ml left. Ready for a quick refill?`,
        'refill_reminder'
      );
      return;
    }
  }

  sendNotification(title, body, tag = 'hydration_notice') {
    if (Notification.permission === 'granted') {
      navigator.serviceWorker.ready.then((registration) => {
        registration.showNotification(title, {
          body: body,
          icon: '/icons/icon-192.png',
          badge: '/icons/icon-192.png',
          tag: tag,
          renotify: true
        });
      });
    }
  }
}
