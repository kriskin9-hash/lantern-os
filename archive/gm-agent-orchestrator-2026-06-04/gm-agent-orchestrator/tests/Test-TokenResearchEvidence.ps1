$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$researchPath = Join-Path $repoRoot 'docs/token-usage-research.md'

if (-not (Test-Path -LiteralPath $researchPath -PathType Leaf)) {
    throw 'Missing docs/token-usage-research.md'
}

$content = Get-Content -LiteralPath $researchPath -Raw
$violations = New-Object System.Collections.Generic.List[string]

$requiredTerms = @(
    'Official public fact',
    'Local observable signal',
    'Manual dashboard observation',
    'Assumption or unknown',
    'https://help.openai.com/en/articles/11369540',
    'https://platform.openai.com/docs/codex',
    'https://platform.openai.com/docs/pricing/',
    'https://docs.anthropic.com/en/docs/claude-code/costs',
    'https://docs.anthropic.com/en/docs/claude-code/settings',
    'https://docs.anthropic.com/en/docs/claude-code/memory'
)

foreach ($term in $requiredTerms) {
    if ($content -notmatch [regex]::Escape($term)) {
        $violations.Add("Token research document is missing required evidence term or source: $term")
    }
}

foreach ($classification in @('quota_capped', 'rate_limited', 'auth_failed', 'unknown_limit')) {
    if ($content -notmatch [regex]::Escape($classification)) {
        $violations.Add("Token research document is missing local classification: $classification")
    }
}

if ($content -notmatch 'nextWakeAt.*only if|only.*nextWakeAt') {
    $violations.Add('Token research document must restrict nextWakeAt to explicit observed evidence.')
}

if ($content -notmatch 'Do not hardcode|must be linked|linked, not copied') {
    $violations.Add('Token research document must forbid hardcoded mutable pricing/quota claims.')
}

# Guard against accidental fixed price/quota claims outside explicit forbidden examples.
$lines = Get-Content -LiteralPath $researchPath
$inForbiddenSection = $false
for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]

    if ($line -match '^## Forbidden claims') {
        $inForbiddenSection = $true
        continue
    }
    if ($inForbiddenSection -and $line -match '^## ' -and $line -notmatch '^## Forbidden claims') {
        $inForbiddenSection = $false
    }

    if ($inForbiddenSection) { continue }

    $hasMoney = $line -match '\$\d+(\.\d+)?'
    $hasQuota = $line -match '\b(exact|fixed|permanent|guaranteed)\b.*\b(quota|limit|price|pricing|rate)\b'
    $hasHardcodedPerToken = $line -match '\bper\s+1M\s+tokens\b'

    if ($hasMoney -or $hasQuota -or $hasHardcodedPerToken) {
        $violations.Add("Mutable pricing/quota-looking claim should be a link or forbidden example only at line $($i + 1): $line")
    }
}

# Require the local observation schema to preserve exact text.
foreach ($schemaField in @('observed_at', 'vendor', 'surface', 'classification', 'exact_text', 'source_path')) {
    if ($content -notmatch [regex]::Escape($schemaField)) {
        $violations.Add("Local evidence schema missing field: $schemaField")
    }
}

if ($violations.Count -gt 0) {
    throw ($violations -join [Environment]::NewLine)
}

Write-Host 'Token research evidence hygiene passed.'
