$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$htmlPath = Join-Path $root "surfaces\tony-garage\index.html"
$sharedCssPath = Join-Path $root "surfaces\shared-canonical.css"

foreach ($path in @($htmlPath, $sharedCssPath)) {
    if (-not (Test-Path $path)) { throw "Missing surface file: $path" }
}

$html = Get-Content -LiteralPath $htmlPath -Raw
$css = Get-Content -LiteralPath $sharedCssPath -Raw

$checks = @(
    [pscustomobject]@{ name = "doctype"; ok = $html -match "(?is)<!doctype html>" },
    [pscustomobject]@{ name = "viewport"; ok = $html -match 'name="viewport"' },
    [pscustomobject]@{ name = "canonical-url"; ok = $html -match 'http://127\.0\.0\.1:4177/' },
    [pscustomobject]@{ name = "meta-refresh"; ok = $html -match 'http-equiv="refresh"' },
    [pscustomobject]@{ name = "one-dashboard-copy"; ok = $html -match 'One Dashboard' },
    [pscustomobject]@{ name = "shared-canonical-css"; ok = $html -match '../shared-canonical\.css' },
    [pscustomobject]@{ name = "light-cockpit-style"; ok = $css -match '--arc: #08756f' }
)

$failed = @($checks | Where-Object { -not $_.ok })
$result = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    ok = ($failed.Count -eq 0)
    failed = $failed
    checks = $checks
}

$outPath = Join-Path $root "manifests\validation\TONY-GARAGE-SURFACE-LATEST.json"
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outPath -Encoding UTF8

if ($failed.Count -gt 0) {
    $failed | Format-Table -AutoSize
    throw "Tony Garage surface validation failed."
}

Write-Output $outPath
