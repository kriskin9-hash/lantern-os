/**
 * Convergence Kernel wrapper for dream-chat integration.
 * Bridges JavaScript dream-chat with Python Convergence Core.
 * wq-015: Dream-chat uses Kernel instance for Remember + Reason stages.
 */

const { spawn } = require("child_process");
const path = require("path");

/**
 * Initialize kernel via Python subprocess.
 * Returns kernel state + methods to query memory, emit records, etc.
 */
async function initializeKernel() {
  return new Promise((resolve, reject) => {
    const script = path.join(__dirname, "..", "..", "src", "convergence", "kernel.py");
    const proc = spawn("python", [script], {
      cwd: path.join(__dirname, "..", ".."),
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      if (code !== 0) {
        console.error(`Kernel init error: ${stderr}`);
        return reject(new Error(`Kernel initialization failed: ${stderr}`));
      }

      try {
        const kernelState = JSON.parse(stdout);
        resolve(kernelState);
      } catch (e) {
        reject(new Error(`Invalid JSON from kernel init: ${e.message}`));
      }
    });

    proc.on("error", (err) => {
      reject(err);
    });
  });
}

/**
 * Query memory via Python Memory.query() interface.
 * Called during dream-chat reasoning to ground responses in memory.
 */
async function queryMemory(pattern, minConfidence = 0.5, limit = 10) {
  return new Promise((resolve, reject) => {
    const script = path.join(__dirname, "..", "..", "src", "convergence", "memory_query.py");
    const args = [
      "--pattern", pattern,
      "--min-confidence", minConfidence.toString(),
      "--limit", limit.toString(),
    ];

    const proc = spawn("python", [script, ...args], {
      cwd: path.join(__dirname, "..", ".."),
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      if (code !== 0) {
        console.error(`Memory query error: ${stderr}`);
        return reject(new Error(`Memory query failed: ${stderr}`));
      }

      try {
        const results = JSON.parse(stdout);
        resolve(results);
      } catch (e) {
        reject(new Error(`Invalid JSON from memory query: ${e.message}`));
      }
    });

    proc.on("error", (err) => {
      reject(err);
    });
  });
}

/**
 * Singleton kernel instance (lazy-loaded on first use).
 */
let kernelInstance = null;
let kernelInitPromise = null;

/**
 * Get or initialize kernel (singleton pattern).
 */
async function getKernel() {
  if (kernelInstance) {
    return kernelInstance;
  }

  if (!kernelInitPromise) {
    kernelInitPromise = initializeKernel();
  }

  try {
    kernelInstance = await kernelInitPromise;
    return kernelInstance;
  } catch (err) {
    console.error("Failed to initialize kernel:", err.message);
    kernelInitPromise = null; // Reset on failure for retry
    throw err;
  }
}

module.exports = {
  getKernel,
  queryMemory,
  initializeKernel,
};
