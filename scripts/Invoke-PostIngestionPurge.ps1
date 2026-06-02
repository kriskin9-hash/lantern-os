param(
    [string]$Root                    = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [int]$ReportPdfRetentionDays     = 7,
    [int]$MaxReceiptsPerClass        = 30,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$stamp       = Get-Date -Format "yyyyMMdd-HHmmss"
$receiptFile = Join-Path $Root "manifests/evidence/purge-$stamp.json"
$cutoff      = (Get-Date).AddDays(-$ReportPdfRetentionDays)

Write-Host "=== Invoke-PostIngestionPurge ===" -ForegroundColor Cyan
Write-Host "Root           : $Root"
Write-Host "PDF retention  : $ReportPdfRetentionDays days (cutoff $($cutoff.ToString('yyyy-MM-dd')))"
Write-Host "Max receipts   : $MaxReceiptsPerClass per class"
if ($DryRun) { Write-Host "[DRY RUN]" -ForegroundColor Yellow }

$purgedPdfs      = [System.Collections.Generic.List[string]]::new()
$purgedReceipts  = [System.Collections.Generic.List[string]]::new()
$purgedKalshi    = [System.Collections.Generic.List[string]]::new()
$errors          = [System.Collections.Generic.List[string]]::new()

# ── 1. Report PDFs ────────────────────────────────────────────────────────────
# reports/PDF/ holds generated artifacts. After Sync-RagAndPdf ingests the
# source markdown into the RAG flat file the PDF is re-derivable. Purge any
# that are older than the retention window.

$pdfDir = Join-Path $Root "reports/PDF"
if (Test-Path $pdfDir) {
    $oldPdfs = Get-ChildItem -Path $pdfDir -Filter "*.pdf" -File |
               Where-Object { $_.LastWriteTime -lt $cutoff }
    foreach ($f in $oldPdfs) {
        Write-Host "  [PDF-PURGE] $($f.Name)" -ForegroundColor Yellow
        if (-not $DryRun) {
            try   { Remove-Item -LiteralPath $f.FullName -Force; $purgedPdfs.Add($f.Name) }
            catch { $errors.Add("pdf:$($f.Name):$($_.Exception.Message)") }
        } else {
            $purgedPdfs.Add($f.Name)
        }
    }
    Write-Host "  PDFs purged: $($purgedPdfs.Count)" -ForegroundColor $(if ($purgedPdfs.Count -gt 0) { 'Yellow' } else { 'Green' })
}

# ── 2. Evidence receipts ──────────────────────────────────────────────────────
# manifests/evidence/ accumulates one JSON/MD receipt per batch run. Keep the
# newest $MaxReceiptsPerClass files per evidence class prefix; drop the rest.
# Class is derived from the filename prefix before the first timestamp segment.

$evidenceDir = Join-Path $Root "manifests/evidence"
if (Test-Path $evidenceDir) {
    $receiptFiles = Get-ChildItem -Path $evidenceDir -File |
                    Where-Object { $_.Extension -in @('.json','.md') }

    # Group by class prefix (everything before the first -YYYYMMDD- or -2026- segment)
    $byClass = @{}
    foreach ($rf in $receiptFiles) {
        $prefix = $rf.BaseName -replace '-\d{8}.*$','' -replace '-2026-.*$',''
        if (-not $byClass.ContainsKey($prefix)) { $byClass[$prefix] = [System.Collections.Generic.List[object]]::new() }
        $byClass[$prefix].Add($rf)
    }

    foreach ($cls in $byClass.Keys) {
        $sorted = $byClass[$cls] | Sort-Object LastWriteTime -Descending
        $toDelete = $sorted | Select-Object -Skip $MaxReceiptsPerClass
        foreach ($f in $toDelete) {
            Write-Host "  [RECEIPT-PURGE] $($f.Name)" -ForegroundColor DarkYellow
            if (-not $DryRun) {
                try   { Remove-Item -LiteralPath $f.FullName -Force; $purgedReceipts.Add($f.Name) }
                catch { $errors.Add("receipt:$($f.Name):$($_.Exception.Message)") }
            } else {
                $purgedReceipts.Add($f.Name)
            }
        }
    }
    Write-Host "  Receipts purged: $($purgedReceipts.Count)" -ForegroundColor $(if ($purgedReceipts.Count -gt 0) { 'Yellow' } else { 'Green' })
}

# ── 3. Kalshi superseded data files ──────────────────────────────────────────
# data/kalshi/ keeps rolling *-latest.json snapshots plus dated backups with
# timestamps in their names. Files matching *-2026-*.json (or older years) that
# are NOT named *-latest.json and are older than the retention window are
# superseded by the latest snapshot and can be dropped.

$kalshiDir = Join-Path $Root "data/kalshi"
if (Test-Path $kalshiDir) {
    $superseded = Get-ChildItem -Path $kalshiDir -Filter "*.json" -File |
                  Where-Object {
                      $_.Name -notmatch '-latest\.json$' -and
                      $_.Name -match '-\d{4}-\d{2}-\d{2}' -and
                      $_.LastWriteTime -lt $cutoff
                  }
    foreach ($f in $superseded) {
        Write-Host "  [KALSHI-PURGE] $($f.Name)" -ForegroundColor DarkYellow
        if (-not $DryRun) {
            try   { Remove-Item -LiteralPath $f.FullName -Force; $purgedKalshi.Add($f.Name) }
            catch { $errors.Add("kalshi:$($f.Name):$($_.Exception.Message)") }
        } else {
            $purgedKalshi.Add($f.Name)
        }
    }
    Write-Host "  Kalshi files purged: $($purgedKalshi.Count)" -ForegroundColor $(if ($purgedKalshi.Count -gt 0) { 'Yellow' } else { 'Green' })
}

# ── Receipt ───────────────────────────────────────────────────────────────────
$receipt = [ordered]@{
    schema          = "lantern.purge_receipt.v1"
    generatedAt     = (Get-Date).ToString("o")
    evidenceClass   = "post_ingestion_purge"
    stamp           = $stamp
    dryRun          = $DryRun.IsPresent
    retentionDays   = $ReportPdfRetentionDays
    maxReceiptsPerClass = $MaxReceiptsPerClass
    purgedPdfs      = @($purgedPdfs)
    purgedReceipts  = @($purgedReceipts)
    purgedKalshi    = @($purgedKalshi)
    totalPurged     = $purgedPdfs.Count + $purgedReceipts.Count + $purgedKalshi.Count
    errors          = @($errors)
}

$receiptDir = Split-Path $receiptFile -Parent
if (-not (Test-Path $receiptDir)) { New-Item -ItemType Directory -Path $receiptDir -Force | Out-Null }
if (-not $DryRun) {
    $receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receiptFile -Encoding UTF8
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "PDFs purged      : $($purgedPdfs.Count)"
Write-Host "Receipts purged  : $($purgedReceipts.Count)"
Write-Host "Kalshi purged    : $($purgedKalshi.Count)"
Write-Host "Errors           : $($errors.Count)" -ForegroundColor $(if ($errors.Count -gt 0) { 'Red' } else { 'Green' })
if (-not $DryRun) { Write-Host "Receipt          : $receiptFile" -ForegroundColor Gray }

exit $(if ($errors.Count -gt 0) { 1 } else { 0 })
