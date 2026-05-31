param(
    [string]$Root           = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$JobsConfig     = "config/batch-jobs.json",
    [string]$Group          = "",
    [switch]$RunOnce,
    [switch]$DryRun,
    [switch]$ListJobs,
    [int]$MainLoopIntervalMinutes = 10
)

$ErrorActionPreference = "Stop"

$logDir  = Join-Path $Root "data/automation/logs"
$dataDir = Join-Path $Root "data/automation"
if (-not (Test-Path $logDir))  { New-Item -ItemType Directory -Path $logDir  -Force | Out-Null }
if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory -Path $dataDir -Force | Out-Null }
$logFile = Join-Path $logDir ("orchestrator-{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts    = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line  = "[$ts] [$Level] $Message"
    $color = switch ($Level) { "ERROR" { "Red" } "WARN" { "Yellow" } default { "White" } }
    Write-Host $line -ForegroundColor $color
    Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8
}

function Get-BatchJobs {
    $configFull = Join-Path $Root $JobsConfig
    if (-not (Test-Path $configFull)) {
        Write-Log "Job config not found: $configFull" "WARN"
        return @()
    }
    $cfg  = Get-Content -LiteralPath $configFull -Raw | ConvertFrom-Json
    $jobs = @($cfg.jobs)
    if ($Group) { $jobs = @($jobs | Where-Object { $_.group -eq $Group }) }
    return @($jobs | Where-Object { $_.enabled -eq $true } | Sort-Object priority)
}

function Invoke-BatchJob {
    param([object]$Job)
    $scriptFull = Join-Path $Root $Job.script
    $jobId      = $Job.id
    $startedAt  = Get-Date
    if (-not (Test-Path $scriptFull)) {
        Write-Log "[$jobId] Script not found: $($Job.script)" "WARN"
        return [pscustomobject]@{ id=$jobId; status="skipped"; reason="script_not_found"; exitCode=$null; durationMs=0; startedAt=$startedAt.ToString("o") }
    }
    Write-Log "[$jobId] Starting: $($Job.name)"
    if ($DryRun) {
        Write-Log "[$jobId] [DRY RUN] $scriptFull $($Job.args -join ' ')"
        return [pscustomobject]@{ id=$jobId; status="dry-run"; reason="dry_run"; exitCode=0; durationMs=0; startedAt=$startedAt.ToString("o") }
    }
    try {
        $argList = @($Job.args) | Where-Object { $_ }
        $proc    = Start-Process powershell -ArgumentList (@("-NoProfile","-ExecutionPolicy","Bypass","-File",$scriptFull) + $argList) -PassThru -NoNewWindow -Wait
        $code    = $proc.ExitCode
        $ms      = [int]((Get-Date) - $startedAt).TotalMilliseconds
        $stat    = if ($code -eq 0) { "ok" } else { "failed" }
        Write-Log "[$jobId] $stat (exit=$code, ${ms}ms)" $(if ($code -eq 0) { "INFO" } else { "WARN" })
        return [pscustomobject]@{ id=$jobId; status=$stat; reason=$null; exitCode=$code; durationMs=$ms; startedAt=$startedAt.ToString("o") }
    } catch {
        $ms = [int]((Get-Date) - $startedAt).TotalMilliseconds
        Write-Log "[$jobId] ERROR: $_" "ERROR"
        return [pscustomobject]@{ id=$jobId; status="error"; reason=$_.Exception.Message; exitCode=-1; durationMs=$ms; startedAt=$startedAt.ToString("o") }
    }
}

function Write-RunReceipt {
    param([array]$JobResults)
    $stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
    $outDir = Join-Path $Root "manifests/evidence"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $ok      = @($JobResults | Where-Object { $_.status -eq "ok" }).Count
    $failed  = @($JobResults | Where-Object { $_.status -in @("failed","error") }).Count
    $skipped = @($JobResults | Where-Object { $_.status -in @("skipped","dry-run") }).Count
    $receipt = [ordered]@{
        receiptId     = "orchestrator-$stamp"
        generatedAt   = (Get-Date).ToString("o")
        evidenceClass = "batch_orchestrator_run"
        dryRun        = $DryRun.IsPresent
        summary       = [ordered]@{ total=$JobResults.Count; ok=$ok; failed=$failed; skipped=$skipped; passed=($failed -eq 0) }
        jobs          = @($JobResults)
        boundary      = "No automated paid API calls. No autonomous action without human review gate."
    }
    $receiptFile = Join-Path $outDir "orchestrator-$stamp.json"
    $latestFile  = Join-Path $dataDir "orchestrator-results.json"
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptFile -Encoding UTF8
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $latestFile  -Encoding UTF8
    Write-Log "Receipt: $receiptFile"
    return $receipt
}

# --- List jobs mode ---
if ($ListJobs) {
    $jobs = Get-BatchJobs
    Write-Host "`n=== Registered Batch Jobs ===" -ForegroundColor Cyan
    foreach ($j in $jobs) {
        Write-Host ("  [p{0}] {1,-38} every {2}min  [{3}]" -f $j.priority, $j.id, $j.intervalMinutes, $j.group)
    }
    exit 0
}

# --- Main ---
Write-Log "=== Automation Orchestrator Started (RunOnce=$RunOnce DryRun=$DryRun) ==="

# Run health check first
$healthScript = Join-Path $Root "scripts/Invoke-HealthCheck.ps1"
if (Test-Path $healthScript) {
    Write-Log "Running health check..."
    try { & powershell -NoProfile -ExecutionPolicy Bypass -File $healthScript 2>&1 | ForEach-Object { Write-Log $_ } }
    catch { Write-Log "Health check error: $_" "WARN" }
}

do {
    $jobs       = Get-BatchJobs
    $jobResults = [System.Collections.Generic.List[object]]::new()
    Write-Log "--- Batch run: $($jobs.Count) enabled jobs ---"

    foreach ($job in $jobs) {
        $result = Invoke-BatchJob -Job $job
        $jobResults.Add($result)
        if ($result.status -eq "error" -and $job.failurePolicy -eq "stop") {
            Write-Log "[$($job.id)] failurePolicy=stop, halting" "ERROR"
            break
        }
    }

    $receipt = Write-RunReceipt -JobResults $jobResults
    $f = $receipt.summary.failed
    if ($f -eq 0) {
        Write-Host "`n=== Batch complete: $($receipt.summary.ok)/$($receipt.summary.total) ok ===" -ForegroundColor Green
    } else {
        Write-Host "`n=== Batch complete: $($receipt.summary.ok) ok, $f failed ===" -ForegroundColor Yellow
    }

    if ($RunOnce) { break }
    Write-Log "Next cycle in $MainLoopIntervalMinutes minutes"
    Start-Sleep -Seconds ($MainLoopIntervalMinutes * 60)

} while ($true)

Write-Log "=== Automation Orchestrator Completed ==="