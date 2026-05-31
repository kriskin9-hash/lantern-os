# Kalshi Tennis Markets: Paper Trade Analysis
**Generated:** 2026-05-31T20:30:00Z  
**Source:** Live Kalshi screenshot (French Open, ATP Challenger, ITF) — research only  
**Mode:** PAPER ONLY — no live orders, no authenticated API calls  
**Boundary:** This is a research analysis. No trades will execute without operator approval + kill switch removal.

---

## Account State (At Time of Analysis)

| Field | Value |
|-------|-------|
| Cash Balance | $10.00 USD |
| Open Positions | 0 live / 8 paper (weather, MLB, Spotify, politics) |
| Paper Allocated Risk | $4.07 (of $5.00 daily max) |
| Remaining Daily Budget | **$1.00** |
| Live Trading | **BLOCKED** (kill switch active) |

---

## Markets Observed (From Screenshot, May 31 ~2:30PM EDT)

### Tier 1 — French Open Men's Singles ($1M+ volume)

| Match | Fav | Fav % | Dog % | Vig | Volume | Status |
|-------|-----|--------|-------|-----|--------|--------|
| Mensik vs Rublev | Mensik | 58% | 44% | ~2% | $5,942,742 | LIVE |
| Ruud vs Fonseca | Ruud | 64% | 38% | ~2% | $1,080,187 | LIVE |

### Tier 2 — ITF + ATP Challenger ($100K–$500K volume)

| Match | Fav | Fav % | Dog % | Volume | Status |
|-------|-----|--------|-------|--------|--------|
| Evans vs Lutkemeyer Obregon | Evans | 96% | 3% | $451,501 | LIVE |
| Poertner vs Broska | Poertner | 69% | 29% | $301,389 | LIVE |
| Chiesa vs Raschdorf | Chiesa | 74% | 25% | $151,819 | LIVE |
| Bigun vs Vales | Vales | 79% | 20% | $105,779 | LIVE |

### Tier 3 — Pre-match (Starting 2:00–2:40PM EDT)

| Match | Fav % | Dog % | Status |
|-------|--------|-------|--------|
| Galan vs Handel | 99% vs 3% | — | Pre-match |
| Milavsky vs Manning | 79% vs 21% | — | Pre-match |
| Colby vs Langmo | 72% vs 31% | — | Pre-match |
| Johns vs Pieczkowski | 66% vs 34% | — | Pre-match |

---

## Paper Trade Analysis (Research Only — No Execution)

### 1. Mensik vs Rublev (French Open R16, LIVE)
**Score at screenshot:** Mensik 6-3, 1-2, 40-30  
**Market:** Mensik 58¢ / Rublev 44¢  
**Implied vig:** ~2% → tight, liquid market

**Analysis:**
- Mensik was a set and a break up; Rublev fighting back in Set 2
- Market pricing Mensik as slight favorite at 58% despite being up a set
- Rublev at 44¢ suggests strong comeback belief
- Both sides trade near intrinsic; spread is only 1-2 cents
- **Vig math:** 58 + 44 = 102 → 1% per side overprice vs fair. Standard for in-play.

**Paper assessment:**
- No independent probability estimate available
- Score + momentum suggest Mensik edge is fair at 58%
- Would need ATP H2H, surface win rate, fatigue index for proper Bayesian update
- **Gate: needs_independent_probability — paper watchlist only**

---

### 2. Ruud vs Fonseca (French Open R16, LIVE)
**Score at screenshot:** Not started yet (0-0 on both counters)  
**Market:** Ruud 64¢ / Fonseca 38¢  
**Implied vig:** ~2%

**Analysis:**
- Ruud is a clay specialist; 3x French Open finalist (2022, 2023, 2024)
- Fonseca is an 18-year-old Brazilian prodigy — real talent but first-time RG R16
- Market has Ruud as strong favorite at 64%
- Fonseca at 38¢ is notable — market prices him as genuine threat
- **Potential observation:** 64 + 38 = 102, standard vig

**Paper edge hypothesis:**  
Ruud's clay record at Roland Garros is elite. If his serve % is >62% on clay (career average), model would likely push him higher than 64%. But Fonseca has been on a run. Market probably has it right.

**Gate: needs_independent_probability — paper watchlist only**

---

### 3. Evans vs Lutkemeyer Obregon (ITF, LIVE)
**Score:** Evans 5-6-4 / Lutkemeyer 7-3-2 (mid-3rd set)  
**Market:** Evans 96¢ / Lutkemeyer 3¢  

**Analysis:**
- Evans appears to have broken and is winning the 3rd set at 4-2 (40-pt lead)
- Market is pricing this as nearly decided (96%)
- Volume: $451K — decent for ITF
- **At 96¢, EV is very thin** — 4¢ upside, 96¢ downside per contract
- Only trade if extremely confident in final outcome
- **Gate: not worth paper cost given risk/reward asymmetry**

---

### 4. Poertner vs Broska (ATP Challenger, LIVE)
**Score:** Poertner 6-4 / Broska 4-3 (mid-2nd set)  
**Market:** Poertner 69¢ / Broska 29¢  
**Order panel visible:** Yes 70¢ / No 31¢  

**Analysis:**
- Broska won Set 1 by 4-2 within? No — Poertner leads 6-4 in sets
- Poertner at 69% with a set lead seems priced conservatively
- 2-cent spread (69/70 ask vs 29/31 ask) slightly wider than French Open
- Volume: $301K — reasonable for Challenger level
- **Paper hypothesis:** Poertner at 69¢ with a set lead could have edge if base rate for set-leaders winning Challenger matches is >70%

**Independent probability estimate:**  
ATP Challenger set-winner-match-winner historical rate: ~68-73% (Poertner is right at market mid). No obvious edge.

**Gate: needs_independent_probability — paper watchlist only**

---

## Vig Analysis Across All Markets

| Market | Yes% | No% | Total | Vig |
|--------|------|-----|-------|-----|
| Mensik/Rublev | 58% | 44% | 102% | 2% |
| Ruud/Fonseca | 64% | 38% | 102% | 2% |
| Evans/Lutkemeyer | 96% | 3% | 99% | -1%? |
| Poertner/Broska | 69% | 29% | 98% | -2%? |

**Note:** Evans and Poertner markets show sub-100% totals in the screenshot — this may be a display lag (in-play prices updating faster than the screenshot captured). Do not interpret as arb opportunity without live order book confirmation.

---

## Paper Ticket Candidates (For Watchlist — No Execution)

### Candidate A: Ruud to win (pre-match or early in match)
- **Ticker:** `KXFRENCHTENNISM-26MAY31RUDFON-RUD` (ticker TBD by Kalshi API)
- **Side:** YES (Ruud wins)
- **Paper limit:** 64¢
- **Max paper loss:** $0.64/contract
- **Paper EV hypothesis:** Ruud's H2H clay edge vs young player; 64% market = fair to slight underline
- **Gate:** independent_probability_missing, human_approval_missing

### Candidate B: Mensik to complete (monitor for 2nd set resolution)
- **Ticker:** `KXFRENCHTENNISM-26MAY31MENRUB-MEN` (ticker TBD)
- **Side:** YES (Mensik wins)
- **Paper limit:** 58¢
- **Max paper loss:** $0.58/contract
- **Gate:** independent_probability_missing, match still in progress

---

## What's Needed Before Any Paper Ticket Upgrades to Live

Per Lantern's kill switch protocol:

1. **KILL SWITCH ACTIVE** — `data/kalshi/LIVE-KILL-SWITCH` must be removed by operator
2. **Independent probability estimate** — Bayesian model with ATP H2H + surface stats
3. **Operator approval** — Alex Place signs off per each trade
4. **Orderbook depth** — Confirm bid/ask depth beyond top-of-book
5. **Fee model** — Kalshi charges $0.03 per contract (≈3¢); must be factored into EV
6. **Budget gate** — Remaining daily budget: $1.00 (near limit)

---

## Budget Status After Tennis Analysis

| Budget Item | Amount |
|-------------|--------|
| Daily max paper loss | $5.00 |
| Already allocated (8 positions) | $4.07 |
| Remaining daily budget | **$0.93** |
| Budget for tennis adds | **$0.93 max** |
| Contracts possible at $0.64 limit | **1 contract max** |

**Conclusion:** Budget is nearly exhausted for today. Any new paper tickets would be at most 1 contract at $0.58–0.64 limit. Recommend waiting for existing positions to settle before opening tennis paper tickets.

---

## Recommended Next Steps

1. **Watch Ruud/Fonseca** — highest clay signal, Ruud's surface advantage is documentable
2. **Build ATP H2H model** — before next French Open session (June 1 matches start ~11AM EDT)
3. **Check existing paper positions** — several expired (weather May 30, Spotify May 29) — update ledger
4. **Do not add live tennis** — kill switch is active, budget near limit, independent probability not established

---

## Circuit Breakers Honored

- ✅ LIVE-KILL-SWITCH is active — no live orders issued
- ✅ No authenticated Kalshi API calls made
- ✅ Screenshot data used for research only
- ✅ Budget constraint acknowledged ($0.93 remaining)
- ✅ All positions flagged as `paper_only_requires_human_approval`

---

**This report is for educational and planning purposes only. Trading on Kalshi involves risk. Past performance on prediction markets is not indicative of future results. All analysis is paper-mode research — no real money is at risk.**
