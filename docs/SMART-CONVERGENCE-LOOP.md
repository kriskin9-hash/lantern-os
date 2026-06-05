# Smart Convergence Loop

Lantern's smart convergence loop is a local-first wrapper around the existing
Lantern consolidate scan. It observes repo state, runs health and validation
checks, ranks the first actionable issues, and emits a bounded repair plan.

It does not start agents, move queued tasks, reset, clean, push, or trust remote
state over local evidence.

## Command

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternSmartConvergenceLoop.ps1
```

Useful variants:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternSmartConvergenceLoop.ps1 -Depth Light -SkipNetwork
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternSmartConvergenceLoop.ps1 -Profile Cloud -SkipNetwork -OutputPath smart-convergence-loop-report.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternSmartConvergenceLoop.ps1 -ApplySafeFixes
```

`-ApplySafeFixes` is intentionally narrow. It is held when the working tree is
dirty and must not be used as a broad code-modifying autopilot.

## Loop Shape

1. Inspect Git state, branch parity, and lock files.
2. Run `scripts/Invoke-LanternConvergenceLoop.ps1` without `-Output` for the
   read-only Lantern consolidate scan.
3. Run fast syntax and contract checks.
4. Probe local health only if the service is already running.
5. Run network checks only when not skipped.
6. Build a patch plan for missing loop surfaces.
7. Report the next safest action.

## Confidence Table

| Action | Cadence | Confidence | Why |
|---|---:|---:|---|
| Git dirt, lock, and branch-divergence scan | Every local loop; every 30 minutes if automated | 0.98 | Cheap local evidence; blocks unsafe pull, push, cleanup, and self-repair. |
| Lantern consolidate read-only scan | Hourly local; every scheduled CI run in Cloud mode | 0.94 | Reuses the existing Lantern 12-step contract and reports first actionable issues. |
| Fast code syntax and contract checks | Every commit or PR; hourly while actively changing code | 0.92 | Catches broken JavaScript, PowerShell, and Python surfaces before deeper tests. |
| Local HTTP health probe | Every 15-30 minutes only when the app should already be running | 0.88 | Verifies the actual local route without starting services or trusting stale status. |
| Cloud scheduled CI smart loop | Every 6 hours plus manual dispatch | 0.86 | Scheduled workflows are useful for recurring cloud checks, but they cannot prove local MCP/runtime state. |
| npm audit high-severity threshold | Daily in network-enabled loop; on demand before release | 0.84 | Fails at a selected severity while preserving full audit output for review. |
| Dependabot dependency and GitHub Actions update PRs | Weekly | 0.82 | Purpose-built dependency update PRs with controlled churn. |
| OpenSSF Scorecard supply-chain posture | Weekly or release-candidate only | 0.78 | Useful external posture signal; private-repo support depends on security settings. |
| Self-repair with `-ApplySafeFixes` | Manual only after a clean Git scan | 0.70 | Good for tiny config/docs repairs; code-changing repair still needs review. |

## Web-Checked Source Notes

- GitHub Actions scheduled workflows use cron, run on the latest default-branch
  commit, and have a shortest interval of five minutes:
  https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- Dependabot version updates are configured with `.github/dependabot.yml` and
  `schedule.interval`:
  https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/configuring-dependabot-version-updates
- `npm audit --audit-level` sets the failure threshold for CI:
  https://docs.npmjs.com/cli/v11/commands/npm-audit/
- OpenSSF Scorecard provides an official GitHub Action:
  https://github.com/ossf/scorecard-action

## Boundaries

- Cloud mode validates repository invariants only.
- Local health checks do not start services.
- Git locks are reported, not deleted.
- Dirty worktrees block self-repair.
- Dependency fixes are proposed, not automatically applied.
- Live MCP or agent readiness still requires local exposed-tool evidence.
