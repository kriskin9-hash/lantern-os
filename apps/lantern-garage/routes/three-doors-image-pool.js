/**
 * Three Doors Image Pool Routes
 *
 * GET /api/three-doors/image-pool/random?sceneKey=<key>
 *   Returns a lore-aware image selection from the configured pool.
 *   Response: { ok, source, sceneKey, url, reason }
 *
 * GET /api/three-doors/image-pool/file/:token
 *   Serves the image file for an opaque token returned by /random.
 *   Path traversal safe — only serves images from known pool dirs.
 *
 * Pool priority:
 *   1. THREE_DOORS_IMAGE_POOL_DIR env var (operator local pool)
 *   2. data/images/caadi/ (repo-ingested CAAD images)
 */

const path = require("path");
const fs = require("fs");
const { buildPool, pickForScene, makeToken, resolveToken } = require("../lib/image-pool");

const MIME = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif" };

module.exports = function threeDoorImagePoolRoutes(req, res, url, deps) {
  const repoRoot = deps.repoRoot || process.cwd();
  const localPoolDir = process.env.THREE_DOORS_IMAGE_POOL_DIR || "";
  const caadiDir = path.join(repoRoot, "data", "images", "caadi");

  // ── GET /api/three-doors/image-pool/random ──────────────────────────
  if (req.method === "GET" && url.pathname === "/api/three-doors/image-pool/random") {
    const sceneKey = url.searchParams.get("sceneKey") || "";

    const pool = buildPool(localPoolDir, caadiDir);
    if (!pool.length) {
      deps.sendJson(res, { ok: false, source: "none", sceneKey, url: null, reason: "pool empty — set THREE_DOORS_IMAGE_POOL_DIR or add images to data/images/caadi/" });
      return true;
    }

    const pick = pickForScene(pool, sceneKey);
    if (!pick) {
      deps.sendJson(res, { ok: false, source: "none", sceneKey, url: null, reason: "no candidates" });
      return true;
    }

    const token = makeToken(pick.source, pick.filename);
    // Never log D:\ absolute paths to the response
    deps.sendJson(res, {
      ok: true,
      source: pick.source,
      sceneKey: sceneKey || null,
      url: `/api/three-doors/image-pool/file/${token}`,
      reason: pick.reason,
    });
    return true;
  }

  // ── GET /api/three-doors/image-pool/file/:token ─────────────────────
  const fileMatch = url.pathname.match(/^\/api\/three-doors\/image-pool\/file\/([A-Za-z0-9_=-]+)$/);
  if (req.method === "GET" && fileMatch) {
    const token = fileMatch[1];
    const resolved = resolveToken(token, localPoolDir, caadiDir);

    if (!resolved) {
      deps.sendJson(res, { error: "not found or invalid token" }, 404);
      return true;
    }

    const ext = path.extname(resolved.full).toLowerCase();
    const mime = MIME[ext] || "application/octet-stream";

    res.writeHead(200, {
      "Content-Type": mime,
      "Cache-Control": "public, max-age=3600",
      "X-Pool-Source": resolved.source,
    });
    fs.createReadStream(resolved.full).pipe(res);
    return true;
  }

  return false;
};
