# Browser Automation Fallback Agent (Research)

**Status:** Research phase
**Rationale:** CLI agents (claude, codex, gemini) are currently blocked. GPT has higher token availability and a web interface can be automated reliably.
**Date:** 2026-04-25

---

## Problem

CLI agent slots are blocked with validation failures:
- claude-main: Validation failed
- codex-main: Validation failed  
- gemini: Not preflight ready

GPT remains available via web interface but has no CLI agent slot.

**Cost:** Tasks queue up. No agent can claim work.

---

## Solution: Browser Automation Fallback

Instead of requiring a CLI agent for every slot, implement a browser-based agent that:
1. Logs into GPT web interface
2. Claims tasks from orchestrator queue
3. Executes tasks through the browser
4. Reports results back to queue

**Advantages:**
- Works with any service that has a web UI (GPT, Claude.ai, Gemini web, etc.)
- No CLI dependency
- No elevation prompts (browser API is stateless)
- Can operate in headless mode for automation

**Disadvantages:**
- Slower than CLI (browser startup overhead)
- Requires session management (login cookies)
- Dependent on web UI remaining stable

---

## Architecture

```
Orchestrator Queue (tasks/queue/)
    ↓
Browser Agent Runner
    ↓
[Browser Process]
    ├─ Open GPT/Claude.ai
    ├─ Paste task description
    ├─ Execute task in conversation
    ├─ Collect outputs
    └─ Return result
    ↓
Task Reporter (updates task state)
    ↓
Orchestrator Completed (tasks/done/)
```

---

## Implementation Options

### Option 1: Puppeteer/Playwright (Node.js)
```javascript
// Launch browser, navigate to GPT, paste task, collect output
const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.goto('https://chat.openai.com');
// ...authenticate...
await page.type('#message-input', taskDescription);
await page.click('[aria-label="Send"]');
// ...wait for response...
```

**Pros:** Standard browser automation, headless support, well-documented
**Cons:** Node.js dependency, requires GPT account with session persistence

### Option 2: PowerShell + Chrome Remote Debugging
```powershell
# Use Chrome DevTools Protocol to control browser instance
$browser = Start-Process chrome --remote-debugging-port=9222
# Connect via CDP, navigate, execute
```

**Pros:** Native Windows, integrates with existing PowerShell scripts
**Cons:** Requires chrome devtools API knowledge, less mature than Playwright

### Option 3: Claude Code Web Automation
```
Use the built-in browser automation tools to control a browser instance
and execute tasks in GPT web interface.
```

**Pros:** Already integrated into this system
**Cons:** Requires this (Claude Code) to be running the orchestrator

### Option 4: Hybrid Approach (Recommended for MVP)
```
1. Keep CLI agents for normal operation
2. On CLI agent failure, spin up browser fallback
3. Browser agent handles only critical P0 tasks
4. Manual escalation for complex tasks
```

**Advantages:**
- Minimal changes to existing system
- Reliable fallback without redesigning all agents
- Can test and stabilize gradually

---

## Recommended: Phase 4 Implementation

Create a `gpt-web` agent slot that:

1. **Initialization:**
   - Detects when all CLI slots are blocked
   - Launches browser to GPT web interface
   - Authenticates using stored credentials or OAuth

2. **Task Execution:**
   - Claims task from queue (same as CLI agents)
   - Pastes task description into GPT chat
   - Waits for response
   - Collects final output
   - Marks task complete/failed

3. **Monitoring:**
   - Heartbeat endpoint for browser session health
   - Auto-restart on browser crash
   - Timeout protection (no infinite wait)

4. **Constraints:**
   - Only run when ≥2 CLI slots are blocked
   - Maximum 1 concurrent browser instance
   - Token usage tracking (browser ops are slower)
   - Fallback to human review on validation failure

---

## Minimal Viable Implementation

Start with a single script: `scripts/Start-BrowserFallbackAgent.ps1`

```powershell
param(
    [string]$SlotName = "gpt-web",
    [string]$QueuePath = "tasks/queue",
    [string]$DonePath = "tasks/done",
    [string]$FailPath = "tasks/failed"
)

# 1. Check if we need fallback (all CLI slots blocked?)
$cliSlots = @("claude-main", "codex-main", "gemini-main")
$allBlocked = ($cliSlots | ForEach-Object { Get-SlotState $_ }).state -contains "blocked"

if (!$allBlocked) { exit 0 }  # Don't start if CLI agents available

# 2. Launch browser to GPT
$browser = Open-BrowserToGpt

# 3. Poll queue for tasks
while ($true) {
    $task = Get-QueuedTask -Path $QueuePath -Limit 1
    if (!$task) { sleep 30; continue }
    
    # 4. Execute in browser
    $output = Invoke-GptTask -Browser $browser -Task $task
    
    # 5. Report result
    if ($output.success) {
        Move-Task -From "$QueuePath/$task" -To $DonePath
    } else {
        Move-Task -From "$QueuePath/$task" -To $FailPath -Error $output.error
    }
}
```

---

## Testing Strategy

1. **Unit tests:** Browser login, task input, output collection
2. **Integration test:** Full task lifecycle in headless browser
3. **Stress test:** 10 tasks in succession, browser stability
4. **Failure test:** Browser crash recovery, timeout handling
5. **Production test:** Fallback activation when CLI slots fail

---

## Success Criteria for Phase 4

- [ ] Browser agent starts when all CLI slots blocked
- [ ] Can claim and execute P0 tasks
- [ ] Results are captured and reported correctly
- [ ] Handles browser crashes gracefully
- [ ] Token usage is tracked separately (informational)
- [ ] Can be manually stopped/restarted

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| GPT API rate limiting | Start with P0 only, with delays |
| Session timeout | Auto-refresh every 1 hour |
| Browser crash | Auto-restart with backoff |
| Infinite loops | 10-minute timeout per task |
| Token counting inaccuracy | Log all operations, manual audits |

---

## Why This Matters

Right now, if CLI agents fail, the orchestrator is stuck. A browser fallback:
- **Unblocks work:** Tasks execute even if CLI agents are down
- **Reduces bottlenecks:** Distributes load across multiple agents
- **Validates system:** Proves the orchestrator can route to different execution methods
- **Future-proofs:** Easy to add other execution methods (Slack bots, REST APIs, etc.)

---

## Next Steps (If Approved)

1. Clarify GPT account credentials strategy (stored session? OAuth?)
2. Decide between Playwright (Node.js) vs. PowerShell + DevTools
3. Implement minimal prototype in Phase 4
4. Test with 3-5 real tasks
5. Document operational procedures (manual intervention, monitoring)

---

## See Also

- `docs/agent-contract.md` - Agent execution contract
- `scripts/Start-AgentSlot.ps1` - Slot runner pattern
- `docs/ALTERNATIVE-TO-POWERSHELL-PROMPTS.md` - HTTP alternatives
- Phase 2-3 GitHub issues (#71-72) - Upcoming improvements
