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

# Check MCP tool against ASI boundaries
$toolName = if ($data.PSObject.Properties.Name -contains 'tool') { $data.tool } else { ""

# Blocked MCP tools for human trial demos
$blockedTools = @(
    'execute_arbitrary_code',
    'modify_system_files',
    'access_secrets',
    'bypass_approval'
)

if ($blockedTools -contains $toolName) {
    $result = @{
        valid = $false
        blocked = $true
        reasons = @("Blocked MCP tool: $toolName")
    } | ConvertTo-Json -Depth 10
    Write-Output $result
    exit 2  # Block the action
}

# Check ASI pattern boundaries
$asiEvidencePath = Join-Path $PSScriptRoot "..\..\manifests\evidence\asi-local-pdf-convergence-2026-05-29.md"
if (Test-Path $asiEvidencePath) {
    # Block tools that would make ASI capability claims
    if ($toolName -like '*asi*' -or $toolName -like '*superintelligence*') {
        $result = @{
            valid = $false
            blocked = $true
            reasons = @("ASI capability claims blocked - ASI patterns are architecture references only")
        } | ConvertTo-Json -Depth 10
        Write-Output $result
        exit 2  # Block the action
    }
}

Write-Output $result
exit 0
