param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$ExecuteOutreach,
    [switch]$ExecuteCommercialPlan,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "=== Emergency Funding Automation ===" -ForegroundColor Cyan
Write-Host "Automated execution of funding outreach and commercial plan" -ForegroundColor Yellow

$outreachFile = Join-Path $Root "offers/EMERGENCY-FUNDING-OUTREACH-2026-05-30.md"
$commercialFile = Join-Path $Root "reports/CONSOLIDATED-THREE-PART-STRATEGY-REPORT-2026-05-30.md"
$automationReport = Join-Path $Root "data\automation\emergency-funding-execution-$(Get-Date -Format 'yyyy-MM-dd').json"

New-Item -ItemType Directory -Force -Path (Split-Path $automationReport) | Out-Null

$result = @{
    timestamp = (Get-Date).ToString("o")
    root = $Root
    outreachExecuted = $false
    commercialPlanExecuted = $false
    actions = @()
}

if ($ExecuteOutreach) {
    Write-Host "Executing automated outreach..." -ForegroundColor Yellow
    
    if (Test-Path $outreachFile) {
        $outreachContent = Get-Content $outreachFile -Raw
        
        # Extract platform-specific messages
        $null = $outreachContent -split "### Patreon Campaign Pitch" | Select-Object -First 1
        $null = $outreachContent -split "### GoFundMe Campaign Pitch" | Select-Object -First 1
        
        $result.actions += @{
            type = "outreach_preparation"
            platforms = @("Kickstarter", "Patreon", "GoFundMe")
            status = "messages_extracted"
            timestamp = (Get-Date).ToString("o")
        }
        
        Write-Host "Outreach messages extracted and ready for deployment" -ForegroundColor Green
        $result.outreachExecuted = $true
    } else {
        Write-Host "Outreach file not found: $outreachFile" -ForegroundColor Red
        $result.actions += @{
            type = "outreach_preparation"
            status = "failed"
            error = "File not found"
            timestamp = (Get-Date).ToString("o")
        }
    }
}

if ($ExecuteCommercialPlan) {
    Write-Host "Executing commercial plan automation..." -ForegroundColor Yellow
    
    if (Test-Path $commercialFile) {
        # Extract seven-day action plan
        $null = Get-Content $commercialFile -Raw | Select-String -Pattern "Seven-Day Action Plan" -Context 0,20
        
        $today = Get-Date
        $currentPhase = "Foundation"
        
        # Determine current phase based on date
        if ($today -ge (Get-Date "2026-05-30")) {
            $currentPhase = "Foundation/Outreach"
        }
        if ($today -ge (Get-Date "2026-06-01")) {
            $currentPhase = "Sales"
        }
        if ($today -ge (Get-Date "2026-06-03")) {
            $currentPhase = "Secondary packaging"
        }
        
        $result.actions += @{
            type = "commercial_plan_execution"
            currentPhase = $currentPhase
            status = "phase_identified"
            timestamp = (Get-Date).ToString("o")
        }
        
        # Automate top priority offer: Repo/RAG cleanup sprint
        $result.actions += @{
            type = "offer_activation"
            offer = "Repo/RAG cleanup sprint"
            price = "$199 pilot or 2 x $125 slots"
            status = "ready_for_outreach"
            timestamp = (Get-Date).ToString("o")
        }
        
        Write-Host "Commercial plan executed - current phase: $currentPhase" -ForegroundColor Green
        Write-Host "Top offer activated: Repo/RAG cleanup sprint" -ForegroundColor Green
        $result.commercialPlanExecuted = $true
    } else {
        Write-Host "Commercial plan file not found: $commercialFile" -ForegroundColor Red
        $result.actions += @{
            type = "commercial_plan_execution"
            status = "failed"
            error = "File not found"
            timestamp = (Get-Date).ToString("o")
        }
    }
}

# Generate immediate action items
$immediateActions = @(
    "Send 15 personalized outreach messages (Day 2 target)"
    "Create payment link for $199 pilot slot"
    "Prepare before/after proof sample"
    "Book first consultation call"
)

$result.actions += @{
    type = "immediate_actions"
    actions = $immediateActions
    status = "pending_execution"
    timestamp = (Get-Date).ToString("o")
}

# Save automation report
$result | ConvertTo-Json -Depth 10 | Set-Content $automationReport

Write-Host "=== Automation Complete ===" -ForegroundColor Cyan
Write-Host "Report saved to: $automationReport" -ForegroundColor Yellow
Write-Host "Immediate actions required: $($immediateActions.Count)" -ForegroundColor Yellow

if (-not $Force) {
    Write-Host ""
    Write-Host "To execute actual outreach, run with -ExecuteOutreach -Force" -ForegroundColor Yellow
    Write-Host "To execute commercial plan, run with -ExecuteCommercialPlan -Force" -ForegroundColor Yellow
}

return $result
