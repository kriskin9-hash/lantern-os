# RAGDoll House Reports Update — 2026-05-29

Status: master receipt
Scope: documentation/reporting only

## Summary

This receipt consolidates the new Lantern OS report direction:

- prediction-market statistics receipts;
- `!trade`, `!spy`, and `!trade-gamble` skill setup;
- operator-controlled execution adapter boundary;
- money-validation PR plan;
- Oracle ARM + Ollama cost-optimized infra plan;
- rationality / Aumann / Bayesian founder / Supergrok fleet lore intake.

## RAGDoll house updates

| Topic | RAGDoll classification | Notes |
|---|---|---|
| Prediction-market statistics | research-only seed | No broker login, no live trade instruction, no profit claim. |
| Trade gamble product | product setup spec | Supports capped naked long call/put workflow as manual/product architecture. |
| Execution adapter | architecture spec | Not local-only; operator-controlled deployment can be local, VPS, cloud, CI, container, or broker-supported runtime. |
| Money validation | PR-gated test harness | Dry-run, paper, live_locked, live_confirm, live_armed, emergency_stop ladder. |
| Oracle ARM + Ollama | infra cost report | Low-cost model backend for Lantern OS agents and RAG tasks. |
| Rationality/Supergrok | conceptual lore receipt | Treat as design contract and knowledge model, not proof of live autonomous fleet. |

## Current branch/PR note

Direct master pushes were used for earlier receipts and skill definitions. The money-validation harness should proceed from a branch and PR. The GitHub connector failed to create the remote branch from chat, so the local workspace should create and push:

```powershell
git fetch origin
git switch -c test/trade-gamble-money-validations origin/master
git push -u origin test/trade-gamble-money-validations
```

After the branch exists, the product files can be added and reviewed through PR.

## Windows curl correction

PowerShell aliases `curl` to `Invoke-WebRequest`, so Linux flags like `-fsSL` fail. Use one of these instead:

```powershell
curl.exe -fsSL https://raw.githubusercontent.com/alex-place/lantern-os/master/infra/setup-lantern-oracle-arm-full.sh -o setup.sh
```

Or run the Linux command from SSH on the Oracle ARM Ubuntu server:

```bash
curl -fsSL https://raw.githubusercontent.com/alex-place/lantern-os/master/infra/setup-lantern-oracle-arm-full.sh | bash
```

## Boundaries

- No credentials in repo, prompts, RAG, PDFs, logs, or screenshots.
- No live broker order from chat.
- No exact live option contract instruction from chat.
- No profitability claim without paper/backtest evidence.
- Product architecture may support operator-controlled adapters under explicit risk gates.

## PDF generated

A new human-readable PDF report was generated for validation:

`LANTERN-OS-RAGDOLL-REPORTS-UPDATE-2026-05-29.pdf`
