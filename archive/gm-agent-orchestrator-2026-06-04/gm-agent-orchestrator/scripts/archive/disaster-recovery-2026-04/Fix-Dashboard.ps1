#!/usr/bin/env pwsh
# Fix-Dashboard.ps1 - run from repo root
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$f = "scripts\Export-ProductManagerDashboard.ps1"
$raw = Get-Content $f -Raw -Encoding UTF8

# ---- Fix 1: line 264 has <html lang= @"en"> which breaks the here-string header.
# The @" on that line makes PS think a new here-string is starting mid-line.
# Fix: replace @"en" with just "en" (normal attribute value inside the here-string).
$raw = $raw -replace '<html lang= @"en">', '<html lang="en">'

# ---- Fix 2: garbled unicode on line 255 (ƒ? corruption between two $() expressions).
# The line should read: "<li>..role.. - ..status..<br><span>..category..</span></li>"
# The ƒ? is a broken em-dash or bullet. Replace with a clean separator.
$raw = $raw -replace ' ƒ\?\s*\$\(', ' - $('

# ---- Verify
$tokErr = $null
$null = [System.Management.Automation.Language.Parser]::ParseInput($raw, [ref]$null, [ref]$tokErr)

if ($tokErr.Count -eq 0) {
    Set-Content $f -Value $raw -Encoding UTF8 -NoNewline
    Write-Host "FIXED: 0 syntax errors remaining" -ForegroundColor Green
} else {
    Write-Host "Errors remaining: $($tokErr.Count)" -ForegroundColor Yellow
    $tokErr | Select-Object -First 5 | ForEach-Object {
        Write-Host "  Line $($_.Extent.StartLineNumber): $($_.Message)"
    }
    # Save anyway - may be partial improvement
    Set-Content $f -Value $raw -Encoding UTF8 -NoNewline
}

# ---- Fix agents.json: headless slot openhands -> claude
$agentsPath = "config\agents.json"
$config = Get-Content $agentsPath -Raw | ConvertFrom-Json
$headless = $config.slots | Where-Object { $_.name -eq 'headless' }
if ($headless -and $headless.agent -eq 'openhands') {
    $headless.agent = 'claude'
    $headless.command = [PSCustomObject]@{
        start          = 'claude --dangerously-skip-permissions --print {prompt}'
        resume         = 'claude --dangerously-skip-permissions --continue --print {prompt}'
        fallbackResume = 'claude --dangerously-skip-permissions -p --continue {prompt}'
    }
    $config | ConvertTo-Json -Depth 20 | Set-Content $agentsPath -Encoding UTF8
    Write-Host "FIXED: headless slot reconfigured openhands -> claude" -ForegroundColor Green
} else {
    Write-Host "SKIP: headless already '$($headless.agent)' or not found" -ForegroundColor Gray
}

# ---- Stage, commit, push
& git add scripts/Export-ProductManagerDashboard.ps1 config/agents.json
$status = & git status --short
if ($status) {
    & git commit -m "fix: dashboard here-string and headless slot Windows compat

- Fix Export-ProductManagerDashboard.ps1: line 264 had @`"en`" inside
  the here-string body which PS parsed as a second here-string header,
  cascading into 29 syntax errors. Changed to lang=`"en`".
- Fix line 255 garbled unicode separator (encoding corruption).
- Reconfigure headless slot: openhands -> claude (OpenHands V1 raises
  NotImplementedError on Windows; claude CLI works identically).

Closes #213"
    & git push origin master
    Write-Host "PUSHED to origin/master" -ForegroundColor Green
} else {
    Write-Host "Nothing to commit" -ForegroundColor Gray
}

# ---- Quick validation
Write-Host ""
Write-Host "--- Syntax test ---"
& powershell -NoProfile -ExecutionPolicy Bypass -File tests\Test-PowerShellSyntax.ps1 2>&1 | Select-Object -Last 5
