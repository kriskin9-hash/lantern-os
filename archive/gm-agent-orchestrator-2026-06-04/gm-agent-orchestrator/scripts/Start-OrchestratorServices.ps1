[CmdletBinding()]
param(
    [string]$Root = "",
    [switch]$DryRun,
    [switch]$Once,
    [int]$IntervalSeconds = 300,
    [int]$HealthTimeoutSeconds = 10,
    [switch]$EnforceHeadlessMode
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$ConfigPath = Join-Path $Root "config\local-services.json"
if (-not (Test-Path $ConfigPath)) {
    $ConfigPath = Join-Path $Root "config\local-services.example.json"
}

if (-not (Test-Path $ConfigPath)) {
    throw "Service registry config not found at $ConfigPath"
}

$StatusPath = Join-Path $Root "status\services.json"

function Get-OptionalJsonProperty {
    param(
        [object]$Object,
        [string]$Name
    )

    if ($null -eq $Object) { return $null }
    if ($null -eq $Object.PSObject.Properties[$Name]) { return $null }
    return $Object.PSObject.Properties[$Name].Value
}

function Test-ServiceHealth {
    param([object]$Service)

    $healthUrl = Get-OptionalJsonProperty -Object $Service -Name "healthUrl"
    $port = Get-OptionalJsonProperty -Object $Service -Name "port"
    $processName = Get-OptionalJsonProperty -Object $Service -Name "processName"

    # HTTP health checks are authoritative when configured. A raw open TCP port
    # can be the wrong process, a dead listener, or an auth-blocked service.
    # Use TCP/process fallback only for services that do not expose healthUrl.
    # Keep the timeout bounded, but allow enough headroom for the single-threaded
    # MCP listener and dashboard status refresh to avoid false offline reports.
    $httpOnline = $false
    if (-not [string]::IsNullOrWhiteSpace([string]$healthUrl)) {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec $HealthTimeoutSeconds -ErrorAction Stop
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
                $httpOnline = $true
            }
        }
        catch {}

        if ($httpOnline) { return "online" }
        return "offline"
    }

    if ($null -ne $port -and [int]$port -gt 0) {
        $connection = New-Object System.Net.Sockets.TcpClient
        try {
            $connection.Connect("127.0.0.1", [int]$port)
            return "online"
        }
        catch {}
        finally {
            if ($null -ne $connection) { $connection.Close() }
        }
    }

    if (-not [string]::IsNullOrWhiteSpace([string]$processName)) {
        if (Get-Process -Name $processName -ErrorAction SilentlyContinue) {
            return "online"
        }
    }

    return "offline"
}

function Invoke-ServiceSupervisor {
    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    $results = @()

    foreach ($service in $config.services) {
        if ($service.enabled -eq $false) {
            $results += [pscustomobject]@{
                name = $service.name
                state = "disabled"
                ok = $true
                lastCheckedAt = (Get-Date).ToString("o")
            }
            continue
        }

        $state = Test-ServiceHealth -Service $service
        $ok = [bool]($state -eq "online")

        if ($state -eq "offline" -and -not $DryRun) {
            Write-Host "Service $($service.name) is offline. Starting..." -ForegroundColor Yellow
            $windowStyle = Get-OptionalJsonProperty -Object $service -Name "windowStyle"
            if ([string]::IsNullOrWhiteSpace([string]$windowStyle)) {
                $windowStyle = "Hidden"
            }

            # Enforce headless mode if requested (suppresses all visible windows)
            if ($EnforceHeadlessMode) {
                $windowStyle = "Hidden"
            }
            
            $startArgs = @{
                FilePath = $service.command
                ArgumentList = $service.args
                WorkingDirectory = $Root
                WindowStyle = $windowStyle
            }

            try {
                Start-Process @startArgs
                $state = "starting"
            }
            catch {
                Write-Error "Failed to start service $($service.name): $($_.Exception.Message)"
                $state = "failed_to_start"
            }
        }

        $results += [pscustomobject]@{
            name = $service.name
            required = $(if ($null -eq $service.PSObject.Properties["required"]) { $false } else { [bool]$service.required })
            state = $state
            ok = $ok
            lastCheckedAt = (Get-Date).ToString("o")
            windowMode = $(if ($null -eq $service.PSObject.Properties["windowMode"]) { "unknown" } else { [string]$service.windowMode })
            plannedAction = $(if ($ok) { "none" } elseif ($DryRun) { "would_start" } else { "start_requested" })
            nextAction = $(if ($ok) { "No action required." } elseif ($DryRun) { "Supervisor would start this service when run without -DryRun." } else { "Monitor service startup." })
        }
    }

    $status = [pscustomobject]@{
        generatedAt = (Get-Date).ToString("o")
        dryRun = $DryRun
        services = $results
    }

    if (-not $DryRun) {
        $statusDir = Split-Path -Parent $StatusPath
        if (-not (Test-Path $statusDir)) { New-Item -ItemType Directory -Path $statusDir -Force | Out-Null }
        $status | ConvertTo-Json -Depth 20 | Set-Content -Path $StatusPath -Encoding UTF8
    }

    return $status
}

if ($Once) {
    Invoke-ServiceSupervisor | ConvertTo-Json -Depth 20
    return
}

Write-Host "Orchestrator Service Supervisor running every $IntervalSeconds seconds."
while ($true) {
    $status = Invoke-ServiceSupervisor
    Write-Host "[$($status.generatedAt)] Supervisor check complete. Services: $((@($status.services | ForEach-Object { "$($_.name)=$($_.state)" }) -join ', '))"
    Start-Sleep -Seconds $IntervalSeconds
}
