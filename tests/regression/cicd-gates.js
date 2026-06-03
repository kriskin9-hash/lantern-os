/**
 * CI/CD Gate Regression Tests
 * Validates the expectations set in .github/workflows/ before they hit CI.
 *
 * Run: node tests/regression/cicd-gates.js
 * Fails fast with clear messages so operators catch violations locally.
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../..");
let passed = 0;
let failed = 0;

function assert(label, condition, detail = "") {
  if (condition) {
    passed++;
    console.log(`  PASS: ${label}`);
  } else {
    failed++;
    console.log(`  FAIL: ${label}${detail ? " — " + detail : ""}`);
  }
}

function readFile(relPath) {
  const p = path.join(ROOT, relPath);
  if (!fs.existsSync(p)) return null;
  return fs.readFileSync(p, "utf8");
}

function listFiles(dir, ext) {
  const p = path.join(ROOT, dir);
  if (!fs.existsSync(p)) return [];
  return fs.readdirSync(p).filter((f) => f.endsWith(ext));
}

function listDirs(dir) {
  const p = path.join(ROOT, dir);
  if (!fs.existsSync(p)) return [];
  return fs
    .readdirSync(p, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);
}

// ── Gate 1: Required top-level files ───────────────────────────────────────
console.log("\n=== Gate 1 — Required top-level files ===");
assert("README.md exists", fs.existsSync(path.join(ROOT, "README.md")));
assert("AGENTS.md exists", fs.existsSync(path.join(ROOT, "AGENTS.md")));
assert("docs/CONVERGENCE-LOOP.md exists", fs.existsSync(path.join(ROOT, "docs", "CONVERGENCE-LOOP.md")));
assert("docs/REPO-CONTRACT.md exists", fs.existsSync(path.join(ROOT, "docs", "REPO-CONTRACT.md")));

// ── Gate 2: Required manifests ───────────────────────────────────────────
console.log("\n=== Gate 2 — Required manifests ===");
assert("manifests/FOUNDRY-MATRIX-RAG-DOLLHOUSE.md exists",
  fs.existsSync(path.join(ROOT, "manifests", "FOUNDRY-MATRIX-RAG-DOLLHOUSE.md")));
assert("manifests/open-issues.md exists",
  fs.existsSync(path.join(ROOT, "manifests", "open-issues.md")));

// ── Gate 3: Required surfaces ────────────────────────────────────────────
console.log("\n=== Gate 3 — Required surfaces ===");
assert("surfaces/shareholder-index/index.html exists",
  fs.existsSync(path.join(ROOT, "surfaces", "shareholder-index", "index.html")));
assert("surfaces/shareholder-index/styles.css exists",
  fs.existsSync(path.join(ROOT, "surfaces", "shareholder-index", "styles.css")));

// ── Gate 4: HTML links valid (no broken relative links) ──────────────────
console.log("\n=== Gate 4 — HTML link integrity ===");
const indexHtml = readFile("surfaces/shareholder-index/index.html");
if (indexHtml) {
  const hrefs = [...indexHtml.matchAll(/href=["']([^"']+)["']/g)].map((m) => m[1]);
  const broken = [];
  for (const href of hrefs) {
    if (href.startsWith("http") || href.startsWith("#") || href.startsWith("mailto:")) continue;
    const target = path.resolve(path.join(ROOT, "surfaces", "shareholder-index"), href);
    if (!fs.existsSync(target)) broken.push(href);
  }
  assert("No broken relative links in shareholder-index", broken.length === 0,
    broken.length ? `broken: ${broken.join(", ")}` : "");
} else {
  assert("HTML link check skipped (missing file)", false);
}

// ── Gate 5: Linear-ticket-gate workflow is valid YAML ────────────────────
console.log("\n=== Gate 5 — Linear ticket gate workflow ===");
const linearGate = readFile(".github/workflows/linear-ticket-gate.yml");
assert("linear-ticket-gate.yml exists", !!linearGate);
if (linearGate) {
  assert("Gate references PR_TITLE", linearGate.includes("PR_TITLE"));
  assert("Gate references PR_BRANCH", linearGate.includes("PR_BRANCH"));
  assert("Gate has anti-sprawl step", linearGate.includes("Anti-sprawl"));
  assert("Gate checks new top-level dirs", linearGate.includes("new_top_dirs"));
  assert("Gate checks for submodules", linearGate.includes("submodule"));
}

// ── Gate 6: CI workflow has all required jobs ────────────────────────────
console.log("\n=== Gate 6 — CI workflow structure ===");
const ciYml = readFile(".github/workflows/ci.yml");
assert("ci.yml exists", !!ciYml);
if (ciYml) {
  assert("CI has validate-repo job", ciYml.includes("validate-repo"));
  assert("CI has test-python job", ciYml.includes("test-python"));
  assert("CI has test-node job", ciYml.includes("test-node"));
  assert("CI has dreamer-journal-api-tests job", ciYml.includes("dreamer-journal-api-tests"));
  assert("CI has dreamer-journal-e2e-tests job", ciYml.includes("dreamer-journal-e2e-tests"));
  assert("CI has convergence-check job", ciYml.includes("convergence-check"));
}

// ── Gate 7: Anti-sprawl — no new top-level dirs without approval ──────────
console.log("\n=== Gate 7 — Anti-sprawl: top-level directory policy ===");
// Only flag dirs that are newly added in the working tree vs HEAD
let unknownTop = [];
try {
  const { execSync } = require("child_process");
  const tracked = execSync("git ls-tree --name-only HEAD", { cwd: ROOT, encoding: "utf8" }).trim().split("\n").filter(Boolean);
  const trackedSet = new Set(tracked);
  const status = execSync("git status --short", { cwd: ROOT, encoding: "utf8" }).trim();
  // Untracked dirs appear as ?? dirname/ or ?? dirname/file
  const untrackedDirs = new Set();
  for (const line of status.split("\n")) {
    if (line.startsWith("?? ")) {
      const rel = line.slice(3).trim();
      const top = rel.split("/")[0];
      // Only flag actual directories, not root-level files like package-lock.json
      if (top && !trackedSet.has(top) && fs.existsSync(path.join(ROOT, top)) && fs.statSync(path.join(ROOT, top)).isDirectory()) {
        untrackedDirs.add(top);
      }
    }
  }
  // Exempt standard build/cache dirs
  const exempt = new Set(["node_modules", "__pycache__", ".pytest_cache", "test-results", ".tmp.drivedownload", ".tmp.driveupload"]);
  unknownTop = [...untrackedDirs].filter((d) => !exempt.has(d) && !d.startsWith("."));
} catch (e) {
  assert("git available for anti-sprawl", false, e.message);
}
assert("No unapproved top-level directories", unknownTop.length === 0,
  unknownTop.length ? `new untracked dirs: ${unknownTop.join(", ")}` : "");

// ── Gate 8: No submodules ────────────────────────────────────────────────
console.log("\n=== Gate 8 — No submodule sprawl ===");
assert(".gitmodules does not exist", !fs.existsSync(path.join(ROOT, ".gitmodules")));

// ── Gate 9: No secrets in tracked files ──────────────────────────────────
console.log("\n=== Gate 9 — Secret leak prevention ===");
const secretPatterns = [
  /sk-[a-zA-Z0-9]{20,}/,          // OpenAI/Anthropic keys
  /ghp_[a-zA-Z0-9]{36}/,          // GitHub PAT
  /glpat-[a-zA-Z0-9\-]{20}/,      // GitLab token
  /AKIA[0-9A-Z]{16}/,             // AWS access key
  /[a-zA-Z0-9_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/, // email (lightweight)
];
const scanDirs = ["src", "apps", "tests", "scripts", "skills", "docs"];
let secretHits = [];
for (const dir of scanDirs) {
  const files = listFiles(dir, ".js")
    .concat(listFiles(dir, ".ts"))
    .concat(listFiles(dir, ".py"))
    .concat(listFiles(dir, ".md"));
  for (const f of files) {
    const content = readFile(path.join(dir, f));
    if (!content) continue;
    for (const pattern of secretPatterns) {
      if (pattern.test(content) && !content.includes("process.env")) {
        // Allow process.env references (env var names, not values)
        secretHits.push(`${dir}/${f}`);
        break;
      }
    }
  }
}
assert("No hardcoded secrets in source/docs",
  secretHits.length === 0,
  secretHits.length ? `suspicious files: ${[...new Set(secretHits)].join(", ")}` : "");

// ── Gate 10: AGENTS.md rules are present ─────────────────────────────────
console.log("\n=== Gate 10 — AGENTS.md contract enforcement ===");
const agentsMd = readFile("AGENTS.md");
assert("AGENTS.md has build/test section", agentsMd && agentsMd.includes("pytest"));
assert("AGENTS.md mentions Linear ticket", agentsMd && agentsMd.includes("Linear"));
assert("AGENTS.md mentions anti-sprawl", agentsMd && agentsMd.includes("sprawl"));
assert("AGENTS.md mentions no secrets", agentsMd && agentsMd.includes("secret"));

// ── Gate 11: Dream Journal server.js has agent personas ────────────────────
console.log("\n=== Gate 11 — Dream Journal agent integrity ===");
const serverJs = readFile("apps/lantern-garage/server.js");
assert("server.js exists", !!serverJs);
if (serverJs) {
  assert("AGENT_PERSONAS defined", serverJs.includes("AGENT_PERSONAS"));
  assert("selectAgent function exists", serverJs.includes("function selectAgent"));
  assert("OpenAI provider present", serverJs.includes("OPENAI_API_KEY"));
  assert("Anthropic provider present", serverJs.includes("ANTHROPIC_API_KEY"));
  assert("Ollama fallback present", serverJs.includes("OLLAMA_BASE_URL"));
  assert("Offline fallback present", serverJs.includes("offline"));
}

// ── Gate 12: Chat memory in UI ───────────────────────────────────────────
console.log("\n=== Gate 12 — Chat UX memory contract ===");
const chatHtmlPath = path.join(ROOT, "apps", "lantern-garage", "public", "index.html");
const chatIndexHtml = fs.existsSync(chatHtmlPath) ? fs.readFileSync(chatHtmlPath, "utf8") : null;
assert("chat index.html exists", !!chatIndexHtml);
if (chatIndexHtml) {
  assert("CHAT_MEMORY_KEY defined", chatIndexHtml.includes("CHAT_MEMORY_KEY"));
  assert("saveChatMemory function", chatIndexHtml.includes("saveChatMemory"));
  assert("loadChatMemory function", chatIndexHtml.includes("loadChatMemory"));
  assert("chatClear button", chatIndexHtml.includes("chatClear"));
  assert("addImageBubble function", chatIndexHtml.includes("addImageBubble"));
}

// ── Summary ──────────────────────────────────────────────────────────────
console.log("\n" + "=".repeat(60));
console.log(`RESULT: ${passed} passed, ${failed} failed`);
if (failed > 0) {
  console.log("Fix failures before opening a PR.");
  process.exit(1);
} else {
  console.log("All CI/CD expectations met. Safe to push.");
  process.exit(0);
}
