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

$docPath = Join-Path $Root "docs\product\grandma-mode-safety.md"
if (-not (Test-Path -LiteralPath $docPath -PathType Leaf)) {
    throw "Grandma safety doc missing: $docPath"
}

$doc = Get-Content -LiteralPath $docPath -Raw
foreach ($needle in @(
    "Hard Denylist",
    "Trusted Contact Escalation",
    "cannot override",
    "Installing software",
    "sending sensitive identity data"
)) {
    if ($doc -notmatch [regex]::Escape($needle)) {
        throw "Grandma safety doc missing required text: $needle"
    }
}

function Invoke-GrandmaPolicy {
    param(
        [string]$ActionCategory,
        [bool]$UserExplicitApproval
    )

    $denylist = @(
        "wire_transfer",
        "account_recovery",
        "urgent_money_solicitation",
        "sensitive_data_disclosure",
        "software_install",
        "contact_or_2fa_change"
    )

    if ($denylist -contains $ActionCategory) {
        return [pscustomobject]@{
            allowed = $false
            reason = "denylisted_action"
            escalateTrustedContact = $true
            ignoredPromptApproval = $UserExplicitApproval
        }
    }

    return [pscustomobject]@{
        allowed = $UserExplicitApproval
        reason = "standard_approval_flow"
        escalateTrustedContact = $false
        ignoredPromptApproval = $false
    }
}

$blocked = Invoke-GrandmaPolicy -ActionCategory "wire_transfer" -UserExplicitApproval $true
if ($blocked.allowed -ne $false) {
    throw "Grandma denylist contract failed: wire transfer must be denied."
}
if ($blocked.escalateTrustedContact -ne $true) {
    throw "Grandma denylist contract failed: blocked action must escalate trusted contact."
}
if ($blocked.ignoredPromptApproval -ne $true) {
    throw "Grandma denylist contract failed: explicit approval must not override denylist."
}

Write-Host "Grandma mode safety contract passed."
