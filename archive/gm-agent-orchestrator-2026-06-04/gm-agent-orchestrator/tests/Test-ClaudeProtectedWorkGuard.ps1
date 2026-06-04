[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$hookPath = Join-Path $Root '.claude/hooks/guard-protected-work.ps1'
$settingsPath = Join-Path $Root '.claude/settings.json'

if (-not (Test-Path -LiteralPath $hookPath)) { throw "Missing hook: $hookPath" }
if (-not (Test-Path -LiteralPath $settingsPath)) { throw "Missing settings: $settingsPath" }

$settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
if (-not ($settings.hooks.PSObject.Properties.Name -contains 'PreToolUse')) {
    throw '.claude/settings.json must register a PreToolUse hook.'
}

$registered = ($settings.hooks.PreToolUse | ConvertTo-Json -Depth 20)
if ($registered -notmatch 'guard-protected-work\.ps1') {
    throw 'PreToolUse hook must run guard-protected-work.ps1.'
}

$hookText = Get-Content $hookPath -Raw
foreach ($required in @('alex.place.7@gmail.com', 'Alex Place', 'ProtectedBranches', 'PreToolUse')) {
    if ($hookText -notmatch [regex]::Escape($required)) {
        throw "guard-protected-work.ps1 is missing required guard marker: $required"
    }
}

$tempRoots = New-Object System.Collections.Generic.List[string]

function New-TestRepo {
    param([string]$Branch = 'master')
    $path = Join-Path ([System.IO.Path]::GetTempPath()) ("gm-orch-guard-test-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $path | Out-Null
    [void]$tempRoots.Add($path)
    & git -C $path init --initial-branch=$Branch | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git init failed' }
    Set-Content -Path (Join-Path $path 'README.md') -Value '# temp' -Encoding UTF8
    & git -C $path add README.md | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git add failed' }
    & git -C $path -c user.name='Bootstrap Bot' -c user.email='bootstrap@example.invalid' commit -m 'init' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git commit init failed' }
    return $path
}

function Invoke-Guard {
    param(
        [string]$Repo,
        [string]$ToolName,
        [hashtable]$ToolInput
    )
    $previousProjectDir = $env:CLAUDE_PROJECT_DIR
    try {
        $env:CLAUDE_PROJECT_DIR = $Repo
        $payload = [pscustomobject]@{
            tool_name = $ToolName
            tool_input = [pscustomobject]$ToolInput
            cwd = $Repo
        } | ConvertTo-Json -Depth 10 -Compress
        $output = $payload | powershell -NoProfile -ExecutionPolicy Bypass -File $hookPath
        if ([string]::IsNullOrWhiteSpace(($output | Out-String).Trim())) { return $null }
        return ($output | Out-String | ConvertFrom-Json)
    }
    finally {
        $env:CLAUDE_PROJECT_DIR = $previousProjectDir
    }
}

function Assert-Block {
    param([object]$Decision, [string]$Pattern, [string]$CaseName)
    if ($null -eq $Decision) { throw "Expected block for $CaseName, got allow." }
    if ($Decision.decision -ne 'block') { throw "Expected block decision for $CaseName, got '$($Decision.decision)'." }
    if ($Decision.reason -notmatch $Pattern) { throw "Unexpected block reason for ${CaseName}: $($Decision.reason)" }
}

try {
    $masterRepo = New-TestRepo -Branch 'master'
    & git -C $masterRepo config user.name 'Alex Place' | Out-Null
    & git -C $masterRepo config user.email 'alex.place.7@gmail.com' | Out-Null

    $editDecision = Invoke-Guard -Repo $masterRepo -ToolName 'Edit' -ToolInput @{ file_path = (Join-Path $masterRepo 'README.md'); old_string = 'temp'; new_string = 'changed' }
    Assert-Block -Decision $editDecision -Pattern "protected branch 'master'" -CaseName 'edit on master'

    $commitDecision = Invoke-Guard -Repo $masterRepo -ToolName 'Bash' -ToolInput @{ command = 'git commit -m "bad"' }
    Assert-Block -Decision $commitDecision -Pattern 'protected branch|protected operator Git identity' -CaseName 'plain commit using operator identity'

    $branchSwitchDecision = Invoke-Guard -Repo $masterRepo -ToolName 'Bash' -ToolInput @{ command = 'git switch -c feature/bot-identity' }
    if ($null -ne $branchSwitchDecision) { throw "Expected branch switch command to be allowed, got: $($branchSwitchDecision | ConvertTo-Json -Compress)" }

    & git -C $masterRepo checkout -b feature/bot-identity | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git checkout feature failed' }

    $plainCommitDecision = Invoke-Guard -Repo $masterRepo -ToolName 'Bash' -ToolInput @{ command = 'git commit -m "bad"' }
    Assert-Block -Decision $plainCommitDecision -Pattern 'protected operator Git identity' -CaseName 'feature branch plain commit using operator identity'

    $botCommitDecision = Invoke-Guard -Repo $masterRepo -ToolName 'Bash' -ToolInput @{ command = 'git -c user.name="Claude Code" -c user.email="claude-code@agents.local" commit -m "ok"' }
    if ($null -ne $botCommitDecision) { throw "Expected bot identity commit command to be allowed, got: $($botCommitDecision | ConvertTo-Json -Compress)" }

    $mcpDecision = Invoke-Guard -Repo $masterRepo -ToolName 'mcp__crinkle-utmost-debit__commit_staged_changes' -ToolInput @{ message = 'bad' }
    Assert-Block -Decision $mcpDecision -Pattern 'protected operator Git identity' -CaseName 'MCP commit using operator identity'

    Write-Host 'Claude protected-work guard tests passed.'
}
finally {
    foreach ($path in $tempRoots) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}
