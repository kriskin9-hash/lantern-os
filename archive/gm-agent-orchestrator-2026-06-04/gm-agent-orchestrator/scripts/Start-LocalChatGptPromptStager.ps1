<#
Local ChatGPT prompt stager.

Purpose:
  Open ChatGPT in a dedicated local Chrome profile, place one operator-approved
  prompt on the clipboard, write local audit evidence, and stop before send.

Non-goals / safety:
  - no credential storage
  - no automatic Send/click/keypress
  - no response scraping
  - no queue movement
  - no agent dispatch
  - no MCP exposure

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LocalChatGptPromptStager.ps1 -Prompt "Summarize the queue state."
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LocalChatGptPromptStager.ps1 -PromptFile .\prompts\next.txt
#>

[CmdletBinding()]
param(
    [string]$Prompt = "",
    [string]$PromptFile = "",
    [string]$ChatUrl = "https://chatgpt.com/",
    [string]$ProfileDir = "",
    [string]$AuditDir = "",
    [string]$ChromePath = "",
    [switch]$NoClipboard,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-PromptText {
    param(
        [string]$InlinePrompt,
        [string]$FilePath
    )

    $hasPrompt = -not [string]::IsNullOrWhiteSpace($InlinePrompt)
    $hasFile = -not [string]::IsNullOrWhiteSpace($FilePath)

    if ($hasPrompt -and $hasFile) {
        throw "Provide either -Prompt or -PromptFile, not both."
    }
    if (-not $hasPrompt -and -not $hasFile) {
        throw "Provide one operator-approved prompt with -Prompt or -PromptFile."
    }

    if ($hasFile) {
        $resolved = Resolve-Path -LiteralPath $FilePath
        return [System.IO.File]::ReadAllText($resolved.Path)
    }

    return $InlinePrompt
}

function Get-DefaultChromePath {
    $candidates = @(
        (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
        (Join-Path $env:LocalAppData "Google\Chrome\Application\chrome.exe")
    )

    foreach ($candidate in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return $candidate
        }
    }

    throw "Chrome executable was not found. Install Chrome or pass -ChromePath."
}

function Get-Sha256Hex {
    param([string]$Text)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        $hash = $sha.ComputeHash($bytes)
        return ([System.BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

$repoRoot = Resolve-RepoRoot
if ([string]::IsNullOrWhiteSpace($ProfileDir)) {
    $ProfileDir = Join-Path $repoRoot ".local\chatgpt-chrome-profile"
}
if ([string]::IsNullOrWhiteSpace($AuditDir)) {
    $AuditDir = Join-Path $repoRoot "logs\chatgpt-prompt-stager"
}
if ([string]::IsNullOrWhiteSpace($ChromePath)) {
    $ChromePath = Get-DefaultChromePath
}
elseif (-not (Test-Path -LiteralPath $ChromePath -PathType Leaf)) {
    throw "ChromePath does not exist: $ChromePath"
}

$promptText = Get-PromptText -InlinePrompt $Prompt -FilePath $PromptFile
if ([string]::IsNullOrWhiteSpace($promptText)) {
    throw "Prompt text is empty after reading input."
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null
New-Item -ItemType Directory -Force -Path $AuditDir | Out-Null

$now = Get-Date
$audit = [ordered]@{
    timestamp = $now.ToString("o")
    tool = "Start-LocalChatGptPromptStager.ps1"
    mode = if ($DryRun) { "dry-run" } else { "stage" }
    chatUrl = $ChatUrl
    chromePath = $ChromePath
    profileDir = $ProfileDir
    promptSource = if ([string]::IsNullOrWhiteSpace($PromptFile)) { "inline" } else { "file" }
    promptLength = $promptText.Length
    promptSha256 = Get-Sha256Hex -Text $promptText
    clipboardPrepared = $false
    browserStarted = $false
    stoppedBeforeSend = $true
    autoSend = $false
    responseScraping = $false
    queueMovement = $false
    agentDispatch = $false
}

if (-not $DryRun) {
    if (-not $NoClipboard) {
        Set-Clipboard -Value $promptText
        $audit.clipboardPrepared = $true
    }

    $arguments = @(
        "--user-data-dir=$ProfileDir",
        "--profile-directory=Default",
        "--new-window",
        $ChatUrl
    )
    Start-Process -FilePath $ChromePath -ArgumentList $arguments | Out-Null
    $audit.browserStarted = $true
}

$auditPath = Join-Path $AuditDir ("prompt-stager-{0}.json" -f $now.ToString("yyyyMMdd-HHmmss"))
($audit | ConvertTo-Json -Depth 8) | Set-Content -Encoding UTF8 -Path $auditPath

$result = [ordered]@{
    ok = $true
    auditPath = $auditPath
    profileDir = $ProfileDir
    promptLength = $promptText.Length
    promptSha256 = $audit.promptSha256
    clipboardPrepared = $audit.clipboardPrepared
    browserStarted = $audit.browserStarted
    stoppedBeforeSend = $true
    nextHumanAction = if ($audit.clipboardPrepared) { "Paste the prompt into ChatGPT, review it, then click Send manually only if correct." } else { "Open ChatGPT, paste/type the approved prompt, review it, then click Send manually only if correct." }
}

$result | ConvertTo-Json -Depth 8
