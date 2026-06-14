// Creator Dashboard Entry Management Routes
// Handles entry metadata, analysis, renders, and thumbnails

module.exports = async function creatorEntriesRoutes(req, res, url, deps) {
  const { sendJson, path: pathModule, repoRoot, collectRequestBody } = deps;
  const fs = require("fs");
  const entryStore = require("../lib/entry-store");

  // =========================================================================
  // GET /api/creator-entries - List all entries
  // =========================================================================
  if (url.pathname === "/api/creator-entries" && req.method === "GET") {
    try {
      const entries = entryStore.listEntries(repoRoot);
      const enriched = entries.map((entry) => ({
        ...entry,
        formattedDate: entryStore.formatTimestamp(entry.createdAt),
      }));
      sendJson(res, { entries: enriched });
      return true;
    } catch (error) {
      console.error("[creator-entries] List error:", error.message);
      sendJson(res, { error: error.message }, 500);
      return true;
    }
  }

  // =========================================================================
  // GET /api/creator-entries/:id - Get entry details
  // =========================================================================
  const entryDetailMatch = url.pathname.match(/^\/api\/creator-entries\/([^/]+)$/);
  if (entryDetailMatch && req.method === "GET") {
    try {
      const entryId = entryDetailMatch[1];
      const entry = entryStore.getEntry(repoRoot, entryId);

      if (!entry) {
        sendJson(res, { error: "Entry not found" }, 404);
        return true;
      }

      // Include analysis if available
      const analysis = entryStore.getAnalysis(repoRoot, entryId);

      sendJson(res, {
        entry: {
          ...entry,
          formattedDate: entryStore.formatTimestamp(entry.createdAt),
        },
        analysis,
      });
      return true;
    } catch (error) {
      console.error("[creator-entries] Detail error:", error.message);
      sendJson(res, { error: error.message }, 500);
      return true;
    }
  }

  // =========================================================================
  // POST /api/creator-entries - Create new entry
  // =========================================================================
  if (url.pathname === "/api/creator-entries" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);

      // Create entry with metadata
      const entry = entryStore.createEntry(repoRoot, {
        title: body.title,
        description: body.description,
        project: body.project,
        tags: body.tags,
        type: body.type || "video",
        filePath: body.filePath,
      });

      sendJson(res, { success: true, entry });
      return true;
    } catch (error) {
      console.error("[creator-entries] Create error:", error.message);
      sendJson(res, { error: error.message }, 500);
      return true;
    }
  }

  // =========================================================================
  // POST /api/creator-entries/:id/analysis - Save analysis results
  // =========================================================================
  const analysisMatch = url.pathname.match(
    /^\/api\/creator-entries\/([^/]+)\/analysis$/
  );
  if (analysisMatch && req.method === "POST") {
    try {
      const entryId = analysisMatch[1];
      const raw = await collectRequestBody(req);
      const analysis = JSON.parse(raw);

      entryStore.saveAnalysis(repoRoot, entryId, analysis);

      sendJson(res, { success: true, message: "Analysis saved" });
      return true;
    } catch (error) {
      console.error("[creator-entries] Analysis save error:", error.message);
      sendJson(res, { error: error.message }, 500);
      return true;
    }
  }

  // =========================================================================
  // POST /api/creator-entries/:id/render/:type - Save rendered video
  // =========================================================================
  const renderMatch = url.pathname.match(
    /^\/api\/creator-entries\/([^/]+)\/render\/([^/]+)$/
  );
  if (renderMatch && req.method === "POST") {
    try {
      const entryId = renderMatch[1];
      const renderType = renderMatch[2]; // highlight, variantA, variantB, variantC
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);

      if (!body.filePath) {
        sendJson(res, { error: "filePath required" }, 400);
        return true;
      }

      entryStore.saveRender(repoRoot, entryId, renderType, body.filePath);

      sendJson(res, { success: true, message: `${renderType} render saved` });
      return true;
    } catch (error) {
      console.error("[creator-entries] Render save error:", error.message);
      sendJson(res, { error: error.message }, 500);
      return true;
    }
  }

  // =========================================================================
  // POST /api/creator-entries/:id/thumbnail - Save thumbnail
  // =========================================================================
  const thumbnailMatch = url.pathname.match(/^\/api\/creator-entries\/([^/]+)\/thumbnail$/);
  if (thumbnailMatch && req.method === "POST") {
    try {
      const entryId = thumbnailMatch[1];
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);

      if (!body.filePath) {
        sendJson(res, { error: "filePath required" }, 400);
        return true;
      }

      entryStore.saveThumbnail(repoRoot, entryId, body.filePath);

      sendJson(res, { success: true, message: "Thumbnail saved" });
      return true;
    } catch (error) {
      console.error("[creator-entries] Thumbnail save error:", error.message);
      sendJson(res, { error: error.message }, 500);
      return true;
    }
  }

  // =========================================================================
  // PUT /api/creator-entries/:id - Update entry metadata
  // =========================================================================
  const updateMatch = url.pathname.match(/^\/api\/creator-entries\/([^/]+)$/);
  if (updateMatch && req.method === "PUT") {
    try {
      const entryId = updateMatch[1];
      const raw = await collectRequestBody(req);
      const updates = JSON.parse(raw);

      const entry = entryStore.updateEntry(repoRoot, entryId, updates);

      sendJson(res, { success: true, entry });
      return true;
    } catch (error) {
      console.error("[creator-entries] Update error:", error.message);
      sendJson(res, { error: error.message }, 500);
      return true;
    }
  }

  return false;
};
