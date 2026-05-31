# Fleet Slot E2E CI/CD Receipt

Generated: 2026-05-31

## Scope

Operator requested more fleet slots from fleet research, one at a time, with free-token preference, bill accountability, E2E CI/CD automation checks, and screenshots.

## Slots Added Locally

These slots were added to the machine-local orchestrator config at `C:\Users\alexp\Documents\gm-agent-orchestrator\config\agents.json`.

| Slot | Model | Billing posture | Green-light evidence |
|---|---|---|---|
| `gemini-flash-lite` | `gemini-2.5-flash-lite` | Gemini API free tier first, 2,000-token task cap | `GEMINI_API_KEY` present; model listed by Google models endpoint; 36 prompt tokens counted; direct bounded API call succeeded |
| `ollama-mistral-local` | `mistral:latest` | local-only, no external API token bill | `ollama` installed; `ollama list` shows `mistral:latest`; local run returned output |

## Slots Not Added

| Candidate | Reason held |
|---|---|
| OpenRouter | no `OPENROUTER_API_KEY` present |
| Groq | no `GROQ_API_KEY` present |
| Hugging Face | no `HF_TOKEN` or `HUGGINGFACEHUB_API_TOKEN` present |
| Qwen CLI | no local `qwen` / `qwen-code` command present |
| OpenCode / Goose / Aider | no local command present |

## GitHub Convergence Tracker

Created issue: `https://github.com/alex-place/lantern-os/issues/40`

Issue #40 tracks branch, PR, and issue convergence toward `master` using the cheapest fleet lanes first.

## E2E / CI/CD Checks

| Check | Result | Evidence |
|---|---|---|
| Gemini syntax check | pass | `scripts/Test-GeminiSyntax.ps1` -> `SYNTAX OK` |
| Convergence fleet contract | pass | `scripts/Test-ConvergenceAgentFleet.py` -> `ok: true`, 36 expected ring slots, 64 pool target |
| Workflow/surface pytest slice | pass | `python -m pytest tests/test_workflow_orchestration.py tests/test_surface_ux.py -q` -> `47 passed, 1 skipped` |
| Local agent ring registry | held/pass guard | `scripts/Test-AgentCliRegistry.ps1` refused to run because paid CLI/API dispatch is configured; no paid ring start occurred |
| GitHub Actions status | failing upstream | Recent `Browser Testing CI`, `Static surface CI`, and `Orchestration challenge CI` runs are failing on PR #38 / master-adjacent work; `Focus Lock` is passing |

## Screenshots

| Surface | Path | Status |
|---|---|---|
| Lantern dashboard | `manifests/evidence/screenshots/fleet-dashboard-2026-05-31.png` | captured |
| Convergence dashboard | `manifests/evidence/screenshots/fleet-convergence-dashboard-2026-05-31.png` | captured |

## Bill Accountability

- Gemini direct call used `gemini-2.5-flash-lite` with a 36-token prompt count and `maxOutputTokens=180`.
- Gemini CLI was attempted but hung after trust setup; related node processes were stopped.
- No OpenAI or Anthropic paid agent was started.
- The local agent ring test refused to start because paid CLI/API dispatch is configured; that failure is intentionally treated as a safety guard.
- Ollama/Mistral ran locally and does not require an external API key.

## Next Action

Use issue #40 as the master convergence board. Merge or inspect PRs in this order after fresh GitHub checks: #34, #33, #35, #29, #38. Keep #32, #31, and #30 held for conflict inspection.

