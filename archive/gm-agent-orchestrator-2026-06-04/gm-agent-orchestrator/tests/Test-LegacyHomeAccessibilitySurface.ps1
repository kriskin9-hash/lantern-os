[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path $Root).Path
$docPath = Join-Path $Root 'docs\product\legacy-home-accessibility-surface.md'
$examplePath = Join-Path $Root 'examples\accessibility\legacy-home-workstation.json'

$violations = New-Object System.Collections.Generic.List[string]

foreach ($path in @($docPath, $examplePath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $violations.Add("Missing legacy home accessibility artifact: $($path.Substring($Root.Length + 1))")
    }
}

if (Test-Path -LiteralPath $docPath -PathType Leaf) {
    $doc = Get-Content -LiteralPath $docPath -Raw
    foreach ($needle in @(
        'Suzie should help users change how they interact with a PC',
        'low vision and eye strain',
        'typing pain and repetitive strain risk',
        'Voice-first command mode',
        'no irreversible action by voice alone',
        'Capability honesty for accessibility',
        'Do not require expensive adaptive hardware.'
    )) {
        if ($doc -notmatch [regex]::Escape($needle)) {
            $violations.Add("Legacy home accessibility doc must preserve required concept: $needle")
        }
    }
}

$example = $null
if (Test-Path -LiteralPath $examplePath -PathType Leaf) {
    try {
        $example = Get-Content -LiteralPath $examplePath -Raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        $violations.Add("Legacy home accessibility example must parse as JSON: $($_.Exception.Message)")
    }
}

if ($null -ne $example) {
    if ($example.profile -ne 'legacy-home-accessibility') {
        $violations.Add('Example profile must be legacy-home-accessibility.')
    }

    foreach ($mode in @('voice', 'dictation', 'large-button', 'switch-compatible', 'text-command')) {
        if (-not (@($example.inputModes) -contains $mode)) {
            $violations.Add("Example inputModes must include: $mode")
        }
    }

    foreach ($mode in @('large-text', 'high-contrast', 'screen-reader-text', 'read-aloud', 'plain-text-summary')) {
        if (-not (@($example.outputModes) -contains $mode)) {
            $violations.Add("Example outputModes must include: $mode")
        }
    }

    foreach ($action in @('send', 'submit', 'pay', 'delete', 'force-push', 'start-agents', 'move-queue')) {
        if (-not (@($example.blockedOneClickActions) -contains $action)) {
            $violations.Add("Dangerous action must be blocked from one-click bindings: $action")
        }
    }

    foreach ($action in @('send', 'submit', 'pay', 'delete', 'agent-start')) {
        if (-not (@($example.missionCriticalSafeguards.confirmationRequiredFor) -contains $action)) {
            $violations.Add("Mission-critical safeguards must require confirmation for: $action")
        }
    }

    if ($example.missionCriticalSafeguards.singleInputDependencyAllowed -ne $false) {
        $violations.Add('Mission-critical surface must not allow single input dependency.')
    }

    if ($example.targetHardware.gpuRequired -ne $false) {
        $violations.Add('Legacy home workstation must not require a GPU.')
    }
}

if ($violations.Count -gt 0) {
    throw ($violations -join [Environment]::NewLine)
}

Write-Host 'Legacy home accessibility surface contract passed.'
