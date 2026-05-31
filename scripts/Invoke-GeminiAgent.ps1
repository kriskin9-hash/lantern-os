# ================================================
# Lantern OS - Gemini Agent CLI v1.0
# Free-tier Gemini 1.5 Flash (cheapest) or 2.5 Flash
# Bill-accountable with JSONL usage logging
# ================================================

<#
.SYNOPSIS
    CLI for the Lantern OS Gemini agent slot.
.DESCRIPTION
    Calls Google AI Studio Gemini API using free tier.
    Logs every request with token count and estimated cost for accountability.
    Requires GEMINI_API_KEY environment variable.
    Free tier limits: 60 req/min, 1,000 req/day, no credit card.
.PARAMETER Prompt
    The prompt to send to Gemini.
.PARAMETER Model
    Gemini model name. Default: gemini-1.5-flash (cheapest).
    Options: gemini-1.5-flash, gemini-2.5-flash-preview-05-20
.PARAMETER MaxOutputTokens
    Maximum output tokens. Default: 1024.
.PARAMETER Temperature
    Sampling temperature. Default: 0.7.
.PARAMETER ShowUsage
    Display current billing/usage summary.
.EXAMPLE
    $env:GEMINI_API_KEY = "your-free-key-from-ai-studio"
    .\Invoke-GeminiAgent.ps1 -Prompt "Summarize the current repo state"
    .\Invoke-GeminiAgent.ps1 -ShowUsage
.NOTES
    Get free API key: https://aistudio.google.com/app/apikey
#>

param(
    [string]$Prompt = "",
    [string]$Model = "gemini-1.5-flash",
    [int]$MaxOutputTokens = 1024,
    [double]$Temperature = 0.7,
    [switch]$ShowUsage = $false,
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# ─── CONFIG ────────────────────────────────────

$ApiBase = "https://generativelanguage.googleapis.com/v1beta"
$UsageLog = "data/gemini-usage.jsonl"
$ApiKey = $env:GEMINI_API_KEY

# Pricing per 1M tokens (for accountability even on free tier)
$Pricing = @{
    "gemini-1.5-flash"             = @{ input = 0.075; output = 0.30 }
    "gemini-2.5-flash-preview-05-20" = @{ input = 0.15;  output = 0.60 }
    "gemini-1.5-pro"               = @{ input = 1.25;  output = 5.00 }
}

# ─── USAGE LOGGING ─────────────────────────────

function Get-UsageLogPath {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $path = Join-Path $repoRoot $UsageLog
    New-Item -ItemType Directory -Force -Path (Split-Path $path) | Out-Null
    return $path
}

function Get-UsageSummary {
    $path = Get-UsageLogPath
    if (-not (Test-Path $path)) { return @{ totalRequests = 0; totalInputTokens = 0; totalOutputTokens = 0; estimatedCostUsd = 0.0; freeTierLimit = "1,000 req/day" } }
    
    $entries = Get-Content $path | ForEach-Object { $_ | ConvertFrom-Json }
    $inputTokens = ($entries | Measure-Object -Property inputTokens -Sum).Sum
    $outputTokens = ($entries | Measure-Object -Property outputTokens -Sum).Sum
    $cost = ($entries | Measure-Object -Property estimatedCostUsd -Sum).Sum
    
    return @{
        totalRequests      = $entries.Count
        totalInputTokens   = $inputTokens
        totalOutputTokens  = $outputTokens
        estimatedCostUsd   = [math]::Round($cost, 4)
        freeTierLimit      = "1,000 req/day | 60 req/min"
        status             = if ($entries.Count -ge 1000) { "WARNING: approaching daily limit" } else { "OK" }
    }
}

function Write-UsageEntry {
    param([string]$ModelName, [int]$InputTokens, [int]$OutputTokens, [string]$Status, [string]$PromptPreview)
    
    $price = $Pricing[$ModelName]
    if (-not $price) { $price = $Pricing["gemini-1.5-flash"] }
    
    $inputCost = ($InputTokens / 1e6) * $price.input
    $outputCost = ($OutputTokens / 1e6) * $price.output
    $totalCost = [math]::Round($inputCost + $outputCost, 6)
    
    $entry = @{
        timestamp        = Get-Date -Format "o"
        model            = $ModelName
        inputTokens      = $InputTokens
        outputTokens     = $OutputTokens
        estimatedCostUsd = $totalCost
        status           = $Status
        promptPreview    = if ($PromptPreview.Length -gt 80) { $PromptPreview.Substring(0, 80) + "..." } else { $PromptPreview }
    }
    
    $entry | ConvertTo-Json -Compress | Add-Content -Path (Get-UsageLogPath) -Encoding UTF8
    return $totalCost
}

# ─── API CALL ──────────────────────────────────

function Invoke-GeminiApi {
    param([string]$Key, [string]$ModelName, [string]$UserPrompt, [int]$MaxTokens, [double]$Temp)
    
    $url = "{0}/models/{1}:generateContent?key={2}" -f $ApiBase, $ModelName, $Key
    
    $body = @{
        contents = @(@{
            parts = @(@{ text = $UserPrompt })
        })
        generationConfig = @{
            maxOutputTokens = $MaxTokens
            temperature     = $Temp
        }
    } | ConvertTo-Json -Depth 5
    
    $resp = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"
    return $resp
}

# ─── MAIN ──────────────────────────────────────

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "     LANTERN OS - GEMINI AGENT CLI v1.0" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($ShowUsage) {
    $summary = Get-UsageSummary
    Write-Host "`n=== GEMINI USAGE SUMMARY ===" -ForegroundColor Yellow
    Write-Host "  Total Requests:     $($summary.totalRequests)" -ForegroundColor White
    Write-Host "  Input Tokens:       $($summary.totalInputTokens)" -ForegroundColor White
    Write-Host "  Output Tokens:      $($summary.totalOutputTokens)" -ForegroundColor White
    Write-Host "  Est. Cost (USD):    `$ $($summary.estimatedCostUsd)" -ForegroundColor White
    Write-Host "  Free Tier Limit:    $($summary.freeTierLimit)" -ForegroundColor Green
    Write-Host "  Status:             $($summary.status)" -ForegroundColor $(if ($summary.status -like "OK*") { "Green" } else { "Red" })
    Write-Host "`nLog: $UsageLog" -ForegroundColor Gray
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Prompt)) {
    Write-Host "`nERROR: -Prompt is required (unless using -ShowUsage)." -ForegroundColor Red
    Write-Host "Usage: .\Invoke-GeminiAgent.ps1 -Prompt 'Your prompt here'" -ForegroundColor Gray
    Write-Host "Get free key: https://aistudio.google.com/app/apikey" -ForegroundColor Gray
    exit 1
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    Write-Host "`nERROR: GEMINI_API_KEY environment variable not set." -ForegroundColor Red
    Write-Host "Set it with: `$env:GEMINI_API_KEY = 'your-key-here'" -ForegroundColor Yellow
    Write-Host "Get free key: https://aistudio.google.com/app/apikey" -ForegroundColor Gray
    exit 1
}

Write-Host "`nModel: $Model" -ForegroundColor Cyan
Write-Host "Prompt: $Prompt" -ForegroundColor Gray
if ($DryRun) {
    Write-Host "`nDRY RUN: Would send request to Gemini API." -ForegroundColor Yellow
    exit 0
}

try {
    Write-Host "`nSending request..." -ForegroundColor Yellow
    $response = Invoke-GeminiApi -Key $ApiKey -ModelName $Model -UserPrompt $Prompt -MaxTokens $MaxOutputTokens -Temp $Temperature
    
    $text = $response.candidates[0].content.parts[0].text
    $inputTokens = $response.usageMetadata.promptTokenCount
    $outputTokens = $response.usageMetadata.candidatesTokenCount
    
    $cost = Write-UsageEntry -ModelName $Model -InputTokens $inputTokens -OutputTokens $outputTokens -Status "success" -PromptPreview $Prompt
    
    Write-Host "`n=== RESPONSE ===" -ForegroundColor Green
    Write-Host $text -ForegroundColor White
    Write-Host "`n=== USAGE ===" -ForegroundColor Yellow
    Write-Host "  Input tokens:  $inputTokens" -ForegroundColor Gray
    Write-Host "  Output tokens: $outputTokens" -ForegroundColor Gray
    Write-Host "  Est. cost:     `$ $cost" -ForegroundColor Gray
    
} catch {
    Write-Error "Gemini API call failed: $_"
    Write-UsageEntry -ModelName $Model -InputTokens 0 -OutputTokens 0 -Status "error: $($_.Exception.Message)" -PromptPreview $Prompt | Out-Null
    exit 1
}
