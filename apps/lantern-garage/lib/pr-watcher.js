/**
 * PR Watcher — polls open GitHub PRs every 60s.
 * After a PR has been idle (no updatedAt change) for IDLE_MS (default 3min),
 * pulls the diff + body, sends to Keystone chat for review, posts result as
 * a PR comment via `gh pr review`.
 *
 * State persisted to data/pr-watcher/state.json so reviews survive restarts.
 */

const { execFile } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");

const POLL_MS = 60_000;
const IDLE_MS = 3 * 60_000;

class PrWatcher {
  constructor({ repoRoot, port = 4177, idleMs = IDLE_MS } = {}) {
    this.repoRoot = repoRoot;
    this.port = port;
    this.idleMs = idleMs;
    this.stateDir = path.join(repoRoot, "data", "pr-watcher");
    this.statePath = path.join(this.stateDir, "state.json");
    this.state = {};
    this.timer = null;
    this.running = false;
    this._loadState();
  }

  start() {
    if (this.running) return;
    this.running = true;
    console.log(`[PR Watcher] Started — idle threshold ${this.idleMs / 1000}s, polling every ${POLL_MS / 1000}s`);
    this._tick();
    this.timer = setInterval(() => this._tick(), POLL_MS);
  }

  stop() {
    if (this.timer) clearInterval(this.timer);
    this.running = false;
    console.log("[PR Watcher] Stopped");
  }

  getStatus() {
    const entries = Object.values(this.state);
    return {
      running: this.running,
      idleThresholdMs: this.idleMs,
      pollIntervalMs: POLL_MS,
      tracked: entries.length,
      pending: entries.filter((e) => !e.reviewedAt).length,
      reviewed: entries.filter((e) => !!e.reviewedAt).length,
      prs: entries,
    };
  }

  async triggerReview(number) {
    const key = String(number);
    if (!this.state[key]) return { ok: false, error: "pr_not_tracked" };
    return this._reviewPr(this.state[key]);
  }

  // ── internals ──────────────────────────────────────────────────────────────

  _loadState() {
    try {
      if (fs.existsSync(this.statePath)) {
        this.state = JSON.parse(fs.readFileSync(this.statePath, "utf8"));
      }
    } catch {
      this.state = {};
    }
  }

  _saveState() {
    try {
      fs.mkdirSync(this.stateDir, { recursive: true });
      fs.writeFileSync(this.statePath, JSON.stringify(this.state, null, 2));
    } catch (err) {
      console.error("[PR Watcher] Failed to save state:", err.message);
    }
  }

  async _tick() {
    let prs;
    try {
      prs = await this._listOpenPrs();
    } catch (err) {
      console.warn("[PR Watcher] gh pr list failed:", err.message);
      return;
    }

    const now = Date.now();
    const seen = new Set();

    for (const pr of prs) {
      const key = String(pr.number);
      seen.add(key);

      const prev = this.state[key];
      const updatedAt = new Date(pr.updatedAt).getTime();

      if (!prev) {
        this.state[key] = { number: pr.number, title: pr.title, updatedAt, firstSeenAt: now, reviewedAt: null };
        console.log(`[PR Watcher] Tracking new PR #${pr.number}: "${pr.title}"`);
        this._saveState();
        continue;
      }

      if (updatedAt > prev.updatedAt) {
        this.state[key].updatedAt = updatedAt;
        this.state[key].reviewedAt = null;
        console.log(`[PR Watcher] PR #${pr.number} updated — resetting review timer`);
        this._saveState();
        continue;
      }

      const idleSince = now - prev.updatedAt;
      if (!prev.reviewedAt && idleSince >= this.idleMs) {
        console.log(`[PR Watcher] PR #${pr.number} idle ${Math.round(idleSince / 1000)}s — starting fleet review`);
        this._reviewPr(this.state[key]).catch((err) => {
          console.error(`[PR Watcher] Review failed for #${pr.number}:`, err.message);
        });
      }
    }

    for (const key of Object.keys(this.state)) {
      if (!seen.has(key)) {
        console.log(`[PR Watcher] PR #${key} closed — removing`);
        delete this.state[key];
      }
    }
    this._saveState();
  }

  async _reviewPr(entry) {
    const { number, title } = entry;
    console.log(`[PR Watcher] Fetching diff for PR #${number}`);

    let diff, prMeta;
    try {
      [diff, prMeta] = await Promise.all([
        this._gh("pr", "diff", String(number)),
        this._ghJson("pr", "view", String(number), "--json", "body,author,headRefName,baseRefName,labels"),
      ]);
    } catch (err) {
      console.error(`[PR Watcher] Could not fetch PR #${number}:`, err.message);
      return { ok: false, error: err.message };
    }

    const MAX_DIFF = 12_000;
    const truncated = diff.length > MAX_DIFF;
    const diffExcerpt = truncated ? diff.slice(0, MAX_DIFF) + "\n\n[... diff truncated — review first 12KB ...]" : diff;

    const labels = (prMeta.labels || []).map((l) => l.name).join(", ") || "none";

    const message = [
      `Fleet review of PR #${number}: "${title}"`,
      `Branch: ${prMeta.headRefName} → ${prMeta.baseRefName} | Author: ${prMeta.author?.login || "unknown"} | Labels: ${labels}`,
      "",
      "## PR Description",
      prMeta.body || "(no description)",
      "",
      "## Diff",
      "```diff",
      diffExcerpt,
      "```",
      "",
      "Review this PR. Check for: correctness bugs, missing test coverage, security issues, simplification opportunities, AGENTS.md compliance.",
      "Be specific — cite file and line. End with a clear verdict: APPROVE, REQUEST_CHANGES, or COMMENT.",
    ].join("\n");

    let reviewText;
    try {
      reviewText = await this._keystoneChat(message);
    } catch (err) {
      console.error(`[PR Watcher] Keystone chat failed for #${number}:`, err.message);
      return { ok: false, error: err.message };
    }

    try {
      await this._gh(
        "pr", "comment", String(number),
        "--body", `🤖 **Fleet Auto-Review** *(idle for ${Math.round(this.idleMs / 60000)}min — triggered automatically)*\n\n${reviewText}`
      );
      console.log(`[PR Watcher] Review posted on PR #${number}`);
    } catch (err) {
      console.error(`[PR Watcher] Failed to post comment on #${number}:`, err.message);
      return { ok: false, error: err.message };
    }

    this.state[String(number)].reviewedAt = Date.now();
    this._saveState();
    return { ok: true, number, reviewText };
  }

  _keystoneChat(message) {
    return new Promise((resolve, reject) => {
      const body = JSON.stringify({
        message,
        user: "pr-watcher",
        conversationId: "pr-review-fleet",
        forceAgent: "keystone",
      });

      const req = http.request(
        {
          hostname: "127.0.0.1",
          port: this.port,
          path: "/api/dream/chat",
          method: "POST",
          headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) },
        },
        (res) => {
          let out = "";
          res.on("data", (c) => (out += c));
          res.on("end", () => {
            try {
              const j = JSON.parse(out);
              resolve(j.reply || j.response || JSON.stringify(j));
            } catch {
              resolve(out);
            }
          });
        }
      );
      req.on("error", reject);
      req.setTimeout(120_000, () => req.destroy(new Error("keystone chat timeout")));
      req.write(body);
      req.end();
    });
  }

  _listOpenPrs() {
    return new Promise((resolve, reject) => {
      execFile(
        "gh", ["pr", "list", "--state", "open", "--json", "number,title,updatedAt,headRefName"],
        { cwd: this.repoRoot, timeout: 15_000 },
        (err, stdout) => {
          if (err) return reject(err);
          try { resolve(JSON.parse(stdout)); }
          catch { reject(new Error("gh pr list: invalid JSON")); }
        }
      );
    });
  }

  _gh(...args) {
    return new Promise((resolve, reject) => {
      execFile("gh", args, { cwd: this.repoRoot, timeout: 30_000, maxBuffer: 4 * 1024 * 1024 }, (err, stdout) => {
        if (err) return reject(err);
        resolve(stdout);
      });
    });
  }

  _ghJson(...args) {
    return new Promise((resolve, reject) => {
      execFile("gh", args, { cwd: this.repoRoot, timeout: 15_000 }, (err, stdout) => {
        if (err) return reject(err);
        try { resolve(JSON.parse(stdout)); }
        catch (e) { reject(new Error(`gh json: ${e.message}`)); }
      });
    });
  }
}

module.exports = { PrWatcher };
