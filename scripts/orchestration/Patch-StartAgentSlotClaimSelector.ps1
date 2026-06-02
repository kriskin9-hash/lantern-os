[CmdletBinding()]
param(
    [string]$Root = "",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function New-Result {
    param(
        [bool]$Ok,
        [string]$State,
        [string]$ErrorMessage = "",
        [object]$Extra = $null
    )

    $payload = [ordered]@{
        ok = $Ok
        state = $State
        dryRun = [bool]$DryRun
        error = $ErrorMessage
        generatedAt = (Get-Date).ToString("o")
    }

    if ($null -ne $Extra) {
        foreach ($property in $Extra.PSObject.Properties) {
            $payload[$property.Name] = $property.Value
        }
    }

    [pscustomobject]$payload
}

try {
    $target = Join-Path $Root "scripts\Start-AgentSlot.ps1"
    if (!(Test-Path -LiteralPath $target -PathType Leaf)) { throw "Missing target: $target" }

    $text = Get-Content -LiteralPath $target -Raw -ErrorAction Stop
    if ($text -match "Claim-OrchestratorQueueTask\.ps1") {
        $result = New-Result -Ok $true -State "already_patched" -Extra ([pscustomobject]@{ target = $target })
    }
    else {
        $pattern = "(?s)function Claim-Task \{.*?\n\}\r?\n\r?\nfunction Install-Contract"
        $replacement = @'
function Claim-Task {
    $claimScript = Join-Path $OrchestratorRoot "scripts\Claim-OrchestratorQueueTask.ps1"
    if (!(Test-Path -LiteralPath $claimScript -PathType Leaf)) {
        throw "Claim selector helper was not found: $claimScript"
    }

    $slotRole = Get-SlotRole
    $claim = & $claimScript `
        -Root $OrchestratorRoot `
        -SlotName $script:SlotName `
        -Role $slotRole `
        -Capabilities @($slotRole, [string]$script:Slot.agent) `
        -PassThru

    if ($null -eq $claim) {
        Write-Slot "No claim result returned by queue selector."
        Write-SlotStatus -State "blocked" -Reason "claim_selector_no_result" -NextAction "Inspect Claim-OrchestratorQueueTask.ps1 and queue state."
        return $null
    }

    if (-not $claim.ok) {
        Write-Slot "Queue selector failed: $($claim.error)"
        Write-SlotStatus -State "blocked" -Reason "claim_selector_failed" -NextAction $claim.error
        return $null
    }

    if ($claim.state -eq "claimed") {
        return Join-RootRelativePath -RelativePath ([string]$claim.activePath)
    }

    if ($claim.state -eq "no_compatible_task") {
        Write-Slot "No compatible queued task for slot $script:SlotName."
        Write-SlotStatus -State "idle" -Reason "no_compatible_task" -NextAction "Queue a compatible task for $script:SlotName or update slot capabilities."
        return $null
    }

    if ($claim.state -eq "no_queued_tasks") {
        Write-Slot "No queued task. Sleeping."
        Write-SlotStatus -State "idle" -Reason "no_queued_tasks" -NextAction "Queue work before starting $script:SlotName."
        return $null
    }

    Write-Slot "Queue selector returned non-claim state: $($claim.state)"
    Write-SlotStatus -State "idle" -Reason ([string]$claim.state) -NextAction "Inspect queue selector output."
    return $null
}

function Install-Contract
'@

        $newText = [regex]::Replace($text, $pattern, $replacement, 1)
        if ($newText -eq $text) { throw "Claim-Task function block was not found or was not replaced." }

        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseInput($newText, [ref]$tokens, [ref]$errors) | Out-Null
        if ($errors.Count -gt 0) {
            throw "Patched Start-AgentSlot.ps1 parser failed: " + (($errors | ForEach-Object { $_.Message }) -join "; ")
        }

        if ($DryRun) {
            $result = New-Result -Ok $true -State "patch_dry_run" -Extra ([pscustomobject]@{ target = $target })
        }
        else {
            $backup = $target + ".bak-claim-selector-" + (Get-Date -Format "yyyyMMdd-HHmmss")
            Copy-Item -LiteralPath $target -Destination $backup -Force
            [System.IO.File]::WriteAllText($target, $newText, [System.Text.UTF8Encoding]::new($false))
            $result = New-Result -Ok $true -State "patched" -Extra ([pscustomobject]@{ target = $target; backup = $backup })
        }
    }
}
catch {
    $result = New-Result -Ok $false -State "error" -ErrorMessage $_.Exception.Message
}

$result | ConvertTo-Json -Depth 20
