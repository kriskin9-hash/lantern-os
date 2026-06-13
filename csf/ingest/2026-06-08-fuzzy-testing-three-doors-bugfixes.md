# Fuzzy Testing & Three Doors Bug Fixes — Session Report

**Ingest date:** 2026-06-08  
**Agent:** Claude  
**Branch:** `claude/phase-1-three-doors-classifier` (server loaded this branch during testing)  
**Scope:** Index page APIs, Dream Chat routing, Three Doors game (`/api/dream/doors`, `/api/dream/doors/image`)

---

## 1. Fuzz Test Suite Created

**File:** `tests/test_fuzzy_index_dreamchat.js`  
**Coverage:** 134 fuzz cases across 5 categories:

| Category | Cases | What it tests |
|----------|-------|--------------|
| Index page APIs | 21 | All 8 APIs hit by `index.html` on load (`/api/health`, `/version.json`, `/api/version`, `/api/status`, `/api/pcsf/routing`, `/api/agents`, `/api/dreamer`, `/api/dream/search`) |
| Dream chat routing | 19 | Bang-command edge cases (`!three-doors`, `!swarm`, `!unknown`, XSS payloads, SQL injection, null/empty) |
| Three Doors game | 63 | `userId` fuzz (empty, null, 10k chars, XSS, path traversal, unicode), `action` fuzz, `choice` fuzz, malformed bodies, wrong HTTP methods, extra fields, oversized payload |
| Three Doors image | 11 | `doorIndex` fuzz (negative, NaN, string, null, missing) |
| Static pages | 9 | Page loads (200) and path traversal blocking (403/404) |

---

## 2. Bugs Found & Fixed

### Bug 1: 10k-char `userId` → Python `OSError: filename too long`
**Root cause:** `ThreeDoorsEngine._state_path()` sanitizes but does not truncate; Windows MAX_PATH exceeded.  
**Fix:** `userId.slice(0, 256)` in `routes/dream.js` before passing to Python engine.  
**Files:** `apps/lantern-garage/routes/dream.js` (`/api/dream/doors` + `/api/dream/doors/image`)

### Bug 2: `"null"` body → TypeError on `body.userId`
**Root cause:** `JSON.parse("null")` returns `null`; accessing `.userId` throws.  
**Fix:** Guard after parse — if result is not a plain object, default to `{}`.  
**Files:** `apps/lantern-garage/routes/dream.js`

### Bug 3: Malformed JSON → 500 instead of 400
**Root cause:** `JSON.parse` throws caught by outer try/catch, returns 500.  
**Fix:** Inner try/catch on `JSON.parse` returns `{ error: "invalid_json" }` with HTTP 400.  
**Files:** `apps/lantern-garage/routes/dream.js`

### Bug 4: `doorIndex: "A"` → `SyntaxError: invalid syntax` in Python
**Root cause:** `Number("A")` = `NaN`; `JSON.stringify(NaN)` → `null`; Python compares `None < len(suggestions)` raising TypeError.  
**Fix:** `Number.isFinite(rawDoorIdx) && rawDoorIdx >= 0 ? Math.floor(rawDoorIdx) : 0`.  
**Files:** `apps/lantern-garage/routes/dream.js` (`/api/dream/doors/image`)

### Bug 5: Oversized payload → `ECONNRESET`
**Root cause:** `collectRequestBody` called `req.destroy()` on size limit, killing socket before 413 response could be written.  
**Fix:** `req.removeAllListeners("data"); req.resume();` (drain stream, don't destroy).  
**Files:** `apps/lantern-garage/lib/http-utils.js`

### Bug 6: CRLF line endings → Python `SyntaxError: invalid syntax`
**Root cause:** Windows CRLF (`\r\n`) in template literal combined with `\\` continuation. Python normalizes `\\\r\n` into a single logical line, merging `if...elif` into illegal syntax.  
**Fix:** Rewrote the multiline Python inline script as a single line using ternary expressions.  
**Before:**
```javascript
const script = `import sys,json; ... e=ThreeDoorsEngine(req['userId']); \\
result = e.to_api_response(); \\
if req['action'] in [...]: ... \\
elif req['action']=='choose': ... \\
print(json.dumps(result))`;
```
**After:**
```javascript
const script = `import sys,json; ... a=req['action']; result=(e.to_api_response(e.start_game()) if a=='start' else (e.to_api_response(e.reset()) if a=='reset' else ((lambda s: e.to_api_response(s) if s else {"error":"invalid_choice"})(e.choose_door(req['choice'])) if a=='choose' else e.to_api_response()))); print(json.dumps(result))`;
```
**Files:** `apps/lantern-garage/routes/dream.js`

---

## 3. Validation Commands

Run the fuzz suite (server must be on port 4177):
```bash
node tests/test_fuzzy_index_dreamchat.js
```

Target: **134/134 pass, 0 failures**.

---

## 4. PR #276 Conflict Resolution (Side Task)

**PR:** `chore(deps): upgrade PyJWT, relax AI/ML pins, drop unused libs`  
**Conflict:** `requirements.txt` — master had added new packages (`openai-agents`, `urllib3`, `yt-dlp`, `apscheduler`) and stricter pins while PR branch was in flight.  
**Resolution:** Merged via git worktree (main index locked by concurrent agent). Kept master's new packages + newer pins, applied PR's removals (`sentence-transformers`, `librosa`, `PyGithub`, `pytest-asyncio`) and `langchain>=0.1.1` relaxation.  
**Outcome:** PR was closed by user before merge. Branch `chore/requirements-dep-upgrade` is now conflict-free if reopened.

---

## 5. Key Lessons

- **Windows CRLF + `python -c` multiline strings = danger.** Always use single-line Python scripts for `spawn(py, ["-c", script])` on Windows, or write the script to a temp file.
- **`req.destroy()` before response = ECONNRESET.** Drain with `req.resume()` when rejecting oversized bodies.
- **Validate `Number()` results.** `Number("A")` → `NaN` → `null` in JSON → Python `None` → cryptic TypeError.
- **Guard `JSON.parse` return type.** `"null"` and `"[]"` are valid JSON but not objects.
- **Fuzz `userId` aggressively.** Long strings, path traversal, null bytes, unicode — all found real crashes.
