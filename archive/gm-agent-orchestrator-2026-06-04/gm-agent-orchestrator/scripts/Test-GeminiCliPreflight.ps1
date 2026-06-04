[CmdletBinding()]
param(
    [int]$TimeoutSeconds = 30,
    [switch]$SkipPrompt
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$statusDir = Join-Path $root "status"
$reportDir = Join-Path $root "reports\agents"
$statusPath = Join-Path $statusDir "gemini-preflight.json"
$reportPath = Join-Path $reportDir "gemini-preflight-latest.md"

function Read-TextFileSafe {
    param([Parameter(Mandatory = $true)] [string]$Path)

    if (-not (Test-Path $Path)) {
        return ""
    }

    $value = Get-Content -Path $Path -Raw -ErrorAction SilentlyContinue
    if ($null -eq $value) {
        return ""
    }

    return $value.Trim()
}

function Invoke-CheckedProcess {
    param(
        [Parameter(Mandatory = $true)] [string]$CommandPath,
        [Parameter(Mandatory = $true)] [string[]]$Arguments,
        [Parameter(Mandatory = $true)] [int]$TimeoutSeconds
    )

    $temp = [System.IO.Path]::GetTempFileName()
    $out = "$temp.out"
    $err = "$temp.err"

    try {
        # Using & for scripts/executables in current shell context with redirection
        $sb = {
            param($c, $a, $o, $e)
            & $c @a > $o 2> $e
            return $LASTEXITCODE
        }

        $job = Start-Job -ScriptBlock $sb -ArgumentList $CommandPath, $Arguments, $out, $err
        $done = Wait-Job $job -Timeout $TimeoutSeconds


        if ($null -eq $done) {
            Stop-Job $job
            Remove-Job $job
            return [ordered]@{ exitCode = $null; timedOut = $true; stdout = ""; stderr = "Timed out" }
        }

        $jobResult = Receive-Job $job
        $exitCode = if ($null -ne $jobResult) { [int]$jobResult } else { 0 }
        Remove-Job $job

        return [ordered]@{
            exitCode = $exitCode
            timedOut = $false
            stdout = Read-TextFileSafe -Path $out
            stderr = Read-TextFileSafe -Path $err
        }
    }
    finally {
        Remove-Item -Path $temp, $out, $err -Force -ErrorAction SilentlyContinue
    }
}

function Limit-Text {
    param([string]$Text, [int]$MaxLength = 500)
    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
    if ($Text.Length -le $MaxLength) { return $Text }
    return $Text.Substring(0, $MaxLength) + "..."
}

function Test-GeminiMcpIssueText {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
    return $Text -match '(?i)MCP issues detected|Run /mcp list for status|MCP server .*failed|MCP.*unavailable'
}

New-Item -ItemType Directory -Path $statusDir -Force | Out-Null
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null

$result = [ordered]@{
    checkedAt = (Get-Date).ToString("o")
    issue = 29
    geminiFound = $false
    commandPath = ""
    version = ""
    authReady = $false
    freeTierEvidence = "unknown; this local preflight does not prove billing or quota status"
    noWritePromptPassed = $false
    mcpIssueDetected = $false
    mcpIssueEvidence = ""
    recommendedNext = "blocked"
    promptAttempted = -not $SkipPrompt.IsPresent
    promptOutputPreview = ""
    errors = @()
    honestyCheck = [ordered]@{
        verified = @()
        assumed = @(
            "Gemini CLI prompt syntax may vary by installed version."
            "Account billing and quota state must be verified outside this basic process check."
        )
        grudgebookEntryRequired = $false
    }
}

$cmd = Get-Command "gemini" -ErrorAction SilentlyContinue
if ($null -eq $cmd) {
    $result.errors += "Gemini CLI was not found on PATH."
}
else {
    $result.geminiFound = $true
    $result.commandPath = $cmd.Source
    $result.honestyCheck.verified += "Gemini CLI command was found on PATH ($($cmd.CommandType))."

    # Use --skip-trust to bypass directory trust dialogs in automation
    $version = Invoke-CheckedProcess -CommandPath $cmd.Source -Arguments @("--version", "--skip-trust") -TimeoutSeconds $TimeoutSeconds
    if (-not $version.timedOut -and -not [string]::IsNullOrWhiteSpace($version.stdout)) {
        $result.version = Limit-Text -Text $version.stdout -MaxLength 120
        $result.honestyCheck.verified += "Gemini CLI responded to --version."
    }
    else {
        $result.errors += "Gemini CLI --version did not return output (TimedOut=$($version.timedOut))."
    }

    if (-not $SkipPrompt.IsPresent) {
        $prompt = "Reply exactly GEMINI_PREFLIGHT_OK. Do not read files. Do not write files. Do not run tools."
        # Use --skip-trust to bypass directory trust dialogs in automation
        $check = Invoke-CheckedProcess -CommandPath $cmd.Source -Arguments @("-p", $prompt, "--skip-trust") -TimeoutSeconds $TimeoutSeconds
        $combined = (($check.stdout, $check.stderr) -join "`n").Trim()
        $result.promptOutputPreview = Limit-Text -Text $combined -MaxLength 500
        $result.mcpIssueDetected = Test-GeminiMcpIssueText -Text $combined
        if ($result.mcpIssueDetected) {
            $result.mcpIssueEvidence = Limit-Text -Text $combined -MaxLength 240
            $result.errors += "Gemini CLI reported MCP issues during the no-write prompt. Run /mcp list locally and verify the configured MCP endpoint before dispatching Gemini slots."
        }

        if (-not $check.timedOut -and $combined -match "GEMINI_PREFLIGHT_OK" -and -not $result.mcpIssueDetected) {
            $result.authReady = $true
            $result.noWritePromptPassed = $true
            $result.recommendedNext = "evaluate"
            $result.honestyCheck.verified += "Gemini CLI completed a tiny no-write prompt with the expected marker."
        }
        elseif (-not $check.timedOut -and $combined -match "GEMINI_PREFLIGHT_OK" -and $result.mcpIssueDetected) {
            $result.authReady = $true
            $result.noWritePromptPassed = $true
            $result.recommendedNext = "blocked"
            $result.honestyCheck.verified += "Gemini CLI completed the no-write prompt, but MCP health was not clean."
        }
        else {
            $result.errors += "Gemini CLI prompt check failed or did not return expected marker."
        }
    }
    else {
        $result.honestyCheck.verified += "Prompt check was skipped by caller."
        $result.recommendedNext = "evaluate"
    }
}

$json = ($result | ConvertTo-Json -Depth 8).TrimEnd()
$json | Set-Content -Path $statusPath -Encoding UTF8

$verifiedLines = (@($result.honestyCheck.verified) | ForEach-Object { "- $_" }) -join "`n"
$assumedLines = (@($result.honestyCheck.assumed) | ForEach-Object { "- $_" }) -join "`n"
$errorLines = if (@($result.errors).Count -gt 0) { (@($result.errors) | ForEach-Object { "- $_" }) -join "`n" } else { "- none" }

$report = @"
# Gemini CLI Preflight

Issue: #29
Checked: $($result.checkedAt)

## Result

- Gemini found: $($result.geminiFound)
- Version: $($result.version)
- Auth ready: $($result.authReady)
- No-write prompt passed: $($result.noWritePromptPassed)
- MCP issue detected: $($result.mcpIssueDetected)
- Recommended next: $($result.recommendedNext)
- Free-tier evidence: $($result.freeTierEvidence)

## Honesty check

Verified:
$verifiedLines

Assumed:
$assumedLines

## Errors

$errorLines
"@.TrimEnd()

$report | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "Wrote $statusPath"
Write-Host "Wrote $reportPath"
Write-Host "Recommended next: $($result.recommendedNext)"

if ($result.recommendedNext -eq "blocked") { exit 1 }
