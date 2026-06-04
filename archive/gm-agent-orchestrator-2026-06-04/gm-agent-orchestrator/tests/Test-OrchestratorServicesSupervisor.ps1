[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    $Root = (Resolve-Path (Join-Path $scriptDir "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$script = Join-Path $Root "scripts\Start-OrchestratorServices.ps1"
if (-not (Test-Path $script)) {
    throw "Service supervisor script not found: $script"
}

$exampleConfigPath = Join-Path $Root "config\local-services.example.json"
if (-not (Test-Path $exampleConfigPath)) {
    throw "Example service registry not found: $exampleConfigPath"
}

$exampleConfig = Get-Content $exampleConfigPath -Raw | ConvertFrom-Json
$exampleMcp = @($exampleConfig.services | Where-Object { $_.name -eq "mcp" } | Select-Object -First 1)
if ($null -eq $exampleMcp) {
    throw "Expected example service registry to include MCP service."
}
if (@($exampleMcp.args) -notcontains "-NoAuth") {
    throw "Startup MCP service args must include -NoAuth for connector compatibility."
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-svc-sup-test-{0}" -f [Guid]::NewGuid().ToString("N"))
$listener = $null
try {
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "config") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "status") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "scripts") | Out-Null

    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), 0)
    $listener.Start()
    $wrongProcessPort = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port

    $configPath = Join-Path $tempRoot "config\local-services.json"
    @{
        services = @(
            @{
                name = "dashboard"
                enabled = $true
                required = $true
                command = "powershell.exe"
                args = @("-NoProfile")
                healthUrl = "http://127.0.0.1:1"
                port = 0
            },
            @{
                name = "mcp"
                enabled = $true
                required = $true
                command = "powershell.exe"
                args = @("-NoProfile")
                healthUrl = "http://127.0.0.1:$wrongProcessPort/health"
                port = $wrongProcessPort
            },
            @{
                name = "ngrok"
                enabled = $true
                required = $false
                command = "ngrok.exe"
                args = @("http", "8787", "--url", "example.ngrok-free.app")
                healthUrl = $null
                port = $null
                processName = "ngrok-orchestrator-test-never-running"
                windowMode = "operator_window"
                windowStyle = "Normal"
            }
        )
    } | ConvertTo-Json -Depth 20 | Set-Content -Path $configPath -Encoding UTF8

    Write-Host "Running dry-run supervisor test..."
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $tempRoot -Once -DryRun 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Supervisor dry run failed: $($output -join "`n")" }
    
    $status = $output | Out-String | ConvertFrom-Json
    if ($status.services[0].name -ne "dashboard") { throw "Expected service name 'dashboard'" }
    if ($status.services[0].state -ne "offline") { throw "Expected state 'offline' for unreachable endpoint" }
    $mcp = @($status.services | Where-Object { $_.name -eq "mcp" } | Select-Object -First 1)
    if ($null -eq $mcp) { throw "Expected MCP service entry in dry-run supervisor status" }
    if ($mcp.state -ne "offline") { throw "Expected MCP to stay offline when healthUrl fails even if the port is open" }
    if ($mcp.ok) { throw "Expected MCP ok=false when only raw TCP port is available" }
    $ngrok = @($status.services | Where-Object { $_.name -eq "ngrok" } | Select-Object -First 1)
    if ($null -eq $ngrok) { throw "Expected ngrok service entry in dry-run supervisor status" }
    if ($ngrok.state -ne "offline") { throw "Expected ngrok to be offline in dry-run test fixture" }
    if ($ngrok.plannedAction -ne "would_start") { throw "Expected ngrok plannedAction would_start in dry-run" }
    if ($ngrok.windowMode -ne "operator_window") { throw "Expected ngrok windowMode operator_window" }
    if (Test-Path (Join-Path $tempRoot "status\services.json")) { throw "Dry run should not write status file" }

    Write-Host "Service supervisor dry-run tests passed."
}
finally {
    if ($null -ne $listener) { $listener.Stop() }
    Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
