/**
 * Repo Context — File search and grounding for Keystone Kernel
 *
 * Provides:
 * - searchRepoFiles(query) — find relevant files
 * - readFileContent(path) — read file with caching
 * - resolveRepoPath(relativePath) — resolve to absolute path
 */

const fs = require("fs").promises;
const path = require("path");
const { execSync } = require("child_process");

const REPO_ROOT = path.resolve(__dirname, "../../../");
const DATA_DIR = path.join(REPO_ROOT, "data");
const SRC_DIR = path.join(REPO_ROOT, "src");
const APPS_DIR = path.join(REPO_ROOT, "apps");
const TESTS_DIR = path.join(REPO_ROOT, "tests");

// Simple file cache to avoid repeated reads
const fileCache = new Map();
const CACHE_TTL = 60000; // 1 minute

// File patterns to prioritize in search
const PRIORITY_PATTERNS = [
  /\.js$/,
  /\.py$/,
  /\.json$/,
  /\.md$/,
  /test_.*\.py$/,
  /.*\.test\.js$/,
];

// Files to exclude from search
const EXCLUDE_PATTERNS = [
  /node_modules/,
  /__pycache__/,
  /\.pyc$/,
  /\.git/,
  /\.env/,
  /\.pem$/,
  /\.key$/,
  /\.csf$/,
  /venv\//,
  /\.pytest_cache/,
  /\.vscode/,
];

/**
 * Search repository for files matching a query.
 * Uses git ls-files for speed, falls back to directory scan.
 */
async function searchRepoFiles(query, maxResults = 10) {
  const keywords = query.toLowerCase().split(/\s+/).filter(Boolean);

  try {
    // Try git ls-files for speed
    const gitFiles = execSync("git ls-files", {
      cwd: REPO_ROOT,
      encoding: "utf-8",
    })
      .split("\n")
      .filter(Boolean);

    // Score files based on keyword matches
    const scored = gitFiles
      .filter((f) => !EXCLUDE_PATTERNS.some((p) => p.test(f)))
      .map((file) => {
        let score = 0;

        // Keyword matches in filename
        const filename = path.basename(file).toLowerCase();
        for (const kw of keywords) {
          if (filename.includes(kw)) score += 10;
        }

        // Keyword matches in path
        const filePath = file.toLowerCase();
        for (const kw of keywords) {
          if (filePath.includes(kw)) score += 5;
        }

        // Boost priority file types
        if (PRIORITY_PATTERNS.some((p) => p.test(file))) score += 2;

        // Prefer shorter paths (more likely to be relevant)
        score -= file.split("/").length * 0.1;

        return { path: file, score };
      })
      .filter((f) => f.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, maxResults);

    return scored;
  } catch (e) {
    // Fallback: directory scan (slower)
    return await scanDirectory(REPO_ROOT, query, maxResults);
  }
}

/**
 * Scan directory recursively (fallback for non-git repos).
 */
async function scanDirectory(dir, query, maxResults = 10, depth = 0) {
  if (depth > 5) return []; // Prevent deep recursion

  const results = [];
  const keywords = query.toLowerCase().split(/\s+/).filter(Boolean);

  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      if (EXCLUDE_PATTERNS.some((p) => p.test(entry.name))) continue;

      const fullPath = path.join(dir, entry.name);
      const relPath = path.relative(REPO_ROOT, fullPath);

      if (entry.isDirectory()) {
        results.push(...(await scanDirectory(fullPath, query, maxResults, depth + 1)));
      } else if (entry.isFile()) {
        let score = 0;
        for (const kw of keywords) {
          if (entry.name.toLowerCase().includes(kw)) score += 10;
          if (relPath.toLowerCase().includes(kw)) score += 5;
        }

        if (score > 0) {
          results.push({ path: relPath, score });
        }
      }

      if (results.length >= maxResults) break;
    }
  } catch (e) {
    // Silently skip unreadable directories
  }

  return results.sort((a, b) => b.score - a.score).slice(0, maxResults);
}

/**
 * Read file content with caching.
 * Respects .gitignore and size limits.
 */
async function readFileContent(filePath, maxSize = 100000) {
  const absPath = resolveRepoPath(filePath);

  // Check cache
  const cached = fileCache.get(absPath);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.content;
  }

  try {
    const stats = await fs.stat(absPath);

    // Skip binary files and huge files
    if (stats.size > maxSize) {
      return `[File too large: ${stats.size} bytes]\n`;
    }

    const content = await fs.readFile(absPath, "utf-8");

    // Cache the result
    fileCache.set(absPath, {
      content,
      timestamp: Date.now(),
    });

    return content;
  } catch (e) {
    throw new Error(`Failed to read ${filePath}: ${e.message}`);
  }
}

/**
 * Resolve a relative path to absolute within repo.
 * Handles various path formats.
 */
function resolveRepoPath(filePath) {
  // Already absolute
  if (path.isAbsolute(filePath)) {
    return filePath;
  }

  // Relative to repo root
  const absPath = path.join(REPO_ROOT, filePath);

  // Check if file exists
  try {
    fs.statSync(absPath);
    return absPath;
  } catch (e) {
    // Try common directories
    for (const dir of [SRC_DIR, APPS_DIR, TESTS_DIR, DATA_DIR]) {
      const candidate = path.join(dir, filePath);
      try {
        fs.statSync(candidate);
        return candidate;
      } catch (e2) {
        // Try next directory
      }
    }

    // Return best guess
    return absPath;
  }
}

/**
 * List all issues from git issue tracker or local files.
 */
async function listIssues(pattern = "") {
  const issues = [];

  // Try to get issues from GitHub via git (if available)
  try {
    const remoteUrl = execSync("git config --get remote.origin.url", {
      cwd: REPO_ROOT,
      encoding: "utf-8",
    }).trim();

    if (remoteUrl.includes("github.com")) {
      // Extract owner/repo
      const match = remoteUrl.match(/github\.com[:/]([^/]+)\/([^/]+?)(\.git)?$/);
      if (match) {
        // Return format hint for user to fetch from GitHub
        return {
          source: "github",
          repo: `${match[1]}/${match[2]}`,
          instruction:
            "Use `gh issue list --state open` to fetch real issues from GitHub",
        };
      }
    }
  } catch (e) {
    // Not a GitHub repo or git not available
  }

  // Fallback: scan for open-issues.md or TODO comments
  try {
    const openIssuesPath = path.join(REPO_ROOT, "docs", "open-issues.md");
    const content = await fs.readFile(openIssuesPath, "utf-8");

    // Simple extraction of issue lines
    const lines = content.split("\n");
    for (const line of lines) {
      if (
        line.includes("#") &&
        (line.includes("TODO") || line.includes("FIXME") || line.includes("BUG"))
      ) {
        issues.push({
          type: "todo",
          text: line.trim(),
        });
      }
    }
  } catch (e) {
    // File not found
  }

  return issues;
}

module.exports = {
  searchRepoFiles,
  readFileContent,
  resolveRepoPath,
  listIssues,
  REPO_ROOT,
};
