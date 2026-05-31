param(
    [string]$CampaignConfigPath = "D:\tmp\lantern-os\data\automation\emergency-campaign-config.json",
    [string]$OutreachTemplatePath = "D:\tmp\lantern-os\offers\EMERGENCY-FUNDING-OUTREACH-2026-05-30.md",
    [string]$ResultsPath = "D:\tmp\lantern-os\data\automation\emergency-campaign-results.json",
    [switch]$RunOnce,
    [switch]$DryRun,
    [switch]$SkipValidation,
    [switch]$ForceSend
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
    
    $logPath = "D:\tmp\lantern-os\data\automation\emergency-campaign.log"
    Add-Content -Path $logPath -Value "[$timestamp] [$Level] $Message" -ErrorAction SilentlyContinue
}

function Get-CampaignConfiguration {
    param([string]$ConfigFile)
    
    if (Test-Path $ConfigFile) {
        try {
            return Get-Content $ConfigFile -Raw | ConvertFrom-Json
        }
        catch {
            Write-Log "Failed to load config: $_" "ERROR"
            return $null
        }
    }
    
    # Default configuration with safety gates
    return @{
        campaign = @{
            name = "Emergency Bridge Funding"
            validationState = "unvalidated"
            operatorApprovalRequired = $true
            platforms = @("kickstarter", "patreon", "gofundme")
            targetAmount = 1000
            currentBalance = -1000
        }
        safety = @{
            requireOperatorSignoff = $true
            maxCampaignAgeHours = 168  # 7 days
            allowPublicPublish = $false
            requireEvidence = $true
        }
        templates = @{
            kickstarter = @{
                tone = "project-focused"
                tiers = @(
                    @{ amount = 25; reward = "Early access + credit" },
                    @{ amount = 50; reward = "Founder tier + roadmap input" },
                    @{ amount = 100; reward = "Sponsor tier + 1hr consult" }
                )
            }
            patreon = @{
                tone = "recurring-support"
                tiers = @(
                    @{ amount = 5; reward = "Insider updates" },
                    @{ amount = 15; reward = "Monthly AMA access" },
                    @{ amount = 50; reward = "Priority support + beta access" }
                )
            }
            gofundme = @{
                tone = "emergency-transparency"
                goal = 1000
                story = "Unexpected infrastructure costs during Lantern OS development"
            }
        }
    }
}

function Test-ValidationBoundary {
    param([object]$Config)
    
    $violations = @()
    
    # Check validation state
    if ($Config.campaign.validationState -eq "unvalidated" -and -not $SkipValidation) {
        $violations += "Campaign is unvalidated - requires operator review"
    }
    
    # Check operator approval
    if ($Config.safety.requireOperatorSignoff -and -not $ForceSend) {
        $violations += "Operator signoff required before any publication"
    }
    
    # Check public publish permission
    if (-not $Config.safety.allowPublicPublish) {
        $violations += "Public publishing explicitly disabled in safety config"
    }
    
    # Check evidence requirements
    if ($Config.safety.requireEvidence) {
        $evidencePath = "D:\tmp\lantern-os\manifests\evidence"
        if (-not (Test-Path $evidencePath)) {
            $violations += "Evidence directory not found: $evidencePath"
        }
    }
    
    return @{
        canProceed = $violations.Count -eq 0
        violations = $violations
        requiresOperatorAction = $violations.Count -gt 0
    }
}

function Get-FinancialState {
    # In production, this would integrate with actual financial APIs
    # For now, returns documented state from emergency funding file
    
    $outreachPath = "D:\tmp\lantern-os\offers\EMERGENCY-FUNDING-OUTREACH-2026-05-30.md"
    
    if (Test-Path $outreachPath) {
        $content = Get-Content $outreachPath -Raw
        
        # Extract financial claims from markdown
        $accountBalance = if ($content -match 'Account balance:\s*(-?\$?\d+)') { $Matches[1] } else { "unknown" }
        $tokenBurn = if ($content -match 'Token burn:\s*([^\r\n]+)') { $Matches[1] } else { "unknown" }
        $rootCause = if ($content -match 'Root cause:\s*([^\r\n]+)') { $Matches[1] } else { "unknown" }
        
        return @{
            accountBalance = $accountBalance
            tokenBurn = $tokenBurn
            rootCause = $rootCause
            source = $outreachPath
            lastUpdated = (Get-Item $outreachPath).LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        }
    }
    
    return @{
        accountBalance = "unknown"
        source = "not found"
        lastUpdated = "never"
    }
}

function Get-OutreachTemplates {
    param([string]$TemplatePath)
    
    if (-not (Test-Path $TemplatePath)) {
        Write-Log "Outreach template not found: $TemplatePath" "WARN"
        return @{
            kickstarter = "Template not available"
            patreon = "Template not available"
            gofundme = "Template not available"
        }
    }
    
    $content = Get-Content $TemplatePath -Raw
    
    # Parse platform sections from markdown
    # This is a simple parser - in production would use proper markdown parsing
    
    $templates = @{}
    
    # Extract Kickstarter section
    if ($content -match "##? Kickstarter[\s\S]*?(?=##? |$)") {
        $templates.kickstarter = $Matches[0]
    }
    
    # Extract Patreon section  
    if ($content -match "##? Patreon[\s\S]*?(?=##? |$)") {
        $templates.patreon = $Matches[0]
    }
    
    # Extract GoFundMe section
    if ($content -match "##? GoFundMe[\s\S]*?(?=##? |$)") {
        $templates.gofundme = $Matches[0]
    }
    
    return $templates
}

function Test-EmergencyThreshold {
    param([object]$FinancialState)
    
    # Check for critical threshold (e.g., -$500 or worse)
    $threshold = -500
    $balance = 0
    
    if ($FinancialState.accountBalance -match '-?\$?(\d+)') {
        $balance = [int]$Matches[1]
        if ($FinancialState.accountBalance -match '-\$?(\d+)') {
            $balance = -$balance
        }
    }
    
    $isNegative = $balance -lt 0
    
    return @{
        isEmergency = $balance -lt $threshold
        isNegative = $isNegative
        balance = $balance
        threshold = $threshold
        daysToResolve = if ($balance -lt 0) { "immediate" } else { "stable" }
    }
}

function Invoke-EmergencyFundingCampaign {
    Write-Log "=== Emergency Funding Campaign Engine Started ==="
    
    if ($DryRun) {
        Write-Log "DRY RUN MODE - No external actions will be taken"
    }
    
    # Load configuration
    $config = Get-CampaignConfiguration -ConfigFile $CampaignConfigPath
    if (-not $config) {
        Write-Log "Failed to load campaign configuration" "ERROR"
        return @{ success = $false; error = "config-load-failed" }
    }
    
    # Get current financial state
    $financialState = Get-FinancialState
    Write-Log "Financial state: Account $($financialState.accountBalance)"
    
    # Check emergency threshold
    $emergencyStatus = Test-EmergencyThreshold -FinancialState $financialState
    if ($emergencyStatus.isEmergency) {
        Write-Log "EMERGENCY THRESHOLD DETECTED: Balance $($emergencyStatus.balance)" "WARN"
    }
    
    # Test validation boundaries
    $validation = Test-ValidationBoundary -Config $config
    if (-not $validation.canProceed) {
        Write-Log "VALIDATION BOUNDARY BLOCKING:" "WARN"
        foreach ($violation in $validation.violations) {
            Write-Log "  - $violation" "WARN"
        }
        
        if ($validation.requiresOperatorAction -and -not $ForceSend) {
            Write-Log "Campaign blocked pending operator action. Use -ForceSend to override (not recommended)." "ERROR"
            
            return @{
                success = $false
                blocked = $true
                validation = $validation
                financialState = $financialState
                emergencyStatus = $emergencyStatus
                nextAction = "Operator must review offers/EMERGENCY-FUNDING-OUTREACH-2026-05-30.md and clear validation"
            }
        }
    }
    
    # Load outreach templates
    $templates = Get-OutreachTemplates -TemplatePath $OutreachTemplatePath
    
    # Compile campaign status
    $campaignStatus = @{
        generatedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        engine = "Emergency Funding Campaign Engine v1.0"
        mode = if ($DryRun) { "dry-run" } else { "live" }
        validation = $validation
        financialState = $financialState
        emergencyStatus = $emergencyStatus
        config = $config
        templates = @{
            kickstarterAvailable = $templates.ContainsKey("kickstarter")
            patreonAvailable = $templates.ContainsKey("patreon")
            gofundmeAvailable = $templates.ContainsKey("gofundme")
        }
        platforms = @()
    }
    
    # Generate platform-specific campaign data
    foreach ($platform in $config.campaign.platforms) {
        $platformData = @{
            name = $platform
            enabled = $true
            templateAvailable = $templates.ContainsKey($platform)
            canPublish = $validation.canProceed -and -not $DryRun
            validationRequired = $true
            operatorBoundary = "Do not publish without operator signoff"
        }
        
        if ($platform -eq "kickstarter") {
            $platformData.tiers = $config.templates.kickstarter.tiers
            $platformData.estimatedReach = "low-moderate"
            $platformData.timeToFunds = "30-60 days"
        }
        elseif ($platform -eq "patreon") {
            $platformData.tiers = $config.templates.patreon.tiers
            $platformData.estimatedReach = "low"
            $platformData.timeToFunds = "immediate but small"
        }
        elseif ($platform -eq "gofundme") {
            $platformData.goal = $config.templates.gofundme.goal
            $platformData.estimatedReach = "moderate"
            $platformData.timeToFunds = "7-14 days"
        }
        
        $campaignStatus.platforms += $platformData
    }
    
    # Determine best path to cash
    $fastestPath = @{
        method = "direct-outreach"
        reason = "Platform routes have delays; direct payment is fastest"
        estimatedTime = "same day if warm contact responds"
        action = "Send personalized outreach to warm contacts with payment link"
        platforms = $campaignStatus.platforms | Where-Object { $_.timeToFunds -match "immediate|7-14" }
    }
    
    $campaignStatus.fastestPath = $fastestPath
    $campaignStatus.recommendedAction = $fastestPath.action
    
    # Safety gate summary
    $campaignStatus.safetyGates = @{
        validationBoundaryActive = $validation.requiresOperatorAction
        publicPublishBlocked = -not $validation.canProceed
        operatorSignoffRequired = $config.safety.requireOperatorSignoff
        evidenceRequired = $config.safety.requireEvidence
    }
    
    # Write results
    if (-not $DryRun) {
        $outputDir = Split-Path $ResultsPath -Parent
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }
        
        $campaignStatus | ConvertTo-Json -Depth 10 | Set-Content $ResultsPath
        Write-Log "Campaign status written to $ResultsPath"
    }
    else {
        Write-Log "DRY RUN: Would write to $ResultsPath"
        $campaignStatus | ConvertTo-Json -Depth 10 | Write-Host
    }
    
    # Summary
    Write-Log "=== Campaign Summary ==="
    Write-Log "Emergency status: $($emergencyStatus.isEmergency)"
    Write-Log "Validation blocking: $($validation.requiresOperatorAction)"
    Write-Log "Platforms configured: $($config.campaign.platforms -join ', ')"
    Write-Log "Fastest path: $($fastestPath.method)"
    Write-Log "Recommended: $($fastestPath.action)"
    
    return $campaignStatus
}

# Main execution
if ($RunOnce -or -not $RunOnce) {
    Invoke-EmergencyFundingCampaign
}
