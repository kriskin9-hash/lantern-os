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

$setupScript = Join-Path $Root "scripts\Setup-LocalAgent.ps1"
$routerScript = Join-Path $Root "scripts\Invoke-LocalRouter.ps1"
$policyTest = Join-Path $Root "tests\Test-LocalRouterPolicy.ps1"
$laneDoc = Join-Path $Root "docs\agents\lm-studio-preflight-lane.md"

foreach ($path in @($setupScript, $routerScript, $policyTest, $laneDoc)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "LM Studio preflight lane required file is missing: $path"
    }
}

$setup = Get-Content -LiteralPath $setupScript -Raw
$router = Get-Content -LiteralPath $routerScript -Raw
$doc = Get-Content -LiteralPath $laneDoc -Raw

foreach ($needle in @("'lmstudio'", "'llmster'", "'ollama'", "http://localhost:1234/v1", "lfm2-24b-a2b", "LOCAL_LLM_MODE=read_only")) {
    if ($setup -notmatch [regex]::Escape($needle)) {
        throw "Setup-LocalAgent.ps1 must preserve local-model setup contract: missing $needle"
    }
}

foreach ($needle in @("classification", "summarization", "routing", "code_explanation", "human_review", "powershell", "secret", "deployment")) {
    if ($router -notmatch [regex]::Escape($needle)) {
        throw "Invoke-LocalRouter.ps1 must preserve read-only local preflight policy: missing $needle"
    }
}

foreach ($needle in @("lm-studio", "lmstudio", "LM Studio", "read_only", "Test-NetConnection localhost -Port 1234", "Test-LocalRouterPolicy.ps1")) {
    if ($doc -notmatch [regex]::Escape($needle)) {
        throw "LM Studio preflight lane docs must preserve naming and validation contract: missing $needle"
    }
}

$policyOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $policyTest -Root $Root 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Local router policy regression test failed: $($policyOutput -join "`n")"
}

Write-Host "Validated LM Studio local preflight lane contract."
