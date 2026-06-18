# Agent Handoff: Distributed Work Queue (2026-06-15)

## Status

**Convergence Model Σ₀ architectural specification is COMPLETE and merged to master.**

- ✅ CONVERGANCE-SIGMA0-BRIEFING.md (immutable North Star)
- ✅ RESEARCH-CANON.md (living research by component)
- ✅ convergence-core-mapping.md (code alignment + roadmap)
- ✅ WORK-QUEUE-SYSTEM.md (distributed coordination spec)
- ✅ CLAUDE.md (updated with architectural constraints)

**Initial work queue deployed: `data/work-queue.jsonl` with 16 Phase 1-4 tasks across 4 agent lanes.**

---

## How to Proceed: Distributed Work Queue Workflow

### For Each Agent Lane (claude, codex, gemini, devin)

**1. Check Available Work**

```bash
# View all queued tasks in your lane
curl -s http://127.0.0.1:4177/api/queue/status?lane=claude | jq '.items[] | select(.status=="queued")'

# Or: check the master work-queue.jsonl directly
cat data/work-queue.jsonl | jq 'select(.lane=="claude" and .status=="queued")'
```

**2. Claim Your First Task**

```bash
# POST to /api/queue/assign
curl -X POST http://127.0.0.1:4177/api/queue/assign \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "machine-alex-main",
    "machine_name": "Your Machine",
    "lane": "claude"
  }'

# Returns: { "ok": true, "item": {...}, "git_commands": [...] }
```

**3. Execute Git Setup**

The assign response gives you a list of git commands. Run them:

```bash
git checkout master
git pull origin master
git checkout -b claude/515-kernel-formalize
git push -u origin claude/515-kernel-formalize
```

**4. Do the Work**

Read the task's `acceptance_criteria` carefully. Implement code, write tests, ensure they pass.

Example task (wq-001-phase1-kernel):
- Create `src/convergence/kernel.py` with Python dataclasses
- Create `src/convergence/objects.py` with Memory, Task, Tool, ConvergenceRecord
- Create tests in `tests/test_convergence_kernel.py`
- All acceptance criteria met + tests passing

**5. Update Progress (Optional)**

As you work:

```bash
curl -X POST http://127.0.0.1:4177/api/queue/progress \
  -H "Content-Type: application/json" \
  -d '{
    "id": "wq-001-phase1-kernel",
    "status": "in_progress",
    "message": "Implementing Memory class with append() method"
  }'
```

**6. Complete and Submit**

When done:

```bash
# Ensure tests pass
python -m pytest tests/test_convergence_kernel.py -q

# Commit your work
git commit -m "feat(convergence): implement kernel with Memory/Task/Tool/ConvergenceRecord dataclasses"

# Get your commit hash
COMMIT_HASH=$(git rev-parse HEAD)

# Submit to queue
curl -X POST http://127.0.0.1:4177/api/queue/complete \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"wq-001-phase1-kernel\",
    \"branch\": \"claude/515-kernel-formalize\",
    \"machine_id\": \"machine-alex-main\",
    \"tests_passed\": true,
    \"commit_hash\": \"$COMMIT_HASH\",
    \"notes\": \"All acceptance criteria met. Memory/Task/Tool/ConvergenceRecord classes tested.\"
  }"

# Returns: { "ok": true, "pr_number": 524, "pr_url": "..." }
```

The queue API automatically:
- Creates a GitHub PR from your branch → master
- Archives the task to work-queue-complete.jsonl
- Removes it from work-queue.jsonl
- Unblocks any dependent tasks

**7. Pick Your Next Task**

Once your task is complete, call assign again:

```bash
curl -X POST http://127.0.0.1:4177/api/queue/assign \
  -H "Content-Type: application/json" \
  -d '{"machine_id": "machine-alex-main", "machine_name": "...", "lane": "claude"}'
```

The queue respects:
- **Monoworkstream:** You can't have 2 tasks in progress simultaneously (within your lane)
- **Dependencies:** If your next task depends on unfinished work, you'll get null + a message listing blockers
- **Phase ordering:** Phase 2 doesn't unlock until Phase 1 is 50% complete

---

## Task Dependency Graph (Phase 1-4)

```
Phase 1: Structure (Week 1)
├─ wq-001: Kernel (claude)           [no deps]
├─ wq-002: Memory (codex)            [blocks: wq-005, wq-006, wq-007, wq-008]
├─ wq-003: Tools (gemini)            [blocks: wq-006]
├─ wq-004: Codebase Index (devin)    [no deps]
├─ wq-014: Kernel Bootstrap (codex)  [blocks: wq-015, wq-016]
├─ wq-015: Dream Integration (gemini) [blocks: wq-005]
└─ wq-016: Verify Baseline (devin)   [no deps]

Phase 2: Linkage (Week 2) [unlocks when Phase 1 > 50%]
├─ wq-005: Dream→ConvergenceRecord (claude) [depends: wq-001, wq-002]
├─ wq-006: Router→ConvergenceRecord (codex) [depends: wq-001, wq-003]
├─ wq-007: Verify Linkage (gemini)          [depends: wq-001, wq-002]
└─ wq-008: Memory Query Integration (devin) [depends: wq-002, wq-005]

Phase 3: Graph (Week 3) [unlocks when Phase 2 > 75%]
├─ wq-009: GraphRAG Integration (claude)    [depends: wq-005, wq-006]
└─ wq-010: Hierarchical Queries (codex)     [depends: wq-009]

Phase 4: Convergence (Week 4) [unlocks when Phase 3 > 100%]
├─ wq-011: Pattern Extraction (gemini)      [depends: wq-006, wq-007]
├─ wq-012: Failure Analysis (devin)         [depends: wq-011]
└─ wq-013: Convergence Metrics (claude)     [depends: wq-011]
```

---

## Monoworkstream Rule (Critical)

**Each lane can have at most ONE task "assigned" or "in_progress" at a time.**

If you try to claim a second task before finishing the first:

```bash
curl -X POST http://127.0.0.1:4177/api/queue/assign \
  -H "Content-Type: application/json" \
  -d '{"machine_id": "...", "machine_name": "...", "lane": "claude"}'

# Returns:
# { "ok": false, "reason": "claude lane already has task wq-001-phase1-kernel in progress" }
```

**Options:**
1. Complete the current task (preferred)
2. Abandon the task (if interrupted):

```bash
curl -X POST http://127.0.0.1:4177/api/queue/abandon \
  -H "Content-Type: application/json" \
  -d '{"id": "wq-001-phase1-kernel", "reason": "Emergency context switch"}'
```

---

## How the Queue Server Works (Technical Reference)

**Endpoints:**

- `GET /api/queue/status` — View queue state (optional filters: ?lane=claude, ?phase=Phase%201, ?status=queued)
- `POST /api/queue/assign` — Claim next queued task (respects monoworkstream, dependencies, phase ordering)
- `POST /api/queue/progress` — Update task status while working
- `POST /api/queue/complete` — Submit finished work (auto-creates PR)
- `POST /api/queue/abandon` — Return task to queue (if interrupted)
- `POST /api/queue/conflict` — Report simultaneous work on same task (first to complete wins)

**Data:**

- `data/work-queue.jsonl` — Append-only log of all tasks (current state)
- `data/work-queue-complete.jsonl` — Archive of completed tasks (for analysis)
- `data/conflicts.jsonl` — Conflict log (for debugging)

**Rules Enforced:**

- ✅ Monoworkstream: one task per lane at a time
- ✅ Dependency blocking: task can't be assigned until all dependencies are completed
- ✅ Phase ordering: Phase 2 requires Phase 1 > 50% complete
- ✅ Conflict detection: two machines claiming same task → first to complete wins

---

## Timeline

**Phase 1: Structure** (Week 1: Jun 15-20)
- 4 parallel lanes, ~4-6 hours per task
- Expected completion: ~24 hours wall-clock (all 7 tasks done in parallel)

**Phase 2: Linkage** (Week 2: Jun 20-27)
- Depends on Phase 1 completion
- 4 tasks, ~3-4 hours each
- Expected: ~12 hours wall-clock

**Phase 3: Graph** (Week 3: Jun 27-Jul 4)
- Depends on Phase 2 completion
- 2 tasks, ~5-6 hours each
- Expected: ~6 hours wall-clock

**Phase 4: Convergence** (Week 4: Jul 4-11)
- Depends on Phase 3 completion
- 3 tasks, ~4-6 hours each
- Expected: ~9 hours wall-clock

**Total wall-clock: ~50 hours across 4 agents in parallel = massive speedup vs serial.**

---

## Getting Help

**If you're blocked:**

1. Check task dependencies: `cat data/work-queue.jsonl | jq '.dependencies'`
2. Check phase unlock status: `curl http://127.0.0.1:4177/api/queue/status | jq '.by_phase'`
3. Read the acceptance criteria carefully (in work-queue.jsonl item)
4. Check CONVERGANCE-SIGMA0-BRIEFING.md and RESEARCH-CANON.md for architectural context
5. Read the existing code in the target files

**If the queue server isn't running:**

```bash
# Start it manually (API runs on port 4177)
node apps/lantern-garage/server.js
```

---

## Success Criteria

**Phase 1 complete when:**
- All 7 Phase 1 tasks merged to master (7/7 PRs closed)
- All acceptance criteria verified
- Tests passing across all modules
- Kernel bootstrap working

**By the end of Phase 4:**
- Σ₀ Convergence Core fully integrated
- All loop stages wired: Observe → Remember → Reason → Act → Verify → Converge
- Memory query API live and tested
- Convergence records flowing through all reasoners
- Pattern extraction running
- Self-improvement loop operational

---

## Remember

**From CONVERGANCE-SIGMA0-BRIEFING.md:**

```
Observe.
Remember.
Reason.
Act.
Verify.
Converge.

Accumulate capability.
Reject sprawl.
Stay local.
```

Every PR should strengthen one stage of the loop. Reference the stage in your commit message.

---

**Deployed:** 2026-06-15  
**Queue Status:** Ready to begin  
**Next Action:** `curl http://127.0.0.1:4177/api/queue/status` to view tasks
