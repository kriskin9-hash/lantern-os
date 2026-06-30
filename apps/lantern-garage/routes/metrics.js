// Outcome metrics API (#1411) — verified-patch-rate, honesty-rate, route-quality.
// GET /api/metrics/outcomes → live metrics computed from append-only logs, plus the
// captured baseline for movement.
const { computeOutcomeMetrics, loadOrCaptureBaseline } = require("../lib/outcome-metrics");

module.exports = async function metricsRoutes(req, res, url, deps) {
  const { sendJson, repoRoot } = deps;

  if (url.pathname === "/api/metrics/outcomes" && req.method === "GET") {
    try {
      const metrics = computeOutcomeMetrics(repoRoot);
      const baseline = loadOrCaptureBaseline(metrics, repoRoot);
      sendJson(res, { ok: true, metrics, baseline }, 200);
    } catch (err) {
      sendJson(res, { ok: false, error: err.message }, 500);
    }
    return true;
  }

  return false;
};
