param(
    [Parameter(ValueFromPipeline)]
    [string]$InputJson
)

$ErrorActionPreference = "Continue"

# Read JSON input from stdin
if (-not $InputJson) {
    $InputJson = [Console]::In.ReadToEnd()
}

$data = $InputJson | ConvertFrom-Json

# Log file write to audit trail
$path = if ($data.PSObject.Properties.Name -contains 'path') { $data.path } else { "" }
$context = if ($data.PSObject.Properties.Name -contains 'context') { $data.context } else { "general" }

$logEntry = @{
    timestamp = (Get-Date).ToString("o")
    action = "file_write"
    path = $path
    context = $context
} | ConvertTo-Json -Depth 10

$logPath = Join-Path $PSScriptRoot "..\..\logs\cascade-audit.log"
$logDir = Split-Path $logPath -Parent

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Add-Content -Path $logPath -Value $logEntry

exit 0
