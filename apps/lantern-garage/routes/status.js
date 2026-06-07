// Health, status, system metrics — read-only telemetry endpoints
const { getRoutingSnapshot } = require("../lib/provider-cache");
const { execSync } = require("child_process");

function getGitVersion(repoRoot) {
  try {
    const commit = execSync("git rev-parse HEAD", { cwd: repoRoot, encoding: "utf8" }).trim();
    const tag = execSync("git describe --tags --always", { cwd: repoRoot, encoding: "utf8" }).trim();
    const branch = execSync("git rev-parse --abbrev-ref HEAD", { cwd: repoRoot, encoding: "utf8" }).trim();
    const date = execSync("git log -1 --format=%cI", { cwd: repoRoot, encoding: "utf8" }).trim();
    return { commit, tag, branch, date };
  } catch {
    return { commit: "unknown", tag: "unknown", branch: "unknown", date: new Date().toISOString() };
  }
}

module.exports = async function statusRoutes(req, res, url, deps) {
  const { sendJson, readJson, readJsonl, getStatus, getReadiness, getMiningLabStatus,
    getActionCapabilities, getOperatorFeedbackMemory, getAccessModel, getCloudMirrorStatus } = deps;

  if (url.pathname === "/favicon.ico") {
    res.writeHead(204);
    res.end();
    return true;
  }
  if (url.pathname === "/api/health") {
    sendJson(res, { ok: true, service: "lantern-garage", generatedAt: new Date().toISOString() });
    return true;
  }
  if (url.pathname === "/api/status") {
    sendJson(res, getStatus());
    return true;
  }
  if (url.pathname === "/api/arc-reactor") {
    sendJson(res, readJson("data/arc-reactor/status.json", {}));
    return true;
  }
  if (url.pathname === "/api/wallet") {
    sendJson(res, {
      wallet: readJson("data/wallet/local-cash-wallet.json", {}),
      ledger: readJsonl("data/wallet/ledger.jsonl", 30),
    });
    return true;
  }
  if (url.pathname === "/api/readiness") {
    sendJson(res, getReadiness());
    return true;
  }
  if (url.pathname === "/api/mining-lab") {
    sendJson(res, getMiningLabStatus());
    return true;
  }
  if (url.pathname === "/api/action-capabilities") {
    sendJson(res, getActionCapabilities());
    return true;
  }
  if (url.pathname === "/api/operator-feedback") {
    sendJson(res, getOperatorFeedbackMemory());
    return true;
  }
  if (url.pathname === "/api/access-model") {
    sendJson(res, getAccessModel());
    return true;
  }
  if (url.pathname === "/api/cloud-mirrors") {
    sendJson(res, getCloudMirrorStatus());
    return true;
  }
  if (url.pathname === "/api/pcsf/routing") {
    sendJson(res, getRoutingSnapshot());
    return true;
  }
  if (url.pathname === "/api/version") {
    sendJson(res, { ok: true, version: getGitVersion(deps.repoRoot), generatedAt: new Date().toISOString() });
    return true;
  }
};
