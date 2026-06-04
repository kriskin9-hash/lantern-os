[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$violations = New-Object System.Collections.Generic.List[string]

function Add-HeadlessSlotViolations {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$SlotPropertyName
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return }

    $relativePath = $Path.Substring($Root.Length + 1)
    $config = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop
    if ($null -eq $config.PSObject.Properties['slots']) { return }

    foreach ($slot in @($config.slots)) {
        $property = $slot.PSObject.Properties[$SlotPropertyName]
        if ($null -eq $property) { continue }

        $slotName = [string]$property.Value
        if ($slotName -match '^headless(?:-|$)') {
            $violations.Add("Legacy headless slot remains in ${relativePath}: $slotName")
        }
    }
}

Add-HeadlessSlotViolations -Path (Join-Path $Root 'config\slot-bindings.json') -SlotPropertyName 'slot'
Add-HeadlessSlotViolations -Path (Join-Path $Root 'config\agents.example.json') -SlotPropertyName 'name'
Add-HeadlessSlotViolations -Path (Join-Path $Root 'config\agents.json') -SlotPropertyName 'name'

$claimScript = Join-Path $Root 'scripts\Claim-OrchestratorQueueTask.ps1'
if (Test-Path -LiteralPath $claimScript -PathType Leaf) {
    $claimContent = Get-Content -LiteralPath $claimScript -Raw
    if ($claimContent -match '\$SlotName\s+-match\s+["'']headless["'']') {
        $violations.Add('Claim-OrchestratorQueueTask.ps1 still contains a headless-specific SlotName routing branch.')
    }
}

if ($violations.Count -gt 0) {
    throw ($violations -join [Environment]::NewLine)
}

Write-Host 'Validated legacy headless slot retirement contract.'
