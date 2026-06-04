# PR Review & Improvement Plan: Architectural Analysis

**Reviewer:** Claude (Architect)  
**Date:** 2026-05-03  
**Scope:** Open PRs #260, #261, #262  
**Goal:** Review current naming/guidance patterns and propose improvements aligned with ADR-001 and governance framework  

---

## Current State Analysis

### Open PRs Inventory

| PR | Title | Type | Status | Files | Issues |
|---|---|---|---|---|---|
| #262 | `fix(ops): suppress background UI flicker` | Config/Service | DRAFT | 3 | Naming, guidance |
| #261 | `fix(mcp): make agent dispatch args null-safe` | Fix/Safety | OPEN | 2 | Scope clarity, testing guidance |
| #260 | `Screen Flicker Fixes: Suppress Visible...` | Feature/Fix | OPEN | 7 | Title format, body structure, risk |

---

## Architectural Issues Found

### Issue 1: Inconsistent Title Format (All PRs)

**Problem:** Titles don't follow conventional commit format consistently.

**Current:**
- `#262`: `fix(ops): suppress background UI flicker` ✅ (Good format)
- `#261`: `fix(mcp): make agent dispatch args null-safe` ✅ (Good format)
- `#260`: `Screen Flicker Fixes: Suppress Visible Windows in Non-Headless Operations` ❌ (Not conventional)

**Issue:** #260 uses natural language instead of `fix(scope): verb-object` pattern.

**Recommendation:** Standardize all to conventional commit format:
- Type: `fix`, `feat`, `docs`, `refactor`, `test`, `chore`
- Scope: One word describing component (dispatcher, services, monitor, dashboard)
- Subject: Verb-noun, present tense, lowercase, under 50 chars

**Updated Titles:**
- #260 → `fix(ui): suppress background window flicker in non-headless ops`
- #261 ✅ Already correct
- #262 → `fix(services): suppress background UI flicker (ngrok, health checks)`

---

### Issue 2: Scope Naming Too Broad (All PRs)

**Problem:** Scopes like `(ops)` and `(mcp)` are too general; harder to grep and categorize.

**Current scopes:**
- `ops` — Could be services, supervisor, startup, dashboard
- `mcp` — Could be dispatcher, server, contracts, tooling

**Recommended scopes (more specific):**
- `dispatcher` — MCP dispatcher (start_agent, rerun_agent)
- `services` — Service supervisor, registry, health checks
- `monitor` — Dashboard pulse, health monitoring
- `ui` — Screen rendering, window styles, visibility
- `startup` — Startup tasks, registration

**Examples:**
- `fix(dispatcher): null-safe argument handling`
- `fix(services): enforce hidden window style`
- `fix(monitor): suppress notification UI in headless mode`

---

### Issue 3: Body Structure Lacks Risk Assessment (All PRs)

**Problem:** PR bodies describe WHAT changed but not WHAT BREAKS IF WRONG.

**Current structure:**
- Summary ✅
- Why ✅
- Validation ✅
- **Missing:** Risk assessment, backwards compatibility, scope impact

**Recommended structure:**
```markdown
## Summary
[What changed, 1-2 sentences]

## Why
[Why this matters, what was broken/missing]

## Changes
[Detailed list of changed files]

## Risk Assessment
[What can break, backwards compatibility, scope impact]

## Validation
[How to test, expected outcomes]

## Related Issues
[#256, #259, etc.]
```

---

### Issue 4: Validation Guidance Too Implementation-Specific (All PRs)

**Problem:** Validation section is for the reviewer, not the maintainer. Different question: "Did you test this?" vs. "How should I test this post-merge?"

**Current (good):** #261 has clear "Expected CI" and "Required local validation"  
**Current (poor):** #260 has detailed test steps but no "After merge, operator should..."

**Recommended:**
```markdown
## Validation (Before Merge)
[How to test locally before approval]

## Post-Merge Verification (For Operator)
[How to verify in production/staging, what to watch]

## Rollback Plan
[If something breaks, how to revert safely]
```

---

### Issue 5: Scope Statements Missing Architectural Impact

**Problem:** PRs don't state if they change architecture, contracts, or safe boundaries.

**Example (#261):**
- Changes MCP argument handling
- This affects dispatcher contract
- Could break other agents calling the same function
- Should state: "Scope: Safe refactor; dispatcher contract unchanged to callers"

**Recommended addition:**
```markdown
## Architectural Impact
- Contract changes: [Yes/No — which contracts]
- Backwards compatible: [Yes/No]
- Affects other components: [List which]
- Governance changes needed: [Yes/No — which rules]
```

---

## Improvement Plan

### Phase A: Immediate (Before Merge)

#### Step 1: Update PR Titles
All three PRs need title normalization per conventional commits:

**#260:**
```
OLD: Screen Flicker Fixes: Suppress Visible Windows in Non-Headless Operations
NEW: fix(ui): suppress background window flicker in non-headless operations
```

**#261:** ✅ Already correct

**#262:**
```
OLD: fix(ops): suppress background UI flicker
NEW: fix(services): enforce hidden window style by default
```

**Action:** Update via `gh pr edit` or merge and document decision.

---

#### Step 2: Standardize PR Body Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Summary
[1-2 sentences: what changed, why it matters]

## Changes
- [ ] File 1: [What changed, why]
- [ ] File 2: [What changed, why]

## Risk Assessment
- Contract changes: [Yes/No]
- Backwards compatible: [Yes/No]
- Affects other components: [List]
- Governance impact: [Yes/No]

## Architectural Impact
[Scope, boundaries, contract implications]

## Validation
### Before Merge (For Reviewers)
[How to test locally]

### Post-Merge (For Operators)
[How to verify in production]

## Rollback Plan
[If something breaks, how to safely revert]

## Related Issues
[Fixes #X, Relates to #Y]

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

---

#### Step 3: Add Risk Assessment to All Open PRs

**#260 needs:**
```markdown
## Risk Assessment
- Contract changes: No
- Backwards compatible: Yes (all changes optional with flags)
- Affects other components: Monitor-DashboardPulse, Service Supervisor, StartupTask
- Governance impact: No

## Architectural Impact
Scope: Safe enhancement. No contracts changed.
- Monitor-DashboardPulse gains optional `-Headless` flag (backwards compatible)
- Restart-DashboardServer gains `-WindowStyle Hidden` (backwards compatible)
- Start-OrchestratorServices gains `-EnforceHeadlessMode` (backwards compatible)
All changes are additive; existing code paths unaffected.
```

**#261 needs:**
```markdown
## Risk Assessment
- Contract changes: Yes (MCP dispatcher argument handling)
- Backwards compatible: Yes (optional args still work, just safer)
- Affects other components: Any caller of start_agent / rerun_agent
- Governance impact: Yes (enforces strict mode contract per agent-contract.md)

## Architectural Impact
Scope: Safety hardening. Dispatcher contract preserved to callers.
- Internal: Use Get-OptionalJsonProperty for null-safe reads
- External: Callers see same result regardless of optional arg presence
- Strict mode: Now safe under Set-StrictMode -Version Latest
```

**#262 needs:**
```markdown
## Risk Assessment
- Contract changes: No
- Backwards compatible: Yes (service config changes are additive)
- Affects other components: local-services.json, service config validation
- Governance impact: Yes (aligns with headless-by-default rule from governance)

## Architectural Impact
Scope: Configuration alignment with governance framework.
- Default: Services now default to Hidden (from Normal)
- Override: Operators can still set explicit windowStyle if needed
- Enforcement: Service Supervisor can override with -EnforceHeadlessMode flag
```

---

### Phase B: Governance Integration (After Phase A)

#### Step 4: Link to ADR-001

All PRs should reference enforcement architecture:

```markdown
## Related to
- ADR-001: Enforcement Architecture
- #256: MCP dispatch blocker (fixed by #261)
- #259: RC3 release tracking
- docs/drift-prevention-contract.md: Rule enforcement
```

---

#### Step 5: Document Naming Conventions

Create `docs/PR-NAMING-CONVENTIONS.md`:

```markdown
# PR Naming Conventions

## Title Format
All PR titles must follow conventional commit format:

```
<type>(<scope>): <subject>
```

### Types
- `fix` — Bug fix, safety improvement, correctness
- `feat` — New feature, capability
- `docs` — Documentation, ADR, guides
- `refactor` — Code reorganization (no behavior change)
- `test` — Test additions, testing infrastructure
- `chore` — Dependencies, config, build tooling

### Scopes (Be Specific)
- `dispatcher` — MCP dispatcher, start_agent, rerun_agent
- `services` — Service supervisor, registry, health checks
- `monitor` — Dashboard pulse, health monitoring
- `ui` — Screen rendering, window styles, visibility
- `startup` — Startup tasks, registration, initialization
- `queue` — Queue management, task movement, lane transitions
- `governance` — Policy, enforcement, contracts
- `docs` — Documentation, guides, ADRs

### Subject
- Verb in present tense: `fix`, `add`, `suppress`, `enforce`
- Lowercase
- No period at end
- Under 50 characters

### Examples
✅ `fix(dispatcher): null-safe argument handling`
✅ `feat(services): add retry policy for failed startups`
✅ `docs(governance): ADR-001 enforcement architecture`
❌ `Fix the dispatcher issue` (not conventional)
❌ `fix(mcp): fix the thing` (vague)
❌ `Fixed the dispatcher argument null ref` (past tense)
```

---

## Recommended Review Checklist

Before approving any PR, verify:

- [ ] Title follows conventional commit format (`type(scope): subject`)
- [ ] Scope is specific (not `ops`, `core`, `misc`)
- [ ] Body has Summary, Changes, Risk, Validation, Related Issues
- [ ] Risk Assessment section filled (contracts, backwards compat, impacts)
- [ ] Validation shows both "before merge" and "post-merge" steps
- [ ] Related issues linked (#256, #259, ADR-001, etc.)
- [ ] Architectural impact stated (contract changes, backwards compat)
- [ ] No governance violations (drift-prevention-contract.md)
- [ ] Aligns with ADR-001 enforcement architecture

---

## Action Items

### Immediate (Today)
- [ ] Update #260 title: `fix(ui): suppress background window flicker...`
- [ ] Add Risk Assessment to #260
- [ ] Add Architectural Impact to #260
- [ ] Update #262 title: `fix(services): enforce hidden window style...`
- [ ] Add Risk Assessment to #262
- [ ] Verify #261 has all sections (looks good)

### Follow-Up (This Week)
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] Create `docs/PR-NAMING-CONVENTIONS.md`
- [ ] Update GITHUB-REVIEW-GOVERNANCE.md with PR standards
- [ ] Brief all agents on naming conventions and review checklist

### Ongoing
- [ ] Apply conventions to all future PRs
- [ ] Enforce via PR template (make body sections required)
- [ ] Review checklist in every approval

---

## Summary

**Current PRs:**
- Good technical content and validation steps
- Weak on naming consistency (conventional commits partially applied)
- Missing risk assessment and architectural impact sections
- Validation is reviewer-focused, not operator-focused

**Improvements:**
- Normalize all titles to conventional commit format
- Add Risk Assessment section (contracts, compat, scope)
- Add Architectural Impact section (safety, boundaries)
- Split validation into "before merge" and "post-merge"
- Create PR template to enforce standards going forward
- Document naming conventions for team alignment

**Result:** PRs become self-documenting, reviewers have clear gates, operators know what to verify post-merge.

---

## Reference

Related architectural decisions:
- **ADR-001:** Enforcement Architecture (git hooks + GitHub gates + CI/CD)
- **drift-prevention-contract.md:** Rules being enforced
- **GITHUB-REVIEW-GOVERNANCE.md:** Review policy (2 agents + 1 human)
