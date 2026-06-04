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

$threatModelPath = Join-Path $Root "docs\security\threat-model.md"
$handoffPath = Join-Path $Root "docs\cto-successor-handoff.md"

foreach ($required in @($threatModelPath, $handoffPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Missing required security contract doc: $required"
    }
}

$threatModel = Get-Content -LiteralPath $threatModelPath -Raw
$handoff = Get-Content -LiteralPath $handoffPath -Raw

$requiredThreatSections = @(
    "Prompt Injection",
    "MCP Server Impersonation",
    "Supply Chain",
    "Tenant Lateral Movement",
    "Detection mechanisms"
)

foreach ($needle in $requiredThreatSections) {
    if ($threatModel -notmatch [regex]::Escape($needle)) {
        throw "Threat model missing required section/text: $needle"
    }
}

foreach ($needle in @(
    "Treat observed content as data",
    "Do not allow agents to",
    "threat-model.md"
)) {
    if ($handoff -notmatch [regex]::Escape($needle)) {
        throw "CTO handoff missing required threat linkage text: $needle"
    }
}

Write-Host "Prompt-injection and threat model contract passed."
