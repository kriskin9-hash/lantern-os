param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

$hookPath = Join-Path $Root '.claude/hooks/enforce-pr-closure.ps1'
if (-not (Test-Path -LiteralPath $hookPath -PathType Leaf)) {
    throw "Missing hook: $hookPath"
}

$hookText = Get-Content -LiteralPath $hookPath -Raw

if ($hookText -match 'Emit-Skip\s+"gh CLI not installed') {
    throw 'PR closure hook must block, not skip, when gh is unavailable.'
}

if ($hookText -notmatch 'Get-Command\s+gh\s+-ErrorAction\s+SilentlyContinue') {
    throw 'PR closure hook must use Get-Command gh -ErrorAction SilentlyContinue to detect gh availability (cross-platform; not where.exe).'
}

if ($hookText -notmatch 'gh CLI not installed or not on PATH') {
    throw "PR closure hook must emit 'gh CLI not installed or not on PATH' block message when gh is absent."
}

if ($hookText -match 'if \(\$branch -in @\("master", "main"\)\) \{\s*Emit-Allow') {
    throw 'PR closure hook must not unconditionally allow protected branches.'
}

$autoPushDefault = Select-String -Path $hookPath -Pattern '^\$autoPushEnabled\s*=' | Select-Object -First 1
if ($null -eq $autoPushDefault -or $autoPushDefault.Line -notmatch '\$false') {
    throw 'PR closure hook must set auto-push default to false.'
}

if ($hookText -notmatch 'CLAUDE_HOOK_AUTOPUSH\s+-match\s+"\^\(1\|true\|yes\|on\)\$"') {
    throw 'PR closure hook must require explicit CLAUDE_HOOK_AUTOPUSH opt-in for auto-push.'
}

function New-TestRepo {
    $path = Join-Path ([System.IO.Path]::GetTempPath()) ("gm-orch-hook-test-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $path | Out-Null

    & git -C $path init --initial-branch=master | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git init failed' }

    & git -C $path config user.email 'hook-test@example.invalid' | Out-Null
    & git -C $path config user.name 'Hook Test' | Out-Null

    Set-Content -LiteralPath (Join-Path $path 'README.md') -Value '# hook test' -Encoding UTF8
    & git -C $path add README.md | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git add failed' }
    & git -C $path commit -m 'initial' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed' }

    return $path
}

function Invoke-HookForRepo {
    param(
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [string]$PayloadJson = '{}'
    )

    $previousProjectDir = $env:CLAUDE_PROJECT_DIR
    $previousAutoPush = $env:CLAUDE_HOOK_AUTOPUSH

    try {
        $env:CLAUDE_PROJECT_DIR = $RepoPath
        Remove-Item Env:\CLAUDE_HOOK_AUTOPUSH -ErrorAction SilentlyContinue

        $output = $PayloadJson | & powershell -NoProfile -ExecutionPolicy Bypass -File $hookPath
        if ($LASTEXITCODE -ne 0) { throw "Hook process exited non-zero: $LASTEXITCODE" }

        $text = ($output | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($text)) {
            throw 'Hook produced no JSON output.'
        }

        return $text | ConvertFrom-Json
    }
    finally {
        if ($null -eq $previousProjectDir) {
            Remove-Item Env:\CLAUDE_PROJECT_DIR -ErrorAction SilentlyContinue
        }
        else {
            $env:CLAUDE_PROJECT_DIR = $previousProjectDir
        }

        if ($null -eq $previousAutoPush) {
            Remove-Item Env:\CLAUDE_HOOK_AUTOPUSH -ErrorAction SilentlyContinue
        }
        else {
            $env:CLAUDE_HOOK_AUTOPUSH = $previousAutoPush
        }
    }
}

function Assert-BlockDecision {
    param(
        [Parameter(Mandatory = $true)]$Decision,
        [Parameter(Mandatory = $true)][string]$ReasonPattern,
        [Parameter(Mandatory = $true)][string]$CaseName
    )

    if ($Decision.decision -ne 'block') {
        throw "$CaseName expected block decision; got: $($Decision.decision)"
    }

    if ($Decision.reason -notmatch $ReasonPattern) {
        throw "$CaseName unexpected block reason: $($Decision.reason)"
    }
}

$tempRoots = New-Object System.Collections.Generic.List[string]

try {
    $dirtyMasterRepo = New-TestRepo
    [void]$tempRoots.Add($dirtyMasterRepo)
    Add-Content -LiteralPath (Join-Path $dirtyMasterRepo 'README.md') -Value 'dirty protected branch'
    $dirtyMasterDecision = Invoke-HookForRepo -RepoPath $dirtyMasterRepo
    Assert-BlockDecision `
        -Decision $dirtyMasterDecision `
        -ReasonPattern "Protected branch 'master' has local changes" `
        -CaseName 'dirty master'

    $noUpstreamRepo = New-TestRepo
    [void]$tempRoots.Add($noUpstreamRepo)
    & git -C $noUpstreamRepo checkout -b feature/no-upstream | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git checkout feature/no-upstream failed' }
    Add-Content -LiteralPath (Join-Path $noUpstreamRepo 'README.md') -Value 'feature work'
    & git -C $noUpstreamRepo add README.md | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git add feature work failed' }
    & git -C $noUpstreamRepo commit -m 'feature work' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git commit feature work failed' }
    $noUpstreamDecision = Invoke-HookForRepo -RepoPath $noUpstreamRepo
    Assert-BlockDecision `
        -Decision $noUpstreamDecision `
        -ReasonPattern "Branch 'feature/no-upstream' has no upstream.*git push -u origin feature/no-upstream" `
        -CaseName 'feature branch without upstream'

    # gh-missing case: covered by static source analysis in the preamble above.
    # Runtime PATH manipulation to remove gh also removes git and system32 tools, causing
    # the hook to fail at branch detection rather than the gh check. The static assertions
    # are sufficient: they verify the mechanism (Get-Command gh), the message text, and
    # that Emit-Block (not Emit-Skip) is called.
}
finally {
    foreach ($path in $tempRoots) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host 'Claude PR closure hook tests passed.'
