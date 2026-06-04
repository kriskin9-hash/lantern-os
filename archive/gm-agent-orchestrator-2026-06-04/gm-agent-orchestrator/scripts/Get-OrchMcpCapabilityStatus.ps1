[CmdletBinding()]
param(
    [string]$Root = "",
    [int]$Port = 8787,
    [switch]$NoNetworkProbe
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function Get-RelativePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    return $Path.Replace($Root, "").TrimStart("\")
}

function Test-RequiredScript {
    param(
        [string]$CheckName,
        [string]$ScriptPath,
        [string]$Capability
    )

    $exists = Test-Path $ScriptPath
    return [pscustomobject]@{
        name = $CheckName
        capability = $Capability
        available = [bool]$exists
        path = Get-RelativePath -Path $ScriptPath
        blocker = $(if ($exists) { "" } else { "missing_script" })
    }
}

function Resolve-PowerShellCommand {
    foreach ($candidate in @("powershell", "pwsh")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $command -and -not [string]::IsNullOrWhiteSpace([string]$command.Source)) {
            return [pscustomobject]@{
                available = $true
                command = $candidate
                path = [string]$command.Source
                blocker = ""
                nextAction = "Use the local PowerShell command runner for MCP helper scripts."
            }
        }
    }

    try {
        $current = Get-Process -Id $PID -ErrorAction Stop
        if ($null -ne $current -and -not [string]::IsNullOrWhiteSpace([string]$current.Path)) {
            return [pscustomobject]@{
                available = $true
                command = [string]$current.Path
                path = [string]$current.Path
                blocker = ""
                nextAction = "Use the current PowerShell host path for MCP helper scripts."
            }
        }
    }
    catch {}

    return [pscustomobject]@{
        available = $false
        command = ""
        path = ""
        blocker = "missing_powershell_command"
        nextAction = "Install or expose powershell/pwsh on PATH before using local MCP actions."
    }
}

function Read-JsonFileOrNull {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path $Path)) { return $null }
    try { return Get-Content $Path -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { return $null }
}

function Get-ConfigPath {
    param([string]$Name)
    $local = Join-Path $Root ("config\{0}.json" -f $Name)
    $example = Join-Path $Root ("config\{0}.example.json" -f $Name)
    if (Test-Path $local) { return $local }
    if (Test-Path $example) { return $example }
    return ""
}

function Test-AgentLocalCapability {
    param([object]$Slot)

    $slotName = $(if ($null -ne $Slot.name) { [string]$Slot.name } else { "" })
    $enabled = $(if ($null -ne $Slot.PSObject.Properties["enabled"]) { [bool]$Slot.enabled } else { $false })
    $hasStartCommand = $false
    $firstCommand = ""
    if ($null -ne $Slot.PSObject.Properties["command"] -and $null -ne $Slot.command -and $null -ne $Slot.command.PSObject.Properties["start"]) {
        $startCommand = @($Slot.command.start)
        $hasStartCommand = $startCommand.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$startCommand[0])
        if ($hasStartCommand) { $firstCommand = [string]$startCommand[0] }
    }

    $available = $enabled -and $hasStartCommand
    $blocker = ""
    if (-not $enabled) { $blocker = "disabled" }
    elseif (-not $hasStartCommand) { $blocker = "missing_start_command" }

    return [pscustomobject]@{
        slot = $slotName
        agent = $(if ($null -ne $Slot.agent) { [string]$Slot.agent } else { "" })
        role = $(if ($null -ne $Slot.PSObject.Properties["role"]) { [string]$Slot.role } else { "" })
        enabled = [bool]$enabled
        available = [bool]$available
        localCapable = [bool]$available
        command = $firstCommand
        blocker = $blocker
        nextAction = $(if ($available) { "Agent can be started through the local orchestrator command path." } elseif ($blocker -eq "disabled") { "Enable the slot before routing local work." } else { "Add a local command.start entry before routing local work to this slot." })
    }
}

function Get-LocalAgentCapabilities {
    $configPath = Get-ConfigPath -Name "agents"
    $config = Read-JsonFileOrNull -Path $configPath
    $agents = @()
    if ($null -ne $config -and $null -ne $config.PSObject.Properties["slots"]) {
        $agents = @($config.slots | Where-Object { $null -ne $_.name -and -not [string]::IsNullOrWhiteSpace([string]$_.name) } | ForEach-Object { Test-AgentLocalCapability -Slot $_ })
    }

    return [pscustomobject]@{
        source = $(if ([string]::IsNullOrWhiteSpace($configPath)) { "" } else { Get-RelativePath -Path $configPath })
        available = @($agents | Where-Object { $_.available })
        blocked = @($agents | Where-Object { -not $_.available })
        all = $agents
    }
}

function Test-LocalPortOpen {
    param([int]$PortNumber)

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect("127.0.0.1", $PortNumber, $null, $null)
        $connected = $async.AsyncWaitHandle.WaitOne(750, $false)
        if (-not $connected) { return $false }
        $client.EndConnect($async)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

$serverScript = Join-Path $Root "scripts\Start-OrchMcpServer.ps1"
$statusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
$queueCreateScript = Join-Path $Root "scripts\New-OrchestratorQueueTask.ps1"
$taskActionScript = Join-Path $Root "scripts\Invoke-OrchestratorTaskAction.ps1"
$agentActionScript = Join-Path $Root "scripts\Invoke-OrchestratorAgentAction.ps1"
$repoSyncScript = Join-Path $Root "scripts\Invoke-OrchestratorRepoSync.ps1"
$safeRunnerScript = Join-Path $Root "scripts\Invoke-OrchestratorSafePowerShell.ps1"
$safeRunnerToolName = "run_safe_powershell"

$checks = @()
$checks += Test-RequiredScript -CheckName "mcp_server" -ScriptPath $serverScript -Capability "serve_mcp"
$checks += Test-RequiredScript -CheckName "status" -ScriptPath $statusScript -Capability "read_status"
$checks += Test-RequiredScript -CheckName "queue_create" -ScriptPath $queueCreateScript -Capability "write_queue_task"
$checks += Test-RequiredScript -CheckName "task_actions" -ScriptPath $taskActionScript -Capability "move_tasks"
$checks += Test-RequiredScript -CheckName "agent_actions" -ScriptPath $agentActionScript -Capability "control_agents"
$checks += Test-RequiredScript -CheckName "repo_sync" -ScriptPath $repoSyncScript -Capability "sync_repo"
$checks += Test-RequiredScript -CheckName "safe_powershell_runner" -ScriptPath $safeRunnerScript -Capability "run_safe_powershell"

$localExecution = Resolve-PowerShellCommand
$localAgents = Get-LocalAgentCapabilities
$hasLocalExecution = [bool]$localExecution.available
$hasLocalCapableAgent = @($localAgents.available).Count -gt 0
$hasRead = @($checks | Where-Object { $_.capability -eq "read_status" -and $_.available }).Count -gt 0
$writeChecks = @($checks | Where-Object { $_.capability -in @("write_queue_task", "move_tasks", "control_agents", "sync_repo", "run_safe_powershell") })
$hasWriteScripts = @($writeChecks | Where-Object { -not $_.available }).Count -eq 0
$hasSafeRunnerScript = @($checks | Where-Object { $_.capability -eq "run_safe_powershell" -and $_.available }).Count -gt 0
$hasSafeRunner = $hasSafeRunnerScript -and $hasLocalExecution
$hasWrite = $hasWriteScripts -and $hasLocalExecution
$hasServer = @($checks | Where-Object { $_.capability -eq "serve_mcp" -and $_.available }).Count -gt 0
$portOpen = $false
if (-not $NoNetworkProbe) {
    $portOpen = Test-LocalPortOpen -PortNumber $Port
}

$missing = @($checks | Where-Object { -not $_.available })
$runtimeBlockers = @()
if (-not $hasLocalExecution) {
    $runtimeBlockers += [pscustomobject]@{ capability = "local_execution"; blocker = $localExecution.blocker; path = $localExecution.path }
}
if (-not $hasLocalCapableAgent) {
    $runtimeBlockers += [pscustomobject]@{ capability = "local_capable_agents"; blocker = "no_available_local_agents"; path = $localAgents.source }
}
$allBlockers = @($missing) + @($runtimeBlockers)
$state = "blocked"
$mode = "offline"
$nextAction = "Start the MCP server after restoring missing scripts."

if ($hasServer -and $portOpen -and $hasRead -and $hasWrite) {
    $state = "ready"
    $mode = "online_writable"
    $nextAction = "Use the MCP connector action path."
}
elseif ($hasServer -and $portOpen -and $hasRead -and -not $hasWrite) {
    $state = "degraded"
    $mode = "online_read_only"
    $nextAction = "Restore missing write/action helpers or local execution before using connector actions."
}
elseif ($hasServer -and -not $portOpen -and $hasRead -and $hasWrite) {
    $state = "blocked"
    $mode = "offline_writable_when_started"
    $nextAction = "Start scripts/Start-OrchMcpServer.ps1 on the local machine, then re-run this health check."
}
elseif ($hasRead -and -not $hasWrite) {
    $state = "degraded"
    $mode = "local_read_only"
    $nextAction = "Restore missing write/action helpers or local execution, then start the MCP server."
}

[pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    state = $state
    mode = $mode
    root = $Root
    port = $Port
    networkProbe = [bool](-not $NoNetworkProbe)
    server = [pscustomobject]@{
        scriptAvailable = [bool]$hasServer
        portOpen = [bool]$portOpen
        healthUrl = "http://127.0.0.1:$Port/health"
        mcpUrl = "http://127.0.0.1:$Port/mcp"
    }
    localExecution = $localExecution
    localAgents = $localAgents
    safePowerShellRunner = [pscustomobject]@{
        toolName = $safeRunnerToolName
        scriptAvailable = [bool]$hasSafeRunnerScript
        available = [bool]$hasSafeRunner
        scriptPath = Get-RelativePath -Path $safeRunnerScript
        auditDirectory = "logs/control-actions"
        allowlistOnly = $true
        mcpDispatchRequired = $true
        nextAction = $(if ($hasSafeRunner) { if ($portOpen) { "Use the MCP connector action path to invoke run_safe_powershell." } else { "Start scripts/Start-OrchMcpServer.ps1 to expose run_safe_powershell through the MCP connector." } } else { "Restore Invoke-OrchestratorSafePowerShell.ps1 and local PowerShell execution before exposing run_safe_powershell." })
    }
    capabilities = [pscustomobject]@{
        readStatus = [bool]$hasRead
        writeQueueTask = [bool](@($checks | Where-Object { $_.capability -eq "write_queue_task" -and $_.available }).Count -gt 0)
        moveTasks = [bool](@($checks | Where-Object { $_.capability -eq "move_tasks" -and $_.available }).Count -gt 0)
        controlAgents = [bool](@($checks | Where-Object { $_.capability -eq "control_agents" -and $_.available }).Count -gt 0)
        syncRepo = [bool](@($checks | Where-Object { $_.capability -eq "sync_repo" -and $_.available }).Count -gt 0)
        safePowerShellRunner = [bool]$hasSafeRunner
        safePowerShellRunnerToolName = $safeRunnerToolName
        localExecution = [bool]$hasLocalExecution
        localCapableAgents = [bool]$hasLocalCapableAgent
        writable = [bool]$hasWrite
    }
    checks = $checks
    blockers = @($allBlockers | ForEach-Object { [pscustomobject]@{ capability = $_.capability; blocker = $_.blocker; path = $_.path } })
    nextAction = [pscustomobject]@{
        action = $nextAction
        owner = $(if ($mode -like "offline*") { "local-orchestrator" } else { "orchestrator" })
        blockedBy = $(if ($allBlockers.Count -gt 0) { "missing or unavailable local capability" } elseif (-not $portOpen) { "mcp server offline" } else { "none" })
    }
} | ConvertTo-Json -Depth 20
