# Lantern OS — Scientific Verification Protocol

**Purpose:** Prevent false confidence claims by agents. All fixes must pass 12-step convergence verification before claiming "done."

## The Problem This Solves

Agent X claims: "Fixed Dream Chat!"  
Reality: Chat still broken, null errors remain.  
Cause: Agent skipped verification steps and relied on theoretical fixes.

## 12-Step Convergence Verification Cycle

### Phase 1: OBSERVE (Baseline Metrics)
- [ ] **Step 1: Gather initial state**
  - Console error count: `grep console.error`
  - API responses: GET `/version.json` returns 200
  - DOM readiness: `document.readyState` logged
  - Network: check no 404/500 errors

- [ ] **Step 2: Document failures**
  - Screenshot browser console
  - List all JavaScript errors with line numbers
  - Record HTTP error codes with endpoints
  - Example: `"Cannot set properties of null (setting 'className') at line 134"`

### Phase 2: HYPOTHESIZE (Root Cause Analysis)
- [ ] **Step 3: Propose mechanism**
  - Is it a timing issue? (DOM not ready)
  - Is it a missing element? (selector returns null)
  - Is it a logic error? (wrong condition)
  - State your hypothesis with specific file:line references

- [ ] **Step 4: Check prerequisites**
  - Are all required HTML elements present?
  - Is the script tag at end of HTML?
  - Are event listeners waiting for DOM ready?
  - Verify with: `grep -n 'id="messages"' dream-chat.html`

### Phase 3: ISOLATE (Minimal Reproduction)
- [ ] **Step 5: Create isolated test**
  - Extract ONE failing code path
  - Test it independently from full app
  - Example: `console.log(document.getElementById("messages"))` in browser console
  - Should NOT be null after page load

- [ ] **Step 6: Verify fix in isolation**
  - Apply proposed fix to isolated test
  - Test again: does it now return the element?
  - Do not proceed if this fails

### Phase 4: VERIFY (Integration Test)
- [ ] **Step 7: Run E2E user flow**
  - Open Dream Chat in browser
  - Type a test message: "hello"
  - Send the message
  - Observe: does it appear in chat?
  - Observe: is it not null? Does agent respond?

- [ ] **Step 8: Check error logs**
  - Open DevTools console
  - **MUST see zero JavaScript errors**
  - If even one error remains → NOT DONE
  - Document any warnings that are acceptable

### Phase 5: MEASURE (Metrics)
- [ ] **Step 9: Compare before/after**
  - Before fix: X errors in console
  - After fix: 0 errors in console
  - Before fix: API calls fail silently
  - After fix: API calls succeed, responses logged

- [ ] **Step 10: Validate acceptance criteria**
  - User can send a message → YES/NO
  - Chat displays response → YES/NO
  - No JavaScript errors → YES/NO
  - Performance acceptable (< 2s latency) → YES/NO
  - **Must have: 4/4 YES before claiming done**

### Phase 6: DOCUMENT (Knowledge Transfer)
- [ ] **Step 11: Record methodology**
  - What was the actual root cause?
  - Which file/line was wrong?
  - What was the fix?
  - Why did I initially miss this?
  - Example: "Root cause was missing DOMContentLoaded wrapper. Dream-chat.js tried to access #messages element at module scope before DOM loaded. Fix: deferred script loading via HTML wrapper."

- [ ] **Step 12: Prevent recurrence**
  - Add automated test for this scenario
  - Document assumption that broke (e.g., "assumed script tag placement was sufficient")
  - Train future agents on this failure mode

## Example: Dream Chat Verification (CORRECT WAY)

### Step 1: Baseline
```
ERROR BEFORE FIX:
- Console: 47 errors
- "Cannot set properties of null (setting 'className')" ×8
- "Cannot read properties of null (reading 'contains')" ×12
- API calls: 500 errors on /api/agents
```

### Step 3: Hypothesis
"Root cause: dream-chat.js runs before DOM loads. Script tag must defer execution until DOMContentLoaded."

### Step 5: Isolated Test
```javascript
// Open console, run this:
console.log("DOM ready?", document.readyState);
console.log("Messages element:", document.getElementById("messages"));
// Before fix: returns "loading", null
// After fix: returns "complete", <div id="messages">
```

### Step 7: E2E Test
1. Refresh page
2. Type: "test message"
3. Press Enter
4. Verify: message appears in chat
5. Verify: agent responds (no error)
6. Verify: console is clean (0 errors)

### Step 10: Acceptance
```
✓ User can send message
✓ Chat displays response  
✓ Zero JavaScript errors
✓ Latency < 2s
RESULT: PASS ✓
```

### Step 11: Document
"Root cause: dream-chat.js accessed DOM elements at module scope before DOM was loaded. Although script tag was at end of HTML, code executed immediately. Fix: wrapped script loading in inline DOMContentLoaded handler in HTML. Applied to dream-chat.html, lines 461-472."

### Step 12: Prevent
- Added regression test: verify `console.error` count = 0 on page load
- Document: "Script tag placement is not sufficient; must defer via DOMContentLoaded"
- Added comment in code explaining why wrapper is necessary

## Red Flags (Stop and Verify)

If you catch yourself thinking ANY of these, you've skipped steps:

- ❌ "This should be fixed now" (without testing)
- ❌ "The logic looks right" (without running it)
- ❌ "I added error handling, so it's safer" (without proving errors are gone)
- ❌ "The fix is obvious" (without isolation testing)
- ❌ "It worked in theory" (without E2E test)

**Correct thinking:**
- ✅ "I observed X. I hypothesize Y. Here's my isolated test. Results: ✓"
- ✅ "Before: N errors. After: 0 errors. E2E passes: ✓"
- ✅ "Root cause documented. Future agents will avoid this."

## When to Use This Protocol

**ALWAYS for:**
- Security fixes
- Null/error handling
- DOM/timing issues
- API integration
- User-facing features

**Quick-check version (all 12 steps, 2 min):**
1. Observe (30s)
2. State hypothesis (30s)
3. Isolated test (30s)
4. E2E test (30s)
5-6. Document (30s)

**Never skip to:** "I think it's fixed"

---

**Enforced by:** Convergence I/O Engine + Agent Fleet  
**Escalates to:** Code Review gate if verification missing  
**Prevents:** "Worked for me" → "Actually broken in production"
