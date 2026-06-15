/**
 * Trader Watchdog — PRL-1 Process Health Monitor
 *
 * Monitors Python trader process:
 * - Is it alive?
 * - Is it frozen (no output)?
 * - Restart if dead
 * - Kill if hanging
 *
 * Guarantees:
 * - Trader always running (or restarted)
 * - No silent crashes
 * - Auto-recovery on hang
 */

"use strict";

const { spawn } = require("child_process");
const path = require("path");

class TraderWatchdog {
  constructor(repoRoot, queue, tracer) {
    this.repoRoot = repoRoot;
    this.queue = queue;
    this.tracer = tracer;

    this.process = null;
    this.alive = false;
    this.lastHeartbeat = Date.now();
    this.restartCount = 0;
    this.hangCount = 0;

    // Watchdog interval (every 10 seconds)
    this.watchInterval = 10000;

    // Hang detection: no output in 30 seconds
    this.hangTimeout = 30000;

    this.running = false;
  }

  /**
   * Start watchdog and trader
   */
  start() {
    if (this.running) {
      console.log("[Watchdog] Already running");
      return;
    }

    this.running = true;
    console.log("[Watchdog] Starting watchdog and trader");

    // Start trader immediately
    this._startTrader();

    // Start watchdog loop
    this._runWatchLoop();
  }

  /**
   * Stop watchdog and trader
   */
  stop() {
    this.running = false;

    if (this.process) {
      console.log("[Watchdog] Terminating trader process");
      this.process.kill();
    }

    console.log("[Watchdog] Stopped");
  }

  /**
   * Start trader process
   */
  _startTrader() {
    try {
      console.log("[Watchdog] Starting trader process");

      const mainPy = path.join(this.repoRoot, "main.py");
      const pythonExe = process.platform === "win32" ? "python" : "python3";

      this.process = spawn(pythonExe, [mainPy, "--mode", "paper", "--lantern-integration", "true"], {
        cwd: this.repoRoot,
        stdio: ["ignore", "pipe", "pipe"]
      });

      this.process.stdout.on("data", (data) => {
        // Log trader output
        const msg = data.toString().trim();
        if (msg) {
          console.log(`[Trader] ${msg}`);
          this.lastHeartbeat = Date.now(); // Update heartbeat on any output
        }
      });

      this.process.stderr.on("data", (data) => {
        const msg = data.toString().trim();
        if (msg) {
          console.error(`[Trader ERR] ${msg}`);
          this.lastHeartbeat = Date.now();
        }
      });

      this.process.on("error", (e) => {
        console.error("[Watchdog] Process error:", e.message);
        this.alive = false;
      });

      this.process.on("exit", (code, signal) => {
        console.warn(`[Watchdog] Trader process exited (code: ${code}, signal: ${signal})`);
        this.alive = false;
        this.process = null;
      });

      this.alive = true;
      this.lastHeartbeat = Date.now();
      this.restartCount++;

      console.log(`[Watchdog] Trader process started (PID: ${this.process.pid}, restart #${this.restartCount})`);

      // Log restart event
      if (this.tracer) {
        this.tracer.recordEvent(
          "TRADER_STARTED",
          "watchdog",
          { pid: this.process.pid, restartCount: this.restartCount }
        );
      }

    } catch (e) {
      console.error("[Watchdog] Failed to start trader:", e.message);
      this.alive = false;
    }
  }

  /**
   * Main watchdog loop
   */
  _runWatchLoop() {
    if (!this.running) return;

    try {
      this._checkHealth();
    } catch (e) {
      console.error("[Watchdog] Health check error:", e.message);
    }

    // Schedule next check
    setTimeout(() => this._runWatchLoop(), this.watchInterval);
  }

  /**
   * Check process health
   */
  _checkHealth() {
    // Check 1: Is process alive?
    if (!this.alive || !this.process) {
      console.warn("[Watchdog] Trader is dead, restarting...");
      this._startTrader();
      return;
    }

    // Check 2: Is process hanging? (no output in 30s)
    const timeSinceHeartbeat = Date.now() - this.lastHeartbeat;
    if (timeSinceHeartbeat > this.hangTimeout) {
      console.warn(`[Watchdog] Trader hanging (no output for ${timeSinceHeartbeat}ms), killing...`);
      this.hangCount++;

      this.process.kill("SIGKILL");
      this.alive = false;
      this.process = null;

      // Log hang event
      if (this.tracer) {
        this.tracer.recordEvent(
          "TRADER_HANG_DETECTED",
          "watchdog",
          { hangCount: this.hangCount, timeSinceHeartbeat }
        );
      }

      // Restart
      setTimeout(() => this._startTrader(), 1000);
      return;
    }

    // All checks passed
    // console.log("[Watchdog] Trader healthy");
  }

  /**
   * Get watchdog status
   */
  getStatus() {
    return {
      running: this.running,
      traderAlive: this.alive,
      traderPid: this.process ? this.process.pid : null,
      metrics: {
        restartCount: this.restartCount,
        hangCount: this.hangCount,
        lastHeartbeat: new Date(this.lastHeartbeat).toISOString(),
        timeSinceHeartbeat: Date.now() - this.lastHeartbeat
      },
      watchInterval: `${this.watchInterval}ms`,
      hangTimeout: `${this.hangTimeout}ms`
    };
  }
}

module.exports = TraderWatchdog;
