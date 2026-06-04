[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$script = Join-Path $Root "scripts\Get-OrchMcpCapabilityStatus.ps1"
if (-not (Test-Path $script)) {
    throw "Capability status script was not found: $script"
}

function New-TestRoot {
    $path = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-mcp-capability-test-{0}" -f [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path (Join-Path $path "scripts") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $path "config") | Out-Null
    return $path
}

function Add-EmptyScript {
    param(
        [string]$RootPath,
        [string]$Name
    )

    "# test placeholder" | Set-Content -Path (Join-Path $RootPath "scripts\$Name") -Encoding UTF8
}

function Add-AgentConfig {
    param(
        [string]$RootPath,
        [string]$CommandName = "powershell"
    )

    [pscustomobject]@{
        slots = @(
            [pscustomobject]@{
                name = "operator-intake"
                agent = "human-interface"
                role = "operator-intake"
                enabled = $true
                branch = "agent/operator-intake"
                routing = [pscustomobject]@{
                    directHumanRequestsFirst = $true
                    implementationEligible = $false
                }
                command = [pscustomobject]@{
                    start = @($CommandName, "-NoProfile", "-Command", "Write-Output intake")
                    resume = @($CommandName, "-NoProfile", "-Command", "Write-Output intake")
                }
            },
            [pscustomobject]@{
                name = "local-main"
                agent = "local-test-agent"
                role = "implementation"
                enabled = $true
                branch = "agent/local-main"
                command = [pscustomobject]@{
                    start = @($CommandName, "-NoProfile", "-Command", "Write-Output ok")
                    resume = @($CommandName, "-NoProfile", "-Command", "Write-Output ok")
                }
            },
            [pscustomobject]@{
                name = "remote-only"
                agent = "remote-test-agent"
                role = "review"
                enabled = $true
                branch = "agent/remote-only"
            }
        )
    } | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $RootPath "config\agents.json") -Encoding UTF8
}

function Invoke-CapabilityStatus {
    param([string]$RootPath)

    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $RootPath -NoNetworkProbe 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Capability script failed with exit code $LASTEXITCODE`: $($output -join "`n")"
    }

    return (($output | Out-String).Trim() | ConvertFrom-Json)
}

$roots = @()
try {
    $writableRoot = New-TestRoot
    $roots += $writableRoot
    foreach ($name in @(
        "Start-OrchMcpServer.ps1",
        "Get-OrchestratorStatus.ps1",
        "New-OrchestratorQueueTask.ps1",
        "Invoke-OrchestratorTaskAction.ps1",
        "Invoke-OrchestratorAgentAction.ps1",
        "Invoke-OrchestratorRepoSync.ps1",
        "Invoke-OrchestratorSafePowerShell.ps1"
    )) {
        Add-EmptyScript -RootPath $writableRoot -Name $name
    }
    Add-AgentConfig -RootPath $writableRoot

    $offlineWritable = Invoke-CapabilityStatus -RootPath $writableRoot
    if ($offlineWritable.mode -ne "offline_writable_when_started") { throw "Expected offline_writable_when_started, got $($offlineWritable.mode)." }
    if (-not $offlineWritable.capabilities.writable) { throw "Expected writable capability to be true when all action helpers and local execution are available." }
    if (-not $offlineWritable.capabilities.localExecution) { throw "Expected localExecution capability to be true when a PowerShell command runner is available." }
    if (-not $offlineWritable.localExecution.available) { throw "Expected local execution object to report available=true." }
    if (-not $offlineWritable.capabilities.safePowerShellRunner) { throw "Expected safePowerShellRunner capability to be true when script and local execution are available." }
    if ($offlineWritable.capabilities.safePowerShellRunnerToolName -ne "run_safe_powershell") { throw "Expected safe runner tool name run_safe_powershell, got $($offlineWritable.capabilities.safePowerShellRunnerToolName)." }
    if ($offlineWritable.safePowerShellRunner.toolName -ne "run_safe_powershell") { throw "safePowerShellRunner object should expose exact tool name." }
    if ($offlineWritable.safePowerShellRunner.auditDirectory -ne "logs/control-actions") { throw "safePowerShellRunner should expose audit directory." }
    if (-not $offlineWritable.safePowerShellRunner.allowlistOnly) { throw "safePowerShellRunner must declare allowlistOnly=true." }
    if ($offlineWritable.safePowerShellRunner.nextAction -ne "Start scripts/Start-OrchMcpServer.ps1 to expose run_safe_powershell through the MCP connector.") { throw "Offline writable status should direct the operator to start the MCP server before using run_safe_powershell." }

    Write-Host "Validated MCP connector capability status states."
}
finally {
    foreach ($path in $roots) {
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
    }
}
