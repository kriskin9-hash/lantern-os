[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $Root 'scripts\Get-HookOpportunities.ps1'
$rulesPath = Join-Path $Root 'docs\hook-opportunity-rules.yml'
$governancePath = Join-Path $Root 'docs\pr-review-governance.md'
$templatePath = Join-Path $Root '.github\pull_request_template.md'

$violations = New-Object System.Collections.Generic.List[string]

foreach ($requiredPath in @($scriptPath, $rulesPath, $governancePath, $templatePath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        $violations.Add("Missing review governance file: $($requiredPath.Substring($Root.Length + 1))")
    }
}

if (Test-Path -LiteralPath $governancePath -PathType Leaf) {
    $governance = Get-Content -LiteralPath $governancePath -Raw
    foreach ($needle in @('Deterministic-first rule', 'Hook opportunity advisor', 'schema validation', 'regex-detectable', 'Portfolio framing')) {
        if ($governance -notmatch [regex]::Escape($needle)) {
            $violations.Add("Governance doc must preserve required section/text: $needle")
        }
    }
}

if (Test-Path -LiteralPath $templatePath -PathType Leaf) {
    $template = Get-Content -LiteralPath $templatePath -Raw
    foreach ($needle in @('Deterministic-first review', 'Industry-standard review readiness', 'Risk level declared', 'Rollback path included')) {
        if ($template -notmatch [regex]::Escape($needle)) {
            $violations.Add("PR template must preserve review-readiness prompt: $needle")
        }
    }
}

if (Test-Path -LiteralPath $rulesPath -PathType Leaf) {
    $rules = Get-Content -LiteralPath $rulesPath -Raw
    foreach ($needle in @('mode: advisory', 'deterministic-first', 'expected_companions', 'queue-dispatch-change-needs-dry-run')) {
        if ($rules -notmatch [regex]::Escape($needle)) {
            $violations.Add("Hook opportunity rules must preserve advisory rule: $needle")
        }
    }
}

if (Test-Path -LiteralPath $scriptPath -PathType Leaf) {
    $jsonText = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath -Root $Root -ChangedPath 'scripts/Invoke-OrchestratorAgentAction.ps1' -AsJson
    if ($LASTEXITCODE -ne 0) {
        $violations.Add("Get-HookOpportunities.ps1 exited with $LASTEXITCODE")
    }
    else {
        try {
            $result = ($jsonText | Out-String).Trim() | ConvertFrom-Json -ErrorAction Stop
            if ($result.ok -ne $true) { $violations.Add('Hook opportunity advisor must return ok=true.') }
            if ($result.mode -ne 'advisory') { $violations.Add("Hook opportunity advisor must stay advisory by default; got mode=$($result.mode)") }
            if ($result.deterministicFirst -ne $true) { $violations.Add('Hook opportunity advisor must report deterministicFirst=true.') }
            if (@($result.opportunities | Where-Object { $_.id -eq 'deterministic-first' }).Count -lt 1) {
                $violations.Add('Expected deterministic-first opportunity for script change.')
            }
            if (@($result.opportunities | Where-Object { $_.id -eq 'script-change-needs-test' }).Count -lt 1) {
                $violations.Add('Expected script-change-needs-test opportunity when script changes without tests.')
            }
        }
        catch {
            $violations.Add("Hook opportunity advisor did not emit valid JSON: $($_.Exception.Message)")
        }
    }
}

if ($violations.Count -gt 0) {
    throw ($violations -join [Environment]::NewLine)
}

Write-Host 'Hook opportunity advisor contract passed.'
