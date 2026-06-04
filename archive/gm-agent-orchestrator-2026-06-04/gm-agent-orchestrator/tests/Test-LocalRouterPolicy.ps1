[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$routerScript = Join-Path $Root 'scripts\Invoke-LocalRouter.ps1'
if (!(Test-Path $routerScript)) {
    throw "Router script was not found: $routerScript"
}

$content = Get-Content -LiteralPath $routerScript -Raw

foreach ($needle in @(
    'classification',
    'summarization',
    'routing',
    'code_explanation',
    'human_review',
    'PolicyOnly requires -RouterJson',
    'Local route denied because risk is not low.',
    'not read-only',
    'commands, deployment, production access, or secrets'
)) {
    if ($content -notmatch [regex]::Escape($needle)) {
        throw "Invoke-LocalRouter.ps1 policy contract is missing: $needle"
    }
}

foreach ($pattern in @(
    '\b(edit\|modify\|write\|rewrite\|patch\|commit\|merge\|rebase\|push\|delete\|remove\|rename\|move)\b',
    '\b(run\|execute\|invoke\|shell\|terminal\|powershell\|cmd\\\.exe\|bash\|script)\b',
    '\b(deploy\|release\|publish\|production\|prod\|rollback\|migration\|database)\b',
    '\b(secret\|credential\|password\|token\|api\[ -\]\?key\|private key)\b'
)) {
    if ($content -notmatch $pattern) {
        throw "Invoke-LocalRouter.ps1 blocked-intent pattern drifted: $pattern"
    }
}

Write-Host 'Local router policy tests passed.'
