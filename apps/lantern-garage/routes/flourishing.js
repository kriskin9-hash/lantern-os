// Human Flourishing Frameworks — direct Node.js integration
// Serves the HFF dashboard and reads world-model snapshots from local JSON files.
// The Python world_model can write a snapshot to integrations/hff/data/snapshot.json;
// if absent, the API returns an empty-but-valid structure so the dashboard degrades
// gracefully instead of crashing.

const path = require("path");
const fs = require("fs");

const HFF_DATA_DIR = path.resolve(__dirname, "../../../integrations/human-flourishing-frameworks/data");
const SNAPSHOT_PATH = path.join(HFF_DATA_DIR, "snapshot.json");
const WORLD_DB_PATH = path.join(HFF_DATA_DIR, "world_model.db");

function readSnapshot() {
  if (fs.existsSync(SNAPSHOT_PATH)) {
    try { return JSON.parse(fs.readFileSync(SNAPSHOT_PATH, "utf8")); } catch (_) {}
  }
  return null;
}

function emptyWorldStatus() {
  return {
    ok: true, source: "local", mode: "direct",
    belief_count: 0, sensor_count: 0, flourishing: null,
    db_exists: fs.existsSync(WORLD_DB_PATH),
    snapshot_exists: fs.existsSync(SNAPSHOT_PATH),
    message: "HFF world model not yet seeded — run integrations/human-flourishing-frameworks/seed_data.py to populate.",
  };
}

module.exports = async function flourishingRoutes(req, res, url, deps) {
  const { sendJson, sendFile, publicRoot } = deps;

  // Dashboard page
  if (url.pathname === "/flourishing" || url.pathname === "/flourishing/") {
    sendFile(res, path.resolve(publicRoot, "hff.html"));
    return true;
  }

  if (!url.pathname.startsWith("/api/flourishing/")) return false;

  const snap = readSnapshot();

  if (url.pathname === "/api/flourishing/world/status") {
    if (snap?.world) {
      sendJson(res, { ok: true, source: "snapshot", mode: "direct", ...snap.world });
    } else {
      sendJson(res, emptyWorldStatus());
    }
    return true;
  }

  if (url.pathname === "/api/flourishing/world/flourishing") {
    sendJson(res, { ok: true, source: snap ? "snapshot" : "empty", by_scope: snap?.flourishing?.by_scope ?? {} });
    return true;
  }

  if (url.pathname === "/api/flourishing/world/beliefs") {
    const limit = parseInt(url.searchParams.get("limit") || "20", 10);
    sendJson(res, { ok: true, source: snap ? "snapshot" : "empty", beliefs: (snap?.beliefs ?? []).slice(0, limit) });
    return true;
  }

  if (url.pathname === "/api/flourishing/violations") {
    sendJson(res, { ok: true, source: snap ? "snapshot" : "empty", violations: snap?.violations ?? [], count: (snap?.violations ?? []).length });
    return true;
  }

  if (url.pathname === "/api/flourishing/autonomous/status") {
    sendJson(res, { ok: true, source: snap ? "snapshot" : "empty", agents: snap?.agents ?? [], escalation_queue: 0, rules: snap?.immutable_rules ?? 0 });
    return true;
  }

  if (url.pathname === "/api/flourishing/adoption/stats") {
    sendJson(res, { ok: true, source: snap ? "snapshot" : "empty", ...(snap?.adoption ?? { verified_nodes: 0, active_nodes: 0, total_nodes: 0 }) });
    return true;
  }

  return false;
};
