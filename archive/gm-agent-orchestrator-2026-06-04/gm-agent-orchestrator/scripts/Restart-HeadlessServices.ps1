[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$NoOrchestrator,
    [switch]$NoDashboard,
    [switch]$NoPulse,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$scripts = $PSScriptRoot
$logsDir = Join-Path $root "logs\headless"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$silentLauncher = Join-Path $scripts "Start-SilentProcess.ps1"
if (-not (Test-Path $silentLauncher)) {
    throw "Silent launcher was not found: $silentLauncher"
}

function Get-OrchestratorServiceProcess {
    param([string]$ScriptName)

    $pattern = [Regex]::Escape($ScriptName)
    return @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match $pattern -and
            $_.CommandLine -match [Regex]::Escape($root)
        })
}

function Stop-ServiceScriptProcess {
    param([string]$ScriptName)

    $processes = @(Get-OrchestratorServiceProcess -ScriptName $ScriptName)
    foreach ($process in $processes) {
        if ($DryRun) {
            Write-Host "[dry-run] Would stop $ScriptName PID $($process.ProcessId)"
            continue
        }

        if ($PSCmdlet.ShouldProcess("PID $($process.ProcessId)", "Stop $ScriptName")) {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped $ScriptName PID $($process.ProcessId)"
        }
    }
}

function Start-ServiceScriptProcess {
    param(
        [string]$Name,
        [string]$ScriptName,
        [string[]]$Arguments = @()
    )

    $scriptPath = Join-Path $scripts $ScriptName
    if (-not (Test-Path $scriptPath)) {
        throw "Service script was not found: $scriptPath"
    }

    $stdout = Join-Path $logsDir ("{0}.out.log" -f $Name)
    $stderr = Join-Path $logsDir ("{0}.err.log" -f $Name)
    $powershellArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath) + $Arguments

    if ($DryRun) {
        Write-Host "[dry-run] Would start ${Name}: powershell.exe $($powershellArgs -join ' ')"
        return
    }

    $result = & $silentLauncher `
        -FilePath "powershell.exe" `
        -ArgumentList $powershellArgs `
        -WorkingDirectory $root `
        -StdOutPath $stdout `
        -StdErrPath $stderr

    Write-Host "Started $Name PID $($result.processId)"
}

function Restart-DashboardService {
    $restartScript = Join-Path $scripts "Restart-DashboardServer.ps1"
    if (-not (Test-Path $restartScript)) {
        throw "Dashboard restart script was not found: $restartScript"
    }

    if ($DryRun) {
        Write-Host "[dry-run] Would bounce dashboard via Restart-DashboardServer.ps1 -Port 8765 -NoOpen -NoRefresh -Json"
        return
    }

    $resultJson = & $restartScript -Port 8765 -NoOpen -NoRefresh -Json
    $result = $resultJson | ConvertFrom-Json
    if ($result.state -ne 'succeeded') {
        throw "Dashboard restart failed: $($result.message)"
    }

    Write-Host "Restarted dashboard PID $($result.startedProcessId)"
}

$services = @()
if (-not $NoOrchestrator) {
    $services += [pscustomobject]@{
        name = "orchestrator"
        script = "Start-GmAgentOrchestrator.ps1"
        args = @("-Headless")
    }
}
if (-not $NoPulse) {
    $services += [pscustomobject]@{
        name = "server-health-pulse"
        script = "Monitor-ServerHealthPulse.ps1"
        args = @("-IntervalSeconds", "180")
    }
}

foreach ($service in $services) {
    Stop-ServiceScriptProcess -ScriptName $service.script
}

Start-Sleep -Milliseconds 750

foreach ($service in $services) {
    Start-ServiceScriptProcess -Name $service.name -ScriptName $service.script -Arguments $service.args
}

if (-not $NoDashboard) {
    Restart-DashboardService
}

$serviceNames = @($services | ForEach-Object { $_.name })
if (-not $NoDashboard) { $serviceNames += "dashboard" }

$status = [pscustomobject]@{
    ok = $true
    generatedAt = (Get-Date).ToString("o")
    root = $root
    dryRun = [bool]$DryRun
    services = @($serviceNames)
    logs = $logsDir
    dashboardUrl = "http://localhost:8765/dashboard/"
    serverHealthStatus = "status/server-health.json"
}

$status | ConvertTo-Json -Depth 5
