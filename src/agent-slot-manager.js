/**
 * Agent Slot Manager
 * Manages agent slots, health monitoring, and lifecycle
 */

const fs = require("fs");
const path = require("path");

const REPO_ROOT = path.resolve(__dirname, "..");

class AgentSlotManager {
  constructor(configPath, statePath) {
    this.configPath = configPath || path.join(process.env.HOME || process.env.USERPROFILE, ".claude", "agent-slots.json");
    this.statePath = statePath || path.join(REPO_ROOT, "data", "agent-slots-state.json");
    this.slots = new Map();
    this.health = new Map();
    this.load();
  }

  /**
   * Load configuration from agent-slots.json, then overlay persisted runtime state.
   */
  load() {
    try {
      const data = JSON.parse(fs.readFileSync(this.configPath, "utf8"));
      if (!data.slots) throw new Error("No slots defined in configuration");

      let savedState = {};
      try {
        savedState = JSON.parse(fs.readFileSync(this.statePath, "utf8"));
      } catch {
        // No state file yet — start fresh
      }

      for (const slot of data.slots) {
        const s = savedState[slot.id] || {};
        this.slots.set(slot.id, {
          ...slot,
          status: s.status || "idle",
          currentWork: s.currentWork || null,
          workStartTime: s.workStartTime ? new Date(s.workStartTime) : null,
          completedCount: s.completedCount || 0,
          failedCount: s.failedCount || 0,
          lastHeartbeat: s.lastHeartbeat ? new Date(s.lastHeartbeat) : new Date(),
        });

        this.health.set(slot.id, {
          healthy: true,
          lastCheck: new Date(),
          failureCount: 0,
          message: s.status === "stale" ? "Recovered from stale state" : "Initialized",
        });
      }

      this.config = data.orchestration || {};
      console.log(`[SlotManager] Loaded ${data.slots.length} agent slots`);
    } catch (err) {
      console.error(`[SlotManager] Failed to load configuration: ${err.message}`);
      throw err;
    }
  }

  /**
   * Persist runtime slot state to data/agent-slots-state.json.
   */
  save() {
    const state = {};
    for (const [id, slot] of this.slots) {
      state[id] = {
        status: slot.status,
        currentWork: slot.currentWork,
        workStartTime: slot.workStartTime,
        completedCount: slot.completedCount,
        failedCount: slot.failedCount,
        lastHeartbeat: slot.lastHeartbeat,
      };
    }
    try {
      fs.writeFileSync(this.statePath, JSON.stringify(state, null, 2));
    } catch (err) {
      console.error(`[SlotManager] Failed to save state: ${err.message}`);
    }
  }

  /**
   * Get all enabled slots
   */
  getEnabledSlots() {
    return Array.from(this.slots.values()).filter((s) => s.enabled);
  }

  /**
   * Get slot by ID
   */
  getSlot(slotId) {
    return this.slots.get(slotId) || null;
  }

  /**
   * Assign work to a slot
   */
  assignWork(slotId, workItem) {
    const slot = this.getSlot(slotId);
    if (!slot) throw new Error(`Slot ${slotId} not found`);
    if (slot.status === "working") throw new Error(`Slot ${slotId} already has work`);

    slot.status = "working";
    slot.currentWork = workItem;
    slot.workStartTime = new Date();
    slot.lastHeartbeat = new Date();

    this.save();
    return slot;
  }

  /**
   * Complete work on a slot
   */
  completeWork(slotId, result) {
    const slot = this.getSlot(slotId);
    if (!slot) throw new Error(`Slot ${slotId} not found`);

    slot.status = "idle";
    slot.completedCount = (slot.completedCount || 0) + 1;
    slot.currentWork = null;
    slot.workStartTime = null;
    slot.lastHeartbeat = new Date();

    this.save();
    return {
      slot: slot.id,
      work: result.workId,
      duration: result.duration,
      success: true,
    };
  }

  /**
   * Mark work as failed on a slot
   */
  failWork(slotId, error) {
    const slot = this.getSlot(slotId);
    if (!slot) throw new Error(`Slot ${slotId} not found`);

    slot.status = "idle";
    slot.failedCount = (slot.failedCount || 0) + 1;
    slot.currentWork = null;
    slot.workStartTime = null;
    slot.lastHeartbeat = new Date();

    // Update health
    const health = this.health.get(slotId);
    health.failureCount = (health.failureCount || 0) + 1;
    if (health.failureCount >= 3) {
      health.healthy = false;
      health.message = `Unhealthy: ${health.failureCount} consecutive failures`;
    }

    this.save();
    return {
      slot: slot.id,
      error,
      failureCount: slot.failedCount,
    };
  }

  /**
   * Heartbeat — mark slot as alive
   */
  heartbeat(slotId) {
    const slot = this.getSlot(slotId);
    if (!slot) return null;

    slot.lastHeartbeat = new Date();

    // Reset failure count on successful heartbeat
    const health = this.health.get(slotId);
    health.lastCheck = new Date();
    if (slot.status === "idle") {
      health.failureCount = 0;
      health.healthy = true;
      health.message = "Healthy";
    }

    return slot.status;
  }

  /**
   * Check slot health
   */
  checkHealth() {
    const now = new Date();
    const staleTimeout = (this.config.staleworkTimeout || 3600000) / 1000; // Convert to seconds

    const results = [];

    for (const [slotId, slot] of this.slots) {
      const health = this.health.get(slotId);
      const timeSinceHeartbeat = (now - slot.lastHeartbeat) / 1000;

      if (timeSinceHeartbeat > staleTimeout && slot.status === "working") {
        health.healthy = false;
        health.message = `Stale work (${Math.floor(timeSinceHeartbeat / 60)}min old)`;
        slot.status = "stale";
      } else if (slot.status !== "working") {
        health.healthy = true;
      }

      results.push({
        slot: slotId,
        status: slot.status,
        healthy: health.healthy,
        message: health.message,
        lastHeartbeat: slot.lastHeartbeat,
        currentWork: slot.currentWork?.id || null,
      });
    }

    return results;
  }

  /**
   * Get slot statistics
   */
  getStats() {
    let totalCompleted = 0;
    let totalFailed = 0;
    let activeCount = 0;

    for (const slot of this.slots.values()) {
      totalCompleted += slot.completedCount || 0;
      totalFailed += slot.failedCount || 0;
      if (slot.status === "working") activeCount++;
    }

    return {
      totalSlots: this.slots.size,
      enabledSlots: this.getEnabledSlots().length,
      activeCount,
      idleCount: this.slots.size - activeCount,
      totalCompleted,
      totalFailed,
      successRate: totalCompleted / (totalCompleted + totalFailed || 1),
    };
  }

  /**
   * Get first idle slot
   */
  getIdleSlot() {
    const enabled = this.getEnabledSlots();
    for (const slot of enabled) {
      if (slot.status === "idle") {
        return slot;
      }
    }
    return null;
  }
}

module.exports = AgentSlotManager;
