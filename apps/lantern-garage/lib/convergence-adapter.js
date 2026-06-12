/**
 * Convergence I/O Adapter
 *
 * Thin wrapper around Python convergence_io_engine.py CLI.
 * Routes messages through the 4-layer hypercube + convergence loop.
 *
 * Input: message, persona, provider
 * Output: {reply, agent, timing, source: "convergence", trace_tree?, error?}
 *
 * Production considerations:
 * - Timeout protection (5s default + configurable)
 * - Circuit breaker on repeated Python failures
 * - Graceful fallback to empty/error responses
 * - JSON output parsing + validation
 * - Environment variable loading (.env)
 * - Request ID tracking for observability
 */

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

// Configuration
const CONVERGENCE_TIMEOUT_MS = process.env.CONVERGENCE_TIMEOUT_MS
  ? parseInt(process.env.CONVERGENCE_TIMEOUT_MS, 10)
  : 5000;

const PYTHON_PATH = process.env.PYTHON_PATH || "python";
const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");

// Simple circuit breaker state
const circuitState = {
  failures: 0,
  failureThreshold: 3,
  lastFailureTime: null,
  recoveryTimeoutMs: 30000,
  state: "closed", // 'closed' | 'open' | 'half_open'
};

/**
 * Check if circuit breaker allows requests
 */
function isCircuitOpen() {
  if (circuitState.state === "closed") {
    return false;
  }
  if (circuitState.state === "open") {
    const timeSinceFailure = Date.now() - circuitState.lastFailureTime;
    if (timeSinceFailure > circuitState.recoveryTimeoutMs) {
      circuitState.state = "half_open";
      return false;
    }
    return true;
  }
  // half_open: allow one attempt
  return false;
}

/**
 * Record a successful call (reset circuit)
 */
function recordSuccess() {
  circuitState.failures = 0;
  circuitState.state = "closed";
}

/**
 * Record a failed call
 */
function recordFailure() {
  circuitState.failures += 1;
  circuitState.lastFailureTime = Date.now();
  if (circuitState.failures >= circuitState.failureThreshold) {
    circuitState.state = "open";
  }
}

/**
 * Sanitize CLI arguments to prevent injection
 */
function sanitizeArg(value) {
  if (value === null || value === undefined) {
    return "";
  }
  const str = String(value).trim();
  // Remove newlines and quotes
  return str.replace(/[\r\n"'`]/g, "");
}

/**
 * Execute convergence engine via Python subprocess
 *
 * @param {string} message - User message to converge
 * @param {string} persona - Agent persona (default: "lantern")
 * @param {string|null} provider - LLM provider (optional, e.g., "anthropic", "openai", "offline")
 * @param {object} options - Additional options
 * @param {number} options.timeoutMs - Timeout in milliseconds (default: CONVERGENCE_TIMEOUT_MS)
 * @returns {Promise<{reply: string, agent: string, timing: object, source: string, trace_tree?: object, error?: string}>}
 */
async function convergeMessage(message, persona = "lantern", provider = null, options = {}) {
  const timeoutMs = options.timeoutMs || CONVERGENCE_TIMEOUT_MS;

  // Check circuit breaker
  if (isCircuitOpen()) {
    return {
      reply: "[503 Service Unavailable] Convergence chamber is recovering. Try again in 30s.",
      agent: persona,
      timing: {},
      source: "convergence",
      error: "circuit_breaker_open",
    };
  }

  // Build CLI args
  const args = [
    path.join(REPO_ROOT, "src", "convergence_io_engine.py"),
    "converge",
    "--message",
    sanitizeArg(message),
    "--persona",
    sanitizeArg(persona),
  ];

  if (provider) {
    args.push("--provider", sanitizeArg(provider));
  }

  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let timedOut = false;

    // Spawn Python process
    const proc = spawn(PYTHON_PATH, args, {
      cwd: REPO_ROOT,
      stdio: ["pipe", "pipe", "pipe"],
      timeout: timeoutMs,
      env: {
        ...process.env,
        PYTHONDONTWRITEBYTECODE: "1",
        PYTHONUNBUFFERED: "1",
      },
    });

    const timeoutHandle = setTimeout(() => {
      timedOut = true;
      proc.kill();
    }, timeoutMs);

    proc.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    proc.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    proc.on("error", (error) => {
      clearTimeout(timeoutHandle);
      recordFailure();
      resolve({
        reply: `[500 Internal Server Error] Convergence spawn failed: ${error.message}`,
        agent: persona,
        timing: {},
        source: "convergence",
        error: error.message,
      });
    });

    proc.on("exit", (code) => {
      clearTimeout(timeoutHandle);

      // Handle timeout
      if (timedOut) {
        recordFailure();
        return resolve({
          reply: `[504 Gateway Timeout] Convergence took >>${timeoutMs}ms. Try again.`,
          agent: persona,
          timing: {},
          source: "convergence",
          error: "timeout",
        });
      }

      // Handle non-zero exit code
      if (code !== 0 && code !== null) {
        recordFailure();
        return resolve({
          reply: `[500 Internal Server Error] Python process exited with code ${code}.`,
          agent: persona,
          timing: {},
          source: "convergence",
          error: `exit_code_${code}`,
          stderr: stderr.slice(0, 500), // Last 500 chars for debugging
        });
      }

      // Parse JSON output
      try {
        if (!stdout.trim()) {
          recordFailure();
          return resolve({
            reply: "[500 Internal Server Error] Convergence produced no output.",
            agent: persona,
            timing: {},
            source: "convergence",
            error: "empty_output",
          });
        }

        const result = JSON.parse(stdout);

        // Validate response structure
        if (!result.text && !result.reply) {
          recordFailure();
          return resolve({
            reply: "[500 Internal Server Error] Invalid convergence response structure.",
            agent: persona,
            timing: {},
            source: "convergence",
            error: "invalid_structure",
          });
        }

        recordSuccess();

        // Normalize response: Python returns 'text', we expose 'reply'
        return resolve({
          reply: result.text || result.reply || "",
          agent: result.persona || persona,
          timing: result.timing || {},
          source: "convergence",
          trace_tree: result.trace_tree, // Optional detailed trace
          provider: result.provider, // Pass through for observability
        });
      } catch (parseError) {
        recordFailure();
        resolve({
          reply: `[500 Internal Server Error] Failed to parse convergence response: ${parseError.message}`,
          agent: persona,
          timing: {},
          source: "convergence",
          error: "parse_error",
          raw_output: stdout.slice(0, 500), // First 500 chars for debugging
        });
      }
    });
  });
}

/**
 * Health check on convergence engine
 * Runs a quick test with minimal overhead
 *
 * @returns {Promise<{healthy: boolean, error?: string}>}
 */
async function healthCheck() {
  const result = await convergeMessage("ping", "lantern", "offline", {
    timeoutMs: 2000,
  });

  return {
    healthy: !result.error && result.reply && result.reply.length > 0,
    circuit_state: circuitState.state,
    failures: circuitState.failures,
    error: result.error,
  };
}

/**
 * Reset circuit breaker (admin utility)
 */
function resetCircuit() {
  circuitState.failures = 0;
  circuitState.state = "closed";
  circuitState.lastFailureTime = null;
}

/**
 * Get circuit state for observability
 */
function getCircuitState() {
  return { ...circuitState };
}

// Export for use in dream-chat.js and other modules
module.exports = {
  convergeMessage,
  healthCheck,
  resetCircuit,
  getCircuitState,
};
