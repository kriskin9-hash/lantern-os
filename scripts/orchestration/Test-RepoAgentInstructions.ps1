[CmdletBinding()]
param(
    [string]$ConfigPath = "config/projects.json",
    [string]$OutputJson = "status/repo-agent-instructions.json",
    [string]$OutputReport = "reports/agents/repo-agent-instructions-latest.md"
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [string]$ConfiguredPath
    )

    $candidates = New-Object System.Collections.Generic.List[string]

    if ($ConfiguredPath) {
        $candidates.Add($ConfiguredPath)
    }

    $scriptRoot = Split-Path -Parent $PSScriptRoot
    if ($scriptRoot) {
        $candidates.Add($scriptRoot)
        $parent = Split-Path -Parent $scriptRoot
        if ($parent) {
            $candidates.Add((Join-Path $parent $Name))
        }
    }

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Container)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return $ConfiguredPath
}

function Get-FileText {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }

    return Get-Content -LiteralPath $Path -Raw
}

function Test-ContainsAny {
    param(
        [AllowNull()][string]$Text,
        [Parameter(Mandatory = $true)][string[]]$Patterns
    )

    if (-not $Text) {
        return $false
    }

    foreach ($pattern in $Patterns) {
        if ($Text -match $pattern) {
            return $true
        }
    }

    return $false
}

function Get-ConfiguredRepos {
    param([string]$ConfigPath)

    $defaults = @(
        [pscustomobject]@{ name = "gm-agent-orchestrator"; path = $null },
        [pscustomobject]@{ name = "gamemaker-room-editor"; path = $null },
        [pscustomobject]@{ name = "ChildOfLevistus"; path = $null }
    )

    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
        return $defaults
    }

    try {
        $config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
    }
    catch {
        Write-Warning "Could not parse $ConfigPath; using default repo names. $($_.Exception.Message)"
        return $defaults
    }

    $repos = New-Object System.Collections.Generic.List[object]

    foreach ($property in $config.PSObject.Properties) {
        $value = $property.Value
        if ($value -and $value.path) {
            $repos.Add([pscustomobject]@{ name = $property.Name; path = [string]$value.path })
        }
    }

    if ($repos.Count -eq 0) {
        return $defaults
    }

    return $repos
}

$checks = @(
    [pscustomobject]@{
        Name = "missingRootAgents"
        Description = "root AGENTS.md exists"
        Test = { param($text) [bool]$text }
    },
    [pscustomobject]@{
        Name = "missingAntiRedundancyRule"
        Description = "anti-redundancy / existing-work check"
        Test = { param($text) Test-ContainsAny -Text $text -Patterns @("(?i)anti[- ]redundancy", "(?i)search existing", "(?i)existing issues", "(?i)duplicate") }
    },
    [pscustomobject]@{
        Name = "missingFinalReportFormat"
        Description = "final report format"
        Test = { param($text) Test-ContainsAny -Text $text -Patterns @("(?i)final report", "(?i)done format", "(?i)handoff") }
    },
    [pscustomobject]@{
        Name = "missingHonestyCheck"
        Description = "honesty / operating-condition check"
        Test = { param($text) Test-ContainsAny -Text $text -Patterns @("(?i)honesty", "(?i)operating[- ]condition", "(?i)verified.*assumed", "(?i)state uncertainty") }
    },
    [pscustomobject]@{
        Name = "missingRepoBoundaryStatement"
        Description = "repo boundary statement"
        Test = { param($text) Test-ContainsAny -Text $text -Patterns @("(?i)repo boundaries", "(?i)this repo owns", "(?i)does not own", "(?i)belongs in") }
    }
)

$results = New-Object System.Collections.Generic.List[object]

foreach ($repo in (Get-ConfiguredRepos -ConfigPath $ConfigPath)) {
    $repoPath = Resolve-RepoPath -Name $repo.name -ConfiguredPath $repo.path
    $agentsPath = if ($repoPath) { Join-Path $repoPath "AGENTS.md" } else { $null }
    $text = if ($agentsPath) { Get-FileText -Path $agentsPath } else { $null }
    $missing = New-Object System.Collections.Generic.List[string]

    foreach ($check in $checks) {
        $passed = & $check.Test $text
        if (-not $passed) {
            $missing.Add($check.Name)
        }
    }

    $results.Add([pscustomobject]@{
        repo = $repo.name
        path = $repoPath
        agentsPath = $agentsPath
        status = if ($missing.Count -eq 0) { "pass" } else { "fail" }
        missing = @($missing)
    })
}

$summary = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    configPath = $ConfigPath
    results = @($results)
}

$jsonDir = Split-Path -Parent $OutputJson
if ($jsonDir -and -not (Test-Path -LiteralPath $jsonDir -PathType Container)) {
    New-Item -ItemType Directory -Path $jsonDir -Force | Out-Null
}

$reportDir = Split-Path -Parent $OutputReport
if ($reportDir -and -not (Test-Path -LiteralPath $reportDir -PathType Container)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputJson -Encoding UTF8

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Repo Agent Instructions Audit")
$lines.Add("")
$lines.Add("Generated: $($summary.generatedAt)")
$lines.Add("")
$lines.Add("| Repo | Status | Missing | Path |")
$lines.Add("| --- | --- | --- | --- |")
foreach ($result in $results) {
    $missingText = if ($result.missing.Count -eq 0) { "none" } else { ($result.missing -join ", ") }
    $lines.Add("| $($result.repo) | $($result.status) | $missingText | $($result.path) |")
}
$lines.Add("")
$lines.Add("## Required checks")
foreach ($check in $checks) {
    $lines.Add("- $($check.Name): $($check.Description)")
}

$lines | Set-Content -LiteralPath $OutputReport -Encoding UTF8

$failed = @($results | Where-Object { $_.status -ne "pass" })
if ($failed.Count -gt 0) {
    Write-Host "Repo agent instruction audit failed for $($failed.Count) repo(s). See $OutputReport and $OutputJson."
    exit 1
}

Write-Host "Repo agent instruction audit passed. See $OutputReport and $OutputJson."
