# GPU Training Orchestration Plan - Maximize Free Quotas

**Status:** Ready to Execute  
**Date:** 2026-06-23  
**Plan Duration:** Weekly rolling schedule

## Executive Summary

**Total Free GPU Hours Available:**
- Per week: **102 hours** (4+ providers)
- Per month: **~408 hours** (4.25 weeks)
- Annual capacity: **5,304 hours** of free GPU compute

**Objective:** Fully utilize free quotas to train Ouro v3 LoRA and execute full eval pipeline

---

## Provider Quota Analysis

| Provider | Quota/Week | GPU | Session Cap | Auto? | Status | Priority |
|----------|-----------|-----|------------|-------|--------|----------|
| **Kaggle** | 30 hrs | T4/P100 | 9h | ✓ YES | Active | 1 (Best) |
| **Lightning AI** | 22 hrs | T4/A10 | 6h | ✓ YES | Active | 2 |
| **AWS SageMaker** | 28 hrs | T4 | 4h | ⚠ Manual | Active | 3 |
| **Google Colab** | 22 hrs | T4 | 8h | ⚠ Manual | Active | 4 |
| **Paperspace** | 0 hrs | M4000 | 6h | ✗ Paid | Inactive | N/A |
| **TOTAL** | **102 hrs/week** | Mixed | - | - | - | - |

---

## GitHub Issues to Close

### Orchestration Issues (Directly Executable)

**#1063 - dispatchTrainingJob — Kaggle kernel push** ✅ READY
- Status: Code merged PR #1077
- Action: Trigger Kaggle dispatch immediately
- Expected: Kernel pushes successfully, training starts

**#1064 - pollJobStatus + rotateProvider** 🔄 IN PROGRESS
- Status: Partial implementation exists
- Action: Execute dispatch → poll → rotate flow
- Expected: Auto-rotate to Lightning AI after Kaggle quota exhausted

**#1065 - wire training dispatch into runWeeklyImprovement** 🎯 KEY
- Status: Ready to implement once dispatch working
- Action: Call dispatchTrainingJob from weekly loop
- Expected: Automated training every week

### Training Issues (Data Prep + Execution)

**#1061 - training: Ouro coder v3 — curated dataset** 📊 NEEDED
- Dataset: ~5K curated coding samples (apples-to-apples vs v2)
- Training: 600 steps @ 180 steps/hour = 3.3 hours/run
- Frequency: Run on Kaggle (30 hrs) + Lightning (22 hrs) = 52+ runs/week possible
- Expected: v3 improves pass@1 by 8-12% over v2

**#1060 - eval: firmer coding eval (eval_coding_ouro.py)** 📈 VALIDATION
- Eval dataset: 500+ Python coding tasks (HumanEval + curated)
- Frequency: Run after each major training checkpoint
- Time: ~30 min per eval run
- Expected: Measure v1, v2, v3 improvements side-by-side

**#1059 - eval: HumanEval pass@1** 🏆 FINAL GATE
- Benchmark: Standard LLM coding eval (HumanEval + pass@1/10)
- Frequency: Run once training complete
- Time: ~1 hour
- Expected: v3 reaches 45%+ pass@1 (vs 38% baseline)

---

## Weekly Training Schedule (Maximize 102 hrs)

### Week Pattern (Mon-Sun)

```
MON-TUE: Kaggle Phase (30 hours available)
  - 3x 9-hour training sessions
  - Model: Ouro v3 LoRA (600 steps each)
  - Dataset: Batch 1 (curated coding samples)
  
WED-THU: Lightning AI Phase (22 hours available)
  - 3x 6-hour sessions (safe limit with auto-stop)
  - Model: Ouro v3 LoRA continuation
  - Dataset: Batch 2 (additional curated samples)
  
FRI-SAT: Manual Providers Phase (28+22 hours = 50 hrs available)
  - AWS SageMaker: 7x 4-hour sessions (28 hrs)
    Strategy: Broad hyperparameter sweep
  - Google Colab: 2x 8-hour sessions (16 hrs remaining)
    Strategy: Fine-grained convergence tuning
  
SUN: Evaluation + Checkpoint
  - Run eval_coding_ouro.py on all 9+ training checkpoints
  - Select best checkpoint for next week
  - Upload to HuggingFace Hub
  - Archive CSF to data/csf/
```

### Training Parameters (Per Run)

```
Model: Ouro LoRA-QLoRA
Seq Length: 1536 tokens
Batch Size: Adaptive (per GPU VRAM)
  - T4 (16GB): 8
  - A10 (24GB): 12
  - P100 (16GB): 8
Learning Rate: 5e-4 (initial)
Steps per run: 600 (3.3 hours @ 180 steps/hour)
Checkpoint Repo: Mookman11/ouro-checkpoints (HuggingFace)
CSF Archive: data/csf/training-runs/ (local)
```

---

## Execution Roadmap

### Phase 1: Immediate (This Week) - Dispatch Validation
**Goal:** Prove all providers dispatch successfully

```yaml
Week 1:
  Mon 06-23:
    - Dispatch #1: Kaggle (issue #1063)
    - Expected: Kernel pushed, training starts
    - Verify: Check Kaggle kernel logs
  
  Tue 06-24:
    - Dispatch #2: Lightning AI (with our fixes)
    - Expected: Studio starts, training runs
    - Verify: Poll job status every 10 min
  
  Wed 06-25:
    - Dispatch #3: AWS SageMaker (manual notebook)
    - Expected: Generates manual_required record
    - Action: Operator opens notebook, clicks Run
  
  Thu 06-26:
    - Dispatch #4: Google Colab (manual notebook)
    - Expected: Generates manual_required record
    - Action: Operator opens notebook, clicks Run
  
  Fri 06-27:
    - Poll all 4 active training jobs
    - Collect checkpoints from HuggingFace
    - Run eval on first checkpoint batch
```

### Phase 2: Automated Weekly Loop (Week 2+)
**Goal:** runWeeklyImprovement automatically dispatches to all providers

```yaml
Each Monday:
  1. Check provider quotas (via PCSF)
  2. Dispatch to Kaggle (30 hrs available)
  3. Dispatch to Lightning (22 hrs available)
  4. Generate manual notebooks (SageMaker + Colab)
  5. Poll every 5 min during execution
  6. Auto-rotate provider when quota exhausted (issue #1064)

Each Friday:
  1. Collect all checkpoints from week
  2. Run eval_coding_ouro.py on each
  3. Select best checkpoint
  4. Log results to data/training-evals.jsonl
  5. Push best to HuggingFace as "ouro-v3-week-X"

Each Sunday:
  1. Run HumanEval pass@1 benchmark
  2. Compare v1 vs v2 vs v3 side-by-side
  3. Update convergence record (Σ₀ grounded)
  4. File issue if v3 improves <5% or regresses
```

---

## GitHub Issues Mapping

| Issue | Purpose | Status | Action |
|-------|---------|--------|--------|
| #1063 | Dispatch to Kaggle | ✅ MERGED (PR #1077) | Execute Now |
| #1064 | Poll + Rotate | 🔄 Ready | Execute Now |
| #1065 | Wire to weekly loop | 🎯 Blocked on #1063-64 | After Phase 1 |
| #1061 | Ouro v3 dataset | 📊 Dependency | Start this week |
| #1060 | Firmer eval | 📈 Dependent on training | Start this week |
| #1059 | HumanEval bench | 🏆 Final gate | Start next week |

---

## Risk Mitigation

### Quota Exhaustion
**Risk:** All providers hit quota limit simultaneously, training stops  
**Mitigation:** Stagger start times (Mon Kaggle, Wed Lightning, Thu SageMaker)  
**Fallback:** Cache checkpoints locally, resume from latest in new week

### Checkpoint Loss
**Risk:** HuggingFace down, checkpoint not uploaded  
**Mitigation:** Auto-pack to CSF, store locally under data/csf/  
**Fallback:** Resume from CSF archive if HF down >1 hour

### Diverged Training
**Risk:** Different providers produce different quality  
**Mitigation:** Same dataset, same LoRA script on all  
**Fallback:** Ensemble checkpoint selection (pick best eval score)

### Manual Provider Delays
**Risk:** Operator forgets to run SageMaker/Colab notebook  
**Mitigation:** Automated Slack/Discord notification with ready-to-copy notebook  
**Fallback:** Accept lower capacity (Kaggle + Lightning only = 52 hrs/week, still sufficient)

---

## Success Metrics

### Week 1: Dispatch Validation
- [ ] Kaggle dispatch returns 200 JSON (not error)
- [ ] Kernel appears at https://www.kaggle.com/code/micahshively/ouro-qlora
- [ ] Lightning dispatch script executes (returns JSON status)
- [ ] Poll endpoint detects "running" status
- [ ] SageMaker notebook auto-generated correctly
- [ ] Colab notebook auto-generated correctly

### Week 2+: Training Velocity
- [ ] ≥80% of 102 hrs/week actually used
- [ ] ≥9 training runs (600 steps each) per week
- [ ] ≥1 full eval_coding_ouro.py run per week
- [ ] 0 checkpoint losses (100% upload success)
- [ ] Training convergence visible in loss curves

### Final: v3 Quality Gate
- [ ] Ouro v3 pass@1 ≥ 42% (up from 38% baseline)
- [ ] Training data quality score ≥ 0.85/1.0
- [ ] Eval completeness ≥ 95% (no dropped tasks)
- [ ] Reproducibility: ±1.2% variance across 3 runs

---

## How to Start

### Step 1: Verify Credentials (Already Done ✅)
```bash
curl -s http://127.0.0.1:4177/api/gpu-training/test \
  -X POST -H "Content-Type: application/json" \
  -d '{"provider":"kaggle"}'
# Expected: "credOk": true
```

### Step 2: Dispatch to Kaggle (NOW)
```bash
curl -s http://127.0.0.1:4177/api/gpu-training/dispatch \
  -X POST -H "Content-Type: application/json" \
  -d '{"provider":"kaggle","steps":600}'
# Expected: "status": "queued", "jobId": "ouro-qlora"
```

### Step 3: Poll Status (Every 5 min)
```bash
curl -s http://127.0.0.1:4177/api/gpu-training/status | jq '.active'
# Expected: "status": "running"
```

### Step 4: Dispatch to Lightning (After Kaggle starts)
```bash
curl -s http://127.0.0.1:4177/api/gpu-training/dispatch \
  -X POST -H "Content-Type: application/json" \
  -d '{"provider":"lightning","steps":600}'
```

### Step 5: Generate Manual Notebooks (SageMaker + Colab)
```bash
curl -s http://127.0.0.1:4177/api/gpu-training/dispatch \
  -X POST -H "Content-Type: application/json" \
  -d '{"provider":"sagemaker","steps":600}'
# Returns: notebookTemplate (copy-paste into SageMaker notebook)

curl -s http://127.0.0.1:4177/api/gpu-training/dispatch \
  -X POST -H "Content-Type: application/json" \
  -d '{"provider":"colab","steps":600}'
# Returns: notebookTemplate (copy-paste into Colab notebook)
```

---

## Next Steps

1. **NOW:** Execute Step 1-5 above to start training
2. **In 30 min:** Check Kaggle kernel is running
3. **In 6 hrs:** Collect first checkpoint from HuggingFace
4. **In 24 hrs:** Run eval_coding_ouro.py on checkpoint
5. **In 2 weeks:** Close issues #1061, #1060, #1059 with results

---

**Plan Status:** ✅ READY TO EXECUTE  
**Owner:** Claude + You (co-authored)  
**Last Updated:** 2026-06-23T03:45:00Z

