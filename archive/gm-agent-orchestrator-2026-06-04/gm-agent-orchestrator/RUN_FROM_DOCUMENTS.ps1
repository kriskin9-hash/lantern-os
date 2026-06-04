# Run this after extracting gm-agent-orchestrator.zip into Documents.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoPath = Join-Path $env:USERPROFILE "Documents\gm-agent-orchestrator"

if (!(Test-Path $repoPath)) {
    throw "Expected folder not found: $repoPath"
}

Set-Location $repoPath

powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Publish-PrivateRepo.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Initialize-LocalConfig.ps1

Write-Host ""
Write-Host "Done. Next edit:"
Write-Host "  $repoPath\config\projects.json"
Write-Host "  $repoPath\config\agents.json"
