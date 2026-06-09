# Three Doors Game — Backlog

**Last Updated:** 2026-06-08  
**Status:** Active development with trained LoRA model available

---

## Priority 0 — Critical (Blockers)

### P0-1: Integrate Trained LoRA into Image Generation
**Status:** Model trained, not integrated  
**Location:** `scripts/generate-with-trained-lora.py` → `apps/lantern-garage/lib/three-doors-chat.js`

**Problem:** LoRA weights trained on 195 door images are available but not wired into the Three Doors game flow. Users see image prompts but no images are generated.

**Implementation:**
- Add `/api/dream/doors/image` endpoint to `routes/dream.js`
- Wire trained LoRA generation into Python engine or create new image service
- Update frontend to call image API and display generated door images
- Cache generated images per scene to avoid re-generation

**Acceptance:** Three Doors game displays actual generated door images using trained style.

---

### P0-2: Fix Dual Implementation Confusion
**Status:** Dead code exists  
**Location:** `lib/dream-chat.js:124-178` vs `lib/three-doors-chat.js:79`

**Problem:** Two separate implementations with different behaviors. Ollama LLM path in `lib/dream-chat.js` is dead code — never executed by frontend.

**Implementation:**
- Remove dead LLM path from `lib/dream-chat.js` OR wire it into frontend if intentional
- Consolidate to single implementation in `lib/three-doors-chat.js`
- Update codemap to reflect actual implementation

**Acceptance:** Single code path for Three Doors game logic, no dead code.

---

### P0-3: Add Subprocess Timeout
**Status:** Security vulnerability  
**Location:** `routes/dream.js:252-264`

**Problem:** Python subprocess spawn has no explicit timeout. Hung Python process blocks Node.js server thread (DoS vulnerability).

**Implementation:**
- Add 30s timeout to Promise wrapper (similar to Ollama timeout in `lib/dream-chat.js:163`)
- Add error handling for timeout scenarios
- Log timeout events for monitoring

**Acceptance:** All subprocess calls have explicit timeout protection.

---

## Priority 1 — High (User Experience)

### P1-1: Unify Trigger Detection
**Status:** Inconsistent  
**Location:** `public/js/dream-chat.js:284` vs `lib/three-doors-chat.js:5-9`

**Problem:** Frontend regex only matches bang commands (`!three-doors`), but helper library supports 8 triggers including "play three doors", "door game".

**Implementation:**
- Expand frontend regex to match all supported triggers
- OR restrict helper library to bang-command-only
- Document trigger behavior in SKILL.md

**Acceptance:** All documented triggers work consistently in UI.

---

### P1-2: Add Client-Side Choice Validation
**Status:** Missing  
**Location:** `public/js/dream-chat.js:1147-1161`

**Problem:** Frontend sends whatever door label user clicks without pre-validation. Unnecessary API round-trips for invalid choices.

**Implementation:**
- Validate choice against `doorsGameState.doors` before API call
- Show inline error for invalid choices
- Disable invalid door buttons visually

**Acceptance:** Invalid choices caught client-side before API call.

---

### P1-3: Fix State Management
**Status:** Stale on refresh  
**Location:** `public/js/dream-chat.js` (global `doorsGameState`)

**Problem:** Game state in global variable with no cleanup on refresh. Users lose progress with no warning.

**Implementation:**
- Add `beforeunload` handler to warn about unsaved game
- Implement session storage for persistence across refreshes
- Add explicit "save/resume" UI buttons
- Add "Reset Game" button in Three Doors UI

**Acceptance:** Game state persists across refreshes with user control.

---

### P1-4: Update Three Doors UI to Match Modern Design
**Status:** Outdated  
**Location:** `public/three-doors-game.html`

**Problem:** Three Doors game page doesn't match the modern cyan-accent design system applied to dream-journal and providers pages.

**Implementation:**
- Apply cyan accent color (#06b6d4) throughout
- Implement dark/light theme support
- Add modern sticky navigation
- Update typography and spacing to match UX standards
- Responsive design improvements

**Acceptance:** Three Doors page matches modern design system.

---

## Priority 2 — Medium (Features)

### P2-1: Wire Image Generation into Scene Flow
**Status:** Partial  
**Location:** `public/js/dream-chat.js:1135-1139`

**Problem:** UI displays `image_prompt` but no image generation call. Endpoint exists but not integrated.

**Implementation:**
- Call `/api/dream/doors/image` after scene generation
- Display generated image above door options
- Add loading state during image generation
- Fallback to prompt-only if generation fails

**Acceptance:** Door images display in game UI using trained LoRA.

---

### P2-2: Add Offline Fallback
**Status:** Missing  
**Location:** `public/js/dream-chat.js:1096-1100`

**Problem:** Frontend requires server API call. No local fallback if server down. Codemap claims "offline-capable" but implementation doesn't support it.

**Implementation:**
- Implement local JavaScript game state machine as fallback
- Detect server availability and switch modes
- Store fallback state in localStorage
- Sync with server when connection restored

**Acceptance:** Game playable offline with local state, syncs when online.

---

### P2-3: Standardize Error Handling
**Status:** Inconsistent  
**Location:** Multiple files

**Problem:** Different error handling strategies across layers. Some errors swallowed silently, others shown to user.

**Implementation:**
- Define consistent error handling strategy
- Standardize error codes and messages
- Add retry mechanism for transient errors
- User-friendly error display with actionable guidance

**Acceptance:** Consistent error UX across all Three Doors interactions.

---

### P2-4: Add Game Export/Import UI
**Status:** Backend exists, no UI  
**Location:** CSF export format defined in SKILL.md

**Problem:** CSF export/import format defined but no UI for users to export/import game state.

**Implementation:**
- Add "Export Game State" button in Three Doors UI
- Generate CSF ingest markdown block
- Add "Import Game State" file upload
- Validate imported state format
- Merge imported state with current session

**Acceptance:** Users can export/import game state via UI.

---

## Priority 3 — Low (Polish)

### P3-1: Fix Global Namespace Pollution
**Status:** Minor  
**Location:** `public/js/dream-chat.js:1147`

**Problem:** `window.chooseDoorsPath` is global function. Could conflict with other scripts.

**Implementation:**
- Use namespaced approach: `window.LanternDoors.choosePath`
- OR use event delegation pattern

**Acceptance:** No global namespace pollution.

---

### P3-2: Make Ollama Port Configurable
**Status:** Partially addressed  
**Location:** `lib/dream-chat.js:128`

**Problem:** Default Ollama URL uses hardcoded port 11434 despite `OLLAMA_BASE_URL` env var.

**Implementation:**
- Parse port from `OLLAMA_BASE_URL` if present
- Remove hardcoded port fallback
- Document port configuration in README

**Acceptance:** Ollama port fully configurable via environment.

---

### P3-3: Update Codemap Documentation
**Status:** Outdated  
**Location:** Codemap vs actual implementation

**Problem:** Codemap describes LLM-first flow but actual implementation is API-first with Python engine.

**Implementation:**
- Update codemap to reflect actual implementation
- OR update implementation to match codemap design
- Document architectural decision

**Acceptance:** Documentation matches implementation.

---

## New Opportunities (Post-Training)

### N1: Batch Door Image Generation
**Status:** Script available  
**Location:** `scripts/generate-with-trained-lora.py`

**Opportunity:** Generate large batch of door images for asset library using trained LoRA.

**Implementation:**
- Create admin UI for batch generation
- Generate 50-100 door variations
- Catalog and tag generated images
- Integrate into game as pre-generated assets

**Acceptance:** Asset library of generated door images available.

---

### N2: Style Transfer for User Uploads
**Status:** New feature idea

**Opportunity:** Allow users to upload their own door images and apply trained style via LoRA.

**Implementation:**
- Add image upload UI
- Apply LoRA style transfer to user images
- Generate stylized door images from user concepts
- Integrate into game as custom doors

**Acceptance:** Users can generate custom-styled door images.

---

### N3: LoRA Fine-Tuning Pipeline
**Status:** Manual process  
**Location:** `scripts/train-door-images-lora.py`

**Opportunity:** Automate LoRA retraining as new door images are added to training set.

**Implementation:**
- Add training data collection from gameplay
- Automated retraining pipeline
- Version LoRA checkpoints
- A/B test new LoRA versions

**Acceptance:** Automated LoRA improvement pipeline.

---

## Dependencies

- **P0-1** depends on: P0-2 (clean code before integration)
- **P1-4** depends on: UX overhaul completion (done)
- **P2-1** depends on: P0-1 (LoRA integration)
- **N1** depends on: P0-1 (LoRA integration)
- **N2** depends on: P0-1 + P2-1 (LoRA + image generation flow)
- **N3** depends on: N1 (asset library)

---

## Recommended Sprint Order

**Sprint 1 (Critical Path):**
1. P0-2: Fix dual implementation confusion
2. P0-3: Add subprocess timeout
3. P0-1: Integrate trained LoRA into image generation

**Sprint 2 (UX Foundation):**
4. P1-1: Unify trigger detection
5. P1-2: Add client-side validation
6. P1-3: Fix state management
7. P1-4: Update Three Doors UI to modern design

**Sprint 3 (Feature Complete):**
8. P2-1: Wire image generation into scene flow
9. P2-4: Add game export/import UI
10. P2-2: Add offline fallback
11. P2-3: Standardize error handling

**Sprint 4 (Polish & Expansion):**
12. P3-1 through P3-3: Polish items
13. N1: Batch door image generation
14. N2: Style transfer for user uploads
15. N3: LoRA fine-tuning pipeline

---

## Metrics

**Current State:**
- Trained LoRA model: ✓ Complete (195 images, 3 epochs, final loss 0.1471)
- Generated sample images: ✓ Complete (5 images)
- Code integration: ✗ Not started
- UX modernization: ✗ Not started
- Known issues: 12 (3 critical, 4 high, 3 medium, 2 low)

**Target State:**
- LoRA integrated into game flow
- Modern UI matching design system
- All critical issues resolved
- Offline capability
- Export/import functionality
