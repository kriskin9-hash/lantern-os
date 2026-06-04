$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$routingPath = Join-Path $repoRoot 'docs/agent-routing-map.md'
$startPath = Join-Path $repoRoot 'docs/agent-start-here.md'

$violations = New-Object System.Collections.Generic.List[string]

foreach ($path in @($routingPath, $startPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $violations.Add("Missing required routing document: $($path.Substring($repoRoot.Length + 1))")
    }
}

if (Test-Path -LiteralPath $routingPath -PathType Leaf) {
    $content = Get-Content -LiteralPath $routingPath -Raw

    foreach ($required in @('README.md', 'docs/README.md', 'docs/agent-start-here.md', 'docs/model-guides/claude.md', 'docs/model-guides/codex.md', 'docs/token-usage-research.md')) {
        if ($content -notmatch [regex]::Escape($required)) {
            $violations.Add("Routing map does not mention required path: $required")
        }
    }

    $badBroadScanPatterns = @(
        'start\s+by\s+(broad\s+)?scann?ing\s+the\s+repo',
        'scan\s+the\s+entire\s+repo\s+first',
        'read\s+everything\s+first',
        'inspect\s+all\s+files\s+first'
    )

    foreach ($pattern in $badBroadScanPatterns) {
        if ($content -match $pattern) {
            $violations.Add("Routing map contains broad-scan-first wording matching: $pattern")
        }
    }

    if ($content -notmatch 'smallest\s+relevant') {
        $violations.Add('Routing map must tell agents to inspect the smallest relevant context.')
    }
}

if ($violations.Count -gt 0) {
    throw ($violations -join [Environment]::NewLine)
}

Write-Host 'Agent routing map passed.'
