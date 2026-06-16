# AI Trader Integration Status

**Updated**: 2026-06-15  
**Current Master**: 7f84b44 (chart rendering fixed)  
**Agent Lane**: `opus/` prefix  

---

## Mission

Integrate and complete the **Independent AI Trader** system to production-ready state.

**What's Done**:
- ✅ Chart rendering fixed (candles visible on load, loading spinner working)
- ✅ PRL-1/1.1/1.2/1.3 (fault tolerance, cloud boundary, Alpaca execution, risk governor) merged to master
- ✅ Server infrastructure stable (port 4177 + 4178 dual-boot)
- ✅ Event queue consumer async bug fixed (4ee68c3)

**What's Needed**:
- 🔲 AI Trader service integration tests (market data → execution)
- 🔲 Error handling for edge cases (timeouts, invalid signals, etc.)
- 🔲 Monitoring/observability for trader decisions
- 🔲 WCAG accessibility Phase 2 (if time permits)

---

## Architecture

```
AI Trader Service (Python)
  → python bridge (ai-trader-bridge.py)
  → POST /api/trading/independent-ai/order (Node endpoint, routes/trading.js)
  → execution router (execution-router.js)
  → event queue (persistent-event-queue.js)
  → event consumer (event-queue-consumer.js, 250ms heartbeat)
  → Alpaca adapter (alpaca-execution-adapter.js)
  → Risk Governor gates (risk-governor.js, 7 checks)
  → Order execution (paper trading mode)
```

---

## Work Items

### Phase A: AI Trader Integration (CRITICAL)

1. **Review Python bridge** (`ai-trader-bridge.py`)
   - [ ] Check timeout handling (5s max)
   - [ ] Validate JSON before passing to Node
   - [ ] Log errors with full context

2. **Complete error handling**
   - [ ] Guard against invalid signal format
   - [ ] Validate confidence in [0,100]
   - [ ] Reject conflicts with position size limits
   - [ ] Handle Alpaca connection failures

3. **Integration tests**
   - [ ] Market data → AI decision → event queue → Alpaca (mocked)
   - [ ] Timeout/crash recovery
   - [ ] Risk governor blocks
   - [ ] Concurrent signal serialization

4. **Observability**
   - [ ] Signal latency metrics
   - [ ] Python process health tracking
   - [ ] Bridge communication reliability

### Phase B: Accessibility (IF TIME)

- [ ] Add heading hierarchy
- [ ] Text labels for direction (▲/▼ + text)
- [ ] Modal focus trapping
- [ ] Error announcements
- [ ] Screen reader test (NVDA)

### Phase C: Polish (NICE-TO-HAVE)

- [ ] API documentation
- [ ] Circuit breaker for Python service
- [ ] Chart rendering performance optimization

---

## Git Workflow

```bash
git checkout -b opus/ai-trader-integration
git commit -m "test(ai-trader): add integration test..."
git push origin opus/ai-trader-integration
gh pr create --title "AI Trader Integration Phase A" --body "..."
```

**Rules**:
- Only ONE open PR in `opus/` lane at a time
- All commits must have clear messages (no "wip", "temp")
- Rebase on master before merge
- No parallel agents — direct work only

---

## Files to Review

**Core Files**:
- `apps/lantern-garage/core/event-queue-consumer.js` (PRL-1 heartbeat)
- `apps/lantern-garage/core/execution-router.js` (PRL-1.1 boundary)
- `apps/lantern-garage/core/alpaca-execution-adapter.js` (PRL-1.2)
- `apps/lantern-garage/core/risk-governor.js` (PRL-1.3)

**AI Trader Files**:
- `apps/lantern-garage/lib/ai-trader-bridge.py`
- `apps/lantern-garage/services/independent-ai-trader-service.py`
- `apps/lantern-garage/routes/trading.js` (actual route handlers — NOT server.js)
  - `POST /api/trading/independent-ai/order` (line ~581)
  - `GET  /api/trading/independent-ai/status` (line ~651)
  - `GET  /api/ai-trader/signals` + `/signals/demo` (proxied, line ~152)

**Testing**:
- `tests/test_ai_trader_integration.py` (create this)
- `npm run test:api --prefix apps/lantern-garage`

---

## Success Criteria

✅ `POST /api/trading/independent-ai/order` accepts signals, returns valid orders  
✅ Signals flow through queue → router → Alpaca (paper mode)  
✅ All errors caught, logged, auditable  
✅ Integration tests pass  
✅ PR merged to master without conflicts  
✅ No console errors in browser/server  
✅ Risk governor can block trades if capital limits violated  

---

## Environment

```bash
# Check .env has:
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets (paper only!)
ALPACA_MODE=paper

# Start dual-boot
make quickstart

# Or single server
npm run dev --prefix apps/lantern-garage

# Run tests. NOTE on the full `tests/` tree:
#   - test_p4_integration_full_loops.py STILL fails at collection (imports
#     ThreeDoorsGameState, which no longer exists in src/three_doors_engine.py) ->
#     keep it ignored until that import is fixed.
#   - Always pass --timeout so any future hang NAMES the test instead of blocking
#     the whole run (on Windows pytest-timeout's thread method can't unwind a
#     lock-deadlock, so an unguarded hang looks like the suite running forever).
python -m pytest tests/ -q --tb=line --timeout=30 --timeout-method=thread \
  --ignore=tests/test_anti_entropy_memory.py \
  --ignore=tests/test_audit_chain.py \
  --ignore=tests/test_discord_bot.py \
  --ignore=tests/test_discord_voice_gate.py \
  --ignore=tests/test_p4_integration_full_loops.py
# Last verified (2026-06-15): 496 passed, 3 failed, 6 skipped, 1 xfailed.
# The 3 failures are PRE-EXISTING and unrelated to AI-trader work: test_oauth_server.py
# + test_mcp_server.py expect MCP_OAUTH_PORT / JWT secret in .env.example (missing).
# (A prior deadlock in src/convergence_io_engine.py SlotManager.flush() was fixed
#  2026-06-15 by switching self._lock to RLock; test_convergence_io_engine.py passes.)

npm run test:api --prefix apps/lantern-garage   # requires server running on 4177
```

---

## Read First

1. `QUICKSTART.md` — startup, dual-boot
2. `AGENTS.md` — git workflow, monoworkstream
3. `PRL_1_3_RISK_GOVERNOR.md` — capital protection
4. `WCAG_ACCESSIBILITY_AUDIT.md` — accessibility findings

---

**Ready to build. Let's make the trader production-safe. 🚀**
