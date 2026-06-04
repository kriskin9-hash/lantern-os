# Evidence Consistency Audit: 2026-05-03

**Auditor:** Claude  
**Date:** 2026-05-03  
**Status:** 🔴 **CONTRADICTIONS FOUND** — 5 evidence gaps requiring cleanup  

---

## Summary

Repository documentation contains 5 evidence gaps where docs describe features/config that conflict with actual code state or are stale/never removed. These must be cleaned before stable operations (per drift-prevention-contract.md Rule 1).

---

## Contradiction #1: Headless Slot Configuration (CRITICAL)

### Evidence Gap
**Location:** Multiple places describe or reference headless slot configuration inconsistently.

**What Docs Say:**
- `docs/agent-start-here.md` (line 5): References `AGENTS.md` (doesn't exist)
- RC3 roadmap planning: "Restore OpenHands Headless Service or Migrate to Claude CLI"
- Various handoff docs: Mix of openhands and claude-cli references

**What Code Does:**
- `config/agents.json` (slot 5): Current headless configuration TBD (needs verification)
- Script: `scripts/Invoke-OpenHandsAgent.ps1` exists (legacy?)
- Startup: `Start-Headless.ps1` delegates to scripts, actual agent unclear

**Actual Status:**
- OpenHands installation unknown (was it ever installed?)
- Claude CLI availability assumed but not pre-flighted
- No active headless slot evidence in PR/issue history

**Contradiction:** Docs claim headless will be "restored" or "migrated", but unclear what current state is.

### Cleanup Action
**Priority:** P0 (RC3 Phase 1.3 blocker)
```
[ ] Verify actual headless slot in config/agents.json (lines 1-10)
[ ] Delete scripts/Invoke-OpenHandsAgent.ps1 if not used (confirm with grep)
[ ] Update docs to reflect decision: "migrate to Claude CLI" or "restore OpenHands with X version"
[ ] Update AGENT_RESUME_SESSION.md with actual slot 5 status
[ ] Commit decision with clear message: "doc: clarify headless slot configuration (RC3 Phase 1.3)"
```

---

## Contradiction #2: Agent Model References (MEDIUM)

### Evidence Gap
**Location:** Multiple files reference agent models with different version claims.

**What Docs Say:**
- `docs/model-guides/claude.md`: Claude 3.5 Sonnet
- `docs/agent-contract.md`: References to "agent" generic, no model versions
- RC2 release notes: May reference older models
- AGENT_RESUME_SESSION.md (newly created): Claude 3.5 Sonnet Codex slot

**What Code Does:**
- `config/agents.json`: Exact model strings in agent definitions (not verified by audit)
- Actual provider responses: Real models running (verified by quota tracking)

**Contradiction:** If config claims "gpt-4" but actual provider is "gpt-4o", or if docs say "Sonnet" but code uses "Opus", evidence becomes incoherent.

### Cleanup Action
**Priority:** P1 (non-blocking for RC3, but needed before Phase 3)
```
[ ] Read config/agents.json fully (lines 1-200), extract model names
[ ] Cross-reference with config/agent-profiles.json and slot-bindings.json
[ ] Verify each model string is exact (e.g., "claude-3-5-sonnet" vs "Claude 3.5 Sonnet")
[ ] Update docs/model-guides/*.md to match actual config
[ ] Update AGENT_RESUME_SESSION.md fleet table with verified models
[ ] Note: "As of [date], verified models in use: [list]"
```

---

## Contradiction #3: Deprecated/Archive Guidance (MEDIUM)

### Evidence Gap
**Location:** References to "deprecated", "legacy", or "removed" features without clear removal dates or current status.

**Found In:**
- `docs/archive/disaster-recovery-2026-04/` (7 docs) — Old disaster recovery procedures
- Old config backups: `config/agents.json.broken-*`, `config/agents.json.bak-*` (5 backups)
- Scripts: Various `Fix-*.ps1` and recovery scripts that may be stale

**What's Wrong:**
- Old disaster recovery docs in main archive directory (unclear if procedures still needed)
- Broken config files not moved to proper archive location with dates
- Some scripts may be "superceded" but docs don't say by what or when

**Contradiction:** Another agent reading `docs/archive/disaster-recovery-2026-04/MCP_CONNECTOR_DIAGNOSTIC.md` won't know if the diagnostic procedure is current or obsolete.

### Cleanup Action
**Priority:** P2 (operational hygiene, not blocking RC3)
```
[ ] Reorganize: Move disaster-recovery to docs/archive/2026-04-disaster-recovery/
[ ] Reorganize: Move broken configs to config/archive/broken-2026-04-28/ with dates
[ ] Update top of each archive doc with: "Status: [Current | Obsolete | Superceded by X] | Date: 2026-04-28"
[ ] Update: Delete disaster recovery procedures when officially replaced by new process
[ ] Clean: Remove if no longer referenced in current runbooks
```

---

## Contradiction #4: Queue & Task State Terminology (MEDIUM)

### Evidence Gap
**Location:** Different documents use different state names for task lifecycle.

**Found In:**
- `agent-start-here.md` (line 30): "queue -> active -> done/failed"
- `operator-runbook.md`: Extended states including "hold", "disabled"
- `drift-prevention-contract.md` (Rule 3): Full state machine with "hold" intermediate
- Task directories: `tasks/queue`, `tasks/active`, `tasks/hold`, `tasks/done`, `tasks/failed`, `tasks/disabled`

**What's Wrong:**
- Old references may say "queue -> done" (skipping active)
- "disabled" state not defined in agent-start-here but exists in file system
- "hold" state introduced but may not be documented in older guides

**Contradiction:** Agent reading old docs follows "queue->done" transition, creates task file in wrong place, breaks queue ledger.

### Cleanup Action
**Priority:** P1 (operational, affects queue mutations)
```
[ ] Define single source of truth: Copy drift-prevention-contract.md Rule 3 state machine to agent-start-here.md
[ ] Add transition diagram to agent-contract.md (Phase 0: state machine rules)
[ ] Update all other docs to reference agent-contract.md lines X-Y for state definitions
[ ] Search for "queue\|active\|done\|failed" in docs/ and verify state references match schema
[ ] Move any old "queue->done" examples to archive/ with obsolescence note
```

---

## Contradiction #5: Service Configuration Defaults (MEDIUM)

### Evidence Gap
**Location:** Documentation and configuration defaults for local services don't align.

**Found In:**
- `local-services.example.json` (line 31): ngrok service had `"windowStyle": "Normal"` (BEFORE screen flicker fixes)
- Docs: No guidance on service window styles until new drift-prevention-contract.md
- Scripts: Start-OrchestratorServices.ps1 defaults to Hidden (line 103) but config can override

**What's Wrong:**
- New agent reads local-services.example.json, sees "Normal" window style, thinks that's correct default
- Service supervisor behavior depends on config not in code (implicit contract)
- No pre-flight validation of service config safety

**Contradiction:** Code defaults to Hidden, example shows Normal, docs don't explain, agent gets confused.

### Cleanup Action
**Priority:** P1 (prevents screen flicker regression)
```
[ ] Update local-services.example.json: Set all services to "Hidden" by default (or remove windowStyle to use default)
[ ] Add comment: "# windowStyle: Hidden (default) suppresses background UI in non-headless ops"
[ ] Create docs/services-configuration-contract.md with safe defaults and override rules
[ ] Add validation in Start-OrchestratorServices.ps1 pre-flight: warn if windowStyle is "Normal"
[ ] Update AGENT_RESUME_STABLE.md services section with config safety rules
```

---

## Summary Table

| # | Category | Severity | Files | Cleanup Owner | Target Date |
|---|----------|----------|-------|---------------|-------------|
| 1 | Headless slot config | P0 | agents.json, scripts, docs | Phase 1 impl | 2026-05-03 |
| 2 | Model version strings | P1 | agents.json, model-guides, RESUME | Phase 1 impl | 2026-05-03 |
| 3 | Deprecated/archive docs | P2 | archive/disaster-recovery, backups | Later | 2026-05-10 |
| 4 | Queue state terminology | P1 | agent-contract.md, start-here, docs | Phase 2 | 2026-05-05 |
| 5 | Service config defaults | P1 | local-services.json, scripts | Phase 1 | 2026-05-03 |

**Total Cleanup Tasks:** 14 specific action items  
**Blocking RC3 Phase 1:** Items #1, #2, #5 (3 items, ~2-3 hours)  
**Blocking RC3 Phase 2-3:** Items #3, #4 (2 items, ~1-2 hours, can defer)  
**Non-Blocking:** Archive reorganization (1-2 hours, nice-to-have)

---

## Remediation Plan (Phase 1)

### Immediate (This Session)
1. Verify headless slot actual state in config/agents.json  
2. Verify model versions in config and update RESUME docs  
3. Verify service config defaults and update example/scripts  
4. Document decisions in new section of agent-contract.md (Phase 0)  
5. Commit with message: "docs: evidence consistency audit fixes, RC3 Phase 1"  

### Follow-Up (Phase 2-3)
1. Add state machine diagram to agent-contract.md  
2. Reorganize archive/ with consistent date/status naming  
3. Remove obsolete disaster recovery procedures  
4. Add pre-flight validation to service supervisor  

---

## Enforcement

After cleanup, add to drift-prevention-contract.md pre-session checklist:
```
[ ] Audit drift-prevention-contract.md Rule 1 (Evidence Consistency)
[ ] Check for contradictions in docs modified this session
[ ] Verify no stale references remain in new/updated docs
```

Evidence consistency is non-negotiable. Each contradiction compounds over sessions, leading to incoherent state and failed dispatches.
