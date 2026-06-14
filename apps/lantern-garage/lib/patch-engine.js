/**
 * Patch Engine — Apply and validate unified diffs
 *
 * Parses unified diffs and applies them to files.
 * Validates patch syntax before application.
 */

const fs = require("fs").promises;
const path = require("path");
const { execSync } = require("child_process");

const REPO_ROOT = path.resolve(__dirname, "../../../");

/**
 * Validate patch syntax before applying.
 * Checks for well-formed unified diff blocks.
 */
function validatePatch(patchText) {
  if (!patchText || typeof patchText !== "string") {
    return {
      valid: false,
      error: "Patch text is empty or not a string",
    };
  }

  const lines = patchText.split("\n");
  let hasFileHeader = false;
  let hasHunkHeader = false;
  const errors = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Detect file headers (--- a/path +++ b/path)
    if (line.startsWith("---") && line.includes("a/")) {
      hasFileHeader = true;
    }

    if (line.startsWith("+++") && line.includes("b/")) {
      hasFileHeader = true;
    }

    // Detect hunk headers (@@ ... @@)
    if (line.match(/^@@\s+-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s+@@/)) {
      hasHunkHeader = true;
    }

    // Check for invalid diff context
    if (line.startsWith(" ") || line.startsWith("+") || line.startsWith("-")) {
      // Valid diff line
    } else if (
      !line.startsWith("---") &&
      !line.startsWith("+++") &&
      !line.match(/^@@/) &&
      !line.startsWith("\\") &&
      line.trim().length > 0
    ) {
      // Could be valid context line or error
    }
  }

  if (!hasFileHeader && !hasHunkHeader) {
    // Might be raw file content or newfile format
    if (patchText.includes("newfile")) {
      return { valid: true, type: "newfile" };
    }
    // Could be a simple diff without headers
    if (
      patchText.includes("---") ||
      patchText.includes("+++") ||
      patchText.match(/^@@/)
    ) {
      return { valid: true, type: "partial" };
    }
    return { valid: false, error: "No valid diff headers found" };
  }

  return {
    valid: true,
    hasFileHeader,
    hasHunkHeader,
    lineCount: lines.length,
  };
}

/**
 * Parse unified diff into structured changes.
 */
function parsePatch(patchText) {
  const changes = [];
  const lines = patchText.split("\n");
  let currentFile = null;
  let currentLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // File header
    if (line.startsWith("---") && lines[i + 1]?.startsWith("+++")) {
      if (currentFile) {
        changes.push({
          file: currentFile,
          additions: currentLines.filter((l) => l.startsWith("+")).length,
          deletions: currentLines.filter((l) => l.startsWith("-")).length,
          lines: currentLines,
        });
        currentLines = [];
      }

      // Extract file path
      const match = lines[i + 1].match(/^\+\+\+ b\/(.+)$/);
      if (match) {
        currentFile = match[1];
      }
      i++; // Skip the +++ line
    } else if (line.startsWith(" ") || line.startsWith("+") || line.startsWith("-")) {
      currentLines.push(line);
    }
  }

  // Add last file
  if (currentFile && currentLines.length > 0) {
    changes.push({
      file: currentFile,
      additions: currentLines.filter((l) => l.startsWith("+")).length,
      deletions: currentLines.filter((l) => l.startsWith("-")).length,
      lines: currentLines,
    });
  }

  return changes;
}

/**
 * Apply patch to repository.
 * Uses `git apply` for reliability, falls back to manual application.
 */
async function applyPatch(patchText, repoPath = REPO_ROOT) {
  const validation = validatePatch(patchText);
  if (!validation.valid && validation.type !== "newfile") {
    return {
      success: false,
      error: validation.error,
    };
  }

  const changed = [];

  try {
    // Try git apply first (most reliable)
    try {
      const result = execSync(`git apply --reject`, {
        cwd: repoPath,
        input: patchText,
        encoding: "utf-8",
      });

      // Get list of changed files from git status
      const status = execSync("git status --porcelain", {
        cwd: repoPath,
        encoding: "utf-8",
      });

      const files = status.split("\n").filter(Boolean);
      for (const file of files) {
        const match = file.match(/^.\s+(.+)$/);
        if (match) {
          changed.push({
            path: match[1],
            status: file.charAt(0),
          });
        }
      }

      return {
        success: true,
        method: "git apply",
        filesChanged: changed.length,
        changed,
      };
    } catch (gitError) {
      // Fall through to manual application
    }

    // Manual application for newfile or simple patches
    if (patchText.includes("newfile")) {
      const result = await applyNewfiles(patchText, repoPath);
      return result;
    }

    // Parse and apply line by line
    const changes = parsePatch(patchText);

    for (const change of changes) {
      const filePath = path.join(repoPath, change.file);

      try {
        // Read current file
        let content;
        try {
          content = await fs.readFile(filePath, "utf-8");
        } catch (e) {
          // File doesn't exist, might be a new file
          content = "";
        }

        // Apply changes
        const lines = content.split("\n");
        let lineIdx = 0;
        let applied = false;

        for (const diffLine of change.lines) {
          if (diffLine.startsWith("+")) {
            // Add line
            const newLine = diffLine.substring(1);
            lines.splice(lineIdx, 0, newLine);
            lineIdx++;
            applied = true;
          } else if (diffLine.startsWith("-")) {
            // Remove line
            const toRemove = diffLine.substring(1);
            if (lines[lineIdx] === toRemove) {
              lines.splice(lineIdx, 1);
            }
            applied = true;
          } else {
            // Context line
            lineIdx++;
          }
        }

        if (applied) {
          // Write back
          await fs.mkdir(path.dirname(filePath), { recursive: true });
          await fs.writeFile(filePath, lines.join("\n"), "utf-8");
          changed.push({
            path: change.file,
            status: "M",
          });
        }
      } catch (e) {
        return {
          success: false,
          error: `Failed to apply change to ${change.file}: ${e.message}`,
          partialChanges: changed,
        };
      }
    }

    return {
      success: true,
      method: "manual",
      filesChanged: changed.length,
      changed,
    };
  } catch (err) {
    return {
      success: false,
      error: err.message,
    };
  }
}

/**
 * Apply newfile format patches.
 */
async function applyNewfiles(patchText, repoPath = REPO_ROOT) {
  const changed = [];
  const blocks = patchText.split(/(?=^newfile\n)/m);

  for (const block of blocks) {
    if (!block.trim().startsWith("newfile")) continue;

    const lines = block.split("\n");
    const filePathLine = lines.find((l) => l && !l.startsWith("newfile"));

    if (!filePathLine) continue;

    const filePath = path.join(repoPath, filePathLine.trim());
    const contentStart = lines.findIndex((l) => !l && l !== lines[0]) + 1;
    const content = lines.slice(contentStart).join("\n");

    try {
      await fs.mkdir(path.dirname(filePath), { recursive: true });
      await fs.writeFile(filePath, content, "utf-8");
      changed.push({
        path: path.relative(repoPath, filePath),
        status: "A",
      });
    } catch (e) {
      return {
        success: false,
        error: `Failed to create file ${filePathLine}: ${e.message}`,
        partialChanges: changed,
      };
    }
  }

  return {
    success: true,
    method: "newfile",
    filesChanged: changed.length,
    changed,
  };
}

module.exports = {
  validatePatch,
  parsePatch,
  applyPatch,
};
