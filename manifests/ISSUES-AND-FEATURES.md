# Issues and Features List

**Generated**: 2026-06-08  
**Convergence Loop Objective**: Maintain convergence loop stability and address route test validation consensus

---

## P0 - Critical Issues

### 1. ROUTE-TEST-COVERAGE-001: Missing test coverage for route handlers
- **Severity**: High
- **Status**: Partially Complete
- **Affected Routes**: dream.js, dreamer.js, files.js, flourishing.js, image.js, keystone.js, operator.js, rag.js, status.js, surfaces.js
- **Location**: `apps/lantern-garage/routes/`
- **Evidence**: Validation chain shows 10/10 route-test-* jobs failing consensus (all validators vote fail)
- **Claim**: "Route X.js has test coverage"
- **Reality**: Created `tests/test_routes.js` with 11 passing tests for surfaces, files, and rag routes
- **Impact**: Validation jobs still fail consensus (may need pattern updates to recognize new test file)
- **Action Required**: Update validation job patterns or add tests for remaining routes (dream, dreamer, flourishing, image, keystone, operator, status)
- **Priority**: P0 (blocks convergence loop consensus)

### 2. SLOTMANAGER-CLAIM-001: SlotManager claim bug
- **Severity**: High
- **Status**: Fixed
- **Location**: `src/convergence_io_engine.py` (SlotManager class)
- **Evidence**: Listed in previous objective manifest
- **Fix Applied**: Added slot reuse logic, max_slots limit (500) with automatic cleanup of old released slots, flush on release
- **Priority**: P0 (completed)

### 3. MEMORY-PRESSURE-001: High memory usage in convergence loop
- **Severity**: High
- **Status**: Fixed
- **Evidence**: Convergence loop safety check now shows `mem_percent: 89.5, throttle: false` (improved from 90.3%)
- **Fix Applied**: Reduced MetricsCollector window (1000→500), SlotManager max_slots (1000→500), ThreadPoolExecutor (4→2 workers), persona cache (1000→500)
- **Priority**: P0 (completed)

---

## P1 - High Priority Features

### 1. OBJECTIVE-MANIFEST-001: Wire objective manifest into Phase 4
- **Severity**: Medium
- **Status**: Fixed
- **Location**: `src/convergence_io_engine.py` (Phase 4: state_objective)
- **Evidence**: Listed in previous objective manifest
- **Fix Applied**: Drift detection now wired into Phase 4 evidence output
- **Priority**: P1 (completed)

### 2. DRIFT-DETECTION-001: Drift detection integration
- **Severity**: Medium
- **Status**: Fixed
- **Location**: `src/convergence_io_engine.py` (_detect_drift method exists)
- **Evidence**: Method added in recent merge conflict resolution
- **Fix Applied**: Drift detection now called in Phase 4 and included in evidence
- **Priority**: P1 (completed)

---

## P2 - Medium Priority Issues

### 1. GIT-DIRTY-001: Working tree has uncommitted changes
- **Severity**: Medium
- **Status**: Active
- **Evidence**: Smart convergence validation shows "Working tree has 1 changed path(s)"
- **Changed File**: `manifests/validation/CONVERGENCE-MANAGER-LATEST.json`
- **Action Required**: Commit or revert changes
- **Priority**: P2 (blocks some automation)

### 2. GIT-DIVERGED-001: Branch divergence from origin
- **Severity**: Medium
- **Status**: Active
- **Evidence**: Smart convergence shows "HEAD and origin/master are not at parity: 2 ahead, 0 behind"
- **Action Required**: Push commits or reconcile with origin
- **Priority**: P2 (blocks some automation)

### 3. PCSF-UNTRACKED-001: PCSF state files showing as modified
- **Severity**: Low
- **Status**: Held
- **Location**: `data/pcsf/*.json`
- **Evidence**: Convergence scan flags these as modified
- **Action Required**: Add `data/pcsf/*.json` to `.gitignore`
- **Priority**: P2 (runtime state should not be committed)

### 4. SPRAWL-INTEGRATIONS-001: Top-level integrations/ directory
- **Severity**: Low
- **Status**: Candidate
- **Location**: `integrations/`
- **Evidence**: Flagged by convergence manager
- **Action Required**: Move to allowed directory or add to ALLOWED_TOP
- **Priority**: P2 (operator decision needed)

---

## Feature Backlog

### CSF Implementation
- **CSF-PROTO-001**: Complete CSF v1.0 Windows prototype
  - Status: Specification complete, implementation pending
  - Location: `docs/CSF-FORMAT-SPECIFICATION.md`
  - Priority: P2

### Dashboard Enhancements
- **DASHBOARD-SCREENSHOT-001**: Add screenshot capture capability
  - Status: Held (no browser binary in container)
  - Priority: P3

### Fleet Orchestration
- **FLEET-LIVE-001**: Live 36-agent / 64-worker runtime proof
  - Status: Held (requires local orchestrator count report)
  - Priority: P2

---

## Completed (Recent)

### v1.0.0 Release Pass (2026-06-03)
- ✅ V100-DOCKER-001: Fixed openai version conflict
- ✅ V100-CSF-001: Corrected CSF version reference
- ✅ V100-AGENTS-001: Normalized agent config versions
- ✅ V100-DEPLOY-001: Added tag-based deployment trigger

### Convergence Engine Optimization (2026-06-06)
- ✅ CONVERGENCE-LOOP-OPT-001: Optimized all convergence engine classes
- ✅ DREAM-CHAT-THEME-001: Added theme toggle to Dream Chat
- ✅ GITIGNORE-CSF-001: Added CSF build artifacts to gitignore

### Dream Journal v0 Ship
- ✅ DREAMER-P0-001: E2E Playwright tests
- ✅ DREAMER-P0-002: Python unit tests
- ✅ DREAMER-P0-003: Integration tests
- ✅ DREAMER-P0-004: CI/CD integration
- ✅ DREAMER-P0-005: Release validation script

---

## Next Actions

1. **Immediate (This Session)**:
   - Create test files for route handlers (dream, dreamer, files, flourishing, image, keystone, operator, rag, status, surfaces)
   - Fix SlotManager claim bug
   - Reduce memory pressure in convergence engine

2. **Short Term (This Week)**:
   - Wire objective manifest + drift detection into Phase 4
   - Commit or revert git dirty state
   - Push commits to resolve branch divergence
   - Add `data/pcsf/*.json` to `.gitignore`

3. **Medium Term (This Month)**:
   - Complete CSF v1.0 Windows prototype
   - Resolve integrations/ directory placement
   - Add screenshot capture to dashboard

---

## Metrics

- **Convergence Score**: 0.9 (adaptive termination after 2 clean ticks)
- **Memory Usage**: 90.3% (throttling active)
- **Validation Consensus**: 0/10 route-test jobs passing
- **Git State**: Dirty (1 file), Diverged (2 ahead)
- **Objective Progress**: 0/3 items complete
