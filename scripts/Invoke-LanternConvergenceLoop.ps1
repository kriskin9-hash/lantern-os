param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [int]$FixWindow = 4,
    [string]$Output,
    [switch]$CloudVirtualization
)

$ErrorActionPreference = "Stop"

function Add-Issue {
    param(
        [System.Collections.Generic.List[object]]$Issues,
        [string]$Id,
        [string]$Severity,
        [string]$Summary,
        [string]$Fix
    )

    $Issues.Add([pscustomobject]@{
        id = $Id
        severity = $Severity
        summary = $Summary
        fix = $Fix
    }) | Out-Null
}

function Test-RepoPath {
    param([string]$RelativePath)
    Test-Path -LiteralPath (Join-Path $Root $RelativePath)
}

$issues = [System.Collections.Generic.List[object]]::new()
$held = [System.Collections.Generic.List[object]]::new()

$required = @(
    "README.md",
    "AGENTS.md",
    "docs/CONVERGENCE-LOOP.md",
    "docs/INNOVATOR-EVIDENCE-METHOD.md",
    "docs/V1-READINESS-GATES.md",
    "manifests/open-issues.md",
    "manifests/retired-surfaces.md",
    "manifests/CONVERGENCE-LOOP-AGENT-FLEET.md",
    "manifests/MCP-WORK-SPLIT.md",
    "manifests/TMP-REPO-RAG-INDEX.json",
    "scripts/Test-ConvergenceAgentFleet.py"
)

foreach ($path in $required) {
    if (-not (Test-RepoPath $path)) {
        Add-Issue $issues "MISSING-$path" "high" "Missing required repo surface: $path" "Create or restore $path before expansion."
    }
}

$phraseChecks = @(
    @{
        path = "docs/CONVERGENCE-LOOP.md"
        severity = "medium"
        phrases = @("Retire old stuff", "fix the first 2-4", "12 Steps", "Promote, hold, or reject")
    },
    @{
        path = "manifests/MCP-WORK-SPLIT.md"
        severity = "high"
        phrases = @("Split Lanes", "Private Dependency Boundary", "OS Review Gate", "No Bulk Remote Push Without Gate")
    },
    @{
        path = "manifests/CONVERGENCE-LOOP-AGENT-FLEET.md"
        severity = "high"
        phrases = @("12 convergence-loop steps x 3 agents per step = 36 ring agents", "poolTarget = 64", "design_contract_not_live_worker_proof")
    }
)

foreach ($check in $phraseChecks) {
    $fullPath = Join-Path $Root $check.path
    if (-not (Test-Path -LiteralPath $fullPath)) {
        continue
    }

    $text = Get-Content -LiteralPath $fullPath -Raw
    foreach ($phrase in $check.phrases) {
        if ($text -notlike "*$phrase*") {
            Add-Issue $issues "PHRASE-MISSING-$($phrase.Replace(' ', '-'))" $check.severity "$($check.path) missing phrase: $phrase" "Update $($check.path)."
        }
    }
}

$sourceRepos = @()
$ragIndexPath = Join-Path $Root "manifests/TMP-REPO-RAG-INDEX.json"
if (Test-Path -LiteralPath $ragIndexPath) {
    try {
        $ragIndex = Get-Content -LiteralPath $ragIndexPath -Raw | ConvertFrom-Json
        $sourceRepos = @($ragIndex.repos | Where-Object {
            $_.ragState -eq "local_inspected" -or $_.ragState -eq "held"
        } | Select-Object -ExpandProperty localFolder)
    } catch {
        Add-Issue $issues "RAG-INDEX-PARSE-FAILED" "high" "Failed to parse TMP-REPO-RAG-INDEX.json." "Validate JSON syntax in manifests/TMP-REPO-RAG-INDEX.json."
    }
}

$sourceStates = foreach ($repo in $sourceRepos) {
    if (-not $repo) {
        continue
    }

    if (Test-Path -LiteralPath $repo) {
        $status = @(git -C $repo status --short 2>&1)
        $gitError = $null
        if ($LASTEXITCODE -ne 0) {
            $gitError = ($status -join " ")
            $status = @()
            $safeRepoId = ($repo -replace "[^A-Za-z0-9]+", "-").Trim("-")
            Add-Issue $issues "SOURCE-GIT-STATUS-FAILED-$safeRepoId" "high" "Git status failed for source repo: $repo" "Inspect source repo ownership or safe-directory settings."
        }

        [pscustomobject]@{
            repo = $repo
            exists = $true
            dirty = if ($gitError) { $null } else { ($status.Count -gt 0) }
            changedCount = $status.Count
            state = if ($gitError) { "git_status_failed" } elseif ($status.Count -gt 0) { "local_dirty" } else { "local_clean" }
            gitStatusError = $gitError
        }
    } else {
        if (-not $CloudVirtualization) {
            Add-Issue $issues "SOURCE-MISSING-$repo" "medium" "Source repo missing: $repo" "Update manifests to current source paths."
        }

        [pscustomobject]@{
            repo = $repo
            exists = $false
            dirty = $false
            changedCount = 0
            state = if ($CloudVirtualization) { "cloud_metadata_only" } else { "missing" }
            boundary = if ($CloudVirtualization) { "Local source tree is not visible from GitHub Actions; inspect locally before mutation." } else { "Local source tree expected but missing." }
        }
    }
}

$held.Add([pscustomobject]@{
    id = "LANTERN-OS-BOOT-001"
    severity = "blocked"
    summary = "Actual dual boot installation requires physical operator action."
    fix = "Keep held; do not automate disk, BCD, firmware, or bootloader mutation."
}) | Out-Null

if ($CloudVirtualization) {
    $held.Add([pscustomobject]@{
        id = "LANTERN-OS-CLOUD-LOCAL-001"
        severity = "held"
        summary = "Cloud virtualization cannot see local-only MCP endpoints, dirty worktrees, Windows Store apps, or private disks."
        fix = "Validate repo invariants in cloud; validate local runtime on the operator machine."
    }) | Out-Null
}

$result = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    mode = if ($CloudVirtualization) { "cloud_virtualization" } else { "local" }
    method = "Lantern OS 12-step convergence loop"
    designedRingSlots = 36
    elasticPoolTarget = 64
    fleetClaimBoundary = "design contract only; live worker counts require local orchestrator evidence"
    fixWindow = $FixWindow
    issueCount = $issues.Count
    leadingIssues = @($issues | Select-Object -First $FixWindow)
    held = $held
    sourceRepos = @($sourceStates)
    nextAction = if ($issues.Count -gt 0) {
        "Fix the first $([Math]::Min($FixWindow, $issues.Count)) actionable issue(s), then rerun."
    } elseif ($CloudVirtualization) {
        "Cloud repo invariants passed. Run local controls on the operator machine before MCP/local runtime mutation."
    } else {
        "No local loop issues found. Review held issues and choose the next promotion candidate."
    }
}

$json = $result | ConvertTo-Json -Depth 8
Write-Output $json

if ($Output) {
    $outputPath = if ([System.IO.Path]::IsPathRooted($Output)) {
        $Output
    } else {
        Join-Path (Get-Location) $Output
    }

    $outputDirectory = Split-Path -Path $outputPath -Parent
    if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    }
    $json | Set-Content -LiteralPath $outputPath -Encoding utf8
}

if ($issues.Count -gt 0) {
    exit 1
}

exit 0
