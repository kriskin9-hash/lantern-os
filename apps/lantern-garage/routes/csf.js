"use strict";

const { getDictStats, readDeltas } = require("../lib/csf-delta-store");
const { execFile } = require("child_process");
const path = require("path");
const fs = require("fs");

const TESSERACT_SCRIPT = path.resolve(__dirname, "../../../scripts/csf_research_tesseract.py");
const TESSERACT_MANIFEST = path.resolve(__dirname, "../../../data/tesseract/manifest.json");

function runPython(args, repoRoot) {
  return new Promise((resolve, reject) => {
    execFile("python", args, { cwd: repoRoot, timeout: 120_000 }, (err, stdout, stderr) => {
      if (err) return reject(new Error(stderr || err.message));
      resolve(stdout.trim());
    });
  });
}

module.exports = async function csfRoutes(req, res, url, deps) {
  const { sendJson, repoRoot } = deps || {};

  if (!url.pathname.startsWith("/api/csf/")) return false;

  if (req.method === "GET" && url.pathname === "/api/csf/stats") {
    const stats = getDictStats();
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(stats));
    return true;
  }

  if (req.method === "GET" && url.pathname === "/api/csf/deltas") {
    const limit = Math.min(parseInt(url.searchParams.get("limit") || "20", 10), 200);
    const deltas = readDeltas(limit);
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(deltas));
    return true;
  }

  // POST /api/csf/tesseract/pack — compress all ingest PDFs into one CSF tesseract
  if (req.method === "POST" && url.pathname === "/api/csf/tesseract/pack") {
    try {
      const out = await runPython([TESSERACT_SCRIPT, "pack"], repoRoot);
      const manifest = fs.existsSync(TESSERACT_MANIFEST)
        ? JSON.parse(fs.readFileSync(TESSERACT_MANIFEST, "utf-8"))
        : null;
      sendJson(res, { ok: true, log: out, manifest });
    } catch (err) {
      sendJson(res, { ok: false, error: err.message }, 500);
    }
    return true;
  }

  // POST /api/csf/tesseract/unpack — read and return the manifest from the tesseract
  if (req.method === "POST" && url.pathname === "/api/csf/tesseract/unpack") {
    try {
      const out = await runPython([TESSERACT_SCRIPT, "unpack"], repoRoot);
      const manifest = fs.existsSync(TESSERACT_MANIFEST)
        ? JSON.parse(fs.readFileSync(TESSERACT_MANIFEST, "utf-8"))
        : null;
      sendJson(res, { ok: true, log: out, manifest });
    } catch (err) {
      sendJson(res, { ok: false, error: err.message }, 500);
    }
    return true;
  }

  // GET /api/csf/tesseract/status — current tesseract info without running anything
  if (req.method === "GET" && url.pathname === "/api/csf/tesseract/status") {
    if (!fs.existsSync(TESSERACT_MANIFEST)) {
      sendJson(res, { exists: false });
      return true;
    }
    const manifest = JSON.parse(fs.readFileSync(TESSERACT_MANIFEST, "utf-8"));
    const csfPath = path.resolve(__dirname, "../../../data/tesseract/research-pool.csf");
    const stat = fs.existsSync(csfPath) ? fs.statSync(csfPath) : null;
    sendJson(res, {
      exists: true,
      manifest,
      csfSize: stat ? stat.size : null,
      csfModified: stat ? stat.mtime.toISOString() : null,
    });
    return true;
  }

  return false;
};
