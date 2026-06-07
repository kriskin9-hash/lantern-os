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
Copy-Item (Join-Path $sourceDir "commit-msg") (Join-Path $hooksDir "commit-msg") -Force
Copy-Item (Join-Path $sourceDir "pre-push")   (Join-Path $hooksDir "pre-push")   -Force

Write-Host "Per-agent workstream hooks installed to .git/hooks/"
Write-Host ""
Write-Host "Rules enforced:"
Write-Host "  - pre-commit:  blocks new branch if this agent (claude/gemini/codex/devin/grok) already has an open PR"
Write-Host "  - commit-msg:  blocks slop messages (empty, too short, WIP, placeholder, etc.)"
Write-Host "  - pre-push:    same per-agent check on push + master protection"
Write-Host ""
Write-Host "Each agent prefix gets one concurrent PR lane."
Write-Host "Human branches (no agent prefix) share one lane."
Write-Host ""
Write-Host "Bypass workstream gate:  SKIP_MONOWORKSTREAM=1 git commit/push ..."
Write-Host "Override master push:    OVERRIDE_MERGE=1 git push origin master"
