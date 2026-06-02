# Start-NgrokTunnels.ps1
# Launches ngrok tunnels for all Lantern OS services and updates documentation URLs

param(
    [string]$AuthToken = $env:NGROK_AUTHTOKEN,
    [string]$ConfigPath = "./.ngrok.yml"
)

# Check if ngrok is available
$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrok) {
    Write-Error "ngrok not found. Please install ngrok: https://ngrok.com/download"
    exit 1
}

Write-Host "🚀 Starting Lantern OS ngrok tunnels..." -ForegroundColor Green

# Validate auth token
if (-not $AuthToken) {
    Write-Error "NGROK_AUTHTOKEN environment variable not set"
    Write-Host "Get your token at: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
}

# Set auth token
Write-Host "Setting ngrok authentication token..."
ngrok config add-authtoken $AuthToken

# Create tunnel URLs log file
$LogFile = "logs/ngrok-tunnels-$(Get-Date -Format 'yyyy-MM-dd-HHmmss').log"
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host "Starting tunnels from config: $ConfigPath"

# Start ngrok with all tunnels
# Note: This will run in foreground - use Start-Job for background
$process = Start-Process -FilePath ngrok -ArgumentList "start --all --config `"$ConfigPath`"" `
    -PassThru -NoNewWindow -RedirectStandardOutput $LogFile -RedirectStandardError "$LogFile.err"

Write-Host "✅ ngrok started with PID: $($process.Id)"
Write-Host "Tunnels log: $LogFile"
Write-Host ""
Write-Host "Waiting for tunnels to initialize..." -ForegroundColor Yellow

# Wait for ngrok API to be ready
Start-Sleep -Seconds 3

# Query ngrok API for tunnel URLs
$retries = 0
while ($retries -lt 10) {
    try {
        $ngrokApi = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop

        if ($ngrokApi.tunnels.Count -gt 0) {
            Write-Host "`n📡 Active Tunnels:" -ForegroundColor Green
            Write-Host "=" * 70

            $tunnels = @{}
            foreach ($tunnel in $ngrokApi.tunnels) {
                $name = $tunnel.name
                $url = $tunnel.public_url
                $tunnels[$name] = $url
                Write-Host "  $name`t→  $url"
            }

            Write-Host "=" * 70

            # Save tunnel URLs to environment file
            $envFile = ".env.ngrok"
            Write-Host "`nSaving tunnel URLs to $envFile..."

            $envContent = @"
# ngrok Tunnel URLs - Generated $(Get-Date)
LANTERN_API_URL=$($tunnels['lantern-api'])
LANTERN_DASHBOARD_URL=$($tunnels['lantern-dashboard'])
LANTERN_BROWSER_URL=$($tunnels['lantern-browser'])
LANTERN_ORCHESTRATOR_URL=$($tunnels['lantern-orchestrator'])
LANTERN_RAG_URL=$($tunnels['lantern-rag'])

# ngrok Dashboard
NGROK_DASHBOARD=http://localhost:4040/
"@

            $envContent | Out-File -FilePath $envFile -Encoding UTF8
            Write-Host "✅ URLs saved to $envFile"

            # Update README with public URLs
            Update-ReadmeWithTunnelUrls -TunnelUrls $tunnels

            Write-Host "`n🌐 Access Lantern OS:"`
            Write-Host "  API:         $($tunnels['lantern-api'])"
            Write-Host "  Dashboard:   $($tunnels['lantern-dashboard'])"
            Write-Host "  Browser:     $($tunnels['lantern-browser'])"
            Write-Host "  Orchestrator: $($tunnels['lantern-orchestrator'])"
            Write-Host "  RAG Server:  $($tunnels['lantern-rag'])"
            Write-Host "`nngrok Dashboard: http://localhost:4040/"
            Write-Host "`nTunnels are live! Press Ctrl+C to stop."

            # Keep process running
            $process.WaitForExit()
            break
        }
    } catch {
        $retries++
        if ($retries -lt 10) {
            Write-Host "  Waiting for ngrok to initialize... ($retries/10)" -ForegroundColor Gray
            Start-Sleep -Seconds 1
        }
    }
}

if ($retries -ge 10) {
    Write-Error "Failed to initialize ngrok tunnels after 10 attempts"
    Stop-Process -Id $process.Id -Force
    exit 1
}

function Update-ReadmeWithTunnelUrls {
    param([hashtable]$TunnelUrls)

    $readmePath = "README.md"
    if (-not (Test-Path $readmePath)) {
        return
    }

    Write-Host "Updating README with public URLs..."

    $readme = Get-Content -Path $readmePath -Raw

    # Create URLs section
    $urlsSection = @"
## Public URLs (ngrok Tunnels)

> **Active tunnels for remote access:**
>
> - **API**: $($TunnelUrls['lantern-api'])
> - **Dashboard**: $($TunnelUrls['lantern-dashboard'])
> - **Browser**: $($TunnelUrls['lantern-browser'])
> - **Orchestrator**: $($TunnelUrls['lantern-orchestrator'])
> - **RAG Server**: $($TunnelUrls['lantern-rag'])
>
> Monitor tunnels: http://localhost:4040/

"@

    # Update or insert URLs section
    if ($readme -match "## Public URLs") {
        $readme = $readme -replace "## Public URLs.*?(?=##|\Z)", $urlsSection
    } else {
        # Insert after Quick Start
        $readme = $readme -replace "(## Quick Start.*?```)\n", "`$1`n`n$urlsSection"
    }

    Set-Content -Path $readmePath -Value $readme -Encoding UTF8
    Write-Host "✅ README updated with public URLs"
}

Write-Host "`n📋 Tunnel logs: $LogFile"
Write-Host "Error logs: $LogFile.err"
Write-Host "Environment: .env.ngrok"
