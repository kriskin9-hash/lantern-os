[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$contractPath = Join-Path $Root "docs\agent-contract.md"
if (-not (Test-Path $contractPath)) {
    throw "Agent contract not found: $contractPath"
}

$contract = Get-Content $contractPath -Raw

foreach ($requiredSection in @(
    "## Evidence records",
    "## Local-machine handoff requirements"
)) {
    if ($contract -notmatch [regex]::Escape($requiredSection)) {
        throw "Missing required contract section: $requiredSection"
    }
}

foreach ($requiredField in @(
    "SOURCE TYPE:",
    "SHELL / TOOL:",
    "DIRECTORY:",
    "COMMANDS RUN:",
    "STDOUT / STDERR EXCERPTS:",
    "EXIT CODE / STATE:",
    "COMMIT / BRANCH / PR / ISSUE / RUN ID:",
    "GENERATED FILES OR STATUS ARTIFACTS:",
    "OBSERVED BLOCKER / NEXT ACTION:",
    "TIMESTAMP:",
    "PROVES:",
    "DOES NOT PROVE:"
)) {
    if ($contract -notmatch [regex]::Escape($requiredField)) {
        throw "Missing evidence record field: $requiredField"
    }
}

foreach ($requiredField in @(
    "SHELL:",
    "SYNC COMMANDS:",
    "RUNTIME COMMANDS:",
    "VERIFY COMMANDS:",
    "EXPECTED RESULT:",
    "IF IT FAILS:",
    "EVIDENCE RECORD:"
)) {
    if ($contract -notmatch [regex]::Escape($requiredField)) {
        throw "Missing local-machine handoff field: $requiredField"
    }
}

foreach ($requiredPhrase in @(
    'Do not call guesses, planned commands, expected behavior, or unrun commands evidence.',
    'If the actual local path is known from evidence, use the actual path in the handoff.',
    'must not say only “sync to master,” “run the check,” or “restart the service.”'
)) {
    if ($contract -notmatch [regex]::Escape($requiredPhrase)) {
        throw "Missing evidence-record rule: $requiredPhrase"
    }
}

Write-Host "Validated evidence record and local-machine handoff contract."
