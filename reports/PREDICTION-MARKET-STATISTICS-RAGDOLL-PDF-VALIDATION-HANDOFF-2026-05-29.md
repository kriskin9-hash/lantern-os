# Prediction Market Statistics RAGDoll — PDF Validation Handoff

Date: 2026-05-29
Branch: master
Status: pushed for operator PDF validation

## Purpose

This handoff preserves the latest convergence around the Polymarket Agents / prediction-market statistics idea as a research-only Lantern OS / RAGDoll skill seed.

It is intended to support a later human-readable PDF validation pass.

## Evidence boundary

The uploaded Polymarket Agents README evidence showed:

- the upstream repository is archived and read-only;
- the repository describes a Python 3.9 developer framework for Polymarket agents;
- it includes Polymarket API integration, Gamma market metadata tooling, CLOB/order tooling, local/remote RAG support, news/data sourcing, Pydantic objects, and CLI market listing;
- it also contains autonomous trading entry points;
- its Terms of Service note prohibits U.S. persons and people in certain jurisdictions from trading through Polymarket UI/API/agents.

Lantern OS should therefore treat this as research architecture, not a live betting system.

## Converged skill

```text
ragdoll.skill.prediction_market_statistics.v1

Mode:
  research-only by default

Inputs:
  market metadata
  current prices
  volume/liquidity
  resolution rules
  public evidence
  related markets
  historical/base-rate data

Core outputs:
  implied probability
  base-rate probability
  evidence-adjusted probability
  confidence band
  ambiguity score
  liquidity/slippage risk
  legal/compliance gate
  recommended action: reject / watch / paper-trade / human-review
```

## Agent table

| Agent | Statistical job | Output |
|---|---|---|
| Market Scanner | Find liquid markets with enough volume | candidate list |
| Resolution Agent | Parse settlement criteria | valid / ambiguous / reject |
| Price Agent | Pull current Yes/No prices | implied probability |
| History Agent | Track price movement over time | trend / volatility |
| Evidence Agent | Gather public sources | source bundle |
| Base-rate Agent | Compare to historical frequency | prior probability |
| Arbitrage Agent | Check related outcomes sum near 100% | inconsistency flags |
| Stance Agent | Summarize comments/news sentiment | directional signal |
| Risk Agent | Block insider/private/thin/ambiguous markets | allow / reject |
| Human Operator | Final decision | no action / watch / paper trade / legal trade |

## Research triage table

| Market type | Statistical edge to look for | Useful metric | Fleet action |
|---|---|---|---|
| Sports favorites | Mispriced injury/news reaction | price move vs confirmed news | watch / paper trade |
| Sports coin-flips | Spread disagreement across markets | 45-55% drift plus volume | compare only |
| Elections | Polling/base-rate mismatch | market probability vs polling average | research brief |
| Crypto targets | Volatility-implied probability mismatch | price distance plus time remaining | alert only |
| Fed / CPI / rates | Calendar-driven stale markets | expected range vs market odds | high-value research |
| Awards | Public sentiment vs insider-like buzz risk | nomination history plus guild data | cautious brief |
| Geopolitics | Usually reject | source quality / insider risk | block |
| Viral/news | Resolution ambiguity | clarity score | reject unless clear |
| Same-day markets | Fast public-info lag | timestamped source delta | alert only |

## Hard gates

1. Do not trade autonomously.
2. Do not trade from restricted jurisdictions.
3. Do not use private, leaked, employer, confidential, classified, medical, military, or insider information.
4. Do not treat common odds as edge.
5. Do not use prediction markets as the primary $200-now plan.
6. Use this as a demonstrable analytics/RAG/fleet asset instead.

## $200-now packaging note

The strongest monetizable package remains a fixed-scope audit offer:

- $199 MCP / RAG / GitHub automation audit
- one-page findings report
- optional cleanup PR or issue list
- 24-hour turnaround

The prediction-market statistics skill can be shown as a demo of the operator's fleet capability, not as a promise of trading profit.

## PDF validation checklist

A validated PDF should be:

- human-readable, not filepath spam;
- clear that this is research-only;
- clear about legal/compliance gates;
- clear about the statistical value of the repo;
- clear that the fastest $200 path is service packaging, not gambling;
- formatted with concise tables and no unsupported profit claims.
