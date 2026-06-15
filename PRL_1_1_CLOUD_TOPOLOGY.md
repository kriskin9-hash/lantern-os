# PRL-1.1: Cloud Topology & Execution Boundary Fix

## The Problem

PRL-1 works beautifully **on a single machine**.

But it has a hidden assumption:

```
Python AI Trader ─→ writes to /data/trading/event-queue.jsonl
Node Lantern OS ─→ reads from /data/trading/event-queue.jsonl
```

### ❌ This breaks in cloud because:

| Scenario | Problem |
|----------|---------|
| Docker | Python container ≠ Node container, separate filesystems |
| Kubernetes | Each pod has isolated filesystem |
| Railway / VPS | Remote Python server can't access local Node filesystem |
| Scaling | If Python scales to N replicas, queue becomes corrupted |

**This is a fundamental architecture problem, not a bug.**

---

## The Solution: PRL-1.1

Remove filesystem coupling entirely. **Python becomes stateless.**

### Architecture Shift:

**BEFORE (Broken in Cloud):**
```
Python ─[filesystem]─> Queue ─[filesystem]─> Node
         (couples them)
```

**AFTER (Cloud-Safe):**
```
Python ─[HTTP API]─> Node Ingestion ─[internal]─> Queue ─[internal]─> Consumer
                                                  (Node owns everything)
```

---

## Key Architectural Decisions

### 1. **Python is Now Stateless**

Python's ONLY job:
- Generate trade decisions
- Send HTTP POST to Node
- No filesystem access
- No state persistence
- No queue ownership

**This means:**
- Python can be anywhere (VPS, Docker, Lambda, K8s pod)
- Python can scale horizontally (no conflicts)
- Python restart doesn't lose state (state is in Node)
- Python crash doesn't corrupt queue

### 2. **Node Owns Everything**

Node's responsibilities:
- Receive decisions (via HTTP API)
- Maintain queue
- Track idempotency
- Execute trades
- Audit log
- All persistent state

**This means:**
- Single source of truth is always Node
- Queue survives Python crash
- Idempotency prevents duplicates from Python re-emission
- Deterministic recovery possible

### 3. **The HTTP Boundary**

```
POST /api/events/ingest
```

This is the **formal contract** between stateless Python and stateful Node.

**Python sends:**
```json
{
  "source": "independent-ai",
  "ticker": "NVDA",
  "action": "BUY",
  "confidence": 0.81,
  "timestamp": 1710000000
}
```

**Node responds:**
```json
{
  "status": "accepted",
  "eventId": "evt-xyz",
  "traceId": "trace-123"
}
```

That's it. No shared filesystem. No IPC. Just HTTP.

---

## New Components

### EventIngestionAPI (`routes/event-ingestion.js`)

Three endpoints:

#### 1. **POST /api/events/ingest** — AI trader submits decisions
```
Validates schema
→ Enqueues to PRL-1 queue
→ Records audit trace
→ Returns eventId + traceId
```

#### 2. **GET /api/system/topology** — Shows deployment architecture
```
Returns:
- Python: stateless-signal-service
- Node: stateful-execution-system
- Coupling: http-only-no-filesystem
- Queue ownership: Node
```

#### 3. **GET /api/events/status** — Ingestion system health
```
Returns:
- Queue depth
- Consumer status
- Recent ingestion rate
```

---

## RuntimeTopology Config (`config/runtime-topology.json`)

Formal declaration of the architecture for different deployment modes:

```json
{
  "deploymentMode": "cloud-safe",
  "services": {
    "ai_trader": {
      "filesystemAccess": false,
      "queueAccess": false,
      "communication": "HTTP/REST only"
    },
    "lantern_os": {
      "queueOwnership": true,
      "auditLogOwnership": true,
      "filesystemAccess": true
    }
  },
  "coupling_rules": {
    "python_ai_trader": {
      "can_access": ["ingestion_api (HTTP)"],
      "cannot_access": ["queue", "state", "audit_log"]
    }
  }
}
```

This serves as:
1. **Documentation** — What each service owns
2. **Validation** — Check deployments against rules
3. **Deployment guide** — How to set up for Docker/K8s/Railway

---

## The Execution Flow (PRL-1.1)

### Normal Operation:

```
1. Python AI generates: BUY NVDA confidence=0.81
2. Python POST to /api/events/ingest
3. Node validates schema + rate limits
4. Node enqueues to PRL-1 queue
5. Consumer loop picks up (every 250ms)
6. Checks idempotency (never executed before)
7. Checks safety gate (stability >= 0.8)
8. Submits to Trade State Engine
9. Records idempotency
10. Marks queue event EXECUTED
```

### On Python Crash:

```
1. Python crashes
2. Decision already in Node queue (disk-backed)
3. Consumer retries when Python restarts
4. Idempotency prevents duplicate
```

### On Python Restart:

```
1. Python restarts
2. Resumes generating decisions
3. Posts to Node ingestion API
4. All state is in Node (no state loss)
5. Deterministic recovery from queue
```

---

## Cloud Deployment Scenarios

### Docker (Two Containers):

```yaml
services:
  ai-trader:
    image: python:3.9
    command: python main.py
    environment:
      LANTERN_OS_HOST: lantern-os
  
  lantern-os:
    image: node:16
    ports:
      - "4177:4177"
    volumes:
      - queue-data:/app/data/trading
    command: npm start

volumes:
  queue-data:
```

✅ Separate containers
✅ HTTP communication only
✅ Queue persists on volume

### Kubernetes (Two Pods):

```yaml
---
apiVersion: v1
kind: Pod
metadata:
  name: ai-trader
spec:
  containers:
  - name: trader
    image: python:3.9
    env:
    - name: LANTERN_OS_HOST
      value: lantern-os-service
---
apiVersion: v1
kind: Pod
metadata:
  name: lantern-os
spec:
  containers:
  - name: node
    image: node:16
    volumeMounts:
    - name: queue
      mountPath: /app/data/trading
  volumes:
  - name: queue
    persistentVolumeClaim:
      claimName: queue-pvc
```

✅ Separate pods
✅ Service DNS communication
✅ Persistent volume for queue

### Railway (Two Services):

```yaml
services:
  ai-trader:
    image: python:3.9
    environment:
      LANTERN_OS_HOST: lantern-os.railway.app

  lantern-os:
    image: node:16
    volumes:
      - queue-data:/app/data
```

✅ Separate services
✅ HTTPS ingestion endpoint
✅ Ephemeral + persistent volume

---

## Validation Checklist

After implementing PRL-1.1, verify:

✅ **No Filesystem Coupling**
```bash
# Python MUST NOT write to /data/trading
grep -r "open.*data/trading" src/
# Should return nothing
```

✅ **HTTP-Only Communication**
```bash
# Python → Node MUST be HTTP only
grep -r "socket\|IPC\|shared_memory" src/
# Should return nothing
```

✅ **Container Separation Test**
```bash
# Run Python and Node in separate containers
# Verify queue still works, no state loss
```

✅ **Topology Config Present**
```bash
# Verify config/runtime-topology.json exists
# Verify it documents the boundary correctly
```

✅ **Ingestion API Working**
```bash
curl -X POST http://localhost:4177/api/events/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"test", "ticker":"TEST", "action":"BUY", "confidence":0.5}'
# Should return eventId + traceId
```

---

## What PRL-1.1 Enables

### ✅ Docker Deployment
- Python and Node in separate containers
- No filesystem coupling
- Queue persists on volume

### ✅ Kubernetes Deployment
- Separate pods
- Python scales to N replicas
- Node single-instance (or HA with Redis later)
- Queue on PVC

### ✅ Cloud Platforms
- Railway, Heroku, GCP, AWS
- Remote Python via API
- No local filesystem assumptions

### ✅ Horizontal Scaling
- Python is stateless → can scale
- Node is stateful → stays single (PRL-2 adds multi-node)

### ✅ Production Reliability
- Clean separation of concerns
- No hidden coupling
- Explicit boundary (HTTP API)
- Deterministic deployment

---

## Files Changed

### New:
- `routes/event-ingestion.js` — HTTP ingestion API
- `config/runtime-topology.json` — Deployment configuration

### Updated:
- Python AI Trader (agents.py / main.py) — Remove filesystem writes, use HTTP

### Remains:
- PRL-1 queue, consumer, watchdog (no changes needed)

---

## Migration Path

### Phase 1 (Now):
- Add ingestion API (Node-side)
- Run both: Python filesystem writes AND HTTP ingestion
- Validate HTTP path works

### Phase 2:
- Remove Python filesystem writes
- Python uses HTTP only

### Phase 3:
- Validate in Docker
- Test container separation

### Phase 4:
- Deploy to cloud platform
- Monitor for state loss or duplication

---

## The Achievement

**Before PRL-1.1:**
> PRL-1 works locally but breaks in cloud due to hidden filesystem coupling.

**After PRL-1.1:**
> PRL-1 works anywhere: Docker, Kubernetes, Railway, VPS, etc.
> Python is stateless, Node owns all state.
> Clean HTTP boundary eliminates coupling.
> Ready for production cloud deployment.

---

## Summary

PRL-1.1 is not a feature. It's a **topology fix**.

It takes the crash-safe, replay-safe, duplicate-safe system (PRL-1) and makes it **cloud-safe** by removing the hidden assumption that Python and Node share a filesystem.

After PRL-1.1:
- ✅ Fully cloud-native architecture
- ✅ Stateless AI trader (can scale)
- ✅ Stateful execution system (single source of truth)
- ✅ Clean HTTP boundary (no coupling)
- ✅ Ready for production deployment

The next step (PRL-2) can now focus on **distributed scaling** rather than fixing fundamental architecture problems.
