---
name: lantern-odds
description: "Lantern Odds skill for evaluating odds, risks, confidence, best next move, and do-not-do warnings for Lantern OS repo, workstation, convergence, and launch decisions."
---

# Lantern Odds Skill

Use this skill from `D:\tmp\lantern-os` when you need to evaluate odds, risks, confidence, and next actions for Lantern OS operations.

## Purpose

Evaluate odds, risks, confidence, best next move, and do-not-do warnings for:
- Implementation odds
- Repo health odds  
- Success probability for workstation setup
- Risk of breaking Lantern OS
- "Best next action" odds

## Input Triggers

Use these patterns to trigger the odds evaluation:

```
!odds second workstation
!odds launch lantern garage
!odds PR #12
!odds this plan
!odds merge all PRs
!odds fleet deployment
!odds convergence loop
```

## Output Format

```markdown
# Odds Read

**Verdict:** Green / Yellow / Red
**Estimated odds:** 70%
**Confidence:** Medium

## Why:
- [Evidence point 1]
- [Evidence point 2]
- [Evidence point 3]

## Top Risks:
1. [Risk description with severity]
2. [Risk description with severity]
3. [Risk description with severity]

## Best Next Move:
[Specific actionable step with priority]

## Do Not Do:
- [Action that would cause failure]
- [Action that violates safety boundaries]
- [Action that requires unresolved dependencies]
```

## Evidence Sources

The skill prefers GitHub repo evidence when available, but works from:
- Local git status and history
- Pasted text or command output
- AGENTS.md boundaries
- Manifest files and convergence reports
- Test results and CI status

## Risk Categories

| Category | Indicators | Severity |
|----------|------------|----------|
| **Repo Health** | Dirty worktrees, merge conflicts, broken tests | High |
| **Convergence** | Failed loops, held boundaries, missing evidence | High |
| **Workstation** | Missing dependencies, path conflicts, permission issues | Medium |
| **Launch** | Unresolved PRs, missing artifacts, safety gates blocked | High |
| **Fleet** | Agent failures, billing issues, API key problems | Medium |

## Verdict Scale

- **Green (70-100%)**: Safe to proceed, minimal risks, all gates satisfied
- **Yellow (40-69%)**: Proceed with caution, some risks, partial gate satisfaction
- **Red (0-39%)**: Do not proceed, critical risks, major gates blocked

## Confidence Levels

- **High**: Direct evidence from repo state, test results, or manifest files
- **Medium**: Inferred from patterns, partial evidence, or similar past situations
- **Low**: Limited evidence, speculative, or requires additional validation

## Special Cases

### PR Merging
- Check for merge conflicts
- Verify CI status
- Review AGENTS.md boundary compliance
- Assess impact on live systems

### Workstation Setup
- Verify path structure matches expected conventions
- Check dependency availability
- Validate permission requirements
- Assess hardware requirements

### Fleet Deployment
- Verify agent slot configuration
- Check billing ledger state
- Validate API key presence
- Assess concurrent execution limits

## Integration with Lantern OS

This skill integrates with:
- `AGENTS.md` for boundary checking
- `manifests/` for evidence validation
- `scripts/Invoke-LanternConvergenceLoop.ps1` for convergence status
- `config/agents.json` for fleet state
- GitHub API for repo evidence when available

## Example Usage

```powershell
# Evaluate odds for second workstation setup
!odds second workstation

# Expected output:
# Odds Read
# Verdict: Yellow
# Estimated odds: 65%
# Confidence: Medium
# 
# Why:
# - Path structure differs from primary workstation
# - Dependencies may need fresh installation
# - Git clone operations require network access
# 
# Top Risks:
# 1. Path conflicts with existing C:\tmp structure (Medium)
# 2. Missing npm dependencies for Lantern Garage (Low)
# 3. Network access for git clone operations (Low)
# 
# Best Next Move:
# Run the provided PowerShell setup script on the target workstation first, then validate path structure before proceeding with fleet deployment.
# 
# Do Not Do:
# - Delete existing C:\tmp structure without backup
# - Proceed with fleet deployment until convergence loop passes
# - Modify AGENTS.md boundaries without operator approval
```

## Safety Boundaries

This skill respects:
- AGENTS.md held boundaries
- Status Cube convergence state
- Kill switch status for trading operations
- Operator approval requirements for v1.0.0 release
- Evidence class validation (local_verified, official_source, etc.)

## Next Safe Action

When odds are evaluated as Green or Yellow:
1. Address top risks in priority order
2. Execute best next move
3. Validate results with convergence loop
4. Update evidence and re-evaluate if needed

When odds are Red:
1. Stop and address critical risks
2. Do not proceed until verdict improves
3. Consult AGENTS.md for boundary guidance
4. Request operator approval if blocked by held gates
