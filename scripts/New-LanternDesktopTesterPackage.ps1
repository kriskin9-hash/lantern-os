param(
    [string]$OutputPath = "",
    [switch]$NoClobber
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$artifactDir = Join-Path $repoRoot "artifacts"
if (-not $OutputPath) {
    $OutputPath = Join-Path $artifactDir "lantern-desktop-tester-latest.zip"
}

$staging = Join-Path $artifactDir "lantern-desktop-tester-staging"
$stagingResolvedParent = (Resolve-Path $artifactDir).Path

if ((Test-Path -LiteralPath $OutputPath) -and $NoClobber) {
    throw "Output already exists: $OutputPath"
}

if (Test-Path -LiteralPath $staging) {
    $resolvedStaging = (Resolve-Path $staging).Path
    if (-not $resolvedStaging.StartsWith($stagingResolvedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove staging outside artifacts: $resolvedStaging"
    }
    Remove-Item -LiteralPath $resolvedStaging -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $staging | Out-Null

function New-PackageDir {
    param([string]$Relative)
    New-Item -ItemType Directory -Force -Path (Join-Path $staging $Relative) | Out-Null
}

function Copy-PackageFile {
    param([string]$Relative)
    $source = Join-Path $repoRoot $Relative
    if (-not (Test-Path -LiteralPath $source)) {
        return
    }
    $target = Join-Path $staging $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
}

function Copy-PackageTree {
    param(
        [string]$Relative,
        [string[]]$ExcludeNames = @()
    )
    $source = Join-Path $repoRoot $Relative
    if (-not (Test-Path -LiteralPath $source)) {
        return
    }
    $targetRoot = Join-Path $staging $Relative
    New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
    Get-ChildItem -LiteralPath $source -Recurse -File | Where-Object {
        $parts = $_.FullName.Substring($source.Length).TrimStart("\") -split "\\"
        -not ($parts | Where-Object { $ExcludeNames -contains $_ })
    } | ForEach-Object {
        $relativeChild = $_.FullName.Substring($source.Length).TrimStart("\")
        $target = Join-Path $targetRoot $relativeChild
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    }
}

New-PackageDir "apps\lantern-garage"
Copy-PackageFile "apps\lantern-garage\package.json"
Copy-PackageFile "apps\lantern-garage\server.js"
Copy-PackageFile "apps\lantern-garage\cloud-server.js"
Copy-PackageFile "apps\lantern-garage\Dockerfile"
Copy-PackageFile "apps\lantern-garage\validate.js"
Copy-PackageTree "apps\lantern-garage\public" @("node_modules", ".env", "credentials")

Copy-PackageFile "scripts\Start-LanternGarageApp.ps1"
Copy-PackageFile "scripts\Get-OneIdeStatus.ps1"
Copy-PackageFile "scripts\Test-DiscordBotHealth.ps1"

Copy-PackageFile "docs\LANTERN-DESKTOP-TESTER.md"
Copy-PackageFile "docs\wiki\WINDOWS-TESTER-INSTALL.md"
Copy-PackageFile "docs\releases\LANTERN-OS-TESTER-2026-05-30.md"
Copy-PackageFile "docs\LANTERN-COMMAND-ENTRYPOINT.md"
Copy-PackageFile "docs\ONE-HOUR-1000-DEMO.md"
Copy-PackageFile "docs\ARC-REACTOR-MINING-LAB.md"
Copy-PackageFile "docs\LANTERN-RUNTIME-CICD.md"

Copy-PackageFile "data\arc-reactor\status.json"
Copy-PackageFile "data\wallet\local-cash-wallet.json"
Copy-PackageFile "manifests\cloud-mirrors.json"
Copy-PackageFile "manifests\evidence\asi-local-pdf-convergence-2026-05-29.md"
Copy-PackageFile "skills\solo-mining\SKILL.md"
Copy-PackageFile "src\discord_lounge_bot\README.md"
Copy-PackageFile "src\discord_lounge_bot\requirements.txt"

@'
# Lantern Desktop Tester

Download page:

```text
https://github.com/alex-place/lantern-os/releases/latest
```

Current Windows tester asset:

```text
lantern-desktop-tester-latest.zip
```

Future installer assets only when attached to a release:

```text
Lantern-OS-Free-Setup.exe
Lantern-OS-Founder-20-Setup.exe
```

Requirement: Node.js 20 or newer.

Run:

```powershell
.\Start-LanternDesktopTester.ps1
```

Then open:

```text
http://127.0.0.1:4177
```

Test: dashboard, chat, demo deck, cloud/local URL map, and command lane.

Do not enter secrets, private keys, seed phrases, payment credentials, or Discord
tokens. This is a tester build, not v1.0.0. The `$20` support tester is not
equity, not a token, not ownership, not admin access, and not an investment
return. Do not claim an `.exe` exists unless it is attached to the release.
'@ | Set-Content -LiteralPath (Join-Path $staging "README-FIRST.md") -Encoding UTF8

@'
$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$app = Join-Path $root "apps\lantern-garage"
$url = "http://127.0.0.1:4177"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js 20+ is required. Install Node, then rerun this script."
}

$nodeVersionText = (& node --version).TrimStart("v")
$nodeMajor = [int]($nodeVersionText.Split(".")[0])
if ($nodeMajor -lt 20) {
    throw "Node.js 20+ is required. Found node v$nodeVersionText."
}

$env:LANTERN_GARAGE_PORT = "4177"
Write-Host "Starting Lantern Desktop Tester at $url"
Start-Process -FilePath "node" -ArgumentList "server.js" -WorkingDirectory $app -WindowStyle Minimized
Start-Sleep -Seconds 2
Start-Process $url
Write-Host "If the browser does not open, go to $url"
'@ | Set-Content -LiteralPath (Join-Path $staging "Start-LanternDesktopTester.ps1") -Encoding UTF8

if (Test-Path -LiteralPath $OutputPath) {
    Remove-Item -LiteralPath $OutputPath -Force
}

Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $OutputPath -Force
Remove-Item -LiteralPath $staging -Recurse -Force

$file = Get-Item -LiteralPath $OutputPath
[ordered]@{
    ok = $true
    outputPath = $file.FullName
    bytes = $file.Length
    url = "http://127.0.0.1:4177/repo/artifacts/$($file.Name)"
    note = "Public-safe tester package; excludes secrets, .git, node_modules, credentials, and live conversation logs."
} | ConvertTo-Json -Depth 4
