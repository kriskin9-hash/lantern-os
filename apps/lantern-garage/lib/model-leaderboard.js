/**
 * Model leaderboard routing (PCSF-preferred).
 *
 * Makes the local Ollama model chain LEADERBOARD-DRIVEN instead of static:
 * the best-performing model for a task (by agent-performance compositeScore)
 * is tried first, so the continually-trained local model (OLLAMA_MODEL, e.g.
 * lantern-sigma0-coder-v2) rises to the top of "work / units / tasks" as it
 * proves itself. Falls back to the static chain when there's no signal yet.
 */

const { getTopAgentsForTask, recordAgentCallFromConvergenceReceipt } = require("./agent-performance");

// The continually-trained local coding model. Always a candidate for work.
function preferredLocalModel() {
  return process.env.OLLAMA_MODEL || "lantern-sigma0-coder-v2";
}

/**
 * Order a static Ollama model chain by leaderboard rank for this task.
 * Models with leaderboard wins come first (best compositeScore first); the
 * rest keep their static order. The preferred local model is guaranteed to be
 * a candidate (prepended for coding/work tasks if absent).
 */
async function orderChainByLeaderboard(staticChain, taskType) {
  const chain = Array.isArray(staticChain) ? [...staticChain] : [];
  const pref = preferredLocalModel();

  // Guarantee the trained local model is in the running for coding/work tasks.
  const workish = ["coding", "reasoning", "default", "repo", "task"].some((t) => String(taskType || "").includes(t));
  if (workish && !chain.includes(pref)) chain.unshift(pref);

  let ranked = [];
  try {
    ranked = await getTopAgentsForTask(taskType, 7, 10); // [{agentId, compositeScore,...}]
  } catch { /* no signal yet — keep static order */ }

  if (!ranked.length) return chain;

  const score = {};
  for (const r of ranked) score[r.agentId] = r.compositeScore;

  // Stable sort: leaderboard-scored models first (desc), unscored keep position.
  return chain
    .map((m, i) => ({ m, i, s: score[m] }))
    .sort((a, b) => {
      if (a.s != null && b.s != null) return b.s - a.s;
      if (a.s != null) return -1;
      if (b.s != null) return 1;
      return a.i - b.i;
    })
    .map((x) => x.m);
}

/**
 * Record a local-model outcome so the leaderboard learns which model is best.
 * Wraps recordAgentCallFromConvergenceReceipt with a minimal synthetic receipt.
 */
function recordModelOutcome(model, taskType, success, latencyMs) {
  try {
    return recordAgentCallFromConvergenceReceipt(
      { source: "ollama-chat", model },
      model,                      // agentId = the model name (so it ranks per model)
      taskType || "default",
      !!success,                  // validationPassed
      latencyMs || 0,
      0,                          // local model = $0 cost (boosts compositeScore)
    );
  } catch (e) {
    return Promise.resolve();
  }
}

module.exports = { orderChainByLeaderboard, recordModelOutcome, preferredLocalModel };
