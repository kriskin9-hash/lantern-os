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

$scriptUnderTest = Join-Path $Root "scripts\Test-OrchTunnelCanary.ps1"
if (-not (Test-Path -LiteralPath $scriptUnderTest -PathType Leaf)) {
    throw "Required script not found: $scriptUnderTest"
}

$content = Get-Content -LiteralPath $scriptUnderTest -Raw
foreach ($required in @(
    "tools/list",
    "NoAgentStart",
    "NoTaskMovement",
    "tunnelTrustedOnlyIfOk",
    "remote_canary_not_requested",
    "Do not trust the tunnel for dispatch visibility",
    'Get-OptionalJsonProperty -Object $payload -Name "error"'
)) {
    if ($content -notmatch [regex]::Escape($required)) {
        throw "Tunnel canary script missing required safety text: $required"
    }
}

$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptUnderTest -Root $Root -LocalMcpUrl "http://127.0.0.1:1/mcp" 2>&1
if ($LASTEXITCODE -ne 0) { throw "Tunnel canary held-mode run failed: $($output -join "`n")" }
$result = ($output -join "`n") | ConvertFrom-Json -ErrorAction Stop
if ($result.allowRemote -ne $false) { throw "Default canary run must not probe the remote tunnel." }
if ($result.local.ok -ne $false) { throw "Fixture local canary should fail closed on unused port." }
if ($result.tunnel.error -ne "remote_canary_not_requested") { throw "Default tunnel canary should be held unless AllowRemote is set." }
if ($result.safety.readOnly -ne $true -or $result.safety.noAgentStart -ne $true -or $result.safety.noTaskMovement -ne $true) {
    throw "Canary safety flags must stay read-only/no-dispatch."
}

Write-Host "Validated read-only tunnel canary contract."
