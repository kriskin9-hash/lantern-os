[CmdletBinding()]
param(
    [int]$Port = 8787,
    [string]$Root = "",
    [string]$BearerToken = $env:ORCH_MCP_TOKEN,
    [switch]$NoAuth
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function New-Token {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) }
    finally { $rng.Dispose() }
    return [Convert]::ToBase64String($bytes).TrimEnd("=")
}

if (!$NoAuth -and [string]::IsNullOrWhiteSpace($BearerToken)) {
    $BearerToken = New-Token
    Write-Warning "ORCH_MCP_TOKEN was not set. Generated a temporary token for this process only."
}

$StatusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
$CapabilityStatusScript = Join-Path $Root "scripts\Get-OrchMcpCapabilityStatus.ps1"
$RepoSyncScript = Join-Path $Root "scripts\Invoke-OrchestratorRepoSync.ps1"
$TaskActionScript = Join-Path $Root "scripts\Invoke-OrchestratorTaskAction.ps1"
$AgentActionScript = Join-Path $Root "scripts\Invoke-OrchestratorAgentAction.ps1"
$GitHubCacheScript = Join-Path $Root "scripts\Get-GitHubDataCache.ps1"
$GameMakerProjectInfoScript = Join-Path $Root "scripts\Get-GameMakerProjectInfo.ps1"
$GameMakerCompilerErrorsScript = Join-Path $Root "scripts\Get-GameMakerCompilerErrors.ps1"
$GameMakerSpriteStatusScript = Join-Path $Root "scripts\Get-GameMakerSpriteAssetStatus.ps1"
$GameMakerRoomStatusScript = Join-Path $Root "scripts\Get-GameMakerRoomEditorStatus.ps1"
$GameMakerBuildStatusScript = Join-Path $Root "scripts\Get-GameMakerBuildStatus.ps1"

foreach ($requiredScript in @($StatusScript, $CapabilityStatusScript, $RepoSyncScript, $TaskActionScript, $AgentActionScript, $GitHubCacheScript, $GameMakerProjectInfoScript, $GameMakerCompilerErrorsScript, $GameMakerSpriteStatusScript, $GameMakerRoomStatusScript, $GameMakerBuildStatusScript)) {
    if (!(Test-Path $requiredScript)) { throw "Missing required script: $requiredScript" }
}

function Write-JsonResponse {
    param([System.Net.HttpListenerContext]$Context, [object]$Body, [int]$StatusCode = 200)
    $json = $Body | ConvertTo-Json -Depth 80 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $Context.Response.StatusCode = $StatusCode
    $Context.Response.ContentType = "application/json; charset=utf-8"
    $Context.Response.ContentLength64 = $bytes.Length
    $Context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Context.Response.OutputStream.Close()
}

function Write-SseResponse {
    param([System.Net.HttpListenerContext]$Context, [object]$Body, [string]$Event = "message", [int]$StatusCode = 200)
    $json = $Body | ConvertTo-Json -Depth 80 -Compress
    $payload = "event: $Event`ndata: $json`n`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
    $Context.Response.StatusCode = $StatusCode
    $Context.Response.ContentType = "text/event-stream; charset=utf-8"
    $Context.Response.Headers["Cache-Control"] = "no-cache"
    $Context.Response.Headers["Connection"] = "keep-alive"
    $Context.Response.SendChunked = $true
    $Context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Context.Response.OutputStream.Flush()
    $Context.Response.OutputStream.Close()
}

function Write-TextResponse {
    param([System.Net.HttpListenerContext]$Context, [string]$Body, [int]$StatusCode = 200)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
    $Context.Response.StatusCode = $StatusCode
    $Context.Response.ContentType = "text/plain; charset=utf-8"
    $Context.Response.ContentLength64 = $bytes.Length
    $Context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Context.Response.OutputStream.Close()
}

function New-JsonRpcResult {
    param([object]$Id, [object]$Result)
    return [pscustomobject]@{ jsonrpc = "2.0"; id = $Id; result = $Result }
}

function New-JsonRpcError {
    param([object]$Id, [int]$Code, [string]$Message)
    return [pscustomobject]@{ jsonrpc = "2.0"; id = $Id; error = [pscustomobject]@{ code = $Code; message = $Message } }
}

function New-McpInitializeResult {
    return [pscustomobject]@{
        protocolVersion = "2025-03-26"
        capabilities = [pscustomobject]@{ tools = [pscustomobject]@{} }
        serverInfo = [pscustomobject]@{ name = "gm-agent-orchestrator"; version = "0.2.0" }
    }
}

function Test-Authorized {
    param([System.Net.HttpListenerRequest]$Request)
    if ($NoAuth) { return $true }
    $auth = [string]$Request.Headers["Authorization"]
    if ([string]::IsNullOrWhiteSpace($auth)) { return $false }
    if (!$auth.StartsWith("Bearer ")) { return $false }
    $token = $auth.Substring(7).Trim()
    return [string]::Equals($token, $BearerToken, [System.StringComparison]::Ordinal)
}

function Read-RequestJson {
    param([System.Net.HttpListenerRequest]$Request)
    $reader = New-Object System.IO.StreamReader($Request.InputStream, $Request.ContentEncoding)
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
    $parsed = $raw | ConvertFrom-Json
    return Normalize-GptJsonRpcRequest -Request $parsed
}

function Normalize-GptJsonRpcRequest {
    param([object]$Request)
    if ($null -eq $Request) { return $null }

    $normalized = [pscustomobject]@{}

    if ($Request.PSObject.Properties["jsonrpc"]) { $normalized | Add-Member -NotePropertyName "jsonrpc" -NotePropertyValue $Request.jsonrpc }
    elseif ([string]::IsNullOrWhiteSpace([string]$Request.jsonrpc)) { $normalized | Add-Member -NotePropertyName "jsonrpc" -NotePropertyValue "2.0" }

    if ($Request.PSObject.Properties["id"]) { $normalized | Add-Member -NotePropertyName "id" -NotePropertyValue $Request.id }
    if ($Request.PSObject.Properties["method"]) { $normalized | Add-Member -NotePropertyName "method" -NotePropertyValue $Request.method }

    if ($Request.PSObject.Properties["params"]) { $normalized | Add-Member -NotePropertyName "params" -NotePropertyValue $Request.params }
    elseif ($Request.PSObject.Properties["arguments"]) { $normalized | Add-Member -NotePropertyName "params" -NotePropertyValue $Request.arguments }
    elseif ($Request.PSObject.Properties["input"]) { $normalized | Add-Member -NotePropertyName "params" -NotePropertyValue $Request.input }

    return $normalized
}

function Invoke-JsonScript {
    param([string]$ScriptPath, [string[]]$Arguments)
    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Script emitted no JSON: $ScriptPath" }
    try { $json = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Script emitted invalid JSON: $ScriptPath. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0 -and $null -eq $json.PSObject.Properties["ok"]) { throw "Script failed with exit code $($exitCode): $ScriptPath" }
    return $json
}

function Get-OrchStatus {
    return Invoke-JsonScript -ScriptPath $StatusScript -Arguments @("-Root", $Root)
}

function ConvertTo-AgentAvailability {
    param([object]$Slot)
    $hasTask = $null -ne $Slot.currentTask
    $hasLimit = $null -ne $Slot.limit
    $hasLock = $null -ne $Slot.manualLock
    $state = [string]$Slot.state
    $available = ($state -in @("idle", "recent")) -and !$hasTask -and !$hasLimit -and !$hasLock
    $reason = "ready"
    if ($hasTask) { $reason = "has_active_task" }
    elseif ($hasLimit) { $reason = "usage_limited" }
    elseif ($hasLock) { $reason = "manual_lock" }
    elseif ($state -in @("sleeping", "blocked", "locked", "stale", "active", "disabled")) { $reason = $state }
    return [pscustomobject]@{
        slot = [string]$Slot.name
        state = $state
        available = [bool]$available
        reason = $reason
        statusText = [string]$Slot.statusText
        currentTask = $Slot.currentTask
        blocker = $Slot.blocker
        limit = $Slot.limit
        manualLock = $Slot.manualLock
        latestLog = $(if ($Slot.latestLog) { [pscustomobject]@{ name = $Slot.latestLog.name; lastWriteTime = $Slot.latestLog.lastWriteTime; ageMinutes = $Slot.latestLog.ageMinutes; importantLine = $Slot.latestLog.importantLine } } else { $null })
        nextAction = $(if ($Slot.nextAction) { $Slot.nextAction.action } else { "" })
    }
}

function Get-AgentStatusTool {
    $status = Get-OrchStatus
    $agents = @($status.slots | ForEach-Object { ConvertTo-AgentAvailability -Slot $_ })
    return [pscustomobject]@{
        generatedAt = $status.generatedAt
        state = $status.state
        headline = $status.headline
        counts = $status.counts
        availability = $status.availability
        agents = $agents
        availableAgents = @($agents | Where-Object { $_.available })
        unavailableAgents = @($agents | Where-Object { !$_.available })
        nextAction = $status.nextAction
    }
}

function Get-QueueSummaryTool {
    $status = Get-OrchStatus
    return [pscustomobject]@{ generatedAt = $status.generatedAt; counts = $status.counts; nextAction = $status.nextAction; availability = $status.availability; queue = $status.tasks.queue; active = $status.tasks.active; failed = $status.tasks.failed }
}

function Get-RecentFailuresTool {
    param([int]$Limit = 10)
    $status = Get-OrchStatus
    return [pscustomobject]@{ generatedAt = $status.generatedAt; failed = @($status.tasks.failed | Select-Object -First $Limit); blockedSlots = @($status.slots | Where-Object { $_.state -in @("blocked", "sleeping", "locked", "stale") } | Select-Object -First $Limit); priorityWarnings = $status.priorityWarnings }
}

function Get-LatestAgentLogsTool {
    $status = Get-OrchStatus
    return [pscustomobject]@{
        generatedAt = $status.generatedAt
        logs = @($status.slots | ForEach-Object { [pscustomobject]@{ slot = $_.name; state = $_.state; latestLog = $(if ($_.latestLog) { [pscustomobject]@{ name = $_.latestLog.name; path = $_.latestLog.path; lastWriteTime = $_.latestLog.lastWriteTime; ageMinutes = $_.latestLog.ageMinutes; importantLine = $_.latestLog.importantLine; tail = $_.latestLog.tail } } else { $null }) } })
    }
}

function Get-McpCapabilityStatusTool {
    return Invoke-JsonScript -ScriptPath $CapabilityStatusScript -Arguments @("-Root", $Root, "-Port", [string]$Port)
}

function Get-GitHubIssuesCachedTool {
    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $GitHubCacheScript -Root $Root -Action "issues" 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Cache script emitted no output: $GitHubCacheScript" }
    try { $result = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Cache script emitted invalid JSON: $GitHubCacheScript. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0) { throw "Cache script failed with exit code $($exitCode): $GitHubCacheScript" }
    return $result
}

function Get-GitHubPrStatusCachedTool {
    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $GitHubCacheScript -Root $Root -Action "prs" 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Cache script emitted no output: $GitHubCacheScript" }
    try { $result = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Cache script emitted invalid JSON: $GitHubCacheScript. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0) { throw "Cache script failed with exit code $($exitCode): $GitHubCacheScript" }
    return $result
}

function Get-GameMakerProjectInfoTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerProjectInfoScript -Arguments $args
}

function Get-GameMakerCompilerErrorsTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerCompilerErrorsScript -Arguments $args
}

function Get-GameMakerSpriteAssetStatusTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerSpriteStatusScript -Arguments $args
}

function Get-GameMakerRoomEditorStatusTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerRoomStatusScript -Arguments $args
}

function Get-GameMakerBuildStatusTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerBuildStatusScript -Arguments $args
}

function Invoke-SyncRepositoryTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.remote) { $args += @("-Remote", [string]$Arguments.remote) }
    if ($Arguments -and $Arguments.branch) { $args += @("-Branch", [string]$Arguments.branch) }
    if ($Arguments -and $Arguments.dry_run) { $args += "-DryRun" }
    if ($Arguments -and $Arguments.plan_only) { $args += "-PlanOnly" }
    if ($Arguments -and $Arguments.allow_dirty) { $args += "-AllowDirty" }
    return Invoke-JsonScript -ScriptPath $RepoSyncScript -Arguments $args
}

function Invoke-TaskActionTool {
    param([string]$Action, [object]$Arguments)
    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$Arguments.task_path)) { throw "Missing required argument: task_path" }
    $args = @("-Root", $Root, "-Action", $Action, "-TaskPath", [string]$Arguments.task_path)
    if ($Arguments.reason) { $args += @("-Reason", [string]$Arguments.reason) }
    if ($Arguments.dry_run) { $args += "-DryRun" }
    if ($Arguments.allow_dirty) { $args += "-AllowDirty" }
    return Invoke-JsonScript -ScriptPath $TaskActionScript -Arguments $args
}

function Invoke-AgentActionTool {
    param([string]$Action, [object]$Arguments)
    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$Arguments.slot)) { throw "Missing required argument: slot" }
    $args = @("-Root", $Root, "-Action", $Action, "-SlotName", [string]$Arguments.slot)
    if ($Arguments.dry_run) { $args += "-DryRun" }
    if ($Arguments.headless) { $args += "-Headless" }
    return Invoke-JsonScript -ScriptPath $AgentActionScript -Arguments $args
}

function New-ToolTextResult {
    param([object]$Value)
    return [pscustomobject]@{ content = @([pscustomobject]@{ type = "text"; text = ($Value | ConvertTo-Json -Depth 80) }) }
}

function New-ObjectSchema {
    param([object]$Properties, [string[]]$Required = @())
    return [pscustomobject]@{ type = "object"; properties = $Properties; required = $Required; additionalProperties = $false }
}

function Get-ToolsList {
    $empty = New-ObjectSchema -Properties ([pscustomobject]@{})
    $taskProperties = [pscustomobject]@{ task_path = [pscustomobject]@{ type = "string" }; reason = [pscustomobject]@{ type = "string" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $false }; allow_dirty = [pscustomobject]@{ type = "boolean"; default = $false } }
    $agentProperties = [pscustomobject]@{ slot = [pscustomobject]@{ type = "string" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $false }; headless = [pscustomobject]@{ type = "boolean"; default = $false } }
    return [pscustomobject]@{
        tools = @(
            [pscustomobject]@{ name = "get_agent_status"; description = "Read current agent availability, wake timing, and next action."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_queue_summary"; description = "Read queue, active, and failed task summaries."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_recent_failures"; description = "Read recent failed tasks and blocked slots."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ limit = [pscustomobject]@{ type = "integer"; minimum = 1; maximum = 50; default = 10 } }) },
            [pscustomobject]@{ name = "get_latest_agent_logs"; description = "Read latest observed log tails for each agent slot."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_mcp_capability_status"; description = "Read MCP connector online/read-only/write capability status."; inputSchema = $empty },
            [pscustomobject]@{ name = "sync_repository"; description = "Safely fast-forward sync the local orchestrator repository. Defaults to dry_run=false and ff-only helper behavior."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ remote = [pscustomobject]@{ type = "string"; default = "origin" }; branch = [pscustomobject]@{ type = "string"; default = "master" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $false }; plan_only = [pscustomobject]@{ type = "boolean"; default = $false }; allow_dirty = [pscustomobject]@{ type = "boolean"; default = $false } }) },
            [pscustomobject]@{ name = "requeue_task"; description = "Move a task markdown file back to tasks/queue through the audited helper."; inputSchema = New-ObjectSchema -Properties $taskProperties -Required @("task_path") },
            [pscustomobject]@{ name = "fail_task"; description = "Move a task markdown file to tasks/failed through the audited helper."; inputSchema = New-ObjectSchema -Properties $taskProperties -Required @("task_path") },
            [pscustomobject]@{ name = "complete_task"; description = "Move a task markdown file to tasks/done through the audited helper."; inputSchema = New-ObjectSchema -Properties $taskProperties -Required @("task_path") },
            [pscustomobject]@{ name = "start_agent"; description = "Start a selected agent slot once through the audited helper."; inputSchema = New-ObjectSchema -Properties $agentProperties -Required @("slot") },
            [pscustomobject]@{ name = "rerun_agent"; description = "Rerun a selected agent slot once through the audited helper."; inputSchema = New-ObjectSchema -Properties $agentProperties -Required @("slot") },
            [pscustomobject]@{ name = "get_github_issues_cached"; description = "Read cached GitHub issues from the child-of-levistus project. Data is cached for 30 seconds."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_github_pr_status_cached"; description = "Read cached GitHub PR metadata from the child-of-levistus project. Data is cached for 30 seconds."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_gamemaker_project_info"; description = "Read GameMaker project metadata (name, version, resource count)."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) },
            [pscustomobject]@{ name = "get_gamemaker_compiler_errors"; description = "Parse GameMaker compiler output and return structured error list with line numbers."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) },
            [pscustomobject]@{ name = "get_sprite_asset_status"; description = "Validate sprite imports, frame counts, and dimensions in the GameMaker project."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) },
            [pscustomobject]@{ name = "get_room_editor_status"; description = "Validate room layouts, object placements, and room structure integrity."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) },
            [pscustomobject]@{ name = "get_game_build_status"; description = "Aggregate build status: compiler errors, asset validation, room structure (all Phase 1 checks)."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) }
        )
    }
}

function Invoke-ToolCall {
    param([string]$Name, [object]$Arguments)
    switch ($Name) {
        "get_agent_status" { return New-ToolTextResult -Value (Get-AgentStatusTool) }
        "get_queue_summary" { return New-ToolTextResult -Value (Get-QueueSummaryTool) }
        "get_recent_failures" { $limit = 10; if ($Arguments -and $null -ne $Arguments.limit) { $limit = [Math]::Max(1, [Math]::Min(50, [int]$Arguments.limit)) }; return New-ToolTextResult -Value (Get-RecentFailuresTool -Limit $limit) }
        "get_latest_agent_logs" { return New-ToolTextResult -Value (Get-LatestAgentLogsTool) }
        "get_mcp_capability_status" { return New-ToolTextResult -Value (Get-McpCapabilityStatusTool) }
        "sync_repository" { return New-ToolTextResult -Value (Invoke-SyncRepositoryTool -Arguments $Arguments) }
        "requeue_task" { return New-ToolTextResult -Value (Invoke-TaskActionTool -Action "requeue_task" -Arguments $Arguments) }
        "fail_task" { return New-ToolTextResult -Value (Invoke-TaskActionTool -Action "fail_task" -Arguments $Arguments) }
        "complete_task" { return New-ToolTextResult -Value (Invoke-TaskActionTool -Action "complete_task" -Arguments $Arguments) }
        "start_agent" { return New-ToolTextResult -Value (Invoke-AgentActionTool -Action "start_agent" -Arguments $Arguments) }
        "rerun_agent" { return New-ToolTextResult -Value (Invoke-AgentActionTool -Action "rerun_agent" -Arguments $Arguments) }
        "get_github_issues_cached" { return New-ToolTextResult -Value (Get-GitHubIssuesCachedTool) }
        "get_github_pr_status_cached" { return New-ToolTextResult -Value (Get-GitHubPrStatusCachedTool) }
        "get_gamemaker_project_info" { return New-ToolTextResult -Value (Get-GameMakerProjectInfoTool -Arguments $Arguments) }
        "get_gamemaker_compiler_errors" { return New-ToolTextResult -Value (Get-GameMakerCompilerErrorsTool -Arguments $Arguments) }
        "get_sprite_asset_status" { return New-ToolTextResult -Value (Get-GameMakerSpriteAssetStatusTool -Arguments $Arguments) }
        "get_room_editor_status" { return New-ToolTextResult -Value (Get-GameMakerRoomEditorStatusTool -Arguments $Arguments) }
        "get_game_build_status" { return New-ToolTextResult -Value (Get-GameMakerBuildStatusTool -Arguments $Arguments) }
        default { throw "Unknown tool: $Name" }
    }
}

function Get-JsonRpcProperty {
    param([object]$Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    if ($null -eq $Object.PSObject.Properties[$Name]) { return $null }
    return $Object.PSObject.Properties[$Name].Value
}

function Handle-McpJsonRpcRequest {
    param([object]$Request)
    if ($null -eq $Request) { return New-JsonRpcError -Id $null -Code -32700 -Message "Empty or invalid JSON request" }
    $id = Get-JsonRpcProperty -Object $Request -Name "id"
    $method = [string](Get-JsonRpcProperty -Object $Request -Name "method")
    $params = Get-JsonRpcProperty -Object $Request -Name "params"

    switch ($method) {
        "initialize" { return New-JsonRpcResult -Id $id -Result (New-McpInitializeResult) }
        "notifications/initialized" { return [pscustomobject]@{ jsonrpc = "2.0"; result = $null } }
        "tools/list" { return New-JsonRpcResult -Id $id -Result (Get-ToolsList) }
        "tools/call" {
            if ($null -eq $params) { return New-JsonRpcError -Id $id -Code -32602 -Message "Missing params object" }
            $toolName = [string](Get-JsonRpcProperty -Object $params -Name "name")
            if ([string]::IsNullOrWhiteSpace($toolName)) { $toolName = [string](Get-JsonRpcProperty -Object $params -Name "tool") }
            if ([string]::IsNullOrWhiteSpace($toolName)) { return New-JsonRpcError -Id $id -Code -32602 -Message "Missing tool name in params" }
            try {
                $toolArgs = Get-JsonRpcProperty -Object $params -Name "arguments"
                return New-JsonRpcResult -Id $id -Result (Invoke-ToolCall -Name $toolName -Arguments $toolArgs)
            }
            catch { return New-JsonRpcError -Id $id -Code -32000 -Message $_.Exception.Message }
        }
        default { return New-JsonRpcError -Id $id -Code -32601 -Message "Method not found: $method" }
    }
}

$listener = New-Object System.Net.HttpListener
$prefix = "http://127.0.0.1:$Port/"
$listener.Prefixes.Add($prefix)
$listener.Start()
Write-Host "Orch MCP server listening on $prefix"
Write-Host "Endpoint path: /mcp"
Write-Host "SSE endpoint path: /mcp/sse"
if ($NoAuth) { Write-Warning "NoAuth is enabled. Only use with a temporary local/tunnel endpoint." } else { Write-Host "Bearer token auth enabled. Token value is not printed." }
Write-Host "Press Ctrl+C to stop."

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $path = ""
        $stage = "route"
        try {
            $path = $context.Request.Url.AbsolutePath.TrimEnd("/")
            if ($context.Request.HttpMethod -eq "GET" -and $path -eq "/health") { Write-JsonResponse -Context $context -Body ([pscustomobject]@{ ok = $true; service = "gm-agent-orchestrator-mcp"; root = $Root; noAuth = [bool]$NoAuth }); continue }
            if ($path -ne "/mcp" -and $path -ne "/mcp/sse") { Write-TextResponse -Context $context -Body "Not found" -StatusCode 404; continue }
            if (!(Test-Authorized -Request $context.Request)) { Write-JsonResponse -Context $context -Body ([pscustomobject]@{ error = "unauthorized" }) -StatusCode 401; continue }
            if ($context.Request.HttpMethod -eq "GET" -and $path -eq "/mcp/sse") { Write-SseResponse -Context $context -Body (New-JsonRpcResult -Id $null -Result ([pscustomobject]@{ endpoint = "/mcp"; transport = "sse"; serverInfo = (New-McpInitializeResult).serverInfo })) -Event "endpoint"; continue }
            if ($context.Request.HttpMethod -eq "GET") { Write-TextResponse -Context $context -Body "gm-agent-orchestrator MCP endpoint is online. Use JSON-RPC POST requests or GET /mcp/sse for SSE discovery."; continue }
            if ($context.Request.HttpMethod -ne "POST") { Write-TextResponse -Context $context -Body "Method not allowed" -StatusCode 405; continue }
            $stage = "parse"
            $request = Read-RequestJson -Request $context.Request
            $stage = "dispatch"
            $response = Handle-McpJsonRpcRequest -Request $request
            $stage = "response"
            if ($path -eq "/mcp/sse" -or ([string]$context.Request.Headers["Accept"]) -match "text/event-stream") { Write-SseResponse -Context $context -Body $response }
            else { Write-JsonResponse -Context $context -Body $response }
        }
        catch { try { Write-JsonResponse -Context $context -Body ([pscustomobject]@{ error = "mcp_server_error"; message = $_.Exception.Message; path = $path; method = [string]$context.Request.HttpMethod; stage = $stage }) -StatusCode 500 } catch {} }
    }
}
finally {
    if ($listener.IsListening) { $listener.Stop() }
    $listener.Close()
}
