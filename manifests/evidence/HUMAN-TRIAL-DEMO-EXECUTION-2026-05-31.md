# Human Trial Demo Execution

**Demo ID:** HTD-2026-05-31-001  
**Operator:** Alex Place  
**Status:** LIVE EXECUTION  
**Start Time:** 2026-05-31T11:20:00-04:00

---

## Pre-Demo Checklist

- [x] Convergence loop run (0 actionable issues)
- [x] MCP canary validated (31 sources, all safe)
- [x] ASI boundaries reviewed (references only, no capability claims)
- [x] Safety gates configured (Windsurf hooks active)
- [x] Rollback path documented
- [x] 5 outreach sends recorded
- [x] Itch.io page published
- [x] COMET LEAP artifacts promoted

---

## Demo Configuration

**Environment:** Production (demo mode)  
**Kill Switch:** Active (`data/kalshi/LIVE-KILL-SWITCH` present)  
**Live Enabled:** `LANTERN_LIVE_ENABLED=0` (default safe)  
**Audit Logging:** Enabled  
**Participant:** Operator self-demo (Alex Place)

---

## Demo Phases

### Phase 1: Convergence Verification (5 min)

**Actions:**
1. Run `Invoke-LanternConvergenceLoop.ps1`
2. Confirm 0 actionable issues
3. Verify held issues understood

**Expected Result:** Clean convergence, ready state confirmed

### Phase 2: MCP Canary Validation (5 min)

**Actions:**
1. Run `Invoke-McpCanaryTestEngine.ps1`
2. Verify all 31 sources safe
3. Confirm no tool execution warnings

**Expected Result:** All sources validated, canProceed=True

### Phase 3: Fleet Health Demo (5 min)

**Actions:**
1. Open dashboard (`apps/lantern-garage/public/index.html`)
2. Show fleet health indicators
3. Display agent ring status (12 steps, 36 slots, 64 pool target)

**Expected Result:** Healthy status, all indicators green

### Phase 4: $1000 Demo Offer (10 min)

**Actions:**
1. Navigate to `demo-1000.html`
2. Present founding seat offer
3. Show RAG memory, URL bundle, command lane
4. Record participant feedback

**Expected Result:** Clear offer presentation, feedback captured

### Phase 5: Evidence Receipt Generation (5 min)

**Actions:**
1. Run `Invoke-ReceiptGenerator.ps1`
2. Generate demo execution receipt
3. Update `human-trial-gate-results.json`

**Expected Result:** Receipt generated, readiness scores updated

---

## Safety Boundaries

**Active Constraints:**
- No live Kalshi orders without explicit "go live" in session
- No AWS mutations without credentials check
- No Discord bot commands without scope verification
- No disk/BCD/firmware changes (boot held)
- No token issuance or investment advice

**Break-Glass:**
- Kill switch: Delete `data/kalshi/LIVE-KILL-SWITCH`
- Abort: Ctrl+C or close terminal
- Rollback: `git reset --hard` to last known good

---

## Post-Demo Actions

- [ ] Update `data/arc-reactor/status.json` confidence scores
- [ ] Record participant feedback
- [ ] Generate trial receipt
- [ ] Push changes to master
- [ ] Update Movie 2 readiness percentage

---

## Success Criteria

- All phases complete without errors
- Safety boundaries respected throughout
- Receipt generated with timestamps
- Human trial readiness >70%

---

*Operator-approved live demo execution 2026-05-31*
