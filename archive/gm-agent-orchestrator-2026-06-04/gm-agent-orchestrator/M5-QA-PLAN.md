# M5 Attestation: QA Plan & Bayesian Confidence Model

**Status:** Code written → needs testing & verification before merge  
**Founder Role:** Pilot user + QA decision-maker  
**Goal:** Measure actual confidence (not optimistic claims)

---

## Bayesian Confidence Model: What's Actually Ready?

### Prior Beliefs (Before Testing)
- Code written: 380 lines attestation + 50 lines UI integration
- Unit test (standalone): Passed (Ollama health check worked)
- Claims made: "Ready for Family A"
- **Actual confidence before founder testing: 35%** (unverified in real use)

### What Could Go Wrong (Failure Modes)

| Failure Mode | Probability | Impact | Detection |
|--------------|-------------|--------|-----------|
| M5 thread crashes on startup | 15% | High | Test launch |
| Ollama health endpoint wrong | 10% | High | Test fallback |
| Ledger file permission denied | 8% | High | Test write |
| TkInter status label disappears | 12% | Medium | Visual check |
| Thread doesn't stop on window close | 20% | Medium | Test close |
| Chat hangs when M5 tests run | 18% | High | Stress test |
| Memory leak in background thread | 12% | Medium | 24hr run |
| Config parsing fails | 5% | High | Test config |
| Attestation records wrong format | 8% | Low | Check ledger |

### Success Criteria (Founder Sign-Off)

After testing, confidence rises based on which tests pass:

- ✅ **Launch test:** App starts without crash → +15%
- ✅ **Chat works:** Type message, get response → +20%
- ✅ **M5 records:** Ledger has entries after 5 min → +15%
- ✅ **Status updates:** Indicator shows "● Operational" → +10%
- ✅ **Fallback works:** Switch provider, chat continues → +20%
- ✅ **24hr stability:** No crashes/memory leaks → +15%
- ✅ **Window closes gracefully:** Attestation stops cleanly → +10%

---

## Testing Checklist (Founder as Pilot)

### Phase 1: Launch & Basic Function (15 min)

**Test 1.1: Does it start?**
```bash
cd scripts/
python3 lantern-chat-ui.py
```
**Expected:** TkInter window opens, no errors  
**Pass:** Yes ☐ / No ☐ / Partial ☐

**Test 1.2: Can you see the UI?**
- Header: "Lantern Chat" visible ☐
- Status bar shows: "Ready ● Operational" ☐
- M5 message: "Attestation active (tests every 5 minutes)" ☐
- Input field is active (cursor visible) ☐

**Test 1.3: Can you type?**
- Type in input field: "hello" ☐
- Send button clickable ☐
- Message appears in chat ☐

---

### Phase 2: Chat Functionality (10 min)

**Test 2.1: Does Ollama respond?**
```
You: what is 2+2
Expected response: Something like "4" or "The answer is 4"
```
**Result:** ☐ Works ☐ Timeout ☐ Error

**Test 2.2: Does streaming work?**
- Response appears word-by-word (not all at once) ☐
- Status bar updates: "Ready (1 messages)" ☐

**Test 2.3: Can you ask again?**
```
You: tell me a joke
```
**Result:** ☐ Works ☐ Timeout ☐ Error

---

### Phase 3: M5 Attestation (5 min + wait)

**Test 3.1: Ledger exists**
```bash
cat ~/.lantern/telemetry/attestation-ledger.jsonl | head -5
```
**Expected:** JSON entries with timestamp, provider, success  
**Result:** ☐ Exists ☐ Empty ☐ Not found ☐ Permission error

**Test 3.2: Capability state exists**
```bash
cat ~/.lantern/telemetry/capability-state.json
```
**Expected:** {"ollama": {"status": "operational", ...}}  
**Result:** ☐ Exists ☐ Empty ☐ Not found

**Test 3.3: Wait 6 min, check ledger grows**
- Timestamp before: `2026-05-25T13:20:00`
- Wait 6 minutes...
- Timestamp after: `2026-05-25T13:26:XX` (2+ new entries) ☐

---

### Phase 4: Status Indicator (Visual)

**Test 4.1: Does indicator match reality?**
- Ollama is running ✓
- Status bar shows: "● Operational" ☐ or "○ Unknown" ☐

**Test 4.2: Turn off Ollama, wait 3 tests (~15 min)**
```bash
# In another terminal, stop Ollama
# Keep Lantern chat running
```
**Expected:** After ~15 min, indicator changes to "⚠ Degraded (3 failures)"  
**Result:** ☐ Changes ☐ Stays same ☐ Crashes

---

### Phase 5: Fallback Chain (if Claude API key available)

**Test 5.1: Verify Claude config (optional)**
```bash
grep -A 2 'api_key' ~/.lantern/llm-configurations.json | head -3
```
**Result:** ☐ Real key present ☐ Placeholder ☐ Not set

**Test 5.2: If real key, test fallback**
- Edit config: set primary to "claude", fallback to "ollama"
- Type message
**Expected:** Claude responds (fast), message logged  
**Result:** ☐ Works ☐ Timeout → fallback works ☐ Error

---

### Phase 6: Window Close & Cleanup (2 min)

**Test 6.1: Close window gracefully**
- Click X button on window
**Expected:** App exits, no error messages  
**Result:** ☐ Clean exit ☐ Hangs ☐ Error

**Test 6.2: Check cleanup**
```bash
ps aux | grep lantern
```
**Expected:** No lingering Python processes  
**Result:** ☐ Clean ☐ Process remains ☐ Multiple processes

**Test 6.3: Check attestation stopped**
```bash
tail -1 ~/.lantern/telemetry/attestation-ledger.jsonl
```
**Expected:** Last entry >5 min ago (no new tests after close)  
**Result:** ☐ Stopped ☐ Still running ☐ Can't tell

---

### Phase 7: Stress Test (Optional, 30 min)

**Test 7.1: Rapid-fire messages**
```
You: 1
You: 2
You: 3
You: 4
You: 5
(5 messages in ~30 sec, while M5 tests run in background)
```
**Result:** ☐ All work ☐ Some hang ☐ Crash ☐ OOM

**Test 7.2: Long message**
```
You: [copy/paste 1000 word Lorem Ipsum]
```
**Result:** ☐ Works ☐ Timeout ☐ Crash

**Test 7.3: Memory check**
```bash
# While chat is running:
ps aux | grep python | grep lantern
# Look for memory usage (RSS column)
```
**Expected:** <300 MB  
**Actual:** ___ MB

---

## Verification Checklist: Each Test Phase

After completing each phase, founder marks:

- [ ] Phase 1 PASSED (Launch + UI)
- [ ] Phase 2 PASSED (Chat works)
- [ ] Phase 3 PASSED (M5 ledger + attestation)
- [ ] Phase 4 PASSED (Status indicator)
- [ ] Phase 5 PASSED (Fallback, if tested)
- [ ] Phase 6 PASSED (Clean shutdown)
- [ ] Phase 7 PASSED (Stress test, optional)

---

## Bayesian Update: Confidence After Testing

**Initial confidence before testing:** 35%

**After Phase 1 (Launch):** 
- If PASS: +15% → **50%**
- If FAIL: -20% → **15%** (redo code)

**After Phase 2 (Chat):**
- If PASS: +20% → **70%**
- If FAIL: -25% → **25%** (blocking issue)

**After Phase 3 (M5 Attestation):**
- If PASS: +15% → **85%**
- If FAIL: -30% → **40%** (critical for patent)

**After Phase 4 (Status Indicator):**
- If PASS: +10% → **95%**
- If FAIL: -15% → **70%** (UI issue, not blocking)

**After Phase 6 (Clean Shutdown):**
- If PASS: +5% → **100%** ✓ READY TO MERGE
- If FAIL: -20% → **65%** (fix threading)

**After Phase 7 (Stress Test, optional):**
- If PASS: +0% (confirms robustness)
- If FAIL on memory: -10% (memory leak to fix)

---

## What Blocks Merge to Master?

**HARD BLOCKERS (Must fix before merge):**
- ✗ App crashes on launch (Phase 1)
- ✗ Chat doesn't work (Phase 2)
- ✗ M5 doesn't record anything (Phase 3)
- ✗ Window doesn't close cleanly (Phase 6)

**SOFT BLOCKERS (Can merge with caveat):**
- ⚠ Memory leak detected (Phase 7) → document known issue
- ⚠ Status indicator wrong (Phase 4) → cosmetic, doesn't affect function

**ACCEPTABLE FAILURES (Don't block):**
- Optional fallback test with Claude API (Phase 5) → requires API key
- Stress test hangs (Phase 7) → rare use case

---

## Founder Decision Point

After all testing, founder decides:

### Option A: APPROVED FOR MERGE
```
Confidence: >90%
Founder: "I tested it, it works, merge to master"
Action: Merge commit
Next: Prepare for Family A launch (May 26)
```

### Option B: NEEDS FIXES
```
Confidence: 50-90%
Founder: "Works but [specific issue], fix this first"
Action: Back to development
Fixed code → retest Phase N
Then → remerge decision
```

### Option C: BLOCKED
```
Confidence: <50%
Founder: "Doesn't work, rewrite this part"
Action: Revert commit, redesign module
```

---

## Post-Test Sign-Off Template

**Fill this in after all testing:**

```
M5 ATTESTATION QA SIGN-OFF
Founder/Pilot: _______________
Date: 2026-05-25
Testing duration: ___ hours
Platforms tested: Windows 11 ☐ / Mac ☐ / Linux ☐
Provider tested: Ollama ☐ / Claude ☐ / LM Studio ☐

Phase 1 (Launch): PASS ☐ / FAIL ☐ / PARTIAL ☐
Phase 2 (Chat): PASS ☐ / FAIL ☐ / PARTIAL ☐
Phase 3 (M5): PASS ☐ / FAIL ☐ / PARTIAL ☐
Phase 4 (UI): PASS ☐ / FAIL ☐ / PARTIAL ☐
Phase 5 (Fallback): PASS ☐ / SKIP ☐ / FAIL ☐
Phase 6 (Shutdown): PASS ☐ / FAIL ☐ / PARTIAL ☐
Phase 7 (Stress): PASS ☐ / SKIP ☐ / FAIL ☐

Critical issues found:
1. _________________________________
2. _________________________________

Known acceptable issues:
1. _________________________________

Founder confidence: ___% → Ready to merge: YES ☐ / NO ☐

Signature: _________________ Date: __________
```

---

## Why This Matters

**Without testing:**
- "M5 is done" = 35% confidence
- Merge → Family A uses untested code
- Fails in production → Family A loses trust

**With rigorous testing:**
- Each phase reveals real issues
- Fix issues → confidence rises
- Merge → Production-ready code
- Family A has reliable system

**This is how you avoid false readiness claims.**

---

**Next: Founder tests live. Report results here. Then decide merge.**
