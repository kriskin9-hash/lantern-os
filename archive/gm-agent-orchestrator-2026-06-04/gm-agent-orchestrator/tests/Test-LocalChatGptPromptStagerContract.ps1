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

function Assert-Contains {
    param(
        [string]$Content,
        [string]$Needle,
        [string]$Message
    )
    if ($Content.IndexOf($Needle, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
        throw $Message
    }
}

$scriptPath = Join-Path $Root "scripts\Start-LocalChatGptPromptStager.ps1"
$dashboardPath = Join-Path $Root "dashboard\index.html"

if (!(Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
    throw "Prompt stager helper missing: $scriptPath"
}
if (!(Test-Path -LiteralPath $dashboardPath -PathType Leaf)) {
    throw "Dashboard missing: $dashboardPath"
}

$script = Get-Content -LiteralPath $scriptPath -Raw
$dashboard = Get-Content -LiteralPath $dashboardPath -Raw

Assert-Contains $script "Set-Clipboard" "Prompt stager must prepare clipboard for manual paste."
Assert-Contains $script "Start-Process" "Prompt stager must launch a local browser."
Assert-Contains $script "--user-data-dir" "Prompt stager must use a dedicated browser profile directory."
Assert-Contains $script "promptSha256" "Prompt stager must write prompt hash audit evidence."
Assert-Contains $script "stoppedBeforeSend" "Prompt stager must record that it stops before Send."
Assert-Contains $script "autoSend = `$false" "Prompt stager must explicitly not auto-send."
Assert-Contains $script "responseScraping = `$false" "Prompt stager must explicitly not scrape responses."
Assert-Contains $script "agentDispatch = `$false" "Prompt stager must explicitly not dispatch agents."
Assert-Contains $script "queueMovement = `$false" "Prompt stager must explicitly not move queues."
Assert-Contains $script "Provide either -Prompt or -PromptFile, not both." "Prompt stager must reject ambiguous prompt sources."

# Only block executable automation hooks here. The helper may contain human-facing
# safety language such as "click Send manually" or "no response scraping".
$blockedAutomationPatterns = @(
    "SendKeys",
    "document\.querySelector",
    "dispatchEvent",
    "Start-AgentSlot",
    "Move-OrchestratorTask",
    "Invoke-OrchestratorAgentAction"
)
foreach ($pattern in $blockedAutomationPatterns) {
    if ([regex]::IsMatch($script, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
        throw "Prompt stager contains blocked automation pattern: $pattern"
    }
}

Assert-Contains $dashboard "Local ChatGPT Prompt Stager" "Dashboard must expose the local ChatGPT prompt stager panel."
Assert-Contains $dashboard "Start-LocalChatGptPromptStager.ps1" "Dashboard must show the helper command."
Assert-Contains $dashboard "Manual-send only" "Dashboard must state manual-send boundary."
Assert-Contains $dashboard "no scraping" "Dashboard must state no response scraping."
Assert-Contains $dashboard "no agent dispatch" "Dashboard must state no agent dispatch."
Assert-Contains $dashboard "Copy command" "Dashboard must include a copy-command affordance."

Write-Host "Validated Local ChatGPT Prompt Stager contract."
