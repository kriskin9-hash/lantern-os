/**
 * AI Control State
 *
 * Central state machine for AI execution control.
 * Tracks permissions, modes, and strategy restrictions.
 *
 * CRITICAL: Single source of truth for AI execution state.
 */

"use strict";

class AIControlState {
  constructor(config = {}) {
    this.state = {
      aiEnabled: true,
      currentMode: "NORMAL",
      shadowMode: false,
      riskLevel: "NORMAL",
      lastAllowedTradeTime: null,
      strategyPermissions: new Map(),
      lastStateChange: null,
      stateChangeReason: null,
    };

    this.config = {
      ...config
    };

    this.history = [];
  }

  /**
   * Update AI execution state
   */
  setState(updates) {
    const previousState = JSON.parse(JSON.stringify(this.state));

    // Apply updates
    for (const [key, value] of Object.entries(updates)) {
      if (key in this.state) {
        this.state[key] = value;
      }
    }

    // Record change
    this.state.lastStateChange = new Date().toISOString();
    this.state.stateChangeReason = updates.reason || "State update";

    // Log history
    this.history.push({
      timestamp: this.state.lastStateChange,
      previousState,
      newState: JSON.parse(JSON.stringify(this.state)),
      reason: updates.reason,
    });

    console.log(
      `[AIControlState] Updated: ${JSON.stringify(updates)}`
    );

    return this.state;
  }

  /**
   * Enable AI trading
   */
  enableAI(reason) {
    return this.setState({
      aiEnabled: true,
      currentMode: "NORMAL",
      reason: reason || "AI enabled",
    });
  }

  /**
   * Disable AI trading
   */
  disableAI(reason) {
    return this.setState({
      aiEnabled: false,
      currentMode: "OFF",
      reason: reason || "AI disabled",
    });
  }

  /**
   * Set execution mode
   */
  setMode(mode, reason) {
    const validModes = ["AGGRESSIVE", "NORMAL", "REDUCED", "SHADOW_ONLY", "OFF"];

    if (!validModes.includes(mode)) {
      throw new Error(`Invalid mode: ${mode}. Must be one of: ${validModes.join(", ")}`);
    }

    return this.setState({
      currentMode: mode,
      shadowMode: mode === "SHADOW_ONLY",
      reason: reason || `Mode changed to ${mode}`,
    });
  }

  /**
   * Enable shadow mode (paper trading)
   */
  enableShadowMode(reason) {
    return this.setState({
      shadowMode: true,
      reason: reason || "Shadow mode enabled",
    });
  }

  /**
   * Disable shadow mode
   */
  disableShadowMode(reason) {
    return this.setState({
      shadowMode: false,
      reason: reason || "Shadow mode disabled",
    });
  }

  /**
   * Set risk level
   */
  setRiskLevel(level, reason) {
    const validLevels = ["LOW", "NORMAL", "ELEVATED", "CRITICAL"];

    if (!validLevels.includes(level)) {
      throw new Error(`Invalid risk level: ${level}`);
    }

    return this.setState({
      riskLevel: level,
      reason: reason || `Risk level set to ${level}`,
    });
  }

  /**
   * Update strategy permissions
   */
  updateStrategyPermission(strategyId, allowed, reason) {
    this.state.strategyPermissions.set(strategyId, {
      allowed,
      timestamp: Date.now(),
      reason,
    });

    console.log(
      `[AIControlState] Strategy ${strategyId}: ${allowed ? "ALLOWED" : "BLOCKED"} - ${reason}`
    );

    return this.state;
  }

  /**
   * Set multiple strategy permissions
   */
  setStrategyPermissions(permissions, reason) {
    for (const [strategyId, allowed] of Object.entries(permissions)) {
      this.updateStrategyPermission(strategyId, allowed, reason);
    }

    return this.state;
  }

  /**
   * Check if strategy is allowed
   */
  isStrategyAllowed(strategyId) {
    const permission = this.state.strategyPermissions.get(strategyId);
    return permission ? permission.allowed : true;  // Default to allowed if not specified
  }

  /**
   * Get all strategy permissions
   */
  getStrategyPermissions() {
    const permissions = {};

    for (const [strategyId, data] of this.state.strategyPermissions) {
      permissions[strategyId] = data.allowed;
    }

    return permissions;
  }

  /**
   * Record last trade execution time
   */
  recordTradeExecution() {
    this.state.lastAllowedTradeTime = Date.now();
  }

  /**
   * Check if AI is in restricted mode
   */
  isRestricted() {
    return (
      !this.state.aiEnabled ||
      this.state.currentMode === "OFF" ||
      this.state.currentMode === "SHADOW_ONLY"
    );
  }

  /**
   * Check if AI can execute live trades
   */
  canExecuteLiveTrades() {
    return (
      this.state.aiEnabled &&
      this.state.currentMode !== "OFF" &&
      this.state.currentMode !== "SHADOW_ONLY"
    );
  }

  /**
   * Get current control state
   */
  getState() {
    return {
      aiEnabled: this.state.aiEnabled,
      currentMode: this.state.currentMode,
      shadowMode: this.state.shadowMode,
      riskLevel: this.state.riskLevel,
      lastAllowedTradeTime: this.state.lastAllowedTradeTime,
      strategyPermissions: Object.fromEntries(
        Array.from(this.state.strategyPermissions.entries()).map(
          ([id, data]) => [id, data.allowed]
        )
      ),
      lastStateChange: this.state.lastStateChange,
      stateChangeReason: this.state.stateChangeReason,
    };
  }

  /**
   * Get status summary
   */
  getStatusSummary() {
    return {
      timestamp: new Date().toISOString(),
      ai: {
        enabled: this.state.aiEnabled,
        mode: this.state.currentMode,
        canTrade: this.canExecuteLiveTrades(),
        canPaperTrade: this.state.shadowMode || this.state.currentMode === "SHADOW_ONLY",
      },
      risk: {
        level: this.state.riskLevel,
        restricted: this.isRestricted(),
      },
      strategies: {
        allowed: Array.from(this.state.strategyPermissions.entries())
          .filter(([_, data]) => data.allowed)
          .map(([id]) => id),
        blocked: Array.from(this.state.strategyPermissions.entries())
          .filter(([_, data]) => !data.allowed)
          .map(([id]) => id),
      },
      lastActivity: {
        tradeTime: this.state.lastAllowedTradeTime,
        stateChange: this.state.lastStateChange,
        reason: this.state.stateChangeReason,
      },
    };
  }

  /**
   * Get state change history
   */
  getHistory(limit = 50) {
    return this.history.slice(-limit);
  }

  /**
   * Rollback to previous state
   */
  rollback() {
    if (this.history.length === 0) {
      return this.state;
    }

    const previousEntry = this.history[this.history.length - 1];
    this.state = previousEntry.previousState;

    console.log(
      `[AIControlState] Rolled back to: ${JSON.stringify(previousEntry.previousState)}`
    );

    return this.state;
  }

  /**
   * Reset to default state
   */
  reset(reason) {
    return this.setState({
      aiEnabled: true,
      currentMode: "NORMAL",
      shadowMode: false,
      riskLevel: "NORMAL",
      reason: reason || "State reset to default",
    });
  }

  /**
   * Create checkpoint (for recovery)
   */
  createCheckpoint() {
    return {
      timestamp: Date.now(),
      state: JSON.parse(JSON.stringify(this.state)),
      historyLength: this.history.length,
    };
  }

  /**
   * Restore from checkpoint
   */
  restoreFromCheckpoint(checkpoint) {
    this.state = JSON.parse(JSON.stringify(checkpoint.state));
    console.log(`[AIControlState] Restored from checkpoint at ${new Date(checkpoint.timestamp).toISOString()}`);
    return this.state;
  }
}

module.exports = AIControlState;
