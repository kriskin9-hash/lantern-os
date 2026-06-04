[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        $PSScriptRoot
    }
    elseif ($MyInvocation.MyCommand.Path) {
        Split-Path -Parent $MyInvocation.MyCommand.Path
    }
    else {
        throw 'Cannot resolve repository root because neither $Root nor script path is available.'
    }

    $Root = (Resolve-Path -LiteralPath (Join-Path -Path $scriptDir -ChildPath '..')).Path
}
else {
    $Root = (Resolve-Path -LiteralPath $Root).Path
}

$runnerScript = Join-Path -Path $Root -ChildPath "scripts\Invoke-OrchestratorSafePowerShell.ps1"
if (-not (Test-Path -LiteralPath $runnerScript -PathType Leaf)) {
    throw "Safe runner script was not found: $runnerScript"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-safe-runner-test-{0}" -f [Guid]::NewGuid().ToString("N"))

function New-TestRoot {
    param([string]$Path)

    New-Item -ItemType Directory -Force -Path (Join-Path $Path "scripts") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $Path "logs\control-actions") | Out-Null

    @'
[CmdletBinding()]
param([string]$Root = "")
[pscustomobject]@{
  ok = $true
  helper = "status"
  root = $Root
} | ConvertTo-Json -Depth 5
'@ | Set-Content -LiteralPath (Join-Path $Path "scripts\Get-OrchestratorStatus.ps1") -Encoding UTF8

    @'
[CmdletBinding()]
param(
  [string]$Title = "Default title",
  [string]$Body = "Default body",
  [switch]$DryRun
)
[pscustomobject]@{
  ok = $true
  helper = "queue-create"
  title = $Title
  body = $Body
  dryRun = [bool]$DryRun
} | ConvertTo-Json -Depth 5
'@ | Set-Content -LiteralPath (Join-Path $Path "scripts\New-OrchestratorQueueTask.ps1") -Encoding UTF8
}

function ConvertTo-ForwardSlashPath {
    param([string]$Path)
    return $Path -replace "\\", "/"
}

function ConvertTo-ArgumentBase64 {
    param([string]$Json)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Json)
    return [Convert]::ToBase64String($bytes)
}

function Invoke-SafeRunner {
    param([string[]]$Arguments)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $runnerScript @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }

        return [pscustomobject]@{
            exitCode = [int]$exitCode
            output = ($output | ForEach-Object { $_.ToString() }) -join "`n"
        }
    }
    catch {
        return [pscustomobject]@{
            exitCode = 1
            output = $_.Exception.Message
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Convert-RunnerJson {
    param([string]$Output)

    $trimmed = $Output.Trim()
    if (-not $trimmed.StartsWith("{")) {
        throw "Expected JSON object output. Actual output: $Output"
    }

    return $trimmed | ConvertFrom-Json -ErrorAction Stop
}

function New-RunnerFailureDetail {
    param([object]$Result)

    return @(
        "state=$($Result.state)",
        "reason=$($Result.reason)",
        "exitCode=$($Result.exitCode)",
        "stdout=$($Result.stdoutTail)",
        "stderr=$($Result.stderrTail)",
        "args=$(@($Result.args) -join ' ')"
    ) -join " | "
}

try {
    New-TestRoot -Path $tempRoot

    $tempRootJsonPath = ConvertTo-ForwardSlashPath -Path $tempRoot
    $statusArgsBase64 = ConvertTo-ArgumentBase64 -Json ('["-Root","' + $tempRootJsonPath + '"]')
    $allowedRead = Invoke-SafeRunner -Arguments @(
        "-Root", $tempRoot,
        "-ScriptName", "Get-OrchestratorStatus.ps1",
        "-ArgumentJsonBase64", $statusArgsBase64
    )
    if ($allowedRead.exitCode -ne 0) { throw "Allowed read-only helper failed: $($allowedRead.output)" }

    $readJson = Convert-RunnerJson -Output $allowedRead.output
    if (-not $readJson.ok) { throw "Expected allowed read-only helper result ok=true. $(New-RunnerFailureDetail -Result $readJson)" }
    if ($readJson.scriptName -ne "Get-OrchestratorStatus.ps1") { throw "Unexpected scriptName: $($readJson.scriptName)" }
    if ($readJson.mutatedState) { throw "Read-only status helper must not report mutatedState=true." }
    if ($readJson.auditPath -notmatch "logs/control-actions/.+safe_powershell_runner\.json") { throw "Expected safe runner audit path, got $($readJson.auditPath)." }
    if ($readJson.stdoutTail -notmatch "status") { throw "Expected stdout tail to include helper output. $(New-RunnerFailureDetail -Result $readJson)" }

    $queueArgsBase64 = ConvertTo-ArgumentBase64 -Json '["-Title","Dry run task","-Body","Safe runner test."]'
    $allowedDryRun = Invoke-SafeRunner -Arguments @(
        "-Root", $tempRoot,
        "-ScriptName", "New-OrchestratorQueueTask.ps1",
        "-ArgumentJsonBase64", $queueArgsBase64,
        "-DryRun"
    )
    if ($allowedDryRun.exitCode -ne 0) { throw "Allowed dry-run helper failed: $($allowedDryRun.output)" }

    $dryJson = Convert-RunnerJson -Output $allowedDryRun.output
    if (-not $dryJson.ok) { throw "Expected queue helper dry-run result ok=true. $(New-RunnerFailureDetail -Result $dryJson)" }
    if ($dryJson.mutatedState) { throw "Dry-run mutating helper must not report mutatedState=true." }
    if (-not $dryJson.dryRun) { throw "Runner result must record dryRun=true." }
    if ($dryJson.stdoutTail -notmatch '"dryRun"\s*:\s*true') { throw "Helper stdout must show dryRun=true. $(New-RunnerFailureDetail -Result $dryJson)" }

    $blockedArgsBase64 = ConvertTo-ArgumentBase64 -Json '["-Recurse","C:/"]'
    $blocked = Invoke-SafeRunner -Arguments @(
        "-Root", $tempRoot,
        "-ScriptName", "Remove-Item.ps1",
        "-ArgumentJsonBase64", $blockedArgsBase64
    )
    if ($blocked.exitCode -ne 0) { throw "Blocked command should still return JSON with process exit 0. Output: $($blocked.output)" }

    $blockedJson = Convert-RunnerJson -Output $blocked.output
    if ($blockedJson.ok) { throw "Unsafe command should return ok=false." }
    if ($blockedJson.state -ne "blocked") { throw "Unsafe command should return state=blocked." }
    if ($blockedJson.reason -notmatch "allowlist") { throw "Unsafe command should explain allowlist rejection. Actual: $($blockedJson.reason)" }
    if ($blockedJson.mutatedState) { throw "Blocked commands must not report mutatedState=true." }
    if ($blockedJson.auditPath -notmatch "logs/control-actions/.+safe_powershell_runner\.json") { throw "Blocked command must still be audited." }

    $unsafeArgumentCases = @(
        @{ name = "LF"; body = "first`nsecond" },
        @{ name = "CR"; body = "first`rsecond" },
        @{ name = "CRLF"; body = "first`r`nsecond" }
    )
    foreach ($case in $unsafeArgumentCases) {
        $json = ConvertTo-Json -Compress -InputObject @("-Title", "$($case.name) newline test", "-Body", $case.body)
        $argsBase64 = ConvertTo-ArgumentBase64 -Json $json
        $result = Invoke-SafeRunner -Arguments @(
            "-Root", $tempRoot,
            "-ScriptName", "New-OrchestratorQueueTask.ps1",
            "-ArgumentJsonBase64", $argsBase64,
            "-DryRun"
        )
        if ($result.exitCode -ne 0) { throw "CR/LF blocked argument should still return JSON with process exit 0. Output: $($result.output)" }

        $jsonResult = Convert-RunnerJson -Output $result.output
        if ($jsonResult.ok) { throw "$($case.name) argument should return ok=false." }
        if ($jsonResult.state -ne "blocked") { throw "$($case.name) argument should return state=blocked." }
        if ($jsonResult.reason -notmatch "CR or LF") { throw "$($case.name) argument should explain CR/LF rejection. Actual: $($jsonResult.reason)" }
        if ($jsonResult.mutatedState) { throw "$($case.name) blocked argument must not report mutatedState=true." }
    }

    $escape = Invoke-SafeRunner -Arguments @(
        "-Root", $tempRoot,
        "-ScriptName", "..\Get-OrchestratorStatus.ps1"
    )
    $escapeJson = Convert-RunnerJson -Output $escape.output
    if ($escapeJson.ok -or $escapeJson.state -ne "blocked") { throw "Path traversal script names must be blocked." }

    Write-Host "Safe PowerShell runner tests passed."
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
