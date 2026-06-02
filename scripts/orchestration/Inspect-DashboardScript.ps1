#!/usr/bin/env pwsh
#Requires -Version 5.1
# Fix-DashboardSyntax.ps1 - surgical fix for Export-ProductManagerDashboard.ps1
# Run from repo root

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$f = Join-Path $PSScriptRoot "scripts\Export-ProductManagerDashboard.ps1"
$raw = Get-Content $f -Raw -Encoding UTF8
$lines = $raw -split "`r?\n"

# Show lines 248-280 so we can see the exact broken section
Write-Host "=== Lines 248-290 of Export-ProductManagerDashboard.ps1 ===" -ForegroundColor Cyan
for ($i = 247; $i -le [Math]::Min(289, $lines.Count - 1); $i++) {
    $prefix = if ($i -ge 253 -and $i -le 275) { ">>>" } else { "   " }
    Write-Host "$prefix $($i+1): $($lines[$i])"
}
Write-Host ""

# Also show the error list
Write-Host "=== PowerShell parse errors ===" -ForegroundColor Cyan
$tokErr = $null
$null = [System.Management.Automation.Language.Parser]::ParseInput($raw, [ref]$null, [ref]$tokErr)
$tokErr | Select-Object -First 15 | ForEach-Object {
    Write-Host "  Line $($_.Extent.StartLineNumber) col $($_.Extent.StartColumnNumber): $($_.Message)"
}
Write-Host ""
Write-Host "Total errors: $($tokErr.Count)"
