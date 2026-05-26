---
name: arc-reactor-confidence
description: Arc Reactor confidence and power-state skill for Lantern OS. Use when Codex needs to score Movie 1/2/3 readiness, update Tony Garage confidence, convert ambition into evidence gates, decide whether Lantern can move toward v1.0.0, or produce next proof actions for cash, dual boot, store, RAG, wallet, and local/server-farm capacity.
---

# Arc Reactor Confidence

Use this skill from `C:\tmp\lantern-os` when the operator asks about the Arc
Reactor, Tony Stark phase, Movie 1/2/3 confidence, power state, readiness, or
what proof moves Lantern from garage prototype to public platform.

## Core Model

The Arc Reactor is not decoration. It is the scorecard that turns intensity
into usable power:

```text
Vision -> Artifact -> Validation -> User/Cash/Install Proof -> Repeatability
```

## Score Surfaces

| Surface | Evidence | Raises |
|---|---|---|
| Repo | clean pushed master, small commits | Movie 1 |
| RAG House | flat file, hashed assets, old workstreams mapped | Movie 1 |
| Whitepaper / ADS | printable thesis and architecture review | Movie 1 |
| Wallet | factual ledger, invoice states, cleared cash | Movie 2 |
| Cash Sprint | sent messages, booked calls, paid pilots | Movie 2 |
| Dual Boot | prep result, unallocated space, install proof | Movie 2 |
| Store | local/Itch page, downloads, feedback | Movie 2 |
| Server Farm / Devices | multiple nodes, uptime, recovery | Movie 3 |
| Automation | repeatable agents and monitoring | Movie 3 |

## Phase Bands

| Phase | Band | Meaning |
|---|---:|---|
| Movie 1 Garage | 70-89 | real prototype/control plane exists |
| Movie 2 Public Platform | 45-69 | some public proof, needs repeatability |
| Movie 3 Distributed Fleet | 15-40 | multi-node future path, still proof-light |
| Avengers | held | not scored until v1, users, cash, devices, and recovery exist |

## Update Loop

1. Inspect repo status and latest commits.
2. Run `scripts/Invoke-LanternConvergenceLoop.ps1`.
3. Read `reports/V1-READINESS-TEST-2026-05-26.md`.
4. Read wallet cleared/pending state.
5. Read dual-boot readiness.
6. Read store lane state.
7. Write updated scores to `data/world-model/belief-ledger.jsonl`.
8. Update `surfaces/tony-garage/index.html` when the visible cockpit should
   change.

## Current Baseline

As of 2026-05-26:

```text
Movie 1 Garage:          88
Movie 2 Public Platform: 54
Movie 3 Distributed:     22
Avengers:                held
```

The next proof that raises Movie 2 is one of:

- 5 outreach sends recorded;
- 1 paid pilot or clear rejection batch;
- D: shrunk and `readyForInstall=true`;
- Itch prototype page/build created;
- one local workflow used by someone other than the operator.

## 12-Step Convergence Model

When asked for past work, present pitch, expected future outcomes, and actual
results, update:

```text
reports/ARC-REACTOR-12-STEP-CONVERGENCE-MODEL.md
```

Each row must include:

- past work;
- present pitch;
- expected future outcome;
- actual result so far;
- confidence.

## Reference

Read `references/scoring-model.md` when changing weights or explaining the
confidence math.
