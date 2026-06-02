# Permanent Progress Tracking System - 99.9999% Uptime Architecture

**Purpose:** Track all COMET LEAPER progress without Claude token dependency

**Uptime Target:** 99.9999% (5 minutes downtime/year max)

**Token Usage:** Minimal Claude; primary load on open models and local compute

---

## Architecture Overview

### Layer 1: Local Source of Truth
- **PROGRESS.jsonl** (append-only event log)
- **MILESTONES.md** (weekly/monthly snapshots)
- **CONFIDENCE-LEDGER.csv** (confidence updates)
- **BURN-TRACKING.csv** (weekly financial)
- **EXPERIMENTS-LOG.jsonl** (daily experiment results)

### Layer 2: Automated Local Processing
- **Windows Task Scheduler** (daily 6am run)
- **PowerShell scripts** (parse logs, generate summaries)
- **Ollama running locally** (analysis without API calls)
- **Python summarization** (batch process logs)

### Layer 3: API Fallback (Open Models)
- **Primary:** OpenRouter (multiple models, redundant)
- **Secondary:** Together.ai (open models)
- **Tertiary:** Local Ollama (runs offline)
- **Claude:** Only for complex synthesis (once/week Friday)

### Layer 4: Persistent Storage
- **GitHub repository** (remote backup, version history)
- **OneDrive sync** (local backup)
- **.jsonl format** (newline-delimited JSON, append-only, git-friendly)

---

## Core Files

### PROGRESS.jsonl (Daily Updates)
```json
{"timestamp":"2026-05-26T09:00:00","event":"experiment_run","assumption":"families_want_weekly","result":"4/5_confirm","confidence_change":"60%→85%"}
{"timestamp":"2026-05-26T10:30:00","event":"revenue_recorded","channel":"institutional","amount":500,"cumulative":500}
{"timestamp":"2026-05-26T11:00:00","event":"milestone_reached","stage":"month1_validation","gate":"3_confirmed_institutions"}
{"timestamp":"2026-05-26T17:00:00","event":"burn_recorded","category":"infrastructure","amount":52}
```

### MILESTONES.md (Weekly Snapshots)
```markdown
# Week 1 Snapshot (May 26, 2026)

**Status:** Validation Phase (Month 1)

**Confidence Changes:**
- Families want weekly: 20% → 85% ✓
- Institutional partners value: 40% → 75% ⚠
- Care coordination feasible: 60% → 80% ✓

**Revenue:** $0 (validation only)

**Burn:** $462 actual vs $455 budgeted (+$7 variance)

**Experiments Run:** 3 completed, 2 pending

**Next Week:** Finalize 2 institutional pilots, run messaging test
```

### CONFIDENCE-LEDGER.csv
```csv
date,assumption,evidence_class,score,source,confidence_trend
2026-05-26,families_want_weekly,source_verified,85%,5_customer_interviews,↑25
2026-05-26,institutional_partners_value,source_verified,75%,2_interested_partners,↑15
2026-05-26,care_coordination_feasible,repo_verified,80%,MVP_shipped_test,↑20
```

### BURN-TRACKING.csv
```csv
week_ending,fixed_costs,variable_costs,personal_stipend,total_burn,runway_weeks
2026-05-26,107,155,200,462,48
```

### EXPERIMENTS-LOG.jsonl
```json
{"date":"2026-05-26","experiment":"customer_interviews_x5","assumption":"weekly_preference","success_criteria":"4/5_confirm","result":"pass","confidence":"60%→85%","budget_spent":100,"insights":"strong_signal"}
```

---

## Automation Workflow

### Daily (6am Windows Task Scheduler)

**Task 1: Update PROGRESS.jsonl**
```powershell
# Append yesterday's events to PROGRESS.jsonl
# Events come from: manual logging, automated sensors (burn tracking), experiment logs
# No external API call - local file write only
```

**Task 2: Run Ollama Analysis (Local, Offline)**
```bash
ollama run mistral "Analyze this week's experiments: [input] Provide confidence changes and anomalies."
```

**Output:** Local markdown file with insights (no token cost)

### Weekly (Friday 3pm - Local Processing)

**Task 1: Generate Weekly Synthesis**
```powershell
# Read PROGRESS.jsonl, EXPERIMENTS-LOG.jsonl, BURN-TRACKING.csv
# Parse into structured summary
# Output to MILESTONES.md
```

**Task 2: Confidence Ledger Update**
```python
# Read PROGRESS.jsonl events
# Extract confidence changes
# Update CONFIDENCE-LEDGER.csv
# Push to GitHub for backup
```

**Task 3: Optional Claude Synthesis (Friday 4pm only)**
```
Claude call: "Synthesize this week [MILESTONES.md snapshot]. Identify patterns, risks, opportunities."
Response: ~1000 tokens, 1x per week = 4,000 tokens/month
```

### Monthly (First Friday - Full Synthesis)

**Input:** All weekly snapshots, confidence ledger, experiment results

**Process:**
1. OpenRouter (lightweight): Pattern identification, risk assessment
2. Ollama (local): Trend analysis
3. Claude (minimal): Strategic implications

**Output:** Monthly strategy memo

---

## Token Budget & Cost Control

### Monthly Token Allocation

| Task | Frequency | Model | Tokens/call | Monthly Total | Cost |
|------|-----------|-------|------------|---------------|------|
| Daily Ollama analysis | 30x | local | 0 | 0 | $0 |
| Weekly synthesis | 4x | OpenRouter | 1,000 | 4,000 | $0.04 |
| Experiment logging | 15x | local | 0 | 0 | $0 |
| Monthly strategy | 1x | Claude | 3,000 | 3,000 | $0.03 |
| **TOTAL** | | | | 7,000 | ~$0.07 |

**Comparison:** 7,000 tokens/month = 84,000 tokens/year = $0.84

Claude's advantage: Used only for high-value synthesis decisions, not for routine progress tracking.

---

## Fallback System (99.9999% Uptime)

### Primary: Local Files + Ollama
- Status: Always available (offline)
- Latency: <1 second
- Cost: $0 (already paid)
- Failure mode: Can't happen (local only)

### Secondary: OpenRouter (10 models, redundant)
- Status: If Ollama slow
- Latency: 2-5 seconds
- Cost: Minimal ($0.01/10M tokens)
- Failure mode: Switch to next model

### Tertiary: GitHub Actions (backup CI/CD)
- Status: If local Windows scheduler fails
- Latency: 2-3 minutes
- Cost: Free (public repo)
- Failure mode: Manual trigger

### Quaternary: Claude (Manual Weekly Review)
- Status: If all automation fails
- Latency: On demand
- Cost: ~$0.03/week
- Failure mode: Token rate limit (won't happen at this volume)

---

## Implementation Checklist (Week 1)

- [ ] Create PROGRESS.jsonl in repo
- [ ] Create MILESTONES.md template
- [ ] Create CONFIDENCE-LEDGER.csv
- [ ] Create BURN-TRACKING.csv
- [ ] Create EXPERIMENTS-LOG.jsonl
- [ ] Set up Windows Task Scheduler (6am daily)
- [ ] Install Ollama locally (mistral model)
- [ ] Create PowerShell summary script
- [ ] Create Python JSONL parser
- [ ] Set up GitHub Actions for backup
- [ ] Configure OpenRouter API key
- [ ] Test full automation cycle (dry run)
- [ ] Document manual logging format
- [ ] Set up Friday 4pm weekly synthesis meeting
- [ ] Document Claude-only weekly synthesis prompt

---

## Data Format Standards

### Timestamps
Format: ISO 8601 (2026-05-26T09:00:00)

### Confidence Scores
Format: XX% (e.g., 85%)

### Money
Format: USD whole dollars (e.g., 500)

### Status Values
- ✓ = Complete/Confirmed
- ⚠ = In Progress/Uncertain
- ✗ = Failed/Not Happening
- ○ = Pending/Unknown

---

## Weekly Manual Input (Founder Only)

Every Friday 3pm:

1. **Experiment outcomes:** 5 minutes
   - Input: Experiment names, results, confidence changes
   - Format: Add to EXPERIMENTS-LOG.jsonl

2. **Financial data:** 5 minutes
   - Input: Weekly burn actual vs budget
   - Format: Add to BURN-TRACKING.csv

3. **Revenue events:** 2 minutes
   - Input: Any revenue recorded
   - Format: Add to PROGRESS.jsonl

4. **Blockers:** 3 minutes
   - Input: Top 2-3 obstacles blocking progress
   - Format: Add to MILESTONES.md

**Total founder time:** 15 minutes/week (vs 90 minutes current synthesis)

**System time:** Everything else automated

---

## Success Metrics

✓ **99.9999% uptime:** Measured by PROGRESS.jsonl append success rate

✓ **Token budget:** <7,000 tokens/month (<$0.10)

✓ **Automation:** 80% of tasks automated (founder only logs outcomes)

✓ **Response time:** Synthesis generated within 1 hour of Friday 3pm

✓ **Data integrity:** All events logged, no data loss, GitHub backup always current

✓ **Accessibility:** Any team member can read PROGRESS.jsonl and understand current state

---

**Implementation:** Start Week 1 (May 27, 2026)

**Founder setup time:** 3-4 hours initial setup, 15 min/week ongoing

**System operational:** By Friday first synthesis (May 31, 2026)

**Token savings:** 99.3% reduction vs Claude-dependent system (7,000 vs 1M+ tokens/month)
