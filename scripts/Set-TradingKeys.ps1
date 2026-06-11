#Requires -Version 5.1
<#
.SYNOPSIS
    Ingest Alpaca (and optionally Kalshi/IBKR) API keys into the repo .env file.

.DESCRIPTION
    Prompts for trading API credentials and upserts them into .env at the repo root.
    Existing values are updated in-place; new keys are appended under a Trading APIs block.
    The .env file is never committed — it is in .gitignore.

.EXAMPLE
    .\scripts\Set-TradingKeys.ps1
    .\scripts\Set-TradingKeys.ps1 -Kalshi -IBKR
#>
param(
    [switch]$Kalshi,   # also prompt for Kalshi API key
    [switch]$IBKR      # also prompt for IBKR host/port overrides
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path $PSScriptRoot -Parent
$envFile  = Join-Path $repoRoot '.env'

# ── helpers ─────────────────────────────────────────────────────────────────

function Read-EnvFile {
    param([string]$Path)
    $lines = @()
    if (Test-Path $Path) { $lines = Get-Content $Path -Encoding UTF8 }
    return $lines
}

function Upsert-EnvKey {
    param(
        [string[]]$Lines,
        [string]$Key,
        [string]$Value
    )
    $pattern = "^$([regex]::Escape($Key))\s*="
    $newLine  = "$Key=$Value"
    $idx = ($Lines | Select-String -Pattern $pattern).LineNumber - 1  # 0-based
    if ($null -ne $idx -and $idx -ge 0) {
        $Lines[$idx] = $newLine
    } else {
        $Lines += $newLine
    }
    return $Lines
}

function Prompt-Secret {
    param([string]$Prompt, [string]$Current)
    if ($Current) {
        $masked = $Current.Substring(0, [Math]::Min(6, $Current.Length)) + '...'
        $input = Read-Host "$Prompt (current: $masked, Enter to keep)"
        if ([string]::IsNullOrWhiteSpace($input)) { return $Current }
        return $input.Trim()
    }
    $input = Read-Host $Prompt
    return $input.Trim()
}

# ── load current .env ────────────────────────────────────────────────────────

$lines = Read-EnvFile $envFile

function Get-CurrentValue([string]$Key) {
    $pattern = "^$([regex]::Escape($Key))\s*=\s*(.*)$"
    $match = $lines | Select-String -Pattern $pattern | Select-Object -First 1
    if ($match) { return $match.Matches[0].Groups[1].Value.Trim() }
    return ''
}

# ── Alpaca ───────────────────────────────────────────────────────────────────

Write-Host ''
Write-Host '=== Alpaca Paper Trading ===' -ForegroundColor Cyan
Write-Host 'Get your keys at: https://app.alpaca.markets → Home → Generate New Key'
Write-Host ''

$alpacaKey    = Prompt-Secret 'ALPACA_API_KEY'    (Get-CurrentValue 'ALPACA_API_KEY')
$alpacaSecret = Prompt-Secret 'ALPACA_SECRET_KEY' (Get-CurrentValue 'ALPACA_SECRET_KEY')

if ($alpacaKey)    { $lines = Upsert-EnvKey $lines 'ALPACA_API_KEY'    $alpacaKey }
if ($alpacaSecret) { $lines = Upsert-EnvKey $lines 'ALPACA_SECRET_KEY' $alpacaSecret }

# ── Kalshi (optional) ────────────────────────────────────────────────────────

if ($Kalshi) {
    Write-Host ''
    Write-Host '=== Kalshi Prediction Markets ===' -ForegroundColor Cyan
    Write-Host 'Get your key at: https://kalshi.com/account/api'
    Write-Host ''
    $kalshiKey = Prompt-Secret 'KALSHI_API_KEY' (Get-CurrentValue 'KALSHI_API_KEY')
    if ($kalshiKey) { $lines = Upsert-EnvKey $lines 'KALSHI_API_KEY' $kalshiKey }
}

# ── IBKR (optional) ──────────────────────────────────────────────────────────

if ($IBKR) {
    Write-Host ''
    Write-Host '=== IBKR Gateway ===' -ForegroundColor Cyan
    Write-Host 'TWS / IBKR Gateway must be running and Client Portal API enabled.'
    Write-Host ''
    $ibkrHost = Prompt-Secret 'IBKR_HOST (default: localhost)' (Get-CurrentValue 'IBKR_HOST')
    $ibkrPort = Prompt-Secret 'IBKR_PORT (default: 4001)'      (Get-CurrentValue 'IBKR_PORT')
    if ($ibkrHost) { $lines = Upsert-EnvKey $lines 'IBKR_HOST' $ibkrHost }
    if ($ibkrPort) { $lines = Upsert-EnvKey $lines 'IBKR_PORT' $ibkrPort }
}

# ── write back ───────────────────────────────────────────────────────────────

$lines | Set-Content $envFile -Encoding UTF8
Write-Host ''
Write-Host '✓ Keys written to .env' -ForegroundColor Green
Write-Host '  Restart the server to pick up changes.' -ForegroundColor DarkGray
Write-Host ''
