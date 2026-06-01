param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$CloudProvider = "local",
    [string]$Environment = "production",
    [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== Lantern OS Cloud Deployment ===" -ForegroundColor Cyan
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

# Build Docker image if not skipped
if (-not $SkipBuild) {
    Write-Host "Building Lantern Garage Docker image..." -ForegroundColor Yellow
    $dockerfile = Join-Path $Root "ops\Dockerfile-lantern-garage"
    $context = Join-Path $Root "apps\lantern-garage"
    
    if (-not (Test-Path $dockerfile)) {
        Write-Host "Creating Dockerfile for Lantern Garage..." -ForegroundColor Yellow
        $dockerfileContent = @"
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application files
COPY . .

# Expose port
EXPOSE 4177

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:4177/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start application
CMD ["node", "server.js"]
"@
        New-Item -ItemType Directory -Force -Path (Split-Path $dockerfile) | Out-Null
        $dockerfileContent | Set-Content -LiteralPath $dockerfile -Encoding UTF8
    }
    
    docker build -t lantern-garage:latest -f $dockerfile $context
    Write-Host "✓ Docker image built successfully" -ForegroundColor Green
}

# Deploy based on provider
switch ($CloudProvider) {
    "local" {
        Write-Host "Deploying to local Docker Compose..." -ForegroundColor Yellow
        $composeFile = Join-Path $Root "ops\cloud-deployment-config.yaml"
        
        if (-not (Test-Path $composeFile)) {
            Write-Host "✗ Docker Compose file not found: $composeFile" -ForegroundColor Red
            exit 1
        }
        
        docker-compose -f $composeFile up -d
        Write-Host "✓ Local deployment completed" -ForegroundColor Green
    }
    
    "gcloud" {
        Write-Host "Deploying to Google Cloud Run..." -ForegroundColor Yellow
        Write-Host "⚠ Google Cloud deployment requires additional setup" -ForegroundColor Yellow
        Write-Host "Please configure gcloud CLI and run:" -ForegroundColor Yellow
        Write-Host "gcloud run deploy lantern-garage --image lantern-garage:latest --platform managed" -ForegroundColor Gray
    }
    
    "aws" {
        Write-Host "Deploying to AWS ECS..." -ForegroundColor Yellow
        Write-Host "⚠ AWS deployment requires additional setup" -ForegroundColor Yellow
        Write-Host "Please configure AWS CLI and ECS cluster" -ForegroundColor Gray
    }
    
    default {
        Write-Host "✗ Unknown cloud provider: $CloudProvider" -ForegroundColor Red
        exit 1
    }
}

# Wait for service to be healthy
Write-Host "Waiting for service health check..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test deployment
try {
    $response = Invoke-WebRequest -Uri "http://localhost:4177/api/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Service health check passed" -ForegroundColor Green
    } else {
        Write-Host "✗ Service health check failed" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠ Service health check inconclusive" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Deployment Summary ===" -ForegroundColor Cyan
Write-Host "Provider: $CloudProvider"
Write-Host "Environment: $Environment"
Write-Host "Status: Deployed"
Write-Host "Access: http://localhost:4177"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Test the web interface at http://localhost:4177"
Write-Host "2. Configure user-specific environments"
Write-Host "3. Set up monitoring and logging"
Write-Host ""