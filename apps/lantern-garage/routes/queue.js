/**
 * Agent Queue & Orchestration Routes
 * Exposes queue and slot manager operations via REST API
 */

module.exports = async function queueRoutes(req, res, url, deps) {
  const { sendJson, collectRequestBody, repoRoot } = deps;
  const fs = require("fs");
  const path = require("path");

  // ── GET /api/queue/status ── (minimal test endpoint)
  if (url.pathname === "/api/queue/status" && req.method === "GET") {
    sendJson(res, {
      ok: true,
      message: "Queue system online",
      queue: {
        pending: 0,
        assigned: 0,
        completed: 0,
        failed: 0,
      },
      agents: {
        totalSlots: 4,
        enabledSlots: 1,
        activeCount: 0,
        idleCount: 1,
        totalCompleted: 0,
        totalFailed: 0,
        successRate: 0,
      },
      timestamp: new Date().toISOString(),
    });
    return true;
  }

  // ── POST /api/queue/enqueue ──
  if (url.pathname === "/api/queue/enqueue" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const payload = JSON.parse(raw);

      // Ensure queue directory exists
      const queuePath = path.join(repoRoot, "data", "agent-work-queue", "pending");
      if (!fs.existsSync(queuePath)) {
        fs.mkdirSync(queuePath, { recursive: true });
      }

      const work = {
        id: `issue-${payload.issueNumber}`,
        issueNumber: payload.issueNumber,
        title: payload.title,
        description: payload.description || "",
        priority: payload.priority || 0,
        assignedTo: null,
        assignedAt: null,
        status: "pending",
        branch: null,
        targetDate: payload.targetDate || null,
        retries: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      // Save to pending queue
      const workFile = path.join(queuePath, `${work.id}.json`);
      fs.writeFileSync(workFile, JSON.stringify(work, null, 2));

      sendJson(res, {
        ok: true,
        work,
        message: `Enqueued issue #${work.issueNumber}`,
      });
      return true;
    } catch (err) {
      console.error("[Queue] Enqueue error:", err);
      sendJson(res, { error: err.message }, 400);
      return true;
    }
  }

  // ── GET /api/queue/list/:status ──
  if (url.pathname.startsWith("/api/queue/list/") && req.method === "GET") {
    try {
      const status = url.pathname.replace("/api/queue/list/", "");
      const queuePath = path.join(repoRoot, "data", "agent-work-queue", status);

      let items = [];
      if (fs.existsSync(queuePath)) {
        const files = fs.readdirSync(queuePath).filter((f) => f.endsWith(".json"));
        items = files.map((f) => JSON.parse(fs.readFileSync(path.join(queuePath, f), "utf8")));
      }

      sendJson(res, {
        status,
        count: items.length,
        items,
      });
      return true;
    } catch (err) {
      sendJson(res, { error: err.message }, 500);
      return true;
    }
  }

  // ── GET /api/queue/agents ──
  // Returns agent slot status specific to queue management (not Tesseract fleet data)
  if (url.pathname === "/api/queue/agents" && req.method === "GET") {
    sendJson(res, {
      slots: [
        { id: "claude", status: "idle", currentWork: null, completedCount: 0, failedCount: 0 },
      ],
      health: [{ slot: "claude", status: "idle", healthy: true, message: "Healthy" }],
      stats: {
        totalSlots: 4,
        enabledSlots: 1,
        activeCount: 0,
        idleCount: 1,
        totalCompleted: 0,
        totalFailed: 0,
        successRate: 0,
      },
      timestamp: new Date().toISOString(),
    });
    return true;
  }

  return false;
};
