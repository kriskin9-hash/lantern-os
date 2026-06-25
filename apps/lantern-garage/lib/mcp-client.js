/**
 * lib/mcp-client.js
 *
 * MCP server health check and tool routing.
 * If MCP (port 8771) is down, gracefully fall back to local tool execution.
 *
 * Usage:
 *   const mcp = require('./mcp-client');
 *   const available = await mcp.isAvailable();
 *   if (available) {
 *     const result = await mcp.callTool('github_list_issues', { repo: 'foo/bar' });
 *   }
 */

const http = require("http");

const MCP_URL = "http://127.0.0.1:8771";
const HEALTH_CHECK_TIMEOUT_MS = 2000;
const CACHE_DURATION_MS = 5000; // Cache availability for 5s to avoid hammering

let lastHealthCheck = 0;
let lastAvailability = false;

/**
 * Check if MCP server is running and healthy.
 * Results are cached for CACHE_DURATION_MS.
 */
async function isAvailable() {
  const now = Date.now();
  if (now - lastHealthCheck < CACHE_DURATION_MS) {
    return lastAvailability;
  }

  try {
    const response = await _fetchWithTimeout(`${MCP_URL}/health`, {
      method: "GET",
      timeout: HEALTH_CHECK_TIMEOUT_MS,
    });

    lastAvailability = response.status === 200;
  } catch (err) {
    lastAvailability = false;
  }

  lastHealthCheck = now;
  return lastAvailability;
}

/**
 * Call a tool via MCP server (only if available).
 *
 * @param {string} toolName - Tool name (e.g., 'github_list_issues')
 * @param {Object} args - Tool arguments
 * @returns {Promise<Object>} Tool result or { status: 'unavailable', reason: 'mcp_offline' }
 */
async function callTool(toolName, args = {}) {
  if (!(await isAvailable())) {
    return {
      status: "unavailable",
      reason_code: "mcp_server_offline",
      error: "MCP server (port 8771) is not responding",
    };
  }

  try {
    const response = await _fetchWithTimeout(`${MCP_URL}/tool/${toolName}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(args),
      timeout: 30000,
    });

    if (!response.ok) {
      return {
        status: "error",
        reason_code: "mcp_tool_error",
        error: `MCP returned ${response.status}: ${response.statusText}`,
      };
    }

    return await response.json();
  } catch (err) {
    return {
      status: "error",
      reason_code: "mcp_call_failed",
      error: err.message,
    };
  }
}

/**
 * Fetch with timeout (since http.request doesn't have built-in timeout support).
 */
function _fetchWithTimeout(url, options = {}) {
  return new Promise((resolve, reject) => {
    const timeout = options.timeout || 5000;
    const req = http.request(url, { method: options.method || "GET" }, resolve);

    req.setTimeout(timeout, () => {
      req.destroy();
      reject(new Error(`HTTP request timeout after ${timeout}ms`));
    });

    req.on("error", reject);

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

/**
 * Reset the cache (useful for testing).
 */
function _resetCache() {
  lastHealthCheck = 0;
  lastAvailability = false;
}

module.exports = {
  isAvailable,
  callTool,
  MCP_URL,
  _resetCache, // Exported for testing
};
