#Requires -Version 5.1
<#
.SYNOPSIS
    Lantern OS / Dream Journal — One-Click Installer
    Idempotent: safe to run multiple times. Updates existing installs.

.DESCRIPTION
    Installs or updates Dream Journal (Lantern OS) on Windows.
    - Validates prerequisites (Node.js, Python, Git)
    - Clones or updates the repo
    - Installs Node.js dependencies (npm install)
    - Installs Python dependencies (pip install)
    - Copies .env.example → .env if no .env exists
    - Creates a desktop shortcut "Dream Journal"
    - Optionally starts the server

.EXAMPLE
    # Run from the web (PowerShell recommended)
    irm https://raw.githubusercontent.com/alex-place/lantern-os/master/scripts/install-dream-journal.ps1 | iex

.EXAMPLE
    # Run locally after cloning
    powershell -ExecutionPolicy Bypass -File .\scripts\install-dream-journal.ps1

.PARAMETER SkipPython
    Skip Python dependency installation (only needed for Discord bot / MCP server).

.PARAMETER StartApp
    Automatically start the Dream Journal server after install.

.PARAMETER InstallDir
    Override the default installation directory.
    Default: $env:USERPROFILE\lantern-os
#>
param(
    [switch]$SkipPython,
    [switch]$StartApp,
    [string]$InstallDir = ""
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
$RepoUrl      = "https://github.com/alex-place/lantern-os.git"
$RepoBranch   = "master"
$ShortcutName = "Dream Journal"
$ServerPort   = 4177

if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $InstallDir = Join-Path $env:USERPROFILE "lantern-os"
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Write-Header {
    param([string]$Text, [string]$Color = "Cyan")
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $Color
    Write-Host "  $Text" -ForegroundColor $Color
    Write-Host "========================================" -ForegroundColor $Color
}

function Write-Step {
    param([string]$Text, [string]$Color = "White")
    Write-Host "  [+] $Text" -ForegroundColor $Color
}

function Write-Warn {
    param([string]$Text)
    Write-Host "  [!] $Text" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Text)
    Write-Host "  [X] $Text" -ForegroundColor Red
}

function Test-Command {
    param([string]$Name)
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-NodeVersion {
    param([version]$Minimum)
    try {
        $raw = node --version 2>$null   # "v20.11.0"
        if ($raw -match '^v(\d+\.\d+\.\d+)') {
            return [version]$Matches[1] -ge $Minimum
        }
    } catch {}
    return $false
}

function New-DesktopShortcut {
    param(
        [string]$Name,
        [string]$Target,
        [string]$Arguments,
        [string]$WorkingDir,
        [string]$Description
    )
    $desktop = [Environment]::GetFolderPath("Desktop")
    if (-not (Test-Path $desktop)) {
        Write-Warn "Desktop folder not found; skipping shortcut creation."
        return
    }
    $lnkPath = Join-Path $desktop "$Name.lnk"
    try {
        $wsh = New-Object -ComObject WScript.Shell
        $lnk = $wsh.CreateShortcut($lnkPath)
        $lnk.TargetPath       = $Target
        $lnk.Arguments        = $Arguments
        $lnk.WorkingDirectory = $WorkingDir
        $lnk.Description      = $Description
        $lnk.IconLocation     = "%SystemRoot%\System32\SHELL32.dll,14"
        $lnk.Save()
        Write-Step "Desktop shortcut created: $lnkPath" "Green"
    } catch {
        Write-Warn "Could not create desktop shortcut: $_"
    }
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
Write-Header "Lantern OS / Dream Journal Installer"
Write-Host "  InstallDir : $InstallDir" -ForegroundColor Gray
Write-Host "  Branch     : $RepoBranch" -ForegroundColor Gray
Write-Host "  Date       : $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Gray
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Prerequisites
# ---------------------------------------------------------------------------
Write-Header "Checking Prerequisites"

$prereqOk = $true

# PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Err "PowerShell 5.1+ required. You have $($PSVersionTable.PSVersion)"
    $prereqOk = $false
} else {
    Write-Step "PowerShell $($PSVersionTable.PSVersion) — OK" "Green"
}

# Git
if (-not (Test-Command "git")) {
    Write-Err "Git not found. Install from https://git-scm.com/download/win"
    $prereqOk = $false
} else {
    Write-Step "Git — OK" "Green"
}

# Node.js (required — this IS the server)
if (-not (Test-Command "node")) {
    Write-Err "Node.js not found. Install v18+ from https://nodejs.org"
    $prereqOk = $false
} elseif (-not (Test-NodeVersion "18.0.0")) {
    $nodeVer = node --version 2>&1
    Write-Err "Node.js 18+ required. Found: $nodeVer. Update at https://nodejs.org"
    $prereqOk = $false
} else {
    $nodeVer = node --version 2>&1
    Write-Step "Node.js $nodeVer — OK" "Green"
}

# Python (optional — for Discord bot, MCP server)
$hasPython = Test-Command "python"
if (-not $SkipPython) {
    if ($hasPython) {
        $pyVer = python --version 2>&1
        Write-Step "$pyVer — OK (Discord bot / MCP server)" "Green"
    } else {
        Write-Warn "Python not found. Install 3.10+ from https://www.python.org/downloads/"
        Write-Warn "   Python is only required for the Discord bot and MCP server, not the web UI."
    }
}

# ffmpeg (optional — required for Discord voice/lounge music)
if (Test-Command "ffmpeg") {
    Write-Step "ffmpeg — OK (Discord voice/lounge)" "Green"
} else {
    Write-Warn "ffmpeg not found. Install for Discord voice features:"
    Write-Warn "   winget install Gyan.FFmpeg"
    Write-Warn "   (or download from https://ffmpeg.org/download.html)"
}

if (-not $prereqOk) {
    Write-Host ""
    Write-Err "Prerequisite checks failed. Please install missing items and re-run."
    exit 1
}

# ---------------------------------------------------------------------------
# 2. Clone or update repo
# ---------------------------------------------------------------------------
Write-Header "Repository Setup"

if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Step "Existing repo found at $InstallDir — pulling latest..."
    Push-Location $InstallDir
    try {
        git fetch origin $RepoBranch 2>&1 | Out-Null
        git reset --hard "origin/$RepoBranch" 2>&1 | Out-Null
        Write-Step "Updated to latest $RepoBranch" "Green"
    } catch {
        Write-Warn "Git pull failed. Continuing with existing files..."
    } finally {
        Pop-Location
    }
} else {
    if (Test-Path $InstallDir) {
        Write-Warn "Directory exists but is not a git repo. Renaming to .backup"
        $backup = "$InstallDir.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
        Rename-Item $InstallDir $backup
    }
    Write-Step "Cloning $RepoUrl into $InstallDir ..."
    git clone --branch $RepoBranch --single-branch $RepoUrl $InstallDir
    Write-Step "Clone complete." "Green"
}

# ---------------------------------------------------------------------------
# 3. Node.js dependencies
# ---------------------------------------------------------------------------
Write-Header "Node.js Dependencies"

$appDir = Join-Path $InstallDir "apps\lantern-garage"
if (Test-Path (Join-Path $appDir "package.json")) {
    Push-Location $appDir
    try {
        Write-Step "Running npm install..."
        npm install --loglevel=error 2>&1 | Out-Null
        Write-Step "npm install OK." "Green"
    } catch {
        Write-Warn "npm install failed: $_"
    } finally {
        Pop-Location
    }
} else {
    Write-Warn "No package.json found in apps/lantern-garage."
}

# ---------------------------------------------------------------------------
# 4. Python dependencies (optional)
# ---------------------------------------------------------------------------
if (-not $SkipPython -and $hasPython) {
    Write-Header "Python Dependencies"

    $requirements = Join-Path $InstallDir "requirements.txt"
    if (Test-Path $requirements) {
        Write-Step "Installing from requirements.txt (Discord bot, MCP server, tests)..."
        python -m pip install --quiet -r $requirements
        Write-Step "Python dependencies installed." "Green"
    } else {
        Write-Warn "No requirements.txt found. Skipping Python dependencies."
    }
} else {
    Write-Header "Python Dependencies"
    if ($SkipPython) {
        Write-Step "Skipped (--SkipPython)" "Gray"
    } else {
        Write-Step "Skipped (Python not found)" "Gray"
    }
}

# ---------------------------------------------------------------------------
# 5. Environment file
# ---------------------------------------------------------------------------
Write-Header "Environment Setup"

$envFile    = Join-Path $InstallDir ".env"
$envExample = Join-Path $InstallDir ".env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Step "Created .env from .env.example" "Green"
        Write-Host ""
        Write-Host "  IMPORTANT: Edit $envFile and add your API keys:" -ForegroundColor Yellow
        Write-Host "    ANTHROPIC_API_KEY  — for Claude (recommended)" -ForegroundColor White
        Write-Host "    GEMINI_API_KEY     — for Gemini (free tier available)" -ForegroundColor White
        Write-Host "    OPENAI_API_KEY     — for GPT-4o-mini (optional)" -ForegroundColor White
        Write-Host ""
        Write-Host "  For Discord bot (optional):" -ForegroundColor Yellow
        Write-Host "    DISCORD_BOT_TOKEN      — your bot token from discord.com/developers" -ForegroundColor White
        Write-Host "    LANTERN_DISCORD_GUILD_ID — your server ID (right-click server → Copy ID)" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Warn ".env.example not found; .env was not created."
        Write-Warn "Create $envFile manually before starting the server."
    }
} else {
    Write-Step ".env already exists — not overwritten." "Gray"
}

# ---------------------------------------------------------------------------
# 6. Desktop shortcut
# ---------------------------------------------------------------------------
Write-Header "Creating Shortcuts"

$startScript = Join-Path $InstallDir "scripts\Start-DreamJournal.ps1"

New-DesktopShortcut `
    -Name $ShortcutName `
    -Target "powershell.exe" `
    -Arguments "-NoProfile -ExecutionPolicy Bypass -File `"$startScript`"" `
    -WorkingDir $InstallDir `
    -Description "Start Dream Journal (Lantern OS) at http://127.0.0.1:$ServerPort"

# ---------------------------------------------------------------------------
# 7. Done
# ---------------------------------------------------------------------------
Write-Header "Installation Complete" "Green"
Write-Host "  Install Dir : $InstallDir" -ForegroundColor White
Write-Host "  Start URL   : http://127.0.0.1:$ServerPort" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Start commands:" -ForegroundColor Yellow
Write-Host "    Shortcut  : Double-click '$ShortcutName' on your Desktop" -ForegroundColor White
Write-Host "    PowerShell: powershell -File `"$startScript`"" -ForegroundColor White
Write-Host "    Manual    : node apps\lantern-garage\server.js" -ForegroundColor White
Write-Host ""

# ---------------------------------------------------------------------------
# 8. Optional auto-start
# ---------------------------------------------------------------------------
if ($StartApp) {
    Write-Header "Starting Dream Journal" "Green"
    Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$startScript`"" -WorkingDirectory $InstallDir
    Start-Sleep 4
    try {
        $health = Invoke-WebRequest -Uri "http://127.0.0.1:$ServerPort/api/health" -UseBasicParsing -TimeoutSec 5
        if ($health.StatusCode -eq 200) {
            Write-Step "Server is healthy. Opening browser..." "Green"
            Start-Process "http://127.0.0.1:$ServerPort"
        }
    } catch {
        Write-Warn "Server may still be starting. Open http://127.0.0.1:$ServerPort in a moment."
    }
} else {
    Write-Host "  Tip: Re-run with -StartApp to launch the server automatically." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Happy journaling. Light the lantern." -ForegroundColor Cyan
Write-Host ""
