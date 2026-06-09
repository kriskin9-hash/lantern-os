const { spawn } = require("child_process");

// Operator notes, conversation log, action triggers
module.exports = async function operatorRoutes(req, res, url, deps) {
  const { sendJson, collectRequestBody, appendJsonlQueued, operatorNotesPath,
    conversationLogPath, path, repoRoot,
    readConversationLog, normalizeConversationEntry, appendConversationEntry,
    runPowerShell, flatRagHousePath, writeFlatRagHouse } = deps;

  if (url.pathname === "/api/operator-notes" && req.method === "POST") {
    try {
      const body = await collectRequestBody(req);
      const input = JSON.parse(body || "{}");
      const text = String(input.text || "").trim().slice(0, 500);
      const priority = ["P0", "P1", "P2"].includes(input.priority) ? input.priority : "P1";
      if (!text) throw new Error("note_text_required");
      const record = { createdAt: new Date().toISOString(), text, priority, done: false };
      await appendJsonlQueued(operatorNotesPath, record);
      sendJson(res, { ok: true, record }, 201);
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return true;
  }
  if (url.pathname === "/api/conversations" && req.method === "GET") {
    const limit = Math.max(1, Math.min(200, Number(url.searchParams.get("limit") || 50)));
    sendJson(res, {
      path: path.relative(repoRoot, conversationLogPath),
      conversations: readConversationLog(limit),
    });
    return true;
  }
  if (url.pathname === "/api/conversations" && req.method === "POST") {
    try {
      const body = await collectRequestBody(req);
      const entry = normalizeConversationEntry(JSON.parse(body || "{}"));
      await appendConversationEntry(entry);
      sendJson(res, { ok: true, entry }, 201);
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return true;
  }
  if (url.pathname === "/api/actions/run-loop" && req.method === "POST") {
    try {
      const py = process.platform === "win32" ? "python" : "python3";
      const proc = spawn(py, [path.join(repoRoot, "src", "convergence_io_engine.py"), "loop"], {
        cwd: repoRoot,
        timeout: 60000,
      });
      let stdout = "";
      let stderr = "";
      proc.stdout.on("data", (data) => { stdout += data; });
      proc.stderr.on("data", (data) => { stderr += data; });
      const result = await new Promise((resolve, reject) => {
        proc.on("close", (code) => {
          resolve({ ok: code === 0, code, stdout: stdout.slice(0, 2000), stderr: stderr.slice(0, 1000) });
        });
        proc.on("error", (err) => reject(err));
      });
      sendJson(res, result, result.ok ? 200 : 500);
    } catch (err) {
      sendJson(res, { ok: false, error: err.message }, 500);
    }
    return true;
  }
  if (url.pathname === "/api/actions/local-controls" && req.method === "POST") {
    const result = await runPowerShell("scripts/Start-LanternLocalControls.ps1");
    sendJson(res, result, result.code === 0 ? 200 : 500);
    return true;
  }
  if (url.pathname === "/api/actions/flat-rag-ingest" && req.method === "POST") {
    const house = await writeFlatRagHouse();
    sendJson(res, {
      code: 0,
      stdout: `Flat RAG house updated: ${path.relative(repoRoot, flatRagHousePath)}`,
      stderr: "",
      house,
    });
    return true;
  }
  if (url.pathname === "/api/actions/update" && req.method === "POST") {
    try {
      const { execSync } = require("child_process");
      const steps = [];

      // Step 1: git pull current branch (or fallback to master)
      try {
        let currentBranch = "master";
        try {
          currentBranch = execSync("git branch --show-current", { cwd: repoRoot, encoding: "utf8" }).trim();
        } catch {}
        const pull = execSync(`git pull origin ${currentBranch}`, { cwd: repoRoot, encoding: "utf8", timeout: 30000 });
        steps.push({ step: "git_pull", ok: true, output: pull.trim(), branch: currentBranch });
      } catch (e) {
        steps.push({ step: "git_pull", ok: false, output: e.stdout?.trim() || e.message });
      }

      // Step 2: npm install
      try {
        const npm = execSync("npm install --prefix apps/lantern-garage", { cwd: repoRoot, encoding: "utf8", timeout: 60000 });
        steps.push({ step: "npm_install", ok: true, output: npm.trim() });
      } catch (e) {
        steps.push({ step: "npm_install", ok: false, output: e.stdout?.trim() || e.message });
      }

      // Step 3: auto-version and get new version info
      try {
        const autoVersionScript = path.join(repoRoot, "scripts/auto-version.js");
        if (require("fs").existsSync(autoVersionScript)) {
          require("child_process").execSync(`node ${autoVersionScript}`, { cwd: repoRoot, encoding: "utf8" });
        }
      } catch (e) {
        console.error("[Auto-version] Error:", e.message);
      }

      let newVersion = { commit: "unknown", tag: "unknown", semver: "unknown", buildId: "unknown", timestamp: "unknown" };
      try {
        const commit = execSync("git rev-parse --short HEAD", { cwd: repoRoot, encoding: "utf8" }).trim();
        const tag = execSync("git describe --tags --always", { cwd: repoRoot, encoding: "utf8" }).trim();
        newVersion = { commit, tag };
        try {
          // Read from public/version.json to match status.js endpoint
          const vjPath = path.join(repoRoot, "apps/lantern-garage/public/version.json");
          const vj = JSON.parse(require("fs").readFileSync(vjPath, "utf8"));
          if (vj.version) newVersion.semver = vj.version;
          if (vj.buildId) newVersion.buildId = vj.buildId;
          if (vj.timestamp) newVersion.timestamp = vj.timestamp;
        } catch {}
      } catch {}

      const allOk = steps.every(s => s.ok);
      const pullOutput = steps.find(s => s.step === "git_pull")?.output || "";
      const codeChanged = allOk && !pullOutput.includes("Already up to date");

      // Step 4: schedule restart only if new code was actually pulled
      if (codeChanged) {
        setTimeout(() => {
          try {
            const { execSync } = require("child_process");
            // Try PM2 first (if globally installed and ecosystem.config.js exists)
            const pm2Config = require("path").join(repoRoot, "apps/lantern-garage/ecosystem.config.js");
            try {
              execSync("pm2 restart lantern-garage", { cwd: repoRoot, encoding: "utf8", timeout: 15000, stdio: "pipe" });
              process.exit(0);
            } catch {
              // PM2 not available, try watchdog
            }
            // Fallback: watchdog.js (pure Node.js supervisor)
            try {
              execSync("node apps/lantern-garage/watchdog.js", { cwd: repoRoot, encoding: "utf8", timeout: 5000, stdio: "pipe" });
              process.exit(0);
            } catch {
              // Watchdog failed, final fallback
            }
            // Final fallback: detached spawn (old behavior)
            const restartScript = process.platform === "win32"
              ? `Start-Sleep -Seconds 2; Start-Process node -ArgumentList "apps/lantern-garage/server.js" -WindowStyle Hidden`
              : `sleep 2 && node apps/lantern-garage/server.js`;
            const shell = process.platform === "win32" ? "powershell.exe" : "sh";
            const args = process.platform === "win32" ? ["-Command", restartScript] : ["-c", restartScript];
            spawn(shell, args, { detached: true, stdio: "ignore", cwd: repoRoot });
            process.exit(0);
          } catch (restartErr) {
            console.error("Restart failed:", restartErr.message);
            process.exit(1);
          }
        }, 1000);
      }

      sendJson(res, { ok: allOk, steps, version: newVersion, restart_scheduled: codeChanged }, allOk ? 200 : 500);
    } catch (err) {
      sendJson(res, { ok: false, error: err.message }, 500);
    }
    return true;
  }
};
