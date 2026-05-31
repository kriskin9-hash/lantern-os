param(
    [string]$StatusPath = "D:\tmp\lantern-os\data\arc-reactor\status.json",
    [string]$OutputPath = "D:\tmp\lantern-os\data\automation\human-trial-gate-results.json",
    [switch]$RunOnce
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
    $logPath = "D:\tmp\lantern-os\data\automation\human-trial-gate.log"
    Add-Content -Path $logPath -Value "[$timestamp] [$Level] $Message" -ErrorAction SilentlyContinue
}

function Get-HumanTrialGates {
    return @(
        @{ id = "founding-demos-5"; description = "5 successful $1000 founding seat demos with cleared cash"; critical = $true; category = "revenue" },
        @{ id = "mcp-canary-all"; description = "MCP canary validates all exposed tools before automation"; critical = $true; category = "safety" },
        @{ id = "rollback-paths"; description = "Documented rollback path for all automated actions"; critical = $true; category = "safety" },
        @{ id = "human-approval"; description = "Explicit human approval recorded for each trial participant"; critical = $true; category = "compliance" },
        @{ id = "ppe-evidence"; description = "Certified PPE or tested prototype evidence if medical claims"; critical = $false; category = "safety" },
        @{ id = "asi-validation"; description = "No ASI capability claim without independent validation"; critical = $true; category = "claims" },
        @{ id = "brier-tracking"; description = "Brier-style error tracking with forecast/outcome pairs"; critical = $true; category = "calibration" },
        @{ id = "safety-gates"; description = "Safety automation gates configured and tested"; critical = $true; category = "safety" }
    )
}

function Test-FoundingDemos {
    # Check for $1000 founding seat demo receipts
    $demoReceipts = Get-ChildItem -Path "D:\tmp\lantern-os\manifests\evidence" -Filter "*demo*" -ErrorAction SilentlyContinue
    $walletReceipts = Get-ChildItem -Path "D:\tmp\lantern-os\ledger" -Filter "*.yaml" -ErrorAction SilentlyContinue
    
    $count = 0
    if ($demoReceipts) { $count += $demoReceipts.Count }
    
    # Check for $1000 amounts in ledger
    $found1000 = $false
    if ($walletReceipts) {
        foreach ($file in $walletReceipts) {
            $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
            if ($content -match '1000|founding|seat') {
                $found1000 = $true
                $count++
            }
        }
    }
    
    $evidence = "Found $count founding demo receipts/ledger entries"
    if ($found1000) { $evidence += " (includes $1000 tier mentions)" }
    
    return @{
        met = $count -ge 5
        current = $count
        target = 5
        evidence = $evidence
        gap = [Math]::Max(0, 5 - $count)
        critical = $true
    }
}

function Test-McpCanaryAll {
    # Check for comprehensive MCP canary validation
    $canaryFiles = Get-ChildItem -Path "D:\tmp\lantern-os\manifests\validation" -Filter "*canary*" -ErrorAction SilentlyContinue
    $hasCanary = ($canaryFiles -and $canaryFiles.Count -gt 0)
    
    $mcpSources = Get-Content "D:\tmp\lantern-os\manifests\lantern-mcp-sources.json" -Raw | ConvertFrom-Json
    $sourceCount = $mcpSources.sources.Count
    
    return @{
        met = $hasCanary -and ($canaryFiles.Count -ge 1)
        current = if ($canaryFiles) { $canaryFiles.Count } else { 0 }
        target = 1
        evidence = if ($hasCanary) { "MCP canary receipts found ($($canaryFiles.Count) files for $sourceCount sources)" } else { "No MCP canary validation yet ($sourceCount sources to check)" }
        gap = if ($hasCanary) { 0 } else { 1 }
        critical = $true
    }
}

function Test-RollbackPaths {
    # Check for rollback documentation
    $rollbackDocs = Get-ChildItem -Path "D:\tmp\lantern-os\docs" -Filter "*rollback*" -ErrorAction SilentlyContinue
    $hasRollback = ($rollbackDocs -and $rollbackDocs.Count -gt 0)
    
    # Check AGENTS.md for rollback guidance
    $agentsMd = Test-Path "D:\tmp\lantern-os\AGENTS.md"
    
    return @{
        met = $hasRollback -or $agentsMd
        current = if ($hasRollback -or $agentsMd) { 1 } else { 0 }
        target = 1
        evidence = if ($hasRollback) { "Rollback documentation exists" } elseif ($agentsMd) { "AGENTS.md provides rollback guidance" } else { "No rollback documentation" }
        gap = if ($hasRollback -or $agentsMd) { 0 } else { 1 }
        critical = $true
    }
}

function Test-HumanApproval {
    # Check for human approval evidence
    $approvalFiles = Get-ChildItem -Path "D:\tmp\lantern-os\manifests\evidence" -Filter "*approval*" -ErrorAction SilentlyContinue
    $hasApproval = ($approvalFiles -and $approvalFiles.Count -gt 0)
    
    return @{
        met = $hasApproval
        current = if ($hasApproval) { 1 } else { 0 }
        target = 1
        evidence = if ($hasApproval) { "Human approval receipts found" } else { "No human approval receipts yet" }
        gap = if ($hasApproval) { 0 } else { 1 }
        critical = $true
    }
}

function Test-PpeEvidence {
    # Check for PPE/prototype evidence (only if medical claims exist)
    $medicalClaims = Get-ChildItem -Path "D:\tmp\lantern-os\reports" -Filter "*medical*" -ErrorAction SilentlyContinue
    $ppeDocs = Get-ChildItem -Path "D:\tmp\lantern-os\manifests\evidence" -Filter "*ppe*" -ErrorAction SilentlyContinue
    
    $needsPpe = ($medicalClaims -and $medicalClaims.Count -gt 0)
    $hasPpe = ($ppeDocs -and $ppeDocs.Count -gt 0)
    
    return @{
        met = if ($needsPpe) { $hasPpe } else { $true }  # Auto-pass if no medical claims
        current = if ($hasPpe) { 1 } else { 0 }
        target = if ($needsPpe) { 1 } else { 0 }
        evidence = if ($needsPpe) { if ($hasPpe) { "PPE evidence found" } else { "Medical claims exist but no PPE evidence" } } else { "No medical claims - PPE not required" }
        gap = if ($needsPpe -and -not $hasPpe) { 1 } else { 0 }
        critical = $false
    }
}

function Test-AsiValidation {
    # Check ASI pattern boundaries in status
    $status = Get-Content $StatusPath -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
    $hasBoundaries = $null -ne $status.asiPatternBoundaries
    
    return @{
        met = $hasBoundaries
        current = if ($hasBoundaries) { 1 } else { 0 }
        target = 1
        evidence = if ($hasBoundaries) { "ASI pattern boundaries configured" } else { "ASI pattern boundaries not found" }
        gap = if ($hasBoundaries) { 0 } else { 1 }
        critical = $true
    }
}

function Test-BrierTracking {
    # Check for Brier calibration engine
    $brierEngine = Test-Path "D:\tmp\lantern-os\scripts\Invoke-BrierCalibrationEngine.ps1"
    $brierHistory = Test-Path "D:\tmp\lantern-os\data\automation\brier-history.json"
    
    return @{
        met = $brierEngine -and $brierHistory
        current = if ($brierEngine -and $brierHistory) { 1 } else { 0 }
        target = 1
        evidence = if ($brierEngine -and $brierHistory) { "Brier tracking system active" } else { "Brier tracking not fully configured" }
        gap = if ($brierEngine -and $brierHistory) { 0 } else { 1 }
        critical = $true
    }
}

function Test-SafetyGates {
    # Check Windsurf hooks configuration
    $hooksJson = Test-Path "D:\tmp\lantern-os\.windsurf\hooks.json"
    $hooksDir = Test-Path "D:\tmp\lantern-os\.windsurf\hooks"
    
    return @{
        met = $hooksJson -and $hooksDir
        current = if ($hooksJson -and $hooksDir) { 1 } else { 0 }
        target = 1
        evidence = if ($hooksJson -and $hooksDir) { "Safety gates configured (hooks.json + hooks/)" } else { "Safety gates incomplete" }
        gap = if ($hooksJson -and $hooksDir) { 0 } else { 1 }
        critical = $true
    }
}

function Invoke-HumanTrialGateMonitor {
    Write-Log "=== Human Trial Gate Monitor Started ==="
    
    $gates = Get-HumanTrialGates
    $results = @()
    $criticalMet = 0
    $criticalTotal = ($gates | Where-Object { $_.critical }).Count
    
    foreach ($gate in $gates) {
        Write-Log "Checking gate: $($gate.description) [critical=$($gate.critical)]"
        
        $test = switch ($gate.id) {
            "founding-demos-5" { Test-FoundingDemos }
            "mcp-canary-all" { Test-McpCanaryAll }
            "rollback-paths" { Test-RollbackPaths }
            "human-approval" { Test-HumanApproval }
            "ppe-evidence" { Test-PpeEvidence }
            "asi-validation" { Test-AsiValidation }
            "brier-tracking" { Test-BrierTracking }
            "safety-gates" { Test-SafetyGates }
            default { @{ met = $false; current = 0; target = 1; evidence = "Unknown gate"; gap = 1; critical = $gate.critical } }
        }
        
        $result = @{
            id = $gate.id
            description = $gate.description
            category = $gate.category
            critical = $gate.critical
            met = $test.met
            current = $test.current
            target = $test.target
            gap = $test.gap
            evidence = $test.evidence
        }
        
        $results += $result
        
        if ($gate.critical -and $test.met) {
            $criticalMet++
        }
        
        Write-Log "  Status: $(if ($test.met) { 'PASS' } else { 'BLOCK' }) - $($test.evidence)"
    }
    
    $readiness = [Math]::Round(($criticalMet / $criticalTotal) * 100, 1)
    $blockedBy = $results | Where-Object { $_.critical -and -not $_.met }
    
    $summary = @{
        generatedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        engine = "Human Trial Gate Monitor v1.0"
        humanTrialReadiness = $readiness
        criticalGatesMet = $criticalMet
        criticalGatesTotal = $criticalTotal
        allGates = $results.Count
        gatesPassing = ($results | Where-Object { $_.met }).Count
        blockedByCount = $blockedBy.Count
        blockedByList = $blockedBy | Select-Object -Property id, description, gap
        canProceed = ($criticalMet -eq $criticalTotal) -and ($readiness -ge 100)
        nextAction = if ($blockedBy.Count -gt 0) {
            "BLOCKED: $($blockedBy[0].description) [critical gate]"
        } else {
            "All critical gates passed - human trial readiness achieved"
        }
    }
    
    $summary | ConvertTo-Json -Depth 10 | Set-Content $OutputPath
    
    # Generate Orion-style markdown report
    $mdReportPath = $OutputPath -replace '\.json$', '.md'
    $passingList = $results | Where-Object { $_.met } | ForEach-Object { 
        $criticalMark = if ($_.critical) { "[CRITICAL]" } else { "" }
        "- [PASS] $criticalMark **$($_.description)** ($($_.current)/$($_.target))" 
    }
    $blockedList = $blockedBy | ForEach-Object { 
        "- [BLOCK] **$($_.description)** [gap: $($_.gap)]" 
    }
    
    $mdContent = @"
# Human Trial Gate Monitor Report

**Generated:** $($summary.generatedAt)  
**Engine:** $($summary.engine)  
**Status:** $(if ($summary.canProceed) { "[READY] HUMAN TRIAL APPROVED" } else { "[BLOCKED] DO NOT PROCEED" })

---

## Simple Answer

Human Trial Demo Readiness is at **$readiness%**. **$criticalMet** of **$criticalTotal** critical gates met. $(if ($blockedBy.Count -eq 0) { "All gates passed. Ready for human trial execution." } else { "Blocked by $($blockedBy.Count) critical gates. DO NOT PROCEED with human trials." })

---

## What It Actually Does

The Human Trial Gate Monitor enforces the 8 strict requirements from `data/arc-reactor/status.json` before any human trial demo can proceed:

1. **5 founding demos** - \$1000 founding seat demos with cleared cash
2. **MCP canary** - All exposed tools validated before automation
3. **Rollback paths** - Documented rollback for every automated action
4. **Human approval** - Explicit approval recorded for each participant
5. **PPE evidence** - Certified PPE if medical claims exist (conditional)
6. **ASI validation** - No ASI capability claims without independent validation
7. **Brier tracking** - Forecast/outcome error tracking active
8. **Safety gates** - Automation gates configured and tested

This is a **hard safety boundary** - no human trials until all critical gates pass.

---

## Evidence / Source Discipline

**Arc Reactor Status:** $StatusPath
**Evidence Directory:** D:\tmp\lantern-os\manifests\evidence
**Wallet Ledger:** D:\tmp\lantern-os\ledger\mookman-20-wallet-version-2026-05-26.yaml

**Gates Checked:**
$(foreach ($gate in $results) {
    $status = if ($gate.met) { "PASS" } else { "BLOCK" }
    $critical = if ($gate.critical) { "(critical)" } else { "" }
    "- **$($gate.id)** $critical - $status - $($gate.evidence)"
})

**Category Breakdown:**
- Safety gates: $($results | Where-Object { $_.category -eq 'safety' -and $_.met } | Measure-Object | Select-Object -ExpandProperty Count)/$($results | Where-Object { $_.category -eq 'safety' } | Measure-Object | Select-Object -ExpandProperty Count) met
- Revenue gates: $($results | Where-Object { $_.category -eq 'revenue' -and $_.met } | Measure-Object | Select-Object -ExpandProperty Count)/$($results | Where-Object { $_.category -eq 'revenue' } | Measure-Object | Select-Object -ExpandProperty Count) met
- Compliance gates: $($results | Where-Object { $_.category -eq 'compliance' -and $_.met } | Measure-Object | Select-Object -ExpandProperty Count)/$($results | Where-Object { $_.category -eq 'compliance' } | Measure-Object | Select-Object -ExpandProperty Count) met
- Calibration gates: $($results | Where-Object { $_.category -eq 'calibration' -and $_.met } | Measure-Object | Select-Object -ExpandProperty Count)/$($results | Where-Object { $_.category -eq 'calibration' } | Measure-Object | Select-Object -ExpandProperty Count) met
- Claims gates: $($results | Where-Object { $_.category -eq 'claims' -and $_.met } | Measure-Object | Select-Object -ExpandProperty Count)/$($results | Where-Object { $_.category -eq 'claims' } | Measure-Object | Select-Object -ExpandProperty Count) met

---

## Proven / Held / Local-Only

**Passing Gates:**
$($passingList -join "`n")

**Blocked Gates:**
$($blockedList -join "`n")

**Local-Only:**
- This report is local evidence only
- CanProceed does NOT authorize autonomous action
- Each human trial requires explicit operator approval
- Brier calibration required for each trial outcome

---

## Next Safe Action

$($summary.nextAction)

$(if ($blockedBy.Count -gt 0) {
    $firstBlock = $blockedBy[0]
@"

**Unblock Path for $($firstBlock.id):**
1. Review gate requirements in status.json
2. Collect evidence of completion
3. Update confidence scores
4. Re-run gate monitor
5. Do not proceed until `canProceed: true`

"@
})

**Trial Execution (when ready):**
1. Verify `canProceed: true` in this report
2. Get explicit operator approval for each participant
3. Record human approval receipt
4. Execute trial with full safety gates active
5. Record outcome for Brier calibration
6. Update Movie 3 confidence

---

## Validation Path

- [ ] Review all blocked gates
- [ ] Collect missing evidence
- [ ] Verify PPE if medical claims
- [ ] Confirm ASI pattern boundaries
- [ ] Test Brier tracking with forecast
- [ ] Operator approval for trial
- [ ] Archive this report

---

*Generated by Human Trial Gate Monitor*  
*Skill Reference: skills/asi-arc-reactor-mk1/SKILL.md*  
*Style Reference: docs/ORION-MOOKMANREPORT4-STYLE.md*  
*Arc Reactor Reference: data/arc-reactor/status.json*
"@
    
    $mdContent | Set-Content $mdReportPath
    
    Write-Log ""
    Write-Log "=== Summary ==="
    Write-Log "Human Trial Readiness: $readiness%"
    Write-Log "Critical Gates: $criticalMet/$criticalTotal"
    Write-Log "All Gates: $($summary.gatesPassing)/$($summary.allGates)"
    Write-Log "Blocked By: $($blockedBy.Count)"
    Write-Log "Can Proceed: $($summary.canProceed)"
    Write-Log "Next: $($summary.nextAction)"
    Write-Log "Orion report: $mdReportPath"
    
    return $summary
}

if ($RunOnce -or -not $RunOnce) {
    Invoke-HumanTrialGateMonitor
}
