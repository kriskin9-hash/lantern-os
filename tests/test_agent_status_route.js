/**
 * Tests for apps/lantern-garage/routes/agent-status.js
 * Run: node tests/test_agent_status_route.js
 *
 * Regression for #836: the route read `slot.lane` directly, but the live
 * agent-slots.json config provides `prefix`/`id` and no `lane` — so the moment a
 * slot was enabled (and especially working) the route threw
 * "Cannot read properties of undefined (reading 'replace')" and returned the
 * empty fallback. The stubbed slots below deliberately omit `lane`.
 */

"use strict";

const fs   = require("fs");
const path = require("path");
const os   = require("os");

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "lantern-asr-test-"));

// ── Stub queue-manager (class API: new QueueManager(dir).listByStatus / getStats) ──
const qmTmp = path.join(TMP, "queue-manager.js");
fs.writeFileSync(qmTmp, `
"use strict";
module.exports = class QueueManager {
  constructor(_dir) {}
  async listByStatus(status) {
    const data = {
      pending:   [{ issueNumber: 101, title: "Pending task" }],
      assigned:  [{ issueNumber: 99, title: "Active task", assignedTo: "gemini-1", assignedAt: new Date(Date.now()-90000).toISOString() }],
      completed: [{ issueNumber: 98, title: "Done task" }, { issueNumber: 97, title: "Done 2" }],
      failed:    [],
    };
    return data[status] || [];
  }
  getStats() { return { successRate: 0.8 }; }
};
`);

// ── Stub agent-slot-manager (class API: new AgentSlotManager(cfg).getEnabledSlots / getStats) ──
// NB: slots carry `prefix`/`id` and NO `lane` — the exact #836 condition.
const smTmp = path.join(TMP, "agent-slot-manager.js");
fs.writeFileSync(smTmp, `
"use strict";
module.exports = class AgentSlotManager {
  constructor(_cfg) {}
  getEnabledSlots() {
    return [
      { id: "claude-1", prefix: "claude/", status: "idle",    enabled: true },
      { id: "gemini-1", prefix: "gemini/", status: "working", enabled: true },
    ];
  }
  getStats() { return { successRate: 0.8 }; }
};
`);

// ── Minimal http-utils stub ───────────────────────────────────────────────────
const utilsTmp = path.join(TMP, "http-utils.js");
fs.writeFileSync(utilsTmp, `
"use strict";
module.exports = {
  sendJson(res, data, status = 200) {
    const body = JSON.stringify(data);
    res.writeHead(status, { "Content-Type": "application/json" });
    res.end(body);
  }
};
`);

// ── Patch route to use stubs ──────────────────────────────────────────────────
const REPO_ROOT = path.resolve(__dirname, "..");
const routeSrc = fs.readFileSync(path.join(REPO_ROOT, "apps/lantern-garage/routes/agent-status.js"), "utf8")
  .replace('require(path.join(REPO_ROOT, "src/queue-manager"))', `require(${JSON.stringify(qmTmp)})`)
  .replace('require(path.join(REPO_ROOT, "src/agent-slot-manager"))', `require(${JSON.stringify(smTmp)})`)
  .replace('require("../lib/http-utils")', `require(${JSON.stringify(utilsTmp)})`);
const routeTmp = path.join(TMP, "agent-status-route.js");
fs.writeFileSync(routeTmp, routeSrc);

const agentStatusRoute = require(routeTmp);

// ── Helpers ───────────────────────────────────────────────────────────────────
function makeReqRes(method, pathname) {
  const res = {
    statusCode: 200,
    headers: {},
    writeHead(code, hdrs) { this.statusCode = code; Object.assign(this.headers, hdrs || {}); },
    end(body) { this._body = body; },
    get body() { return JSON.parse(this._body || "{}"); },
  };
  const url = new URL(`http://localhost${pathname}`);
  const req = { method, url: pathname, headers: { host: "localhost" } };
  return { req, res, url };
}

let passed = 0, failed = 0;
function assert(label, cond, detail = "") {
  if (cond) { console.log(`  ✓ ${label}`); passed++; }
  else       { console.error(`  ✗ ${label}${detail ? " — " + detail : ""}`); failed++; }
}
function section(n) { console.log(`\n── ${n}`); }

// ── Tests ─────────────────────────────────────────────────────────────────────

(async () => {
  section("GET /api/dream/status/agents (slots have prefix, no lane — #836)");
  const { req, res, url } = makeReqRes("GET", "/api/dream/status/agents");
  const handled = await agentStatusRoute(req, res, url);
  assert("route handled", handled === true);
  assert("status 200", res.statusCode === 200);
  // #836 regression: must NOT be the swallowed-error fallback.
  assert("not the error fallback", !/^Agent status unavailable:/.test(res.body.text || ""), res.body.text);
  assert("body has text", typeof res.body.text === "string");
  assert("body has queue", typeof res.body.queue === "object");
  assert("pending count correct", res.body.queue.pending === 1);
  assert("working count correct", res.body.queue.working === 1);
  assert("completed count correct", res.body.queue.completed === 2);
  assert("pct calculated", res.body.queue.pct === 50); // 2/(1+1+2)
  // lane resolved from `prefix` via laneOf() rather than crashing on undefined.lane
  assert("text mentions claude lane", res.body.text.includes("claude lane"));
  assert("text mentions gemini lane", res.body.text.includes("gemini lane"));
  assert("slots[].lane resolved from prefix", res.body.slots.every(s => typeof s.lane === "string" && s.lane.length > 0));
  assert("text mentions Queue:", res.body.text.includes("Queue:"));
  assert("next items present", res.body.queue.next.length > 0);
  assert("next item has number", res.body.queue.next[0].number === 101);

  section("working slot shows timing");
  assert("gemini lane shows 'working'", res.body.text.includes("working"));

  section("non-matching routes pass through");
  const { req: r2, res: res2, url: u2 } = makeReqRes("GET", "/api/other");
  assert("returns false for other routes", (await agentStatusRoute(r2, res2, u2)) === false);
  const { req: r3, res: res3, url: u3 } = makeReqRes("POST", "/api/dream/status/agents");
  assert("returns false for POST", (await agentStatusRoute(r3, res3, u3)) === false);

  console.log(`\n${passed + failed} tests: ${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
  fs.rmSync(TMP, { recursive: true, force: true });
})().catch(e => { console.error(e); process.exit(1); });
