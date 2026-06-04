# Contract Enforcement Matrix

Status: initial traceability matrix  
Audience: hiring managers, staff engineers, reviewers  
Purpose: reduce doc-to-code mismatch risk by mapping claims to scripts, tests, CI, and evidence.

---

## How to read this matrix

Status values:

- **Enforced**: there is a named script/tool and a named test or CI step that should fail on drift.
- **Partially enforced**: there is some code/test coverage, but gaps remain.
- **CI-listed**: a check is present in GitHub Actions, but this portfolio page still needs a pasted run transcript.
- **Evidence needed**: likely implemented, but this portfolio pack needs a concrete redacted example.
- **Doc-only**: documented expectation only; do not claim production enforcement.

This matrix should be updated whenever a new safety claim is added to the docs.

---

## Matrix

| Contract / reliability claim | Current enforcement surface | Current test / CI evidence | Portfolio evidence | Status | Gap / next action |
|---|---|---|---|---|---|
| PowerShell syntax should stay valid. | `tests/Test-PowerShellSyntax.ps1` | Orchestrator Health: `Validate PowerShell syntax` | `evidence/test-output-001.md` | CI-listed | Paste latest CI/local output. |
| Agent config should avoid unsafe defaults. | `tests/Test-AgentConfigSafety.ps1` | Orchestrator Health: `Validate agent config safety` | `evidence/test-output-001.md` | CI-listed | Paste latest CI/local output. |
| Claude hook must enforce PR closure expectations. | `.claude/hooks/**`, `tests/Test-ClaudePrClosureHook.ps1` | Orchestrator Health: `Validate Claude PR closure hook` | `evidence/test-output-001.md` | CI-listed | Add hook transcript when available. |
| Protected-work guard should prevent unsafe protected branch/task work. | Claude protected-work guard scripts/tests | Orchestrator Health: `Validate Claude protected-work guard` | `evidence/test-output-001.md` | CI-listed | Add redacted blocked-action example. |
| Gemini dispatch should block when preflight is absent, stale, unreadable, or MCP-unhealthy. | `scripts/Invoke-OrchestratorAgentAction.ps1`, Gemini preflight logic | `tests/Test-GeminiCliPreflightContract.ps1`, `tests/Test-GeminiDispatchPreflightGate.ps1` | `evidence/failure-recovery-001.md` | Partially enforced | Attach actual failing/prevented dispatch output. |
| Repo structure should stay canonical. | `docs/repo-structure-contract.md`, structure tests | Orchestrator Health: `Validate repo structure contract` | `evidence/test-output-001.md` | CI-listed | Paste latest output. |
| Evidence records should follow the agent contract. | `docs/agent-contract.md`, `tests/Test-AgentContractEvidenceRecord.ps1` | Orchestrator Health: `Validate evidence record handoff contract` | `evidence/test-output-001.md` | CI-listed | Add one real evidence record example. |
| Agent routing map should remain valid. | agent routing map docs/config | Orchestrator Health: `Validate agent routing map` | `evidence/test-output-001.md` | CI-listed | Link specific routing map file and paste output. |
| Token/provider research evidence should stay hygienic. | token research evidence tests | Orchestrator Health: `Validate token research evidence hygiene` | `evidence/test-output-001.md` | CI-listed | Link source registry / evidence file. |
| Queue task movement should follow contract. | queue/task movement scripts | Orchestrator Health: `Validate queue task movement contract` | `evidence/queue-transition-001.md` | Evidence needed | Capture dry-run or redacted before/after transition. |
| Queue claiming should be hardened. | queue claim selector logic | Orchestrator Health: `Validate queue claim selector hardness` | `evidence/queue-transition-001.md` | Evidence needed | Add transcript showing claim selection/idempotency behavior. |
| Work pipeline should have E2E contract coverage. | work pipeline scripts | Orchestrator Health: `Validate work pipeline E2E contract` | `evidence/demo-run-001.md` | Evidence needed | Capture full dry-run transcript. |
| Agent slots should use task movement helper instead of ad hoc moves. | agent slot scripts | Orchestrator Health: `Validate agent slot movement helper usage` | `evidence/queue-transition-001.md` | CI-listed | Paste output and link implementation files. |
| Stale branch status should be tracked consistently. | stale branch status contract scripts | Orchestrator Health: `Validate stale branch status contract` | `evidence/test-output-001.md` | CI-listed | Add sample status output. |
| Legacy headless slot paths should remain retired. | retirement contract tests | Orchestrator Health: `Validate legacy headless slot retirement` | `evidence/test-output-001.md` | CI-listed | Paste output. |
| Repository sync JSON contracts should remain parseable. | repo sync helper scripts | Orchestrator Health: `Validate repository sync JSON contract` | `evidence/test-output-001.md` | CI-listed | Paste output. |
| Control helper JSON contracts should remain parseable. | orchestrator control helpers | Orchestrator Health: `Validate control helper JSON contracts` | `evidence/test-output-001.md` | CI-listed | Paste output. |
| MCP server routes should satisfy route contracts. | Orch MCP server scripts | Orchestrator Health: `Validate MCP server route contracts` | `evidence/demo-run-001.md` | CI-listed | Capture route/tool transcript. |
| MCP safe PowerShell tool should enforce safe command boundaries. | MCP safe PowerShell tool | Orchestrator Health: `Validate MCP safe PowerShell tool contract` | `evidence/demo-run-001.md` | CI-listed | Add allowed/blocked command examples. |
| MCP ops tools should satisfy contracts. | MCP ops tools | Orchestrator Health: `Validate MCP ops tools contract` | `evidence/demo-run-001.md` | CI-listed | Capture exposed tool list. |
| MCP safe tools patch contract should stay valid. | MCP safe tools patch logic | Orchestrator Health: `Validate MCP safe tools patch contract` | `evidence/test-output-001.md` | CI-listed | Paste latest output. |
| MCP connector capability states should be explicit. | MCP capability status scripts | Orchestrator Health: `Validate MCP connector capability states` | `evidence/dashboard-snapshot-001.md` | CI-listed | Capture status JSON/dashboard snapshot. |
| LM Studio preflight lane should remain contractual if enabled. | LM Studio preflight lane scripts/tests | Orchestrator Health: `Validate LM Studio preflight lane contract` | `evidence/test-output-001.md` | CI-listed | Paste latest output. |
| Orchestrator status should emit valid JSON. | `scripts/Get-OrchestratorStatus.ps1` | Orchestrator Health: `Validate orchestrator status JSON stdout` and status generation step | `evidence/dashboard-snapshot-001.md` | CI-listed | Capture redacted JSON snapshot. |
| Dashboard activity should include failure context. | dashboard activity scripts/tests | Orchestrator Health: `Validate dashboard activity failure context` | `evidence/dashboard-snapshot-001.md` | CI-listed | Capture dashboard failure example. |
| Dashboard restart behavior should follow contract. | dashboard restart scripts/tests | Orchestrator Health: `Validate dashboard restart contract` | `evidence/dashboard-snapshot-001.md` | CI-listed | Paste output. |
| Server health pulse should be testable. | health pulse scripts/tests | Orchestrator Health: `Validate server health pulse contract` | `evidence/dashboard-snapshot-001.md` | CI-listed | Capture health pulse output. |
| Services supervisor should have restart contract coverage. | service supervisor scripts/tests | Orchestrator Health: `Validate restart service supervisor contract` | `evidence/dashboard-snapshot-001.md` | CI-listed | Paste output. |
| Startup task should have restart contract coverage. | startup task scripts/tests | Orchestrator Health: `Validate restart startup task contract` | `evidence/dashboard-snapshot-001.md` | CI-listed | Paste output. |
| Dashboard service health should be contract-tested. | dashboard service health scripts/tests | Orchestrator Health: `Validate dashboard service health contract` | `evidence/dashboard-snapshot-001.md` | CI-listed | Capture dashboard/service health output. |

---

## Explicit non-claims

Until concrete evidence is added, do not claim:

- production-grade multi-user auth;
- complete MCP authorization model;
- concurrent queue locking under load;
- long-running service uptime;
- repeated multi-agent dispatch reliability;
- enterprise-grade secret redaction;
- clean-machine bootstrap success.

These may be future goals, but the portfolio should separate current proof from intended design.
