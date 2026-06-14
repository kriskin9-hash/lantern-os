/**
 * Keystone Kernel Mode — Claude Code Execution Loop
 *
 * Embedded execution engine inside Dream Chat.
 * File-grounded, tool-driven, patch-based workflow.
 *
 * Flow: GROUND → PLAN → PATCH → VERIFY
 */

const fs = require("fs").promises;
const path = require("path");
const { exec } = require("child_process");
const { promisify } = require("util");
const execAsync = promisify(exec);

const { searchRepoFiles, readFileContent, resolveRepoPath } = require("./repo-context");
const { applyPatch, validatePatch } = require("./patch-engine");

const KEYSTONE_SYSTEM_PROMPT = `You are Keystone Code Kernel inside Lantern OS.
You are a repository-first coding agent modeled after Claude Code.

RULES:
- Always inspect repository files before reasoning.
- Never rely on memory, CSF, or symbolic context.
- Treat filesystem as the only source of truth.
- Output actionable patches, not explanations.
- Prefer minimal diffs over large rewrites.
- Validate changes using available tools when possible.

You operate in a strict loop:
GROUND → PLAN → PATCH → VERIFY

No deviation is allowed.

When you produce code changes, output them as unified diffs.
When you need to create new files, clearly mark the filename and content.
Always verify your work by running tests or checks when relevant.`;

async function keystoneRun(issue, repo, llm, options = {}) {
  const { verbose = false, maxFiles = 10 } = options;
  const results = [];

  try {
    // PHASE 1: GROUND — Search and read relevant files
    log(verbose, "🔍 PHASE 1: GROUNDING");
    const searchResults = await searchRepoFiles(issue, maxFiles);
    log(verbose, `Found ${searchResults.length} relevant files`);

    const files = [];
    for (const result of searchResults.slice(0, maxFiles)) {
      try {
        const content = await readFileContent(result.path);
        files.push({
          path: result.path,
          content,
          relevance: result.score,
        });
        log(verbose, `  ✓ ${result.path}`);
      } catch (e) {
        log(verbose, `  ✗ ${result.path} (read error)`);
      }
    }

    if (files.length === 0) {
      return {
        status: "failed",
        error: "No relevant files found",
        phase: "grounding",
      };
    }

    results.push({
      phase: "ground",
      files: files.map((f) => ({ path: f.path, relevance: f.relevance })),
    });

    // Build grounding context
    const groundingContext = files
      .map((f) => `\n=== ${f.path} ===\n${f.content.slice(0, 2000)}`)
      .join("\n");

    // PHASE 2: PLAN — Ask LLM to understand the issue
    log(verbose, "📋 PHASE 2: PLANNING");
    const planPrompt = `
Issue: ${issue}

Repository context:
${groundingContext}

Analyze this issue. What files need to change? What is the minimal fix?
Output a clear, numbered plan. Be specific about line numbers and changes.`;

    const planResponse = await llm({
      system: KEYSTONE_SYSTEM_PROMPT,
      messages: [{ role: "user", content: planPrompt }],
    });

    const plan = planResponse.content || planResponse;
    log(verbose, "Plan generated");
    results.push({ phase: "plan", plan });

    // PHASE 3: PATCH — Ask LLM to generate diffs
    log(verbose, "🔧 PHASE 3: PATCH GENERATION");
    const patchPrompt = `
Based on your plan, generate the EXACT code changes needed.

For each file that changes, output a unified diff:
\`\`\`diff
--- a/path/to/file
+++ b/path/to/file
@@ -start,count +start,count @@
\`\`\`

For new files, output:
\`\`\`newfile
path/to/new/file
content goes here
\`\`\`

Output ONLY the diffs and new files. No explanation.`;

    const patchResponse = await llm({
      system:
        "Return ONLY unified diffs and file contents. No explanation or preamble.",
      messages: [
        { role: "user", content: planPrompt },
        { role: "assistant", content: plan },
        { role: "user", content: patchPrompt },
      ],
    });

    const patchText = patchResponse.content || patchResponse;
    log(verbose, "Patch generated");

    // Validate patch structure
    const patchValidation = await validatePatch(patchText);
    if (!patchValidation.valid) {
      log(verbose, `⚠ Patch validation: ${patchValidation.error}`);
    }

    results.push({
      phase: "patch",
      patch: patchText,
      validation: patchValidation,
    });

    // PHASE 4: APPLY — Execute the patch
    log(verbose, "✏️ PHASE 4: APPLYING PATCH");
    const applyResult = await applyPatch(patchText, repo);

    if (!applyResult.success) {
      log(verbose, `❌ Patch failed: ${applyResult.error}`);
      return {
        status: "patch_failed",
        error: applyResult.error,
        phase: "apply",
        plan,
        patch: patchText,
      };
    }

    log(verbose, `✓ Applied ${applyResult.filesChanged} files`);
    results.push({
      phase: "apply",
      filesChanged: applyResult.filesChanged,
      changed: applyResult.changed,
    });

    // PHASE 5: VERIFY — Run tests if available
    log(verbose, "✅ PHASE 5: VERIFICATION");
    let verification = null;
    try {
      const testCmd =
        applyResult.changed[0]?.path?.endsWith(".py") ||
        applyResult.changed.some((f) => f.path?.includes("test"))
          ? "python -m pytest tests/ -q --tb=short"
          : "npm test --prefix apps/lantern-garage 2>&1 | head -50";

      const verifyResult = await execAsync(testCmd, {
        cwd: repo,
        timeout: 30000,
        maxBuffer: 1024 * 1024,
      });

      verification = {
        success: true,
        output: verifyResult.stdout.slice(0, 1000),
      };
      log(verbose, "Tests passed");
    } catch (e) {
      verification = {
        success: false,
        output: String(e.message).slice(0, 500),
      };
      log(verbose, "Tests failed or unavailable");
    }

    results.push({
      phase: "verify",
      tests: verification,
    });

    return {
      status: "success",
      issue,
      plan,
      patch: patchText,
      applied: applyResult.changed,
      tests: verification,
      fullResults: results,
    };
  } catch (err) {
    return {
      status: "error",
      error: err.message,
      phase: "unknown",
      fullResults: results,
    };
  }
}

function log(verbose, message) {
  if (verbose) console.log(`[Keystone] ${message}`);
}

module.exports = {
  keystoneRun,
  KEYSTONE_SYSTEM_PROMPT,
};
