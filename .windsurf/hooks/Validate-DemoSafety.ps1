param(
    [Parameter(ValueFromPipeline)]
    [string]$InputJson
)

$ErrorActionPreference = "Stop"

# Read JSON input from stdin
if (-not $InputJson) {
    $InputJson = [Console]::In.ReadToEnd()
}

$data = $InputJson | ConvertFrom-Json

# Initialize validation result
$result = @{
    valid = $true
    blocked = $false
    reasons = @()
} | ConvertTo-Json -Depth 10

# Check if this is a human trial demo context
if ($data.PSObject.Properties.Name -contains 'context' -and $data.context -eq 'human_trial_demo') {
    # Check Arc Reactor status
    $arcStatusPath = Join-Path $PSScriptRoot "..\..\data\arc-reactor\status.json"
    if (Test-Path $arcStatusPath) {
        $arcStatus = Get-Content $arcStatusPath | ConvertFrom-Json
        
        # Check human trial readiness
        if ($arcStatus.humanTrialDemoReadiness -lt 50) {
            $result = @{
                valid = $false
                blocked = $true
                reasons = @("Human trial demo readiness below threshold (current: $($arcStatus.humanTrialDemoReadiness))")
            } | ConvertTo-Json -Depth 10
            Write-Output $result
            exit 2  # Block the action
        }
    }
    
    # Check MCP canary status
    $mcpCanaryPath = Join-Path $PSScriptRoot "..\..\manifests\validation\MCP-CANARY-LATEST.json"
    if (Test-Path $mcpCanaryPath) {
        $mcpStatus = Get-Content $mcpCanaryPath | ConvertFrom-Json
        
        if ($mcpStatus.status -ne 'passed') {
            $result = @{
                valid = $false
                blocked = $true
                reasons = @("MCP canary validation failed (status: $($mcpStatus.status))")
            } | ConvertTo-Json -Depth 10
            Write-Output $result
            exit 2  # Block the action
        }
    }
}

# Check for dangerous commands
$dangerousPatterns = @(
    'rm -rf',
    'del /',
    'format',
    'diskpart',
    'bootsect',
    'bcdedit',
    'shutdown',
    'reboot'
)

$command = if ($data.PSObject.Properties.Name -contains 'command') { $data.command } else { "" }

foreach ($pattern in $dangerousPatterns) {
    if ($command -like "*$pattern*") {
        $result = @{
            valid = $false
            blocked = $true
            reasons = @("Dangerous command pattern detected: $pattern")
        } | ConvertTo-Json -Depth 10
        Write-Output $result
        exit 2  # Block the action
    }
}

Write-Output $result
exit 0
