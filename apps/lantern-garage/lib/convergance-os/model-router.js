/**
 * Convergance OS — Model Router (v0)
 *
 * Classifies intent from inbound messages and selects the appropriate
 * model profile. v0 is a routing contract layer — the actual model call
 * still goes through the existing provider chain in stream-chat.js.
 *
 * Architecture:
 *   request -> classifyIntent() -> selectProfile() -> route()
 *   route() returns { profile, provider, ollamaAvailable }
 *   The caller uses this to pick provider and inject profile behavior rules.
 */

const { getProfile, isOllamaModelAvailable } = require("./profiles");
const { logRouteDecision } = require("./receipts");

// Intent classification — keyword-based v0, replaceable with trained classifier
const INTENT_PATTERNS = {
  dream_chat: [
    "dream", "sleep", "night", "woke", "remember", "flying", "falling",
    "door", "three doors", "bathhouse", "raven", "mosaic", "symbol",
    "journal", "feeling", "emotion", "lucid", "nightmare",
  ],
  convergance_action: [
    "!convergance", "!converge", "receipt", "promote", "hold", "reject",
    "validate", "inspect", "next action", "smallest action",
  ],
  capacity_query: [
    "provider", "capacity", "fallback", "status", "which model",
    "pcsf", "local model", "ollama", "metered",
  ],
  technical_debug: [
    "working or not", "error", "broken", "bug", "not responding", "crash",
    "why", "what happened", "debug", "fix", "issue", "problem",
    "chat bubble", "ui", "interface", "click", "not sending",
  ],
};

function classifyIntent(message) {
  const lower = String(message || "").toLowerCase();

  // Bang commands override
  if (lower.startsWith("!convergance") || lower.startsWith("!converge")) {
    return "convergance_action";
  }

  if (
    lower.startsWith("!three-doors") ||
    lower.startsWith("!threedoors") ||
    lower.startsWith("!three_doors")
  ) {
    return "three_doors";
  }

  let bestIntent = "dream_chat";
  let bestScore = 0;

  for (const [intent, keywords] of Object.entries(INTENT_PATTERNS)) {
    let score = 0;
    for (const kw of keywords) {
      if (lower.includes(kw)) score++;
    }
    if (score > bestScore) {
      bestScore = score;
      bestIntent = intent;
    }
  }

  return bestIntent;
}

const INTENT_TO_PROFILE = {
  dream_chat: "lantern-csf-dream",
  three_doors: "lantern-csf-dream",
  convergance_action: "lantern-convergance",
  capacity_query: "lantern-pcsf",
  technical_debug: "keystone", // Route to Keystone MCP for real-time debugging
};

/**
 * Route a message through the Convergance OS layer.
 * Returns routing decision without making the actual LLM call.
 */
async function route(message, { requestedProvider } = {}) {
  const startTime = Date.now();
  const intent = classifyIntent(message);
  const profileId = INTENT_TO_PROFILE[intent];
  const profile = getProfile(profileId);

  // Check if local Ollama model is available for this profile
  const ollamaAvailable = await isOllamaModelAvailable(profileId);

  // Determine effective provider
  let effectiveProvider;
  if (requestedProvider && requestedProvider !== "auto") {
    effectiveProvider = requestedProvider;
  } else if (ollamaAvailable) {
    effectiveProvider = "ollama";
  } else {
    effectiveProvider = profile.fallbackProvider;
  }

  const decision = {
    intent,
    profile,
    profileId,
    provider: effectiveProvider,
    ollamaAvailable,
    ollamaUsed: effectiveProvider === "ollama",
    behaviorRules: profile.behavior,
    temperature: profile.temperature,
    maxTokens: profile.maxTokens,
  };

  // Log receipt
  logRouteDecision({
    profile: profileId,
    provider: effectiveProvider,
    intent,
    ollamaUsed: decision.ollamaUsed,
    latencyMs: Date.now() - startTime,
    success: true,
  });

  return decision;
}

/**
 * Build a behavior preamble to inject into the system prompt.
 * This is the bridge between Convergance OS routing and the existing
 * persona system in dream-chat.js.
 */
function buildBehaviorPreamble(decision) {
  if (!decision || !decision.behaviorRules) return "";
  return [
    `[Convergance OS · ${decision.profileId} · ${decision.intent}]`,
    "Behavior contract:",
    ...decision.behaviorRules.map((r) => `- ${r}`),
    "",
  ].join("\n");
}

module.exports = { classifyIntent, route, buildBehaviorPreamble, INTENT_PATTERNS };
