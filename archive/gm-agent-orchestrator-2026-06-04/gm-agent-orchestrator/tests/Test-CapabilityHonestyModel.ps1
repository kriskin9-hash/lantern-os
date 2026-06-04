[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path $Root).Path
$docPath = Join-Path $Root 'docs\product\capability-honesty-model.md'
$schemaPath = Join-Path $Root 'schemas\capability-map.schema.json'
$examplePath = Join-Path $Root 'status\capability-map.example.json'

$violations = New-Object System.Collections.Generic.List[string]

foreach ($path in @($docPath, $schemaPath, $examplePath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $violations.Add("Missing capability honesty artifact: $($path.Substring($Root.Length + 1))")
    }
}

if (Test-Path -LiteralPath $docPath -PathType Leaf) {
    $doc = Get-Content -LiteralPath $docPath -Raw
    foreach ($needle in @(
        'Suzie must not assume that every installed model, agent slot, tool, or extension can perform every task.',
        'Static config is never enough.',
        'Honest decline pattern',
        'Agent-slot behavior contract',
        'what can Suzie safely do right now?'
    )) {
        if ($doc -notmatch [regex]::Escape($needle)) {
            $violations.Add("Capability honesty doc must preserve required concept: $needle")
        }
    }
}

$schema = $null
if (Test-Path -LiteralPath $schemaPath -PathType Leaf) {
    try {
        $schema = Get-Content -LiteralPath $schemaPath -Raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        $violations.Add("Capability map schema must parse as JSON: $($_.Exception.Message)")
    }
}

$example = $null
if (Test-Path -LiteralPath $examplePath -PathType Leaf) {
    try {
        $example = Get-Content -LiteralPath $examplePath -Raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        $violations.Add("Capability map example must parse as JSON: $($_.Exception.Message)")
    }
}

if ($null -ne $schema) {
    foreach ($requiredRoot in @('schemaVersion', 'capturedAt', 'profile', 'slots', 'capabilities', 'decisions')) {
        if (-not ($schema.required -contains $requiredRoot)) {
            $violations.Add("Capability map schema required fields must include: $requiredRoot")
        }
    }

    $stateEnum = @($schema.'$defs'.capabilityState.enum)
    foreach ($state in @('available', 'degraded', 'blocked', 'unverified', 'unavailable', 'unsafe')) {
        if (-not ($stateEnum -contains $state)) {
            $violations.Add("Capability state enum must include: $state")
        }
    }
}

if ($null -ne $example) {
    foreach ($prop in @('schemaVersion', 'profile', 'slots', 'capabilities', 'decisions')) {
        if (-not ($example.PSObject.Properties.Name -contains $prop)) {
            $violations.Add("Capability map example must include root property: $prop")
        }
    }

    if ($example.profile.id -ne 'k12-school') {
        $violations.Add('Capability map example should dogfood the k12-school profile.')
    }

    if ($example.profile.cloudAllowed -ne $false) {
        $violations.Add('K-12 capability example should keep cloudAllowed=false by default.')
    }

    $capabilityIds = @($example.capabilities | ForEach-Object { $_.id })
    foreach ($requiredCapability in @('document-summary', 'cloud-ai-processing', 'file-edit', 'outbound-message-send')) {
        if (-not ($capabilityIds -contains $requiredCapability)) {
            $violations.Add("Capability map example must include capability: $requiredCapability")
        }
    }

    $cloudCapability = $example.capabilities | Where-Object { $_.id -eq 'cloud-ai-processing' } | Select-Object -First 1
    if ($null -eq $cloudCapability -or $cloudCapability.state -ne 'blocked') {
        $violations.Add('K-12 cloud-ai-processing capability must be blocked by default.')
    }

    $decisions = @($example.decisions | ForEach-Object { $_.decision })
    foreach ($decision in @('allow', 'degrade', 'decline')) {
        if (-not ($decisions -contains $decision)) {
            $violations.Add("Capability map example must include decision type: $decision")
        }
    }
}

if ($violations.Count -gt 0) {
    throw ($violations -join [Environment]::NewLine)
}

Write-Host 'Capability honesty model contract passed.'
