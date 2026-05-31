---
description: Human Trial Demo workflow for Lantern OS ASI Arc Reactor MK1. Use when preparing and executing human trial demos with proper safety gates, evidence collection, and validation.
---

# Human Trial Demo Workflow

## Purpose

Prepare and execute human trial demos for Lantern OS with ASI Arc Reactor MK1 integration, ensuring all safety gates, evidence collection, and validation requirements are met before claiming human trial readiness.

## Pre-Demo Checklist

Before any human trial demo:

1. **Run convergence loop**: Execute `scripts/Invoke-LanternConvergenceLoop.ps1` and fix first 2-4 issues
2. **Check Arc Reactor status**: Verify `data/arc-reactor/status.json` shows adequate confidence scores
3. **Validate MCP canary**: Ensure MCP canary validates all exposed tools
4. **Review ASI boundaries**: Confirm ASI patterns are architecture references only
5. **Check wallet ledger**: Verify founding seat receipts and cleared cash evidence
6. **Test rollback path**: Validate documented rollback for all automated actions
7. **Configure safety gates**: Ensure Windsurf hooks block dangerous operations

## Demo Setup

### Participant Preparation

- Document participant consent with explicit approval recording
- Identify PPE requirements if medical claims are involved
- Verify certified PPE or tested prototype evidence exists
- Record participant profile and use case

### Environment Preparation

- Clean repo state with no uncommitted changes
- MCP canary active and validated
- Command allow/deny lists configured
- Audit logging enabled
- Break-glass recovery path documented

### Demo Script

| Phase | Action | Evidence Required |
|---|---|---|
| **Pre-Trial** | Run convergence loop, fix issues | Loop output receipt |
| **Setup** | Document consent, PPE, boundaries | Signed consent form |
| **Execution** | Record all actions, outcomes | Action log with timestamps |
| **Feedback** | Capture participant feedback | Feedback form/receipt |
| **Post-Trial** | Update confidence scores | Updated status.json |
| **Receipt** | Generate trial receipt | Trial receipt JSON/MD |

## Safety Gates

### MCP Canary Validation

Before any automated action:

```powershell
# Test MCP canary
python .\scripts\Test-McpCanary.ps1
```

Expected output:
- All exposed tools validated
- No secret leakage
- Command allow/deny lists active

### Windsurf Hooks Configuration

Configure `.windsurf/hooks.json` with safety gates:

```json
{
  "pre_run_command": {
    "command": "scripts/Validate-DemoSafety.ps1",
    "block_on_failure": true
  },
  "pre_mcp_tool_use": {
    "command": "scripts/Validate-McpTool.ps1",
    "block_on_failure": true
  }
}
```

### Rollback Path Validation

Test rollback before demo:

```powershell
# Test rollback path
python .\scripts\Test-RollbackPath.ps1
```

## Evidence Collection

### Required Evidence for Each Demo

1. **Convergence loop output**: Latest loop status and issues
2. **Participant consent**: Signed consent form with explicit approval
3. **Action log**: All actions with timestamps and outcomes
4. **Feedback receipt**: Participant feedback form
5. **Confidence update**: Updated Arc Reactor status with Brier-style tracking
6. **Trial receipt**: JSON and markdown receipt with evidence class

### Brier-Style Error Tracking

For each forecast:

```json
{
  "forecast": "Demo will complete in 60 minutes with participant satisfaction > 8/10",
  "confidenceInterval": [0.7, 0.9],
  "evidenceClass": "participant_satisfaction_score",
  "actualOutcome": "Completed in 55 minutes, satisfaction 9/10",
  "brierScore": 0.15,
  "confidenceUpdate": "+0.05"
}
```

## Post-Demo Actions

1. **Update Arc Reactor status**: Apply Brier-style error tracking to confidence scores
2. **Generate trial receipt**: Create JSON and markdown receipt
3. **Record in wallet ledger**: Add demo event if paid founding seat
4. **Update convergence loop**: Add any new issues discovered
5. **Archive evidence**: Store all receipts in `manifests/evidence/`

## Blocked Actions

The following actions are **blocked** during human trial demos:

- No ASI capability claims without independent validation
- No medical or PPE claims without certified evidence
- No automated actions without MCP canary validation
- No token issuance or investment advice
- No unattended disk mutation
- No Discord-to-MCP command execution before canary
- No human trial readiness claim without cleared cash and safety gates

## Success Criteria

A human trial demo is successful when:

- All pre-demo checklist items pass
- MCP canary validates all exposed tools
- Participant consent is documented with explicit approval
- All actions are logged with timestamps
- Rollback path is tested and validated
- Trial receipt is generated with evidence class
- Arc Reactor status is updated with observed evidence
- No safety gates were violated
- No blocked claims were made

## Failure Handling

If a demo fails:

1. **Stop immediately** if safety gate violation occurs
2. **Document failure** with evidence class and root cause
3. **Apply rollback** if automated actions were executed
4. **Update blockers** in `manifests/open-issues.md`
5. **Review ASI boundaries** to ensure no capability claims were made
6. **Update confidence scores** with Brier-style error tracking
7. **Hold future demos** until blockers are resolved

## Validation Commands

```powershell
# Pre-demo validation (run in order)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LoopReceipt.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1

# Post-demo validation
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Update-ArcReactorStatus.ps1 -Evidence "5 outreach sends recorded in the wallet ledger"
# Replace -Evidence value with the actual gate string(s) from data/arc-reactor/status.json raisesMovie2 / raisesHumanTrial
```

## References

- `skills/asi-arc-reactor-mk1/SKILL.md` - ASI Arc Reactor MK1 skill
- `data/arc-reactor/status.json` - Current confidence scores
- `manifests/evidence/asi-local-pdf-convergence-2026-05-29.md` - ASI pattern boundaries
- `docs/CONVERGENCE-LOOP.md` - 12-step convergence method
- `docs/V1-READINESS-GATES.md` - Release readiness criteria
- `docs/ONE-HOUR-1000-DEMO.md` - $1000 founding seat demo script

## Next Action

After completing this workflow, update the Arc Reactor status with observed evidence and generate the trial receipt. Do not claim human trial readiness until all safety gates pass and evidence receipts exist.
