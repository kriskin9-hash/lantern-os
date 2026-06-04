[CmdletBinding()]
param(
    [switch]$PrepareOnly,
    [switch]$RunOnce,
    [switch]$Headless,
    [string]$AgentsConfigPath = "",
    [string]$ProjectsConfigPath = "",
    [string]$ProjectName = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$startScript = Join-Path $PSScriptRoot "Start-GmAgentOrchestrator.ps1"
if (!(Test-Path $startScript)) {
    throw "Missing orchestrator launcher: $startScript"
}

& $startScript `
    -AgentsConfigPath $AgentsConfigPath `
    -ProjectsConfigPath $ProjectsConfigPath `
    -ProjectName $ProjectName `
    -SlotName "claude-main" `
    -PrepareOnly:$PrepareOnly `
    -RunOnce:$RunOnce `
    -Headless:$Headless
