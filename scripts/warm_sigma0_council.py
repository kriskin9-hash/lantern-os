"""
warm_sigma0_council.py — backfill the Σ₀ trader council with REAL closed-trade
history so it has graded outcomes to calibrate on and a per-signal realized-edge
table to re-weight from (instead of sitting "warming — needs ≥20 closed trades").

External-Reality Rule: every warm-up row is a REAL closed trade with a realized
outcome. Nothing synthetic is injected. Two grounded sources:

  A. lanternOS  lessons.db  trade_history  — joined to data/convergence/records.jsonl
     by ticker + nearest timestamp for the full signal vector (the re-weighting
     evidence) and the Σ₀ p_win as the graded confidence. Outcomes are RECOMPUTED
     from the actual Alpaca fill prices (entry/exit), because the stored `pnl_pct`
     column is corrupted (sign-flipped on the TP-zone / EOD rows).
  B. Independant AI Trader  trading.log  — `EOD closed TICKER: X%` lines, a
     ~7-week (2026-05-11 → 06-30) realized-pnl stream from a *separate* system.
     No signal vector (different pipeline) and no recorded conviction, so these
     carry confidence=0.5 (honest no-information prior): they pad win-rate/volume
     but do not inform per-signal edge or claim calibration credit.

Every appended row carries `source` ("warmup-lanternos" | "warmup-indep") and a
deterministic `record_id`, so the warm-up is fully idempotent and removable:

    grep -v '"source": "warmup' data/convergence/trader-outcomes.jsonl   # undo

Run:  python scripts/warm_sigma0_council.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTCOMES = REPO / "data" / "convergence" / "trader-outcomes.jsonl"
RECORDS = REPO / "data" / "convergence" / "records.jsonl"
LESSONS_DBS = [REPO / "lessons.db", REPO / "src" / "trading_agents" / "lessons.db"]
INDEP_LOG = Path(r"C:\Independant AI Trader\trading.log")

JOIN_WINDOW_S = 300  # a trade row joins the convergence record within ±5 min


def _parse_ts(s: str):
    try:
        return datetime.fromisoformat(str(s).replace("Z", ""))
    except Exception:
        return None


def _normalize_signals(sig: dict) -> dict | None:
    """Map the legacy merged `llm` signal onto the split council members
    (grok = the old llm conviction; claude neutral) so the per-signal edge table
    is consistent with the live schema."""
    if not isinstance(sig, dict) or not sig:
        return None
    out = dict(sig)
    if "llm" in out and "grok" not in out:
        out["grok"] = out.pop("llm")
        out.setdefault("claude", 0.5)
    return out


def load_convergence_records() -> dict[str, list]:
    """{ticker: [(ts, p_win, signals), ...]} from the shared convergence store."""
    by_ticker: dict[str, list] = {}
    if not RECORDS.exists():
        return by_ticker
    for line in RECORDS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "cr-trade" not in line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        res = r.get("result") or {}
        tkr = res.get("ticker")
        ts = _parse_ts(r.get("timestamp"))
        if not tkr or ts is None:
            continue
        by_ticker.setdefault(tkr, []).append(
            (ts, float(r.get("confidence") or 0.5), _normalize_signals(res.get("signals")))
        )
    return by_ticker


def match_record(records: dict, ticker: str, ts: datetime):
    """Nearest convergence record for this ticker within the join window."""
    best, best_dt = None, JOIN_WINDOW_S + 1
    for rts, pwin, sig in records.get(ticker, []):
        dt = abs((rts - ts).total_seconds())
        if dt < best_dt:
            best, best_dt = (pwin, sig), dt
    return best if best_dt <= JOIN_WINDOW_S else None


def from_lessons_db(records: dict) -> list[dict]:
    rows_out, seen = [], set()
    for db in LESSONS_DBS:
        if not db.exists():
            continue
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        except Exception:
            continue
        try:
            cur = con.execute(
                "select ts,symbol,action,entry_price,exit_price,confidence,status "
                "from trade_history"
            )
        except Exception:
            con.close()
            continue
        for ts, sym, action, entry, ex, conf, status in cur:
            # Real-fill grounding: drop anything without a valid round-trip.
            if status != "closed" or entry in (None, 0) or ex in (None, 0):
                continue
            # Recompute pnl from the ACTUAL fills (stored pnl_pct is unreliable).
            sign = 1.0 if str(action).upper() == "BUY" else -1.0
            pnl_pct = round(sign * (float(ex) - float(entry)) / float(entry) * 100.0, 4)
            outcome = 1 if pnl_pct > 0 else 0
            tsp = _parse_ts(ts)
            key = (sym, ts)
            if key in seen:
                continue
            seen.add(key)
            m = match_record(records, sym, tsp) if tsp else None
            if m:
                confidence, signals = m[0], m[1]
            else:
                confidence = max(0.05, min(0.95, float(conf or 50) / 100.0))
                signals = None
            rid = f"warmup-lz-{sym}-{re.sub('[^0-9]', '', str(ts))[:20]}"
            rows_out.append({
                "record_id": rid, "ticker": sym,
                "confidence": round(float(confidence), 4),
                "passed": bool(outcome), "outcome": outcome,
                "brier_score": round((float(confidence) - outcome) ** 2, 4),
                "pnl_pct": pnl_pct, "signals": signals,
                "source": "warmup-lanternos",
                "conviction_recorded": True,  # real agent/Σ₀ conviction
                "joined_signals": signals is not None,
                "graded_at": tsp.isoformat() if tsp else None,
            })
        con.close()
    return rows_out


def from_indep_log() -> list[dict]:
    if not INDEP_LOG.exists():
        return []
    # Read via a temp copy so we never lock the live trader's log.
    tmp = Path(tempfile.gettempdir()) / "indep_trading.log"
    try:
        shutil.copy2(INDEP_LOG, tmp)
    except Exception:
        tmp = INDEP_LOG
    text = tmp.read_text(encoding="utf-8", errors="replace")
    pat = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})[^\n]*?EOD closed ([A-Z]+): (-?[0-9.]+)%",
                     re.MULTILINE)
    rows_out = []
    for i, (ts, sym, pct) in enumerate(pat.findall(text)):
        pnl_pct = round(float(pct), 4)
        outcome = 1 if pnl_pct > 0 else 0
        rows_out.append({
            "record_id": f"warmup-ind-{sym}-{i}-{re.sub('[^0-9]', '', ts)}",
            "ticker": sym,
            "confidence": 0.5,   # conviction not recorded by that system — no-info prior
            "passed": bool(outcome), "outcome": outcome,
            "brier_score": round((0.5 - outcome) ** 2, 4),
            "pnl_pct": pnl_pct, "signals": None,
            "source": "warmup-indep",
            "conviction_recorded": False,  # other system never logged its conviction → no-info 0.5 prior
            "joined_signals": False,
            "graded_at": ts.replace(" ", "T"),
        })
    return rows_out


def main() -> int:
    existing_ids = set()
    if OUTCOMES.exists():
        for line in OUTCOMES.read_text(encoding="utf-8").splitlines():
            try:
                existing_ids.add(json.loads(line).get("record_id"))
            except Exception:
                pass

    records = load_convergence_records()
    rows = from_lessons_db(records) + from_indep_log()
    new = [r for r in rows if r["record_id"] not in existing_ids]

    OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTCOMES, "a", encoding="utf-8") as fh:
        for r in new:
            fh.write(json.dumps(r) + "\n")

    joined = sum(1 for r in new if r["joined_signals"])
    ln = sum(1 for r in new if r["source"] == "warmup-lanternos")
    ind = sum(1 for r in new if r["source"] == "warmup-indep")
    wins = sum(r["outcome"] for r in new)
    print(f"appended {len(new)} warm-up rows ({ln} lanternOS / {ind} indep); "
          f"{joined} carry a joined signal vector; {wins}/{len(new)} wins")
    print(f"  -> {OUTCOMES.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
