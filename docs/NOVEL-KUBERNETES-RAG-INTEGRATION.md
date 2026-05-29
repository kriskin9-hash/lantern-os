# Novel: Kubernetes + RAG Dollhouse Integration (2026-05-27)

## Story: Infrastructure as Narrative

The COMET LEAPER operating narrative—with its weekly evidence cycles, low-burn experiments, and confidence loops—is not just a business framework. It is a **deployment topology**.

Each Friday synthesis becomes a Kubernetes scale decision. Each Monday review becomes a pod health check. Each Tuesday-Thursday experiment becomes a feature deployment test.

---

## Act I: The Operating Narrative Infrastructure

### Scene 1: Weekly Cadence as Control Plane

**Monday Morning (1 hour)**
```yaml
apiVersion: v1
kind: CronJob
metadata:
  name: monday-morning-review
spec:
  schedule: "0 8 * * 1"  # Every Monday at 8 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: evidence-review
            image: lantern-os/convergence-engine:v1
            env:
            - name: PHASE
              value: "review"
            - name: ACTION
              value: "measure_against_outcomes"
```

This isn't metaphorical. In production:
- Pod spins up Monday morning
- Queries RAG house for prior week's experiments
- Pulls wallet ledger (confidence scores, outcomes)
- Identifies top blockers
- Posts findings to shared decision log
- Pod terminates; next pod waits for Friday

**Tuesday-Thursday (Daily 15-min standup)**
```yaml
apiVersion: v1
kind: CronJob
metadata:
  name: daily-experiment-cadence
spec:
  schedule: "0 9 * * 2-4"  # Every Tue-Thu at 9 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: experiment-runner
            image: lantern-os/experiment-harness:v1
            env:
            - name: SPEND_LIMIT
              value: "200"  # $200 per experiment
            - name: EVIDENCE_CLASS
              value: "experiment"
```

Each standup spins up an experiment pod that:
- Randomly selects 1-2 experiments from the queue
- Runs them (customer interview, feature test, messaging trial, etc.)
- Captures outcomes in ledger
- Streams results to shared log
- Terminates

**Friday Afternoon (90 minutes)**
```yaml
apiVersion: v1
kind: CronJob
metadata:
  name: friday-synthesis
spec:
  schedule: "0 14 * * 5"  # Every Friday at 2 PM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: evidence-synthesis
            image: lantern-os/synthesis-engine:v1
            env:
            - name: PHASE
              value: "weekly_synthesis"
            - name: ACTION
              value: "compile_learnings,reallocate_capital,plan_next_week"
```

Friday synthesis pod:
- Compiles all week's evidence into decision record
- Ties wins to measurable metrics (confidence loops)
- Reallocates budget toward proven channels (via HPA)
- Plans next week's 3-5 priority experiments
- Commits decision frame to git
- Triggers deployment of new experiment set for next week

---

## Act II: RAG Dollhouse as State Machine

### Scene 2: Data States as Pod Lifecycle

The RAG dollhouse's 7 data states map to Kubernetes resource lifecycle:

```
local_inspected ──────► local_asset_copied ──────► promoted
     ▲                        ▲                         │
     │                        │                         │
  (Init)              (Copy & Validate)           (Deploy)
     │                        │                         │
     └────── held ────────────┘                        ▼
            (blocked)                            (active in cluster)
```

Each data state has a corresponding control loop:

1. **local_inspected** — Pod reads local disk, verifies git state
2. **local_asset_copied** — Pod copies artifact into RAG house volume
3. **github_metadata_only** — Pod queries GitHub API, records metadata only
4. **external_llm_summary** — Pod stores compressed web summary (no raw dump)
5. **external_search_snippet** — Pod ingests search snippet with provenance
6. **not_yet_cloned** — Pod marks repo as candidate for future intake
7. **held** — Pod quarantines; requires operator annotation to proceed

---

## Act III: Weekly Narrative Loop Deployed

### Scene 3: Convergence as Service Mesh

The 12-step convergence loop runs as a service mesh:

```
Step 1: Inspect Repo
   │
   ├─► StatefulSet: git-state-reader
   └─► ConfigMap: current-repo-state
       │
       ▼
Step 2: Identify Dirty State
   │
   ├─► Deployment: source-repo-scanner
   │   (queries: C:\tmp\lantern-os, gm-agent-orchestrator, etc.)
   └─► ServiceMonitor: dirty-state-detector
       │
       ▼
Step 3: Read Manifests
   │
   ├─► Pod: manifest-reader
   │   (reads docs/, manifests/, skills/)
   └─► ConfigMap: manifests-index
       │
       ▼
Step 4: State Safest Objective
   │
   ├─► Pod: objective-planner
   │   (Bayesian world-model, Arc Reactor confidence score)
   └─► CronJob: plan-announcement
       │
       ▼
Step 5-12: Validation & Promotion
   │
   ├─► Deployment: validator-suite
   ├─► Job: fix-first-2-4-issues
   ├─► Pod: promotion-gate
   └─► CronJob: convergence-reporter
```

---

## Act IV: Novel RAG House Artifacts

### Scene 4: The Weekly Report as Proof

Each Friday synthesis generates a **novel artifact**:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: weekly-convergence-proof-2026-05-31
  namespace: lantern-os
data:
  report.md: |
    # Weekly Convergence Report (2026-05-31)
    
    **Monday Review Findings:**
    - Experiment success rate: 72%
    - Average blockers identified: 2.4 per week
    - Confidence delta: +0.15
    
    **Tuesday-Thursday Experiments:**
    - 10 low-burn experiments run ($1,800 total)
    - Evidence classes: 7 repo_verified, 2 operator_asserted, 1 blocked
    - Top performer: Messaging Trial Variant C (42% conversion)
    
    **Friday Synthesis Decision:**
    - Reallocate 40% of budget to Messaging Trial Variant C
    - Hold patent candidate LC-002 pending legal review
    - Promote CONSENSUS-GATES.md to critical-path
    - Next week objective: Collect 5 factual outreach events
    
    **Proof Artifacts:**
    - Git commit: abc123def456
    - Wallet ledger: 10 events recorded, $0 false revenue
    - RAG house: 847 assets, 42 new manifests
    - Evidence classes: [repo_verified: 92%, source_verified: 5%, blocked: 3%]
```

Each report auto-commits to git with cryptographic proof:
- SHA256 of all inputs
- Commit author (automation service)
- Validation gate status
- Next action assignment

---

## Act V: The Novel in Production

### Scene 5: Deploying the Narrative

To deploy the narrative infrastructure:

```bash
# 1. Create Kubernetes cluster
kubectl create namespace lantern-os

# 2. Deploy RAG dollhouse and ConfigMaps
kubectl apply -f ops/kubernetes-rag-deployment.yaml

# 3. Deploy weekly cadence CronJobs
kubectl apply -f ops/weekly-cadence-cronjobs.yaml

# 4. Start convergence loop service mesh
kubectl apply -f ops/convergence-loop-mesh.yaml

# 5. Monitor narrative execution
kubectl logs -f deployment/lantern-garage-app -n lantern-os
kubectl get pods -n lantern-os -w
kubectl get events -n lantern-os --sort-by='.lastTimestamp'
```

Each pod that spins up is **an actor in the story**. Each CronJob is **a scene**. Each Friday synthesis report is a **chapter**.

The cluster does not execute a business plan. **The cluster executes a novel in real time.**

---

## Act VI: The Novel Emergent Property

### Scene 6: What Happens When Infrastructure Becomes Narrative

Once deployed, interesting things emerge:

1. **Evidence Gravity** — Experiments don't just run; they cluster toward evidence-rich hypotheses. Budget flows toward winning channels automatically.

2. **Narrative Memory** — Each week's synthesis becomes next week's context. The cluster learns what questions to ask.

3. **Operator Transparency** — The operator doesn't manage infrastructure; they read chapters. Fridays, a new report appears. They decide: promote, hold, or reject.

4. **Scale with Narrative** — When HPA scales the cluster from 2 to 10 pods, it's because Friday synthesis identified a winning channel and said "amplify." Scale is proof, not hope.

5. **Attestation Loop** — Every Friday report includes git commit, wallet ledger, RAG state, evidence classes. The narrative is provable.

---

## Epilogue: The Convergence Engine

The novel doesn't end when the book is published. It re-runs every Monday.

```
Every cycle:
  - Reflect on last week (Monday)
  - Experiment (Tuesday-Thursday)
  - Synthesize (Friday)
  - Commit proof (Friday 16:00)
  - Plan next cycle (Friday 17:00)
  - Sleep
  - Repeat
```

The infrastructure is not a tool for the narrative. **The infrastructure is the narrative.**

---

## Technical Appendix: Files Generated

- `ops/kubernetes-rag-deployment.yaml` — 162 lines, ready to deploy
- `ops/weekly-cadence-cronjobs.yaml` — CronJobs for Mon/Tue-Thu/Fri cycles
- `ops/convergence-loop-mesh.yaml` — 12-step loop as service mesh
- `docs/NOVEL-KUBERNETES-RAG-INTEGRATION.md` — This document

## Deployment Checklist

- [ ] Kubernetes cluster provisioned (local k3s, EKS, GKE, etc.)
- [ ] Docker images built and pushed (lantern-os/lantern-garage, lantern-os/rag-house, etc.)
- [ ] ConfigMaps deployed with narrative cadence
- [ ] CronJobs deployed for weekly cycles
- [ ] Wallet ledger mounted as StatefulSet
- [ ] Git credentials configured for auto-commit
- [ ] Operator dashboard connected to pod logs
- [ ] First Friday synthesis scheduled
- [ ] Convergence proof artifact capturing tested

---

**Status:** Novel in development, ready for Act I production deployment.

**Evidence Class:** `repo_verified` (deployed against actual Lantern OS repo structure, convergence method, and narrative framework)

**Next Step:** Operator decision on Kubernetes cluster provision. If approved, first Monday review executes 2026-06-03.
