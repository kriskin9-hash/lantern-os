// Web Search Client — calls MCP web_search tool for real-time grounding
// Uses DuckDuckGo lite via local MCP server (no API key required)

const http = require("http");

const MCP_HOST = process.env.MCP_SERVER_HOST || "127.0.0.1";
const MCP_PORT = parseInt(process.env.MCP_SERVER_PORT || "8771", 10);
const MCP_TIMEOUT = parseInt(process.env.MCP_CLIENT_TIMEOUT || "8000", 10);

/**
 * Call the MCP web_search tool.
 * @param {string} query - Search query
 * @param {number} maxResults - Max results (default 5)
 * @returns {Promise<{success: boolean, results?: Array, error?: string}>}
 */
async function webSearchMcp(query, maxResults = 5) {
  return new Promise((resolve) => {
    const payload = JSON.stringify({
      jsonrpc: "2.0",
      id: Date.now(),
      method: "tools/call",
      params: {
        name: "web_search",
        arguments: { query, max_results: maxResults },
      },
    });

    const req = http.request(
      {
        hostname: MCP_HOST,
        port: MCP_PORT,
        path: "/messages",
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(payload),
        },
        timeout: MCP_TIMEOUT,
      },
      (res) => {
        let data = "";
        res.on("data", (chunk) => { data += chunk; });
        res.on("end", () => {
          try {
            const parsed = JSON.parse(data);
            if (parsed.result) {
              resolve(parsed.result);
            } else if (parsed.error) {
              resolve({ success: false, error: parsed.error.message || String(parsed.error) });
            } else {
              resolve({ success: false, error: "Unexpected MCP response" });
            }
          } catch (e) {
            resolve({ success: false, error: `Parse error: ${e.message}` });
          }
        });
      }
    );

    req.on("error", (err) => resolve({ success: false, error: err.message }));
    req.on("timeout", () => { req.destroy(); resolve({ success: false, error: "Timeout" }); });
    req.write(payload);
    req.end();
  });
}

/**
 * Format web search results into a grounding context string for prompts.
 * @param {Array} results - Search results from webSearchMcp
 * @param {string} query - Original query
 * @returns {string}
 */
function formatGroundingContext(results, query) {
  if (!results || results.length === 0) {
    return "";
  }
  const lines = [
    `--- Web Search Grounding (query: "${query}") ---`,
    "Use the following real-time search results to ground your response. Do not hallucinate beyond what is supported.",
    "",
  ];
  for (const r of results.slice(0, 5)) {
    lines.push(`[${r.rank}] ${r.title}`);
    lines.push(`    URL: ${r.url}`);
    if (r.snippet) lines.push(`    Snippet: ${r.snippet}`);
    lines.push("");
  }
  lines.push("--- End grounding ---");
  return lines.join("\n");
}

/**
 * Detect if a message likely needs web search grounding.
 * Simple heuristic: factual questions, current events, "what is", "how to", etc.
 * @param {string} message
 * @returns {boolean}
 */
function needsGrounding(message) {
  const lower = String(message || "").toLowerCase();
  // Skip if it's a personal reflection, greeting, or command
  const skipPatterns = [
    /^!\w+/,                     // bang commands
    /^(hi|hello|hey|yo)\b/,      // greetings
    /^(i feel|i think|i had|i dreamt|i dreamed|today i|yesterday i)\b/, // personal
    /^(thank|thanks|ok|okay|bye|goodbye)\b/, // social
  ];
  for (const p of skipPatterns) {
    if (p.test(lower)) return false;
  }
  // Factual patterns that benefit from grounding
  const needsPatterns = [
    /\b(what is|who is|where is|when is|how to|why does|what are|who are|where are)\b/,
    /\b(news|current|latest|recent|today|this week|this month|202[4-9]|2025)\b/,
    /\b(define|explain|compare|difference between)\b/,
    /\?(\s|$)/,                   // ends with question mark
    /\b(weather|stock|price|cost|rate|score|status of)\b/,
  ];
  return needsPatterns.some((p) => p.test(lower));
}

/**
 * Extract a concise search query from a user's message.
 * @param {string} message
 * @returns {string|null}
 */
function extractSearchQuery(message) {
  const lower = String(message || "").toLowerCase();
  // Remove personal prefixes
  let query = message
    .replace(/^\s*\!?\s*(?:search|lookup|find|google)\s+(for\s+)?/i, "")
    .replace(/\b(in\s+lantern\s+os|in\s+the\s+journal)\b/gi, "")
    .trim();
  if (query.length < 3) return null;
  // If it's a question, use the whole thing; otherwise just the first sentence
  if (lower.includes("?")) {
    return query.split("?")[0] + "?";
  }
  return query.split(/[.!?]/)[0].trim();
}

module.exports = {
  webSearchMcp,
  formatGroundingContext,
  needsGrounding,
  extractSearchQuery,
};
