#!/usr/bin/env pwsh
# Install-MonoworkstreamHooks.ps1
# Installs monoworkstream pre-commit and pre-push hooks for single-dev workflow.

$ErrorActionPreference = "Stop"
$repoRoot = git rev-parse --show-toplevel
$hooksDir = Join-Path $repoRoot ".git\hooks"
$sourceDir = Join-Path $repoRoot "scripts\hooks"

if (-not (Test-Path $hooksDir)) {
    throw ".git/hooks directory not found. Run from a git repository."
}

if (-not (Test-Path (Join-Path $sourceDir "pre-commit"))) {
    throw "Source hooks not found at scripts/hooks/"
}

Copy-Item (Join-Path $sourceDir "pre-commit") (Join-Path $hooksDir "pre-commit") -Force
Copy-Item (Join-Path $sourceDir "pre-push")  (Join-Path $hooksDir "pre-push")  -Force

# On Windows, Git hooks need to be executable. Git for Windows respects the shebang.
# We don't need chmod here because Git for Windows handles .sh files with bash.
Write-Host "Monoworkstream hooks installed to .git/hooks/"
Write-Host ""
Write-Host "Rules enforced:"
Write-Host "  - pre-commit: blocks new commits while any PR is open"
Write-Host "  - pre-push:   blocks new pushes while any PR is open + protects master"
Write-Host ""
Write-Host "Bypass (emergency only): SKIP_MONOWORKSTREAM=1 git commit ..."
