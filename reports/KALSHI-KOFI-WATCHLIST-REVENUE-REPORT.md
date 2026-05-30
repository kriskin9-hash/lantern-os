# Kalshi + Ko-fi Watchlist Revenue Report

Generated: 2026-05-29T21:53:43.6805924-04:00

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
| Empty/no-activity markets | 2794 |
| Wide-spread research-only markets | 711 |
| Excluded below 20-cent midpoint | 1393 |
| Excluded below $5.00 visible activity | 3156 |
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
| 1 | KXLOWTCHI-26MAY30-T58 | 0.585 | -0.59 to +0.41 | 70% | independent probability + human approval + max-loss budget |
| 2 | KXHIGHTSEA-26MAY30-B64.5 | 0.225 | -0.23 to +0.77 | 70% | independent probability + human approval + max-loss budget |
| 3 | KXMLBTOTAL-26MAY301610MILHOU-9 | 0.515 | -0.52 to +0.48 | 70% | independent probability + human approval + max-loss budget |

## Custom HFT / Spread-Capture Research Queue

This is the custom HFT direction: spread-aware, maker-style research. It is not live trading and it does not use account credentials.

| Rank | Ticker | Mid | Spread | Activity | Gross P/L | Required Before Live |
|---:|---|---:|---:|---:|---|---|
| 1 | KXWNBA1HSPREAD-26MAY29ATLPDX-ATL5 | 0.500 | 0.020 | 7424.61 | -0.51 to +0.49 | orderbook depth + fee model + latency sim + human approval |
| 2 | KXMLBTOTAL-26MAY301605KCTEX-8 | 0.540 | 0.020 | 6810.38 | -0.55 to +0.45 | orderbook depth + fee model + latency sim + human approval |
| 3 | KXAAAGASD-26MAY30-4.340 | 0.970 | 0.020 | 4800.61 | -0.98 to +0.02 | orderbook depth + fee model + latency sim + human approval |
| 4 | KXHIGHLAX-26MAY30-B68.5 | 0.240 | 0.020 | 4336.09 | -0.25 to +0.75 | orderbook depth + fee model + latency sim + human approval |
| 5 | KXHIGHTDAL-26MAY30-B92.5 | 0.580 | 0.020 | 1931.49 | -0.59 to +0.41 | orderbook depth + fee model + latency sim + human approval |

## Top Watchlist

| Rank | Ticker | Title | Mid | Spread | Gross P/L | Data Conf. | Activity | 24h Vol | OI | Close | Gate |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|---|
| 1 | KXLOWTCHI-26MAY30-T58 | Will the minimum temperature be >58?? on May 30, 2026? | 0.585 | 0.010 | -0.59 to +0.41 | 70% | 2526.65 | 2526.65 | 1001.26 | 2026-05-31T06:00:00Z | no execution |
| 2 | KXHIGHTSEA-26MAY30-B64.5 | Will the maximum temperature be 64-65?? on May 30, 2026? | 0.225 | 0.010 | -0.23 to +0.77 | 70% | 823.09 | 823.09 | 579.08 | 2026-05-31T08:00:00Z | no execution |
| 3 | KXMLBTOTAL-26MAY301610MILHOU-9 | Milwaukee vs Houston Total Runs? | 0.515 | 0.010 | -0.52 to +0.48 | 70% | 1541 | 1541 | 907 | 2026-06-02T20:10:00Z | no execution |
| 4 | KXMLBSPREAD-26MAY302205NYYATH-NYY2 | New York Y wins by over 1.5 runs? | 0.465 | 0.010 | -0.47 to +0.53 | 70% | 1522.71 | 1522.71 | 1317.56 | 2026-06-03T02:05:00Z | no execution |
| 5 | KXSPOTIFYGLOBALD-26MAY29-HAT | Top Global Song on Spotify on May 29, 2026? | 0.975 | 0.010 | -0.98 to +0.02 | 70% | 3360.64 | 3360.64 | 3069.64 | 2026-05-30T03:59:00Z | no execution |
| 6 | KXBRENTD-26JUN0117-T86.50 | Will the brent crude oil close price be above 86.50 USD/Bbl on June 01, 2026 at 5:00 PM EDT? | 0.845 | 0.010 | -0.85 to +0.15 | 70% | 1609 | 1609 | 1609 | 2026-06-01T21:00:00Z | no execution |
| 7 | KXBRENTD-26JUN0117-T83.00 | Will the brent crude oil close price be above 83.00 USD/Bbl on June 01, 2026 at 5:00 PM EDT? | 0.945 | 0.010 | -0.95 to +0.05 | 70% | 777.71 | 777.71 | 768.71 | 2026-06-01T21:00:00Z | no execution |
| 8 | KXHIGHTSFO-26MAY30-B67.5 | Will the maximum temperature be 67-68?? on May 30, 2026? | 0.345 | 0.010 | -0.35 to +0.65 | 70% | 2116.79 | 2116.79 | 1146.34 | 2026-05-31T08:00:00Z | no execution |
| 9 | KXITFMATCH-26MAY29SHIKIM-KIM | Will Dong Ju Kim win the Shin vs Kim: M15 Gimcheon Semifinal match? | 0.215 | 0.010 | -0.22 to +0.78 | 70% | 616.6 | 603.67 | 616.6 | 2026-06-13T02:00:00Z | no execution |
| 10 | KXMLBTOTAL-26MAY301410DETCWS-8 | Detroit vs Chicago WS Total Runs? | 0.535 | 0.010 | -0.54 to +0.46 | 70% | 582.4 | 582.4 | 582.4 | 2026-06-02T18:10:00Z | no execution |
| 11 | KXSPOTIFYD-26MAY29-HAT | Top USA Song on Spotify on May 29, 2026? | 0.965 | 0.010 | -0.97 to +0.03 | 70% | 1328.59 | 1321.53 | 1321.53 | 2026-05-30T03:59:00Z | no execution |
| 12 | KXHIGHLAX-26MAY30-B72.5 | Will the **high temp in LA** be 72-73?? on May 30, 2026? | 0.215 | 0.010 | -0.22 to +0.78 | 70% | 2876.31 | 2876.31 | 1757.75 | 2026-05-31T07:59:00Z | no execution |
| 13 | KXHIGHLAX-26MAY30-B70.5 | Will the **high temp in LA** be 70-71?? on May 30, 2026? | 0.515 | 0.010 | -0.52 to +0.48 | 70% | 1646.98 | 1646.98 | 1201.78 | 2026-05-31T07:59:00Z | no execution |
| 14 | KXVOTEHUBTRUMPUPDOWN-26JUN04 | Will Donald Trump's approval rating be above 39.3% for Jun 4, 2026? | 0.445 | 0.010 | -0.45 to +0.55 | 70% | 2996.46 | 2996.46 | 2767.76 | 2026-06-05T03:59:00Z | no execution |
| 15 | KXHIGHTDAL-26MAY30-B94.5 | Will the maximum temperature be 94-95?? on May 30, 2026? | 0.225 | 0.010 | -0.23 to +0.77 | 70% | 591.36 | 591.36 | 573.78 | 2026-05-31T06:00:00Z | no execution |
| 16 | KXMLBSPREAD-26MAY301915ATLCIN-ATL2 | Atlanta wins by over 1.5 runs? | 0.435 | 0.010 | -0.44 to +0.56 | 70% | 805.03 | 805.03 | 805.03 | 2026-06-02T23:15:00Z | no execution |
| 17 | KXAPRPOTUS-26JUN05-39.4 | Will the President's approval rating be between 39.3 and 39.5 according to RealClearPolitics? | 0.225 | 0.010 | -0.23 to +0.77 | 70% | 654.42 | 654.42 | 623.42 | 2026-06-05T15:00:00Z | no execution |
| 18 | KXHIGHTSATX-26MAY30-T89 | Will the maximum temperature be <89?? on May 30, 2026? | 0.475 | 0.010 | -0.48 to +0.52 | 70% | 1246.71 | 1246.71 | 565.55 | 2026-05-31T06:00:00Z | no execution |
| 19 | KXAPRPOTUS-26JUN05-39.7 | Will the President's approval rating be between 39.6 and 39.8 according to RealClearPolitics? | 0.245 | 0.010 | -0.25 to +0.75 | 70% | 797.24 | 797.24 | 709.85 | 2026-06-05T15:00:00Z | no execution |
| 20 | KXBRENTD-26JUN0117-T84.00 | Will the brent crude oil close price be above 84.00 USD/Bbl on June 01, 2026 at 5:00 PM EDT? | 0.925 | 0.010 | -0.93 to +0.07 | 70% | 615.09 | 615.09 | 577 | 2026-06-01T21:00:00Z | no execution |

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