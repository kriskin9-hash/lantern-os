# !trade Skill — OSS Intraday Signal Research Fleet

Status: research-only by default
Default mode: paper trade
Live execution: disabled unless a separate human-approved implementation exists

## Purpose

`!trade` is a Lantern OS / RAGDoll skill for building and validating an OSS intraday signal research stack.

It is not financial advice, not a promise of profit, and not a live-order automation skill.

The skill exists to convert market ideas into logged, testable, risk-capped research receipts.

## Supported universe

Initial watchlist:

- SPY
- QQQ
- AAPL
- MSFT
- NVDA
- TSLA
- META
- AMZN
- GOOGL

## OSS stack

| Layer | Preferred tools | Purpose |
|---|---|---|
| Data sandbox | Python, pandas, yfinance/Stooq/CSV imports | slow research and local fixtures |
| Fast research | vectorbt | indicator sweeps and fast signal scans |
| Backtest engine | Backtrader or QuantConnect LEAN | strategy validation with fees/slippage |
| Paper broker | Alpaca paper or IBKR paper | simulated order handling |
| Crypto-only bot lane | Hummingbot / Freqtrade | separate crypto experiments only |
| Ledger | SQLite/Postgres/CSV | every signal, order, fill, and result |
| Operator UI | Lantern OS dashboard | human approval and daily report |

## Agent roles

| Agent | Job | Output |
|---|---|---|
| Data Agent | Pull OHLCV, calendar, option-chain, VIX, and spread data | normalized dataset |
| Regime Agent | Classify trend/chop/panic/squeeze | market regime |
| Signal Agent | Evaluate VWAP, opening range, gap fade, and continuation setups | candidate signal |
| Options Agent | Check chain, delta, IV, spread, OI, and expiration risk | option viability |
| Risk Agent | Enforce max loss, no averaging down, no revenge trade | allow / reject |
| Execution Agent | Paper orders only by default | simulated fill |
| Report Agent | Produce daily receipt/PDF summary | human-readable report |

## Strategy candidates

| Strategy | Tickers | Description | Default action |
|---|---|---|---|
| VWAP reclaim/rejection | SPY, QQQ | price confirms above/below VWAP | paper-track |
| Opening range breakout | SPY, QQQ, NVDA | break and hold above/below opening range | paper-track |
| Gap fade | SPY, QQQ, AAPL, MSFT | failed continuation after large open gap | paper-track |
| Momentum continuation | NVDA, TSLA, QQQ | volume-supported trend continuation | paper-track, high risk |
| Options debit spread proxy | SPY, QQQ | defined-risk option expression of share signal | micro only after validation |
| Crypto market-making | BTC, ETH | spread capture on crypto venues | separate stack only |

## Risk gates

Hard rules:

1. No live trade by default.
2. No broker keys in repo.
3. No wallet keys in repo.
4. No trade without max loss known before entry.
5. No averaging down.
6. No second trade after a loss in the same test session.
7. No 0DTE full-send behavior.
8. No strategy promotion until at least 100 paper trades are logged.

Minimum validation before live micro:

| Gate | Minimum |
|---|---|
| Paper trades | 100+ |
| Fees/slippage | modeled |
| Spread filter | present |
| Max daily loss | fixed |
| Kill switch | tested |
| Average R | positive after costs |
| Drawdown | documented |
| Human approval | required |

## $100 high-risk sleeve policy

If the operator assigns a $100 high-risk sleeve, the skill must treat it as capped tuition, not core capital.

| Bucket | Max | Rule |
|---|---:|---|
| Live micro test | $25-$40 | one defined-risk idea only |
| Paper mirror | remainder | track missed/alternate ideas |
| Max daily live loss | $40 | stop after loss |
| Max trades/day | 1 | no revenge trade |

## Output receipt schema

```yaml
skill: ragdoll.skill.intraday_signal_research.v1
mode: paper
universe:
  - SPY
  - QQQ
  - AAPL
  - MSFT
  - NVDA
  - TSLA
  - META
  - AMZN
  - GOOGL
signal:
  ticker: null
  timestamp: null
  timeframe: null
  regime: null
  setup: null
  direction_bias: bullish|bearish|neutral
  premium_bias: buy|sell|avoid
  above_or_below_vwap: null
  opening_range_status: null
  spread_ok: false
  max_loss: null
  invalidation_level: null
  action: reject|watch|paper_trade|human_review
result:
  entry: null
  exit: null
  pnl: null
  r_multiple: null
  mistake_notes: null
```

## Promotion path

1. Run offline backtest.
2. Run paper-trade harness.
3. Generate daily RAGDoll receipts.
4. Review 100+ paper trades.
5. Only then consider live micro with hard risk caps.
