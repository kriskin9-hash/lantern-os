# Fleet Signal — Shnaider Validation Receipt

Date: 2026-05-29
Status: research-only receipt
Branch: master

## Fleet Signal

The highest-value validation target is still the Diana Shnaider 86% line. The correct action is not to trade; it is to run resolution-rule, market-metadata, order-book, and source checks.

The best normal research seeds are Swiatek and Sabalenka title baselines, followed by Osaka/Jovic as a short-horizon calibration sample.

## Why this matters

A displayed market percentage is not a validated probability. The RAGDoll fleet should treat large gaps between visible market pricing and public baseline evidence as validation targets, not immediate trade signals.

## Required validation checks

| Check | Purpose | Output |
|---|---|---|
| Resolution-rule check | Confirm exactly what the market resolves on | clear / ambiguous / reject |
| Market-metadata check | Confirm event, outcome, expiry, and token mapping | valid / stale / mismatched |
| Order-book check | Confirm depth, spread, and whether the visible price is executable | liquid / thin / misleading |
| Public-source check | Compare against current public evidence only | supported / unsupported |
| Baseline-stat check | Compare ranking, form, surface, draw, and historical rates | baseline range |
| Risk gate | Block private-info, jurisdiction, and autonomous execution risks | allow research / reject |

## Current research seed priority

| Rank | Seed | Role |
|---:|---|---|
| 1 | Diana Shnaider 86% line | anomaly validation target |
| 2 | Iga Swiatek title baseline | normal high-value baseline |
| 3 | Aryna Sabalenka title baseline | normal high-value baseline |
| 4 | Osaka/Jovic | short-horizon calibration sample |

## Hard boundary

Do not trade from this receipt. Do not log into accounts, use wallet keys, execute orders, or automate betting. This receipt exists to preserve the validation target and fleet method.

## Source trail

Sources checked in the chat response before this receipt:

- Reuters French Open day-six coverage
- Reuters Swiatek fourth-round report
- Reuters Sabalenka/Gauff/Osaka progress report
- WTA ranking table snapshot

The full citations remain in the chat response that generated this receipt.
