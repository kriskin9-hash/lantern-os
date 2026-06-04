# Start Local LLMs (LM Studio + Ollama) for Lantern
# This script launches both services and waits for them to be ready

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "        Lantern Local LLM Startup (LM Studio + Ollama)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Configuration
$LM_STUDIO_PORT = 1234
$OLLAMA_PORT = 11434
$MAX_WAIT_SECONDS = 60
$WAIT_INTERVAL = 2

# Function to check if port is listening
function Test-PortOpen {
    param([int]$Port, [string]$PortName)

    $socket = New-Object System.Net.Sockets.TcpClient
    try {
        $socket.Connect("127.0.0.1", $Port)
        $socket.Close()
        return $true
    } catch {
        return $false
    }
}

# Function to wait for service
function Wait-ForService {
    param([int]$Port, [string]$ServiceName, [int]$MaxSeconds)

    Write-Host "[*] Waiting for $ServiceName on port $Port..." -ForegroundColor Yellow

    $elapsedSeconds = 0
    while ($elapsedSeconds -lt $MaxSeconds) {
        if (Test-PortOpen $Port) {
            Write-Host "[OK] $ServiceName is ready on port $Port" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds $WAIT_INTERVAL
        $elapsedSeconds += $WAIT_INTERVAL
        Write-Host "     Still waiting... ($elapsedSeconds/$MaxSeconds sec)" -ForegroundColor Gray
    }

    Write-Host "[!] $ServiceName did not start within $MaxSeconds seconds" -ForegroundColor Red
    return $false
}

# ============================================================================
# 1. START LM STUDIO
# ============================================================================
Write-Host ""
Write-Host "1. Starting LM Studio..." -ForegroundColor Cyan

$lmStudioPaths = @(
    "C:\Program Files\LM Studio\LM Studio.exe",
    "C:\Program Files (x86)\LM Studio\LM Studio.exe",
    "$env:APPDATA\LM Studio\bin\lm-studio.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\lmstudio\lm-studio.exe"
)

$lmStudioFound = $false
foreach ($path in $lmStudioPaths) {
    if (Test-Path $path) {
        Write-Host "[OK] Found LM Studio at: $path" -ForegroundColor Green
        try {
            Start-Process -FilePath $path -WindowStyle Minimized -ErrorAction Stop
            $lmStudioFound = $true
            break
        } catch {
            Write-Host "[!] Failed to start LM Studio: $_" -ForegroundColor Red
        }
    }
}

if (-not $lmStudioFound) {
    Write-Host "[!] LM Studio not found. Install from https://lmstudio.ai/" -ForegroundColor Yellow
}

# ============================================================================
# 2. START OLLAMA
# ============================================================================
Write-Host ""
Write-Host "2. Starting Ollama..." -ForegroundColor Cyan

$ollamaPaths = @(
    "C:\Program Files\Ollama\ollama.exe",
    "C:\Program Files (x86)\Ollama\ollama.exe",
    "$env:APPDATA\Ollama\ollama.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Ollama\ollama.exe"
)

$ollamaFound = $false
foreach ($path in $ollamaPaths) {
    if (Test-Path $path) {
        Write-Host "[OK] Found Ollama at: $path" -ForegroundColor Green
        try {
            # Ollama typically runs as a service, but we can also start the executable
            Start-Process -FilePath $path -WindowStyle Minimized -ErrorAction Stop
            $ollamaFound = $true
            break
        } catch {
            Write-Host "[!] Failed to start Ollama: $_" -ForegroundColor Red
        }
    }
}

if (-not $ollamaFound) {
    Write-Host "[!] Ollama not found. Install from https://ollama.ai/" -ForegroundColor Yellow
}

# ============================================================================
# 3. WAIT FOR SERVICES TO BE READY
# ============================================================================
Write-Host ""
Write-Host "3. Waiting for services to initialize..." -ForegroundColor Cyan

$lmStudioReady = Wait-ForService $LM_STUDIO_PORT "LM Studio" $MAX_WAIT_SECONDS
$ollamaReady = Wait-ForService $OLLAMA_PORT "Ollama" $MAX_WAIT_SECONDS

# ============================================================================
# 4. SUMMARY & NEXT STEPS
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                        Status Summary" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "LM Studio (port $LM_STUDIO_PORT):" -ForegroundColor White
if ($lmStudioReady) {
    Write-Host "  ✅ READY - http://127.0.0.1:$LM_STUDIO_PORT" -ForegroundColor Green
} else {
    Write-Host "  ⭕ NOT READY - Install or start LM Studio manually" -ForegroundColor Yellow
    Write-Host "     Download: https://lmstudio.ai/" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Ollama (port $OLLAMA_PORT):" -ForegroundColor White
if ($ollamaReady) {
    Write-Host "  ✅ READY - http://127.0.0.1:$OLLAMA_PORT" -ForegroundColor Green
} else {
    Write-Host "  ⭕ NOT READY - Install or start Ollama manually" -ForegroundColor Yellow
    Write-Host "     Download: https://ollama.ai/" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
if ($lmStudioReady -or $ollamaReady) {
    Write-Host "  1. Start Lantern Desktop: python scripts\lantern-desktop-auth-ui.py" -ForegroundColor Gray
    Write-Host "  2. Select LM Studio or Ollama from the provider buttons" -ForegroundColor Gray
    Write-Host "  3. Click Ready to start chatting" -ForegroundColor Gray
} else {
    Write-Host "  1. Install LM Studio from https://lmstudio.ai/" -ForegroundColor Gray
    Write-Host "  2. Install Ollama from https://ollama.ai/" -ForegroundColor Gray
    Write-Host "  3. Run this script again" -ForegroundColor Gray
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Keep window open
if ($Host.UI.RawUI.KeyAvailable) {
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null
}
