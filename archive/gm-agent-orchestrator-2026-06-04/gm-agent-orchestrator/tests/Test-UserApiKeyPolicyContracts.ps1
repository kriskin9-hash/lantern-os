[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$docPath = Join-Path $Root "docs\product\user-identity-and-api-keys.md"
if (-not (Test-Path -LiteralPath $docPath -PathType Leaf)) {
    throw "User API key policy doc missing: $docPath"
}

$doc = Get-Content -LiteralPath $docPath -Raw
foreach ($needle in @(
    "Rotation cadence",
    "Expiration handling",
    "Leak response",
    "Revocation closed loop",
    "Per-task cap",
    "must not silently retry"
)) {
    if ($doc -notmatch [regex]::Escape($needle)) {
        throw "User key policy doc missing required section/text: $needle"
    }
}

function Resolve-KeyForTask {
    param(
        [array]$KeyStates,
        [string]$UserId,
        [decimal]$EstimatedCostUsd
    )

    # Contract: only evaluate keys that belong to the requesting user.
    $candidateKeys = @($KeyStates | Where-Object { $_.userId -eq $UserId })
    foreach ($key in $candidateKeys) {
        if ($key.revoked -eq $true) { continue }
        if ($key.cacheState -eq "revoked") { continue }
        if (($key.taskSpentUsd + $EstimatedCostUsd) -gt $key.taskCapUsd) { continue }
        if (($key.dailySpentUsd + $EstimatedCostUsd) -gt $key.dailyCapUsd) { continue }
        if (($key.monthlySpentUsd + $EstimatedCostUsd) -gt $key.monthlyCapUsd) { continue }
        return $key
    }
    return $null
}

# Contract 1: revoked key cannot be served from cache after revocation.
$revokedSet = @(
    [pscustomobject]@{
        keyId = "key-a"
        userId = "alice"
        revoked = $true
        cacheState = "revoked"
        taskCapUsd = 20
        taskSpentUsd = 0
        dailyCapUsd = 50
        dailySpentUsd = 0
        monthlyCapUsd = 200
        monthlySpentUsd = 0
    }
)

$revokedResolved = Resolve-KeyForTask -KeyStates $revokedSet -UserId "alice" -EstimatedCostUsd 5
if ($null -ne $revokedResolved) {
    throw "Revocation contract failed: revoked key was returned."
}

# Contract 2: per-task cap hit must not silently fallback to another user's key.
$capSet = @(
    [pscustomobject]@{
        keyId = "alice-key"
        userId = "alice"
        revoked = $false
        cacheState = "active"
        taskCapUsd = 10
        taskSpentUsd = 9
        dailyCapUsd = 50
        dailySpentUsd = 5
        monthlyCapUsd = 200
        monthlySpentUsd = 20
    },
    [pscustomobject]@{
        keyId = "bob-key"
        userId = "bob"
        revoked = $false
        cacheState = "active"
        taskCapUsd = 30
        taskSpentUsd = 0
        dailyCapUsd = 80
        dailySpentUsd = 0
        monthlyCapUsd = 500
        monthlySpentUsd = 0
    }
)

$capResolved = Resolve-KeyForTask -KeyStates $capSet -UserId "alice" -EstimatedCostUsd 3
if ($null -ne $capResolved) {
    throw "Per-task cap contract failed: request should block, not fallback."
}

Write-Host "User API key policy contracts passed."
