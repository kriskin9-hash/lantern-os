# Git Hooks — Comprehensive Quality Enforcement

Complete reference for all git hooks enforcing:
1. **Version/Changelog** — Consistent version bumping
2. **Deployment Readiness** — Safe production deployments
3. **Auto-Update Safety** — Safe version updates
4. **AGENTS.md Documentation** — Agent governance

---

## Quick Start

**Install all hooks (one time):**
```bash
bash scripts/install-hooks.sh
```

**Hooks run automatically on every commit.**

---

## Hook Overview

### Pre-commit Hook (Comprehensive)

Runs **4 validators** on every commit:

```
git commit
  ↓
[1/4] validate-version-changelog.py
  ├─ Code changed? → version must bump
  ├─ Version bumped? → changelog must update
  ├─ Changelog format valid? (date, sections, content)
  └─ Version format valid? (semantic: x.y.z)
  ↓
[2/4] validate-deployment-readiness.py
  ├─ Deployment file changed? → deployment.json valid
  ├─ Has rollback plan? (documented steps)
  ├─ Health checks defined? (/health, /status endpoints)
  ├─ No breaking API changes? (exports, routes intact)
  └─ Environment configured? (name, region)
  ↓
[3/4] validate-autoupdate-safety.py
  ├─ Version bumped? → auto-update script exists
  ├─ Major/minor bump? → migration script required
  ├─ Critical deps changed? (express, body-parser, etc)
  ├─ Backwards compatible? (no removed exports)
  └─ Rollback docs present? (README.md rollback section)
  ↓
[4/4] validate-agents-md.py
  ├─ Agent commit? → AGENTS.md must be updated
  ├─ Agent documented? (name, capabilities, owner)
  ├─ Runbook defined? (behavior, constraints)
  ├─ Monoworkstream rule? (max 1 open PR per lane)
  └─ No PII or secrets? (validate agent metadata)
  ↓
✓ All pass → commit allowed
✗ Any fail → commit blocked
```

---

## Hook 1: Version & Changelog

**When:** On every commit  
**Triggers if:** Code files changed OR version changed  
**Validates:** Semantic versioning + changelog consistency

### Rules

**If code changed:**
- Version **must** be bumped
- Changelog **must** have entry for new version
- Changelog must have: Added/Fixed/Changed sections with items

**If version bumped:**
- Format must be semantic: `major.minor.patch` (e.g., `1.2.4`)
- Changelog entry must exist: `## [1.2.4] - YYYY-MM-DD`
- Entry must have content in each section

### Example Success

```bash
$ git add src/feature.js package.json CHANGELOG.md
$ git commit -m "feat: add new feature"

[*] Validating version and changelog...
    Current version: 1.2.3
    Staged version:  1.2.4
    Code changed: true
    [✓] Version format valid: 1.2.4
    [✓] Changelog version found: 1.2.4
    [✓] Changelog entry valid

[OK] All validations passed
```

### Example Failure

```bash
$ git add src/feature.js
$ git commit -m "feat: add new feature"

[!] Code files changed but version not bumped (still 1.2.3)

→ To fix: Update package.json version, add CHANGELOG.md entry, retry
```

### Changelog Format

**Required:**
```markdown
## [1.2.4] - 2026-06-08

### Added
- New feature 1
- New feature 2

### Fixed
- Bug fix 1

### Changed
- Breaking change
```

**Rules:**
- Version header: `## [x.y.z] - YYYY-MM-DD`
- Each section with at least one item
- Date format: ISO 8601 (YYYY-MM-DD)
- Bullet items start with `-`

### Skip This Check

```bash
SKIP_VERSION_CHECK=1 git commit -m "temp: work in progress"
```

---

## Hook 2: Deployment Readiness

**When:** On every commit  
**Triggers if:** Server/routes/lib files changed  
**Validates:** Safe deployment configuration

### Rules

**If deployment files changed:**
- `apps/lantern-garage/deployment.json` must exist
- Must have: version, status, environment, rollbackPlan, healthChecks
- Rollback plan must have documented steps
- Health check endpoints must exist
- No breaking changes to APIs

### Required: deployment.json

```json
{
  "version": "1.2.4",
  "status": "ready",
  "environment": {
    "name": "production",
    "region": "us-east-1"
  },
  "lastDeployed": "2026-06-08T22:00:00Z",
  "healthChecks": [
    "/health",
    "/api/status"
  ],
  "rollbackPlan": {
    "previousVersion": "1.2.3",
    "steps": [
      "Stop current deployment",
      "Revert to v1.2.3",
      "Verify /health endpoint returns 200",
      "Notify ops team"
    ]
  }
}
```

### Validation Checks

1. **File exists:** deployment.json present
2. **Structure valid:** all required fields
3. **Rollback plan:** documented with steps
4. **Health endpoints:** /health or /status routes exist
5. **API compatibility:** no removed routes/exports

### Example Failure

```bash
$ git add apps/lantern-garage/server.js
$ git commit -m "feat: add new route"

[!] Deployment-critical files changed
[!] apps/lantern-garage/deployment.json not found

→ To fix: Create deployment.json with rollback plan and health checks
```

### Skip This Check

```bash
SKIP_DEPLOY_CHECK=1 git commit -m "hotfix: emergency patch"
```

---

## Hook 3: Auto-Update Safety

**When:** On every commit  
**Triggers if:** Version changed in package.json  
**Validates:** Safe auto-update capability

### Rules

**If version bumped:**
- `scripts/auto-version.js` must exist
- Major/minor bumps require migration script: `scripts/migrations/X.Y.Z_to_A.B.C.js`
- No critical dependencies removed (express, body-parser, dotenv, node-sse)
- Rollback instructions in README.md
- No breaking changes to module exports

### Migration Scripts

**Required for major/minor bumps:**

```javascript
// scripts/migrations/1.2.3_to_1.3.0.js
module.exports = {
  async up() {
    // Handle data migrations, schema changes
    // e.g., update stored config format
  },
  async down() {
    // Rollback procedure
  }
};
```

### Critical Dependencies

Cannot be removed without major version bump:
- `express` — web framework
- `body-parser` — request parsing
- `dotenv` — environment config
- `node-sse` — server-sent events

### Example Failure

```bash
$ git add package.json  # removed express dependency
$ git commit -m "chore: bump to 1.3.0"

[!] Critical dependency change: express removed
[!] Migration script 1.2.3_to_1.3.0.js not found

→ To fix: Either restore express OR create migration script AND major version bump
```

### Skip This Check

```bash
SKIP_UPDATE_CHECK=1 git commit -m "version: test bump"
```

---

## Hook 4: AGENTS.md Documentation

**When:** On every agent commit  
**Triggers if:** Branch prefix matches agent lane (claude/, gemini/, devin/, etc.)  
**Validates:** Agent documentation is complete and current

### Rules

**If agent branch detected:**
- `AGENTS.md` must exist and be updated
- Agent must be documented with:
  - **Status:** active | on-hold | deprecated
  - **Model:** LLM/model being used
  - **Lane:** branch prefix (claude/, gemini/, etc.)
  - **Owner:** contact person
  - **Capabilities:** what this agent does
  - **Runbook:** how it operates
  - **Constraints:** limits and exclusions

### Required: AGENTS.md Section

```markdown
## Claude Agent

**Status:** active
**Model:** claude-opus
**Lane:** claude/
**Owner:** Alex Place
**Last Updated:** 2026-06-08

### Capabilities
- Feature engineering
- Python/Node.js development
- Documentation writing
- Code review
- System design

### Runbook / Behavior
Claude operates as the primary multi-domain agent. Focuses on comprehensive solutions with proper documentation and testing. Prefers to clarify ambiguous requirements before proceeding.

### Constraints
- Maximum open PRs: 1 per claude/ lane
- Focus area: Full-stack features, infrastructure
- Not responsible for: Graphics, 3D rendering, real-time systems
- Preferred tools: Python, Node.js, bash scripting

### Recent Activity
- 2026-06-08: Implemented training convergence system with Bayesian scheduling
- 2026-06-07: Created comprehensive git hooks system
```

### Branch Prefixes (Defined Lanes)

| Lane | Agent |
|------|-------|
| claude/ | Claude (multi-purpose) |
| gemini/ | Gemini (reasoning-focused) |
| codex/ | Codex (code-focused) |
| devin/ | Devin (autonomous engineer) |
| grok/ | Grok (novel-thinking) |
| openai/ | OpenAI (standard reasoning) |

### Example Success

```bash
$ git add AGENTS.md src/feature.js
$ git commit -m "feat(claude): add new feature"

[*] Detected agent: claude
[✓] AGENTS.md exists
[✓] Agent documented in AGENTS.md
[✓] Agent documentation complete
    - Capabilities defined
    - Runbook present
    - Owner documented

[OK] Agent documentation validated
```

### Example Failure

```bash
$ git add src/feature.js  # but not AGENTS.md
$ git commit -m "feat: new code"

[*] Detected agent: claude
[!] Agent 'claude' not documented in AGENTS.md

→ To fix: Add claude to AGENTS.md with full documentation
```

### Monoworkstream Rules

**Per agent lane:**
- Maximum **1 open PR** at a time
- Cannot create second branch until first is merged/closed
- Enforced by this hook with warnings
- Also enforced by git pre-push hook (in CI)

### Skip This Check

```bash
SKIP_AGENT_CHECK=1 git commit -m "wip: agent work"
```

---

## Skip Options

### Individual Skips

```bash
# Skip one validator
SKIP_VERSION_CHECK=1 git commit

# Skip multiple (recommended for complex changes)
SKIP_VERSION_CHECK=1 SKIP_DEPLOY_CHECK=1 git commit

# Specific use cases:
SKIP_VERSION_CHECK=1 git commit     # Docs-only changes
SKIP_DEPLOY_CHECK=1 git commit      # Non-server changes
SKIP_UPDATE_CHECK=1 git commit      # Pre-version-bump prep
SKIP_AGENT_CHECK=1 git commit       # Non-agent contribution
```

### Emergency (All Skipped)

```bash
SKIP_ALL_CHECKS=1 git commit -m "EMERGENCY: critical hotfix"
```

⚠️ **Use sparingly.** Emergency bypasses exist for truly urgent situations, not routine development.

---

## Commit-Msg Hook (Format Validation)

Enforces structured commit messages: `type(scope): subject`

### Valid Types

- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation
- `refactor` — Code refactoring
- `perf` — Performance improvement
- `test` — Tests
- `chore` — Maintenance
- `ci` — CI/CD
- `build` — Build system
- `style` — Code style

### Valid Scopes (Optional)

- `training` — ML training
- `versioning` — Version/release
- `api` — REST API
- `ui` — Frontend
- `router` — Intent routing
- `deployment` — Deployment config
- etc. (any logical grouping)

### Examples

```
✓ feat(training): add Bayesian learning rate scheduling
✓ fix(router): handle null intent classification
✓ docs: update knowledge center
✓ chore: bump version to 1.2.4
✗ wip (no type)
✗ fix the bug (no scope format)
```

---

## Manual Validation

Run validators outside git hooks:

```bash
# All four validators
python3 scripts/validate-version-changelog.py
python3 scripts/validate-deployment-readiness.py
python3 scripts/validate-autoupdate-safety.py
python3 scripts/validate-agents-md.py

# Output: [OK] or [ERROR] messages with specific issues
```

---

## Troubleshooting

### "Module not found: packaging"

```bash
pip install packaging
```

### "Hook failed, commit blocked"

1. Read the error message (it tells you what's wrong)
2. Fix the issue in your code/docs
3. Stage the fix
4. Retry the commit

### "I need to bypass for a good reason"

Use the appropriate `SKIP_*` environment variable:
- Non-code changes? `SKIP_VERSION_CHECK=1`
- Architecture-only? `SKIP_DEPLOY_CHECK=1`
- Pre-update prep? `SKIP_UPDATE_CHECK=1`
- Testing? `SKIP_AGENT_CHECK=1`

### "Hooks not running"

Verify installation:
```bash
bash scripts/install-hooks.sh

# Check hooks exist:
ls -lh .git/hooks/pre-commit
ls -lh .git/hooks/commit-msg
```

---

## PR Review Checklist

When reviewing PRs, check:
- [ ] Version bumped (if code changed)
- [ ] Changelog updated (if version bumped)
- [ ] Changelog format valid (date, sections, content)
- [ ] Deployment config updated (if server changed)
- [ ] Health checks still pass (if routes changed)
- [ ] No breaking API changes
- [ ] Auto-update safety (if version bumped)
- [ ] AGENTS.md updated (if agent commit)
- [ ] Commit messages follow format

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/validate-version-changelog.py` | Version/changelog logic |
| `scripts/validate-deployment-readiness.py` | Deployment validation |
| `scripts/validate-autoupdate-safety.py` | Auto-update safety |
| `scripts/validate-agents-md.py` | AGENTS.md validation |
| `scripts/hooks/pre-commit-full-validation` | Combined pre-commit hook |
| `scripts/hooks/commit-msg-format` | Commit message hook |
| `scripts/install-hooks.sh` | Installation script |
| `docs/HOOKS.md` | Original documentation |
| `docs/HOOKS-COMPREHENSIVE.md` | This comprehensive guide |

---

## Summary

**Four-layer validation ensures:**
1. ✅ **Version consistency** — code changes tracked via semantic versioning
2. ✅ **Deployment safety** — production rollbacks documented and tested
3. ✅ **Update capability** — version updates safe and reversible
4. ✅ **Agent governance** — agents documented, capabilities clear, monoworkstream rule enforced

**All automatic on commit. Individual skips available. Emergency bypass exists.**

