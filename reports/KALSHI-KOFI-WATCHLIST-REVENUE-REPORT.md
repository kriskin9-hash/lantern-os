# Kalshi + Ko-fi Watchlist Revenue Report

Generated: 2026-05-29T22:48:30.1420236-04:00

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
| Empty/no-activity markets | 3061 |
| Wide-spread research-only markets | 599 |
| Excluded below 20-cent midpoint | 1232 |
| Excluded below $5.00 visible activity | 3426 |
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
| 1 | KXHIGHTBOS-26MAY30-B56.5 | 0.225 | -0.23 to +0.77 | 70% | independent probability + human approval + max-loss budget |
| 2 | KXMLBTOTAL-26MAY302205NYYATH-10 | 0.505 | -0.51 to +0.49 | 70% | independent probability + human approval + max-loss budget |
| 3 | KXAAAGASW-26JUN01-4.290 | 0.975 | -0.98 to +0.02 | 70% | independent probability + human approval + max-loss budget |

## Custom HFT / Spread-Capture Research Queue

This is the custom HFT direction: spread-aware, maker-style research. It is not live trading and it does not use account credentials.

| Rank | Ticker | Mid | Spread | Activity | Gross P/L | Required Before Live |
|---:|---|---:|---:|---:|---|---|
| 1 | KXITFMATCH-26MAY29MAGDEL-DEL | 0.740 | 0.020 | 67115.46 | -0.75 to +0.25 | orderbook depth + fee model + latency sim + human approval |
| 2 | KXMLBTOTAL-26MAY301605KCTEX-8 | 0.530 | 0.020 | 13100.14 | -0.54 to +0.46 | orderbook depth + fee model + latency sim + human approval |
| 3 | KXWNBA1HWINNER-26MAY29ATLPDX-ATL | 0.780 | 0.020 | 11993.5 | -0.79 to +0.21 | orderbook depth + fee model + latency sim + human approval |
| 4 | KXHIGHLAX-26MAY30-B72.5 | 0.220 | 0.020 | 2989.32 | -0.23 to +0.77 | orderbook depth + fee model + latency sim + human approval |
| 5 | KXHIGHLAX-26MAY30-B70.5 | 0.550 | 0.020 | 2233.39 | -0.56 to +0.44 | orderbook depth + fee model + latency sim + human approval |

## Top Watchlist

| Rank | Ticker | Title | Mid | Spread | Gross P/L | Data Conf. | Activity | 24h Vol | OI | Close | Gate |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|---|
| 1 | KXHIGHTBOS-26MAY30-B56.5 | Will the maximum temperature be 56-57?? on May 30, 2026? | 0.225 | 0.010 | -0.23 to +0.77 | 70% | 700.98 | 696.98 | 563.87 | 2026-05-31T05:00:00Z | no execution |
| 2 | KXMLBTOTAL-26MAY302205NYYATH-10 | New York Y vs A's Total Runs? | 0.505 | 0.010 | -0.51 to +0.49 | 70% | 3129 | 3127 | 3076 | 2026-06-03T02:05:00Z | no execution |
| 3 | KXAAAGASW-26JUN01-4.290 | Will average **gas prices** be above $4.290? | 0.975 | 0.010 | -0.98 to +0.02 | 70% | 6557.6 | 6557.6 | 6511.6 | 2026-06-01T03:59:00Z | no execution |
| 4 | KXSPOTIFYD-26MAY29-HAT | Top USA Song on Spotify on May 29, 2026? | 0.965 | 0.010 | -0.97 to +0.03 | 70% | 2693.03 | 2384.11 | 2384.5 | 2026-05-30T03:59:00Z | no execution |
| 5 | KXMLBSPREAD-26MAY301915ATLCIN-ATL2 | Atlanta wins by over 1.5 runs? | 0.445 | 0.010 | -0.45 to +0.55 | 70% | 2410.85 | 2378.76 | 2405.85 | 2026-06-02T23:15:00Z | no execution |
| 6 | KXHIGHTSEA-26MAY30-B64.5 | Will the maximum temperature be 64-65?? on May 30, 2026? | 0.235 | 0.010 | -0.24 to +0.76 | 70% | 869.09 | 858.09 | 621.08 | 2026-05-31T08:00:00Z | no execution |
| 7 | KXHIGHTATL-26MAY30-T85 | Will the maximum temperature be >85?? on May 30, 2026? | 0.315 | 0.010 | -0.32 to +0.68 | 70% | 3178.23 | 3169.23 | 1485.88 | 2026-05-31T05:00:00Z | no execution |
| 8 | KXVOTEHUBTRUMPUPDOWN-26JUN04 | Will Donald Trump's approval rating be above 39.3% for Jun 4, 2026? | 0.445 | 0.010 | -0.45 to +0.55 | 70% | 3005.12 | 3005.12 | 2776.42 | 2026-06-05T03:59:00Z | no execution |
| 9 | KXLOWTDEN-26MAY30-T48 | Will the minimum temperature be <48?? on May 30, 2026? | 0.295 | 0.010 | -0.30 to +0.70 | 70% | 1229.19 | 1229.19 | 476.17 | 2026-05-31T07:00:00Z | no execution |
| 10 | KXHIGHTBOS-26MAY30-B60.5 | Will the maximum temperature be 60-61?? on May 30, 2026? | 0.245 | 0.010 | -0.25 to +0.75 | 70% | 1658.61 | 1656.04 | 1590.08 | 2026-05-31T05:00:00Z | no execution |
| 11 | KXHIGHTPHX-26MAY30-B92.5 | Will the maximum temperature be 92-93?? on May 30, 2026? | 0.445 | 0.010 | -0.45 to +0.55 | 70% | 1151.51 | 1150.51 | 861.81 | 2026-05-31T07:00:00Z | no execution |
| 12 | KXMLBSPREAD-26MAY302205NYYATH-NYY2 | New York Y wins by over 1.5 runs? | 0.475 | 0.010 | -0.48 to +0.52 | 70% | 1944.11 | 1944.11 | 1738.96 | 2026-06-03T02:05:00Z | no execution |
| 13 | KXMLBSPREAD-26MAY301610LAATB-LAA2 | Los Angeles A wins by over 1.5 runs? | 0.265 | 0.010 | -0.27 to +0.73 | 70% | 41515.67 | 41515.67 | 41493 | 2026-06-02T20:10:00Z | no execution |
| 14 | KXMLBSPREAD-26MAY301610LAATB-TB2 | Tampa Bay wins by over 1.5 runs? | 0.395 | 0.010 | -0.40 to +0.60 | 70% | 2153.37 | 2153.37 | 2153.37 | 2026-06-02T20:10:00Z | no execution |
| 15 | KXMLBSPREAD-26MAY301610MILHOU-MIL2 | Milwaukee wins by over 1.5 runs? | 0.385 | 0.010 | -0.39 to +0.61 | 70% | 1189.03 | 1189.03 | 1005.03 | 2026-06-02T20:10:00Z | no execution |
| 16 | KXHIGHAUS-26MAY30-T90 | Will the **high temp in Austin** be <90?? on May 30, 2026? | 0.315 | 0.010 | -0.32 to +0.68 | 70% | 2850.12 | 2850.12 | 1613.64 | 2026-05-31T05:59:00Z | no execution |
| 17 | KXMLBTOTAL-26MAY301610MILHOU-9 | Milwaukee vs Houston Total Runs? | 0.515 | 0.010 | -0.52 to +0.48 | 70% | 1898 | 1898 | 1130 | 2026-06-02T20:10:00Z | no execution |
| 18 | KXHIGHMIA-26MAY30-B89.5 | Will the **high temp in Miami** be 89-90?? on May 30, 2026? | 0.405 | 0.010 | -0.41 to +0.59 | 70% | 2481.94 | 2465.99 | 1787.24 | 2026-05-31T04:59:00Z | no execution |
| 19 | KXHIGHPHIL-26MAY30-B70.5 | Will the **high temp in Philadelphia** be 70-71?? on May 30, 2026? | 0.525 | 0.010 | -0.53 to +0.47 | 70% | 716.67 | 715.67 | 655.55 | 2026-05-31T04:59:00Z | no execution |
| 20 | KXSPOTIFYGLOBALD-26MAY29-HAT | Top Global Song on Spotify on May 29, 2026? | 0.975 | 0.010 | -0.98 to +0.02 | 70% | 3360.64 | 3360.64 | 3069.64 | 2026-05-30T03:59:00Z | no execution |

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