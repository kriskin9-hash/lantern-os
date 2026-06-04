[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $Root 'scripts\Test-GeminiCliPreflight.ps1'
$statusPath = Join-Path $Root 'status\gemini-preflight.json'
$reportPath = Join-Path $Root 'reports\agents\gemini-preflight-latest.md'

if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
    throw "Missing Gemini preflight script: $scriptPath"
}

$content = Get-Content -LiteralPath $scriptPath -Raw
foreach ($needle in @('mcpIssueDetected', 'MCP issues detected', 'Run /mcp list locally', 'Test-GeminiMcpIssueText')) {
    if ($content -notmatch [regex]::Escape($needle)) {
        throw "Gemini preflight must preserve MCP issue classification contract: missing $needle"
    }
}

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("gm-orch-fake-gemini-" + [guid]::NewGuid().ToString('N'))
$oldPath = $env:PATH
$statusExisted = Test-Path -LiteralPath $statusPath
$reportExisted = Test-Path -LiteralPath $reportPath
$statusBackup = if ($statusExisted) { Get-Content -LiteralPath $statusPath -Raw } else { $null }
$reportBackup = if ($reportExisted) { Get-Content -LiteralPath $reportPath -Raw } else { $null }

try {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    $fakeGemini = Join-Path $tempDir 'gemini.cmd'
    @'
@echo off
if "%1"=="--version" (
  echo 0.40.1-test
  exit /b 0
)
echo MCP issues detected. Run /mcp list for status.GEMINI_PREFLIGHT_OK
exit /b 0
'@ | Set-Content -LiteralPath $fakeGemini -Encoding ASCII

    $env:PATH = "$tempDir;$oldPath"
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath -TimeoutSeconds 10 2>&1
    $exitCode = $LASTEXITCODE
    # The child preflight is expected to exit 1 for a blocked MCP state. Keep that
    # assertion, but do not let the expected child exit code poison this parent
    # contract test's final process exit code after validations pass.
    $global:LASTEXITCODE = 0
    if ($exitCode -eq 0) {
        throw "Gemini preflight must exit non-zero when MCP issues are reported. Output: $($output -join "`n")"
    }

    $status = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
    if ($status.noWritePromptPassed -ne $true) { throw 'Expected no-write prompt marker to be recorded as passed.' }
    if ($status.authReady -ne $true) { throw 'Expected authReady=true when marker is present.' }
    if ($status.mcpIssueDetected -ne $true) { throw 'Expected mcpIssueDetected=true for Gemini MCP warning text.' }
    if ($status.recommendedNext -ne 'blocked') { throw "Expected recommendedNext=blocked, got $($status.recommendedNext)." }
    if (@($status.errors | Where-Object { $_ -match 'MCP issues' }).Count -lt 1) { throw 'Expected MCP issue to be present in errors.' }

    Write-Host 'Gemini CLI preflight contract tests passed.'
}
finally {
    $env:PATH = $oldPath
    Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue

    if ($statusExisted) { Set-Content -LiteralPath $statusPath -Value $statusBackup -Encoding UTF8 }
    elseif (Test-Path -LiteralPath $statusPath) { Remove-Item -LiteralPath $statusPath -Force }

    if ($reportExisted) { Set-Content -LiteralPath $reportPath -Value $reportBackup -Encoding UTF8 }
    elseif (Test-Path -LiteralPath $reportPath) { Remove-Item -LiteralPath $reportPath -Force }
}
