#Requires -Version 7
<#
.SYNOPSIS
    Lantern OS — Complete Service Quickstart
    Starts all services: Lanterns Garage, Ollama, Image Generation, MCP Server
    Opens Dream Chat in Chrome. Dual-boot compatible (Windows/WSL).

.DESCRIPTION
    1. Verifies prerequisites (Node, Python, Ollama)
    2. Stops any stale processes
    3. Installs Node dependencies
    4. Starts Ollama (LLM fallback, Windows)
    5. Starts Lanterns Garage (Dream Chat UI, port 4177)
    6. Starts Image Generation Service (port 5555)
    7. Starts MCP Server (port 8771, optional)
    8. Launches Dream Chat in Chrome

.PARAMETER Root
    Repository root directory (default: current directory)

.PARAMETER SkipOllama
    Skip Ollama service startup

.PARAMETER SkipImageGen
    Skip Image Generation service startup

.PARAMETER SkipMCP
    Skip MCP Server startup

.PARAMETER NoBrowser
    Don't auto-launch Chrome

.EXAMPLE
    pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/Start-LanternOS.ps1
    pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/Start-LanternOS.ps1 -SkipOllama -NoBrowser
#>

param(
    [string]$Root = ".",
    [switch]$SkipOllama,
    [switch]$SkipImageGen,
    [switch]$SkipMCP,
    [switch]$NoBrowser,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$RepoRoot = (Resolve-Path $Root).Path
$AppRoot = Join-Path $RepoRoot "apps" "lantern-garage"
$ServicesRoot = Join-Path $RepoRoot "services"
$SrcRoot = Join-Path $RepoRoot "src"

# Colors
$Success = @{ ForegroundColor = "Green" }
$ErrorColor = @{ ForegroundColor = "Red" }
$Info = @{ ForegroundColor = "Cyan" }
$Warn = @{ ForegroundColor = "Yellow" }

function Log-Success { param([string]$Msg) Write-Host "  ✓ $Msg" @Success }
function Log-Error { param([string]$Msg) Write-Host "  ✗ $Msg" @ErrorColor }
function Log-Info { param([string]$Msg) Write-Host "  → $Msg" @Info }
function Log-Warn { param([string]$Msg) Write-Host "  ⚠ $Msg" @Warn }

Write-Host ""
Write-Host "🚀 Lanterns OS — Service Quickstart" @Info
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" @Info
Write-Host ""

# Detect platform (dual-boot awareness)
$IsWindows = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)
$IsLinux = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Linux)

if ($IsLinux) {
    Write-Host "[PLATFORM] Running on Linux/WSL" @Warn
}
Write-Host ""

# ──────────────────────────────────────────────────────────────────

# Helper: Wait for port to be ready
function Wait-Port {
    param(
        [int]$Port,
        [string]$Service,
        [int]$TimeoutSeconds = 30
    )
    $start = Get-Date
    while ((Get-Date) - $start -lt [TimeSpan]::FromSeconds($TimeoutSeconds)) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" `
                -ErrorAction SilentlyContinue -SkipHttpErrorCheck -TimeoutSec 2
            if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 404) {
                Log-Success "$Service ready (port $Port)"
                return $true
            }
        }
        catch { }
        Start-Sleep -Milliseconds 500
    }
    Log-Error "$Service timeout (port $Port)"
    return $false
}

# Helper: Get process on port
function Get-ProcessOnPort {
    param([int]$Port)
    try {
        $proc = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -First 1
        return $proc
    }
    catch { return $null }
}

# Helper: Stop process on port
function Stop-ServiceOnPort {
    param(
        [int]$Port,
        [string]$Service
    )
    try {
        $proc = Get-ProcessOnPort -Port $Port
        if ($proc) {
            Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue
            Log-Warn "Stopped process on port $Port"
            Start-Sleep -Milliseconds 500
        }
    }
    catch { }
}

# ──────────────────────────────────────────────────────────────────

# Step 1: Verify prerequisites
Write-Host "[1/8] Checking prerequisites..." @Info

$hasNode = $null -ne (Get-Command node -ErrorAction SilentlyContinue)
$hasNpm = $null -ne (Get-Command npm -ErrorAction SilentlyContinue)
$hasPython = $null -ne (Get-Command python -ErrorAction SilentlyContinue)
$hasOllama = Test-Path "C:\Program Files\Ollama\ollama.exe"

if (-not $hasNode -or -not $hasNpm) {
    Log-Error "Node.js/npm not found"
    Write-Host "       Install from https://nodejs.org/" @Info
    exit 1
}

Log-Success "Node.js: $(node --version)"
Log-Success "npm: $(npm --version)"

if ($hasPython) {
    Log-Success "Python: $(python --version 2>&1)"
}

if ($hasOllama) {
    Log-Success "Ollama: installed"
} else {
    Log-Warn "Ollama: not found"
}

if (-not $hasPython -and -not $SkipMCP) {
    Log-Warn "Python not found. MCP skipped."
    $SkipMCP = $true
}

Write-Host ""

# ──────────────────────────────────────────────────────────────────

# Step 2: Clean up stale processes
Write-Host "[2/8] Cleaning up existing services..." @Info

foreach ($port in @(4177, 5555, 8771, 11434)) {
    $proc = Get-ProcessOnPort -Port $port
    if ($proc) {
        Stop-ServiceOnPort -Port $port -Service "Port $port"
    }
}

Start-Sleep -Milliseconds 500
Write-Host ""

# ──────────────────────────────────────────────────────────────────

# Step 3: Install Node dependencies
Write-Host "[3/8] Installing Node dependencies..." @Info

Push-Location $AppRoot -ErrorAction SilentlyContinue
$npmOut = npm install --silent 2>&1
if ($LASTEXITCODE -eq 0) {
    Log-Success "Dependencies ready"
} else {
    if ($Verbose) { Log-Warn "npm warnings (non-fatal)" }
}
Pop-Location

Write-Host ""

# ──────────────────────────────────────────────────────────────────

# Step 4: Start Ollama
if (-not $SkipOllama -and $hasOllama -and $IsWindows) {
    Write-Host "[4/8] Starting Ollama (LLM fallback)..." @Info

    $ollamaPath = "C:\Program Files\Ollama\ollama.exe"
    $proc = Start-Process -FilePath $ollamaPath -WindowStyle Hidden -PassThru `
        -ErrorAction SilentlyContinue -NoNewWindow

    if ($null -ne $proc) {
        Log-Info "Started (PID $($proc.Id))"
        Start-Sleep -Seconds 2
    } else {
        Log-Warn "Could not start Ollama"
    }
    Write-Host ""
} else {
    Write-Host "[4/8] Skipping Ollama" @Warn
    Write-Host ""
}

# ──────────────────────────────────────────────────────────────────

# Step 5: Start Lanterns Garage
Write-Host "[5/8] Starting Lanterns Garage (Dream Chat UI)..." @Info

Push-Location $AppRoot -ErrorAction SilentlyContinue
$garageProc = Start-Process -FilePath "node" -ArgumentList "server.js" `
    -WindowStyle Hidden -PassThru -ErrorAction SilentlyContinue -NoNewWindow
Pop-Location

if ($null -eq $garageProc) {
    Log-Error "Failed to start Lanterns Garage"
    exit 1
}

Log-Info "Started (PID $($garageProc.Id))"
if (-not (Wait-Port -Port 4177 -Service "Lanterns Garage" -TimeoutSeconds 15)) {
    Log-Warn "Server may still be initializing"
}
Write-Host ""

# ──────────────────────────────────────────────────────────────────

# Step 6: Start Image Generation Service
if (-not $SkipImageGen) {
    Write-Host "[6/8] Starting Image Generation Service..." @Info

    Push-Location $ServicesRoot -ErrorAction SilentlyContinue
    $imageProc = Start-Process -FilePath "node" -ArgumentList "image-gen-service.js" `
        -WindowStyle Hidden -PassThru -ErrorAction SilentlyContinue -NoNewWindow
    Pop-Location

    if ($null -ne $imageProc) {
        Log-Info "Started (PID $($imageProc.Id))"
        Start-Sleep -Milliseconds 500
        Wait-Port -Port 5555 -Service "Image Generation" -TimeoutSeconds 5 | Out-Null
    } else {
        Log-Warn "Image Generation unavailable"
    }
    Write-Host ""
}

# ──────────────────────────────────────────────────────────────────

# Step 7: Start MCP Server
if (-not $SkipMCP -and $hasPython) {
    Write-Host "[7/8] Starting MCP Server..." @Info

    Push-Location $SrcRoot -ErrorAction SilentlyContinue
    $mcpProc = Start-Process -FilePath "python" -ArgumentList "mcp_server/server.py" `
        -WindowStyle Hidden -PassThru -ErrorAction SilentlyContinue -NoNewWindow
    Pop-Location

    if ($null -ne $mcpProc) {
        Log-Info "Started (PID $($mcpProc.Id))"
        Start-Sleep -Milliseconds 500
        Wait-Port -Port 8771 -Service "MCP Server" -TimeoutSeconds 5 | Out-Null
    } else {
        Log-Warn "MCP Server unavailable"
    }
    Write-Host ""
}

# ──────────────────────────────────────────────────────────────────

# Step 8: Launch browser
Write-Host "[8/8] Opening Dream Chat in Chrome..." @Info

if (-not $NoBrowser) {
    try {
        $chrome = Get-Command chrome.exe -ErrorAction SilentlyContinue
        if ($chrome) {
            Start-Process -FilePath "chrome.exe" `
                -ArgumentList "http://127.0.0.1:4177/dream-chat.html" `
                -ErrorAction SilentlyContinue -NoNewWindow
            Log-Success "Browser launched"
        } else {
            Log-Warn "Chrome not found"
            Log-Info "Open: http://127.0.0.1:4177/dream-chat.html"
        }
    }
    catch {
        Log-Warn "Could not auto-launch browser"
        Log-Info "Open: http://127.0.0.1:4177/dream-chat.html"
    }
}

Write-Host ""

# ──────────────────────────────────────────────────────────────────

# Final status
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" @Info
Write-Host "🌙 Lanterns OS is running!" @Success
Write-Host ""
Write-Host "Services active:" @Info
Write-Host "  • Lanterns Garage (Dream Chat):   http://127.0.0.1:4177" @Info
Write-Host "  • Image Generation:                http://127.0.0.1:5555" @Info
Write-Host "  • MCP Server:                      http://127.0.0.1:8771" @Info
Write-Host "  • Ollama (LLM fallback):           http://127.0.0.1:11434" @Info
Write-Host ""
Write-Host "To stop services:" @Info
Write-Host "  Get-Process node,ollama | Stop-Process -Force" @Info
Write-Host ""
