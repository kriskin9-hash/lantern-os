param(
    [string]$EvidencePath = "D:\tmp\lantern-os\manifests\evidence",
    [string]$OutputPath = "D:\tmp\lantern-os\data\automation\evidence-validation-results.json",
    [switch]$RunOnce
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

function Test-EvidenceFile {
    param([string]$Path)
    
    $content = Get-Content $Path -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return @{ valid = $false; score = 0 } }
    
    $score = 100
    $issues = @()
    
    if ($content -notmatch "## Simple Answer") { $score -= 20; $issues += "missing-simple-answer" }
    if ($content -notmatch "## Evidence") { $score -= 15; $issues += "missing-evidence-section" }
    if ($content -notmatch "\d{4}-\d{2}-\d{2}") { $score -= 10; $issues += "no-date" }
    if ($content -notmatch "(not production-ready|requires operator|local-only|unvalidated)") { 
        $score -= 5; $issues += "no-claim-boundaries" 
    }
    
    return @{ valid = $score -ge 70; score = [Math]::Max(0, $score); issues = $issues }
}

function Invoke-EvidenceValidationEngine {
    Write-Log "=== Evidence Validation Engine Started ==="
    
    $files = Get-ChildItem -Path $EvidencePath -Filter "*.md" -Recurse -ErrorAction SilentlyContinue
    $results = @()
    
    foreach ($file in $files) {
        $test = Test-EvidenceFile -Path $file.FullName
        $results += @{
            name = $file.Name
            path = $file.FullName
            valid = $test.valid
            score = $test.score
            issues = $test.issues
        }
    }
    
    $validCount = ($results | Where-Object { $_.valid -eq $true }).Count
    $totalScore = 0
    $scoreCount = 0
    foreach ($r in $results) {
        if ($r -and $r.ContainsKey('score')) {
            $totalScore += $r.score
            $scoreCount++
        }
    }
    $avgScore = if ($scoreCount -gt 0) { [Math]::Round($totalScore / $scoreCount, 1) } else { 0 }
    
    $summary = @{
        generatedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        engine = "Evidence Validation Engine v1.0"
        totalFiles = $results.Count
        validFiles = $validCount
        averageScore = $avgScore
        files = $results
        nextAction = "Review $($results.Count - $validCount) invalid evidence files"
    }
    
    $summary | ConvertTo-Json -Depth 5 | Set-Content $OutputPath
    Write-Log "Validated $($summary.totalFiles) files, $($summary.validFiles) valid, avg score $($summary.averageScore)"
    
    return $summary
}

if ($RunOnce -or -not $RunOnce) {
    Invoke-EvidenceValidationEngine
}
