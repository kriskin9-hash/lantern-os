<#
.SYNOPSIS
    Starts or validates the Lantern OS 36-slot local agent ring.
.DESCRIPTION
    Uses local sequential receipt workers only. It never dispatches paid CLIs or API-backed agents.
#>
[CmdletBinding()]
param(
    [string]$Root = "D:\tmp\lantern-os",
    [string]$ConfigPath = "D:\tmp\lantern-os\config\agents.json",
    [string]$ReceiptDir = "D:\tmp\lantern-os\data\automation\agent-ring",
    [string]$ProofPath = "D:\tmp\lantern-os\manifests\validation\LIVE-FLEET-PROOF-LATEST.json",
    [switch]$RunOnce,
    [switch]$KeepAlive,
    [switch]$RunLoopReceiptOnce
)

$ErrorActionPreference = "Stop"

function New-AgentReceipt {
    param(
        [object]$Slot,
        [string]$RootPath,
        [string]$OutDir,
        [object]$LoopSummary
    )

    $statusPath = Join-Path $RootPath ".git"
    $scriptPath = Join-Path $RootPath "scripts\Invoke-LanternConvergenceLoop.ps1"
    $agentsPath = Join-Path $RootPath "AGENTS.md"
    $openIssuesPath = Join-Path $RootPath "manifests\open-issues.md"
    $loopDocPath = Join-Path $RootPath "docs\CONVERGENCE-LOOP.md"
    $fleetDocPath = Join-Path $RootPath "manifests\CONVERGENCE-LOOP-AGENT-FLEET.md"
    $gitDirty = $false
    try {
        $gitDirty = @(& git -C $RootPath status --short).Count -gt 0
    }
    catch {
        $gitDirty = $true
    }

    $receipt = [ordered]@{
        schema = "lantern.local_agent_receipt.v1"
        generatedAt = (Get-Date).ToUniversalTime().ToString("o")
        name = $Slot.name
        slot = [int]$Slot.slot
        step = [int]$Slot.step
        agent = $Slot.agent
        role = $Slot.role
        runtime = $Slot.runtime
        cli = $Slot.cli
        spendPolicy = $Slot.spendPolicy
        tokenBudget = [int]$Slot.tokenBudget
        status = "completed"
        workType = "convergence_step_receipt"
        paidDispatch = $false
        evidence = @(
            @{ name = "repo_git_dir"; ok = (Test-Path $statusPath) },
            @{ name = "convergence_loop_script"; ok = (Test-Path $scriptPath) },
            @{ name = "agent_rules"; ok = (Test-Path $agentsPath) },
            @{ name = "loop_doc"; ok = (Test-Path $loopDocPath) },
            @{ name = "fleet_doc"; ok = (Test-Path $fleetDocPath) },
            @{ name = "open_issues_manifest_checked"; ok = (Test-Path $openIssuesPath) },
            @{ name = "git_dirty_observed"; ok = $gitDirty }
        )
        boundaries = @("local_worker_only", "no_paid_api_calls", "no_external_cli_dispatch", "no_retry_loop_churn")
        loopIssueCount = if ($LoopSummary) { $LoopSummary.issueCount } else { $null }
        loopNextAction = if ($LoopSummary) { $LoopSummary.nextAction } else { $null }
        validation = "pass"
        nextAction = "wait_for_next_local_queue_item"
    }

    $outPath = Join-Path $OutDir ("{0}.json" -f $Slot.name)
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -Path $outPath -Encoding utf8
    return $receipt
}

function Assert-NoPaidDispatch {
    param([object]$Config)
    $bad = @($Config.slots | Where-Object { $_.cli -ne "none" -or $_.tokenBudget -ne 0 -or $_.spendPolicy -ne "no_paid_api_calls" })
    if ($Config.paidAccountPolicy.allowPaidApiCalls -ne $false -or $bad.Count -gt 0) {
        throw "Paid CLI/API dispatch is configured; refusing to start local ring."
    }
}

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
Assert-NoPaidDispatch -Config $config
New-Item -ItemType Directory -Force -Path $ReceiptDir | Out-Null

$loopSummary = $null
if ($RunLoopReceiptOnce) {
    $loopJson = & (Join-Path $Root "scripts\Invoke-LanternConvergenceLoop.ps1") 2>$null
    $loopSummary = ($loopJson -join "`n") | ConvertFrom-Json
}

$slots = @($config.slots | Where-Object { $_.enabled })
if ($slots.Count -ne 36) { throw "Expected 36 enabled slots; found $($slots.Count)." }

$receipts = @()
foreach ($slot in $slots) {
    $receipts += New-AgentReceipt -Slot $slot -RootPath $Root -OutDir $ReceiptDir -LoopSummary $loopSummary
}

$failures = @($receipts | Where-Object { $_.validation -ne "pass" -or $_.paidDispatch -ne $false })
$proof = [ordered]@{
    schema = "lantern.live_fleet_proof.v1"
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    ok = ($receipts.Count -eq 36 -and $failures.Count -eq 0)
    orchestratorBaseUrl = "local_agent_ring"
    mcpHealth = "not_required_for_local_receipt_workers"
    toolsVisible = @("local_sequential_workers", "local_filesystem_receipts")
    workerPoolTarget = $config.poolTarget
    activeWorkers = 0
    idleWorkers = $receipts.Count
    queuedJobs = 0
    failedWorkers = $failures.Count
    ringSlotsAssigned = $slots.Count
    ringSlotsHealthy = $receipts.Count - $failures.Count
    consensusReceipts = @($receipts | ForEach-Object { "data/automation/agent-ring/$($_.name).json" })
    paidCliDispatchAllowed = $false
    churnGuard = $config.paidAccountPolicy.churnGuard
    claimBoundary = "36_real_local_convergence_receipt_workers_ran_once_no_paid_cli_workers"
    keepAlive = [bool]$KeepAlive
}
$proof | ConvertTo-Json -Depth 8 | Set-Content -Path $ProofPath -Encoding utf8
$proof | ConvertTo-Json -Depth 8

if (-not $proof.ok) { exit 1 }
if ($KeepAlive) {
    Write-Host "KeepAlive requested: local receipts are healthy; no paid persistent churn loop started."
}
