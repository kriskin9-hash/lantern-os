# MCP Quick-Win Tools: Phase 1 Exposure

**Purpose:** Expose 5 existing scripts as MCP tools to enable agents to access system state safely without creating new tool implementations. These are "quick wins" because the scripts already exist; we just need to wire them through Start-OrchMcpServer.ps1.

**Timeline:** Phase 1 Week 1 (2-4 hours)  
**Owner:** Claude + Codex  
**Blocking:** No (parallel to RC3 Phase 1-2)  

---

## Philosophy

Instead of building new MCP tool implementations from scratch, expose existing working scripts. Benefits:

- **No new code to test:** Existing scripts already validate and handle errors
- **Proven behavior:** Scripts used successfully by orchestrator internally
- **Faster delivery:** Hours to expose vs. days to implement new tools
- **Single source of truth:** Script = tool source; no duplication

---

## Quick-Win #1: `get_branch_status` → Expose `git branch -vv` + PR lookup

### Current Script
**Path:** None (currently inlined in orchestrator logic)  
**Input:** None (uses CWD)  
**Output:** JSON with branch, tracking, commit, PR status  

### MCP Tool Definition
```typescript
{
  name: "get_branch_status",
  description: "Get current branch, tracking info, commits ahead, and active PR details",
  inputSchema: {
    type: "object",
    properties: {}
  }
}
```

### Implementation Steps
1. Create `scripts/Get-BranchStatus.ps1` wrapper around existing logic
   - Input: None (uses current git state)
   - Output: JSON object with branch, tracking, commits, pr_number, pr_status
   - Example output:
   ```json
   {
     "current_branch": "fix/exact-task-selection",
     "tracking": "origin/fix/exact-task-selection",
     "commits_ahead": 2,
     "commits_behind": 0,
     "pr_number": 260,
     "pr_status": "OPEN",
     "pr_title": "Screen Flicker Fixes",
     "pr_url": "https://github.com/alex-place/gm-agent-orchestrator/pull/260"
   }
   ```

2. Register in Start-OrchMcpServer.ps1 (line ~175)
   ```powershell
   # Add to tools array:
   [pscustomobject]@{
     name = "get_branch_status"
     handler = "scripts/Get-BranchStatus.ps1"
     timeout_seconds = 10
   }
   ```

3. Wire in MCP request dispatcher (Handle-McpRequest function)
   ```powershell
   "get_branch_status" {
     & scripts/Get-BranchStatus.ps1 | ConvertTo-Json -Depth 10
   }
   ```

4. Test: Call from agent with no parameters, verify JSON output

**Effort:** 1 hour  
**Risk:** Low (wrapping existing git commands)  
**Value:** Enables agents to check their own branch state without spawning git processes  

---

## Quick-Win #2: `get_queue_summary` → Expose queue task counts

### Current Script
**Path:** `scripts/Invoke-OrchestratorTaskAction.ps1` (embedded in queue operations)  
**Input:** None  
**Output:** JSON with queue/active/failed counts  

### MCP Tool Definition
```typescript
{
  name: "get_queue_summary",
  description: "Get count of tasks in each queue lane (queue/active/hold/done/failed)",
  inputSchema: {
    type: "object",
    properties: {}
  }
}
```

### Implementation Steps
1. Create `scripts/Get-QueueSummary.ps1`
   - Reads `tasks/queue`, `tasks/active`, `tasks/hold`, `tasks/done`, `tasks/failed`, `tasks/disabled`
   - Counts files in each directory
   - Output JSON with counts and total
   - Example:
   ```json
   {
     "queue": 3,
     "active": 1,
     "hold": 2,
     "done": 18,
     "failed": 1,
     "disabled": 0,
     "total": 25,
     "timestamp": "2026-05-03T18:15:00Z"
   }
   ```

2. Register in Start-OrchMcpServer.ps1

3. Wire in dispatcher

4. Test: Verify counts match actual task files

**Effort:** 45 minutes  
**Risk:** Low (simple file counting)  
**Value:** Enables agents to know if queue is blocked, busy, or idle  

---

## Quick-Win #3: `get_token_budget_status` → Expose quota-tracker.json

### Current Script
**Path:** Status file only (no script yet)  
**Input:** None  
**Output:** JSON from `status/quota-tracker.json`  

### MCP Tool Definition
```typescript
{
  name: "get_token_budget_status",
  description: "Get current provider token quota state and refresh timestamp",
  inputSchema: {
    type: "object",
    properties: {}
  }
}
```

### Implementation Steps
1. Create `scripts/Get-TokenBudgetStatus.ps1`
   - Reads `status/quota-tracker.json`
   - Checks freshness (if >5 min old, triggers refresh warning)
   - Formats JSON with provider states
   - Example:
   ```json
   {
     "providers": {
       "claude": {
         "used": 180000,
         "limit": 200000,
         "percent_used": 90,
         "fallback_priority": 1,
         "status": "online"
       },
       "codex": {
         "used": 160000,
         "limit": 200000,
         "percent_used": 80,
         "fallback_priority": 2,
         "status": "online"
       },
       "gemini": {
         "used": 95000,
         "limit": 100000,
         "percent_used": 95,
         "fallback_priority": 3,
         "status": "approaching_limit",
         "alert": "Quota approaching limit"
       },
       "gpt-web": {
         "used": 50000,
         "limit": 75000,
         "percent_used": 67,
         "fallback_priority": 4,
         "status": "online"
       }
     },
     "fleet_total_percent": 84,
     "quota_tracker_age_seconds": 120,
     "last_refresh": "2026-05-03T18:00:00Z",
     "next_reset_eta": "2026-05-05T00:00:00Z"
   }
   ```

2. Register in Start-OrchMcpServer.ps1

3. Wire in dispatcher

4. Test: Verify against actual quota-tracker.json

**Effort:** 1 hour  
**Risk:** Low (reading JSON file)  
**Value:** Highest impact — enables agents to make smart routing decisions and avoid quota exhaustion  

---

## Quick-Win #4: `get_agent_status` → Expose fleet health

### Current Script
**Path:** None (status inferred from logs)  
**Input:** None  
**Output:** JSON with agent availability  

### MCP Tool Definition
```typescript
{
  name: "get_agent_status",
  description: "Get status of all 5 agent slots (online/offline, last activity, current task)",
  inputSchema: {
    type: "object",
    properties: {}
  }
}
```

### Implementation Steps
1. Create `scripts/Get-AgentStatus.ps1`
   - Reads `status/services.json` (from service supervisor)
   - Reads recent agent process status
   - Reads latest activity from logs
   - Example:
   ```json
   {
     "agents": [
       {
         "name": "claude-slot-1",
         "status": "online",
         "current_task": "256-fix-mcp-dispatch",
         "task_started": "2026-05-03T17:45:00Z",
         "last_activity": "2026-05-03T18:15:00Z",
         "process_id": 12345,
         "estimated_completion": "2026-05-03T19:00:00Z"
       },
       {
         "name": "codex-slot-2",
         "status": "online",
         "current_task": null,
         "last_activity": "2026-05-03T17:30:00Z",
         "process_id": null,
         "estimated_completion": null
       },
       {
         "name": "gemini-slot-3",
         "status": "offline",
         "reason": "Quota exhausted, in cooldown",
         "cooldown_until": "2026-05-05T00:00:00Z",
         "last_activity": "2026-05-02T14:30:00Z"
       },
       {
         "name": "gpt-web-slot-4",
         "status": "online",
         "current_task": null,
         "last_activity": "2026-05-02T22:15:00Z"
       },
       {
         "name": "headless-slot-5",
         "status": "online",
         "current_task": null,
         "last_activity": "2026-05-03T08:00:00Z",
         "role": "utility/supervisor"
       }
     ],
     "fleet_summary": {
       "online": 4,
       "offline": 1,
       "total": 5,
       "available_for_new_work": 3
     }
   }
   ```

2. Register in Start-OrchMcpServer.ps1

3. Wire in dispatcher

4. Test: Verify status matches actual agent processes

**Effort:** 1.5 hours  
**Risk:** Low (reading service supervisor status)  
**Value:** Enables agents to understand fleet capacity and adjust routing  

---

## Quick-Win #5: `get_game_build_status` → Expose compiler output parsing

### Current Script
**Path:** Partially in orchestrator (GameMaker compilation runner)  
**Input:** None (reads from GameMaker project)  
**Output:** JSON with compiler errors, asset validation results  

### MCP Tool Definition
```typescript
{
  name: "get_game_build_status",
  description: "Get GameMaker project build status: compiler errors, asset validation, room structure",
  inputSchema: {
    type: "object",
    properties: {
      project: {
        type: "string",
        description: "Project name (default: child-of-levistus)"
      }
    }
  }
}
```

### Implementation Steps
1. Create `scripts/Get-GameMakerBuildStatus.ps1`
   - Reads `status/gamemaker-build-status.json` (generated by orchestrator)
   - Or triggers quick build validation if stale
   - Parses compiler output
   - Example:
   ```json
   {
     "project": "child-of-levistus",
     "last_build": "2026-05-03T18:10:00Z",
     "build_status": "FAILED",
     "error_count": 2,
     "warning_count": 5,
     "errors": [
       {
         "file": "objects/obj_player/Create_0.gml",
         "line": 15,
         "message": "Unexpected symbol '}'",
         "severity": "error"
       },
       {
         "file": "sprites/spr_player/spr_player.yy",
         "line": 1,
         "message": "Sprite frame dimension mismatch",
         "severity": "error"
       }
     ],
     "asset_validation": {
       "sprites": { "valid": 24, "missing_frames": 1, "dimension_issues": 0 },
       "objects": { "valid": 18, "missing_events": 2, "orphaned": 0 },
       "rooms": { "valid": 5, "structural_errors": 0, "object_placement_issues": 1 }
     }
   }
   ```

2. Register in Start-OrchMcpServer.ps1

3. Wire in dispatcher

4. Test: Verify against actual project status

**Effort:** 1.5 hours  
**Risk:** Medium (depends on orchestrator's GameMaker integration)  
**Value:** High — enables agents to diagnose build failures without running compiler themselves  

---

## Implementation Sequence

**Day 1 (2-4 hours):**
1. Create all 5 scripts (script shells can be created in parallel)  
2. Register in Start-OrchMcpServer.ps1  
3. Wire into dispatcher  
4. Manual test each tool  

**Day 2 (1-2 hours):**
1. Integrate tests into CI  
2. Update MCP capability status  
3. Document in agent guides  
4. Commit and merge  

---

## Testing Checklist

For each tool:
- [ ] Calls script with example parameters
- [ ] Returns valid JSON (parseable by PowerShell ConvertTo-Json)
- [ ] Output matches expected schema
- [ ] Handles errors gracefully (no crashes)
- [ ] Timeout works (returns error after 10 seconds if script hangs)
- [ ] Integrates with agent dispatch (agent can call from orchestrator context)

---

## Risk Mitigation

**Risk: Script fails, breaks MCP dispatcher**  
→ Mitigate: Wrap each handler in try-catch, return JSON error object

**Risk: Tool returns stale data (quota-tracker 1 hour old)**  
→ Mitigate: Return `timestamp` and `age_seconds` in every response, mark stale data

**Risk: Performance (tool takes >10s)**  
→ Mitigate: Set timeout, cache results in status files, avoid expensive calculations

**Risk: Contradicts GRUDGEBOOK Rule about safe tools**  
→ Mitigate: All tools are read-only; no mutations; no file writes outside status/

---

## Success Metrics (Phase 1 Exit Gate)

- [ ] All 5 tools implemented and tested
- [ ] Tools registered in Start-OrchMcpServer.ps1
- [ ] Agent can call each tool without errors
- [ ] Tool output matches documented schema
- [ ] Tools integrate with quota tracking and fleet decisions
- [ ] AGENT_RESUME_STABLE.md updated with MCP tool list
- [ ] Deployed to production (agents have access)

---

## Follow-Up: Phase 2 Strategic Tools (Not Quick-Wins)

After quick-wins are deployed, implement 5 more strategic tools (requires new implementations):

1. **`stage_git_files`** — Stage files without spawning git UI  
2. **`commit_git_changes`** — Commit with audit trail without UI  
3. **`propose_queue_mutation`** — Dry-run queue movement, get approval  
4. **`get_stale_branch_list`** — Find branches ready for cleanup  
5. **`run_safe_powershell`** — Execute pre-approved scripts with sandboxing  

Estimated: 6-8 hours total (Phase 2, Week 2)
