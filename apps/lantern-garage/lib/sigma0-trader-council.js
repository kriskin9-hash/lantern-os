"use strict";
// sigma0-trader-council.js — Converge stage for the trader's Σ₀ EV.
//
// The Python engine emits a ConvergenceRecord per executed ENTER and, on close,
// a Brier-graded outcome (data/convergence/trader-outcomes.jsonl). This module is
// the council's read side: it runs the CANONICAL calibration grader over those
// outcomes and adds a per-signal realized-edge table — which evidence (zone,
// structure, news, …) actually predicted wins — the input to re-weighting the EV.
// Pure aggregation + one file read; safe to call on every status poll.

const fs = require("fs");
const path = require("path");
const { calibrationSummary } = require("./convergence-outcome-grader");

const OUTCOMES_PATH = path.resolve(
  __dirname, "..", "..", "..", "data", "convergence", "trader-outcomes.jsonl"
);

function _read(file) {
  try {
    return fs.readFileSync(file || OUTCOMES_PATH, "utf8")
      .split("\n").map((l) => l.trim()).filter(Boolean)
      .map((l) => { try { return JSON.parse(l); } catch { return null; } })
      .filter(Boolean);
  } catch {
    return [];
  }
}

// Per-signal realized edge: when a signal fired "strong" (>0.55) vs "weak", what
// was the win rate? lift = strong_winrate − weak_winrate. A positive lift means
// the signal genuinely predicted wins and deserves (more) weight; ~0 or negative
// means it's noise. This is the council's re-weighting evidence. Pure.
function perSignalEdge(rows) {
  const acc = {};
  for (const r of rows || []) {
    const sig = r && r.signals;
    if (!sig || typeof sig !== "object") continue;
    const win = r.outcome ? 1 : (r.passed ? 1 : 0);
    for (const k of Object.keys(sig)) {
      const a = (acc[k] = acc[k] || { sN: 0, sW: 0, wN: 0, wW: 0 });
      if (Number(sig[k]) > 0.55) { a.sN++; a.sW += win; }
      else { a.wN++; a.wW += win; }
    }
  }
  const out = {};
  for (const k of Object.keys(acc)) {
    const a = acc[k];
    const sw = a.sN ? a.sW / a.sN : null;
    const ww = a.wN ? a.wW / a.wN : null;
    const r2 = (x) => (x == null ? null : Math.round(x * 100) / 100);
    out[k] = {
      strong_n: a.sN, strong_winrate: r2(sw),
      weak_n: a.wN, weak_winrate: r2(ww),
      lift: (sw != null && ww != null) ? r2(sw - ww) : null,
    };
  }
  return out;
}

// Full council snapshot for /api/trading/sigma0/calibration.
function council(file) {
  const rows = _read(file);
  const wins = rows.filter((r) => r.outcome || r.passed).length;
  return {
    graded: rows.length,
    win_rate: rows.length ? Math.round((wins / rows.length) * 100) / 100 : null,
    avg_pnl_pct: rows.length
      ? Math.round((rows.reduce((s, r) => s + (Number(r.pnl_pct) || 0), 0) / rows.length) * 100) / 100
      : null,
    calibration: calibrationSummary(rows), // canonical Brier/ECE/skill grader
    per_signal_edge: perSignalEdge(rows),
    maturity: rows.length >= 20 ? "ready"
      : rows.length > 0 ? "warming — needs ≥20 closed trades before re-weighting is trustworthy"
      : "no graded trades yet — the loop populates as positions close",
  };
}

module.exports = { council, perSignalEdge, OUTCOMES_PATH };
