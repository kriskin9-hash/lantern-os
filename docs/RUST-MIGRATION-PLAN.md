# Rust Migration Plan — RAM & Performance Optimization

**Date**: 2026-06-13  
**Status**: Draft  
**Priority**: High

---

## Executive Summary

Current Python components have unbounded memory growth and performance bottlenecks. This plan migrates critical memory-intensive components to Rust, leveraging existing `csf_rust` and `cadd_rust` infrastructure.

**Current Issues**:
- Discord bot: Unbounded per-guild state, global catalog, session memory
- Convergence engine: Unbounded caches, no LRU eviction
- Memory engine: Unbounded inverted indexes, full registry scans
- Trading agents: Bounded deques (already optimized)

**Target State**:
- Bounded caches with LRU eviction
- Zero-copy streaming via memmap2
- Parallel compression via rayon
- Rust FFI bridges for Python integration

---

## Current Rust Infrastructure

### csf_rust (v1.0.1)
- **Purpose**: Convergence-Fitted Searchable Binary Archive
- **Features**: zstd compression, bitvec, memmap2, rayon parallel compression
- **Status**: CLI tool ready, needs Python FFI bridge

### cadd_rust (v0.2.1)
- **Purpose**: Capture, Assess, Distill, Dock — brand asset validation
- **Features**: Image processing, regex, walkdir, xxhash
- **Status**: CLI tool ready, needs Python FFI bridge

---

## Phase 1: Discord Bot Memory Management

### Issue Analysis

**bot_v2.py**:
```python
_LOUNGE_STATES: dict[int, LoungeState] = {}  # Unbounded per-guild state
_LOUNGE_CATALOG: dict[str, list[LoungeTrack]] = {}  # Global catalog (hundreds of tracks)
state.queue: list[LoungeTrack]  # Unbounded queue
state._pool: dict[str, list[LoungeTrack]]  # Duplicate pool storage
```

**memory_layer.py**:
```python
MemoryStore.sessions: Dict[int, SessionMemory] = {}  # Unbounded sessions
SessionMemory.messages: List[Dict]  # Unbounded message history
```

### Migration Plan

#### 1.1 Rust Lounge State Manager
**New crate**: `src/discord_rust/Cargo.toml`

**Features**:
- Bounded LRU cache for guild states (max 100 guilds)
- Catalog streaming via memmap2 (no full load into RAM)
- Queue size limits (max 50 tracks per guild)
- Connection pooling for archive.org HTTP

**Python FFI**:
```python
# discord_lounge_bot/lounge_state_rust.py
from ctypes import CDLL, c_int, c_char_p

lib = CDLL("target/release/discord_rust.dll")

# Rust functions:
# - lounge_state_get(guild_id: i32) -> *mut LoungeState
# - lounge_state_set_queue_limit(guild_id: i32, limit: i32)
# - lounge_catalog_stream(mode: *const c_char) -> *mut CatalogStream
```

#### 1.2 Rust Session Memory Manager
**Features**:
- Bounded LRU cache for sessions (max 1000 sessions)
- Message history limit per session (max 100 messages)
- TTL-based eviction (24h inactive sessions)
- CSF export path via existing csf_rust

**Python FFI**:
```python
# discord_lounge_bot/memory_rust.py
# Rust functions:
# - session_get(user_id: i64) -> *mut SessionMemory
# - session_add_message(user_id: i64, content: *const c_char)
# - session_end(user_id: i64)
# - session_export_csf(user_id: i64) -> *const c_char
```

### Effort Estimate
- **Rust implementation**: 3 days
- **Python FFI bridge**: 1 day
- **Testing**: 1 day
- **Total**: 5 days

---

## Phase 2: Convergence Engine Caches

### Issue Analysis

**convergence_io_engine.py**:
```python
TesseractConvergence._phase_cache: Dict[str, PhaseResult]  # Unbounded
TesseractConvergence._persona_cache: Dict[str, str]  # Max 500 (already bounded)
TesseractConvergence._circuit_cache: Dict[str, CircuitBreaker]  # Unbounded
```

### Migration Plan

#### 2.1 Rust Phase Cache
**New crate**: `src/convergence_rust/Cargo.toml`

**Features**:
- Bounded LRU cache for phase results (max 1000 entries)
- Repo hash-based cache invalidation
- Persistent cache via csf_rust storage
- TTL-based eviction (1h)

**Python FFI**:
```python
# convergence_rust/phase_cache.py
# Rust functions:
# - phase_cache_get(repo_hash: *const c_char, phase: *const c_char) -> *const c_char
# - phase_cache_set(repo_hash: *const c_char, phase: *const c_char, result: *const c_char)
# - phase_cache_invalidate(repo_hash: *const c_char)
```

#### 2.2 Rust Circuit Breaker Cache
**Features**:
- Bounded cache for circuit breakers (max 100 circuits)
- State persistence via csf_rust
- Automatic recovery after cooldown

**Python FFI**:
```python
# Rust functions:
# - circuit_get(name: *const c_char) -> *mut CircuitBreaker
# - circuit_record_success(name: *const c_char)
# - circuit_record_failure(name: *const c_char)
```

### Effort Estimate
- **Rust implementation**: 2 days
- **Python FFI bridge**: 1 day
- **Testing**: 1 day
- **Total**: 4 days

---

## Phase 3: Memory Engine Indexes

### Issue Analysis

**csf/memory_engine.py**:
```python
MemoryEngine._keyword_index: Dict[str, Set[str]]  # Unbounded
MemoryEngine._entity_index: Dict[str, Set[str]]  # Unbounded
_load_index()  # Full registry scan on startup O(n)
```

### Migration Plan

#### 3.1 Rust Inverted Index
**Extend**: `src/csf_rust/` (add index module)

**Features**:
- Bounded LRU index (max 100k entries per index type)
- Incremental index updates (no full scans)
- Zero-copy index queries via memmap2
- Fused multi-signal scoring in Rust

**Python FFI**:
```python
# csf_rust/index.py
# Rust functions:
# - index_update(record_id: *const c_char, keywords: *const c_char, entities: *const c_char)
# - index_query(keywords: *const c_char, entities: *const c_char) -> *mut CandidateSet
# - index_multi_signal_score(record: *const c_char, query: *const c_char) -> f32
```

#### 3.2 Rust Registry Streaming
**Features**:
- Streaming JSONL parser (no full load)
- Parallel record processing via rayon
- Checksum validation via xxhash-rust

**Python FFI**:
```python
# Rust functions:
# - registry_stream(path: *const c_char) -> *mut RegistryStream
# - registry_next(stream: *mut RegistryStream) -> *const c_char
# - registry_close(stream: *mut RegistryStream)
```

### Effort Estimate
- **Rust implementation**: 4 days
- **Python FFI bridge**: 1 day
- **Testing**: 2 days
- **Total**: 7 days

---

## Phase 4: Python Optimizations (Immediate)

### 4.1 Discord Bot Immediate Fixes
**File**: `src/discord_lounge_bot/bot_v2.py`

```python
# Add queue size limits
MAX_QUEUE_SIZE = 50
MAX_CATALOG_TRACKS = 200

def _lounge_refill(state: LoungeState, mode: str) -> None:
    pool = list(_LOUNGE_CATALOG.get(mode, []))
    if not pool:
        return
    random.shuffle(pool)
    # Limit queue size
    if len(state.queue) < MAX_QUEUE_SIZE:
        state.queue.extend(pool[:MAX_QUEUE_SIZE - len(state.queue)])

# Add session cleanup
MAX_SESSION_AGE_HOURS = 24
def _cleanup_old_sessions():
    now = time.time()
    for user_id, session in list(memory_store.sessions.items()):
        age = now - session.created_at.timestamp()
        if age > MAX_SESSION_AGE_HOURS * 3600:
            memory_store.end_session(user_id)
```

### 4.2 Convergence Engine Immediate Fixes
**File**: `src/convergence_io_engine.py`

```python
# Add cache size limits
_MAX_PHASE_CACHE_SIZE = 1000
_MAX_CIRCUIT_CACHE_SIZE = 100

# In TesseractConvergence.__init__:
self._phase_cache: Dict[str, PhaseResult] = {}
self._phase_cache_max = _MAX_PHASE_CACHE_SIZE

# Add LRU eviction
def _evict_phase_cache(self):
    if len(self._phase_cache) >= self._phase_cache_max:
        # Remove oldest 10%
        keys_to_remove = list(self._phase_cache.keys())[:len(self._phase_cache) // 10]
        for k in keys_to_remove:
            del self._phase_cache[k]
```

### 4.3 Memory Engine Immediate Fixes
**File**: `src/csf/memory_engine.py`

```python
# Add index size limits
_MAX_INDEX_SIZE = 100_000

def _update_index(self, record: MemoryRecord) -> None:
    for kw in record.keywords:
        if len(self._keyword_index[kw.lower()]) >= _MAX_INDEX_SIZE:
            continue  # Skip index update if full
        self._keyword_index[kw.lower()].add(record.memory_id)
    for ent in record.entities:
        if len(self._entity_index[ent.lower()]) >= _MAX_INDEX_SIZE:
            continue
        self._entity_index[ent.lower()].add(record.memory_id)
```

### Effort Estimate
- **Discord bot fixes**: 2 hours
- **Convergence fixes**: 1 hour
- **Memory engine fixes**: 1 hour
- **Testing**: 2 hours
- **Total**: 6 hours

---

## Implementation Order

1. **Phase 4** (Immediate Python fixes) — 6 hours
2. **Phase 1** (Discord bot Rust) — 5 days
3. **Phase 2** (Convergence Rust) — 4 days
4. **Phase 3** (Memory engine Rust) — 7 days

**Total Timeline**: ~16 working days

---

## Success Metrics

- **RAM usage**: < 500MB for Discord bot (current: unbounded)
- **Cache hit rate**: > 80% for phase cache
- **Index query time**: < 10ms for keyword/entity queries
- **Queue latency**: < 100ms for lounge track advance

---

## Dependencies

- Rust 1.70+ (already installed)
- Python 3.11+ (already installed)
- PyO3 for Python-Rust FFI (new dependency)
- Maturin for building Python wheels (new dependency)

---

## Risk Mitigation

- **Fallback**: Keep Python implementations as fallback if Rust fails
- **Gradual rollout**: Feature flags for Rust components
- **Monitoring**: Add RAM usage metrics to health check
- **Testing**: Load tests with 1000+ guilds, 10k+ records

---

## Next Actions

1. Implement Phase 4 immediate fixes (today)
2. Create `src/discord_rust/` crate structure
3. Set up PyO3 build pipeline
4. Write unit tests for Rust components
5. Integration tests with Python bot

---

**Last Updated**: 2026-06-13  
**Owner**: Lantern OS Project  
**Review**: Pending
