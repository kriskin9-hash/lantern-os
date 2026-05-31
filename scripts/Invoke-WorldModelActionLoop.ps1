param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$RunOnce,
    [switch]$AutoApproveSafe,
    [switch]$DryRun,
    [int]$IntervalSeconds = 300,
    [string]$ZipPath = "C:\Users\alexp\Downloads\human-flourishing-frameworks-master.zip"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$Level] $Message"
    Write-Host $logLine
    $logDir = Join-Path $Root "data\automation"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    Add-Content -Path (Join-Path $logDir "world-model-action-loop.log") -Value $logLine
}

function Read-JsonOrNull {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { return $null }
}

function Get-JsonlRows {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return @() }
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($line in Get-Content -LiteralPath $Path -ErrorAction Stop) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try { $rows.Add(($line | ConvertFrom-Json -ErrorAction Stop)) | Out-Null }
        catch { }
    }
    return @($rows.ToArray())
}

function Invoke-HouseThinkerStep {
    param([string]$RepoRoot)
    $scriptPath = Join-Path $RepoRoot "scripts\Invoke-HouseThinker.ps1"
    $validationPath = Join-Path $RepoRoot "manifests\validation\HOUSE-THINKER-LATEST.json"
    if (-not (Test-Path $scriptPath)) {
        Write-Log "HouseThinker script not found: $scriptPath" "WARN"
        return $null
    }
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath -Once -Root $RepoRoot | Out-Null
        if (Test-Path $validationPath) {
            return (Get-Content $validationPath -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue)
        }
        return $null
    }
    catch {
        Write-Log "HouseThinker failed: $_" "ERROR"
        return $null
    }
}

function Invoke-ConvergenceStep {
    param([string]$RepoRoot)
    $scriptPath = Join-Path $RepoRoot "scripts\Invoke-LanternConvergenceLoop.ps1"
    if (-not (Test-Path $scriptPath)) {
        Write-Log "Convergence script not found: $scriptPath" "WARN"
        return $null
    }
    try {
        $json = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath
        return ($json | ConvertFrom-Json -ErrorAction SilentlyContinue)
    }
    catch {
        Write-Log "Convergence failed: $_" "ERROR"
        return $null
    }
}

function Get-WorldModelPredictions {
    param([string]$RepoRoot)
    $beliefPath = Join-Path $RepoRoot "data\world-model\belief-ledger.jsonl"
    $rows = Get-JsonlRows -Path $beliefPath

    $predictions = @()
    foreach ($row in $rows) {
        $posterior = [double]($row.posterior)
        $action = switch ($posterior) {
            { $_ -ge 0.90 } { "promote" }
            { $_ -ge 0.70 } { "candidate" }
            { $_ -ge 0.40 } { "backlog" }
            default { "reject" }
        }
        $predictions += [pscustomobject]@{
            claim = $row.claim
            posterior = $posterior
            action = $action
            evidenceClass = $row.evidenceClass
            decision = $row.decision
        }
    }
    return $predictions
}

function Test-ZipIntegration {
    param([string]$ZipFile, [string]$RepoRoot)
    if (-not (Test-Path $ZipFile)) {
        Write-Log "Zip file not found: $ZipFile" "WARN"
        return $null
    }
    $zipSize = (Get-Item $ZipFile).Length
    $extractDir = Join-Path $RepoRoot "data\archive-commons\zip-intake"
    New-Item -ItemType Directory -Force -Path $extractDir | Out-Null

    # Get zip manifest without extracting
    $entries = & python -c "import zipfile; z=zipfile.ZipFile(r'$ZipFile'); [print(e.filename) for e in z.infolist()]; z.close()" 2>$null
    $topLevel = $entries | Where-Object { $_ -match '^[^/]+/?$' } | Select-Object -First 1

    return [pscustomobject]@{
        zipPath = $ZipFile
        zipSize = $zipSize
        extractDir = $extractDir
        topLevelDir = $topLevel
        entryCount = ($entries | Measure-Object).Count
        action = "hold_for_review"
        reason = "Zip intake requires human approval before extraction into repo"
    }
}

function Request-HumanApproval {
    param(
        [string]$Prompt,
        [int]$TimeoutSeconds = 30
    )
    Write-Log "HUMAN APPROVAL REQUIRED: $Prompt" "WARN"
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  HUMAN IN THE LOOP GATE" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host $Prompt -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Auto-approve in $TimeoutSeconds seconds if no response..." -ForegroundColor Gray
    # Note: In a non-interactive IDE context, we default to hold
    Write-Log "Non-interactive mode: defaulting to HOLD" "WARN"
    return $false
}

function Execute-Action {
    param(
        [pscustomobject]$Action,
        [bool]$DryRun,
        [bool]$AutoApproveSafe
    )
    $name = $Action.name
    $safe = $Action.safe -eq $true
    $reversible = $Action.reversible -eq $true

    if ($DryRun) {
        Write-Log "[DRY RUN] Would execute: $name" "INFO"
        return $true
    }

    # Determine if human approval is needed
    $needsApproval = $true
    if ($AutoApproveSafe -and $safe -and $reversible) {
        $needsApproval = $false
    }

    if ($needsApproval) {
        $approved = Request-HumanApproval -Prompt "Approve action: $name (safe=$safe, reversible=$reversible)"
        if (-not $approved) {
            Write-Log "Action HELD by human gate: $name" "WARN"
            return $false
        }
    }

    Write-Log "Executing action: $name"
    try {
        if ($Action.script) {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $Action.script
        }
        elseif ($Action.command) {
            Invoke-Expression $Action.command
        }
        Write-Log "Action completed: $name"
        return $true
    }
    catch {
        Write-Log "Action failed: $name - $_" "ERROR"
        return $false
    }
}

function Write-ActionReceipt {
    param(
        [string]$RepoRoot,
        [array]$Predictions,
        [object]$ConvergenceResult,
        [object]$HouseThinkerResult,
        [object]$ZipStatus,
        [array]$ExecutedActions
    )
    $receiptDir = Join-Path $RepoRoot "data\automation"
    New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null
    $receiptPath = Join-Path $receiptDir "WORLD-MODEL-ACTION-RECEIPT-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"

    $receipt = [ordered]@{
        generatedAt = (Get-Date).ToString("o")
        mode = "world_model_action_loop"
        humanInTheLoop = $true
        autoApproveSafe = $AutoApproveSafe
        dryRun = $DryRun
        inputs = [ordered]@{
            beliefLedgerPredictions = $Predictions
            convergenceResult = $ConvergenceResult
            houseThinkerResult = $HouseThinkerResult
            zipStatus = $ZipStatus
        }
        executedActions = $ExecutedActions
        nextActions = @(
            "Review predictions above 0.70 posterior for promotion"
            "Address convergence held items"
            "Approve or reject zip intake"
            "Re-run loop after manual actions"
        )
        safeClaim = "World model action loop ran deterministically. All irreversible actions held for human approval."
    }

    $receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
    Write-Log "Receipt written: $receiptPath"
    return $receiptPath
}

# === MAIN LOOP ===
Write-Log "=== World Model Action Loop Started ==="

$cycle = 0
do {
    $cycle++
    Write-Log "--- Cycle $cycle ---"

    # 1. World Model Predictions
    Write-Log "Loading world model predictions..."
    $predictions = Get-WorldModelPredictions -RepoRoot $Root
    Write-Log "Belief ledger rows: $($predictions.Count)"
    foreach ($p in $predictions) {
        Write-Log "  Claim: $($p.claim.Substring(0,[Math]::Min(60,$p.claim.Length)))... | Posterior: $($p.posterior) | Action: $($p.action)"
    }

    # 2. HouseThinker Evidence Scan
    Write-Log "Running HouseThinker evidence scan..."
    $thinkerResult = Invoke-HouseThinkerStep -RepoRoot $Root
    if ($thinkerResult) {
        Write-Log "HouseThinker OK. Patent matches: $($thinkerResult.counts.patentEvidenceMatches), Convergence matches: $($thinkerResult.counts.convergenceEvidenceMatches)"
    }

    # 3. Convergence Audit
    Write-Log "Running convergence audit..."
    $convergenceResult = Invoke-ConvergenceStep -RepoRoot $Root
    if ($convergenceResult) {
        Write-Log "Convergence OK. Issues: $($convergenceResult.issueCount), Held: $($convergenceResult.held.Count)"
        foreach ($held in $convergenceResult.held) {
            Write-Log "  HELD: $($held.id) - $($held.summary)" "WARN"
        }
    }

    # 4. Zip File Check
    Write-Log "Checking zip intake..."
    $zipStatus = Test-ZipIntegration -ZipFile $ZipPath -RepoRoot $Root
    if ($zipStatus) {
        Write-Log "Zip found: $($zipStatus.zipPath) ($($zipStatus.zipSize) bytes, $($zipStatus.entryCount) entries)"
        Write-Log "Zip action: $($zipStatus.action) - $($zipStatus.reason)"
    }

    # 5. Propose Actions based on predictions + convergence
    $proposedActions = @()

    # Safe, reversible: log and auto-approve if AutoApproveSafe
    foreach ($p in $predictions | Where-Object { $_.action -eq "promote" -and $_.posterior -ge 0.90 }) {
        $proposedActions += [pscustomobject]@{
            name = "Promote claim: $($p.claim.Substring(0,[Math]::Min(40,$p.claim.Length)))"
            safe = $true
            reversible = $true
            script = $null
            command = $null
            reason = "Posterior >= 0.90"
        }
    }

    # Held convergence items -> propose manual action
    foreach ($held in $convergenceResult.held) {
        $proposedActions += [pscustomobject]@{
            name = "Address held item: $($held.id)"
            safe = $false
            reversible = $false
            script = $null
            command = $null
            reason = $held.summary
        }
    }

    # Zip intake -> always requires approval
    if ($zipStatus -and $zipStatus.zipSize -gt 0) {
        $proposedActions += [pscustomobject]@{
            name = "Extract zip intake: $($zipStatus.zipPath)"
            safe = $false
            reversible = $true
            script = $null
            command = "Expand-Archive -Path '$($zipStatus.zipPath)' -DestinationPath '$($zipStatus.extractDir)' -Force"
            reason = "New zip file detected"
        }
    }

    # 6. Execute approved actions
    $executed = @()
    foreach ($action in $proposedActions) {
        $success = Execute-Action -Action $action -DryRun $DryRun -AutoApproveSafe $AutoApproveSafe
        $executed += [pscustomobject]@{
            name = $action.name
            success = $success
            timestamp = (Get-Date).ToString("o")
        }
    }

    # 7. Write receipt
    $receiptPath = Write-ActionReceipt `
        -RepoRoot $Root `
        -Predictions $predictions `
        -ConvergenceResult $convergenceResult `
        -HouseThinkerResult $thinkerResult `
        -ZipStatus $zipStatus `
        -ExecutedActions $executed

    Write-Log "Cycle $cycle complete. Receipt: $receiptPath"

    if ($RunOnce) { break }
    if ($IntervalSeconds -gt 0) {
        Write-Log "Sleeping $($IntervalSeconds)s until next cycle..."
        Start-Sleep -Seconds $IntervalSeconds
    }
} while ($true)

Write-Log "=== World Model Action Loop Completed ==="
