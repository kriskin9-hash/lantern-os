# PBFT Consensus Module for Suzie Orchestrator
# Byzantine Fault Tolerant consensus across distributed operator slots
#
# Protocol: Practical Byzantine Fault Tolerance (PBFT)
# Guarantees: No single operator failure cascades; requires 2n/3 + 1 consensus

param(
    [string]$Action = "init",
    [string]$OperatorId = $env:COMPUTERNAME,
    [string]$ProposalId = "",
    [string]$ProposalData = ""
)

$ConsensusDir = "$env:USERPROFILE\.suzie\consensus"
$ConsensusLedger = "$ConsensusDir\consensus-ledger.jsonl"
$LocalState = "$ConsensusDir\local-state-$OperatorId.json"
$ViewStateFile = "$ConsensusDir\view-state.json"

function Initialize-ConsensusState {
    <#
    .SYNOPSIS
    Initialize PBFT state on this operator PC.
    #>
    if (-not (Test-Path $ConsensusDir)) {
        New-Item -ItemType Directory -Force -Path $ConsensusDir | Out-Null
    }

    # Create local state
    $state = @{
        operator_id = $OperatorId
        initialized_at = Get-Date -AsUTC
        last_checkpoint = 0
        consensus_round = 0
        accepted_proposals = @()
    }

    $state | ConvertTo-Json | Out-File -Path $LocalState -Force

    # Create or read view state (shared across network, coordinated via MCP)
    if (-not (Test-Path $ViewStateFile)) {
        $viewState = @{
            current_view = 0
            primary_operator = "pc-1"
            n_operators = 20
            f_tolerance = 6  # floor(20-1/3) = 6 Byzantine operators tolerated
            last_update = Get-Date -AsUTC
            quorum_size = 15  # 2*6 + 3 = 15 required for consensus
        }
        $viewState | ConvertTo-Json | Out-File -Path $ViewStateFile -Force
    }

    Write-Host "[✓] PBFT Consensus initialized for $OperatorId"
}

function Propose-Task {
    <#
    .SYNOPSIS
    Propose a task for consensus.

    .PARAMETER ProposalId
    Unique task ID (UUID or sequential)

    .PARAMETER ProposalData
    JSON string containing task details (cmd, args, priority, deadline)

    .EXAMPLE
    Propose-Task -ProposalId "task-12345" -ProposalData '{"cmd": "test", "args": "..."}'
    #>

    $viewState = Get-Content $ViewStateFile | ConvertFrom-Json
    $consensusRound = $viewState.current_view

    $proposal = @{
        proposal_id = $ProposalId
        operator_id = $OperatorId
        timestamp = Get-Date -AsUTC
        consensus_round = $consensusRound
        data = $ProposalData
        status = "proposed"
        votes = @($OperatorId)  # Operator votes for own proposal
    }

    # Log proposal
    Add-ConsensusLogEntry -Entry $proposal
    Write-Host "[→] Proposal $ProposalId submitted by $OperatorId in round $consensusRound"
}

function Validate-ProposalSignature {
    <#
    .SYNOPSIS
    Validate proposal using HMAC-SHA256 (simplified PBFT without full PKI).
    #>
    param(
        [string]$ProposalId,
        [string]$Data,
        [string]$Signature,
        [string]$OperatorId
    )

    # In production: verify Ed25519 signature with operator public key
    # Here: use shared HMAC key for simplicity
    $HmacKey = "lantern-pbft-consensus-key-20260525"
    $ExpectedSig = [Convert]::ToBase64String(
        [System.Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($HmacKey)).ComputeHash(
            [Text.Encoding]::UTF8.GetBytes("$ProposalId|$Data")
        )
    )

    return $ExpectedSig -eq $Signature
}

function Collect-Consensus {
    <#
    .SYNOPSIS
    Collect votes from all operators and finalize if quorum reached.
    #>
    param(
        [string]$ProposalId
    )

    $ledger = Get-ConsensusLedger
    $proposal = $ledger | Where-Object { $_.proposal_id -eq $ProposalId } | Select-Object -Last 1

    if (-not $proposal) {
        Write-Host "[!] Proposal not found: $ProposalId"
        return $false
    }

    $viewState = Get-Content $ViewStateFile | ConvertFrom-Json
    $quorumSize = $viewState.quorum_size

    if ($proposal.votes.Count -ge $quorumSize) {
        # Consensus reached
        $proposal.status = "finalized"
        Add-ConsensusLogEntry -Entry $proposal

        Write-Host "[✓] CONSENSUS REACHED: $ProposalId (votes: $($proposal.votes.Count)/$quorumSize)"
        return $true
    } else {
        Write-Host "[⏳] Waiting for consensus on $ProposalId (votes: $($proposal.votes.Count)/$quorumSize)"
        return $false
    }
}

function Add-Vote {
    <#
    .SYNOPSIS
    Operator votes on a proposal.
    #>
    param(
        [string]$ProposalId,
        [string]$VotingOperatorId
    )

    $ledger = Get-ConsensusLedger
    $proposal = $ledger | Where-Object { $_.proposal_id -eq $ProposalId } | Select-Object -Last 1

    if (-not $proposal) {
        Write-Host "[!] Proposal not found: $ProposalId"
        return
    }

    if ($proposal.votes -notcontains $VotingOperatorId) {
        $proposal.votes += $VotingOperatorId
    }

    Add-ConsensusLogEntry -Entry $proposal
    Write-Host "  ✓ Vote from $VotingOperatorId on $ProposalId ($($proposal.votes.Count) total)"
}

function Get-ConsensusLedger {
    <#
    .SYNOPSIS
    Read entire consensus ledger from JSONL file.
    #>
    if (-not (Test-Path $ConsensusLedger)) {
        return @()
    }

    Get-Content $ConsensusLedger | ConvertFrom-Json
}

function Add-ConsensusLogEntry {
    <#
    .SYNOPSIS
    Append entry to consensus ledger (JSONL format).
    #>
    param([object]$Entry)

    if (-not (Test-Path $ConsensusLedger)) {
        New-Item -ItemType File -Path $ConsensusLedger -Force | Out-Null
    }

    $Entry | ConvertTo-Json -Compress | Add-Content -Path $ConsensusLedger
}

function Report-ConsensusStatus {
    <#
    .SYNOPSIS
    Display current consensus state and recent proposals.
    #>
    Write-Host "`n=== PBFT Consensus Status ===" -ForegroundColor Cyan
    Write-Host "Operator: $OperatorId"
    Write-Host "State: $(Test-Path $LocalState ? 'Initialized' : 'Not Initialized')"

    if (Test-Path $ViewStateFile) {
        $view = Get-Content $ViewStateFile | ConvertFrom-Json
        Write-Host "Current View: $($view.current_view)"
        Write-Host "Primary: $($view.primary_operator)"
        Write-Host "N: $($view.n_operators), F: $($view.f_tolerance), Quorum: $($view.quorum_size)"
    }

    Write-Host "`nRecent Proposals:"
    $ledger = Get-ConsensusLedger
    $ledger | Select-Object -Last 5 | ForEach-Object {
        $status = $_.status
        $statusColor = if ($status -eq "finalized") { "Green" } elseif ($status -eq "proposed") { "Yellow" } else { "Red" }
        Write-Host "  [$($_.proposal_id)] $status (votes: $($_.votes.Count)) - $($_.operator_id)" -ForegroundColor $statusColor
    }

    Write-Host ""
}

function Rotate-Primary {
    <#
    .SYNOPSIS
    Rotate primary operator (if current primary fails).
    #>
    $viewState = Get-Content $ViewStateFile | ConvertFrom-Json

    # Simple round-robin: next in operator list
    $operators = 1..$viewState.n_operators | ForEach-Object { "pc-$_" }
    $currentIndex = $operators.IndexOf($viewState.primary_operator)
    $nextPrimary = $operators[($currentIndex + 1) % $viewState.n_operators]

    $viewState.primary_operator = $nextPrimary
    $viewState.current_view += 1
    $viewState.last_update = Get-Date -AsUTC

    $viewState | ConvertTo-Json | Out-File -Path $ViewStateFile -Force

    Write-Host "[!] Primary rotated: $($viewState.primary_operator) (view $($viewState.current_view))"
}

# Main dispatcher
switch ($Action) {
    "init" { Initialize-ConsensusState }
    "propose" { Propose-Task -ProposalId $ProposalId -ProposalData $ProposalData }
    "vote" { Add-Vote -ProposalId $ProposalId -VotingOperatorId $OperatorId }
    "collect" { Collect-Consensus -ProposalId $ProposalId }
    "status" { Report-ConsensusStatus }
    "rotate" { Rotate-Primary }
    default {
        Write-Host "Usage: pbft-consensus.ps1 -Action [init|propose|vote|collect|status|rotate] [options]"
    }
}
