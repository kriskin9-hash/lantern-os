/**
 * Intent Router — Capability Registry & Intent Classification
 *
 * Exports:
 * - CAPABILITY_REGISTRY: Array of {id, name, intents, triggers, canConverge, isBlocking}
 * - classifyIntent(message): {intent, agent, surface, confidence, reason, requires_convergence}
 *
 * MVP uses keyword matching (regex triggers) for intent classification.
 */

// ============================================================================
// CAPABILITY REGISTRY
// ============================================================================

const CAPABILITY_REGISTRY = [
  {
    id: "keystone",
    name: "Keystone",
    intents: ["code", "refactor", "bug_fix", "debug", "review"],
    triggers: [
      /\b(code|refactor|bug|fix|debug|error|trace|review|lint|test)\b/i,
      /\b(function|class|var|const|return|throw|import|export)\b/i,
      /\b(crash|fail|broke|broken|issue|problem|error|exception)\b/i,
      /\b(clean up|rewrite|optimize|simplify|performance)\b/i,
    ],
    canConverge: true,
    isBlocking: false,
    description: "Code & technical problem-solving. Logic, refactoring, bug fixes.",
  },

  {
    id: "founder",
    name: "Founder",
    intents: ["strategy", "planning", "architecture", "vision", "decision"],
    triggers: [
      /\b(strategy|plan|planning|roadmap|vision|design|architecture)\b/i,
      /\b(decision|choice|trade.?off|priority|prioritize|scope)\b/i,
      /\b(build|product|feature|launch|ship|release|deploy)\b/i,
      /\b(business|market|growth|opportunity|direction)\b/i,
    ],
    canConverge: true,
    isBlocking: true,
    description: "Strategic planning, architecture, high-level decisions, roadmap.",
  },

  {
    id: "lantern",
    name: "Lantern",
    intents: ["dream", "reflection", "journal", "introspection", "memory"],
    triggers: [
      /\b(dream|reflect|reflection|journal|memory|remember|thought)\b/i,
      /\b(feeling|feel|emotion|mood|heart|soul|spirit)\b/i,
      /\b(meaning|symbol|metaphor|story|narrative)\b/i,
      /\b(write|share|express|explore|discover)\b/i,
    ],
    canConverge: true,
    isBlocking: false,
    description: "Dream journal, reflection, introspection, emotional processing.",
  },

  {
    id: "three-doors",
    name: "Three-Doors Kingdome",
    intents: ["rp_game", "game_state", "archetype", "stage", "convergence_loop"],
    triggers: [
      /\b(three.?doors?|kingdome|game|play|rp|role.?play|character)\b/i,
      /\b(stage|level|door|choice|path|journey|quest)\b/i,
      /\b(archetype|symbol|myth|legend|story|narrative)\b/i,
      /\b(infinite|replay|replayable|loop|cycle)\b/i,
    ],
    canConverge: true,
    isBlocking: false,
    description: "Three-Doors game state, RP, archtypes, infinite replayability.",
  },

  {
    id: "csf",
    name: "CSF & Memory",
    intents: ["memory", "export", "archive", "csf", "convergence_fitted"],
    triggers: [
      /\b(memory|memories|forget|remember|store|save|persist)\b/i,
      /\b(export|import|archive|backup|extract|dump|serialize)\b/i,
      /\b(csf|convergence.?fitted|binary|format|compression)\b/i,
      /\b(data|dataset|corpus|knowledge|base)\b/i,
    ],
    canConverge: true,
    isBlocking: false,
    description: "Memory export, CSF archival, data convergence, symbolic compression.",
  },

  {
    id: "trading",
    name: "Trading & Markets",
    intents: ["market", "trading", "position", "order", "portfolio", "alpaca"],
    triggers: [
      /\b(trading?|trade|invest|portfolio|position|stock)\b/i,
      /\b(market|price|ticker|symbol|buy|sell|order)\b/i,
      /\b(alpaca|broker|brokerage|account|balance)\b/i,
      /\b(profit|loss|gain|return|pnl|risk)\b/i,
    ],
    canConverge: false,
    isBlocking: true,
    description: "Trading, markets, positions, Alpaca integration, portfolio management.",
  },
];

// ============================================================================
// INTENT CLASSIFICATION
// ============================================================================

/**
 * classifyIntent(message)
 *
 * Analyzes a user message and returns:
 * {
 *   intent: string,              // e.g. "bug_fix", "strategy", "dream"
 *   agent: string,               // e.g. "keystone", "founder", "lantern"
 *   surface: "direct" | "ambient",  // "direct" if explicit, "ambient" if inferred
 *   confidence: number,          // 0.0 to 1.0
 *   reason: string,              // Why this intent was chosen
 *   requires_convergence: boolean // Whether this needs multi-agent coordination
 * }
 *
 * MVP uses regex keyword matching across triggers. Returns highest-confidence match.
 */
function classifyIntent(message) {
  if (!message || typeof message !== "string") {
    return {
      intent: "unknown",
      agent: "lantern",
      surface: "ambient",
      confidence: 0.0,
      reason: "Empty or invalid message",
      requires_convergence: false,
    };
  }

  // Score each capability based on trigger matches
  const scores = CAPABILITY_REGISTRY.map((cap) => {
    let matchCount = 0;
    const totalTriggers = cap.triggers.length;

    // Count how many triggers match
    for (const trigger of cap.triggers) {
      if (trigger.test(message)) {
        matchCount++;
      }
    }

    // Calculate confidence: % of triggers that matched, capped at 1.0
    const confidence = matchCount > 0 ? Math.min(matchCount / totalTriggers, 1.0) : 0.0;

    return {
      capabilityId: cap.id,
      capabilityName: cap.name,
      intent: cap.intents[0] || "unknown",
      confidence,
      matchCount,
      canConverge: cap.canConverge,
      isBlocking: cap.isBlocking,
    };
  });

  // Sort by confidence (descending)
  scores.sort((a, b) => b.confidence - a.confidence);

  const topMatch = scores[0];

  // If no triggers matched, return generic fallback
  if (topMatch.confidence === 0.0) {
    return {
      intent: "reflection",
      agent: "lantern",
      surface: "ambient",
      confidence: 0.0,
      reason: "No explicit intent triggers matched; defaulting to Lantern reflection",
      requires_convergence: false,
    };
  }

  // Determine if convergence is needed
  // - Multi-blocking intents require coordination
  // - Complex messages with high word count
  const wordCount = message.split(/\s+/).length;
  const requiresConvergence = topMatch.canConverge && (topMatch.isBlocking || wordCount > 50);

  return {
    intent: topMatch.intent,
    agent: topMatch.capabilityId,
    surface: topMatch.matchCount > 2 ? "direct" : "ambient",
    confidence: topMatch.confidence,
    reason: `Matched ${topMatch.matchCount} trigger(s) from ${topMatch.capabilityName} capability`,
    requires_convergence: requiresConvergence,
  };
}

/**
 * Get agent capability info by ID
 * @param {string} agentId - Agent ID
 * @returns {object|null}
 */
function getAgent(agentId) {
  return CAPABILITY_REGISTRY.find((a) => a.id === agentId) || null;
}

module.exports = {
  CAPABILITY_REGISTRY,
  classifyIntent,
  getAgent,
};
