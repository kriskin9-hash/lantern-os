param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("wallet_event", "profile_report", "founder_report", "validate_pdf", "perfect_loop")]
    [string]$Action,
    [string]$Root = "",
    [string]$PersonId = "founder",
    [string]$ReportTitle = "COMET LEAP Founder Perfect Report",
    [string]$Source = "reports/FOUNDER-TOPLEVEL-RAG-MASTER-REPORT-2026-05-27.md",
    [string]$Output = "artifacts/FOUNDER-TOPLEVEL-RAG-MASTER-REPORT-2026-05-27-v4-tesseract-dark-wcag-prominent.pdf",
    [int]$Iterations = 1,
    [string]$Event = "",
    [string]$Status = "recorded",
    [decimal]$AmountUsd = 0,
    [string]$InvoiceId = "",
    [string]$Offer = "",
    [string]$Evidence = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Run-Script([string]$Path, [string[]]$Args) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Path @Args
}

$scripts = @{
    wallet   = Join-Path $Root "scripts/Add-WalletLedgerEvent.ps1"
    profile  = Join-Path $Root "scripts/New-PerfectProfileReport.ps1"
    founder  = Join-Path $Root "scripts/Build-PerfectArtPdf.founder-v4.dark.ps1"
    validate = Join-Path $Root "scripts/Validate-PerfectReportDesign.ps1"
}

switch ($Action) {
    "wallet_event" {
        if ([string]::IsNullOrWhiteSpace($Event)) { throw "Event is required for wallet_event." }
        Run-Script $scripts.wallet @(
            "-Event", $Event, "-Status", $Status, "-AmountUsd", "$AmountUsd",
            "-InvoiceId", $InvoiceId, "-Offer", $Offer, "-Evidence", $Evidence
        )
    }
    "profile_report" {
        Run-Script $scripts.profile @("-PersonId", $PersonId, "-ReportTitle", $ReportTitle)
    }
    "founder_report" {
        Run-Script $scripts.founder @("-Source", $Source, "-Output", $Output)
        Run-Script $scripts.validate @("-MarkdownPath", $Source, "-PdfPath", $Output)
    }
    "validate_pdf" {
        Run-Script $scripts.validate @("-MarkdownPath", $Source, "-PdfPath", $Output)
    }
    "perfect_loop" {
        if ($Iterations -lt 1) { throw "Iterations must be >= 1." }
        for ($i = 1; $i -le $Iterations; $i++) {
            Run-Script $scripts.profile @("-PersonId", $PersonId, "-ReportTitle", "$ReportTitle (loop $i)")
        }
    }
}
