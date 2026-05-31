param(
    [string]$LanternRoot = "C:\tmp\lantern-os",
    [switch]$SkipTradeChat,
    [switch]$SkipBrowser,
    [int]$GaragePort = 4177,
    [int]$TradeChatPort = 8080
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Lantern OS Full Stack Startup"         -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---- Validation ----
if (-not (Test-Path -LiteralPath $LanternRoot)) {
    Write-Host "ERROR: LanternRoot not found: $LanternRoot" -ForegroundColor Red
    Write-Host "Clone the repo first:"
    Write-Host "  git clone https://github.com/alex-place/lantern-os.git C:\tmp\lantern-os"
    exit 1
}

$nodeOk   = $null -ne (Get-Command node   -ErrorAction SilentlyContinue)
$npmOk    = $null -ne (Get-Command npm    -ErrorAction SilentlyContinue)
$pythonOk = $null -ne (Get-Command python -ErrorAction SilentlyContinue)

if (-not $nodeOk) {
    Write-Host "ERROR: node.exe not found. Install Node.js 20+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}
if (-not $npmOk) {
    Write-Host "ERROR: npm not found. Reinstall Node.js." -ForegroundColor Red
    exit 1
}

Write-Host "Prerequisites:" -ForegroundColor Green
Write-Host "  node.js: $(node --version)"
if ($pythonOk) { Write-Host "  python:  $(python --version)" }
Write-Host ""

# ---- Install node deps if needed ----
$modulesPath = Join-Path $LanternRoot "apps\lantern-garage\node_modules"
if (-not (Test-Path -LiteralPath $modulesPath)) {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
    Push-Location (Join-Path $LanternRoot "apps\lantern-garage")
    npm install
    Pop-Location
    Write-Host "  Done." -ForegroundColor Green
}

# ---- Kill anything already on these ports ----
foreach ($port in @($GaragePort, 3000)) {
    $pids = @(netstat -ano 2>$null | Select-String ":$port\s" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Where-Object { $_ -match '^\d+$' } | Sort-Object -Unique)
    foreach ($pid in $pids) {
        try { Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue } catch {}
    }
}

# ---- Start Lantern Garage ----
Write-Host "Starting Lantern Garage on port $GaragePort..." -ForegroundColor Cyan
$garageProc = Start-Process -FilePath "node" `
    -ArgumentList "apps\lantern-garage\server.js" `
    -WorkingDirectory $LanternRoot `
    -PassThru `
    -WindowStyle Minimized

Write-Host "  PID: $($garageProc.Id)"

# Wait for Lantern Garage to respond
$garageUrl = "http://127.0.0.1:$GaragePort/api/health"
$maxWait = 15
$waited  = 0
Write-Host "  Waiting for Lantern Garage..." -NoNewline
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    $waited++
    Write-Host "." -NoNewline
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri $garageUrl -TimeoutSec 2
        if ($r.StatusCode -eq 200) { break }
    } catch {}
}
Write-Host ""

try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $garageUrl -TimeoutSec 2
    if ($r.StatusCode -eq 200) {
        Write-Host "  Lantern Garage: ONLINE at http://127.0.0.1:$GaragePort" -ForegroundColor Green
    } else {
        Write-Host "  Lantern Garage: started but health returned $($r.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Lantern Garage: may still be starting up ($($_.Exception.Message))" -ForegroundColor Yellow
}

# ---- Trade Chat (optional) ----
$tradeChatStarted = $false
if (-not $SkipTradeChat) {
    $tradePath = Join-Path $LanternRoot "apps\lantern-trade-chat"
    $envPath   = Join-Path $tradePath ".env"
    $venvPath  = Join-Path $tradePath ".venv\Scripts\python.exe"

    if (-not (Test-Path -LiteralPath $envPath)) {
        Write-Host ""
        Write-Host "Trade Chat: Skipping — .env file not configured" -ForegroundColor Yellow
        Write-Host "  To enable trading, create: $envPath"
        Write-Host "  With: KALSHI_API_KEY_ID, KALSHI_PRIVATE_KEY, GITHUB_OAUTH_CLIENT_ID, GITHUB_OAUTH_CLIENT_SECRET"
    } elseif (-not $pythonOk -and -not (Test-Path -LiteralPath $venvPath)) {
        Write-Host ""
        Write-Host "Trade Chat: Skipping — Python not found" -ForegroundColor Yellow
        Write-Host "  Install Python 3.8+ from https://python.org"
    } else {
        Write-Host ""
        Write-Host "Starting Trade Chat on port $TradeChatPort..." -ForegroundColor Cyan

        $pythonExe = if (Test-Path -LiteralPath $venvPath) { $venvPath } else { "python" }

        # Install deps if venv doesn't exist
        if (-not (Test-Path -LiteralPath $venvPath)) {
            Write-Host "  Setting up Python venv..."
            Push-Location $tradePath
            python -m venv .venv
            & ".\.venv\Scripts\pip.exe" install -e . -q
            Pop-Location
            $pythonExe = $venvPath
        }

        $tradeChatProc = Start-Process -FilePath $pythonExe `
            -ArgumentList "-m", "uvicorn", "app.main:app", "--port", $TradeChatPort `
            -WorkingDirectory $tradePath `
            -PassThru `
            -WindowStyle Minimized

        Write-Host "  PID: $($tradeChatProc.Id)"

        Start-Sleep -Seconds 3
        try {
            $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$TradeChatPort/api/health" -TimeoutSec 3
            if ($r.StatusCode -eq 200) {
                Write-Host "  Trade Chat: ONLINE at http://127.0.0.1:$TradeChatPort" -ForegroundColor Green
                $tradeChatStarted = $true
            }
        } catch {
            Write-Host "  Trade Chat: starting up (may take a few more seconds)" -ForegroundColor Yellow
        }
    }
}

# ---- Run confidence report ----
Write-Host ""
Write-Host "Running confidence report..." -ForegroundColor Cyan
$reportScript = Join-Path $LanternRoot "scripts\Build-LanternConfidenceReport.ps1"
if (Test-Path -LiteralPath $reportScript) {
    $reportJson = & $reportScript -LanternRoot $LanternRoot -WriteReceipt 2>$null
    try {
        $report = $reportJson | ConvertFrom-Json
        Write-Host ""
        Write-Host "Feature Confidence:" -ForegroundColor White
        foreach ($f in $report.features) {
            $score = if ($null -ne $f.confidenceScore) { "$($f.confidenceScore * 100)%" } else { " N/A" }
            $color = if ($f.confidenceScore -ge 0.80) { "Green" } elseif ($f.confidenceScore) { "Yellow" } else { "DarkGray" }
            Write-Host ("  {0,-42} {1,5}  {2}" -f $f.name, $score, $f.status) -ForegroundColor $color
        }
        Write-Host ""
        $gl = $report.summary.greenLight
        if ($gl) {
            Write-Host "  Overall Confidence: $($report.summary.overallConfidence * 100)% — GREEN LIGHT" -ForegroundColor Green
        } else {
            Write-Host "  Overall Confidence: $($report.summary.overallConfidence * 100)% — needs attention" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  (Could not parse report output)" -ForegroundColor DarkGray
    }
}

# ---- Summary ----
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Stack Summary"                         -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Lantern Garage:  http://127.0.0.1:$GaragePort"
Write-Host "  Imagniverse:     http://127.0.0.1:$GaragePort/imagniverse"
Write-Host "  Dreamer:         http://127.0.0.1:$GaragePort (sidebar)"
if ($tradeChatStarted) {
    Write-Host "  Trade Chat:      http://127.0.0.1:$TradeChatPort  [paper/demo mode]"
} else {
    Write-Host "  Trade Chat:      not started (see above)"
}
Write-Host ""
Write-Host "  Confidence Report: manifests/validation/LANTERN-CONFIDENCE-LATEST.json"
Write-Host ""

# ---- Open browser ----
if (-not $SkipBrowser) {
    Start-Process "http://127.0.0.1:$GaragePort"
}

Write-Host "Press Ctrl+C to stop all services." -ForegroundColor DarkGray
Write-Host ""

# Keep process alive so child processes stay visible
try {
    Wait-Process -Id $garageProc.Id
} catch {
    # Garage process exited or was killed
}
