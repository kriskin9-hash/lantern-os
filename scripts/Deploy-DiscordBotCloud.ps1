param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$CloudProvider = "local",
    [string]$Environment = "production",
    [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== Discord Bot Cloud Deployment ===" -ForegroundColor Cyan
Write-Host "Provider: $CloudProvider"
Write-Host "Environment: $Environment"
Write-Host ""

# Validate Docker is available
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker detected: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker first." -ForegroundColor Red
    exit 1
}

# Check for Discord bot token
$discordToken = $env:DISCORD_BOT_TOKEN
if ([string]::IsNullOrEmpty($discordToken)) {
    Write-Host "✗ DISCORD_BOT_TOKEN environment variable not set" -ForegroundColor Red
    Write-Host "Please set it with: `$env:DISCORD_BOT_TOKEN = 'your-bot-token'" -ForegroundColor Yellow
    exit 1
}

# Build Docker image if not skipped
if (-not $SkipBuild) {
    Write-Host "Building Discord Bot Docker image..." -ForegroundColor Yellow
    $dockerfile = Join-Path $Root "ops\Dockerfile-discord-bot"
    $context = Join-Path $Root "src\discord_lounge_bot"
    $requirementsFile = Join-Path $Root "ops\requirements-discord-bot.txt"
    
    # Ensure requirements file exists
    if (-not (Test-Path $requirementsFile)) {
        Write-Host "Creating requirements file..." -ForegroundColor Yellow
        "discord.py>=2.3.2`nrequests>=2.31.0" | Set-Content -LiteralPath $requirementsFile -Encoding UTF8
    }
    
    if (-not (Test-Path $dockerfile)) {
        Write-Host "✗ Dockerfile not found: $dockerfile" -ForegroundColor Red
        exit 1
    }
    
    docker build -t discord-lounge-bot:latest -f $dockerfile --build-arg REQ_FILE=$requirementsFile $Root
    Write-Host "✓ Docker image built successfully" -ForegroundColor Green
}

# Deploy based on provider
switch ($CloudProvider) {
    "local" {
        Write-Host "Deploying to local Docker..." -ForegroundColor Yellow
        
        # Run Discord bot container
        $containerName = "discord-lounge-bot-cloud"
        
        # Stop existing container if running
        $existingContainer = docker ps -q -f name=$containerName
        if ($existingContainer) {
            Write-Host "Stopping existing container..." -ForegroundColor Yellow
            docker stop $containerName | Out-Null
            docker rm $containerName | Out-Null
        }
        
        # Run new container
        $envVars = @(
            "DISCORD_BOT_TOKEN=$discordToken",
            "LANTERN_DISCORD_GUILD_ID=$env:LANCERN_DISCORD_GUILD_ID",
            "LANTERN_DISCORD_CHANNEL_ID=$env:LANCERN_DISCORD_CHANNEL_ID",
            "LANTERN_STATUS_URL=http://host.docker.internal:4177/api/status",
            "LANTERN_CLOUD_MODE=true"
        )
        
        $envVarString = $envVars -join " -e "
        
        docker run -d `
            --name $containerName `
            --restart unless-stopped `
            -e $envVarString `
            discord-lounge-bot:latest
            
        Write-Host "✓ Discord bot deployed locally" -ForegroundColor Green
    }
    
    "heroku" {
        Write-Host "Deploying to Heroku..." -ForegroundColor Yellow
        Write-Host "⚠ Heroku deployment requires additional setup" -ForegroundColor Yellow
        Write-Host "Please configure Heroku CLI and run:" -ForegroundColor Yellow
        Write-Host "heroku create lantern-discord-bot" -ForegroundColor Gray
        Write-Host "heroku container:push discord-lounge-bot --app lantern-discord-bot" -ForegroundColor Gray
        Write-Host "heroku container:release web --app lantern-discord-bot" -ForegroundColor Gray
    }
    
    default {
        Write-Host "✗ Unknown cloud provider: $CloudProvider" -ForegroundColor Red
        exit 1
    }
}

# Check container status
Write-Host "Checking container status..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    $containerStatus = docker ps -f name=discord-lounge-bot-cloud --format "{{.Status}}"
    Write-Host "✓ Container status: $containerStatus" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not determine container status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Deployment Summary ===" -ForegroundColor Cyan
Write-Host "Provider: $CloudProvider"
Write-Host "Environment: $Environment"
Write-Host "Status: Deployed"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Verify Discord bot is online in your server"
Write-Host "2. Test !lantern-status command in configured channel"
Write-Host "3. Check container logs: docker logs discord-lounge-bot-cloud"
Write-Host ""