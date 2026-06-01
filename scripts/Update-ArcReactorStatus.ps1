param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [ValidateSet("movie1GarageConfidence","movie2PublicPlatformConfidence","movie3DistributedFleetConfidence","avengersState","currentPhase")]
    [string]$Field,
    [string]$Value,
    [string]$Note = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$statusPath = Join-Path $Root "data/arc-reactor/status.json"
if (-not (Test-Path -LiteralPath $statusPath)) {
    Write-Host "Arc Reactor status file not found: $statusPath" -ForegroundColor Red
    exit 1
}

$status = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json

# Update timestamp
$status.generatedAt = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")

# Update requested field
if ($Field -eq "movie1GarageConfidence" -or
    $Field -eq "movie2PublicPlatformConfidence" -or
    $Field -eq "movie3DistributedFleetConfidence") {
    $status.$Field = [int]$Value
} else {
    $status.$Field = $Value
}

# Append note if provided
if ($Note) {
    if (-not ($status.PSObject.Properties.Name -contains "updateLog")) {
        $status | Add-Member -NotePropertyName "updateLog" -NotePropertyValue @()
    }
    $status.updateLog += [pscustomobject]@{
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
        field = $Field
        value = $Value
        note = $Note
    }
}

$json = $status | ConvertTo-Json -Depth 10

if ($DryRun) {
    Write-Host "=== Dry Run ===" -ForegroundColor Yellow
    Write-Host $json
} else {
    Set-Content -LiteralPath $statusPath -Value $json -Encoding UTF8
    Write-Host "Arc Reactor updated: $Field = $Value" -ForegroundColor Green
    Write-Host "Timestamp: $($status.generatedAt)" -ForegroundColor Gray
}
