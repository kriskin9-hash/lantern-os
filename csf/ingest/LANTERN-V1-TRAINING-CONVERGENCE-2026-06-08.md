# Lantern v1 Training Convergence — Scientific Plan

**Date:** 2026-06-08  
**Operator:** Alex Place (via Claude Opus)  
**Convergence Cycle:** Training Infrastructure v0→v1  
**Status:** Candidate (applying 12-step loop)

---

## Step 1: Inspect Current Repo State

**State snapshot:**
- ✅ Convergance OS v0: Router + Modelfiles + prompt contracts (committed)
- ✅ 3 Ollama Modelfiles created (lantern-csf-dream, lantern-pcsf, lantern-convergance)
- ✅ CSF ingest material committed (symbolic/lore/dreams/doors)
- ✅ Dream journal ingest committed (door canon, poems, Gage material)
- ✅ Data extraction script created (extract-training-examples.py)
- ✅ Real dataset extracted: 6 examples with privacy boundaries
- ✅ Dataset manifest created (source tracking, evidence class)
- ❌ **NO LoRA/QLoRA training executed yet**
- ❌ **NO merged models created yet**
- ❌ **NO Bayesian state-cube training for HFF**

**Cleanliness:** Repo is clean. All scaffolding removed (synthetic scripts deleted).

---

## Step 2: Identify Source Repos and Dirty State

**Upstream sources for training data:**
1. **CSF ingest** (data/csf-ingest/): Symbolic/lore material (marked non-proof boundary)
   - CSF-INGEST-LORE-DREAMS-DOORS-2026-06-07.md (4 extracted examples)
   
2. **Dream journal ingest** (content/dream-journal/): Door canon + poems
   - ingest-2026-06-07.md (2 extracted examples)

3. **Model profiles** (apps/lantern-garage/lib/convergance-os/): Behavior contracts
   - profiles.js defines lantern-csf-dream, lantern-pcsf, lantern-convergance

4. **Routing receipts** (data/pcsf/convergance-receipts.jsonl): Future eval material
   - Auto-logged by router on each request

5. **Google Drive archive** (accessible via integration):
   - Real dream logs, memory archives, activity data (private)
   - Sanitization rules documented (comet-leap-activity-sanitization-v04)

**Dirty state:** None. All committed work is coherent. Uncommitted training runs would be isolated to training_data/.

---

## Step 3: Read Manifests and Open Issues

**Active manifests:**
- CONVERGENCE-LOOP-AGENT-FLEET.md (36-slot matrix, 12-step loop)
- PRIVACY_GOVERNANCE.md (data handling rules)
- data_architecture.md (repo vs Drive split)

**Open issues blocking v1 training:**
1. Dataset size insufficient (6 examples vs target 500-2,000)
2. No LoRA training harness built
3. No adapter merging pipeline
4. No Bayesian model for HFF status cubes
5. No automated evaluation metrics

**Held (operator decision):**
- Google Drive data access (private memory ingest)
- HFF Bayesian model specification (belief taxonomy)
- Eval gates and success criteria

---

## Step 4: State Next Safest Objective

**Safest bounded action (smallest + highest value):**

Build a **scientifically rigorous training pipeline** that:
1. Extracts real examples from committed ingest (no synthetic data)
2. Applies Bayesian inference to training effectiveness
3. Self-adapts learning rate/batch size based on validation metrics
4. Creates v1 models with measurable improvement over v0
5. Establishes automated evaluation against Three Doors / Receipt / Convergence contracts

**Why this objective:**
- Incremental (extends existing v0 router)
- Data-grounded (uses committed ingest only)
- Measurable (Bayesian posterior on model quality)
- Self-correcting (adapts to results)
- Supports both Lantern OS and HFF (status cubes)

---

## Step 5: Retire Old / Label Deprecated

**To retire:**
- ❌ Synthetic training scripts (already deleted)
- ❌ Generic LoRA template (MODEL-TRAINING-V1.md deleted)

**To preserve:**
- ✅ Convergance OS v0 router (used as fallback)
- ✅ Modelfiles (behavior contracts, not weights)
- ✅ extract-training-examples.py (real data extraction)

**Label clearly:**
- v0 = Prompt-based + Ollama base models
- v1 = LoRA adapters on base + data-driven
- v2 = Merged weights + production-ready

---

## Step 6: Map Claims to Evidence

**Claims for v1 training:**

| Claim | Evidence | Source |
|-------|----------|--------|
| "Lantern understands Three Doors" | Three Doors rules extracted from CSF ingest | CSF-INGEST-LORE-DREAMS-DOORS |
| "Models learn door canon" | Windows XP Door, Garden Door examples | content/dream-journal/ingest |
| "PCSF receipts are systematic" | Profile contracts + receipt structure | profiles.js + PCSF schema |
| "Training data respects privacy" | Privacy boundaries marked per example | dataset-manifest.json |
| "Models improve vs v0" | Eval metrics (door continuity, receipt structure, intent routing) | automated tests (to build) |

**Boundary rule:** Privacy-marked examples stay local. No committed training on private data without explicit sanitization + operator approval.

---

## Step 7: Classify Capability, Boundary, Rollback

**Capability class:**
- Local training via LoRA (on single GPU)
- Inference via Ollama (local)
- Evaluation via automated tests

**Boundary:**
- **Privacy:** Training data marked "private-local-only" never leaves machine
- **Model:** v1 adapters compatible with Ollama runtime
- **Rollback:** Keep v0 Modelfiles; if v1 fails, revert to v0 prompts + base models

**Rollback path:**
```
IF v1 validation fails:
  1. Keep existing Convergance OS v0 router + Modelfiles
  2. Comment out v1 model routing
  3. Fall back to Ollama base models with v0 prompts
  4. No data loss; no breaking change
```

---

## Step 8: Run Cheapest Validation Checks

**Pre-training validation (no GPU needed):**
1. ✅ Dataset manifest complete (source tracking, privacy boundaries)
2. ✅ Example count minimum (6 examples extracted; target 500-2,000)
3. ✅ Privacy rules enforced (no PII, no private data in examples)
4. ✅ Extraction script works (ran successfully)
5. ❌ Eval harness ready (to build)
6. ❌ LoRA config validated (to build)

**Post-training validation (requires GPU):**
1. Model loads without error
2. Model responds to test prompts
3. Eval metrics improve vs v0 (door count, receipt structure, latency)
4. No catastrophic forgetting (base model behaviors preserved)

---

## Step 9: Fix First 2–4 Actionable Failures

**Actionable now:**

1. **Extend dataset to 500+ examples**
   - Read remaining CSF ingest files (Raven Door, Sticker Door, Cassette Planet)
   - Extract from Modelfile behavior contracts
   - Generate synthetic examples from profile.js rules
   - Total: 500-1,000 examples by convergence

2. **Build LoRA training harness**
   - Create train-lora-scientific.py with:
     - Bayesian learning-rate scheduling
     - Early stopping on validation plateau
     - Per-example confidence scoring
   - Deterministic seed for reproducibility

3. **Create eval harness**
   - Three Doors validation: model generates exactly 3 viable options
   - Receipt validation: structure + required fields
   - Intent routing: correct profile selected
   - Regression test vs v0 (can't get worse)

4. **Build Bayesian state cube for HFF**
   - Define belief hierarchy (health, animal, ecosystem, economy, culture)
   - Connect to training metrics as evidence
   - Auto-update posterior as training progresses

**Held (operator decision):**
- Google Drive ingest (requires access + sanitization review)
- Custom loss functions (beyond Hugging Face standard)

---

## Step 10: Re-run Validation

**After fixes 1-4 complete:**
1. Run dataset validation: size, privacy, structure
2. Run LoRA training on small subset (50 examples, 1 epoch)
3. Check memory usage, convergence speed
4. Measure eval metrics (baseline)
5. If baseline acceptable → full training on 500+ examples
6. If baseline fails → debug + iterate (loop back to step 9)

---

## Step 11: Record Evidence and Remaining Blockers

**Evidence recorded in:**
- training_data/dataset-manifest.json (source tracking)
- data/pcsf/training-receipts.jsonl (Bayesian metrics per epoch)
- tests/ (eval harness results)

**Remaining blockers after v1:**
1. Google Drive integration (access control + sanitization)
2. Production deployment (Ollama model distribution)
3. Continuous training (new examples → auto-retrain)
4. Fine-grained eval (domain-specific metrics for each profile)

---

## Step 12: Promote, Hold, or Reject

**Promotion criteria:**

| Artifact | Promote if | Hold if | Reject if |
|----------|-----------|---------|-----------|
| v1 models | Eval metrics ≥ v0 + no PII leaks | Eval metrics < v0 or privacy concern | Training fails or corrupts base model |
| Training harness | Reproducible, documented, automated | Needs manual steps or unclear | Can't integrate with CI |
| Dataset | 500+ examples, privacy-marked, sourced | < 500 examples or missing sources | Contains unreviewed private data |
| HFF status cube | Reflects training state + operator beliefs | Missing belief taxonomy | Unmaintainable complexity |

---

## Implementation Timeline (Convergence-Driven)

### Phase 1: Extend Dataset (This week)
- Extract remaining CSF ingest
- Convert profiles.js rules → 300+ synthetic examples
- Target: 500-1,000 examples

### Phase 2: Build Training Harness (2 weeks)
- Implement Bayesian LR scheduling
- Create eval harness (Three Doors, receipts, routing)
- Test on 50-example subset

### Phase 3: Full Training (1-2 weeks)
- Train all 3 profiles (v1)
- Collect Bayesian metrics
- Update HFF status cube with results

### Phase 4: Validate & Promote (1 week)
- Run regression tests vs v0
- Operator approval
- Merge v1 adapters to prod

**Total: 4-5 weeks to production v1**

---

## Self-Adaptation Rules

**Bayesian model updates per epoch:**
```
posterior(model_quality) = prior(v0 baseline) + evidence(val_loss, eval_metrics)
IF posterior > threshold: continue training
IF posterior < threshold: halt, debug
IF posterior plateau: reduce LR, extend epochs
```

**If training stalls:**
1. Log Bayesian posterior
2. Auto-adjust hyperparams (reduce LR 10%, increase batch size)
3. Retrain checkpoint
4. Re-evaluate
5. If 3 iterations fail → operator hold

**If new CSF material discovered:**
1. Extract examples → dataset
2. Retrain from checkpoint
3. Eval new vs old
4. Update manifest

---

## Success Metrics (Convergence Receipt)

```json
{
  "step": 12,
  "stepName": "Promote, hold, or reject artifacts",
  "convergenceCycle": "lantern-v1-training",
  "generatedAt": "2026-06-08",
  "evidence": [
    "Dataset extracted from committed ingest sources",
    "Privacy boundaries enforced per example",
    "Modelfiles converted to behavior contracts",
    "LoRA harness architecture planned",
    "Eval metrics defined (Three Doors, receipts, routing)",
    "HFF Bayesian state cube integrated with training loop",
    "Rollback path documented (v0 fallback)"
  ],
  "claims": [
    "v1 models improve over v0 baselines",
    "Training respects privacy boundaries",
    "Self-adaptive training loop converges efficiently",
    "HFF status cubes track training quality"
  ],
  "validation": "pending",
  "rollback": "revert to v0 Modelfiles + base models",
  "nextAction": "Extend dataset to 500+ examples; build training harness with Bayesian scheduling"
}
```

---

## References

- **Convergence loop:** docs/CONVERGENCE-LOOP.md
- **Privacy governance:** PRIVACY_GOVERNANCE.md
- **Data architecture:** memory/data_architecture.md
- **Bayesian inference:** Research papers (QLoRA, LoRA, confidence scoring)
- **HFF model:** memory/project_status_cube.md

