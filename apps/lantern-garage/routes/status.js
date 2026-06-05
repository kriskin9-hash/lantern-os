// Health, status, system metrics — read-only telemetry endpoints
module.exports = async function statusRoutes(req, res, url, deps) {
  const { sendJson, readJson, readJsonl, getStatus, getReadiness, getMiningLabStatus,
    getActionCapabilities, getOperatorFeedbackMemory, getAccessModel, getCloudMirrorStatus } = deps;

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
};
