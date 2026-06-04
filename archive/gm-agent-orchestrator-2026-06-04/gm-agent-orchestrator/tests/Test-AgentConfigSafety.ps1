param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

$violations = New-Object System.Collections.Generic.List[string]

$configPaths = @(
    (Join-Path $Root 'config/agents.example.json'),
    (Join-Path $Root 'config/agents.json')
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }

if (@($configPaths).Count -eq 0) {
    throw 'No agent config files found.'
}

foreach ($agentsPath in $configPaths) {
    $config = Get-Content -LiteralPath $agentsPath -Raw | ConvertFrom-Json
    $relativePath = $agentsPath.Substring($Root.Length + 1)

    foreach ($slot in @($config.slots)) {
        foreach ($commandName in @('start', 'resume', 'fallbackResume')) {
            $property = $slot.command.PSObject.Properties[$commandName]
            if ($null -eq $property) { continue }

            $args = @($property.Value | ForEach-Object { [string]$_ })
            if ($args -contains '--dangerously-skip-permissions') {
                $violations.Add("$relativePath slot '$($slot.name)' command '$commandName' uses --dangerously-skip-permissions.")
            }
        }
    }
}

if ($violations.Count -gt 0) {
    throw ($violations -join [Environment]::NewLine)
}

Write-Host 'Agent config safety tests passed.'
