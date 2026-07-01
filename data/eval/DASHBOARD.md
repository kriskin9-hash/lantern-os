# Coding-Eval Dashboard

_Tracked pass-rate per model/route from `data/eval/leaderboard.jsonl` (39 rows). Regenerate: `python scripts/eval_dashboard.py`._

## ?  ·  1 run(s)  ·  best pass@1 **—** (goldenv1-coder-v2)

| model / route | run label | pass@1 | accuracy | n | subset | last run | runs |
|---|---|---:|---:|---:|:--:|---|---:|
| lantern-sigma0-coder-v2:latest | goldenv1-coder-v2 | — | 33.8% | 65 | full | 2026-06-19 | 1 |

## humaneval  ·  36 run(s)  ·  best pass@1 **75.0%** (ouro-coding-v3-he20)

| model / route | run label | pass@1 | accuracy | n | subset | last run | runs |
|---|---|---:|---:|---:|:--:|---|---:|
| ouro-fast-cached · Qwen2.5-Coder-3B-Instruct | ouro-coding-v3-he20 | 75.0% | — | 20 | yes | 2026-06-20 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-v1-he20 | 65.0% | 65.0% | 20 | yes | 2026-06-23 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-checkpoint-150 | 50.0% | 50.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-checkpoint-600 | 50.0% | 50.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-confirm-checkpoint-150 | 50.0% | 50.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-confirm-checkpoint-600 | 50.0% | 50.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-full-ck600 | 42.7% | 42.7% | 164 | full | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-checkpoint-300 | 40.0% | 40.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-checkpoint-450 | 40.0% | 40.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-checkpoint-750 | 40.0% | 40.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-checkpoint-900 | 40.0% | 40.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-fixed-harness | 35.0% | 35.0% | 20 | yes | 2026-06-25 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-peak-checkpoint-1000 | 35.0% | 35.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-lantern-pr-only | 30.0% | 30.0% | 20 | yes | 2026-06-25 | 2 |
| ouro-fast-cached · Ouro-1.4B | ouro-oc-checkpoint-1050 | 30.0% | 30.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-oc-checkpoint-1650 | 25.0% | 25.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-he10 | 10.0% | — | 10 | yes | 2026-06-19 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-candidate | 10.0% | 10.0% | 20 | yes | 2026-06-25 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-lantern-10h | 10.0% | 10.0% | 20 | yes | 2026-06-25 | 2 |
| ouro-fast-cached · Ouro-1.4B | ouro-oc-final | 10.0% | 10.0% | 20 | yes | 2026-06-26 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-baseline-he20 | 5.0% | — | 20 | yes | 2026-06-20 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-base-he20 | 5.0% | 5.0% | 20 | yes | 2026-06-25 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-base-depth1 | 5.0% | 5.0% | 20 | yes | 2026-06-27 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-ci-checkpoint-900-heldout | 5.0% | 5.0% | 40 | yes | 2026-06-27 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-ci-checkpoint-1350-heldout | 5.0% | 5.0% | 40 | yes | 2026-06-27 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-ci-checkpoint-2500-heldout | 2.5% | 2.5% | 40 | yes | 2026-06-27 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-smoke | 0.0% | — | 1 | yes | 2026-06-19 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-smoke3 | 0.0% | — | 3 | yes | 2026-06-19 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-smoke5 | 0.0% | — | 5 | yes | 2026-06-19 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-candidate-smoke | 0.0% | 0.0% | 3 | yes | 2026-06-25 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-candidate-smoke2 | 0.0% | 0.0% | 5 | yes | 2026-06-25 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-v2-he20 | 0.0% | 0.0% | 20 | yes | 2026-06-23 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-base-depth2 | 0.0% | 0.0% | 20 | yes | 2026-06-27 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-base-depth3 | 0.0% | 0.0% | 20 | yes | 2026-06-27 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-base-depth4 | 0.0% | 0.0% | 20 | yes | 2026-06-27 | 1 |
| ouro-fast-cached · Ouro-1.4B | ouro-ci-checkpoint-1950-heldout | 0.0% | 0.0% | 40 | yes | 2026-06-27 | 1 |

