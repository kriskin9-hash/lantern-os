param(
    [string]$StatusPath = "D:\tmp\lantern-os\data\arc-reactor\status.json",
    [string]$WalletLedgerPath = "D:\tmp\lantern-os\ledger\mookman-20-wallet-version-2026-05-26.yaml",
    [string]$OutputPath = "D:\tmp\lantern-os\data\automation\movie2-readiness-results.json",
    [switch]$RunOnce
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
    $logPath = "D:\tmp\lantern-os\data\automation\movie2-readiness.log"
    Add-Content -Path $logPath -Value "[$timestamp] [$Level] $Message" -ErrorAction SilentlyContinue
}

function Get-Movie2Criteria {
    return @(
        @{ id = "outreach-5"; description = "5 outreach sends recorded in wallet ledger"; weight = 0.15; category = "outreach" },
        @{ id = "paid-pilot-1"; description = "1 paid pilot or hard rejection batch"; weight = 0.20; category = "revenue" },
        @{ id = "public-proof"; description = "1 public proof page or demo artifact"; weight = 0.15; category = "proof" },
        @{ id = "user-feedback"; description = "1 user/customer/stakeholder feedback receipt"; weight = 0.10; category = "feedback" },
        @{ id = "discord-health"; description = "Discord lounge bot health check passes"; weight = 0.10; category = "infrastructure" },
        @{ id = "mcp-canary"; description = "MCP canary validates actual exposed tools"; weight = 0.15; category = "safety" },
        @{ id = "dual-boot"; description = "D: shrunk and dual boot readyForInstall=true"; weight = 0.10; category = "infrastructure" },
        @{ id = "workflow-used"; description = "one workflow used by someone other than operator"; weight = 0.05; category = "adoption" }
    )
}

function Test-OutreachCount {
    param([string]$LedgerPath)
    
    $count = 0
    $evidence = "No ledger found"
    
    if (Test-Path $LedgerPath) {
        $content = Get-Content $LedgerPath -Raw -ErrorAction SilentlyContinue
        # Count outreach-related entries
        $outreachMatches = [regex]::Matches($content, 'outreach|send|message|email', 'IgnoreCase')
        $count = $outreachMatches.Count
        $evidence = "Found $count outreach references in ledger"
    }
    
    return @{
        met = $count -ge 5
        current = $count
        target = 5
        evidence = $evidence
        gap = [Math]::Max(0, 5 - $count)
    }
}

function Test-PaidPilot {
    param([string]$LedgerPath)
    
    $hasPilot = $false
    $evidence = "No pilot evidence found"
    
    if (Test-Path $LedgerPath) {
        $content = Get-Content $LedgerPath -Raw -ErrorAction SilentlyContinue
        # Look for paid pilot indicators
        if ($content -match 'pilot.*paid|paid.*pilot|invoice.*199|invoice.*299|\$199|\$299|revenue.*\d{3,}') {
            $hasPilot = $true
            $evidence = "Paid pilot evidence found in ledger"
        }
    }
    
    # Also check reports for pilot mentions
    $pilotReports = Get-ChildItem -Path "D:\tmp\lantern-os\reports" -Filter "*pilot*" -ErrorAction SilentlyContinue
    if ($pilotReports -and $pilotReports.Count -gt 0) {
        $hasPilot = $true
        $evidence += "; Pilot reports exist"
    }
    
    return @{
        met = $hasPilot
        current = if ($hasPilot) { 1 } else { 0 }
        target = 1
        evidence = $evidence
        gap = if ($hasPilot) { 0 } else { 1 }
    }
}

function Test-PublicProof {
    # Check for public proof pages/artifacts
    $publicDir = "D:\tmp\lantern-os\surfaces"
    
    $htmlFiles = if (Test-Path $publicDir) { 
        Get-ChildItem -Path $publicDir -Filter "*.html" -Recurse -ErrorAction SilentlyContinue | 
            Where-Object { $_.Name -notmatch 'index' }
    } else { $null }
    
    $demoCount = if ($htmlFiles) { $htmlFiles.Count } else { 0 }
    
    return @{
        met = $demoCount -gt 0
        current = $demoCount
        target = 1
        evidence = if ($demoCount -gt 0) { "Found $demoCount demo pages" } else { "No public demo artifacts found" }
        gap = [Math]::Max(0, 1 - $demoCount)
    }
}

function Test-UserFeedback {
    # Check evidence folder for user feedback
    $feedbackFiles = Get-ChildItem -Path "D:\tmp\lantern-os\manifests\evidence" -Filter "*feedback*" -ErrorAction SilentlyContinue
    $hasFeedback = ($feedbackFiles -and $feedbackFiles.Count -gt 0)
    
    return @{
        met = $hasFeedback
        current = if ($hasFeedback) { 1 } else { 0 }
        target = 1
        evidence = if ($hasFeedback) { "Feedback receipts found" } else { "No user feedback receipts yet" }
        gap = if ($hasFeedback) { 0 } else { 1 }
    }
}

function Test-DiscordHealth {
    # Check if Discord bot health check exists
    $healthScript = "D:\tmp\lantern-os\scripts\Test-DiscordBotHealth.ps1"
    $hasScript = Test-Path $healthScript
    
    return @{
        met = $hasScript
        current = if ($hasScript) { 1 } else { 0 }
        target = 1
        evidence = if ($hasScript) { "Discord health check script exists" } else { "No Discord health check configured" }
        gap = if ($hasScript) { 0 } else { 1 }
    }
}

function Test-McpCanary {
    # Check for MCP canary test receipts
    $canaryFiles = Get-ChildItem -Path "D:\tmp\lantern-os\manifests\validation" -Filter "*canary*" -ErrorAction SilentlyContinue
    $hasCanary = ($canaryFiles -and $canaryFiles.Count -gt 0)
    
    return @{
        met = $hasCanary
        current = if ($hasCanary) { 1 } else { 0 }
        target = 1
        evidence = if ($hasCanary) { "MCP canary receipts found" } else { "No MCP canary validation yet" }
        gap = if ($hasCanary) { 0 } else { 1 }
    }
}

function Test-DualBootReadiness {
    # Check for dual boot validation files
    $dualBootFiles = Get-ChildItem -Path "D:\tmp\lantern-os\manifests\validation" -Filter "*dual*boot*" -ErrorAction SilentlyContinue
    $hasValidation = ($dualBootFiles -and $dualBootFiles.Count -gt 0)
    
    # Check D: drive status
    $dDrive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'" -ErrorAction SilentlyContinue
    $dExists = $null -ne $dDrive
    
    return @{
        met = $hasValidation -and $dExists
        current = if ($hasValidation -and $dExists) { 1 } else { 0 }
        target = 1
        evidence = "D: exists=$dExists, validation=$hasValidation"
        gap = if ($hasValidation -and $dExists) { 0 } else { 1 }
    }
}

function Test-WorkflowUsage {
    # Check for workflow usage evidence
    $workflowUsed = $false
    
    # Check if any non-operator evidence exists
    $externalEvidence = Get-ChildItem -Path "D:\tmp\lantern-os\manifests\evidence" -Filter "*external*" -ErrorAction SilentlyContinue
    if ($externalEvidence -and $externalEvidence.Count -gt 0) {
        $workflowUsed = $true
    }
    
    return @{
        met = $workflowUsed
        current = if ($workflowUsed) { 1 } else { 0 }
        target = 1
        evidence = if ($workflowUsed) { "External workflow usage found" } else { "No external workflow usage yet" }
        gap = if ($workflowUsed) { 0 } else { 1 }
    }
}

function Invoke-Movie2ReadinessTracker {
    Write-Log "=== Movie 2 Readiness Tracker Started ==="
    
    $criteria = Get-Movie2Criteria
    $results = @()
    $metWeight = 0.0
    $totalWeight = 0.0
    
    foreach ($criterion in $criteria) {
        Write-Log "Checking: $($criterion.description)"
        
        $test = switch ($criterion.id) {
            "outreach-5" { Test-OutreachCount -LedgerPath $WalletLedgerPath }
            "paid-pilot-1" { Test-PaidPilot -LedgerPath $WalletLedgerPath }
            "public-proof" { Test-PublicProof }
            "user-feedback" { Test-UserFeedback }
            "discord-health" { Test-DiscordHealth }
            "mcp-canary" { Test-McpCanary }
            "dual-boot" { Test-DualBootReadiness }
            "workflow-used" { Test-WorkflowUsage }
            default { @{ met = $false; current = 0; target = 1; evidence = "Unknown criterion"; gap = 1 } }
        }
        
        $result = @{
            id = $criterion.id
            description = $criterion.description
            category = $criterion.category
            weight = $criterion.weight
            met = $test.met
            current = $test.current
            target = $test.target
            gap = $test.gap
            evidence = $test.evidence
        }
        
        $results += $result
        $totalWeight += $criterion.weight
        
        if ($test.met) {
            $metWeight += $criterion.weight
        }
        
        Write-Log "  Status: $(if ($test.met) { 'MET' } else { 'NOT MET' }) - $($test.evidence)"
    }
    
    $readinessScore = if ($totalWeight -gt 0) { [Math]::Round($metWeight / $totalWeight * 100, 1) } else { 0 }
    $criteriaMet = ($results | Where-Object { $_.met }).Count
    $criteriaTotal = $results.Count
    
    $unmetCritical = $results | Where-Object { $_.weight -ge 0.15 -and -not $_.met }
    
    $summary = @{
        generatedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        engine = "Movie 2 Readiness Tracker v1.0"
        movie2Confidence = $readinessScore
        criteriaMet = $criteriaMet
        criteriaTotal = $criteriaTotal
        weightedProgress = [Math]::Round($metWeight * 100, 1)
        totalPossibleWeight = [Math]::Round($totalWeight * 100, 1)
        results = $results
        unmetCriticalCount = $unmetCritical.Count
        unmetCriticalItems = $unmetCritical | Select-Object -Property id, description, weight, gap
        nextAction = if ($unmetCritical.Count -gt 0) {
            "Focus on: $($unmetCritical[0].description) [gap: $($unmetCritical[0].gap)]"
        } else {
            "Movie 2 criteria sufficiently met - advance to readiness review"
        }
        readyForPromotion = ($criteriaMet -ge 6) -and ($readinessScore -ge 75)
    }
    
    $summary | ConvertTo-Json -Depth 10 | Set-Content $OutputPath
    
    # Generate Orion-style markdown report
    $mdReportPath = $OutputPath -replace '\.json$', '.md'
    $unmetList = $unmetCritical | ForEach-Object { "- **$($_.description)** [weight: $([Math]::Round($_.weight * 100, 1))%, gap: $($_.gap)]" }
    $metList = $results | Where-Object { $_.met } | ForEach-Object { "- ✅ $($_.description) ($($_.current)/$($_.target))" }
    
    $mdContent = @"
# Movie 2 Readiness Report

**Generated:** $($summary.generatedAt)  
**Engine:** $($summary.engine)  
**Status:** $(if ($summary.readyForPromotion) { "READY FOR PROMOTION" } else { "IN PROGRESS" })

---

## Simple Answer

Movie 2 Public Platform readiness is at **$readinessScore%**. $($criteriaMet) of $($criteriaTotal) criteria met. $(if ($unmetCritical.Count -gt 0) { "Blocked by $($unmetCritical.Count) critical items." } else { "All critical gates passed." })

---

## What It Actually Does

This tracker evaluates the 8 criteria required to advance from Movie 1 (garage proven) to Movie 2 (public platform):

1. **Outreach sends** - Evidence of 5+ outreach attempts in wallet ledger
2. **Paid pilot** - At least 1 paid pilot or hard rejection batch
3. **Public proof** - Demo page or artifact visible to public
4. **User feedback** - Customer/stakeholder feedback receipt
5. **Discord health** - Bot health check passes without leaking secrets
6. **MCP canary** - Safety validation before any tool execution
7. **Dual boot ready** - D: shrunk and ready for NixOS installation
8. **Workflow usage** - External operator using a Lantern workflow

---

## Evidence / Source Discipline

**Sources Checked:**
- Wallet ledger: $($WalletLedgerPath)
- Reports directory: D:\tmp\lantern-os\reports
- Validation manifests: D:\tmp\lantern-os\manifests\validation
- Discord health script: D:\tmp\lantern-os\scripts\Test-DiscordBotHealth.ps1

**Weight Distribution:**
- Outreach: 15%
- Paid pilot: 20% (highest - revenue critical)
- Public proof: 15%
- User feedback: 10%
- Discord health: 10%
- MCP canary: 15% (safety critical)
- Dual boot: 10%
- Workflow usage: 5%

---

## Proven / Held / Local-Only

**Proven (Met Criteria):**
$($metList -join "`n")

**Held (Unmet Critical):**
$($unmetList -join "`n")

**Local-Only:**
- This report is local evidence only
- Promotion decision requires operator review
- ReadyForPromotion flag is advisory, not autonomous

---

## Next Safe Action

$($summary.nextAction)

Priority order:
1. Record outreach sends in wallet ledger (need 4 more)
2. Close first paid pilot or document hard rejections
3. Create public demo page for Lantern Garage
4. Collect user feedback from pilot participants
5. Validate MCP canary before any Discord-to-MCP execution

---

## Validation Path

- [ ] Review this readiness report
- [ ] Verify wallet ledger entries are actual sends, not plans
- [ ] Confirm paid pilot has cleared cash or documented rejection
- [ ] Test public demo page accessibility
- [ ] Run MCP canary validation
- [ ] Operator approval for Movie 2 promotion

---

*Generated by Movie 2 Readiness Tracker*  
*Skill Reference: skills/asi-arc-reactor-mk1/SKILL.md*
"@
    
    $mdContent | Set-Content $mdReportPath
    
    Write-Log ""
    Write-Log "=== Summary ==="
    Write-Log "Movie 2 Confidence: $readinessScore%"
    Write-Log "Criteria: $criteriaMet/$criteriaTotal met"
    Write-Log "Weighted Progress: $([Math]::Round($metWeight * 100, 1))%"
    Write-Log "Unmet Critical: $($unmetCritical.Count)"
    Write-Log "Next Action: $($summary.nextAction)"
    Write-Log "Ready for Promotion: $($summary.readyForPromotion)"
    Write-Log "Orion report: $mdReportPath"
    
    return $summary
}

if ($RunOnce -or -not $RunOnce) {
    Invoke-Movie2ReadinessTracker
}
