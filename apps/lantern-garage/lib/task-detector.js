/**
 * Task Type Detector
 * Classifies user messages to determine optimal LLM provider chain
 * Used by provider-router to select task-aware fallback order
 */

/**
 * Detect task type from message and context
 * @param {string} message - User message
 * @param {object} context - {isTradingQuery, isCodeRequest, isCreative, etc.}
 * @returns {"coding" | "reasoning" | "creative" | "trading" | "default"}
 */
function detectTaskType(message, context = {}) {
  const lower = message.toLowerCase();

  // Explicit context flags take priority
  if (context.isTradingQuery) return "trading";
  if (context.isCodeRequest) return "coding";
  if (context.isCreative) return "creative";
  if (context.isReasoning) return "reasoning";

  // Coding detection (function, class, api, bug fix, etc.)
  const codingKeywords = /\b(function|class|method|interface|import|export|api|server|database|sql|bug|fix|code|refactor|test|debug|git|push|commit|merge|branch|pull.request|dockerfile|yaml|json|xml|html|css|javascript|python|rust|go|typescript|npm|pip|cargo|build|deploy|docker|kubernetes|jenkins|github|gitlab|bitbucket|lint|format|eslint|prettier|prettier|webpack|vite|babel|node|express|react|vue|angular|flask|django|fastapi|rails|spring)\b/i;

  if (codingKeywords.test(message)) {
    return "coding";
  }

  // Reasoning detection (explain, analyze, why, logic, strategy, research)
  const reasoningKeywords = /\b(explain|analyze|why|reason|logic|argument|pattern|strategy|plan|research|compare|contrast|evaluate|assess|review|critique|hypothesis|theory|model|framework|architecture|design|principle|rule|law|theorem|proof|derive|infer|deduce|conclude)\b/i;

  if (reasoningKeywords.test(message)) {
    return "reasoning";
  }

  // Creative detection (dream, story, poem, art, music, game, imagine, visualize)
  const creativeKeywords = /\b(dream|story|poem|art|music|game|imagine|visualize|create|invent|design|fiction|novel|script|dialogue|character|scene|setting|plot|narrative|metaphor|symbol|theme|mood|atmosphere|aesthetic|style|technique|composition|harmony|rhythm|melody|color|light|shadow|texture)\b/i;

  if (creativeKeywords.test(message)) {
    return "creative";
  }

  // Default: balanced chain
  return "default";
}

/**
 * Confidence score for task type detection (0-1)
 * Higher = more confident in the classification
 * Used to decide if override is appropriate
 */
function getDetectionConfidence(message, context = {}) {
  const type = detectTaskType(message, context);
  const lower = message.toLowerCase();

  // Explicit context = highest confidence
  if (context.isTradingQuery || context.isCodeRequest || context.isCreative || context.isReasoning) {
    return 0.95;
  }

  // Count keyword matches for confidence
  let matchCount = 0;
  const keywords = getKeywordsForType(type);
  for (const kw of keywords) {
    const regex = new RegExp(`\\b${kw}\\b`, "i");
    if (regex.test(lower)) matchCount++;
  }

  // 0-1 scale: more matches = higher confidence
  return Math.min(1.0, matchCount / 5);
}

/**
 * Get keyword list for a task type
 * @private
 */
function getKeywordsForType(type) {
  const keywords = {
    coding: [
      "function",
      "class",
      "api",
      "server",
      "database",
      "bug",
      "fix",
      "code",
      "git",
      "docker",
      "deploy",
    ],
    reasoning: [
      "explain",
      "analyze",
      "why",
      "reason",
      "logic",
      "strategy",
      "research",
      "compare",
      "evaluate",
      "hypothesis",
    ],
    creative: [
      "dream",
      "story",
      "poem",
      "art",
      "music",
      "imagine",
      "visualize",
      "create",
      "design",
      "narrative",
    ],
    default: ["help", "question", "tell", "describe", "what", "how"],
  };
  return keywords[type] || keywords.default;
}

module.exports = {
  detectTaskType,
  getDetectionConfidence,
};
