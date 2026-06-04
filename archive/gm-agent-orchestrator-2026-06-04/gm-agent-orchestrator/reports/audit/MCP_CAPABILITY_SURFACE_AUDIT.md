# MCP Capability Surface Audit
## Child of Levistus Development Acceleration Analysis

**Date:** 2026-04-25  
**Audit Scope:** Read-only orchestrator MCP tools  
**Project:** Child of Levistus (GameMaker)  
**Status:** INCOMPLETE - Missing critical dev tools

---

## Current MCP Tools (Read-Only)

### 1. **get_agent_status**
- Returns: Agent availability, wake timing, next action
- Use case: Know which agents can work
- **Limitation:** No GameMaker-specific asset/build status

### 2. **get_queue_summary**
- Returns: Task counts (queued, active, failed)
- Use case: Understand orchestrator workload
- **Limitation:** No game compilation status, no asset validation

### 3. **get_recent_failures**
- Returns: Failed tasks + blocked slots (limited to 50)
- Use case: Troubleshoot task failures
- **Limitation:** No compile errors, no asset build errors

### 4. **get_latest_agent_logs**
- Returns: Latest log tail for each agent slot
- Use case: Debug agent execution
- **Limitation:** Generic agent logs, not game-specific

---

## Missing Tools for Child of Levistus Development

### HIGH PRIORITY (Blocks Development)

#### 1. **get_game_build_status**
**Problem:** Can't tell if code compiles without running full agent cycle  
**What it should return:**
```
{
  projectFile: "ChildOfLevistus.yyp",
  lastCompileTime: ISO8601,
  compileStatus: "success|error|warning",
  errorCount: number,
  warningCount: number,
  errors: [{ file, line, message }],
  compileDuration: milliseconds,
  targetPlatforms: ["Windows", "HTML5", "..."]
}
```
**Benefit:** 5-minute turnaround instead of waiting for full agent cycle

#### 2. **get_asset_validation_status**
**Problem:** Can't validate sprites, rooms, audio without full build  
**What it should return:**
```
{
  assetType: "sprite|room|sound|script|...",
  validationStatus: "valid|invalid|warnings",
  issues: [{ asset, severity, message }],
  byType: {
    sprites: { valid, invalid, warnings },
    rooms: { valid, invalid, warnings },
    scripts: { valid, invalid, warnings },
    ...
  }
}
```
**Benefit:** Quick validation loop - catch asset errors in minutes not hours

#### 3. **get_gamemaker_compiler_errors**
**Problem:** Compile errors are buried in agent logs  
**What it should return:**
```
{
  projectFile: "ChildOfLevistus.yyp",
  errors: [{
    file: "scripts/player_controller/player_controller.gml",
    line: 42,
    column: 15,
    severity: "error|warning",
    message: "Undefined variable: player_speed",
    context: "code snippet around error"
  }],
  summary: "3 errors, 2 warnings"
}
```
**Benefit:** Immediate feedback without parsing logs

#### 4. **get_room_editor_status**
**Problem:** Can't validate room layouts, object placements without full run  
**What it should return:**
```
{
  rooms: [{
    name: "rm_start",
    status: "valid|invalid|modified",
    objectCount: number,
    tileCount: number,
    issues: [{ issue, severity }],
    lastEdited: ISO8601,
    byEditor: "gamemaker|room-editor-mcp"
  }],
  totalRooms: number,
  validRooms: number
}
```
**Benefit:** Catch room design issues before agent cycles

#### 5. **get_sprite_asset_status**
**Problem:** Can't validate sprite imports, animations, sizes  
**What it should return:**
```
{
  sprites: [{
    name: "child_of_levi_splash",
    status: "valid|invalid|import_pending",
    frameCount: number,
    width: number,
    height: number,
    issues: [{ issue, severity, recommendation }],
    lastImported: ISO8601,
    sourceFile: "path/to/source"
  }],
  invalidSprites: number,
  pendingImports: number
}
```
**Benefit:** Asset pipeline visibility - spot import errors immediately

---

### MEDIUM PRIORITY (Improves Workflow)

#### 6. **get_script_analysis**
**Problem:** No static analysis of GML code quality  
**Returns:** Undefined variables, function calls, cyclic dependencies, style violations

#### 7. **get_resource_dependency_graph**
**Problem:** Can't understand asset dependencies without code reading  
**Returns:** Which scripts call which scripts, which rooms use which sprites, etc.

#### 8. **get_game_performance_metrics**
**Problem:** No visibility into runtime performance  
**Returns:** FPS targets, memory usage, frame timing analysis

#### 9. **get_test_results**
**Problem:** Test output is hidden in agent logs  
**Returns:** Unit test status, regression test results, smoke test status

#### 10. **get_asset_import_queue**
**Problem:** Can't see what's pending import  
**Returns:** Assets waiting to be imported, import order, blockers

---

### LOWER PRIORITY (Nice to Have)

- **get_git_diff_stats** - Show what changed in last commit
- **get_branch_status** - Show which branches have uncommitted changes
- **get_gamemaker_version** - Confirm GM version + extensions
- **get_code_coverage** - Test coverage metrics
- **get_memory_profile** - Asset memory usage breakdown

---

## Impact Analysis

### Without These Tools
- **Per iteration cost:** 15-30 minutes (wait for agent cycle)
- **Feedback loop:** Slow (can't validate until full run)
- **Error discovery:** Late (compile errors found after agent execution)
- **Parallelization:** Blocked (need validation before next task)

### With These Tools
- **Per iteration cost:** 2-5 minutes (direct validation)
- **Feedback loop:** Fast (immediate validation)
- **Error discovery:** Early (compile check before queue)
- **Parallelization:** Enabled (validate while agents work)

**Estimated acceleration:** 3-6x faster development cycle

---

## Implementation Priority

1. **Phase 1 (CRITICAL):** get_game_build_status + get_gamemaker_compiler_errors
   - Enables immediate compile feedback
   - Unblocks asset validation workflows

2. **Phase 2 (HIGH):** get_asset_validation_status + get_sprite_asset_status + get_room_editor_status
   - Completes asset validation pipeline
   - Catches design errors early

3. **Phase 3 (MEDIUM):** get_script_analysis + get_resource_dependency_graph
   - Enables code quality metrics
   - Supports refactoring workflows

4. **Phase 4 (NICE):** Remaining tools as bandwidth allows

---

## Technical Implementation Notes

### Data Sources
- **Compiler output:** GameMaker IDE logs, `gml_module` output
- **Asset validation:** GameMaker resource parser + room editor checks
- **Sprite status:** Asset import logs + sprite metadata
- **Room status:** Room editor MCP + GameMaker resource parser

### Integration Points
- Read-only access to: `ChildOfLevistus.yyp`, GameMaker IDE output
- Leverage: Existing `run-room-editor-mcp.ps1` for room/asset validation
- Extend: `Get-OrchestratorStatus.ps1` to include game-specific metrics

---

## Recommendation

**Add Phase 1 tools immediately.** The compile feedback loop is the biggest bottleneck for iterative GameMaker development. Without it, agents waste time waiting for validation that could be done in seconds.

These tools would transform the development flow from:
```
Write Code → Queue Task → Wait for Agent → Check Logs → Find Error → Iterate
(30 min per cycle)
```

To:
```
Write Code → Validate Locally (2 min) → Queue Task → Agent Executes Clean Code
(5 min per cycle)
```
