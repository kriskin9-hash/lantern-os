#requires -Version 5.1
<#
.SYNOPSIS
    Install Rust toolchain for Lantern OS contributors (Windows).

.DESCRIPTION
    Checks for rustc/cargo. If missing, downloads rustup-init.exe
    and installs the stable toolchain with default profile.
    After install, runs a quick `cargo --version` sanity check.

    Run: powershell -ExecutionPolicy Bypass -File scripts/Install-Rust.ps1
#>

$ErrorActionPreference = "Stop"

function Test-RustInstalled {
    try {
        $rustc = Get-Command rustc -ErrorAction SilentlyContinue
        $cargo = Get-Command cargo -ErrorAction SilentlyContinue
        if ($rustc -and $cargo) {
            $rv = & rustc --version 2>$null
            $cv = & cargo --version 2>$null
            Write-Output "Rust already installed: $rv / $cv"
            return $true
        }
    } catch {}
    return $false
}

if (Test-RustInstalled) {
    Write-Output "No action needed."
    exit 0
}

Write-Output "Rust not found. Installing via rustup..."

$rustupUrl = "https://win.rustup.rs/x86_64"
$tempPath = Join-Path $env:TEMP "rustup-init.exe"

Write-Output "Downloading rustup-init from $rustupUrl ..."
Invoke-WebRequest -Uri $rustupUrl -OutFile $tempPath -UseBasicParsing

Write-Output "Running rustup installer (stable toolchain, default profile)..."
& $tempPath -y --default-toolchain stable --profile default

if ($LASTEXITCODE -ne 0) {
    Write-Error "rustup installation failed with exit code $LASTEXITCODE"
}

# rustup adds cargo to PATH for future sessions but not current.
# Refresh PATH in this session.
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "Machine")

if (-not (Test-RustInstalled)) {
    Write-Error "Installation appeared to succeed but rustc/cargo still not on PATH. Restart your terminal."
}

Write-Output "Rust installation complete."

# Optional: quick build test
$csfRustDir = Join-Path $PSScriptRoot ".." "src" "csf_rust" | Resolve-Path
Write-Output "Quick sanity build in $csfRustDir ..."
Push-Location $csfRustDir
    cargo build --release
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Sanity build failed. Check for compilation errors above."
    }
Pop-Location

Write-Output "Done. You can now run 'cargo test' in src/csf_rust/"
