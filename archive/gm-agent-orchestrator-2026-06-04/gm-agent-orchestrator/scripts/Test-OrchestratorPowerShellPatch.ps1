[CmdletBinding()]
param(
    [string]$Root = "",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-TestResult {
    param(
        [bool]$Ok,
        [string]$State,
        [string]$ErrorMessage = ""
    )

    [pscustomobject]@{
        ok = $Ok
        state = $State
        dry_run = [bool]$DryRun
        error = $ErrorMessage
        generated_at = (Get-Date).ToString("o")
    }
}

try {
    if ([string]::IsNullOrWhiteSpace($Root)) {
        $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    if (!(Test-Path -LiteralPath $Root -PathType Container)) {
        throw "Missing root: $Root"
    }

    $helper = Join-Path $Root "scripts\Invoke-OrchestratorPowerShellPatch.ps1"
    if (!(Test-Path -LiteralPath $helper -PathType Leaf)) {
        throw "Missing helper script: $helper"
    }

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $helper), [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) {
        throw "Helper parser failed: " + (($errors | ForEach-Object { $_.Message }) -join "; ")
    }

    $sampleDir = Join-Path $Root ".patch-staging\selftest"
    $samplePayload = Join-Path $sampleDir "sample.ps1"

    if (!$DryRun) {
        New-Item -ItemType Directory -Force -Path $sampleDir | Out-Null
        Set-Content -LiteralPath $samplePayload -Encoding UTF8 -Value "Write-Output 'sample patch payload'"
    }

    $result = & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -Root $Root -Action rollback -DryRun | ConvertFrom-Json
    if ($null -eq $result) {
        throw "Helper returned no JSON"
    }

    if ($result.state -ne "not_implemented") {
        throw "Unexpected rollback dry-run state: $($result.state)"
    }

    $result = New-TestResult -Ok $true -State "passed"
}
catch {
    $result = New-TestResult -Ok $false -State "failed" -ErrorMessage $_.Exception.Message
}

$result | ConvertTo-Json -Depth 20


