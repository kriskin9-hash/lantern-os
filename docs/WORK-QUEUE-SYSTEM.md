# Lantern OS Distributed Work Queue System

Multi-machine contributor coordination via JSONL queue + HTTP API.

---

## Canonical Queues & Branch Naming

> **Reconciliation note (2026-06-15).** Two distinct queues exist; do not conflate:
>
> - **`data/work-queue.jsonl`** - *canonical* queue for the **Convergence Core** build (Phases 1-4, ids `wq-NNN`). The autonomous dispatcher consumes this for core work.
> - **`data/agent-work-queue/{pending,assigned,in_progress,completed,failed}/queue.jsonl`** - a *separate* dispatch lane for **Three-Doors / CSF** items (`issue-3NN`). Different lifecycle.
>
> **Branch names derive from the queue item `id`, NOT a GitHub issue number.** Earlier rows set `branch` from `issue_number`, which collided with real GitHub issues/PRs (e.g. `claude/527-A1-stream-autonomous-work`). Queued items now use `branch = "<lane>/<id>"` with `issue_number: null` until actually filed.

---

## Architecture

```
GitHub Issues
    ↓
Intake API (POST /api/queue/intake)
    ↓
work-queue.jsonl (append-only persistent store)
    ↓
Status API (GET /api/queue/status)
    ↓
Machine 1: claude/branch-name
Machine 2: codex/branch-name
Machine 3: gemini/branch-name
    ↓
Completion API (POST /api/queue/complete)
    ↓
work-queue-complete.jsonl (archive)
    ↓
GitHub PR (auto-created on completion)
```

---

## Data Structures

### WorkItem (in work-queue.jsonl)

```json
{
  "id": "wq-001-phase1-kernel",
  "issue_number": 601,
  "phase": "Phase 1: Structure",
  "component": "LANTERN-KERNEL",
  "title": "Formalize Kernel as state machine",
  "description": "Define Python dataclasses: Memory, Task, Tool, ConvergenceRecord. Implement six-stage loop orchestration.",
  "acceptance_criteria": [
    "✅ Memory class with append() and query() methods",
    "✅ Task dataclass with goal + constraints + status",
    "✅ Tool dataclass wrapping existing routes",
    "✅ ConvergenceRecord with hypothesis + evidence + result + confidence",
    "✅ Tests passing"
  ],
  "lane": "claude",
  "branch": "claude/601-kernel-formalize",
  "files": [
    "src/convergence/kernel.py",
    "src/convergence/objects.py",
    "tests/test_convergence_kernel.py"
  ],
  "dependencies": [],
  "status": "queued",
  "assigned_to": null,
  "assigned_machine": null,
  "assigned_at": null,
  "started_at": null,
  "completed_at": null,
  "pr_url": null,
  "estimated_hours": 4,
  "priority": 1
}
```

### QueueStatus (GET response)

```json
{
  "total_items": 16,
  "by_phase": {
    "Phase 1: Structure": { "queued": 4, "assigned": 2, "completed": 1 },
    "Phase 2: Linkage": { "queued": 4, "assigned": 0, "completed": 0 },
    "Phase 3: Graph": { "queued": 2, "assigned": 0, "completed": 0 },
    "Phase 4: Convergence": { "queued": 2, "assigned": 0, "completed": 0 }
  },
  "by_lane": {
    "claude": { "queued": 4, "assigned": 1, "in_progress": 1, "completed": 0 },
    "codex": { "queued": 4, "assigned": 1, "in_progress": 0, "completed": 0 },
    "gemini": { "queued": 4, "assigned": 0, "in_progress": 0, "completed": 0 },
    "devin": { "queued": 4, "assigned": 0, "in_progress": 0, "completed": 0 }
  },
  "by_machine": {
    "machine-alex-main": { "assigned": 2, "in_progress": 1 },
    "machine-contrib-1": { "assigned": 1, "in_progress": 0 }
  },
  "blocked": [
    { "id": "wq-005-verify", "blocked_by": ["wq-001-kernel", "wq-002-memory"] }
  ]
}
```

---

## API Endpoints

### 1. Intake: Create Work Item

**POST /api/queue/intake**

Request:
```json
{
  "issue_number": 601,
  "phase": "Phase 1: Structure",
  "component": "LANTERN-KERNEL",
  "title": "...",
  "description": "...",
  "acceptance_criteria": [...],
  "lane": "claude",
  "files": [...],
  "dependencies": [],
  "estimated_hours": 4
}
```

Response:
```json
{
  "ok": true,
  "id": "wq-001-phase1-kernel",
  "status": "queued"
}
```

---

### 2. Status: View Queue

**GET /api/queue/status**

Optional query params:
- `lane=claude` — filter by lane
- `phase=Phase 1` — filter by phase
- `status=queued|assigned|in_progress|completed`

Response:
```json
{
  "total_items": 16,
  "items": [
    { "id": "wq-001", "status": "queued", "lane": "claude" },
    { "id": "wq-002", "status": "assigned", "assigned_to": "machine-alex-main" }
  ]
}
```

---

### 3. Assign: Check Out Task

**POST /api/queue/assign**

Request:
```json
{
  "machine_id": "machine-alex-main",
  "machine_name": "Alex MacBook",
  "lane": "claude"
}
```

Response:
```json
{
  "ok": true,
  "item": {
    "id": "wq-001-phase1-kernel",
    "branch": "claude/601-kernel-formalize",
    "files": ["src/convergence/kernel.py", ...],
    "acceptance_criteria": [...]
  },
  "git_commands": [
    "git checkout master",
    "git pull origin master",
    "git checkout -b claude/601-kernel-formalize",
    "git push -u origin claude/601-kernel-formalize"
  ]
}
```

**Behavior:**
- Assigns next queued item in lane
- Returns null if lane has blocking dependencies
- Returns null if lane already has item in progress (monoworkstream rule)
- Updates assigned_to, assigned_machine, assigned_at
- Appends to work-queue.jsonl: status → "assigned"

---

### 4. Progress: Update Status

**POST /api/queue/progress**

Request:
```json
{
  "id": "wq-001-phase1-kernel",
  "status": "in_progress",
  "message": "Started kernel.py implementation"
}
```

Response:
```json
{
  "ok": true
}
```

---

### 5. Complete: Submit Work

**POST /api/queue/complete**

Request:
```json
{
  "id": "wq-001-phase1-kernel",
  "branch": "claude/601-kernel-formalize",
  "machine_id": "machine-alex-main",
  "tests_passed": true,
  "commit_hash": "a1b2c3d",
  "notes": "All acceptance criteria met. Ready for review."
}
```

Response:
```json
{
  "ok": true,
  "pr_number": 524,
  "pr_url": "https://github.com/alex-place/lantern-os/pull/524"
}
```

**Behavior:**
- Validates tests passed
- Creates GitHub PR automatically (branch → master)
- Archives to work-queue-complete.jsonl
- Removes from work-queue.jsonl
- Sets status → "completed"
- Returns PR number

---

### 6. Conflict: Handle Simultaneous Work

**POST /api/queue/conflict**

Request:
```json
{
  "id": "wq-001-phase1-kernel",
  "machine_1": "machine-alex-main",
  "machine_2": "machine-contrib-1",
  "message": "Both machines checked out same task"
}
```

Response:
```json
{
  "ok": true,
  "winner": "machine-alex-main",
  "action": "machine-contrib-1 must abandon branch"
}
```

**Resolution:**
- First machine to POST /complete wins
- Second machine must abandon work, request new task
- Logged to conflicts.jsonl for analysis

---

## Queue Management Rules

### Monoworkstream Enforcement
- **One task per lane at a time**
- If `claude` has task in "assigned" or "in_progress", next assign to `claude` returns null
- Machine must complete or abandon before requesting new `claude` task

### Dependency Blocking
- Task with `dependencies: ["wq-001", "wq-002"]` cannot be assigned until those are "completed"
- Status endpoint lists blocked items

### Phase Ordering
- Phase 1 must be 50% complete before Phase 2 auto-unlocks
- Phase 2 must be 75% complete before Phase 3 unlocks
- Phase 4 requires all of 1-3 complete

---

## Machine Registration

Each machine maintains a local `~/.lantern/machine-config.json`:

```json
{
  "machine_id": "machine-alex-main",
  "machine_name": "Alex MacBook Pro",
  "repo_path": "/Users/alex/GitHub/lantern-os",
  "queue_api": "http://127.0.0.1:4177/api/queue",
  "git_remote": "https://github.com/alex-place/lantern-os.git",
  "active_lanes": ["claude", "codex"],
  "concurrent_limit": 2
}
```

---

## CLI Tools (lantern-queue command)

### Check Status

```bash
lantern-queue status
lantern-queue status --lane claude
lantern-queue status --phase "Phase 1"
```

Output:
```
LANTERN OS WORK QUEUE

Phase 1: Structure
  ✓ wq-001-kernel (claude)          [COMPLETED]
  ⏳ wq-002-memory (codex)           [IN_PROGRESS] (machine-contrib-1)
  ⏳ wq-003-tools (gemini)           [ASSIGNED] (machine-alex-main, 1h ago)
  ⌛ wq-004-model-broker (devin)     [QUEUED]

Phase 2: Linkage
  ⌛ wq-005-convergence-record (claude)  [QUEUED] (blocked by wq-001, wq-002)
  ...
```

### Check Out Task

```bash
lantern-queue checkout --lane claude
# or
lantern-queue next
```

Output:
```
ASSIGNED: wq-002-memory-dataclasses

Branch:       codex/602-memory-dataclasses
Lane:         codex
Component:    LANTERN-MEMORY
Est. Time:    6 hours

Acceptance Criteria:
  ✓ Memory class with append() and query()
  ✓ JSONL persistence
  ✓ Confidence tracking
  ✓ Tests passing

Files to modify:
  src/convergence/memory.py
  tests/test_convergence_memory.py

Ready? Run:
  git checkout master && git pull
  git checkout codex/602-memory-dataclasses
  git push -u origin codex/602-memory-dataclasses
```

### Update Progress

```bash
lantern-queue progress --id wq-002 --status in_progress
lantern-queue progress --id wq-002 --message "Implementing append() method"
```

### Complete Task

```bash
lantern-queue complete --id wq-002 --tests-passed
# or
lantern-queue done --id wq-002
```

Output:
```
COMPLETED: wq-002-memory-dataclasses

✓ Tests passed
✓ Commits: 3
✓ Files changed: 2

Creating PR...
→ PR #524: feat(memory): implement Memory dataclass with append/query
→ https://github.com/alex-place/lantern-os/pull/524

Next task in codex lane:
  lantern-queue next
```

### Abandon Task (if interrupted)

```bash
lantern-queue abandon --id wq-002 --reason "Emergency context switch"
```

Output:
```
ABANDONED: wq-002-memory-dataclasses

Cleanup:
  git checkout master
  git branch -D codex/602-memory-dataclasses
  
Task returned to queue.
```

---

## Work Queue Data Files

### work-queue.jsonl

Append-only log of all work items (one JSON object per line).

```jsonl
{"id":"wq-001-phase1-kernel","issue_number":601,"status":"completed","completed_at":"2026-06-15T14:30:00Z","pr_url":"https://github.com/alex-place/lantern-os/pull/524"}
{"id":"wq-002-memory-dataclasses","issue_number":602,"status":"assigned","assigned_to":"machine-contrib-1","assigned_at":"2026-06-15T14:32:00Z"}
```

### work-queue-complete.jsonl

Archive of completed items (for historical reference).

```jsonl
{"id":"wq-001-phase1-kernel","completed_at":"2026-06-15T14:30:00Z","pr_url":"...",estimated_hours":4,"actual_hours":3.5,"notes":"..."}
```

### conflicts.jsonl

Logs of detected conflicts for analysis.

```jsonl
{"timestamp":"2026-06-15T14:45:00Z","id":"wq-002","machine_1":"machine-alex-main","machine_2":"machine-contrib-1","resolution":"machine-alex-main won"}
```

---

## Multi-Machine Sync

All machines pull `work-queue.jsonl` every 30 seconds:

```python
# Every 30 seconds
GET /api/queue/status  # fetch latest queue state
# Compare to local copy
# Update local ~work-queue-local.json
# Detect conflicts
```

---

## Integration with Convergence 12

**Which loop stage does this improve?**

✅ **Act stage:** Distributed tool execution across machines  
✅ **Verify stage:** Task completion + PR creation tracking  
✅ **Convergence stage:** Queue metrics → pattern extraction (which tasks are bottlenecks?)

---

## Deployment

### On Primary Machine (where API runs)

```bash
# Start queue API server
node apps/lanterns-garage/routes/work-queue-api.js

# Verify
curl http://127.0.0.1:4177/api/queue/status
```

### On Contributor Machines

```bash
# Install CLI
npm install -g @lantern-os/queue-cli

# Configure
lantern-queue configure --api http://primary-machine:4177/api/queue

# Start polling / get work
lantern-queue next
```

---

## Example: 4-Machine Phase 1 Execution

```
PHASE 1: Structure (4 parallel lanes)

T=0:00
  Machine 1 (claude):  lantern-queue next → wq-001-kernel
  Machine 2 (codex):   lantern-queue next → wq-002-memory
  Machine 3 (gemini):  lantern-queue next → wq-003-tools
  Machine 4 (devin):   lantern-queue next → wq-004-model-broker

T=1:30
  Machine 1: lantern-queue progress --status in_progress --message "Implementing state machine"
  Machine 2: lantern-queue progress --status in_progress --message "Writing Memory dataclass"

T=3:45
  Machine 1: lantern-queue complete ✓
  → PR #524 created automatically
  → wq-001 archived
  
  Machine 3: lantern-queue complete ✓
  → PR #525 created automatically
  → wq-003 archived

T=4:30
  Machine 1: lantern-queue next → wq-005-convergence-record (Phase 2, depends on 001+002)
  → Blocked: returns null, suggests machine 1 wait or pick different lane
  → Machine 1: lantern-queue next --lane codex → wq-006-evidence-linking
```

Result: **All Phase 1 tasks done in ~4.5 hours across 4 machines in parallel.**

---

## Status Visibility

At any time, any machine can see:

```bash
lantern-queue status

PHASE 1: Structure
  ✓ wq-001-kernel (machine-1, completed 14:30)
  ⏳ wq-002-memory (machine-2, 1h 15m elapsed)
  ⏳ wq-003-tools (machine-3, 45m elapsed)
  ⏳ wq-004-model-broker (machine-4, 30m elapsed)

PHASE 2: Linkage [BLOCKED until Phase 1 > 50%]
  ⌛ wq-005-convergence-record [blocked by wq-001, wq-002]
  ...

All machines see same queue. Perfect coordination.
```

---

## Implementation Checklist

- [ ] **work-queue-api.js** — HTTP API (POST intake, GET status, POST assign, POST complete)
- [ ] **lantern-queue CLI** — Node.js CLI tool for machines
- [ ] **work-queue.jsonl** — Initial queue with Phase 1-4 tasks
- [ ] **conflicts.jsonl** — Empty (populated on conflicts)
- [ ] **Auto-PR creation** — Create PR when task completed via API
- [ ] **Dependency resolution** — Blocking logic in assign endpoint
- [ ] **Machine registration** — Detect and register connected machines
- [ ] **Status dashboard** — Optional web UI showing queue progress

---

**Status:** Specification complete. Ready to implement as LANTERN-KERNEL component.

This system replaces manual coordination with **persistent, distributed, conflict-aware task execution** that scales from 1 machine to N machines.
