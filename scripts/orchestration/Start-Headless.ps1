[CmdletBinding()]
param(
    [switch]$NoDashboard,
    [switch]$NoPulse
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$scripts = $PSScriptRoot
$logsDir = Join-Path $root "logs\headless"
$silentLauncher = Join-Path $scripts "Start-SilentProcess.ps1"

if (-not (Test-Path $silentLauncher)) {
    throw "Silent launcher was not found: $silentLauncher"
}

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

function Start-HeadlessComponent {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$ScriptName,
        [string[]]$Arguments = @()
    )

    $scriptPath = Join-Path $scripts $ScriptName
    if (-not (Test-Path $scriptPath)) {
        throw "Component script was not found: $scriptPath"
    }

    $stdout = Join-Path $logsDir ("{0}.out.log" -f $Name)
    $stderr = Join-Path $logsDir ("{0}.err.log" -f $Name)
    $powershellArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath) + $Arguments

    $result = & $silentLauncher `
        -FilePath "powershell.exe" `
        -ArgumentList $powershellArgs `
        -WorkingDirectory $root `
        -StdOutPath $stdout `
        -StdErrPath $stderr

    Write-Host "[OK] $Name PID $($result.processId)"
}

Write-Host "Starting headless gm-agent-orchestrator..."

Start-HeadlessComponent `
    -Name "orchestrator" `
    -ScriptName "Start-GmAgentOrchestrator.ps1" `
    -Arguments @("-Headless")

if (-not $NoDashboard) {
    Start-HeadlessComponent `
        -Name "dashboard" `
        -ScriptName "Start-Dashboard.ps1" `
        -Arguments @("-NoOpen", "-NoRefresh")
}

if (-not $NoPulse) {
    Start-HeadlessComponent `
        -Name "pulse" `
        -ScriptName "Monitor-DashboardPulse.ps1" `
        -Arguments @("-IntervalSeconds", "60", "-Headless")
}

Write-Host "All components started in background. Logs: $logsDir"
