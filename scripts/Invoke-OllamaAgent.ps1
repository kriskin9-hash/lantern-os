# ================================================
# Lantern OS - Ollama Agent CLI v1.0
# Local inference, zero external cost, no tokens
# ================================================

<#
.SYNOPSIS
    CLI for the Lantern OS Ollama local agent slot.
.DESCRIPTION
    Calls locally-running Ollama API (localhost:11434).
    Runs entirely on operator hardware — zero external API cost.
    Logs usage for accountability even though cost is $0.
.PARAMETER Prompt
    The prompt to send.
.PARAMETER Model
    Ollama model name. Default: mistral.
.PARAMETER ShowUsage
    Display local usage summary.
.PARAMETER PullModel
    Pull the specified model if not present.
.EXAMPLE
    .\Invoke-OllamaAgent.ps1 -Prompt "Summarize repo state"
    .\Invoke-OllamaAgent.ps1 -ShowUsage
.NOTES
    Requires Ollama installed: https://ollama.com/download
#>

param(
    [string]$Prompt = "",
    [string]$Model = "mistral",
    [switch]$ShowUsage = $false,
    [switch]$PullModel = $false,
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

$OllamaBase = "http://localhost:11434"
$UsageLog = "data/ollama-usage.jsonl"

function Get-UsageLogPath {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $path = Join-Path $repoRoot $UsageLog
    New-Item -ItemType Directory -Force -Path (Split-Path $path) | Out-Null
    return $path
}

function Get-UsageSummary {
    $path = Get-UsageLogPath
    if (-not (Test-Path $path)) { return @{ totalRequests = 0; totalPromptChars = 0; totalResponseChars = 0; estimatedCostUsd = 0.0; note = "Local inference = $0 external cost" } }
    $entries = Get-Content $path | ForEach-Object { $_ | ConvertFrom-Json }
    $promptChars = ($entries | Measure-Object -Property promptChars -Sum).Sum
    $responseChars = ($entries | Measure-Object -Property responseChars -Sum).Sum
    return @{ totalRequests = $entries.Count; totalPromptChars = $promptChars; totalResponseChars = $responseChars; estimatedCostUsd = 0.0; note = "Local inference = $0 external cost" }
}

function Write-UsageEntry {
    param([string]$ModelName, [int]$PromptChars, [int]$ResponseChars, [string]$Status)
    $entry = @{
        timestamp = Get-Date -Format "o"
        model = $ModelName
        promptChars = $PromptChars
        responseChars = $ResponseChars
        estimatedCostUsd = 0.0
        status = $Status
    }
    $entry | ConvertTo-Json -Compress | Add-Content -Path (Get-UsageLogPath) -Encoding UTF8
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "     LANTERN OS - OLLAMA AGENT CLI v1.0" -ForegroundColor Cyan
Write-Host "     Local inference | Zero external cost" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($ShowUsage) {
    $summary = Get-UsageSummary
    Write-Host "`n=== OLLAMA USAGE SUMMARY ===" -ForegroundColor Yellow
    Write-Host "  Total Requests:     $($summary.totalRequests)" -ForegroundColor White
    Write-Host "  Prompt Chars:       $($summary.totalPromptChars)" -ForegroundColor White
    Write-Host "  Response Chars:     $($summary.totalResponseChars)" -ForegroundColor White
    Write-Host "  Est. Cost:          `$0 (local)" -ForegroundColor Green
    Write-Host "  Note:               $($summary.note)" -ForegroundColor Green
    exit 0
}

# Check Ollama is running
try {
    $health = Invoke-RestMethod -Uri "$OllamaBase/api/tags" -Method Get -ErrorAction Stop
    Write-Host "`nOllama healthy. Models available:" -ForegroundColor Green
    foreach ($m in $health.models | Select-Object -First 5) {
        Write-Host "  - $($m.name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "`nERROR: Ollama not running on $OllamaBase" -ForegroundColor Red
    Write-Host "Start it with: ollama serve" -ForegroundColor Yellow
    exit 1
}

# Pull model if requested
if ($PullModel) {
    Write-Host "`nPulling model $Model..." -ForegroundColor Yellow
    $pullBody = @{ name = $Model; stream = $false } | ConvertTo-Json
    Invoke-RestMethod -Uri "$OllamaBase/api/pull" -Method Post -Body $pullBody -ContentType "application/json" | Out-Null
    Write-Host "Model pull complete." -ForegroundColor Green
}

if ([string]::IsNullOrWhiteSpace($Prompt)) {
    Write-Host "`nERROR: -Prompt is required (unless using -ShowUsage or -PullModel)." -ForegroundColor Red
    exit 1
}

if ($DryRun) {
    Write-Host "`nDRY RUN: Would send to Ollama model=$Model" -ForegroundColor Yellow
    exit 0
}

Write-Host "`nModel: $Model" -ForegroundColor Cyan
Write-Host "Prompt: $Prompt" -ForegroundColor Gray
Write-Host "`nGenerating..." -ForegroundColor Yellow

try {
    $body = @{
        model = $Model
        prompt = $Prompt
        stream = $false
        options = @{ temperature = 0.7 }
    } | ConvertTo-Json

    $resp = Invoke-RestMethod -Uri "$OllamaBase/api/generate" -Method Post -Body $body -ContentType "application/json"
    $text = $resp.response

    Write-UsageEntry -ModelName $Model -PromptChars $Prompt.Length -ResponseChars $text.Length -Status "success"

    Write-Host "`n=== RESPONSE ===" -ForegroundColor Green
    Write-Host $text -ForegroundColor White
    Write-Host "`n=== USAGE ===" -ForegroundColor Yellow
    Write-Host "  Prompt chars:  $($Prompt.Length)" -ForegroundColor Gray
    Write-Host "  Response chars: $($text.Length)" -ForegroundColor Gray
    Write-Host "  Est. cost:     `$0 (local inference)" -ForegroundColor Gray

} catch {
    Write-Error "Ollama API call failed: $_"
    Write-UsageEntry -ModelName $Model -PromptChars 0 -ResponseChars 0 -Status "error: $($_.Exception.Message)" | Out-Null
    exit 1
}
