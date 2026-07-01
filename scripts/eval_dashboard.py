#!/usr/bin/env python3
"""
Coding-eval dashboard (CAP-1, #1553) — surface the tracked pass-rate per
model/route from data/eval/leaderboard.jsonl in one command.

The *baseline* already exists: scripts/eval_coding.py / eval_humaneval_chat.py /
eval_swebench_chat.py each append a row to data/eval/leaderboard.jsonl (CI-gated
by .github/workflows/eval-leaderboard-gate.yml), and docs/BENCHMARKS.md is the
human registry. What was missing was the "small dashboard" from the CAP-1
proposed fix: a single command that renders those tracked rows as a pass-rate
table per model/route, so capability is legible at a glance instead of buried
in a JSONL log.

This is a Verify-stage tool: it only *reads* the append-only leaderboard and
renders it. It never fabricates a score — an empty leaderboard renders an empty
table, honestly.

    python scripts/eval_dashboard.py                 # print table + write DASHBOARD.md
    python scripts/eval_dashboard.py --no-write       # print only
    python scripts/eval_dashboard.py --benchmark humaneval
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEADERBOARD = ROOT / "data" / "eval" / "leaderboard.jsonl"
OUT_MD = ROOT / "data" / "eval" / "DASHBOARD.md"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def load_rows(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # skip malformed — never guess
    return rows


def _fmt_date(ts) -> str:
    try:
        return time.strftime("%Y-%m-%d", time.gmtime(int(float(ts))))
    except (ValueError, TypeError):
        return "?"


def _pct(v) -> str:
    try:
        return f"{float(v) * 100:.1f}%"
    except (ValueError, TypeError):
        return "—"


def route_of(row: dict) -> str:
    """The 'model/route' identity: explicit model/route, else engine + base_model."""
    if row.get("model"):
        return str(row["model"])
    if row.get("route"):
        return str(row["route"])
    engine = row.get("engine") or "?"
    base = row.get("base_model") or ""
    base = base.split("/")[-1] if base else ""
    return f"{engine}" + (f" · {base}" if base else "")


def latest_per_run(rows: list[dict]) -> dict[tuple, dict]:
    """Keep the most recent row per (benchmark, label); track run count."""
    best: dict[tuple, dict] = {}
    counts: dict[tuple, int] = {}
    for r in rows:
        key = (r.get("benchmark", "?"), r.get("label", "?"))
        counts[key] = counts.get(key, 0) + 1
        prev = best.get(key)
        if prev is None or float(r.get("ts", 0) or 0) >= float(prev.get("ts", 0) or 0):
            best[key] = r
    for key, r in best.items():
        r["_runs"] = counts[key]
    return best


def render(rows: list[dict], only: str | None = None) -> str:
    latest = latest_per_run(rows)
    entries = list(latest.values())
    if only:
        entries = [r for r in entries if r.get("benchmark") == only]

    lines: list[str] = []
    lines.append("# Coding-Eval Dashboard")
    lines.append("")
    lines.append(f"_Tracked pass-rate per model/route from "
                 f"`data/eval/leaderboard.jsonl` ({len(rows)} rows). "
                 f"Regenerate: `python scripts/eval_dashboard.py`._")
    lines.append("")

    if not entries:
        lines.append("_No leaderboard rows yet — run a harness "
                     "(`scripts/eval_coding.py --label <run> --model <model>`) to populate._")
        return "\n".join(lines) + "\n"

    benchmarks = sorted({r.get("benchmark", "?") for r in entries})
    for bench in benchmarks:
        group = [r for r in entries if r.get("benchmark", "?") == bench]
        group.sort(key=lambda r: (r.get("pass@1") is None, -(float(r.get("pass@1") or 0))))
        best = group[0]
        lines.append(f"## {bench}  ·  {len(group)} run(s)  ·  "
                     f"best pass@1 **{_pct(best.get('pass@1'))}** ({best.get('label')})")
        lines.append("")
        lines.append("| model / route | run label | pass@1 | accuracy | n | subset | last run | runs |")
        lines.append("|---|---|---:|---:|---:|:--:|---|---:|")
        for r in group:
            lines.append(
                f"| {route_of(r)} | {r.get('label','?')} | {_pct(r.get('pass@1'))} | "
                f"{_pct(r.get('accuracy'))} | {r.get('n','?')} | "
                f"{'yes' if r.get('subset') else 'full'} | {_fmt_date(r.get('ts'))} | {r.get('_runs',1)} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Render the coding-eval leaderboard as a pass-rate dashboard (#1553).")
    ap.add_argument("--benchmark", default=None, help="Filter to one benchmark (e.g. humaneval).")
    ap.add_argument("--no-write", action="store_true", help="Print only; do not write DASHBOARD.md.")
    a = ap.parse_args()

    rows = load_rows(LEADERBOARD)
    md = render(rows, only=a.benchmark)
    print(md)
    if not a.no_write:
        OUT_MD.write_text(md, encoding="utf-8")
        print(f"[wrote] {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
