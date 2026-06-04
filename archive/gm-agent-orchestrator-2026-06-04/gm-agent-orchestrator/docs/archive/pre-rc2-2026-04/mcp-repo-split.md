# MCP Repository Responsibility Split
## Public vs Private Orchestrator MCPs

**Purpose:** Clearly delineate what belongs in each repository to avoid duplication and confusion.

---

## Repository Overview

### Public MCP Repo
**Location:** `github.com/alex-place/gamemaker-mcp` (or similar)  
**Visibility:** Public, open-source  
**Audience:** GameMaker developers everywhere  
**Responsibility:** General-purpose GameMaker tools usable by any team

### Private Orchestrator MCP Repo
**Location:** `C:\Users\alexp\Documents\gm-agent-orchestrator`  
**Visibility:** Private  
**Audience:** Internal team + Claude agents  
**Responsibility:** Multi-agent orchestration specific to this project

---

## Public MCP: What Goes Here

### Core GameMaker Tools (Read-Only)

#### ✅ get_gamemaker_project_info
- Returns project metadata (name, version, target platforms)
- Source: Parse *.yyp file
- Use case: Any GameMaker dev needs basic project info
- Status: SHARED infrastructure

#### ✅ get_gamemaker_compiler_errors
- Parse compiler output, return structured error list
- Source: GameMaker IDE build logs (standard format)
- Use case: Any dev needs to understand compile failures
- Stability: HIGH - Compiler output format stable

#### ✅ get_sprite_asset_status
- Validate sprite imports, frame counts, dimensions
- Source: Asset metadata (standard GameMaker format)
- Use case: Any dev needs asset validation
- Stability: HIGH - Asset format stable

#### ✅ get_room_editor_status
- Validate room layouts, object placements
- Source: Room editor MCP output
- Use case: Any dev needs room validation
- Stability: MEDIUM - Custom room editor tool

#### ✅ get_script_analysis
- Static analysis: undefined vars, dead code, style violations
- Source: Parse GML source directly
- Use case: Any dev needs code quality checks
- Stability: HIGH - Pure parsing

#### ✅ get_resource_dependency_graph
- What scripts call what, room->sprite relationships
- Source: Parse project files
- Use case: Understand architecture, refactoring impact
- Stability: HIGH - Pure parsing

#### ✅ get_gamemaker_version_info
- Installed GM version, extensions, runtime
- Source: GameMaker installation registry/CLI
- Use case: Verify compatibility
- Stability: HIGH - Stable registry access

---

### Public MCP: What Stays Out

#### ❌ get_orchestrator_agent_status
**Why:** Orchestrator-specific, not useful to general public  
**Where:** Private MCP only

#### ❌ get_queue_summary
**Why:** Orchestrator task queue is internal  
**Where:** Private MCP only

#### ❌ sync_repository
**Why:** Specific to orchestrator's git workflow  
**Where:** Private MCP only

#### ❌ requeue_task / fail_task / complete_task
**Why:** Task state management is orchestrator-specific  
**Where:** Private MCP only

#### ❌ start_agent / rerun_agent
**Why:** Agent management is orchestrator-specific  
**Where:** Private MCP only

#### ❌ Cached GitHub data
**Why:** Workaround for Claude connector constraint, not general  
**Where:** Private MCP only

---

## Private Orchestrator MCP: What Goes Here

### Orchestrator-Specific Tools (Read-Only + Write)

#### ✅ get_agent_status
- Agent availability, wake timing, next action
- Use case: Orchestrator knows who can work
- Access: Claude agents only (authenticated)

#### ✅ get_queue_summary
- Task counts, queue status, next action
- Use case: Orchestrator tracks work
- Access: Claude agents only

#### ✅ get_recent_failures
- Failed tasks, blocked slots
- Use case: Orchestrator debugging
- Access: Claude agents only

#### ✅ get_latest_agent_logs
- Agent execution logs
- Use case: Orchestrator debugging
- Access: Claude agents only

#### ✅ sync_repository
- Git fast-forward sync (orchestrator-specific workflow)
- Use case: Keep orchestrator repo in sync
- Access: Claude agents only

#### ✅ requeue_task / fail_task / complete_task
- Task state management (orchestrator-specific)
- Use case: Agent workflow coordination
- Access: Claude agents only

#### ✅ start_agent / rerun_agent
- Agent lifecycle (orchestrator-specific)
- Use case: Agent orchestration
- Access: Claude agents only

### Orchestrator Additions

#### ✅ get_github_issues_cached (NEW)
- Cached GitHub issue data (workaround for connector conflict)
- Use case: Avoid mixed connector constraints
- Access: Claude agents only
- Note: NOT in public MCP (workaround-specific)

#### ✅ get_github_pr_status_cached (NEW)
- Cached PR metadata (workaround for connector conflict)
- Use case: Avoid mixed connector constraints
- Access: Claude agents only
- Note: NOT in public MCP (workaround-specific)

---

## Public MCP Tool Reuse in Private MCP

Private orchestrator MCP **delegates** to public MCP for GameMaker tools:

```
Private MCP get_build_status()
  ├─> Public MCP get_gamemaker_compiler_errors()
  ├─> Public MCP get_gamemaker_version_info()
  └─> Return aggregated orchestrator-specific view
```

**Benefits:**
- Single source of truth for GameMaker parsing
- Public improvements automatically benefit orchestrator
- No duplication of GameMaker logic

**Pattern:**
```powershell
function Get-BuildStatusTool {
    # Call public MCP tools
    $errors = Invoke-PublicMcpTool -Name "get_gamemaker_compiler_errors"
    $version = Invoke-PublicMcpTool -Name "get_gamemaker_version_info"
    
    # Add orchestrator-specific wrapping
    return @{
        projectFile = "ChildOfLevistus.yyp"
        compileStatus = if ($errors.Length -gt 0) { "error" } else { "success" }
        orchestratorLastCheck = Get-Date
    }
}
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ PUBLIC MCP REPO                                         │
│ (gamemaker-mcp)                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✓ get_gamemaker_project_info                          │
│  ✓ get_gamemaker_compiler_errors                       │
│  ✓ get_sprite_asset_status                             │
│  ✓ get_room_editor_status                              │
│  ✓ get_script_analysis                                 │
│  ✓ get_resource_dependency_graph                       │
│  ✓ get_gamemaker_version_info                          │
│                                                         │
│  Audience: Any GameMaker developer                      │
│  NPM Package: @gamemaker-tools/mcp                      │
└─────────────────────────────────────────────────────────┘
           ↑
           │ imports / delegates to
           │
┌─────────────────────────────────────────────────────────┐
│ PRIVATE ORCHESTRATOR MCP REPO                           │
│ (gm-agent-orchestrator)                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ORCHESTRATOR-SPECIFIC:                                 │
│  ✓ get_agent_status                                    │
│  ✓ get_queue_summary                                   │
│  ✓ get_recent_failures                                 │
│  ✓ get_latest_agent_logs                               │
│  ✓ sync_repository                                     │
│  ✓ requeue_task / fail_task / complete_task            │
│  ✓ start_agent / rerun_agent                           │
│  ✓ get_github_issues_cached (workaround)               │
│  ✓ get_github_pr_status_cached (workaround)            │
│                                                         │
│  DELEGATED TO PUBLIC MCP:                               │
│  ✓ get_gamemaker_compiler_errors                       │
│  ✓ get_sprite_asset_status                             │
│  ✓ ... other GameMaker tools                           │
│                                                         │
│  Audience: Claude agents (authenticated)                │
│  HTTP Endpoint: http://127.0.0.1:8787/mcp              │
│  Bearer Token: Required                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Ownership & Maintenance

### Public MCP Maintainers
- **Responsible for:** GameMaker tool reliability, compatibility
- **Versioning:** Semantic versioning (public API stability)
- **Breaking changes:** Rare, with deprecation warnings
- **Release process:** NPM package + GitHub releases
- **Test coverage:** High (used by external teams)

### Private Orchestrator Maintainers
- **Responsible for:** Agent coordination, workflow orchestration
- **Versioning:** Internal only, no stability guarantee
- **Breaking changes:** OK if all agents updated simultaneously
- **Release process:** Direct deployment to orchestrator
- **Test coverage:** Medium (internal only)

### Tool-by-Tool Ownership

| Tool | Repo | Owner | Change Policy |
|------|------|-------|----------------|
| get_gamemaker_compiler_errors | Public | Public team | Backwards-compatible |
| get_sprite_asset_status | Public | Public team | Backwards-compatible |
| get_agent_status | Private | Orchestrator | Internal only |
| get_queue_summary | Private | Orchestrator | Internal only |
| get_github_issues_cached | Private | Orchestrator | Workaround-specific |
| requeue_task | Private | Orchestrator | Internal only |

---

## Integration Points

### How Private Uses Public

**Read-Only delegation:**
```
Agent calls: Private MCP get_build_status()
  → Private MCP calls: Public MCP get_gamemaker_compiler_errors()
  → Agent receives aggregated result
```

**Process:**
1. Agent needs to validate game compile
2. Agent calls private MCP's `get_build_status`
3. Private MCP internally calls public MCP's `get_gamemaker_compiler_errors`
4. Private MCP wraps result with orchestrator context
5. Agent sees unified response

### Public MCP Use Cases

**Direct use (not through private MCP):**
- External GameMaker developers using public tools
- Game studios validating their own projects
- CI/CD pipelines for GameMaker games
- IDE plugins integrating GameMaker analysis

**Example:**
```powershell
# External use (no orchestrator involved)
Invoke-MCP -Uri "https://gamemaker-tools.org/mcp" `
    -Tool "get_gamemaker_compiler_errors" `
    -Arguments @{ projectFile = "MyGame.yyp" }
```

---

## Deployment Architecture

```
EXTERNAL DEVELOPERS
        │
        ↓
    npm install @gamemaker-tools/mcp
        │
        ├─→ PUBLIC MCP SERVICE (if hosted)
        │
        └─→ LOCAL PUBLIC MCP INSTANCE

INTERNAL TEAM / CLAUDE AGENTS
        │
        ↓
    Bearer Token: ORCH_MCP_TOKEN
        │
        ↓
    PRIVATE ORCHESTRATOR MCP
        │
        ├─→ Delegates to PUBLIC MCP (local instance)
        │
        └─→ Uses orchestrator-specific tools
```

---

## Dependency Management

### Public MCP Has Zero Dependencies on Private MCP
- Public MCP is standalone
- Can be used without orchestrator
- No imports from private MCP
- ✅ CORRECT separation

### Private MCP Depends on Public MCP
- Private MCP calls public MCP tools
- Via local import or HTTP delegation
- ✅ CORRECT one-way dependency

### DO NOT
- ❌ Public MCP importing from private repo
- ❌ Circular dependencies
- ❌ Private MCP tools in public package

---

## Future: Graduation Path

If a tool becomes generally useful, move it from private → public:

**Example:** Token tracking feature
1. **Currently:** Private MCP only (orchestrator-specific)
2. **Graduation:** Extract to public MCP as `get_token_usage_metrics`
3. **Update:** Private MCP delegates to public version
4. **Benefit:** External teams can use token tracking too

**Process:**
1. Stabilize tool in private repo
2. Extract to public repo
3. Release as new version
4. Update private repo to use public version
5. Deprecate old private implementation

---

## Testing & Validation

### Public MCP Tests
- Use: Standard GameMaker projects (open-source or test projects)
- Focus: GameMaker tool correctness
- CI/CD: GitHub Actions (public)

### Private Orchestrator MCP Tests
- Use: Child of Levistus project
- Focus: Agent orchestration workflows
- CI/CD: Private orchestrator workflow

### Integration Tests
- Test that private MCP correctly delegates to public MCP
- Test that aggregated results are correct
- Run as part of private orchestrator validation

---

## Summary: Who Does What

| Responsibility | Public MCP | Private MCP |
|---|---|---|
| GameMaker tool development | ✅ | ❌ |
| GameMaker tool maintenance | ✅ | ❌ (delegates) |
| Agent orchestration | ❌ | ✅ |
| Task queue management | ❌ | ✅ |
| GitHub integration workarounds | ❌ | ✅ |
| Multi-agent coordination | ❌ | ✅ |
| Public releases | ✅ | ❌ |
| Internal deployment | ❌ | ✅ |

**Golden Rule:**
- **Public MCP:** "What every GameMaker developer needs"
- **Private MCP:** "How we orchestrate our agents"
