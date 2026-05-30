# Kalshi + Ko-fi Watchlist Revenue Report

Generated: 2026-05-30T14:16:36.5597249-04:00

Status: current public-data manual-review candidates and outreach packet; no trades executed.

## Boundary

- This is not financial advice, investment advice, or a guarantee of profit.
- No Kalshi order was placed and no authenticated trading endpoint was used.
- No pooled capital, copy-trading, trade signals, or managed account offer.
- A market can become a trade candidate only after an independent probability estimate, max-loss budget, fee check, and manual review.

## Sources

- Kalshi public homepage: `https://kalshi.com/`
- Kalshi public markets endpoint: `https://external-api.kalshi.com/trade-api/v2/markets?status=open&mve_filter=exclude&limit=1000`
- Kalshi docs: `https://docs.kalshi.com/api-reference/market/get-markets`
- Kalshi public data quick start: `https://docs.kalshi.com/getting_started/quick_start_market_data`
- Ko-fi support link from existing repo reports: `https://ko-fi.com/alexplace`

## Snapshot

| Metric | Value |
|---|---:|
| Open markets pulled | 5000 |
| Public pages pulled | 5 / 5 |
| Cursor present | True |
| Empty/no-activity markets | 2651 |
| Wide-spread research-only markets | 268 |
| Excluded below 20-cent midpoint | 1445 |
| Excluded below $5.00 visible activity | 2905 |
| Watchlist rows emitted | 20 |
| Manual-approval queue rows | 3 |
| Executable trade recommendations | 0 |
| Trade readiness | research only; not actionable-trade ready |
| Manual review budget requested | $19 |

## Right Now Answer

Executable trades to make right now: **0**.

Best current use of this data: manually review the top watchlist rows, open the market rules in Kalshi, and build an independent probability note before any trade decision. Tight spread and activity make a market worth reading first; they do not prove edge.

Filters applied: do not include market values below 20 cents of YES midpoint, and do not include markets below $5.00 visible public activity.

Profit range is gross per contract if buying YES at the displayed ask: maximum loss is the ask paid; maximum gross profit is $1.00 minus the ask, before fees and slippage. Confidence is data-quality confidence only, not outcome probability.

After loading more data: Lantern can emit a manual-approval queue, but it still cannot place live trades. A human must approve any account action after independent probability, rule, fee, slippage, and max-loss checks.

Paper-ticket output: data/kalshi/kalshi-paper-trade-tickets-latest.json. Trade docs gate: manifests/evidence/kalshi-api-docs-and-trade-gate-2026-05-29.md.

Spread course: custom HFT/spread-capture research is preserved. Wider spreads can be desirable for a maker strategy, but only after orderbook depth, queue position, fees, latency, and cancel/fill risk are modeled.

## `$19` Manual Review Gate

Lantern is ready to prepare a public-data watchlist and research packet. It is not ready to make actionable trades, place orders, manage funds, or recommend that the operator buy or sell a market.

The $19 lane is a manual-review budget marker only:

- no authenticated Kalshi endpoint;
- no order placement;
- no automated execution;
- no claim of edge until independent probability, fees, spread, and max-loss notes exist;
- final trading decisions remain outside Lantern.

## Manual-Approval Queue

These rows are the closest thing to a trade queue after the deeper public-data load. They are not orders.

| Rank | Ticker | Mid | Gross P/L | Data Conf. | Required Before Trade |
|---:|---|---:|---|---:|---|
| 1 | KXMLBTOTAL-26MAY301610LAATB-9 | 0.365 | -0.37 to +0.63 | 70% | independent probability + human approval + max-loss budget |
| 2 | KXMLBF5-26MAY301610LAATB-TB | 0.485 | -0.49 to +0.51 | 70% | independent probability + human approval + max-loss budget |
| 3 | KXMLBTOTAL-26MAY301610LAATB-8 | 0.445 | -0.45 to +0.55 | 70% | independent probability + human approval + max-loss budget |

## Custom HFT / Spread-Capture Research Queue

This is the custom HFT direction: spread-aware, maker-style research. It is not live trading and it does not use account credentials.

| Rank | Ticker | Mid | Spread | Activity | Gross P/L | Required Before Live |
|---:|---|---:|---:|---:|---|---|
| 1 | KXCS2GAME-26MAY300700100TNEM-100T | 0.250 | 0.020 | 67127.77 | -0.26 to +0.74 | orderbook depth + fee model + latency sim + human approval |
| 2 | KXITFMATCH-26MAY30KLOTHA-KLO | 0.380 | 0.020 | 39807.76 | -0.39 to +0.61 | orderbook depth + fee model + latency sim + human approval |
| 3 | KXCS2GAME-26MAY300700100TNEM-NEM | 0.740 | 0.020 | 33621.11 | -0.75 to +0.25 | orderbook depth + fee model + latency sim + human approval |
| 4 | KXITFMATCH-26MAY30KLOTHA-THA | 0.620 | 0.020 | 18471.5 | -0.63 to +0.37 | orderbook depth + fee model + latency sim + human approval |
| 5 | KXMLBF5SPREAD-26MAY301915ATLCIN-ATL3 | 0.230 | 0.020 | 14495.22 | -0.24 to +0.76 | orderbook depth + fee model + latency sim + human approval |

## Top Watchlist

| Rank | Ticker | Title | Mid | Spread | Gross P/L | Data Conf. | Activity | 24h Vol | OI | Close | Gate |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|---|
| 1 | KXMLBTOTAL-26MAY301610LAATB-9 | Los Angeles A vs Tampa Bay Total Runs? | 0.365 | 0.010 | -0.37 to +0.63 | 70% | 1289.71 | 1289.71 | 1289.71 | 2026-06-02T20:10:00Z | no execution |
| 2 | KXMLBF5-26MAY301610LAATB-TB | Los Angeles A vs Tampa Bay first 5 innings winner? | 0.485 | 0.010 | -0.49 to +0.51 | 70% | 14546.12 | 14526.42 | 14545.12 | 2026-06-02T20:10:00Z | no execution |
| 3 | KXMLBTOTAL-26MAY301610LAATB-8 | Los Angeles A vs Tampa Bay Total Runs? | 0.445 | 0.010 | -0.45 to +0.55 | 70% | 11165.12 | 10891.18 | 9873.04 | 2026-06-02T20:10:00Z | no execution |
| 4 | KXMLBTOTAL-26MAY301610LAATB-6 | Los Angeles A vs Tampa Bay Total Runs? | 0.655 | 0.010 | -0.66 to +0.34 | 70% | 1866.27 | 1755.28 | 1866.27 | 2026-06-02T20:10:00Z | no execution |
| 5 | KXMLBTOTAL-26MAY301610LAATB-7 | Los Angeles A vs Tampa Bay Total Runs? | 0.575 | 0.010 | -0.58 to +0.42 | 70% | 883.47 | 883.47 | 808.57 | 2026-06-02T20:10:00Z | no execution |
| 6 | KXMLBF5SPREAD-26MAY301610LAATB-TB2 | Tampa Bay wins first 5 innings by over 1.5 runs? | 0.335 | 0.010 | -0.34 to +0.66 | 70% | 10448.53 | 10448.53 | 10448.53 | 2026-06-02T20:10:00Z | no execution |
| 7 | KXMLBSPREAD-26MAY301610BOSCLE-CLE2 | Cleveland wins by over 1.5 runs? | 0.345 | 0.010 | -0.35 to +0.65 | 70% | 18333.17 | 18219.18 | 18204.17 | 2026-06-02T20:10:00Z | no execution |
| 8 | KXHIGHLAX-26MAY31-B74.5 | Will the **high temp in LA** be 74-75?? on May 31, 2026? | 0.335 | 0.010 | -0.34 to +0.66 | 70% | 1108.72 | 1104.72 | 745.84 | 2026-06-01T07:59:00Z | no execution |
| 9 | KXHIGHTSFO-26MAY31-B72.5 | Will the maximum temperature be 72-73?? on May 31, 2026? | 0.285 | 0.010 | -0.29 to +0.71 | 70% | 599 | 599 | 363 | 2026-06-01T08:00:00Z | no execution |
| 10 | KXMLBF5TOTAL-26MAY301610LAATB-4 | Los Angeles A vs Tampa Bay first 5 innings runs? | 0.505 | 0.010 | -0.51 to +0.49 | 70% | 2496.53 | 2496.53 | 2168.46 | 2026-06-02T20:10:00Z | no execution |
| 11 | KXMLBSPREAD-26MAY301610BOSCLE-BOS2 | Boston wins by over 1.5 runs? | 0.325 | 0.010 | -0.33 to +0.67 | 70% | 869.16 | 869.16 | 869.16 | 2026-06-02T20:10:00Z | no execution |
| 12 | KXMLBTOTAL-26MAY301610MIANYM-8 | Miami vs New York M Total Runs? | 0.455 | 0.010 | -0.46 to +0.54 | 70% | 12777.56 | 12730.39 | 11597.14 | 2026-06-02T20:10:00Z | no execution |
| 13 | KXMLBF5-26MAY301610MIANYM-MIA | Miami vs New York M first 5 innings winner? | 0.375 | 0.010 | -0.38 to +0.62 | 70% | 972.71 | 972.71 | 972.71 | 2026-06-02T20:10:00Z | no execution |
| 14 | KXMLBTOTAL-26MAY301610MIANYM-7 | Miami vs New York M Total Runs? | 0.575 | 0.010 | -0.58 to +0.42 | 70% | 3773.17 | 3773.17 | 3614.02 | 2026-06-02T20:10:00Z | no execution |
| 15 | KXMLBSPREAD-26MAY301610MIANYM-MIA2 | Miami wins by over 1.5 runs? | 0.325 | 0.010 | -0.33 to +0.67 | 70% | 929.14 | 929.14 | 929.14 | 2026-06-02T20:10:00Z | no execution |
| 16 | KXMLBSPREAD-26MAY301610MIANYM-NYM2 | New York M wins by over 1.5 runs? | 0.355 | 0.010 | -0.36 to +0.64 | 70% | 8183.14 | 8183.14 | 7963.29 | 2026-06-02T20:10:00Z | no execution |
| 17 | KXMLBSPREAD-26MAY301610LAATB-LAA2 | Los Angeles A wins by over 1.5 runs? | 0.265 | 0.010 | -0.27 to +0.73 | 70% | 59091.32 | 59091.32 | 57627.94 | 2026-06-02T20:10:00Z | no execution |
| 18 | KXHIGHTHOU-26MAY31-B89.5 | Will the maximum temperature be 89-90?? on May 31, 2026? | 0.235 | 0.010 | -0.24 to +0.76 | 70% | 638.4 | 632.4 | 378.88 | 2026-06-01T06:00:00Z | no execution |
| 19 | KXHIGHTSATX-26MAY31-B88.5 | Will the maximum temperature be 88-89?? on May 31, 2026? | 0.305 | 0.010 | -0.31 to +0.69 | 70% | 794.4 | 794.4 | 455.14 | 2026-06-01T06:00:00Z | no execution |
| 20 | KXMLBTOTAL-26MAY301610LAATB-2 | Los Angeles A vs Tampa Bay Total Runs? | 0.975 | 0.010 | -0.98 to +0.02 | 70% | 1081.26 | 1081.26 | 1076.26 | 2026-06-02T20:10:00Z | no execution |

## Stats Model

Model name: `liquidity_spread_watchlist_v0`.

Inputs used:

- YES bid / ask / midpoint.
- Bid-ask spread.
- 24h volume, total volume, liquidity, and open interest.
- Visible activity floor and custom HFT spread-capture queue.
- Days to close.
- Title clarity and combo-market penalty.

What the model does:

- ranks markets worth reading first;
- rejects empty no-activity markets from the top list;
- flags wide-spread markets as research-only;
- preserves the trading gate: no order without independent probability and bankroll limit.

What the model does not do:

- it does not estimate true probability;
- it does not predict profit;
- it does not place trades;
- it does not sell trade signals.

## Ko-fi Revenue Lane

Use Ko-fi for support and paid research operations, not trade pooling.

| Offer | Price | Deliverable | Boundary |
|---|---:|---|---|
| Public supporter note | `$5` | Early watchlist snapshot and methodology note | no trade signals |
| Founder/support tester | `$20` | Weekly public-data market watchlist plus Lantern setup support | no managed money |
| Custom stats cleanup sprint | `$99-$299` | One repo/data/source cleanup plus a reproducible report | no investment advice |

## Outreach Copy

Short Ko-fi post:

> I pulled a live Kalshi public-market snapshot and turned it into a no-hype watchlist report: liquidity, spreads, close dates, and model gates. No trade signals, no pooled money, no guaranteed profit. If you want more open-source local-first stats tooling like this, support Lantern OS here: https://ko-fi.com/alexplace

Warm DM:

> I am testing a Lantern OS stats workflow: public Kalshi markets in, clean watchlist/report out. It ranks what is worth researching and blocks actual trade claims until independent probability work is done. If that kind of transparent AI/data tool is useful, I have a `$20` support lane on Ko-fi: https://ko-fi.com/alexplace

## Next Manual Actions

1. Review the top 20 watchlist rows manually in Kalshi UI.
2. Choose 3 markets with clear rules and real liquidity.
3. Build independent probability notes for those 3 markets from public sources.
4. If any edge exists after fees and spread, record a max-loss budget before any trade.
5. Publish the Ko-fi support note as a support/product update, not a trading advice post.