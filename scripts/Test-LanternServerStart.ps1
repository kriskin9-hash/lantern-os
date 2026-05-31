param([string]$Port = "4177")

$ErrorActionPreference = "Continue"
$appDir = Join-Path $PSScriptRoot "..\apps\lantern-garage"
$appDir = (Resolve-Path $appDir).Path
$url    = "http://127.0.0.1:$Port"

Write-Host ""
Write-Host "=== Lantern OS Server Start Test ===" -ForegroundColor Cyan
Write-Host "App dir : $appDir"
Write-Host "URL     : $url"
Write-Host ""

# Kill any existing process on this port
$existing = netstat -ano 2>$null | Select-String ":$Port "
if ($existing) {
    Write-Host "Killing existing process on port $Port..." -ForegroundColor Yellow
    $existing | ForEach-Object {
        $procPid = ($_ -split '\s+')[-1]
        if ($procPid -match '^\d+$') { Stop-Process -Id $procPid -Force -ErrorAction SilentlyContinue }
    }
    Start-Sleep 1
}

# Set port env and start node
$env:LANTERN_GARAGE_PORT = $Port
Write-Host "Starting node server.js ..." -ForegroundColor Cyan
$proc = Start-Process -FilePath "node" -ArgumentList "server.js" -WorkingDirectory $appDir -PassThru -WindowStyle Minimized
Write-Host "Node PID: $($proc.Id)"

Start-Sleep 4

# Test HTTP
Write-Host ""
Write-Host "Testing $url ..." -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 6
    Write-Host ""
    Write-Host "SERVER IS UP" -ForegroundColor Green
    Write-Host "  Status : $($resp.StatusCode)" -ForegroundColor Green
    Write-Host "  Length : $($resp.Content.Length) bytes" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Open in browser: $url" -ForegroundColor Yellow
} catch {
    Write-Host ""
    Write-Host "SERVER DID NOT RESPOND" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check: is node in PATH? Is port $Port blocked?" -ForegroundColor Yellow
}
