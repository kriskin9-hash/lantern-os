$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$skill = Get-Content -LiteralPath (Join-Path $root "skills\solo-mining\SKILL.md") -Raw

$required = @(
    "wallet_bruteforce",
    "unauthorized_transfers",
    "hidden_transaction_signing",
    "mining_on_unowned_devices",
    "fake_roi_claims",
    "eth_mainnet_mining_claims",
    "cpu",
    "gpu",
    "asic_required"
)

foreach ($phrase in $required) {
    if ($skill -notlike "*$phrase*") {
        throw "Missing skill phrase: $phrase"
    }
}

$fixture = Join-Path $env:TEMP "lantern-mining-profit-fixture.csv"
$output = Join-Path $env:TEMP "lantern-mining-profit-output.csv"
@"
coin,network_status,practical_method,required_hardware,effective_hashrate,network_hashrate,block_reward,blocks_per_day,pool_fee,spot_price_usd,watts,hours_per_day,power_usd_per_kwh,verdict,source_url,notes
FIX,PoW,pool,fixture,100,1000,10,100,0.1,2,100,24,0.1,candidate,fixture,fixture
"@ | Set-Content -LiteralPath $fixture -Encoding ASCII

powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "scripts\Test-MiningProfitability.ps1") -InputPath $fixture -OutputPath $output | Out-Null
$row = Import-Csv -LiteralPath $output | Select-Object -First 1

if ([decimal]$row.coins_per_day -ne 90) { throw "coins_per_day mismatch: $($row.coins_per_day)" }
if ([decimal]$row.gross_usd_day -ne 180) { throw "gross_usd_day mismatch: $($row.gross_usd_day)" }
if ([decimal]$row.power_usd_day -ne 0.24) { throw "power_usd_day mismatch: $($row.power_usd_day)" }
if ([decimal]$row.net_usd_day -ne 179.76) { throw "net_usd_day mismatch: $($row.net_usd_day)" }

$shortcutScript = Get-Content -LiteralPath (Join-Path $root "scripts\Install-LanternShortcut.ps1") -Raw
if ($shortcutScript -like "*Mining Dashboard*") {
    throw "Shortcut installer should not create a Mining Dashboard shortcut."
}

Write-Output "SOLO_MINING_SKILL_TEST_OK"
