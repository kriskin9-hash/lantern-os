param(
    [string]$InputPath = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "templates\coin-feasibility.csv"),
    [string]$OutputPath = "",
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputPath)) {
    throw "Input CSV not found: $InputPath"
}

$rows = Import-Csv -LiteralPath $InputPath
$results = foreach ($row in $rows) {
    $effectiveHashrate = [decimal]($row.effective_hashrate -as [decimal])
    $networkHashrate = [decimal]($row.network_hashrate -as [decimal])
    $blockReward = [decimal]($row.block_reward -as [decimal])
    $blocksPerDay = [decimal]($row.blocks_per_day -as [decimal])
    $poolFee = [decimal]($row.pool_fee -as [decimal])
    $spotPrice = [decimal]($row.spot_price_usd -as [decimal])
    $watts = [decimal]($row.watts -as [decimal])
    $hoursPerDay = [decimal]($row.hours_per_day -as [decimal])
    $powerRate = [decimal]($row.power_usd_per_kwh -as [decimal])

    $coinsPerDay = [decimal]0
    if ($effectiveHashrate -gt 0 -and $networkHashrate -gt 0 -and $blockReward -gt 0 -and $blocksPerDay -gt 0) {
        $coinsPerDay = ($effectiveHashrate / $networkHashrate) * $blockReward * $blocksPerDay * (1 - $poolFee)
    }
    $grossUsdDay = $coinsPerDay * $spotPrice
    $powerUsdDay = ($watts / 1000) * $hoursPerDay * $powerRate
    $netUsdDay = $grossUsdDay - $powerUsdDay

    $decision = if ($row.verdict -match "reject|wallet|only|experiment|do_not_route") {
        $row.verdict
    } elseif ($netUsdDay -gt 0) {
        "candidate_after_live_refresh"
    } else {
        "reject_until_validated"
    }

    [pscustomobject]@{
        coin = $row.coin
        required_hardware = $row.required_hardware
        coins_per_day = [math]::Round([double]$coinsPerDay, 12)
        gross_usd_day = [math]::Round([double]$grossUsdDay, 4)
        power_usd_day = [math]::Round([double]$powerUsdDay, 4)
        net_usd_day = [math]::Round([double]$netUsdDay, 4)
        decision = $decision
        source_url = $row.source_url
        notes = $row.notes
    }
}

if ($OutputPath) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
    $results | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8
}

if ($AsJson) {
    $results | ConvertTo-Json -Depth 4
} else {
    $results
}
