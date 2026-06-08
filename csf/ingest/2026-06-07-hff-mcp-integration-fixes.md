# HFF / MCP Integration Fixes — 2026-06-07

## Issues Found

### 1. mesh_bridge.py: duplicate peer entries on re-registration
**Location:** `src/mcp_server/mesh_bridge.py:74-96`  
**Problem:** `register_peer()` generates a new `peer_id = str(uuid.uuid4())[:8]` on every call. When a peer re-registers (e.g. after restart), it gets a *new* ID instead of updating the existing entry. The docstring claims "re-register an existing one" but the implementation never looks up existing peers by name or URL.  
**Impact:** Mesh topology reports inflated peer counts; dispatched calls may target stale entries.  
**Fix:** Look up existing peer by `mcp_url` or `name` before generating a new ID; update `last_seen` and `status` in place.

### 2. flourishing.js: hffReady flag is set but never consumed
**Location:** `apps/lantern-garage/routes/flourishing.js:11,45-52`  
**Problem:** The 3-second health probe sets `hffReady = true/false`, but `proxyRequest()` never checks it. On the first request after server start, HFF may still be initializing, causing an immediate 502.  
**Impact:** First `/flourishing` or `/api/flourishing/*` request often fails with 502 Bad Gateway.  
**Fix:** Before proxying, check `hffReady`; if false and HFF is still starting, return a 503 with `Retry-After` header instead of forwarding to a dead port.

### 3. (Documentation note) surfaces.js /hff vs /flourishing split
**Location:** `apps/lantern-garage/routes/surfaces.js:10-13`  
**Observation:** `/hff` serves the static `public/hff/index.html` (intentional phase-1 direct-link surface). The actual HFF Flask dashboard is proxied at `/flourishing`. The codemap trace 5b labels `/hff` as "HFF dashboard" which is architecturally misleading. No code change needed yet — this is a claim-boundary / design doc issue.

## Files to Change
- `src/mcp_server/mesh_bridge.py` — peer re-registration dedup
- `apps/lantern-garage/routes/flourishing.js` — readiness gate before proxy

## Effort
Small — two focused edits, no schema changes.
