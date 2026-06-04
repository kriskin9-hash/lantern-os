[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $Root "scripts\Monitor-ServerHealthPulse.ps1"
if (-not (Test-Path $script)) {
    throw "Server health pulse script was not found: $script"
}

function Start-FakeJsonServer {
    param([string]$Json)

    $probe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), 0)
    $probe.Start()
    $port = ([System.Net.IPEndPoint]$probe.LocalEndpoint).Port
    $probe.Stop()

    $job = Start-Job -ScriptBlock {
        param([int]$Port, [string]$Body)

        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $Port)
        $listener.Start()
        try {
            $client = $listener.AcceptTcpClient()
            try {
                $stream = $client.GetStream()
                $buffer = New-Object byte[] 1024
                $stream.Read($buffer, 0, $buffer.Length) | Out-Null
                $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
                $header = "HTTP/1.1 200 OK`r`nContent-Type: application/json`r`nContent-Length: $($bodyBytes.Length)`r`nConnection: close`r`n`r`n"
                $headerBytes = [System.Text.Encoding]::ASCII.GetBytes($header)
                $stream.Write($headerBytes, 0, $headerBytes.Length)
                $stream.Write($bodyBytes, 0, $bodyBytes.Length)
            }
            finally {
                $client.Close()
            }
        }
        finally {
            $listener.Stop()
        }
    } -ArgumentList $port, $Json

    Start-Sleep -Milliseconds 300
    return [pscustomobject]@{
        port = $port
        job = $job
    }
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-server-health-test-{0}" -f [Guid]::NewGuid().ToString("N"))
$jobs = @()
try {
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "config") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "scripts") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "status") | Out-Null

    @{
        services = @(
            @{
                name = "ngrok"
                enabled = $true
                required = $false
                command = "ngrok.exe"
                args = @("http", "8787", "--url", "example.ngrok-free.app")
                processName = "ngrok"
            }
        )
    } | ConvertTo-Json -Depth 20 | Set-Content -Path (Join-Path $tempRoot "config\local-services.json") -Encoding UTF8

    $helperPath = Join-Path $tempRoot "scripts\Get-OrchMcpCapabilityStatus.ps1"
    @'
[CmdletBinding()]
param([string]$Root = "", [switch]$NoNetworkProbe)
[pscustomobject]@{
    mode = "offline_writable_when_started"
    capabilities = [pscustomobject]@{
        writable = $true
        localExecution = $true
        localCapableAgents = $true
    }
    nextAction = [pscustomobject]@{
        action = "Start scripts/Start-OrchMcpServer.ps1 on the local machine."
    }
} | ConvertTo-Json -Depth 10
'@ | Set-Content -Path $helperPath -Encoding UTF8

    $statusPath = Join-Path $tempRoot "status\server-health.json"
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $script `
        -Root $tempRoot `
        -Once `
        -StatusPath $statusPath `
        -DashboardUrl "http://127.0.0.1:1/api/status" `
        -McpHealthUrl "http://127.0.0.1:1/health" `
        -NgrokProcessName ([System.Diagnostics.Process]::GetCurrentProcess().ProcessName) `
        -NgrokApiUrl "http://127.0.0.1:1/api/tunnels" `
        -NgrokExpectedHost "example.ngrok-free.app" `
        -NgrokExpectedLocalPort 8787 `
        -TimeoutSeconds 1 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "Server health pulse failed: $($output -join "`n")"
    }

    if (-not (Test-Path $statusPath)) {
        throw "Expected server health status file to be written."
    }

    $status = Get-Content $statusPath -Raw | ConvertFrom-Json -ErrorAction Stop
    if ($status.state -ne "offline") {
        throw "Expected offline state for unreachable test endpoints, got $($status.state)."
    }
    if ($status.ok) {
        throw "Expected ok=false for unreachable test endpoints."
    }
    if (@($status.servers | Where-Object { $_.name -eq "dashboard" -and $_.state -eq "offline" }).Count -ne 1) {
        throw "Expected dashboard server offline entry."
    }
    if (@($status.servers | Where-Object { $_.name -eq "mcp" -and $_.state -eq "offline" }).Count -ne 1) {
        throw "Expected MCP server offline entry."
    }
    if (@($status.servers | Where-Object { $_.name -eq "ngrok" }).Count -ne 1) {
        throw "Expected ngrok server entry."
    }
    $ngrok = @($status.servers | Where-Object { $_.name -eq "ngrok" } | Select-Object -First 1)
    if ($ngrok.state -eq "online" -or $ngrok.ok) {
        throw "Expected ngrok process-only evidence to be degraded, not online."
    }
    if ($ngrok.blocker -notmatch "gateway_identity_unverified") {
        throw "Expected ngrok identity verification blocker when API cannot verify the tunnel."
    }

    $matchingTunnelJson = @{
        tunnels = @(
            @{
                public_url = "https://example.ngrok-free.app"
                config = @{ addr = "http://localhost:8787" }
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress
    $server = Start-FakeJsonServer -Json $matchingTunnelJson
    $jobs += $server.job
    $matchStatusPath = Join-Path $tempRoot "status\server-health-match.json"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $script `
        -Root $tempRoot `
        -Once `
        -StatusPath $matchStatusPath `
        -DashboardUrl "http://127.0.0.1:1/api/status" `
        -McpHealthUrl "http://127.0.0.1:1/health" `
        -NgrokProcessName ([System.Diagnostics.Process]::GetCurrentProcess().ProcessName) `
        -NgrokApiUrl "http://127.0.0.1:$($server.port)/api/tunnels" `
        -NgrokExpectedHost "example.ngrok-free.app" `
        -NgrokExpectedLocalPort 8787 `
        -TimeoutSeconds 1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Matching ngrok tunnel fixture failed." }
    $matchStatus = Get-Content $matchStatusPath -Raw | ConvertFrom-Json -ErrorAction Stop
    $matchingNgrok = @($matchStatus.servers | Where-Object { $_.name -eq "ngrok" } | Select-Object -First 1)
    if ($matchingNgrok.state -ne "online" -or -not $matchingNgrok.ok) {
        throw "Expected verified ngrok tunnel to be online."
    }
    if ($matchingNgrok.url -ne "https://example.ngrok-free.app/mcp") {
        throw "Expected ngrok URL to report the external MCP endpoint."
    }

    $wrongHostTunnelJson = @{
        tunnels = @(
            @{
                public_url = "https://not-example.ngrok-free.app"
                config = @{ addr = "http://localhost:8787" }
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress
    $wrongHostServer = Start-FakeJsonServer -Json $wrongHostTunnelJson
    $jobs += $wrongHostServer.job
    $mismatchStatusPath = Join-Path $tempRoot "status\server-health-mismatch.json"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $script `
        -Root $tempRoot `
        -Once `
        -StatusPath $mismatchStatusPath `
        -DashboardUrl "http://127.0.0.1:1/api/status" `
        -McpHealthUrl "http://127.0.0.1:1/health" `
        -NgrokProcessName ([System.Diagnostics.Process]::GetCurrentProcess().ProcessName) `
        -NgrokApiUrl "http://127.0.0.1:$($wrongHostServer.port)/api/tunnels" `
        -NgrokExpectedHost "example.ngrok-free.app" `
        -NgrokExpectedLocalPort 8787 `
        -TimeoutSeconds 1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Mismatched ngrok tunnel fixture failed." }
    $mismatchStatus = Get-Content $mismatchStatusPath -Raw | ConvertFrom-Json -ErrorAction Stop
    $mismatchedNgrok = @($mismatchStatus.servers | Where-Object { $_.name -eq "ngrok" } | Select-Object -First 1)
    if ($mismatchedNgrok.state -eq "online" -or $mismatchedNgrok.ok) {
        throw "Expected wrong ngrok host to stay degraded."
    }
    if ($mismatchedNgrok.blocker -ne "gateway_identity_mismatch") {
        throw "Expected ngrok host mismatch blocker."
    }
    if ($status.mcpCapability.mode -ne "offline_writable_when_started") {
        throw "Expected MCP capability helper output to be included."
    }
    if (-not $status.mcpCapability.writable) {
        throw "Expected MCP capability writable=true from helper fixture."
    }
    if ($status.nextAction -notmatch "dashboard" -or $status.nextAction -notmatch "mcp") {
        throw "Expected nextAction to name offline servers."
    }

    Write-Host "Validated server health pulse contract."
}
finally {
    foreach ($job in $jobs) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
