[CmdletBinding()]
param(
    [string]$Root = "",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function Convert-YamlScalar {
    param([string]$Value)

    $v = $Value.Trim()
    if ($v.StartsWith('"') -and $v.EndsWith('"')) { return $v.Trim('"') }
    if ($v.StartsWith("'") -and $v.EndsWith("'")) { return $v.Trim("'") }
    return $v
}

function Read-SourceRegistry {
    param([string]$Path)

    $sources = @()
    $current = $null
    $activeArrayKey = ""

    foreach ($line in (Get-Content -LiteralPath $Path)) {
        if ($line -match '^\s{2}-\s+id:\s*(.+)\s*$') {
            if ($null -ne $current) {
                $sources += [pscustomobject]$current
            }
            $current = [ordered]@{}
            $current.id = Convert-YamlScalar $Matches[1]
            $activeArrayKey = ""
            continue
        }

        if ($null -eq $current) { continue }

        if ($line -match '^\s{4}([a-zA-Z0-9_]+):\s*(.*)\s*$') {
            $key = $Matches[1]
            $value = $Matches[2]
            if ([string]::IsNullOrWhiteSpace($value)) {
                $current[$key] = @()
                $activeArrayKey = $key
            }
            else {
                $current[$key] = Convert-YamlScalar $value
                $activeArrayKey = ""
            }
            continue
        }

        if ($line -match '^\s{6}-\s*(.+)\s*$' -and -not [string]::IsNullOrWhiteSpace($activeArrayKey)) {
            $arr = @($current[$activeArrayKey])
            $arr += (Convert-YamlScalar $Matches[1])
            $current[$activeArrayKey] = $arr
            continue
        }
    }

    if ($null -ne $current) {
        $sources += [pscustomobject]$current
    }

    return @($sources)
}

function Read-ClaimRegistry {
    param([string]$Path)

    $claims = @()
    $lineNumber = 0
    foreach ($line in (Get-Content -LiteralPath $Path)) {
        $lineNumber += 1
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $claims += ($line | ConvertFrom-Json -ErrorAction Stop)
        }
        catch {
            throw "Invalid JSON in claim registry at line ${lineNumber}: $($_.Exception.Message)"
        }
    }
    return @($claims)
}

$contextPath = Join-Path $Root "status\research-context.json"
$sourcePath = Join-Path $Root "research\index\source-registry.yml"
$claimPath = Join-Path $Root "research\index\claim-registry.jsonl"
$auditPath = Join-Path $Root "research\audits\latest.md"
$requestPath = Join-Path $Root "research\requests\open"

foreach ($required in @($sourcePath, $claimPath, $auditPath, $requestPath)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required research artifact missing: $required"
    }
}

$sources = Read-SourceRegistry -Path $sourcePath
$claims = Read-ClaimRegistry -Path $claimPath

$existing = $null
if (Test-Path -LiteralPath $contextPath) {
    $existing = Get-Content -LiteralPath $contextPath -Raw | ConvertFrom-Json -ErrorAction Stop
}

$knownGaps = @()
$auditText = Get-Content -LiteralPath $auditPath -Raw
$gapLines = @($auditText -split "`r?`n" | Where-Object {
        $_ -match '^\s*-\s+' -or $_ -match 'known gaps' -or $_ -match 'Known gaps'
    })
if ($gapLines.Count -gt 0) {
    $knownGaps = @(
        [pscustomobject]@{
            id = "gap-audit-summary"
            severity = "watch"
            summary = (($gapLines | Select-Object -First 8) -join " ")
        }
    )
}

$coverage = [ordered]@{
    sources_total = @($sources).Count
    sources_complete = @($sources | Where-Object { $_.read_status -eq "complete" }).Count
    sources_partial = @($sources | Where-Object { $_.read_status -in @("partial", "skimmed") }).Count
    claims_total = @($claims).Count
    claims_verified = @($claims | Where-Object { $_.status -eq "verified" }).Count
    claims_needs_source = @($claims | Where-Object { $_.status -eq "needs_source" }).Count
}

$bestSynthesis = "research/audits/latest.md"
$latestAudit = "research/audits/latest.md"
$sourceRegistry = "research/index/source-registry.yml"
$claimRegistry = "research/index/claim-registry.jsonl"
$requestPathRelative = "research/requests/open/"
$decision = "Use registry-backed research ingestion with validation-first checks before workflow enforcement."
$howToRequest = "Create a markdown request under research/requests/open/ using research/requests/README.md."

if ($null -ne $existing) {
    if (-not [string]::IsNullOrWhiteSpace([string]$existing.best_synthesis) -and (Test-Path (Join-Path $Root ([string]$existing.best_synthesis)))) {
        $bestSynthesis = [string]$existing.best_synthesis
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$existing.latest_audit) -and (Test-Path (Join-Path $Root ([string]$existing.latest_audit)))) {
        $latestAudit = [string]$existing.latest_audit
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$existing.source_registry) -and (Test-Path (Join-Path $Root ([string]$existing.source_registry)))) {
        $sourceRegistry = [string]$existing.source_registry
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$existing.claim_registry) -and (Test-Path (Join-Path $Root ([string]$existing.claim_registry)))) {
        $claimRegistry = [string]$existing.claim_registry
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$existing.request_path) -and (Test-Path (Join-Path $Root ([string]$existing.request_path)))) {
        $requestPathRelative = [string]$existing.request_path
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$existing.decision)) {
        $decision = [string]$existing.decision
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$existing.how_to_request_research)) {
        $howToRequest = [string]$existing.how_to_request_research
    }
    if ($null -ne $existing.known_gaps -and @($existing.known_gaps).Count -gt 0) {
        $knownGaps = @($existing.known_gaps)
    }
}

$semantic = [ordered]@{
    result = "partial-pass"
    best_synthesis = $bestSynthesis
    latest_audit = $latestAudit
    source_registry = $sourceRegistry
    claim_registry = $claimRegistry
    request_path = $requestPathRelative
    coverage = $coverage
    known_gaps = $knownGaps
    decision = $decision
    how_to_request_research = $howToRequest
}

$existingSemantic = $null
if ($null -ne $existing) {
    $existingSemantic = [ordered]@{
        result = [string]$existing.result
        best_synthesis = [string]$existing.best_synthesis
        latest_audit = [string]$existing.latest_audit
        source_registry = [string]$existing.source_registry
        claim_registry = [string]$existing.claim_registry
        request_path = [string]$existing.request_path
        coverage = $existing.coverage
        known_gaps = $existing.known_gaps
        decision = [string]$existing.decision
        how_to_request_research = [string]$existing.how_to_request_research
    }
}

$semanticJson = ($semantic | ConvertTo-Json -Depth 12)
$existingSemanticJson = if ($null -eq $existingSemantic) { "" } else { ($existingSemantic | ConvertTo-Json -Depth 12) }
$semanticChanged = ($semanticJson -ne $existingSemanticJson)

$updatedAt = if ($semanticChanged) {
    (Get-Date).ToString("o")
}
elseif ($null -ne $existing -and -not [string]::IsNullOrWhiteSpace([string]$existing.updated_at)) {
    [string]$existing.updated_at
}
else {
    (Get-Date).ToString("o")
}

$updated = [ordered]@{
    updated_at = $updatedAt
    result = $semantic.result
    best_synthesis = $semantic.best_synthesis
    latest_audit = $semantic.latest_audit
    source_registry = $semantic.source_registry
    claim_registry = $semantic.claim_registry
    request_path = $semantic.request_path
    coverage = $semantic.coverage
    known_gaps = $semantic.known_gaps
    decision = $semantic.decision
    how_to_request_research = $semantic.how_to_request_research
}

$newJson = ($updated | ConvertTo-Json -Depth 12)
$oldJson = if (Test-Path -LiteralPath $contextPath) { Get-Content -LiteralPath $contextPath -Raw } else { "" }

if ($DryRun) {
    [pscustomobject]@{
        ok = $true
        dryRun = $true
        changed = $semanticChanged
        path = $contextPath
        coverage = $coverage
    } | ConvertTo-Json -Depth 8
    exit 0
}

if (-not $semanticChanged) {
    [pscustomobject]@{
        ok = $true
        dryRun = $false
        changed = $false
        path = $contextPath
        message = "No content changes required."
    } | ConvertTo-Json -Depth 8
    exit 0
}

$parentDir = Split-Path -Parent $contextPath
if (-not (Test-Path -LiteralPath $parentDir)) {
    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
}

Set-Content -LiteralPath $contextPath -Value $newJson -Encoding UTF8

[pscustomobject]@{
    ok = $true
    dryRun = $false
    changed = $true
    path = $contextPath
    coverage = $coverage
} | ConvertTo-Json -Depth 8

exit 0
