$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$contractPath = Join-Path $repoRoot 'docs/repo-structure-contract.md'

if (-not (Test-Path -LiteralPath $contractPath)) {
    throw 'Missing docs/repo-structure-contract.md'
}

$allowedExactRootFiles = @(
    '.env.local.example',
    'README.md',
    'AGENTS.md',
    'CLAUDE.md',
    '.gitignore',
    '.gitattributes',
    'LICENSE',
    'SECURITY.md',
    'CONTRIBUTING.md',
    'AGENT_LINEUP_ANALYSIS.md',
    'AGENT_RESPONSIBILITIES.md',
    'AGENT_STATUS.md',
    'Cold-Start.ps1',
    'COMPLETION_SUMMARY.md',
    'CONTAINERIZATION_AND_DR.md',
    'DASHBOARD_IMPLEMENTATION_STATUS.md',
    'DESIGN_CONTRACT.md',
    'Inspect-DashboardScript.ps1',
    'ISSUE_CLAUDE_UI_DEGRADATION.md',
    'orchestrator.json',
    'QA_CHECKLIST.md',
    'RUN_FROM_DOCUMENTS.ps1',
    'RUN_INIT_AGENT_CLI.ps1',
    'TASK_FAILURE_POLICY.txt',
    'tunnel.log'
)

$allowedRootPatterns = @(
    '^package(-lock)?\.json$',
    '^pnpm-lock\.yaml$',
    '^yarn\.lock$',
    '^requirements\.txt$',
    '^pyproject\.toml$',
    '^PSScriptAnalyzerSettings\.psd1$'
)

$rootFiles = Get-ChildItem -LiteralPath $repoRoot -File -Force
$violations = New-Object System.Collections.Generic.List[string]

foreach ($file in $rootFiles) {
    $name = $file.Name
    $isAllowed = $allowedExactRootFiles -contains $name

    if (-not $isAllowed) {
        foreach ($pattern in $allowedRootPatterns) {
            if ($name -match $pattern) {
                $isAllowed = $true
                break
            }
        }
    }

    if (-not $isAllowed) {
        $violations.Add("Root file is not allowlisted; archive, promote, or explicitly allow it: $name")
    }
}

$requiredDirectories = @(
    'docs/archive/disaster-recovery-2026-04',
    'scripts/archive/disaster-recovery-2026-04',
    'tests'
)

foreach ($relativePath in $requiredDirectories) {
    $path = Join-Path $repoRoot $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        $violations.Add("Missing required directory: $relativePath")
    }
}

$requiredIndexes = @(
    'docs/archive/disaster-recovery-2026-04/INDEX.md',
    'scripts/archive/disaster-recovery-2026-04/INDEX.md'
)

foreach ($relativePath in $requiredIndexes) {
    $path = Join-Path $repoRoot $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $violations.Add("Missing archive index: $relativePath")
    }
}

$taskFolders = @('queue', 'active', 'done', 'failed', 'hold', 'disabled')
foreach ($folder in $taskFolders) {
    $path = Join-Path $repoRoot (Join-Path 'tasks' $folder)
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        $violations.Add("Missing task state folder: tasks/$folder")
        continue
    }

    $archiveDirs = @(Get-ChildItem -LiteralPath $path -Directory -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -in @('archive', 'archives', 'docs') })
    foreach ($archiveDir in $archiveDirs) {
        $violations.Add("Task folder must not become a docs archive: $($archiveDir.FullName.Substring($repoRoot.Length + 1))")
    }

    $unexpectedFiles = @(Get-ChildItem -LiteralPath $path -File -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne '.gitkeep' -and $_.Extension -ne '.md' })
    foreach ($unexpectedFile in $unexpectedFiles) {
        $violations.Add("Task folder contains non-task file: $($unexpectedFile.FullName.Substring($repoRoot.Length + 1))")
    }
}

if ($violations.Count -gt 0) {
    throw ($violations -join [Environment]::NewLine)
}

Write-Host 'Repo structure contract passed.'
