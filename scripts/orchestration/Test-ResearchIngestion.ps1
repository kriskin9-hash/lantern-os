[CmdletBinding()]
param(
    [string]$Root = "",
    [switch]$AsJson
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

    # Deterministic fallback parser for this repo's source-registry.yml shape.
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

$failures = New-Object System.Collections.Generic.List[string]

$contextPath = Join-Path $Root "status\research-context.json"
$sourcePath = Join-Path $Root "research\index\source-registry.yml"
$claimPath = Join-Path $Root "research\index\claim-registry.jsonl"
$auditPath = Join-Path $Root "research\audits\latest.md"
$requestPath = Join-Path $Root "research\requests\open"

foreach ($required in @($contextPath, $sourcePath, $claimPath, $auditPath, $requestPath)) {
    if (-not (Test-Path -LiteralPath $required)) {
        $failures.Add("FAIL|missing_path|$required") | Out-Null
    }
}

$context = $null
$sources = @()
$claims = @()
$auditText = ""

if (Test-Path -LiteralPath $contextPath) {
    try {
        $context = Get-Content -LiteralPath $contextPath -Raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        $failures.Add("FAIL|context_parse|status/research-context.json is not valid JSON: $($_.Exception.Message)") | Out-Null
    }
}

if (Test-Path -LiteralPath $sourcePath) {
    try {
        $sources = Read-SourceRegistry -Path $sourcePath
    }
    catch {
        $failures.Add("FAIL|source_parse|research/index/source-registry.yml parse failed: $($_.Exception.Message)") | Out-Null
    }
}

if (Test-Path -LiteralPath $claimPath) {
    try {
        $claims = Read-ClaimRegistry -Path $claimPath
    }
    catch {
        $failures.Add("FAIL|claim_parse|research/index/claim-registry.jsonl parse failed: $($_.Exception.Message)") | Out-Null
    }
}

if (Test-Path -LiteralPath $auditPath) {
    $auditText = (Get-Content -LiteralPath $auditPath -Raw)
}

$allowedReadStatus = @("complete", "partial", "skimmed", "inaccessible", "not_started", "superseded", "needs_research")
$allowedFreshness = @("current", "watch", "stale", "unknown")
$allowedAuthority = @("primary", "secondary", "repo_verified", "internal_hypothesis")
$allowedClaimStatus = @("verified", "inferred", "needs_source", "needs_research", "contradicted", "stale", "retired")

$sourceIds = @{}
foreach ($source in $sources) {
    if ([string]::IsNullOrWhiteSpace($source.id)) {
        $failures.Add("FAIL|source_id|source-registry contains a source with missing id.") | Out-Null
        continue
    }

    $sourceIds[$source.id] = $true

    if ($allowedReadStatus -notcontains [string]$source.read_status) {
        $failures.Add("FAIL|source_read_status|source '$($source.id)' has invalid read_status '$($source.read_status)'.") | Out-Null
    }
    if ($allowedFreshness -notcontains [string]$source.freshness) {
        $failures.Add("FAIL|source_freshness|source '$($source.id)' has invalid freshness '$($source.freshness)'.") | Out-Null
    }
    if ($allowedAuthority -notcontains [string]$source.authority) {
        $failures.Add("FAIL|source_authority|source '$($source.id)' has invalid authority '$($source.authority)'.") | Out-Null
    }
}

foreach ($claim in $claims) {
    $claimId = [string]$claim.claim_id
    if ($allowedClaimStatus -notcontains [string]$claim.status) {
        $failures.Add("FAIL|claim_status|claim '$claimId' has invalid status '$($claim.status)'.") | Out-Null
    }

    $sourceRefIds = @($claim.source_ids)
    if ([string]$claim.status -ne "needs_source" -and $sourceRefIds.Count -lt 1) {
        $failures.Add("FAIL|claim_source_ids|claim '$claimId' must include source_ids unless status is needs_source.") | Out-Null
    }

    foreach ($sid in $sourceRefIds) {
        if (-not $sourceIds.ContainsKey([string]$sid)) {
            $failures.Add("FAIL|claim_source_ref|claim '$claimId' references unknown source_id '$sid'.") | Out-Null
        }
    }
}

if ($null -ne $context) {
    $actualCoverage = [ordered]@{
        sources_total = @($sources).Count
        sources_complete = @($sources | Where-Object { $_.read_status -eq "complete" }).Count
        sources_partial = @($sources | Where-Object { $_.read_status -in @("partial", "skimmed") }).Count
        claims_total = @($claims).Count
        claims_verified = @($claims | Where-Object { $_.status -eq "verified" }).Count
        claims_needs_source = @($claims | Where-Object { $_.status -eq "needs_source" }).Count
    }

    foreach ($k in $actualCoverage.Keys) {
        $expected = [int]$actualCoverage[$k]
        $observed = [int]$context.coverage.$k
        if ($expected -ne $observed) {
            $failures.Add("FAIL|coverage_mismatch|coverage.$k expected=$expected observed=$observed") | Out-Null
        }
    }

    $knownGapText = ""
    if ($null -ne $context.known_gaps) {
        $knownGapText = (($context.known_gaps | ConvertTo-Json -Depth 8))
    }
    $combinedGapText = ($auditText + "`n" + $knownGapText)

    foreach ($source in $sources) {
        $needsGapMention = ($source.read_status -in @("partial", "skimmed", "inaccessible", "not_started", "needs_research")) -or ($source.freshness -in @("stale", "unknown"))
        if (-not $needsGapMention) { continue }

        $title = [string]$source.title
        $id = [string]$source.id
        if ($combinedGapText -notmatch [regex]::Escape($id) -and $combinedGapText -notmatch [regex]::Escape($title)) {
            $failures.Add("FAIL|gap_mention|source '$id' is partial/stale/unknown but is not mentioned in audit/latest or known_gaps.") | Out-Null
        }
    }
}

$result = [ordered]@{
    ok = ($failures.Count -eq 0)
    root = $Root
    checkedAt = (Get-Date).ToString("o")
    sourceCount = @($sources).Count
    claimCount = @($claims).Count
    failures = @($failures)
}

if ($AsJson) {
    $result | ConvertTo-Json -Depth 8
}
else {
    if ($result.ok) {
        Write-Output "PASS|research_ingestion|source_count=$($result.sourceCount)|claim_count=$($result.claimCount)"
    }
    else {
        foreach ($f in $failures) { Write-Output $f }
    }
}

if ($failures.Count -gt 0) {
    exit 1
}

exit 0
