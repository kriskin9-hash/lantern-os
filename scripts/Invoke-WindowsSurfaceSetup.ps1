param(
    [string]$DesktopPath = "$env:USERPROFILE\OneDrive\Desktop\Lantern Surfaces",
    [string]$StartMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Lantern",
    [string]$HFFScanRepo = "C:\tmp\human-flourishing-frameworks-scan",
    [string]$OrchestratorRepo = "C:\Users\alexp\Documents\gm-agent-orchestrator",
    [switch]$SingleShortcutOnly
)

$ErrorActionPreference = "Stop"

if ($SingleShortcutOnly) {
    & (Join-Path $PSScriptRoot "Install-LanternShortcut.ps1") -DesktopPath $DesktopPath -StartMenuPath $StartMenuPath
    return
}

function New-LanternShortcut {
    param(
        [string]$Path,
        [string]$Name,
        [string]$TargetPath,
        [string]$Description = "",
        [string]$IconPath = "",
        [string]$Arguments = ""
    )

    $shortcutPath = Join-Path $Path "$Name.lnk"

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $TargetPath

    if ($Description) {
        $shortcut.Description = $Description
    }

    if ($Arguments) {
        $shortcut.Arguments = $Arguments
    }

    if ($IconPath -and (Test-Path $IconPath)) {
        $shortcut.IconLocation = $IconPath
    }

    $shortcut.Save()
    Write-Output "Created: $shortcutPath"
}

function New-URLShortcut {
    param(
        [string]$Path,
        [string]$Name,
        [string]$URL,
        [string]$Description = ""
    )

    $shortcutPath = Join-Path $Path "$Name.url"

    $content = @"
[InternetShortcut]
URL=$URL
"@

    if ($Description) {
        $content += "`nComment=$Description`n"
    }

    Set-Content -LiteralPath $shortcutPath -Value $content -Encoding ASCII
    Write-Output "Created: $shortcutPath"
}

# Create directories
Write-Output "Creating Lantern directory structure..."
New-Item -ItemType Directory -Path $DesktopPath -Force | Out-Null
New-Item -ItemType Directory -Path $StartMenuPath -Force | Out-Null
New-Item -ItemType Directory -Path "$DesktopPath\assets" -Force | Out-Null

# Copy or create the Feather Lantern icon
$featherIconSource = Join-Path $HFFScanRepo "assets\feather-lantern.ico"
$featherIconDest = Join-Path $DesktopPath "assets\feather-lantern.ico"

if (Test-Path $featherIconSource) {
    Copy-Item -LiteralPath $featherIconSource -Destination $featherIconDest -Force
    Write-Output "Copied feather-lantern.ico"
}

Write-Output "Creating Windows surface shortcuts..."

# COMET LEAP Artifacts
$cometLeapDir = Join-Path $DesktopPath "COMET LEAP"
New-Item -ItemType Directory -Path $cometLeapDir -Force | Out-Null

if (Test-Path (Join-Path $HFFScanRepo "COMET-LEAP-MINI-BUFFET-30DAY-MERGED.pdf")) {
    New-LanternShortcut -Path $cometLeapDir `
        -Name "30-Day Model (Merged PDF)" `
        -TargetPath (Join-Path $HFFScanRepo "COMET-LEAP-MINI-BUFFET-30DAY-MERGED.pdf") `
        -Description "COMET LEAP 30-day update model with visual timeline"
}

if (Test-Path (Join-Path $HFFScanRepo "COMET-LEAP-MINI-BUFFET-30DAY-ART-MODEL.docx")) {
    New-LanternShortcut -Path $cometLeapDir `
        -Name "Art Model (DOCX)" `
        -TargetPath (Join-Path $HFFScanRepo "COMET-LEAP-MINI-BUFFET-30DAY-ART-MODEL.docx") `
        -Description "Art model for the 30-day cycle"
}

if (Test-Path (Join-Path $HFFScanRepo "COMET-LEAPER-FOUNDER-MONEY-CONFIDENCE-REPORT-v1.pdf")) {
    New-LanternShortcut -Path $cometLeapDir `
        -Name "Money + Confidence Report" `
        -TargetPath (Join-Path $HFFScanRepo "COMET-LEAPER-FOUNDER-MONEY-CONFIDENCE-REPORT-v1.pdf") `
        -Description "Founder money and confidence assessment"
}

if (Test-Path (Join-Path $HFFScanRepo "COMET-LEAPER-FOUNDER-TRUTH-ONLY-REPORT-v2.pdf")) {
    New-LanternShortcut -Path $cometLeapDir `
        -Name "Truth-Only Report" `
        -TargetPath (Join-Path $HFFScanRepo "COMET-LEAPER-FOUNDER-TRUTH-ONLY-REPORT-v2.pdf") `
        -Description "Unfiltered truth assessment"
}

if (Test-Path (Join-Path $HFFScanRepo "COMET-LEAP-SPIN-STATE-v1.pdf")) {
    New-LanternShortcut -Path $cometLeapDir `
        -Name "Spin State" `
        -TargetPath (Join-Path $HFFScanRepo "COMET-LEAP-SPIN-STATE-v1.pdf") `
        -Description "Current operational spin state"
}

# NixOS and Dual Boot
$nixosDir = Join-Path $DesktopPath "NixOS"
New-Item -ItemType Directory -Path $nixosDir -Force | Out-Null

if (Test-Path (Join-Path $OrchestratorRepo "nixos-lantern-production-optimized.nix")) {
    New-LanternShortcut -Path $nixosDir `
        -Name "NixOS Config (Optimized)" `
        -TargetPath (Join-Path $OrchestratorRepo "nixos-lantern-production-optimized.nix") `
        -Description "Optimized production NixOS configuration"
}

if (Test-Path (Join-Path $OrchestratorRepo "nixos-lantern-production.nix")) {
    New-LanternShortcut -Path $nixosDir `
        -Name "NixOS Config (Base)" `
        -TargetPath (Join-Path $OrchestratorRepo "nixos-lantern-production.nix") `
        -Description "Base production NixOS configuration"
}

# Dual Boot Prep
if (Test-Path (Join-Path $DesktopPath "DUAL-BOOT-PREP-WINDOWS-NIXOS-BUFFETT.md")) {
    New-LanternShortcut -Path $nixosDir `
        -Name "Dual Boot Prep (Markdown)" `
        -TargetPath (Join-Path $DesktopPath "DUAL-BOOT-PREP-WINDOWS-NIXOS-BUFFETT.md") `
        -Description "Dual boot preparation checklist and guide"
}

# Lantern OS Project Links
$projectDir = Join-Path $DesktopPath "Lantern OS"
New-Item -ItemType Directory -Path $projectDir -Force | Out-Null

New-LanternShortcut -Path $projectDir `
    -Name "Lantern OS (C:\tmp\lantern-os)" `
    -TargetPath "explorer.exe" `
    -Arguments "C:\tmp\lantern-os" `
    -Description "Lantern OS v1.0.0 staging repository"

New-LanternShortcut -Path $projectDir `
    -Name "HFF Scan Repo" `
    -TargetPath "explorer.exe" `
    -Arguments $HFFScanRepo `
    -Description "Human Flourishing Frameworks source repository"

New-LanternShortcut -Path $projectDir `
    -Name "GM Agent Orchestrator Repo" `
    -TargetPath "explorer.exe" `
    -Arguments $OrchestratorRepo `
    -Description "GM Agent Orchestrator source repository"

# Update Start Menu with main reference points
Write-Output "Creating Start Menu shortcuts..."

New-URLShortcut -Path $StartMenuPath `
    -Name "Lantern OS" `
    -URL "http://127.0.0.1:4177/" `
    -Description "Single Lantern OS dashboard"

New-LanternShortcut -Path $StartMenuPath `
    -Name "Lantern OS Repository" `
    -TargetPath "explorer.exe" `
    -Arguments "C:\tmp\lantern-os" `
    -Description "Lantern OS staging repository"

Write-Output "Windows surface setup complete!"
Write-Output "Desktop: $DesktopPath"
Write-Output "Start Menu: $StartMenuPath"
Write-Output "Total shortcuts created: $(Get-ChildItem -Path $DesktopPath, $StartMenuPath -Recurse -Filter '*.lnk', '*.url' | Measure-Object | Select-Object -ExpandProperty Count)"
