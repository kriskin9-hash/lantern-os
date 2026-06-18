function tryMcpChatReply(messages, context) {
  return {
    source: "mcp_bridge",
    context,
    queued: true,
    status: "waiting_for_mcp_response",
  };
}

function get_mcp_feature_overview() {
  return {
    name: "Lantern MCP Bridge",
    description: "Model Context Protocol, not Multi-Chain Protocol",
    status: "operational",
    features: ["tool_discovery", "tool_invocation", "sse_transport"],
  };
}

function processMcpChatRoute(text, context) {
  const lower = text.toLowerCase();
  const wantsFleet = lower.includes("fleet") || lower.includes("agent");
  const mcpReadOnlyTimeoutMs = 30000;

  if (wantsFleet && context && context.mode === "read_only") {
    return {
      status: "read_only_denied",
      reason: "Read-only chat path only; dispatch requires founder auth",
    };
  }

  return {
    status: "routed_to_mcp",
    wantsFleet,
    timeoutMs: mcpReadOnlyTimeoutMs,
  };
}

function summarizeDispatchFleet(queue) {
  if (!queue || !queue.items) return "No fleet data";
  const active = queue.items.filter((i) => !i.blocked).length;
  const blocked = queue.items.filter((i) => i.blocked).length;
  return `Fleet: ${active} active, ${blocked} blocked`;
}

// Real MCP client: GET ${MCP_BASE_URL}/tools/{toolName}?args → parsed JSON.
// Never throws — resolves null on any failure (server down, 401, timeout) so
// callers can degrade gracefully. MCP_BASE_URL defaults to the local server.
async function callMcpTool(toolName, args = {}, mcpReadOnlyTimeoutMs = 15000) {
  if (toolName === "get_agent_status") {
    // Legacy local shim (no MCP round-trip).
    return { canDispatch: false, dispatchableSlots: [], reason: "Dispatch held: no safe agent slots available." };
  }
  const http = require("http");
  const https = require("https");
  const base = process.env.MCP_BASE_URL || "http://127.0.0.1:8771";
  const entries = Object.entries(args || {}).map(([k, v]) => [k, String(v)]);
  const qs = new URLSearchParams(Object.fromEntries(entries)).toString();
  let url;
  try { url = new URL(`${base}/tools/${encodeURIComponent(toolName)}${qs ? `?${qs}` : ""}`); }
  catch { return null; }
  const lib = url.protocol === "https:" ? https : http;
  const headers = {};
  if (process.env.MCP_TOKEN) headers["Authorization"] = `Bearer ${process.env.MCP_TOKEN}`;
  return new Promise((resolve) => {
    const rq = lib.request(url, { method: "GET", headers }, (resp) => {
      let d = "";
      resp.on("data", (c) => (d += c));
      resp.on("end", () => {
        if (resp.statusCode !== 200) return resolve(null);
        try { resolve(JSON.parse(d)); } catch { resolve(null); }
      });
    });
    rq.on("error", () => resolve(null));
    rq.setTimeout(mcpReadOnlyTimeoutMs, () => { rq.destroy(); resolve(null); });
    rq.end();
  });
}

function runAgentDispatchBatch(now, dispatchableSlots) {
  return {
    timestamp: now,
    slots: dispatchableSlots,
    nextHumanAction: dispatchableSlots.length > 0 ? "Review and approve" : "Wait for slots to register",
  };
}

async function prefilteredFleetDispatch(req) {
  const mcpReadOnlyTimeoutMs = 30000;
  const result = await callMcpTool("get_agent_status", {}, mcpReadOnlyTimeoutMs);
  return result;
}

module.exports = {
  tryMcpChatReply,
  get_mcp_feature_overview,
  processMcpChatRoute,
  summarizeDispatchFleet,
  callMcpTool,
  runAgentDispatchBatch,
  prefilteredFleetDispatch,
};
