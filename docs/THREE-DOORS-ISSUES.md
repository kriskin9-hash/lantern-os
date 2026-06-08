# Three Doors Integration — Issues Found

**Review Date:** 2026-06-08  
**Scope:** Three Doors Dream Chat UX and JS Integration codemap review

---

## Critical Issues

### 1. Dual Implementation Confusion (CRITICAL)
**Location:** `apps/lantern-garage/lib/dream-chat.js` vs `apps/lantern-garage/lib/three-doors-chat.js`

**Problem:** Two separate implementations exist with different behaviors:
- `lib/dream-chat.js:124` — `handleThreeDoorsServer()` attempts Ollama LLM first, falls back to Python
- `lib/three-doors-chat.js:79` — `handleThreeDoorsChat()` directly calls API
- Frontend (`dream-chat.js:290`) uses `startThreeDoors()` which calls API directly, **bypassing the LLM path entirely**

**Impact:** The Ollama LLM integration code in `lib/dream-chat.js` (lines 132-178) is dead code — never executed by the frontend.

**Recommendation:** Remove dead LLM path from `lib/dream-chat.js` or wire it into the frontend if intentional.

---

### 2. Inconsistent Trigger Detection
**Location:** `apps/lantern-garage/public/js/dream-chat.js:284` vs `apps/lantern-garage/lib/three-doors-chat.js:5-9`

**Problem:** 
- Frontend regex: `/^!(?:three-doors|threedoors|doors)\b/i` — only matches bang commands
- Helper library: Array of 8 triggers including "play three doors", "door game", etc.

**Impact:** Users typing "play three doors" won't trigger the game in the UI, despite the helper library supporting it.

**Recommendation:** Unify trigger detection. Either expand frontend regex or restrict helper library to match.

---

### 3. Missing Subprocess Timeout
**Location:** `apps/lantern-garage\routes\dream.js:252-264`

**Problem:** Python subprocess spawn has no explicit timeout. If Python engine hangs, the Node.js route hangs indefinitely.

**Impact:** DoS vulnerability — a hung Python process blocks the Node.js server thread.

**Recommendation:** Add timeout to the Promise wrapper (similar to the 30s timeout on Ollama requests in `lib/dream-chat.js:163`).

---

## High Priority Issues

### 4. Global Namespace Pollution
**Location:** `apps/lantern-garage\public\js\dream-chat.js:1147`

**Problem:** `window.chooseDoorsPath` is set as a global function. Could conflict with other scripts.

**Impact:** Potential naming collisions in larger applications or if multiple instances are loaded.

**Recommendation:** Use namespaced approach (e.g., `window.LanternDoors.choosePath`) or event delegation.

---

### 5. Stale State Management
**Location:** `apps/lantern-garage\public\js\dream-chat.js` (global `doorsGameState` variable)

**Problem:** Game state is stored in a global variable with no cleanup on page refresh or navigation.

**Impact:** Users refreshing the page lose game progress with no warning. State can become desynchronized with server.

**Recommendation:** 
- Add `beforeunload` handler to warn about unsaved game
- Consider session storage for persistence across refreshes
- Add explicit "save/resume" UI

---

### 6. No Client-Side Choice Validation
**Location:** `apps/lantern-garage\public\js\dream-chat.js:1147-1161`

**Problem:** Frontend sends whatever door label the user clicks directly to API without pre-validation.

**Impact:** Unnecessary API round-trips for invalid choices. Poor UX (delay before error).

**Recommendation:** Validate choice against current `doorsGameState.doors` before sending API request.

---

### 7. Image Generation Integration Incomplete
**Location:** `apps/lantern-garage\public\js\dream-chat.js:1135-1139`

**Problem:** UI displays `image_prompt` but there's no visible image generation call. Codemap mentions `/api/dream/doors/image` endpoint but it's not integrated into the scene rendering flow.

**Impact:** Users see Stable Diffusion prompts but no images are actually generated or displayed.

**Recommendation:** Either remove prompt display or wire in image generation API call.

---

## Medium Priority Issues

### 8. Codemap Documentation Mismatch
**Location:** Codemap vs actual implementation

**Problem:** Codemap describes LLM-first flow with game rules in system prompt, but actual implementation is API-first with Python engine.

**Impact:** Misleading documentation for developers trying to understand the system.

**Recommendation:** Update codemap to reflect actual implementation, or update implementation to match codemap design.

---

### 9. No Offline Fallback
**Location:** `apps/lantern-garage\public\js\dream-chat.js:1096-1100`

**Problem:** Frontend always requires server API call. No local fallback if server is down.

**Impact:** Codemap claims "offline-capable" but implementation requires live server.

**Recommendation:** Either remove offline claim or implement local JavaScript game state machine as fallback.

---

### 10. Error Handling Inconsistency
**Location:** Multiple files

**Problem:** 
- `lib/dream-chat.js:158` — Catches JSON parse errors silently, returns empty content
- `routes/dream.js:268` — Returns different error codes based on error message string matching
- Frontend shows error in bubble but no retry mechanism

**Impact:** Inconsistent error UX. Some errors swallowed silently, others shown to user.

**Recommendation:** Standardize error handling strategy across all layers.

---

## Low Priority Issues

### 11. Hardcoded Port in Ollama URL
**Location:** `apps/lantern-garage\lib\dream-chat.js:128`

**Problem:** Default Ollama URL uses hardcoded port 11434.

**Impact:** Less flexible for non-standard Ollama configurations.

**Recommendation:** Already partially addressed with `OLLAMA_BASE_URL` env var, but port fallback is hardcoded.

---

### 12. No Game Reset UI
**Location:** Python engine has `reset()` method, but no UI trigger

**Problem:** Users can't reset game without clearing browser storage or sending a specific API call.

**Impact:** Stuck if game state becomes corrupted or user wants to restart.

**Recommendation:** Add "Reset Game" button in the Three Doors UI.

---

## Summary Statistics

- **Critical:** 3 issues
- **High:** 4 issues  
- **Medium:** 3 issues
- **Low:** 2 issues
- **Total:** 12 issues

**Recommended Action Order:**
1. Fix dual implementation confusion (remove dead code or wire it in)
2. Add subprocess timeout (security)
3. Unify trigger detection
4. Add client-side validation
5. Fix state management
6. Complete or remove image generation integration
