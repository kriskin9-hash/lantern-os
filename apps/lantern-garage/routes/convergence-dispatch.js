/**
 * Convergence Dispatch Route — Token-Efficient Router Integration
 *
 * Integrates ConvergenceRouter into the request pipeline to:
 * - Route 90% of requests locally (no external API calls)
 * - Cache patterns for >70% hit rate
 * - Measure token efficiency metrics
 *
 * Maps to: /api/convergence/* endpoints
 */

const { getRouter } = require("../lib/convergence-router");
const convergenceAgent = require("../lib/convergence-agent");
const { sendJson } = require("../lib/http-utils");

module.exports = async (req, res, url, deps) => {
  const router = getRouter();
  const pathname = url.pathname;

  // GET /api/convergence/stats — Router statistics
  if (pathname === "/api/convergence/stats" && req.method === "GET") {
    const stats = router.getStats();
    sendJson(res, {
      ...stats,
      description: "Convergence router pattern cache statistics",
      targets: {
        localRoutingPercent: 90,
        cacheHitRatePercent: 70
      }
    }, 200);
    return true;
  }

  // POST /api/convergence/route-intent — Route a message intent
  if (pathname === "/api/convergence/route-intent" && req.method === "POST") {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", async () => {
      try {
        const { message, context } = JSON.parse(body);
        if (!message) {
          sendJson(res, { error: "message required" }, 400);
          return;
        }

        const result = await router.routeIntent(message, context);
        sendJson(res, {
          success: true,
          ...result,
          tokensSaved: result.cacheHit ? 15 : 0
        }, 200);
      } catch (err) {
        sendJson(res, { error: err.message }, 500);
      }
    });
    return true;
  }

  // POST /api/convergence/agent — Deterministic answer + actions (no LLM)
  if (pathname === "/api/convergence/agent" && req.method === "POST") {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", async () => {
      try {
        const { message } = JSON.parse(body || "{}");
        if (!message) {
          sendJson(res, { error: "message required" }, 400);
          return;
        }

        const result = await convergenceAgent.respond(message);
        sendJson(res, {
          success: true,
          ...result,
          tokensSaved: 60 // full local turn — no external model call
        }, 200);
      } catch (err) {
        sendJson(res, { error: err.message }, 500);
      }
    });
    return true;
  }

  // POST /api/convergence/autonomous-work — Work an issue autonomously
  if (pathname === "/api/convergence/autonomous-work" && req.method === "POST") {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", async () => {
      try {
        const { issue } = JSON.parse(body || "{}");
        const issueNumber = parseInt(issue, 10);
        
        if (!issueNumber) {
          sendJson(res, { ok: false, error: "issue_number_required" }, 400);
          return;
        }

        // Import self-edit functions
        const { generatePlan, generatePatch, applyPatch, runTests, gitAddAll, gitCommit, gitPush, openDraftPr } = require("../lib/self-edit-engine");
        const { execFile } = require("child_process");
        const path = require("path");
        const REPO_ROOT = path.resolve(__dirname, "../../..");
        const GH_REPO = "alex-place/lantern-os";

        // Fetch issue details
        const issueDetails = await new Promise((resolve) => {
          execFile(
            "gh",
            ["issue", "view", String(issueNumber), "--repo", GH_REPO, "--json", "title,body,state"],
            { cwd: REPO_ROOT, timeout: 10000, windowsHide: true },
            (err, stdout) => {
              if (err) return resolve(null);
              try {
                resolve(JSON.parse(stdout));
              } catch (_e) {
                resolve(null);
              }
            }
          );
        });

        if (!issueDetails) {
          sendJson(res, { ok: false, error: "issue_not_found" }, 404);
          return;
        }

        // Check current branch and switch from master if needed
        const currentBranch = await new Promise((resolve) => {
          execFile(
            "git",
            ["branch", "--show-current"],
            { cwd: REPO_ROOT, timeout: 5000, windowsHide: true },
            (err, stdout) => {
              if (err) return resolve("master");
              resolve(stdout.trim());
            }
          );
        });

        let branchName = currentBranch;
        if (currentBranch === "master") {
          branchName = `auto/issue-${issueNumber}`;
          await new Promise((resolve) => {
            execFile(
              "git",
              ["checkout", "-b", branchName],
              { cwd: REPO_ROOT, timeout: 5000, windowsHide: true },
              (err) => {
                if (err) return resolve(false);
                resolve(true);
              }
            );
          });
        }

        // Step 1: Generate plan
        const plan = await generatePlan(REPO_ROOT, issueDetails.title + "\n\n" + issueDetails.body, [], []);
        
        // Step 2: Generate patch
        const { diffText, files } = await generatePatch(REPO_ROOT, plan);
        
        // Step 3: Apply patch
        applyPatch(REPO_ROOT, diffText);
        
        // Step 4: Run tests
        const testResults = runTests(REPO_ROOT, []);
        const allTestsOk = testResults.every((r) => r.ok);
        
        if (!allTestsOk) {
          // Rollback on test failure
          execFile("git", ["checkout", "--", "."], { cwd: REPO_ROOT });
          sendJson(res, { 
            ok: false, 
            error: "tests_failed", 
            testResults,
            message: "Tests failed after applying changes. Changes rolled back."
          }, 500);
          return;
        }
        
        // Step 5: Commit
        gitAddAll(REPO_ROOT);
        const commitTitle = `fix: ${issueDetails.title} (fixes #${issueNumber})`;
        gitCommit(REPO_ROOT, commitTitle);
        
        // Step 6: Push
        gitPush(REPO_ROOT, branchName);
        
        // Step 7: Open PR
        const prBody = `Fixes #${issueNumber}\n\n${issueDetails.body}`;
        const prUrl = openDraftPr(REPO_ROOT, branchName, commitTitle, prBody);

        sendJson(res, {
          ok: true,
          issue: issueNumber,
          title: issueDetails.title,
          branch: branchName,
          prUrl,
          steps: ["fetched_issue", "generated_plan", "applied_patch", "ran_tests", "committed", "pushed", "opened_pr"],
          testResults
        });
      } catch (err) {
        sendJson(res, { ok: false, error: err.message, stack: err.stack }, 500);
      }
    });
    return true;
  }

  // POST /api/convergence/route-task — Route a task
  if (pathname === "/api/convergence/route-task" && req.method === "POST") {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", async () => {
      try {
        const { taskType, payload } = JSON.parse(body);
        if (!taskType) {
          sendJson(res, { error: "taskType required" }, 400);
          return;
        }

        const result = await router.routeTask(taskType, payload);
        sendJson(res, {
          success: true,
          ...result,
          tokensSaved: result.source === "deterministic_route" ? 20 : 0
        }, 200);
      } catch (err) {
        sendJson(res, { error: err.message }, 500);
      }
    });
    return true;
  }

  // POST /api/convergence/route-market — Route market search
  if (pathname === "/api/convergence/route-market" && req.method === "POST") {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", async () => {
      try {
        const { ticker } = JSON.parse(body);
        if (!ticker) {
          sendJson(res, { error: "ticker required" }, 400);
          return;
        }

        const result = await router.routeMarketSearch(ticker);
        sendJson(res, {
          success: true,
          ...result,
          tokensSaved: result.source === "cache" ? 25 : 0
        }, 200);
      } catch (err) {
        sendJson(res, { error: err.message }, 500);
      }
    });
    return true;
  }

  // POST /api/convergence/route-code — Route code generation
  if (pathname === "/api/convergence/route-code" && req.method === "POST") {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", async () => {
      try {
        const { fileType, scope, keywords } = JSON.parse(body);
        if (!fileType || !scope) {
          sendJson(res, { error: "fileType and scope required" }, 400);
          return;
        }

        const result = await router.routeCodeGeneration(fileType, scope, keywords);
        sendJson(res, {
          success: true,
          ...result
        }, 200);
      } catch (err) {
        sendJson(res, { error: err.message }, 500);
      }
    });
    return true;
  }

  // GET /api/convergence/health — Health check
  if (pathname === "/api/convergence/health" && req.method === "GET") {
    const stats = router.getStats();
    sendJson(res, {
      status: "ok",
      router: "ConvergenceRouter",
      cacheSize: stats.totalCachedRoutes,
      healthy: stats.totalCachedRoutes > 0
    }, 200);
    return true;
  }

  return false;
};
