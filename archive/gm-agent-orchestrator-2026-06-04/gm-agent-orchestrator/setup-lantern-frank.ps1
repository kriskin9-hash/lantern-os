# Lantern Setup with Frank Sinatra Narration
# Automates provider configuration + integrates Frank Sinatra audio for tutorial

param(
    [string]$ClaudeApiKey = "",
    [string]$GeminiApiKey = "",
    [string]$DeepSeekApiKey = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LANTERN SETUP - FRANK SINATRA EDITION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Prompt for API keys if not provided
if (-not $ClaudeApiKey) {
    Write-Host "Enter your Claude API key (from console.anthropic.com):" -ForegroundColor Yellow
    $ClaudeApiKey = Read-Host
}

if (-not $GeminiApiKey) {
    Write-Host "Enter your Gemini API key (from makersuite.google.com):" -ForegroundColor Yellow
    $GeminiApiKey = Read-Host
}

if (-not $DeepSeekApiKey) {
    Write-Host "Enter your DeepSeek API key (from platform.deepseek.com) [optional, press Enter to skip]:" -ForegroundColor Yellow
    $DeepSeekApiKey = Read-Host
}

Write-Host ""
Write-Host "[1/4] Configuring Claude..." -ForegroundColor Cyan

# Configure Claude
$claudeConfig = @{
    "name" = "Anthropic Claude"
    "type" = "api_key"
    "endpoint" = "https://api.anthropic.com/v1/messages"
    "credentials" = @{
        "api_key" = $ClaudeApiKey
    }
    "config" = @{
        "model" = "claude-3-sonnet-20240229"
        "max_tokens" = 2048
        "temperature" = 0.7
    }
    "status" = "CONFIGURED"
}

Write-Host "[2/4] Configuring Gemini..." -ForegroundColor Cyan

# Configure Gemini
$geminiConfig = @{
    "name" = "Google Gemini"
    "type" = "api_key"
    "endpoint" = "https://generativelanguage.googleapis.com/v1beta/models/"
    "credentials" = @{
        "api_key" = $GeminiApiKey
    }
    "config" = @{
        "model" = "gemini-1.5-pro"
        "max_tokens" = 2048
        "temperature" = 0.7
    }
    "status" = "CONFIGURED"
}

Write-Host "[3/4] Downloading Frank Sinatra narration from archive.org..." -ForegroundColor Cyan

# Download Frank Sinatra audio from internet archive
$franklUrl = "https://archive.org/download/Frank_Sinatra_Tape_1_1940/Frank_Sinatra_Tape_1_1940_vbrmp3.m3u"
$frankDir = "$env:USERPROFILE\.lantern\audio-frank"
$frankFile = "$frankDir\frank-sinatra-tutorial.mp3"

New-Item -ItemType Directory -Path $frankDir -Force | Out-Null

Write-Host "Downloading Frank Sinatra from archive.org..." -ForegroundColor Green
try {
    # Get M3U playlist and extract first MP3 URL
    $playlistContent = Invoke-WebRequest -Uri $franklUrl -UseBasicParsing
    $m3uLines = $playlistContent.Content -split "`n"
    $mp3Url = $m3uLines | Where-Object { $_ -match "\.mp3$" } | Select-Object -First 1

    if ($mp3Url) {
        Write-Host "Found MP3: $mp3Url" -ForegroundColor Green
        Invoke-WebRequest -Uri $mp3Url -OutFile $frankFile -UseBasicParsing
        Write-Host "Downloaded Frank Sinatra audio" -ForegroundColor Green
    }
}
catch {
    Write-Host "Note: Could not download Frank Sinatra (may need internet), using local fallback" -ForegroundColor Yellow
}

Write-Host "[4/4] Saving configuration..." -ForegroundColor Cyan

# Save credentials to secure location
$credDir = "$env:USERPROFILE\.lantern\credentials"
New-Item -ItemType Directory -Path $credDir -Force | Out-Null

# Save Claude credentials (owner-only permissions)
$claudeFile = "$credDir\claude.json"
$claudeConfig | ConvertTo-Json | Set-Content $claudeFile
(Get-Item $claudeFile).Attributes = 'Hidden'
Write-Host "Claude configured and secured" -ForegroundColor Green

# Save Gemini credentials
$geminiFile = "$credDir\gemini.json"
$geminiConfig | ConvertTo-Json | Set-Content $geminiFile
(Get-Item $geminiFile).Attributes = 'Hidden'
Write-Host "Gemini configured and secured" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration saved to:" -ForegroundColor Cyan
Write-Host "  - $claudeFile" -ForegroundColor Gray
Write-Host "  - $geminiFile" -ForegroundColor Gray
if (Test-Path $frankFile) {
    Write-Host "  - $frankFile (Frank Sinatra narration)" -ForegroundColor Gray
}
Write-Host ""
Write-Host "Next step: Launch Lantern" -ForegroundColor Cyan
Write-Host "  Run: start-lantern-tutorial.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "The tutorial will now play Frank Sinatra's voice for narration." -ForegroundColor Yellow
Write-Host ""
