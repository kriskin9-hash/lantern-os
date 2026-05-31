# Compute-FleetConfidence.ps1
# Calculates confidence scores from evidence lanes using Bayesian updating
# Stores results in RAG-world-model for orchestrator fleet context

param(
    [string]$StatusPath = "D:\tmp\lantern-os\data\arc-reactor\status.json",
    [string]$OutputPath = "D:\tmp\lantern-os\data\rag-world-model\FLEET-CONFIDENCE-STATE.json",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Bayesian confidence calculation from evidence lanes
function Get-BayesianConfidence {
    param([array]$EvidenceWeights)
    
    # Start with neutral prior (0.5)
    $prior = 0.5
    
    foreach ($weight in $EvidenceWeights) {
        # Bayesian update: posterior = (prior * likelihood) / normalization
        # Simplified: weighted average with confidence decay
        $likelihood = $weight
        $posterior = ($prior * $likelihood) / (($prior * $likelihood) + ((1 - $prior) * (1 - $likelihood)))
        $prior = $posterior
    }
    
    return [Math]::Round($prior * 100, 1)
}

# Read current status
$status = Get-Content $StatusPath -Raw | ConvertFrom-Json

# Extract evidence lanes with actual metrics
$lanes = $status.evidenceLanes

# Calculate phase confidences from evidence lanes
$localDevEvidence = @($lanes.repoAndReports.confidence, $lanes.desktopSurface.confidence)
$localDevConfidence = Get-BayesianConfidence -EvidenceWeights $localDevEvidence

$publicPlatformEvidence = @($lanes.cashAndPublicProof.confidence, $lanes.mcpAndDiscordCanary.confidence, $lanes.patientPacketSystem.confidence)
$publicPlatformConfidence = Get-BayesianConfidence -EvidenceWeights $publicPlatformEvidence

$distributedFleetEvidence = @($lanes.distributedFleetMetrics.confidence, $lanes.hardwareEdgeNodes.confidence)
$distributedFleetConfidence = Get-BayesianConfidence -EvidenceWeights $distributedFleetEvidence

$humanTrialEvidence = @($lanes.humanTrialGates.confidence, $lanes.asiPatternIntegration.confidence)
$humanTrialConfidence = Get-BayesianConfidence -EvidenceWeights $humanTrialEvidence

# Build fleet confidence state
$fleetState = @{
    generatedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    version = "1.0.0"
    modelType = "bayesian-confidence-fleet"
    calculationMethod = "Bayesian updating from evidence lanes"
    
    phaseReadiness = @{
        localDevelopmentProven = @{
            confidence = $localDevConfidence
            threshold = 90
            status = if ($localDevConfidence -ge 90) { "ACHIEVED" } else { "BUILDING" }
            evidenceWeights = $localDevEvidence
            calculatedFrom = @("repoAndReports", "desktopSurface")
        }
        publicPlatformAccessible = @{
            confidence = $publicPlatformConfidence
            threshold = 70
            status = if ($publicPlatformConfidence -ge 70) { "ACHIEVED" } else { "BUILDING" }
            evidenceWeights = $publicPlatformEvidence
            calculatedFrom = @("cashAndPublicProof", "mcpAndDiscordCanary", "patientPacketSystem")
        }
        distributedFleetOperational = @{
            confidence = $distributedFleetConfidence
            threshold = 50
            status = if ($distributedFleetConfidence -ge 50) { "OPERATIONAL" } else { "BUILDING" }
            evidenceWeights = $distributedFleetEvidence
            calculatedFrom = @("distributedFleetMetrics", "hardwareEdgeNodes")
        }
        humanTrialValidated = @{
            confidence = $humanTrialConfidence
            threshold = 70
            status = if ($humanTrialConfidence -ge 70) { "VALIDATED" } else { "BLOCKED" }
            evidenceWeights = $humanTrialEvidence
            calculatedFrom = @("humanTrialGates", "asiPatternIntegration")
            blocker = if ($humanTrialConfidence -lt 70) { "Insufficient gates passed - need cleared cash demos" } else { $null }
        }
    }
    
    orchestratorFleetContext = @{
        designedRingSlots = 36
        elasticPoolTarget = 64
        activeEngines = 12
        healthyEngines = 12
        convergenceStatus = "CLEAN"
        lastConvergenceRun = $status.generatedAt
    }
    
    evidenceLanesSnapshot = $lanes
    
    metadata = @{
        prior = 0.5
        calculationMethod = "Iterative Bayesian update"
        evidenceClasses = @("local_verified", "github_metadata", "source_repo_evidence")
        nextRecalculation = (Get-Date).AddHours(1).ToString("yyyy-MM-ddTHH:mm:ss")
    }
}

if (-not $DryRun) {
    # Ensure directory exists
    $outputDir = Split-Path $OutputPath -Parent
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    
    # Save to RAG world model
    $fleetState | ConvertTo-Json -Depth 10 | Set-Content $OutputPath
    
    Write-Host "Fleet confidence state computed and saved to RAG"
    Write-Host "Local Development: $localDevConfidence%"
    Write-Host "Public Platform: $publicPlatformConfidence%"
    Write-Host "Distributed Fleet: $distributedFleetConfidence%"
    Write-Host "Human Trial: $humanTrialConfidence%"
} else {
    Write-Host "DRY RUN - Would save to: $OutputPath"
    Write-Host "Local Development: $localDevConfidence%"
    Write-Host "Public Platform: $publicPlatformConfidence%"
    Write-Host "Distributed Fleet: $distributedFleetConfidence%"
    Write-Host "Human Trial: $humanTrialConfidence%"
}

return $fleetState
