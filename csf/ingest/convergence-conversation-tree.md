# CSF Ingestion — Conversation Tree Branching

**Status:** queued  
**Priority:** 4 — architectural change, high value for long sessions  
**Estimated effort:** 6–8 hours  
**Source:** [Conversation Tree Architecture, arxiv 2603.21278](https://arxiv.org/html/2603.21278v1)

## Problem

The dream chat uses a linear `conversationHistory` array. When a user picks Door 2, it overwrites the Door 1 path. Users can't return to a prior door choice. This makes the three-doors canary system a one-way funnel instead of a branching exploration space.

## Proposed Architecture

```
session
  └── branch:root
        ├── turn 1: "fog valley, three doors"
        │     reply: "The fog itself is speaking…"
        │     DOORS: [A, B, C]
        ├── branch:A — "I step through mist"
        │     └── turn 2A, turn 3A…
        ├── branch:B — "I hear the doors creak"
        │     └── turn 2B, turn 3B…
        └── branch:C — "I touch what waits beyond"
              └── turn 2C, turn 3C…
```

**Client state:**
```js
const sessionTree = {
  sessionId: crypto.randomUUID(),
  branches: { root: [] },
  currentBranch: 'root'
};
```

When a door chip is clicked, a new branch is created forking from the current turn. The history sent to the API is the path from root → current branch, not the whole tree.

**Branch navigation:** Small breadcrumb bar above messages showing current path. Click any ancestor node to view that branch.

## Files to Change
- `apps/lantern-garage/public/dream-chat.html` — `sessionTree` state, branch UI, breadcrumb nav
- `apps/lantern-garage/lib/conversation-store.js` — add `sessionId` + `branchId` fields
- `apps/lantern-garage/routes/dream.js` — `GET /api/dream/session/:sessionId` to load a full tree

## Key Insight from Research
[arxiv 2603.21278](https://arxiv.org/html/2603.21278v1) — chronological insertion (insert branch point in correct temporal order) outperforms end-append for causal coherence. When building the branch history to send to the AI, insert the branch divergence point at the correct position, not at the end.
