[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Message,

    [string]$ProfilePath = "$env:USERPROFILE\.chatgpt-profile",
    [int]$TimeoutSeconds = 45,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FallbackScript = Join-Path $ScriptDir "..\tools\chatgpt-browser-fallback\chatgpt-fallback.py"
$LogDir = Join-Path $env:USERPROFILE "Documents\gm-agent-orchestrator\logs\control-actions"

# Ensure output directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Execute Python script - capture only JSON output
try {
    $output = & python $FallbackScript $Message 2>&1

    # Parse JSON from output (Python prints only JSON now)
    $result = $output | ConvertFrom-Json -ErrorAction Stop

    # Output result as JSON to caller
    Write-Output ($result | ConvertTo-Json -Depth 10)
} catch {
    # Output error as JSON
    $errorObj = [pscustomobject]@{
        status = "error"
        error = $_.Exception.Message
        timestamp = (Get-Date -Format "o")
    }
    Write-Output ($errorObj | ConvertTo-Json -Depth 10)
}
