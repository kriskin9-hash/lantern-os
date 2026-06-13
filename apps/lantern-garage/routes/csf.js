"use strict";

const { getDictStats, readDeltas } = require("../lib/csf-delta-store");

module.exports = async function csfRoutes(req, res, url) {
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

  return false;
};
