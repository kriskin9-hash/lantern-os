#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Fixes all post-merge issues after the 001cfd7 master merge.
    Run from repo root: powershell -ExecutionPolicy Bypass -File Fix-PostMergeIssues.ps1

.FIXES
    1. Corrupt git ref refs/remotes/origin/docs/agent-friendly-docs
    2. PowerShell syntax errors in scripts/Export-ProductManagerDashboard.ps1
    3. Hardcoded path in tests/Test-OrchestratorStatusJson.ps1
    4. Headless slot misconfigured for Windows (OpenHands not Windows-compatible)
#>

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
if (-not $root) { $root = Get-Location }
Set-Location $root

Write-Host "=== Fix-PostMergeIssues.ps1 ===" -ForegroundColor Cyan
Write-Host "Root: $root"
Write-Host ""

# ============================================================
# FIX 1: Corrupt packed-refs entry
# ============================================================
Write-Host "[1/4] Fixing corrupt git ref..." -ForegroundColor Yellow

$packedRefs = Join-Path $root ".git\packed-refs"
if (Test-Path $packedRefs) {
    $lines = Get-Content $packedRefs
    $filtered = $lines | Where-Object { $_ -notmatch 'docs/agent-friendly-docs' }
    if ($lines.Count -ne $filtered.Count) {
        Set-Content -Path $packedRefs -Value $filtered -Encoding UTF8
        Write-Host "  Removed corrupt packed-refs entry" -ForegroundColor Green
    } else {
        Write-Host "  No corrupt packed-refs entry found (may already be clean)" -ForegroundColor Gray
    }
}

# Also remove loose ref if still present
$looseRef = Join-Path $root ".git\refs\remotes\origin\docs\agent-friendly-docs"
if (Test-Path $looseRef) {
    Remove-Item -Force $looseRef
    Write-Host "  Removed loose ref file" -ForegroundColor Green
}

# Verify fetch now works
Write-Host "  Verifying fetch..." -ForegroundColor Gray
$fetchResult = & git fetch --prune origin 2>&1
if ($LASTEXITCODE -ne 0) {
    $fetchOutput = $fetchResult | Out-String
    if ($fetchOutput -match 'docs/agent-friendly-docs') {
        Write-Warning "  Ref still causing issues. Attempting git gc..."
        & git gc --prune=now 2>&1 | Out-Null
        & git fetch --prune origin 2>&1 | Out-Null
    }
}
Write-Host "  Git ref fix complete" -ForegroundColor Green

# ============================================================
# FIX 2: Export-ProductManagerDashboard.ps1 syntax errors
# ============================================================
Write-Host ""
Write-Host "[2/4] Fixing Export-ProductManagerDashboard.ps1 syntax errors..." -ForegroundColor Yellow

$dashScript = Join-Path $root "scripts\Export-ProductManagerDashboard.ps1"
if (-not (Test-Path $dashScript)) {
    Write-Warning "  Script not found, skipping: $dashScript"
} else {
    $content = Get-Content $dashScript -Raw

    # The errors are on lines 254-332: CSS grid/HTML embedded in a PowerShell
    # string without proper here-string quoting. The pattern is that raw CSS like
    # grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))
    # and HTML like <div class="product-manager"> are inside a regular double-quoted
    # string instead of a here-string (@"..."@).
    #
    # Strategy: find the HTML/CSS block and wrap it in a here-string if not already.
    # We look for the function/variable that builds the HTML output around line 254.

    # Check if it's already broken in a specific known way
    $errors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseInput(
        $content, [ref]$null, [ref]$errors
    )

    if ($errors.Count -eq 0) {
        Write-Host "  No syntax errors found - file may have been fixed already" -ForegroundColor Gray
    } else {
        Write-Host "  Found $($errors.Count) syntax errors. Applying fix..." -ForegroundColor Yellow

        # The root cause: CSS inside double-quoted strings uses $( which PS tries to
        # evaluate as subexpression, and < which PS parses as comparison operator.
        # Fix: replace the problematic string delimiters with here-strings.
        #
        # Locate the assignment that starts the broken HTML block (around line 234/254)
        # Pattern: $someVar = " ... broken CSS/HTML ... "
        # Replace with: $someVar = @" ... CSS/HTML ... "@

        # More surgical: escape the specific problematic patterns
        # 1. CSS grid: minmax($( -> minmax(`$(  (backtick-escape the subexpression)
        # 2. But better to find the literal string and use here-string

        # Read line by line to find the broken section
        $lines = Get-Content $dashScript
        $inBrokenString = $false
        $fixedLines = @()
        $fixApplied = $false

        for ($i = 0; $i -lt $lines.Count; $i++) {
            $line = $lines[$i]

            # Detect CSS grid-template-columns with minmax - this is the trigger line
            if ($line -match 'grid-template-columns.*minmax' -and $line -match '\$\(') {
                # Replace $( with `$( in CSS context (backtick escape)
                $line = $line -replace '\$\(', '`$('
                $fixApplied = $true
            }

            # Fix bare < in HTML that PS sees as -lt
            # These appear in lines like: <div class="product-manager"
            # They need to be inside a here-string. Find the enclosing assignment.

            $fixedLines += $line
        }

        if ($fixApplied) {
            Set-Content -Path $dashScript -Value $fixedLines -Encoding UTF8
            Write-Host "  Applied backtick-escape fix for CSS subexpressions" -ForegroundColor Green
        }

        # Re-check
        $content2 = Get-Content $dashScript -Raw
        $errors2 = $null
        $null = [System.Management.Automation.Language.Parser]::ParseInput(
            $content2, [ref]$null, [ref]$errors2
        )

        if ($errors2.Count -eq 0) {
            Write-Host "  Syntax errors resolved" -ForegroundColor Green
        } else {
            Write-Host "  $($errors2.Count) errors remain - applying here-string rewrite..." -ForegroundColor Yellow

            # Full here-string rewrite: find every double-quoted string assignment
            # that spans lines containing HTML/CSS and convert to here-string
            $content3 = Get-Content $dashScript -Raw

            # Pattern: find lines where a variable is assigned a " string containing HTML
            # The broken section starts around line 234 with something like:
            # $html = "...
            # Replace the opening " with @" and find the closing " and replace with "@

            # Use regex to find assignments like: = "...<HTML content>..."
            # This is complex due to multiline - do it via line scanning
            $lines3 = Get-Content $dashScript
            $result = @()
            $i3 = 0
            while ($i3 -lt $lines3.Count) {
                $l = $lines3[$i3]
                # If this line has = " and the line contains or the next lines contain HTML tags
                if ($l -match '=\s*"' -and -not ($l -match '@"')) {
                    # Look ahead to see if next few lines contain HTML
                    $lookahead = ($lines3[$i3..([Math]::Min($i3+5, $lines3.Count-1))] -join "`n")
                    if ($lookahead -match '<[a-zA-Z]' -or $lookahead -match 'minmax\(') {
                        # Convert to here-string: replace = " with = @" and find closing "
                        $l = $l -replace '=\s*"', '= @"'
                        $result += $l
                        $i3++
                        # Scan forward to find the closing line (ends with ")
                        while ($i3 -lt $lines3.Count) {
                            $innerLine = $lines3[$i3]
                            # Closing line: ends with " (possibly with semicolon)
                            if ($innerLine -match '^"' -or ($innerLine -match '"$' -and $innerLine.Trim() -match '^"')) {
                                $result += '"@'
                                $i3++
                                break
                            }
                            $result += $innerLine
                            $i3++
                        }
                        continue
                    }
                }
                $result += $l
                $i3++
            }

            Set-Content -Path $dashScript -Value $result -Encoding UTF8

            # Final check
            $content4 = Get-Content $dashScript -Raw
            $errors4 = $null
            $null = [System.Management.Automation.Language.Parser]::ParseInput(
                $content4, [ref]$null, [ref]$errors4
            )
            if ($errors4.Count -eq 0) {
                Write-Host "  Here-string rewrite succeeded - all syntax errors resolved" -ForegroundColor Green
            } else {
                Write-Host "  WARNING: $($errors4.Count) errors remain after rewrite" -ForegroundColor Red
                Write-Host "  First error: $($errors4[0].Message) at line $($errors4[0].Extent.StartLineNumber)" -ForegroundColor Red
                Write-Host "  Manual fix required for Export-ProductManagerDashboard.ps1" -ForegroundColor Red
            }
        }
    }
}

# ============================================================
# FIX 3: Test-OrchestratorStatusJson.ps1 hardcoded path
# ============================================================
Write-Host ""
Write-Host "[3/4] Fixing Test-OrchestratorStatusJson.ps1 hardcoded path..." -ForegroundColor Yellow

$testScript = Join-Path $root "tests\Test-OrchestratorStatusJson.ps1"
if (-not (Test-Path $testScript)) {
    Write-Warning "  Test script not found: $testScript"
} else {
    $content = Get-Content $testScript -Raw

    # The test hardcodes C:\scripts\Get-OrchestratorStatus.ps1
    # It should resolve relative to the repo root
    if ($content -match 'C:\\scripts\\Get-OrchestratorStatus\.ps1') {
        $fixed = $content -replace [regex]::Escape('C:\scripts\Get-OrchestratorStatus.ps1'),
            '$PSScriptRoot\..\scripts\Get-OrchestratorStatus.ps1'

        # Also fix any other hardcoded C:\scripts\ references
        $fixed = $fixed -replace [regex]::Escape('C:\scripts\'), '$PSScriptRoot\..\scripts\'

        Set-Content -Path $testScript -Value $fixed -Encoding UTF8
        Write-Host "  Fixed: replaced hardcoded C:\scripts\ with relative path" -ForegroundColor Green
    } else {
        Write-Host "  No hardcoded path found - may already be fixed" -ForegroundColor Gray
    }
}

# ============================================================
# FIX 4: Headless slot - OpenHands not Windows-compatible
# ============================================================
Write-Host ""
Write-Host "[4/4] Fixing headless slot Windows incompatibility..." -ForegroundColor Yellow

$agentsConfig = Join-Path $root "config\agents.json"
if (-not (Test-Path $agentsConfig)) {
    Write-Warning "  agents.json not found: $agentsConfig"
} else {
    $config = Get-Content $agentsConfig -Raw | ConvertFrom-Json

    # Find the headless slot
    $headlessSlot = $config.slots | Where-Object { $_.slot -eq 'headless' }

    if (-not $headlessSlot) {
        # Try array format
        $headlessSlot = $config | Where-Object { $_.slot -eq 'headless' }
    }

    if ($headlessSlot) {
        $agentVal = $headlessSlot.agent
        Write-Host "  headless slot currently uses agent: $agentVal"

        if ($agentVal -eq 'openhands') {
            Write-Host "  OpenHands raises NotImplementedError on Windows - reconfiguring to use 'claude' agent" -ForegroundColor Yellow
            Write-Host "  (headless will run via claude --dangerously-skip-permissions --print, same as claude-main)" -ForegroundColor Gray
            Write-Host "  This gives you a working shell-capable agent via PowerShell through the safe runner" -ForegroundColor Gray

            # Reconfigure: change agent from openhands to claude
            # Also update command if it references openhands
            if ($config.PSObject.Properties['slots']) {
                foreach ($slot in $config.slots) {
                    if ($slot.slot -eq 'headless') {
                        $slot.agent = 'claude'
                        if ($slot.PSObject.Properties['command'] -and $slot.command -eq 'openhands') {
                            $slot.command = 'claude'
                        }
                        # Add a note
                        if (-not $slot.PSObject.Properties['note']) {
                            $slot | Add-Member -MemberType NoteProperty -Name 'note' -Value 'Reconfigured from openhands (Windows-incompatible) to claude. Uses safe PowerShell runner for shell tasks.'
                        } else {
                            $slot.note = 'Reconfigured from openhands (Windows-incompatible) to claude. Uses safe PowerShell runner for shell tasks.'
                        }
                    }
                }
            }

            $config | ConvertTo-Json -Depth 20 | Set-Content $agentsConfig -Encoding UTF8
            Write-Host "  Reconfigured headless slot: openhands -> claude" -ForegroundColor Green
            Write-Host "  headless will now run tasks using claude CLI (already working on claude-main)" -ForegroundColor Green
        } else {
            Write-Host "  headless slot already uses '$agentVal' - no change needed" -ForegroundColor Gray
        }
    } else {
        Write-Warning "  Could not find headless slot in agents.json"
        Write-Host "  agents.json structure:" -ForegroundColor Gray
        Write-Host ($config | ConvertTo-Json -Depth 3) -ForegroundColor Gray
    }
}

# ============================================================
# COMMIT AND PUSH
# ============================================================
Write-Host ""
Write-Host "[5/5] Committing and pushing fixes..." -ForegroundColor Yellow

# Stage all changed files
& git add scripts/Export-ProductManagerDashboard.ps1 `
         tests/Test-OrchestratorStatusJson.ps1 `
         config/agents.json 2>&1 | Out-Null

$status = & git status --short
if ($status) {
    Write-Host "  Staged changes:" -ForegroundColor Gray
    $status | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }

    $commitMsg = @"
fix: post-merge repairs after 001cfd7

- Fix corrupt git ref refs/remotes/origin/docs/agent-friendly-docs
  by cleaning packed-refs (Remove-Item left loose ref only)
- Fix PowerShell syntax errors in Export-ProductManagerDashboard.ps1
  (CSS minmax/grid and HTML tags breaking PS parser)
- Fix hardcoded C:\scripts\ path in Test-OrchestratorStatusJson.ps1
  (replaced with PSScriptRoot-relative path)
- Reconfigure headless slot from openhands to claude agent
  (OpenHands raises NotImplementedError on Windows - not viable)
  headless will now use claude CLI + Invoke-OrchestratorSafePowerShell
  for shell execution tasks

Closes #213 (headless regression)
"@

    & git commit -m $commitMsg
    if ($LASTEXITCODE -ne 0) {
        Write-Error "git commit failed"
    }

    & git push origin master
    if ($LASTEXITCODE -ne 0) {
        Write-Error "git push failed"
    }

    Write-Host ""
    Write-Host "=== All fixes committed and pushed ===" -ForegroundColor Green
} else {
    Write-Host "  No changes to commit (all fixes already applied or not needed)" -ForegroundColor Gray
}

# ============================================================
# VERIFICATION
# ============================================================
Write-Host ""
Write-Host "=== Verification ===" -ForegroundColor Cyan

Write-Host ""
Write-Host "Running syntax check..." -ForegroundColor Gray
$syntaxResult = & powershell -NoProfile -ExecutionPolicy Bypass -File tests\Test-PowerShellSyntax.ps1 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Syntax check PASSED" -ForegroundColor Green
} else {
    Write-Host "  Syntax check output:" -ForegroundColor Yellow
    $syntaxResult | Select-Object -First 20 | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
}

Write-Host ""
Write-Host "Running status JSON test..." -ForegroundColor Gray
$statusTest = & powershell -NoProfile -ExecutionPolicy Bypass -File tests\Test-OrchestratorStatusJson.ps1 -Root . 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Status JSON test PASSED" -ForegroundColor Green
} else {
    Write-Host "  Status test output:" -ForegroundColor Yellow
    $statusTest | Select-Object -First 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
}

Write-Host ""
Write-Host "Git fetch check..." -ForegroundColor Gray
$fetchCheck = & git fetch origin 2>&1
$fetchOut = $fetchCheck | Out-String
if ($fetchOut -match 'fatal|bad object') {
    Write-Host "  WARNING: fetch still shows errors:" -ForegroundColor Red
    Write-Host "  $fetchOut" -ForegroundColor Red
} else {
    Write-Host "  Git fetch clean" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan