[CmdletBinding()]
param(
    [string]$TunnelName = "gm-agent-orchestrator",
    [int]$LocalPort = 8787,
    [string]$LocalHost = "localhost"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$localUrl = "http://{0}:{1}" -f $LocalHost, $LocalPort

Write-Host "Starting Cloudflare Tunnel: $TunnelName"
Write-Host "Routing to: $localUrl"
Write-Host ""

# Use existing tunnel or create new one
& cloudflared tunnel run $TunnelName --url $localUrl
