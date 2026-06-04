[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path

$agents = Join-Path $root "config\agents.json"
$agentsExample = Join-Path $root "config\agents.example.json"
$projects = Join-Path $root "config\projects.json"
$projectsExample = Join-Path $root "config\projects.example.json"

if (!(Test-Path $agents)) {
    Copy-Item $agentsExample $agents
    Write-Host "Created config\agents.json"
}

if (!(Test-Path $projects)) {
    Copy-Item $projectsExample $projects
    Write-Host "Created config\projects.json"
}

Write-Host "Next:"
Write-Host "1. Edit config\projects.json"
Write-Host "2. Edit config\agents.json"
Write-Host "3. Add a task to tasks\queue"
Write-Host "4. Run .\scripts\Start-GmAgentOrchestrator.ps1"
