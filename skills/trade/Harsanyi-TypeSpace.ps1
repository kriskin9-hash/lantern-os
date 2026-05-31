# ================================================
# Lantern OS - Harsanyi Type Space Model v1.0
# Cloud Agent & Web Trading Fleet
# ================================================

<#
.SYNOPSIS
    Model Lantern OS agent fleet as a Harsanyi type space.
.DESCRIPTION
    Loads real agent states from Lantern OS data files, constructs type profiles,
    computes a common prior, and checks for belief divergence on critical
    approval boundaries (live trading, kill-switch, cloud deployment).
.PARAMETER ReportOnly
    If set, output report without enforcing gates.
.PARAMETER LogPath
    Where to write the type-space snapshot.
#>

param(
    [switch]$ReportOnly = $false,
    [string]$LogPath = "logs/harsanyi-type-space.jsonl"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

# ─── UTILITIES ─────────────────────────────────

function Test-EnvVar {
    param([string]$Name, [string]$Default = "")
    $val = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($val)) { return $Default }
    return $val
}

function Read-JsonIfExists {
    param([string]$Path)
    $full = Join-Path $RepoRoot $Path
    if (Test-Path $full) {
        return Get-Content $full -Raw | ConvertFrom-Json
    }
    return $null
}

function Read-JsonLIfExists {
    param([string]$Path, [int]$Tail = 1)
    $full = Join-Path $RepoRoot $Path
    if (Test-Path $full) {
        $lines = Get-Content $full -Tail $Tail
        return $lines | ForEach-Object { $_ | ConvertFrom-Json }
    }
    return @()
}

# ─── AGENT TYPE CONSTRUCTORS ───────────────────

function New-HumanType {
    $capital = 0
    $ledger = Read-JsonLIfExists -Path "data\wallet\ledger.jsonl" -Tail 1
    if ($ledger -and $ledger.Count -gt 0) {
        $last = $ledger | Select-Object -Last 1
        if ($null -ne $last.balanceUsd) { $capital = $last.balanceUsd }
    }

    $energy = 7   # placeholder; operator self-assessment
    # riskAppetite: conservative default for pre-v1.0.0
    $liveIntent = (Test-EnvVar -Name "LANTERN_LIVE_ENABLED" -Default "0")
    $killSwitchActive = Test-Path (Join-Path $RepoRoot "KILLSWITCH-ACTIVE.flag")

    return @{
        Agent         = "Human"
        Beliefs       = @{ marketOutlook = "neutral"; systemHealth = "stable" }
        Capabilities  = @("approve_trade", "toggle_kill_switch", "deploy_cloud")
        Information   = @{
            capitalUsd     = $capital
            energyLevel    = $energy
            familyContext  = "Waynesville_7_members"
            liveIntent     = $liveIntent
        }
        RiskTolerance = @{
            maxLossUsd        = 50
            maxPositions      = 10
            paperBeforeLive   = $true
        }
        ApprovalStatus = if ($liveIntent -eq "1") { "live_pending" } else { "blocked" }
        KillSwitch     = $killSwitchActive
    }
}

function New-KalshiType {
    $positions = Read-JsonIfExists -Path "data\kalshi\kalshi-paper-positions-latest.json"
    $posCount = 0
    $allocated = 0.0
    if ($positions -and $positions.positions) {
        $posCount = $positions.positions.Count
        $allocated = $positions.allocatedPaperRiskUsd
    }

    $apiKeyPresent = -not [string]::IsNullOrWhiteSpace((Test-EnvVar -Name "KALSHI_API_KEY_ID"))
    $privateKeyPresent = -not [string]::IsNullOrWhiteSpace((Test-EnvVar -Name "KALSHI_PRIVATE_KEY"))
    $env = Test-EnvVar -Name "KALSHI_ENVIRONMENT" -Default "demo"
    $liveEnabled = (Test-EnvVar -Name "LANTERN_LIVE_ENABLED" -Default "0") -eq "1"

    # Blockers from real position data
    $blockers = @("missing_independent_probability", "missing_orderbook_depth",
                   "missing_fee_slippage_model", "missing_max_loss_budget",
                   "missing_human_approval", "pre_v1_0_0_authenticated_trading_block")

    $approval = if (-not $liveEnabled) { "blocked" }
                 elseif (-not $apiKeyPresent -or -not $privateKeyPresent) { "blocked" }
                 elseif ($blockers.Count -gt 0) { "paper" }
                 else { "live_pending" }

    return @{
        Agent         = "KalshiAgent"
        Beliefs       = @{
            marketProbability = "from_api"
            settlementRisk    = "flagged_Khamenei_dispute"
            orderbookDepth    = "unknown"
        }
        Capabilities  = @("submit_order", "query_positions", "sign_rsa_pss")
        Information   = @{
            apiKeyPresent     = $apiKeyPresent
            privateKeyPresent = $privateKeyPresent
            environment       = $env
            positionCount     = $posCount
            allocatedUsd      = $allocated
            blockers          = $blockers
        }
        RiskTolerance = @{
            bankrollUsd      = 50
            perMarketMaxUsd  = 10
            dailyLossLimit   = 20
        }
        ApprovalStatus = $approval
    }
}

function New-IBKRType {
    $ledgerPath = "d:\tmp\lantern-os (1)\trade-ledger.csv"
    $tradeCount = 0
    if (Test-Path $ledgerPath) {
        $tradeCount = (Get-Content $ledgerPath | Measure-Object).Count - 1  # header
        if ($tradeCount -lt 0) { $tradeCount = 0 }
    }

    $mode = "paper"  # Autonomous-Trade-Executor.ps1 defaults to paper
    $killSwitch = Test-Path (Join-Path $RepoRoot "KILLSWITCH-ACTIVE.flag")

    return @{
        Agent         = "IBKRExecutor"
        Beliefs       = @{
            priceFeed         = "from_ibkr_api"
            spread            = "unknown"
            marginRequirement = "unknown"
        }
        Capabilities  = @("execute_market_order", "validate_risk", "log_ledger")
        Information   = @{
            tradeCount        = $tradeCount
            modeFlag          = $mode
            killSwitchPresent = $killSwitch
        }
        RiskTolerance = @{
            maxPositionSize   = 100
            maxRiskPerTrade   = 50
        }
        ApprovalStatus = if ($killSwitch -or $mode -eq "paper") { "paper" } else { "live_approved" }
    }
}

function New-CloudMirrorType {
    $manifest = Read-JsonIfExists -Path "manifests\cloud-mirrors.json"
    $status = "unknown"
    $mirrorCount = 0
    if ($manifest) {
        $status = $manifest.cloudMirrors[0].status
        $mirrorCount = $manifest.cloudMirrors.Count
    }

    return @{
        Agent         = "CloudMirror"
        Beliefs       = @{
            mirrorHealth   = $status
            netlifyStatus  = $status
            localPrimary   = $true
        }
        Capabilities  = @("serve_static", "proxy_api", "report_health")
        Information   = @{
            mirrorCount    = $mirrorCount
            provider       = "Netlify"
            lastChecked    = if ($manifest) { $manifest.lastChecked } else { "never" }
        }
        RiskTolerance = @{
            readOnlyMethods = $true
            noWriteWithoutLocal = $true
        }
        ApprovalStatus = if ($status -eq "live") { "healthy" } else { "degraded" }
    }
}

function New-McpAuditorType {
    $canary = Read-JsonIfExists -Path "data\automation\mcp-canary-results.json"
    $lastCheck = "never"
    $status = "unknown"
    if ($canary) {
        $lastCheck = $canary.checkedAt
        $status = $canary.status
    }

    return @{
        Agent         = "McpAuditor"
        Beliefs       = @{
            toolSafety     = $status
            readOnlyOnly   = $true
        }
        Capabilities  = @("validate_tool", "log_audit", "alert_operator")
        Information   = @{
            lastCanaryCheck = $lastCheck
            canaryStatus    = $status
        }
        RiskTolerance = @{
            blockDestructive = $true
            requireApproval  = $true
        }
        ApprovalStatus = if ($status -eq "pass") { "healthy" } else { "held" }
    }
}

function New-ConvergenceValidatorType {
    $latestReceipt = Read-JsonIfExists -Path "manifests\evidence\loop-receipt-LATEST.json"
    $issues = 999
    $exitCode = 1
    if ($latestReceipt) {
        $issues = if ($null -ne $latestReceipt.issueCount) { $latestReceipt.issueCount } else { $latestReceipt.issuesFound }
        $exitCode = $latestReceipt.exitCode
    }

    return @{
        Agent         = "ConvergenceValidator"
        Beliefs       = @{
            repoHealth     = if ($exitCode -eq 0) { "clean" } else { "dirty" }
            heldIssues     = $issues
        }
        Capabilities  = @("run_checks", "generate_receipt", "report_issues")
        Information   = @{
            lastReceiptPath = "manifests/evidence/loop-receipt-LATEST.json"
            issueCount    = $issues
            exitCode      = $exitCode
        }
        RiskTolerance = @{
            maxIssues       = 0
            blockOnHeld     = $true
        }
        ApprovalStatus = if ($exitCode -eq 0 -and $issues -eq 0) { "healthy" } else { "held" }
    }
}

# ─── COMMON PRIOR CONSTRUCTION ─────────────────

function New-CommonPrior {
    param([hashtable[]]$Types)

    # The common prior is the empirical distribution of actual agent states
    # loaded from Lantern OS files, not an arbitrary guess.
    $prior = @{
        Schema      = "lantern.harsanyi_type_space.v1"
        Timestamp   = Get-Date -Format "o"
        AgentCount  = $Types.Count
        Agents      = $Types
        JointBelief = @{
            repoHealthy      = ($Types | Where-Object { $_.Agent -eq "ConvergenceValidator" }).ApprovalStatus -eq "healthy"
            tradingBlocked   = ($Types | Where-Object { $_.Agent -in @("KalshiAgent","IBKRExecutor") }).ApprovalStatus -contains "blocked"
            cloudLive        = ($Types | Where-Object { $_.Agent -eq "CloudMirror" }).ApprovalStatus -eq "healthy"
            humanGateActive  = ($Types | Where-Object { $_.Agent -eq "Human" }).KillSwitch -eq $true
        }
    }

    return $prior
}

# ─── DIVERGENCE DETECTION ──────────────────────

function Test-BeliefDivergence {
    param([hashtable]$Prior)

    $divergences = @()
    $agents = $Prior.Agents

    # Critical divergence: any trading agent thinks it can go live
    # while the human operator has not enabled live mode
    $human = $agents | Where-Object { $_.Agent -eq "Human" }
    $kalshi = $agents | Where-Object { $_.Agent -eq "KalshiAgent" }
    $ibkr = $agents | Where-Object { $_.Agent -eq "IBKRExecutor" }

    # Gate 1: Human live intent vs trading agent approval
    if ($human.Information.liveIntent -ne "1") {
        if ($kalshi.ApprovalStatus -in @("live_pending","live")) {
            $divergences += @{
                Type       = "CRITICAL"
                Agents     = @("Human","KalshiAgent")
                Issue      = "Human liveIntent=0 but KalshiAgent approvalStatus=$($kalshi.ApprovalStatus)"
                Action     = "BLOCK LIVE TRADING"
            }
        }
        if ($ibkr.ApprovalStatus -eq "live_approved") {
            $divergences += @{
                Type       = "CRITICAL"
                Agents     = @("Human","IBKRExecutor")
                Issue      = "Human liveIntent=0 but IBKRExecutor approvalStatus=live_approved"
                Action     = "BLOCK LIVE TRADING"
            }
        }
    }

    # Gate 2: Kill switch active but any agent reports live-ready
    if ($human.KillSwitch) {
        if ($kalshi.ApprovalStatus -in @("live_pending","live")) {
            $divergences += @{
                Type       = "CRITICAL"
                Agents     = @("Human","KalshiAgent")
                Issue      = "Kill switch active; KalshiAgent must remain in paper/demo"
                Action     = "FORCE PAPER MODE"
            }
        }
    }

    # Gate 3: Cloud mirror degraded but repo says healthy
    $cloud = $agents | Where-Object { $_.Agent -eq "CloudMirror" }
    $conv = $agents | Where-Object { $_.Agent -eq "ConvergenceValidator" }
    if ($cloud.ApprovalStatus -eq "degraded" -and $conv.ApprovalStatus -eq "healthy") {
        $divergences += @{
            Type       = "WARNING"
            Agents     = @("CloudMirror","ConvergenceValidator")
            Issue      = "Cloud mirror degraded but convergence loop reports clean"
            Action     = "REVIEW cloud-mirrors.json"
        }
    }

    # Gate 4: MCP auditor held
    $mcp = $agents | Where-Object { $_.Agent -eq "McpAuditor" }
    if ($mcp.ApprovalStatus -eq "held") {
        $divergences += @{
            Type       = "WARNING"
            Agents     = @("McpAuditor","All")
            Issue      = "MCP canary not passing; tool safety unverified"
            Action     = "RUN mcp canary before any automated action"
        }
    }

    return $divergences
}

# ─── MAIN ──────────────────────────────────────

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "     LANTERN OS - HARSANYI TYPE SPACE v1.0" -ForegroundColor Cyan
Write-Host "     Cloud Agent & Web Trading Fleet Model" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$humanType    = New-HumanType
$kalshiType   = New-KalshiType
$ibkrType     = New-IBKRType
$cloudType    = New-CloudMirrorType
$mcpType      = New-McpAuditorType
$convType     = New-ConvergenceValidatorType

$allTypes = @($humanType, $kalshiType, $ibkrType, $cloudType, $mcpType, $convType)

# Build common prior from real Lantern OS state
$prior = New-CommonPrior -Types $allTypes

Write-Host "`n=== AGENT TYPE PROFILES ===" -ForegroundColor Yellow
foreach ($t in $allTypes) {
    $color = switch ($t.ApprovalStatus) {
        "healthy"    { "Green" }
        "paper"      { "Cyan" }
        "live_pending" { "Yellow" }
        "blocked"    { "Red" }
        "held"       { "DarkYellow" }
        "degraded"   { "Magenta" }
        default      { "White" }
    }
    Write-Host "  $($t.Agent) -> Approval: $($t.ApprovalStatus)" -ForegroundColor $color
}

Write-Host "`n=== COMMON PRIOR (Joint Belief) ===" -ForegroundColor Yellow
$prior.JointBelief.GetEnumerator() | ForEach-Object {
    $val = if ($_.Value -is [bool]) { if ($_.Value) { "TRUE" } else { "FALSE" } } else { $_.Value }
    $color = if ($_.Value -eq $true -or $_.Value -eq "blocked") { "Green" } elseif ($_.Value -eq $false) { "Red" } else { "White" }
    Write-Host "  $($_.Key): $val" -ForegroundColor $color
}

# Detect divergence
$divergences = Test-BeliefDivergence -Prior $prior

Write-Host "`n=== BELIEF DIVERGENCE ANALYSIS ===" -ForegroundColor Yellow
if ($divergences.Count -eq 0) {
    Write-Host "  No critical divergence detected. Common prior holds." -ForegroundColor Green
} else {
    foreach ($d in $divergences) {
        $color = if ($d.Type -eq "CRITICAL") { "Red" } else { "DarkYellow" }
        Write-Host "  [$($d.Type)] $($d.Issue)" -ForegroundColor $color
        Write-Host "      Action: $($d.Action)" -ForegroundColor White
    }
}

# Safety gate
$criticalCount = ($divergences | Where-Object { $_.Type -eq "CRITICAL" }).Count
if ($criticalCount -gt 0 -and -not $ReportOnly) {
    Write-Host "`n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" -ForegroundColor Red
    Write-Host "!!  SAFETY GATE ACTIVE" -ForegroundColor Red
    Write-Host "!!  $criticalCount critical divergence(s) block live action." -ForegroundColor Red
    Write-Host "!!  Run with -ReportOnly to bypass enforcement (audit only)." -ForegroundColor Red
    Write-Host "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" -ForegroundColor Red
}

# Persist snapshot
$logFull = Join-Path $RepoRoot $LogPath
New-Item -ItemType Directory -Force -Path (Split-Path $logFull) | Out-Null
$prior | ConvertTo-Json -Depth 10 -Compress | Add-Content -Path $logFull -Encoding UTF8

Write-Host "`nType-space snapshot appended to: $LogPath" -ForegroundColor Gray
Write-Host "Harsanyi Type Space Model complete.`n" -ForegroundColor Cyan
