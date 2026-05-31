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

# Log command execution to audit trail
$command = if ($data.PSObject.Properties.Name -contains 'command') { $data.command } else { "" }
$context = if ($data.PSObject.Properties.Name -contains 'context') { $data.context } else "general"

$logEntry = @{
    timestamp = (Get-Date).ToString("o")
    action = "command_execution"
    command = $command
    context = $context
} | ConvertTo-Json -Depth 10

$logPath = Join-Path $PSScriptRoot "..\..\logs\cascade-audit.log"
$logDir = Split-Path $logPath -Parent

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Add-Content -Path $logPath -Value $logEntry

exit 0
