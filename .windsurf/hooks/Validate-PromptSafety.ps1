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

# Check prompt for blocked patterns
$prompt = if ($data.PSObject.Properties.Name -contains 'prompt') { $data.prompt } else { "" }

$blockedPatterns = @(
    'bypass.*approval',
    'ignore.*safety',
    'disable.*validation',
    'ASI.*capability.*exists',
    'local.*superintelligence'
)

foreach ($pattern in $blockedPatterns) {
    if ($prompt -match $pattern) {
        $result = @{
            valid = $false
            blocked = $true
            reasons = @("Blocked prompt pattern detected: $pattern")
        } | ConvertTo-Json -Depth 10
        Write-Output $result
        exit 2  # Block the action
    }
}

Write-Output $result
exit 0
