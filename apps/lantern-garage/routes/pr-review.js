/**
 * PR Review routes — exposes PrWatcher status and manual trigger.
 *
 * GET  /api/pr-review/status  — watcher state, tracked PRs, reviewed count
 * POST /api/pr-review/trigger — force-review a specific PR now
 * POST /api/pr-review/reset   — clear reviewedAt for a PR (re-arm the idle trigger)
 */

module.exports = async function prReviewRoutes(req, res, url, deps) {
  const { sendJson, collectRequestBody, prWatcher } = deps;
  if (!prWatcher) return false;

  if (url.pathname === "/api/pr-review/status" && req.method === "GET") {
    sendJson(res, prWatcher.getStatus());
    return true;
  }

  if (url.pathname === "/api/pr-review/trigger" && req.method === "POST") {
    let body = {};
    try { body = JSON.parse(await collectRequestBody(req)); } catch { /* ok */ }
    const number = parseInt(body.number, 10);
    if (!number) {
      sendJson(res, { error: "missing_number" }, 400);
      return true;
    }
    const result = await prWatcher.triggerReview(number);
    sendJson(res, result, result.ok ? 200 : 400);
    return true;
  }

  if (url.pathname === "/api/pr-review/reset" && req.method === "POST") {
    let body = {};
    try { body = JSON.parse(await collectRequestBody(req)); } catch { /* ok */ }
    const number = String(parseInt(body.number, 10));
    if (!number || number === "NaN") {
      sendJson(res, { error: "missing_number" }, 400);
      return true;
    }
    const st = prWatcher.state[number];
    if (!st) {
      sendJson(res, { error: "pr_not_tracked" }, 404);
      return true;
    }
    st.reviewedAt = null;
    prWatcher._saveState();
    sendJson(res, { ok: true, number, message: "reviewedAt cleared — idle timer re-armed" });
    return true;
  }

  return false;
};
