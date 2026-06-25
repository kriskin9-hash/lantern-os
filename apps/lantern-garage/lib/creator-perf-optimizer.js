// ── Creator Dashboard Performance Optimizer ─────────────────────────────
// Reduces resource usage through visibility-based polling, lazy loading, and caching

class CreatorPerfOptimizer {
  constructor() {
    this.pollingIntervals = new Map(); // Track active intervals
    this.visibilityState = 'visible';
    this.pausedIntervals = new Map(); // Store paused intervals
    this.stats = {
      apiCallsSkipped: 0,
      apiCallsMade: 0,
      energySaved: 0, // Estimated in mJ
      bandwidthSaved: 0, // In bytes
      startTime: Date.now(),
    };

    this.setupVisibilityHandler();
  }

  // Setup page visibility listener to pause/resume polling
  setupVisibilityHandler() {
    if (typeof document !== 'undefined') {
      this._visibilityHandler = () => {
        this.visibilityState = document.visibilityState;
        if (document.hidden) {
          this.pauseAllPolling();
        } else {
          this.resumeAllPolling();
        }
      };
      document.addEventListener('visibilitychange', this._visibilityHandler);
    }
  }

  // Register a polling interval for management.
  // Accepts the callback + interval duration so pause/resume can recreate it.
  // Returns the intervalId so callers can still cancel manually if needed.
  registerPollingInterval(id, callbackFn, intervalMs, estimatedApiCalls = 1) {
    const tracked = this.stats;
    const wrappedFn = () => { tracked.apiCallsMade += estimatedApiCalls; callbackFn(); };
    const interval = setInterval(wrappedFn, intervalMs);
    this.pollingIntervals.set(id, {
      interval,
      callbackFn: wrappedFn,
      intervalMs,
      estimatedApiCalls,
      isPaused: false,
      bytesPerCall: 2048,
    });
    return interval;
  }

  // Pause all registered polling intervals
  pauseAllPolling() {
    for (const id of Array.from(this.pollingIntervals.keys())) {
      const config = this.pollingIntervals.get(id);
      if (config && !config.isPaused) {
        clearInterval(config.interval);
        config.isPaused = true;
        this.pausedIntervals.set(id, config);
        this.pollingIntervals.delete(id);
        this.stats.apiCallsSkipped += config.estimatedApiCalls;
        this.stats.bandwidthSaved += config.bytesPerCall;
        this.stats.energySaved += 50;
      }
    }
  }

  // Resume all paused polling intervals
  resumeAllPolling() {
    for (const [id, config] of this.pausedIntervals.entries()) {
      if (config.isPaused) {
        config.interval = setInterval(config.callbackFn, config.intervalMs);
        config.isPaused = false;
        this.pollingIntervals.set(id, config);
        this.pausedIntervals.delete(id);
      }
    }
  }

  // Lazy-load module with intersection observer
  lazyLoadModule(elementId, loadCallback) {
    if (typeof IntersectionObserver === 'undefined') {
      loadCallback();
      return;
    }

    const element = document.getElementById(elementId);
    if (!element) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          loadCallback();
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    observer.observe(element);
  }

  // Debounce function for resize/scroll events
  debounce(fn, delayMs) {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delayMs);
    };
  }

  // Request animation frame batching for UI updates
  batchUIUpdates(updateFn) {
    if (typeof requestAnimationFrame === 'undefined') {
      updateFn();
      return;
    }
    requestAnimationFrame(updateFn);
  }

  // Virtual scrolling for large lists (client-side hint)
  getVirtualScrollConfig(totalItems, itemHeight, containerHeight) {
    const visibleItems = Math.ceil(containerHeight / itemHeight);
    const overscan = 5; // Items to render outside viewport

    return {
      totalItems,
      itemHeight,
      containerHeight,
      visibleItems,
      overscan,
      getVisibleRange: (scrollTop) => {
        const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
        const endIndex = Math.min(totalItems, startIndex + visibleItems + overscan * 2);
        return { startIndex, endIndex };
      },
    };
  }

  // Get performance statistics
  getStats() {
    const uptime = Date.now() - this.stats.startTime;
    const energySavedEstimate = (this.stats.energySaved / 1000).toFixed(2); // Convert to Joules
    const bandwidthMB = (this.stats.bandwidthSaved / 1024 / 1024).toFixed(2);

    return {
      ...this.stats,
      uptime,
      energySavedJoules: parseFloat(energySavedEstimate),
      bandwidthMB: parseFloat(bandwidthMB),
      apiCallsAvoidedPercent: (() => {
        const total = this.stats.apiCallsMade + this.stats.apiCallsSkipped;
        return total === 0 ? '0.0%' : ((this.stats.apiCallsSkipped / total) * 100).toFixed(1) + '%';
      })(),
    };
  }

  // Reset all intervals (for cleanup)
  cleanup() {
    if (this._visibilityHandler && typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', this._visibilityHandler);
    }
    for (const config of this.pollingIntervals.values()) {
      clearInterval(config.interval);
    }
    for (const config of this.pausedIntervals.values()) {
      clearInterval(config.interval);
    }
    this.pollingIntervals.clear();
    this.pausedIntervals.clear();
  }
}

module.exports = { CreatorPerfOptimizer };
