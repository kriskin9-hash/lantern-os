[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$LocalMcpUrl = "http://127.0.0.1:8787/mcp",
    [string]$TunnelUrl = "",
    [int]$TimeoutSec = 15,
    [switch]$AllowRemote
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function Read-JsonFileOrNull {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { return $null }
}

function Get-OptionalJsonProperty {
    param([object]$Object, [string]$Name)
    if ($null -eq $Object -or $null -eq $Object.PSObject.Properties[$Name]) { return $null }
    return $Object.PSObject.Properties[$Name].Value
}

function Get-ConfiguredTunnelUrl {
    $statusPaths = @(
        (Join-Path $Root "status\server-health.json"),
        (Join-Path $Root "status\orchestrator.json")
    )
    foreach ($path in $statusPaths) {
        $status = Read-JsonFileOrNull -Path $path
        if ($null -eq $status) { continue }
        $servers = @()
        if ($null -ne (Get-OptionalJsonProperty -Object $status -Name "servers")) { $servers = @(Get-OptionalJsonProperty -Object $status -Name "servers") }
        elseif ($null -ne $status.serviceHealth -and $null -ne $status.serviceHealth.servers) { $servers = @($status.serviceHealth.servers) }
        foreach ($server in $servers) {
            if ([string](Get-OptionalJsonProperty -Object $server -Name "name") -eq "ngrok") {
                $url = [string](Get-OptionalJsonProperty -Object $server -Name "url")
                if ($url -match '^https://') { return $url }
            }
        }
    }

    $config = Read-JsonFileOrNull -Path (Join-Path $Root "config\local-services.json")
    foreach ($service in @($config.services)) {
        if ([string](Get-OptionalJsonProperty -Object $service -Name "name") -ne "ngrok") { continue }
        $args = @((Get-OptionalJsonProperty -Object $service -Name "args"))
        for ($i = 0; $i -lt $args.Count; $i++) {
            if ([string]$args[$i] -eq "--url" -and $i + 1 -lt $args.Count) {
                return "https://$($args[$i + 1])/mcp"
            }
        }
    }
    return ""
}

function Invoke-ToolsListCanary {
    param([string]$Url, [string]$Lane)
    $result = [ordered]@{
        lane = $Lane
        url = $Url
        ok = $false
        statusCode = $null
        toolCount = 0
        requiredToolsVisible = $false
        tools = @()
        error = ""
    }
    if ([string]::IsNullOrWhiteSpace($Url)) {
        $result.error = "missing_url"
        return [pscustomobject]$result
    }

    $requiredTools = @("get_agent_status", "get_queue_summary", "get_mcp_feature_overview")
    $body = @{
        jsonrpc = "2.0"
        id = "canary-$Lane"
        method = "tools/list"
        params = @{}
    } | ConvertTo-Json -Depth 8 -Compress

    for ($attempt = 1; $attempt -le 2; $attempt++) {
        try {
            $payload = Invoke-RestMethod -Method Post -Uri $Url -Body $body -ContentType "application/json" -TimeoutSec $TimeoutSec
            $payloadError = Get-OptionalJsonProperty -Object $payload -Name "error"
            if ($null -ne $payloadError) {
                $message = [string](Get-OptionalJsonProperty -Object $payloadError -Name "message")
                if ([string]::IsNullOrWhiteSpace($message)) { $message = [string]$payloadError }
                throw $message
            }
            $names = @($payload.result.tools | ForEach-Object { [string]$_.name } | Sort-Object -Unique)
            $missing = @($requiredTools | Where-Object { $names -notcontains $_ })
            $result.statusCode = 200
            $result.toolCount = @($names).Count
            $result.requiredToolsVisible = @($missing).Count -eq 0
            $result.tools = @($names)
            $result.ok = $result.statusCode -eq 200 -and $result.requiredToolsVisible
            $result.error = ""
            break
        }
        catch {
            $result.error = $_.Exception.Message
            if ($attempt -lt 2 -and $result.error -match "timed out") {
                Start-Sleep -Milliseconds 200
                continue
            }
            break
        }
    }
    return [pscustomobject]$result
}

if ([string]::IsNullOrWhiteSpace($TunnelUrl)) {
    $TunnelUrl = Get-ConfiguredTunnelUrl
}

$local = Invoke-ToolsListCanary -Url $LocalMcpUrl -Lane "local"
$tunnel = [pscustomobject]@{
    lane = "tunnel"
    url = $TunnelUrl
    ok = $false
    statusCode = $null
    toolCount = 0
    requiredToolsVisible = $false
    tools = @()
    error = "remote_canary_not_requested"
}
if ($AllowRemote) {
    $tunnel = Invoke-ToolsListCanary -Url $TunnelUrl -Lane "tunnel"
}

$ok = $local.ok -eq $true -and ($(if ($AllowRemote) { $tunnel.ok -eq $true } else { $true }))

[pscustomobject]@{
    ok = [bool]$ok
    action = "orch_tunnel_canary"
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    allowRemote = [bool]$AllowRemote
    local = $local
    tunnel = $tunnel
    safety = [pscustomobject]@{
        method = "tools/list"
        readOnly = $true
        noAgentStart = $true
        noTaskMovement = $true
        tunnelTrustedOnlyIfOk = $true
    }
    nextAction = $(if ($ok) { "Canary passed; tunnel exposes the expected read-only MCP catalog." } else { "Do not trust the tunnel for dispatch visibility until this canary is green." })
} | ConvertTo-Json -Depth 20
