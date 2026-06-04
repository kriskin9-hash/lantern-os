# Dashboard Design Contract (HARD CONSTRAINTS)

**Authority:** User specification, enforced by QA checklist  
**Status:** BINDING - No deviations allowed

---

## Zone Layout (IMMUTABLE)

```
┌─────────────────────────────────────────────┐
│  NOTIFICATIONS BAR (collapsing/self-hiding) │
├─────────────────────┬──────────────────────┤
│                     │                      │
│  AGENTS GRID        │  QUEUE STATUS        │
│  (Primary Content)  │  (Sidebar)           │
│  Left column 70%    │  Right column 30%    │
│                     │                      │
│  - Cards clickable  │  - Real-time counts  │
│  - Expand full-page │  - Health indicator  │
│  - Context actions  │  - Color coded       │
│                     │                      │
├─────────────────────┴──────────────────────┤
│  ACTIVITY LOG (bottom)                     │
└─────────────────────────────────────────────┘
```

## Required Features (CHECKED)

### Notifications Bar ✅
- [ ] Position: Fixed at top
- [ ] Behavior: Collapses when clicked (✕ button)
- [ ] Auto-hide: Disappears when system healthy
- [ ] Show: When issues exist (blockers, failures)
- [ ] Message: Human language, actionable
- [ ] Not a modal - doesn't block interaction

### Agents Grid (Primary Content) ✅
- [ ] Position: Top-left, 70% width
- [ ] Display: Responsive grid (auto-fit, minmax 280px)
- [ ] Cards clickable: Click anywhere on card
- [ ] Expand action: Click card → expands to full width
- [ ] Collapse: Click ✕ or click outside
- [ ] State colors:
  - 🟢 Green = Ready/Healthy
  - 🔵 Blue = Working/Busy
  - 🟡 Amber = Idle
  - 🔴 Red = Stuck/Blocked

### Expanded Agent View (Full-Width) ❌ REQUIRED
- [ ] Show full panel width on click
- [ ] Content includes:
  - Agent name + type
  - Current state + status badge
  - Current task (if any)
  - Next 3 actions available
- [ ] Context-sensitive actions:
  - If IDLE: Show "⚡ Wake" button
  - If WORKING: Show "⏸ Pause" button
  - If BLOCKED: Show "❌ Issue: [reason]" + "Fix Steps" link
  - If ERROR: Show error details + "Retry" button
- [ ] Blocker remediation:
  - [ ] If blocked: Show "What's wrong"
  - [ ] If blocked: Show "How to fix" (step-by-step)
  - [ ] If blocked: Show "Who to ask" (escalation)
- [ ] Close button (✕) to collapse
- [ ] Back button to go back to grid

### Queue Status Sidebar (Real-time) ✅
- [ ] Position: Right column, 30% width
- [ ] Always visible (no collapse)
- [ ] Shows real counts:
  - 📋 TO DO
  - ⚙️ WORKING
  - ✅ COMPLETED
  - 🚫 BLOCKED
  - ❌ FAILED
- [ ] Health indicator:
  - Green dot + text = "System Healthy"
  - Amber dot + text = "Issues Found"
  - Red dot + text = "Needs Attention"
- [ ] Colors semantic:
  - Done = Green (#10b981)
  - Blocked = Amber (#f59e0b)
  - Failed = Red (#ef4444)

### Activity Log (Bottom) ✅
- [ ] Shows recent events
- [ ] Max 20 items visible
- [ ] Scrollable if overflow
- [ ] Icons: success (green), warning (amber), error (red)
- [ ] Format: Title + description + timestamp

---

## Non-Technical User Test ✅

**Contract:** If user's sister or wife looked at dashboard, she should know:
1. What's the problem? (from notification bar color + message)
2. What's the status? (from queue numbers + health indicator color)
3. What do I do? (from blocker remediation steps or "system is working")

**Acceptance:** She can answer all 3 without technical knowledge

---

## Context-Sensitive Actions (HARD REQUIREMENT)

Actions shown depend on agent state:

```
Agent State → Actions Shown
───────────────────────────

IDLE        → [⚡ Wake] [Details →]
WORKING     → [⏸ Pause] [Details →]
BLOCKED     → [❌ Blocked] [See Fix Steps] [Escalate]
ERROR       → [❌ Error] [View Details] [Retry]
STUCK       → [⚠️ Stuck] [Diagnose] [Escalate]
```

No generic "unknown" state. Every state has specific actions.

---

## Colors (LOCKED)

| Meaning | Hex | Use Case |
|---------|-----|----------|
| Healthy | #10b981 | Working, Done, Ready |
| Working | #3b82f6 | Currently processing |
| Idle | #f59e0b | Waiting for work |
| Blocked | #f59e0b | Waiting on external (auth, creds) |
| Failed | #ef4444 | Error, needs attention |
| Default | #94a3b8 | Neutral, no action |

---

## QA Checklist (ENFORCED)

Before marking complete, verify ALL of:

### Layout
- [ ] Notifications bar is fixed at top
- [ ] Agents grid is left, 70% width
- [ ] Queue sidebar is right, 30% width
- [ ] Activity log is bottom
- [ ] No overlapping zones
- [ ] Responsive on mobile

### Notifications Bar
- [ ] Shows only when issues exist
- [ ] ✕ button collapses it
- [ ] Auto-hides when system healthy
- [ ] Message is human language
- [ ] Not blocking (click through)

### Agents Grid
- [ ] Cards are clickable (whole card)
- [ ] Click expands to full width
- [ ] Collapse button (✕) works
- [ ] Color matches state
- [ ] Shows real agent data from orchestrator.json

### Expanded Agent View (CRITICAL)
- [ ] Takes full width (minus padding)
- [ ] Shows complete agent details
- [ ] Shows context-sensitive actions
- [ ] If BLOCKED: Shows "What's wrong"
- [ ] If BLOCKED: Shows "How to fix"
- [ ] If BLOCKED: Shows "Who to ask"
- [ ] Collapse (✕) returns to grid

### Queue Sidebar
- [ ] Shows real counts from QUEUE_STATUS.json
- [ ] Updates every 10 seconds
- [ ] Health indicator matches system state
- [ ] Colors are semantic
- [ ] Numbers are readable

### Non-Technical Test
- [ ] Sister can see what's wrong
- [ ] Sister can see system health
- [ ] Sister knows if action needed
- [ ] No tech jargon in messages
- [ ] Colors communicate state clearly

---

## Violations = Rebuild

If any item marked [ ] at end, the feature is NOT COMPLETE.

No partial credit. No "good enough." No "user can figure it out."

Either all items checked ✅ or feature is broken and needs rebuild.

---

## Hard Rules (Never Break)

1. **Real data only** - Never show mock/fake data. If unavailable, show explicit "loading" or "unavailable" state.
2. **Single responsibility** - Each zone has one job. No zone overlap.
3. **Semantic colors** - Colors always mean the same thing. Never red for "working."
4. **Human language** - No technical jargon in UI. "Waiting for credentials" not "AUTH_FAILED".
5. **Context-sensitive** - Actions match state. IDLE gets different actions than BLOCKED.
6. **No modals** - Notifications don't block. Full-width agent view has clear close button.
7. **Responsive** - Works on phone/tablet/desktop without scrolling horizontally (except within zones).
8. **Accessible** - Keyboard navigation possible. Color blind friendly (not color-only).

---

## Sign-Off

✅ **This contract is binding.**

Any deviation from above = contract violation.

QA will enforce every item.

Implementation is not complete until ALL checkboxes are ✅.
