# !CONVERGANCE Σ₀

## PROJECT

Lantern OS is a local-first Convergence Engine.

It is **not**:
- an AGI
- a mind uploader
- a chatbot
- a cloud service

It is:
**a persistent reasoning and coding system that improves through accumulated experience.**

---

## CORE LOOP

```
Observe
    ↓
Remember
    ↓
Reason
    ↓
Act
    ↓
Verify
    ↓
Converge
```

Nothing exists outside this loop.

---

## FIRST PRINCIPLES

1. **External reality beats internal consistency.**
   - Claim + evidence + confidence always.
   - Verification is mandatory.
   - Grounding is the safety mechanism.

2. **Models are replaceable.**
   - Convergence Core never assumes a specific LLM.
   - Swap Ollama ↔ llama.cpp ↔ vLLM without changing architecture.

3. **Memory is persistent.**
   - Append-only JSONL + graph.
   - Nothing is deleted; confidence may shift.

4. **Verification is mandatory.**
   - Every hypothesis tested.
   - Every code change validated.
   - Every decision grounded in evidence.

5. **Learning happens through retrieval and experience, not weight modification.**
   - Never retrain.
   - Store patterns as memories.
   - Improve by accumulating and recombining knowledge.

6. **Local ownership is a feature.**
   - User owns memory.
   - User owns codebase.
   - User owns model selection.
   - No cloud dependency.

7. **Architectural sprawl is technical debt.**
   - One loop.
   - Four objects (Memory, Task, Tool, ConvergenceRecord).
   - Everything else is implementation.

---

## CONVERGENCE 12

Native Lantern components that own one stage of the loop or the system itself.

### [01] LANTERN-KERNEL
**Purpose:** Core orchestration loop.

**Owns:**
- Task lifecycle
- State machine
- Orchestration
- Loop execution

**Does:**
- Observe → Remember → Reason → Act → Verify → Converge
- Manages the six stages

**OSS Inspiration:**
- AIOS concepts
- Runloop OS

**Status:** ✅ Core project

---

### [02] LANTERN-MODEL-BROKER
**Purpose:** Routes interchangeable local models.

**Abstraction:**
```
Lantern
     |
------------------
|    |    |      |
Qwen DS   Dev    Future
```

**Rule:** Never hardcode a provider.

**Dependencies:**
- Ollama
- llama.cpp
- vLLM
- LM Studio (future)

**Status:** 🔄 Existing abstraction (needs formalization)

---

### [03] LANTERN-MEMORY
**Purpose:** Persistent accumulated learning.

**Stores:**
- Patterns (extracted from successful convergence)
- Failures (root cause → solution → pattern)
- Architecture (design decisions)
- Projects (what we've built)
- Corrections (what we learned wrong)

**Data Structure:**
```
Memory {
    id
    timestamp
    source
    confidence
    content
    evidence_ids[]  // linked memories
}
```

**OSS Reference:**
- Codebase-Memory paper
- Mem0 patterns
- CADD/CSF format (existing)

**Status:** ✅ Existing concept (needs formalization)

---

### [04] LANTERN-GRAPH
**Purpose:** Knowledge relationships (not chat history).

**Structure:**
```
Project
    |
Architecture
    |
Files
    |
Lessons
    |
Patterns
```

**Not chat history.**
**Not conversation logs.**
**Knowledge only.**

**OSS Dependency:**
- GraphRAG (primary)
- Neo4j (optional, future)

**Status:** 🔄 Roadmap (not yet implemented)

---

### [05] LANTERN-TOOLS
**Purpose:** Unified execution layer.

**Available Tools:**
- bash
- git
- editor / file operations
- grep
- browser (MCP-based)
- test runners
- filesystem ops

**Protocol:**
- MCP-compatible
- Tool {name, input_schema, output_schema, call()}
- Always return {success, output, confidence}

**OSS Reference:**
- Model Context Protocol
- lazy-tool patterns

**Status:** ✅ Existing direction

---

### [06] LANTERN-CODER
**Purpose:** Coding specialization (not separate intelligence).

**Definition:**
```
Coder = 
  Kernel 
  + Memory
  + Tools
  + Task specialization (goal = "improve codebase")
```

**Not a separate system.**
**A task type.**

**OSS Inspiration:**
- Claude Code (reference)
- Aider (reference)
- OpenHands (reference)
- Goose (reference)
- Cline (reference)

**Status:** 🔄 Current objective (formalize as task, not system)

---

### [07] LANTERN-VERIFY
**Purpose:** Reality loop.

**Rule:** Every claim must have:
```
claim
evidence
confidence
source
```

**Handles:**
- Unit tests / integration tests
- Benchmarks (SWE-bench, Terminal-bench)
- Web verification (fetch + validate)
- Provenance (who said this?)
- Trace (where did this come from?)

**OSS Reference:**
- SWE-bench
- Terminal-bench
- Σ₀ framework (existing)

**Status:** ✅ Σ₀ framework aligned

---

### [08] LANTERN-DREAM
**Purpose:** Exploration mode (not a separate engine).

**Definition:**
```
Dream Mode =
  high creativity
  +
  low confidence
  +
  mandatory verification
```

**Rules:**
- exploration = 0.9
- verification_required = true
- memory_write = proposal_only (never final)
- confidence = max 0.3 until verified

**Never writes permanent truth.**

**Implementation:**
```python
dream_mode = {
    "reasoning_params": {
        "exploration": 0.9,
        "temperature": 0.8
    },
    "verification": "required",
    "memory_write": "proposal_only",
    "max_confidence": 0.3
}
```

**Status:** ✅ Existing design (rename to reasoning_params)

---

### [09] LANTERN-OBSERVATORY
**Purpose:** Repository and system understanding.

**Auto-generates:**
- Architecture diagrams
- Dependency maps
- File structure understanding
- Module relationships
- Dataflow

**Does not:**
- Hardcode paths (infer from codebase)
- Assume framework (detect and map)
- Miss hidden complexity (graph the dependencies)

**OSS Dependency:**
- repo-lantern patterns
- Corbell approaches

**Status:** 🔄 Mostly existing (needs formalization)

---

### [10] LANTERN-SANDBOX
**Purpose:** Safe isolated execution.

**Capabilities:**
- git worktrees (parallel experiment)
- Task isolation (one task ≠ affect another)
- Rollback (undo experiment)
- Snapshots (checkpoint state)

**Prevents:**
- State pollution
- Destructive experiments
- Cascading failures

**OSS Inspiration:**
- SWE-Agent patterns
- Firecracker approaches

**Status:** 🔄 Needed (partially exists as worktree support)

---

### [11] LANTERN-CONVERGENCE
**Purpose:** Pattern accumulation and self-improvement.

**Tracks:**
- Solved problems (don't solve twice)
- Repeated failures (root cause analysis)
- Stable patterns (extractable knowledge)
- Confidence growth (which hypotheses are getting stronger?)

**Rule:** Never retrains weights.
**Only:** Accumulates engineering knowledge.

**Data Flow:**
```
Failure
    ↓
Root Cause Analysis
    ↓
Solution
    ↓
Pattern
    ↓
Memory (+ evidence + confidence)
```

**Status:** ✅ Core philosophy (needs implementation)

---

### [12] LANTERN-LOCAL
**Purpose:** User sovereignty and offline operation.

**Rules:**
- local first (offline capable)
- model replaceable (user chooses)
- user owns memory (local storage)
- user owns history (not cloud)
- no external dependency (except optional cloud fallback)

**Dependencies:**
- Ollama (local models)
- local vector DB (if Graph uses embeddings)
- local graph DB (optional)

**Status:** ✅ Foundational

---

## OSS PHILOSOPHY

External projects are **not features**.

They become one of two things:

1. **Reference Implementation** — Study how it works; don't use directly
2. **Optional OSS Dependency** — Import as a module; Lantern owns the integration

**Examples:**

| OSS | Component | Role |
|-----|-----------|------|
| Ollama | Model Broker | Dependency |
| llama.cpp | Model Broker | Dependency |
| vLLM | Model Broker | Dependency |
| MCP | Tools | Dependency |
| GraphRAG | Graph | Dependency |
| Aider | Coder | Reference |
| OpenHands | Coder | Reference |
| Goose | Coder | Reference |
| Mem0 | Memory | Reference |
| SWE-bench | Verify | Reference |
| AIOS | Kernel | Reference |
| repo-lantern | Observatory | Reference |

---

## DESIGN LAW

Every new feature must answer:

**Which part of the Convergence Loop does this improve?**

```
| Feature | Loop Stage | Allowed? |
|---------|-----------|----------|
| Better memory retrieval | Remember | ✅ Yes |
| Better planning / routing | Reason | ✅ Yes |
| Better verification / grounding | Verify | ✅ Yes |
| Better tool execution | Act | ✅ Yes |
| Better convergence metrics | Converge | ✅ Yes |
| Separate dream engine | — | ❌ No |
| Separate digital personality | — | ❌ No |
| Multiple memory systems | — | ❌ No |
| Independent agent ecosystems | — | ❌ No |
| Cloud-first architecture | — | ❌ No |
```

**If the answer is unclear, do not add the feature.**

---

## LONG TERM GOAL

Build a local general-purpose coding agent that:

- **owns its memory** (append-only, user controls)
- **understands its codebase** (graph-based knowledge)
- **uses interchangeable models** (not locked to one LLM)
- **improves through experience** (retrieval, not retraining)
- **remains grounded in external reality** (verification mandatory)

---

## MOTTO

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

---

**This document is immutable.**  
**All architectural decisions reference it.**  
**No exceptions.**
