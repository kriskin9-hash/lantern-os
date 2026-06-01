[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$DesktopPath = "$env:USERPROFILE\OneDrive\Desktop\Lantern Surfaces",
    [string]$StartMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Lantern",
    [string]$LanternUrl = "http://127.0.0.1:4177",
    [switch]$IncludeDiagnostics
)

$ErrorActionPreference = "Stop"

function New-LanternUrlShortcut {
    param(
        [string]$Directory,
        [string]$Name,
        [string]$Url,
        [string]$Comment
    )

    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $shortcutPath = Join-Path $Directory "$Name.url"
    $content = @"
[InternetShortcut]
URL=$Url
Comment=$Comment
"@
    if ($PSCmdlet.ShouldProcess($shortcutPath, "Create Lantern URL shortcut")) {
        Set-Content -LiteralPath $shortcutPath -Value $content -Encoding ASCII
    }
    return $shortcutPath
}

$created = @()
$created += New-LanternUrlShortcut -Directory $DesktopPath -Name "Lantern OS" -Url $LanternUrl -Comment "Single Lantern OS front door"
$created += New-LanternUrlShortcut -Directory $StartMenuPath -Name "Lantern OS" -Url $LanternUrl -Comment "Single Lantern OS front door"

if ($IncludeDiagnostics) {
    $created += New-LanternUrlShortcut -Directory $StartMenuPath -Name "Lantern Diagnostics" -Url "$LanternUrl/api/status" -Comment "Optional Lantern local diagnostics"
}

[pscustomobject]@{
    mode = "single_lantern_shortcut"
    lanternUrl = $LanternUrl
    includeDiagnostics = [bool]$IncludeDiagnostics
    created = $created
    miningDashboardShortcutCreated = $false
}
