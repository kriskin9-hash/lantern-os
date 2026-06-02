[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-GitPullClassification {
    param(
        [Parameter(Mandatory = $true)][int]$ExitCode,
        [bool]$TimedOut = $false
    )

    if ($TimedOut) { return 'timed_out' }
    if ($ExitCode -eq 0) { return 'success' }
    return 'failed'
}

$simulatedStdout = @'
Already up to date.
'@

$simulatedStderr = @'
From https://github.com/alex-place/gm-agent-orchestrator
 * branch            master     -> FETCH_HEAD
'@

$classification = Get-GitPullClassification -ExitCode 0

if ($classification -ne 'success') {
    throw "Expected exitCode 0 with git progress text to classify as success, got: $classification"
}

$result = [pscustomobject]@{
    ok = $true
    gitPull = [pscustomobject]@{
        exitCode = 0
        stdout = $simulatedStdout
        stderr = $simulatedStderr
        classification = $classification
    }
}

$result | ConvertTo-Json -Depth 10
