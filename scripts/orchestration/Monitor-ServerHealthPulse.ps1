[CmdletBinding()]
param(
    [string]$Root = "",
    [int]$IntervalSeconds = 180,
    [switch]$Once,
    [string]$StatusPath = "",
    [string]$DashboardUrl = "http://localhost:8765/api/status",
    [string]$McpHealthUrl = "http://127.0.0.1:8787/health",
    [string]$NgrokProcessName = "ngrok",
    [string]$NgrokApiUrl = "http://127.0.0.1:4040/api/tunnels",
    [string]$NgrokExpectedHost = "",
    [int]$NgrokExpectedLocalPort = 0,
    [int]$TimeoutSeconds = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

if ([string]::IsNullOrWhiteSpace($StatusPath)) {
    $StatusPath = Join-Path $Root "status\server-health.json"
}

function Test-HttpEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$RecoveryAction,
        [int]$TimeoutSec
    )

    $started = Get-Date
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        $elapsedMs = [Math]::Round(((Get-Date) - $started).TotalMilliseconds)
        $online = $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
        return [pscustomobject]@{
            name = $Name
            url = $Url
            state = $(if ($online) { "online" } else { "degraded" })
            ok = [bool]$online
            statusCode = [int]$response.StatusCode
            latencyMs = [int]$elapsedMs
            checkedAt = (Get-Date).ToString("o")
            blocker = $(if ($online) { "" } else { "unexpected_status_code" })
            nextAction = $(if ($online) { "No action required." } else { $RecoveryAction })
        }
    }
    catch {
        $elapsedMs = [Math]::Round(((Get-Date) - $started).TotalMilliseconds)
        return [pscustomobject]@{
            name = $Name
            url = $Url
            state = "offline"
            ok = $false
            statusCode = 0
            latencyMs = [int]$elapsedMs
            checkedAt = (Get-Date).ToString("o")
            blocker = $_.Exception.Message
            nextAction = $RecoveryAction
        }
    }
}

function Get-McpCapabilitySnapshot {
    param([string]$RootPath)

    $helper = Join-Path $RootPath "scripts\Get-OrchMcpCapabilityStatus.ps1"
    if (-not (Test-Path $helper)) {
        return [pscustomobject]@{
            available = $false
            blocker = "missing Get-OrchMcpCapabilityStatus.ps1"
            mode = "unknown"
            nextAction = "Restore the MCP capability helper."
        }
    }

    try {
        $json = & $helper -Root $RootPath -NoNetworkProbe 2>&1
        $jsonText = ($json | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($jsonText)) {
            return [pscustomobject]@{
                available = $false
                blocker = "MCP capability helper returned no output."
                mode = "unknown"
                nextAction = "Fix the MCP capability helper before trusting MCP runtime status."
            }
        }

        $status = $jsonText | ConvertFrom-Json -ErrorAction Stop
        return [pscustomobject]@{
            available = $true
            blocker = ""
            mode = $status.mode
            writable = [bool]$status.capabilities.writable
            localExecution = [bool]$status.capabilities.localExecution
            localCapableAgents = [bool]$status.capabilities.localCapableAgents
            nextAction = $status.nextAction.action
        }
    }
    catch {
        return [pscustomobject]@{
            available = $false
            blocker = $_.Exception.Message
            mode = "unknown"
            nextAction = "Fix the MCP capability helper before trusting MCP runtime status."
        }
    }
}

function Write-ServerHealthStatus {
    param([object]$Status)

    $directory = Split-Path -Parent $StatusPath
    if (-not [string]::IsNullOrWhiteSpace($directory)) {
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
    }

    $Status | ConvertTo-Json -Depth 20 | Set-Content -Path $StatusPath -Encoding UTF8
}

function Get-OptionalJsonProperty {
    param(
        [object]$Object,
        [string]$Name
    )

    if ($null -eq $Object) { return $null }
    if ($null -eq $Object.PSObject.Properties[$Name]) { return $null }
    return $Object.PSObject.Properties[$Name].Value
}

function Get-NgrokGatewayExpectation {
    $configPath = Join-Path $Root "config\local-services.json"
    if (-not (Test-Path $configPath)) {
        $configPath = Join-Path $Root "config\local-services.example.json"
    }

    $expectedHost = $NgrokExpectedHost
    $expectedLocalPort = $(if ($NgrokExpectedLocalPort -gt 0) { $NgrokExpectedLocalPort } else { 8787 })
    if (Test-Path $configPath) {
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
            $ngrok = @($config.services | Where-Object { $_.name -eq "ngrok" } | Select-Object -First 1)
            if ($null -ne $ngrok) {
                $args = @(Get-OptionalJsonProperty -Object $ngrok -Name "args")
                for ($i = 0; $i -lt $args.Count; $i++) {
                    $arg = [string]$args[$i]
                    if ($arg -match "^\d+$") {
                        $expectedLocalPort = [int]$arg
                    }
                    elseif ($arg -eq "--url" -and ($i + 1) -lt $args.Count) {
                        $expectedHost = [string]$args[$i + 1]
                    }
                }
            }
        }
        catch {}
    }

    return [pscustomobject]@{
        host = $expectedHost
        localPort = $expectedLocalPort
    }
}

function Get-UriHostOrEmpty {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $candidate = $Value
    if ($candidate -notmatch "^[a-zA-Z][a-zA-Z0-9+.-]*://") {
        $candidate = "https://$candidate"
    }

    try { return ([uri]$candidate).Host }
    catch { return "" }
}

function Get-McpGatewayUrl {
    param([string]$PublicUrl)

    if ([string]::IsNullOrWhiteSpace($PublicUrl)) { return "external-gateway" }
    return $PublicUrl.TrimEnd("/") + "/mcp"
}

function Test-NgrokGateway {
    param([object]$Expectation)

    $process = Get-Process -Name $NgrokProcessName -ErrorAction SilentlyContinue
    $checkedAt = (Get-Date).ToString("o")
    if (-not $process) {
        return [pscustomobject]@{
            name = "ngrok"
            url = "external-gateway"
            state = "offline"
            ok = $false
            statusCode = 0
            latencyMs = 0
            checkedAt = $checkedAt
            blocker = "process_not_found"
            expectedHost = $Expectation.host
            expectedLocalPort = $Expectation.localPort
            nextAction = "Start ngrok gateway for local MCP port $($Expectation.localPort)."
        }
    }

    $started = Get-Date
    try {
        $response = Invoke-WebRequest -Uri $NgrokApiUrl -UseBasicParsing -TimeoutSec $TimeoutSeconds -ErrorAction Stop
        $elapsedMs = [Math]::Round(((Get-Date) - $started).TotalMilliseconds)
        $payload = $response.Content | ConvertFrom-Json -ErrorAction Stop
        $matchingTunnel = $null
        foreach ($tunnel in @($payload.tunnels)) {
            $publicUrl = [string](Get-OptionalJsonProperty -Object $tunnel -Name "public_url")
            $config = Get-OptionalJsonProperty -Object $tunnel -Name "config"
            $addr = [string](Get-OptionalJsonProperty -Object $config -Name "addr")
            $expectedHost = Get-UriHostOrEmpty -Value ([string]$Expectation.host)
            $actualHost = Get-UriHostOrEmpty -Value $publicUrl
            $hostMatches = [string]::IsNullOrWhiteSpace($expectedHost) -or $actualHost -eq $expectedHost
            $portMatches = $addr -match "(:|/)$($Expectation.localPort)(/)?$" -or $addr -eq [string]$Expectation.localPort
            if ($hostMatches -and $portMatches) {
                $matchingTunnel = $tunnel
                break
            }
        }

        $ok = $null -ne $matchingTunnel
        return [pscustomobject]@{
            name = "ngrok"
            url = $(if ($ok) { Get-McpGatewayUrl -PublicUrl ([string]$matchingTunnel.public_url) } else { "external-gateway" })
            state = $(if ($ok) { "online" } else { "degraded" })
            ok = [bool]$ok
            statusCode = [int]$response.StatusCode
            latencyMs = [int]$elapsedMs
            checkedAt = (Get-Date).ToString("o")
            blocker = $(if ($ok) { "" } else { "gateway_identity_mismatch" })
            expectedHost = $Expectation.host
            expectedLocalPort = $Expectation.localPort
            nextAction = $(if ($ok) { "No action required." } else { "Verify ngrok is exposing local MCP port $($Expectation.localPort) on the expected host." })
        }
    }
    catch {
        $elapsedMs = [Math]::Round(((Get-Date) - $started).TotalMilliseconds)
        return [pscustomobject]@{
            name = "ngrok"
            url = "external-gateway"
            state = "degraded"
            ok = $false
            statusCode = 0
            latencyMs = [int]$elapsedMs
            checkedAt = (Get-Date).ToString("o")
            blocker = "gateway_identity_unverified: $($_.Exception.Message)"
            expectedHost = $Expectation.host
            expectedLocalPort = $Expectation.localPort
            nextAction = "Verify ngrok is exposing local MCP port $($Expectation.localPort) on the expected host."
        }
    }
}

function Invoke-ServerHealthPulse {
    $servers = @()
    $servers += Test-HttpEndpoint -Name "dashboard" -Url $DashboardUrl -TimeoutSec $TimeoutSeconds -RecoveryAction "Run scripts/Restart-DashboardServer.ps1 locally or inspect dashboard port 8765 ownership."
    $servers += Test-HttpEndpoint -Name "mcp" -Url $McpHealthUrl -TimeoutSec $TimeoutSeconds -RecoveryAction "Start scripts/Start-OrchMcpServer.ps1 locally or inspect MCP port 8787 ownership."

    $servers += Test-NgrokGateway -Expectation (Get-NgrokGatewayExpectation)

    # Load local services status if available
    $servicesPath = Join-Path $Root "status\services.json"
    $localServices = @()
    if (Test-Path $servicesPath) {
        try {
            $svcStatus = Get-Content $servicesPath -Raw | ConvertFrom-Json
            $localServices = @($svcStatus.services)
        }
        catch {}
    }

    $mcpCapability = Get-McpCapabilitySnapshot -RootPath $Root
$mcpServer = @($servers | Where-Object { $_.name -eq "mcp" } | Select-Object -First 1)

if ($null -ne $mcpServer -and $mcpServer.ok -and $mcpCapability.available -and $mcpCapability.writable) {
    $mcpCapability.mode = "online_writable"
    $mcpCapability.nextAction = "No action required."
}

$offline = @($servers | Where-Object { -not $_.ok })
$state = $(if ($offline.Count -eq 0) { "online" } elseif ($offline.Count -eq $servers.Count) { "offline" } else { "degraded" })

    $status = [pscustomobject]@{
        generatedAt = (Get-Date).ToString("o")
        root = $Root
        intervalSeconds = $IntervalSeconds
        state = $state
        ok = [bool]($offline.Count -eq 0)
        servers = $servers
        localServices = $localServices
        mcpCapability = $mcpCapability
        nextAction = $(if ($offline.Count -eq 0) { "No action required." } else { "Restore offline server(s): $((@($offline | ForEach-Object { $_.name }) -join ', '))." })
    }

    Write-ServerHealthStatus -Status $status
    return $status
}

if ($IntervalSeconds -lt 30 -and -not $Once) {
    throw "IntervalSeconds must be at least 30 for recurring pulse mode."
}

if ($Once) {
    Invoke-ServerHealthPulse | ConvertTo-Json -Depth 20
    return
}

Write-Host "Monitoring server health every $IntervalSeconds seconds. Writing $StatusPath"
while ($true) {
    $status = Invoke-ServerHealthPulse
    Write-Host "[$($status.generatedAt)] Server health: $($status.state)"
    Start-Sleep -Seconds $IntervalSeconds
}
