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

# Check file path for sensitive locations
$filePath = if ($data.PSObject.Properties.Name -contains 'path') { $data.path } else { "" }

$sensitivePaths = @(
    '.env',
    'secrets',
    'private',
    'credentials',
    'tokens'
)

foreach ($path in $sensitivePaths) {
    if ($filePath -like "*$path*") {
        # Log access but don't block (read-only is okay)
        $result = @{
            valid = $true
            blocked = $false
            reasons = @("Sensitive file access logged: $path")
        } | ConvertTo-Json -Depth 10
        Write-Output $result
        exit 0
    }
}

Write-Output $result
exit 0
