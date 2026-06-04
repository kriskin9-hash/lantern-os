[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$agentActionScript = Join-Path $Root 'scripts\Invoke-OrchestratorAgentAction.ps1'
if (-not (Test-Path -LiteralPath $agentActionScript -PathType Leaf)) {
    throw "Missing agent action script: $agentActionScript"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("gm-orch-gemini-dispatch-gate-" + [guid]::NewGuid().ToString('N'))
try {
    foreach ($dir in @('scripts', 'config', 'status', 'tasks\active', 'tasks\queue', 'tasks\done', 'tasks\failed')) {
        New-Item -ItemType Directory -Path (Join-Path $tempRoot $dir) -Force | Out-Null
    }
    Copy-Item -LiteralPath $agentActionScript -Destination (Join-Path $tempRoot 'scripts\Invoke-OrchestratorAgentAction.ps1')

    @{
        slots = @(
            @{ name = 'gemini-main'; agent = 'gemini'; enabled = $true; branch = 'agent/gemini-main'; command = @{ start = @('gemini') } },
            @{ name = 'codex-main'; agent = 'codex'; enabled = $true; branch = 'agent/codex-main'; command = @{ start = @('codex') } }
        )
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $tempRoot 'config\agents.json') -Encoding UTF8

    @{
        recommendedNext = 'blocked'
        mcpIssueDetected = $true
        mcpIssueEvidence = 'MCP issues detected. Run /mcp list for status.'
        errors = @('Gemini CLI reported MCP issues during the no-write prompt.')
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $tempRoot 'status\gemini-preflight.json') -Encoding UTF8

    $geminiOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tempRoot 'scripts\Invoke-OrchestratorAgentAction.ps1') -Root $tempRoot -Action start_agent -SlotName gemini-main -DryRun
    $gemini = ($geminiOutput | Out-String).Trim() | ConvertFrom-Json -ErrorAction Stop
    if ($gemini.ok -ne $false) { throw 'Gemini dry-run dispatch must be blocked when preflight is blocked.' }
    if ($gemini.blocked -ne $true) { throw 'Gemini dry-run dispatch must report blocked=true.' }
    if ($gemini.error -notmatch 'Gemini preflight blocks') { throw "Unexpected Gemini block reason: $($gemini.error)" }
    if ($null -ne $gemini.claim) { throw 'Gemini preflight block must occur before queue claim.' }

    '# active' | Set-Content -LiteralPath (Join-Path $tempRoot 'tasks\active\codex-main__active.md') -Encoding UTF8
    $codexOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tempRoot 'scripts\Invoke-OrchestratorAgentAction.ps1') -Root $tempRoot -Action start_agent -SlotName codex-main -DryRun
    $codex = ($codexOutput | Out-String).Trim() | ConvertFrom-Json -ErrorAction Stop
    if ($codex.ok -ne $false) { throw 'start_agent dry-run must be blocked when the slot already has an active task.' }
    if ($codex.error -notmatch 'already has an active task') { throw "Unexpected active-task block reason: $($codex.error)" }
    if ($null -ne $codex.claim) { throw 'Active-task block must occur before queue claim.' }

    Write-Host 'Gemini dispatch preflight gate tests passed.'
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
