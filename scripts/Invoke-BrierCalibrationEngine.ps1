param(
    [string]$StatusPath = "D:\tmp\lantern-os\data\arc-reactor\status.json",
    [string]$HistoryPath = "D:\tmp\lantern-os\data\automation\brier-history.json",
    [string]$OutputPath = "D:\tmp\lantern-os\data\automation\brier-calibration-results.json",
    [switch]$DryRun,
    [switch]$RunOnce
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
    
    $logPath = "D:\tmp\lantern-os\data\automation\brier-calibration.log"
    Add-Content -Path $logPath -Value "[$timestamp] [$Level] $Message" -ErrorAction SilentlyContinue
}

function Get-CurrentConfidenceScores {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        Write-Log "Status file not found: $Path" "WARN"
        return $null
    }
    
    try {
        $status = Get-Content $Path -Raw | ConvertFrom-Json
        
        return @{
            movie1Garage = $status.movie1GarageConfidence
            movie2Public = $status.movie2PublicPlatformConfidence
            movie3Fleet = $status.movie3DistributedFleetConfidence
            humanTrial = $status.humanTrialDemoReadiness
            evidenceLanes = $status.evidenceLanes
            timestamp = $status.generatedAt
            modelVersion = $status.modelVersion
        }
    }
    catch {
        Write-Log "Failed to parse status file: $_" "ERROR"
        return $null
    }
}

function Get-BrierHistory {
    param([string]$Path)
    
    if (Test-Path $Path) {
        try {
            return Get-Content $Path -Raw | ConvertFrom-Json
        }
        catch {
            Write-Log "Failed to load history, starting fresh" "WARN"
        }
    }
    
    return @{
        forecasts = @()
        calibrationScore = 0.0
        totalPredictions = 0
        accuratePredictions = 0
    }
}

function Save-BrierHistory {
    param([string]$Path, [object]$History)
    
    $outputDir = Split-Path $Path -Parent
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    
    if (-not $DryRun) {
        $History | ConvertTo-Json -Depth 10 | Set-Content $Path
    }
}

function Calculate-BrierScore {
    param([double]$Forecast, [bool]$Outcome)
    
    # Brier score = (forecast - outcome)^2
    # Lower is better (0 = perfect, 1 = worst)
    $outcomeNum = if ($Outcome) { 1.0 } else { 0.0 }
    $normalizedForecast = $Forecast / 100.0
    
    $score = [Math]::Pow($normalizedForecast - $outcomeNum, 2)
    return [Math]::Round($score, 4)
}

function Get-RaisesMovie2Criteria {
    # From status.json raisesMovie2 list
    return @(
        @{ id = "outreach-5"; description = "5 outreach sends recorded in wallet ledger"; weight = 0.15 }
        @{ id = "paid-pilot-1"; description = "1 paid pilot or hard rejection batch"; weight = 0.20 }
        @{ id = "public-proof"; description = "1 public proof page or demo artifact"; weight = 0.15 }
        @{ id = "user-feedback"; description = "1 user/customer/stakeholder feedback receipt"; weight = 0.10 }
        @{ id = "discord-health"; description = "Discord lounge bot health check passes"; weight = 0.10 }
        @{ id = "mcp-canary"; description = "MCP canary validates exposed tools"; weight = 0.15 }
        @{ id = "dual-boot"; description = "D: shrunk and dual boot readyForInstall=true"; weight = 0.10 }
        @{ id = "workflow-used"; description = "one workflow used by someone other than operator"; weight = 0.05 }
    )
}

function Test-CriteriaStatus {
    param([string]$CriteriaId)
    
    # These would integrate with actual checks in production
    # For now, return simulated status based on known state
    
    $checks = @{
        "outreach-5" = @{ met = $false; evidence = "3 sends recorded, need 2 more" }
        "paid-pilot-1" = @{ met = $false; evidence = "0 paid pilots completed" }
        "public-proof" = @{ met = $false; evidence = "No public demo page yet" }
        "user-feedback" = @{ met = $false; evidence = "No external user feedback collected" }
        "discord-health" = @{ met = $true; evidence = "Bot responds to health checks" }
        "mcp-canary" = @{ met = $false; evidence = "Canary tests defined but not automated" }
        "dual-boot" = @{ met = $false; evidence = "D: not shrunk, disk prep pending" }
        "workflow-used" = @{ met = $false; evidence = "No external workflow usage recorded" }
    }
    
    return $checks[$CriteriaId]
}

function Get-CalibrationTrend {
    param([array]$Forecasts)
    
    if ($Forecasts.Count -lt 2) {
        return @{ trend = "insufficient-data"; change = 0 }
    }
    
    $recent = $Forecasts | Sort-Object -Property timestamp -Descending | Select-Object -First 5
    $movie2Scores = $recent | ForEach-Object { $_.scores.movie2Public } | Where-Object { $_ -ne $null }
    
    if ($movie2Scores.Count -lt 2) {
        return @{ trend = "insufficient-data"; change = 0 }
    }
    
    $first = $movie2Scores[-1]
    $last = $movie2Scores[0]
    $change = $last - $first
    
    if ($change -gt 5) {
        return @{ trend = "improving"; change = $change }
    }
    elseif ($change -lt -5) {
        return @{ trend = "declining"; change = $change }
    }
    else {
        return @{ trend = "stable"; change = $change }
    }
}

function Invoke-BrierCalibrationEngine {
    Write-Log "=== Brier Calibration Engine Started ==="
    
    # Load current confidence scores
    $currentScores = Get-CurrentConfidenceScores -Path $StatusPath
    if (-not $currentScores) {
        Write-Log "Cannot load confidence scores, exiting" "ERROR"
        return @{ success = $false; error = "no-status-data" }
    }
    
    Write-Log "Loaded confidence scores: Movie1=$($currentScores.movie1Garage)%, Movie2=$($currentScores.movie2Public)%"
    
    # Load history
    $history = Get-BrierHistory -Path $HistoryPath
    
    # Record current forecast snapshot
    $forecast = @{
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        scores = @{
            movie1Garage = $currentScores.movie1Garage
            movie2Public = $currentScores.movie2Public
            movie3Fleet = $currentScores.movie3Fleet
            humanTrial = $currentScores.humanTrial
        }
        evidenceLanes = $currentScores.evidenceLanes
    }
    
    # Ensure forecasts is an array, then add
    $forecastList = [System.Collections.ArrayList]@($history.forecasts)
    if ($null -eq $forecastList) { $forecastList = [System.Collections.ArrayList]@() }
    $forecastList.Add($forecast) | Out-Null
    $history.forecasts = $forecastList.ToArray()
    
    # Keep only last 90 days of forecasts
    $cutoff = (Get-Date).AddDays(-90).ToString("yyyy-MM-dd")
    $history.forecasts = $history.forecasts | Where-Object { $_.timestamp -gt $cutoff }
    
    # Check Movie 2 criteria
    $criteria = Get-RaisesMovie2Criteria
    $criteriaStatus = @()
    $metWeight = 0.0
    
    foreach ($criterion in $criteria) {
        $status = Test-CriteriaStatus -CriteriaId $criterion.id
        $criteriaStatus += @{
            id = $criterion.id
            description = $criterion.description
            weight = $criterion.weight
            met = $status.met
            evidence = $status.evidence
        }
        
        if ($status.met) {
            $metWeight += $criterion.weight
        }
    }
    
    # Calculate calibration metrics
    $trend = Get-CalibrationTrend -Forecasts $history.forecasts
    
    # Calculate expected Movie 2 readiness based on criteria
    $expectedReadiness = [Math]::Round($metWeight * 100, 1)
    $actualReadiness = $currentScores.movie2Public
    $calibrationGap = $actualReadiness - $expectedReadiness
    
    # Update history stats
    $history.totalPredictions = $history.forecasts.Count
    $history.lastCalibration = @{
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        expectedReadiness = $expectedReadiness
        actualReadiness = $actualReadiness
        calibrationGap = $calibrationGap
        criteriaMet = ($criteriaStatus | Where-Object { $_.met }).Count
        criteriaTotal = $criteria.Count
    }
    
    # Save history
    Save-BrierHistory -Path $HistoryPath -History $history
    
    # Generate recommendations
    $recommendations = @()
    
    $unmetCritical = $criteriaStatus | Where-Object { $_.weight -ge 0.15 -and -not $_.met }
    foreach ($item in $unmetCritical) {
        $recommendations += @{
            priority = "high"
            action = "movie2-criteria"
            target = $item.id
            description = $item.description
            impact = "+$([Math]::Round($item.weight * 100, 1))% confidence"
        }
    }
    
    if ($calibrationGap -gt 10) {
        $recommendations += @{
            priority = "medium"
            action = "calibration-review"
            description = "Confidence score exceeds criteria-based expectation by $([Math]::Round($calibrationGap, 1))%"
            note = "Verify evidence supports current confidence level"
        }
    }
    
    # Compile results
    $results = @{
        generatedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        engine = "Brier Calibration Engine v1.0"
        mode = if ($DryRun) { "dry-run" } else { "live" }
        currentScores = $currentScores
        criteriaStatus = $criteriaStatus
        criteriaMet = ($criteriaStatus | Where-Object { $_.met }).Count
        criteriaTotal = $criteria.Count
        weightedProgress = [Math]::Round($metWeight * 100, 1)
        calibrationGap = $calibrationGap
        trend = $trend
        history = @{
            totalForecasts = $history.totalPredictions
            firstForecast = if ($history.forecasts.Count -gt 0) { $history.forecasts[0].timestamp } else { $null }
            lastForecast = if ($history.forecasts.Count -gt 0) { $history.forecasts[-1].timestamp } else { $null }
        }
        recommendations = $recommendations
        nextAction = if ($unmetCritical.Count -gt 0) {
            "Focus on unmet critical criteria: $($unmetCritical[0].description)"
        } else {
            "Movie 2 criteria sufficiently met - consider readiness review"
        }
    }
    
    if (-not $DryRun) {
        $results | ConvertTo-Json -Depth 10 | Set-Content $OutputPath
        Write-Log "Results written to $OutputPath"
    }
    
    Write-Log "=== Summary ==="
    Write-Log "Criteria: $($results.criteriaMet)/$($results.criteriaTotal) met"
    Write-Log "Weighted progress: $($results.weightedProgress)%"
    Write-Log "Calibration gap: $($results.calibrationGap)"
    Write-Log "Trend: $($trend.trend)"
    Write-Log "Next: $($results.nextAction)"
    
    return $results
}

# Main
if ($RunOnce -or -not $RunOnce) {
    Invoke-BrierCalibrationEngine
}
