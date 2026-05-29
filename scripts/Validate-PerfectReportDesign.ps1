param(
    [Parameter(Mandatory = $true)]
    [string]$MarkdownPath,
    [Parameter(Mandatory = $true)]
    [string]$PdfPath,
    [string]$Root = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$md = Join-Path $Root $MarkdownPath
$pdf = Join-Path $Root $PdfPath
$builder = Join-Path $Root "scripts/Build-PerfectArtPdf.ps1"

if (-not (Test-Path -LiteralPath $md)) { throw "Missing markdown: $md" }
if (-not (Test-Path -LiteralPath $pdf)) { throw "Missing pdf: $pdf" }
if (-not (Test-Path -LiteralPath $builder)) { throw "Missing reportlab art builder: $builder" }

$mdText = Get-Content -LiteralPath $md -Raw
if ($mdText -notmatch "(?m)^#\s+") { throw "Design validation failed: report must contain H1 heading." }
if ($mdText -notmatch "(?m)^##\s+") { throw "Design validation failed: report must contain section headings." }
if ($mdText -notmatch "(?m)^\|.*\|") { throw "Design validation failed: report must contain at least one evidence table." }

$pdfItem = Get-Item -LiteralPath $pdf
if ($pdfItem.Length -lt 8192) { throw "Design validation failed: PDF appears too small ($($pdfItem.Length) bytes)." }

Write-Output ("DESIGN_OK md={0} pdf={1} bytes={2}" -f $md, $pdf, $pdfItem.Length)
