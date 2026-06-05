/**
 * cloud-server.js — Railway / Render / cloud deploy entry point
 *
 * Thin wrapper over server.js that enforces cloud defaults:
 *   PORT env var → binds 0.0.0.0 (Railway sets this automatically)
 *   LANTERN_REPO_ROOT env var → override for cloud filesystem layout
 *
 * All routes, streaming, and settings are identical to local server.js.
 * No duplication — single source of truth.
 */
process.env.PORT = process.env.PORT || "8080"; // Railway injects PORT; default 8080 for other clouds
require("./server.js");
