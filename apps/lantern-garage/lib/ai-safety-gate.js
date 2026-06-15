/**
 * AI Safety Gate
 *
 * Hard enforcement layer before ANY AI output is allowed.
 * Final checkpoint that blocks AI if ANY safety condition is violated.
 *
 * CRITICAL: This is the last gate. If it says no, AI gets nothing.
 */

"use strict";

class AISafetyGate {
  constructor(killSwitch, circuitBreakers, governor) {
    this.killSwitch = killSwitch;
    this.circuitBreakers = circuitBreakers;
    this.governor = governor;
  }

  /**
   * Check if AI is allowed to execute
   * Returns { allowed: boolean, violations: [], reason: string }
   */
  checkAIPermission() {
    const violations = [];

    // 1. Kill switch check
    if (this.killSwitch && this.killSwitch.isActive()) {
      violations.push({
        gate: "KILL_SWITCH",
        level: "CRITICAL",
        reason: `Kill switch active since ${this.killSwitch.getStatus().activatedAt}`,
      });
    }

    // 2. Circuit breaker check
    if (this.circuitBreakers && this.circuitBreakers.isTriggered()) {
      const status = this.circuitBreakers.getStatus();
      const triggered = Object.entries(status.breakers)
        .filter(([_, data]) => data.active)
        .map(([name]) => name);

      violations.push({
        gate: "CIRCUIT_BREAKERS",
        level: "CRITICAL",
        reason: `Breakers triggered: ${triggered.join(", ")}`,
      });
    }

    // 3. Governor mode check
    if (this.governor) {
      const govStatus = this.governor.getStatus();

      if (!govStatus.allowed) {
        violations.push({
          gate: "GOVERNOR",
          level: "CRITICAL",
          reason: "Governor has disabled AI execution",
        });
      }

      if (govStatus.mode === "OFF") {
        violations.push({
          gate: "GOVERNOR_MODE",
          level: "CRITICAL",
          reason: "Governor mode is OFF - AI cannot trade",
        });
      }

      if (govStatus.mode === "SHADOW_ONLY") {
        violations.push({
          gate: "SHADOW_ONLY_MODE",
          level: "WARNING",
          reason: "Governor mode is SHADOW_ONLY - only paper trading allowed",
        });
      }
    }

    // Determine if AI is allowed
    const allowed = violations.length === 0;

    return {
      allowed,
      violations,
      summary: allowed ? "AI execution allowed" : `AI blocked: ${violations.length} violations`,
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Guard function to block AI trade if unsafe
   * Throws error if AI should not execute
   */
  guard(tradeRequest) {
    const permission = this.checkAIPermission();

    if (!permission.allowed) {
      const reasons = permission.violations
        .map(v => `[${v.gate}] ${v.reason}`)
        .join("; ");

      const error = new Error(`AI_SAFETY_GATE_BLOCKED: ${reasons}`);
      error.code = "AI_SAFETY_GATE_BLOCKED";
      error.violations = permission.violations;
      throw error;
    }
  }

  /**
   * Check if shadow trading mode should be enforced
   */
  shouldForceShadowMode() {
    if (this.governor) {
      const mode = this.governor.getMode();
      return mode === "SHADOW_ONLY";
    }
    return false;
  }

  /**
   * Get detailed safety report
   */
  getSafetyReport() {
    const report = {
      timestamp: new Date().toISOString(),
      systems: {
        killSwitch: null,
        circuitBreakers: null,
        governor: null,
      },
      overallStatus: "UNKNOWN",
      aiAllowed: false,
    };

    // Kill switch status
    if (this.killSwitch) {
      report.systems.killSwitch = {
        active: this.killSwitch.isActive(),
        status: this.killSwitch.getStatus(),
      };
    }

    // Circuit breaker status
    if (this.circuitBreakers) {
      report.systems.circuitBreakers = {
        triggered: this.circuitBreakers.isTriggered(),
        status: this.circuitBreakers.getStatus(),
      };
    }

    // Governor status
    if (this.governor) {
      report.systems.governor = {
        allowed: this.governor.isAllowed(),
        mode: this.governor.getMode(),
        status: this.governor.getStatus(),
      };
    }

    // Overall AI permission
    const permission = this.checkAIPermission();
    report.aiAllowed = permission.allowed;
    report.overallStatus = permission.allowed ? "SAFE" : "BLOCKED";
    report.violations = permission.violations;

    return report;
  }

  /**
   * Check if specific trade is allowed
   */
  isTradeAllowed(tradeRequest) {
    const permission = this.checkAIPermission();
    return permission.allowed;
  }

  /**
   * Get permission reason
   */
  getPermissionReason() {
    const permission = this.checkAIPermission();

    if (permission.allowed) {
      return {
        decision: "ALLOWED",
        reason: "All safety checks passed",
      };
    }

    const reasons = permission.violations.map(v => v.reason);
    return {
      decision: "BLOCKED",
      reason: reasons.join("; "),
      violations: permission.violations,
    };
  }

  /**
   * Emergency access (for testing/debugging)
   * Should require explicit user confirmation in production
   */
  overrideAllowAI(reason, confirmationCode) {
    // In production, this would require:
    // 1. Administrator authorization
    // 2. Reason logging
    // 3. Temporary window (e.g., 5 minutes)
    // 4. Audit trail

    if (!reason || !confirmationCode) {
      throw new Error("Override requires reason and confirmation code");
    }

    console.warn(
      `[AISafetyGate] OVERRIDE REQUESTED: ${reason} (code: ${confirmationCode})`
    );

    // Would deactivate governor temporarily or allow specific trade
    // Requires external confirmation in real system
    return {
      success: false,
      reason: "Override requires external administrator confirmation",
    };
  }
}

module.exports = AISafetyGate;
