# Arc Reactor Mining Lab

Status: local-first mining package candidate.

Arc Reactor Mining Lab is not an "outperform ASICs" project. It is a safe,
legal, convergent Lantern OS package that does four things well:

1. inventories the fleet;
2. routes hardware only into viable lanes;
3. validates wallets and claims in read-only mode;
4. produces receipts that can support a tiny compliant sell-to-USD test.

The first seed USD should come primarily from selling the package as a service,
not from hoping mined coins carry the whole burden. Mining receipts prove that
the lab works; they are weak as a primary cash engine unless the operator
already has a power, hardware, or hosting edge.

## Repo Boundary

Lantern OS is the control and documentation plane. It should not become a
hidden wallet operator, signing app, mining daemon, or fake dashboard.

The first release ships in two layers:

| Layer | Contents | Release rule |
|---|---|---|
| Repo-native | Docs, scripts, templates, skill files, reports, tests | Works even if orchestration is unhealthy. |
| Surface | One backed card/route inside the chosen Lantern surface | Only appears when repo files or live APIs back it. |

## One Shortcut Rule

Use one Lantern OS entrypoint first. Mining Lab is an internal card or route,
not a separate launcher. `scripts/Install-LanternShortcut.ps1` creates one
Lantern shortcut and an optional diagnostics shortcut. It does not create a
mining dashboard shortcut.

## Feasibility Table

| Coin | Network status | Practical method | Required hardware | Verdict |
|---|---|---|---|---|
| BTC | PoW remains active | Pool or solo-lottery | SHA-256 ASIC | Reject for current CPU/GPU fleet. |
| ETH | Mainnet proof-of-stake | None | None | Wallet, claim, or microbuy only. |
| XMR | RandomX PoW | Pool or P2Pool | CPU first | Best CPU fleet learning lane. |
| KAS | PoW blockDAG | Hardware-specific validation | kHeavyHash ASIC | Only if owned hardware is justified. |
| LTC | Scrypt PoW | Pool, often DOGE-coupled | Scrypt ASIC | Only with existing ASIC and cheap power. |
| DOGE | Scrypt PoW | Usually same practical lane as LTC | Scrypt ASIC | Do not route desktops here. |
| RVN | KAWPOW PoW | Pool or hobby experiment | GPU | GPU experiment only. |
| ETC | ETChash PoW | Pool or hobby experiment | GPU or ETChash ASIC | Useful only for sunk-cost hardware. |
| Other | Case by case | Official-doc review first | Match algorithm to owned hardware | Reject until validated. |

## Universal Revenue Model

```text
coins_per_day = (effective_hashrate / network_hashrate) * block_reward * blocks_per_day * (1 - pool_fee)
gross_usd_day = coins_per_day * spot_price_usd
power_usd_day = (watts / 1000) * hours_per_day * power_usd_per_kwh
net_usd_day = gross_usd_day - power_usd_day
```

Use this formula everywhere. Do not hard-code ROI claims.

## Hardware Inventory

Windows:

```powershell
Get-CimInstance Win32_Processor |
  Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed

Get-CimInstance Win32_VideoController |
  Select-Object Name, AdapterRAM, DriverVersion, VideoProcessor

$ram = Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum
[pscustomobject]@{ TotalRAM_GB = [math]::Round($ram.Sum / 1GB, 2) }

Get-ComputerInfo |
  Select-Object CsName, WindowsProductName, WindowsVersion, OsBuildNumber

nvidia-smi --query-gpu=name,power.draw,power.limit,temperature.gpu,memory.total,driver_version --format=csv
```

Linux:

```bash
lscpu
lsblk
rocm-smi --showproductname --showpower --showtemp --showmeminfo vram
```

ASIC inventory is usually manual unless vendor APIs are already on-LAN. Record
host/IP, model, algorithm, firmware, target hashrate, observed hashrate, wall
watts, cooling type, pool URL, worker name, and wallet destination.

## Safe Workflow

1. Run `scripts/Get-HardwareInventory.ps1` and fill manual ASIC rows if needed.
2. Fill `templates/wallet-matrix.csv` with receive addresses or watch-only IDs.
3. Run `scripts/Test-MiningProfitability.ps1` with refreshed live inputs.
4. Use `skills/solo-mining/examples/read_only_eth_balance.py` and
   `read_only_btc_balance.py` only for watch-only checks.
5. Use `skills/solo-mining/examples/claim_guard.py` before any EVM claim.
6. Write receipts with `templates/mining-receipt.json` shape.
7. Surface only evidence-backed status through Lantern OS.

## Legal And Compliance Boundary

This is not legal, tax, investment, or financial advice. The package assumes
U.S. off-ramps may require identity checks and tax records. It preserves cost,
receipt, and transaction evidence from the beginning.

Do not use mixers or obfuscation services in this package. U.S. treatment of
mixers and privacy tools has been legally volatile; that instability is not a
fit for a clean seed-funding lab.

If another Lantern or Orion lane touches sportsbook or prediction-market work,
keep that separate at the wallet, report, and shortcut level.

## Source Baseline

| Topic | Source |
|---|---|
| Ethereum proof-of-stake | https://ethereum.org/developers/docs/consensus-mechanisms/pos/ |
| Ethereum JSON-RPC read-only calls | https://ethereum.org/developers/docs/apis/json-rpc/ |
| Historical Ethereum PoW/Ethash | https://ethereum.org/developers/docs/consensus-mechanisms/pow/mining/mining-algorithms/ethash/ |
| Monero RandomX | https://web.getmonero.org/resources/moneropedia/randomx.html |
| Monero tail emission | https://www.getmonero.org/resources/moneropedia/tail-emission.html |
| Ravencoin KAWPOW | https://ravencoin.org/about/ |
| Ethereum Classic ETChash | https://ethereumclassic.com/learn/mining/mining-hardware |
| Kaspa kHeavyHash | https://kaspa.org/ |
| Esplora address API | https://github.com/Blockstream/esplora/blob/master/API.md |
| ERC-20 approve | https://eips.ethereum.org/EIPS/eip-20 |
| ERC-721 setApprovalForAll | https://eips.ethereum.org/EIPS/eip-721 |
| EIA electricity data | https://www.eia.gov/electricity/data.php |
| Treasury digital asset broker reporting | https://home.treasury.gov/news/press-releases/jy2438 |
| Tornado Cash delisting and mixer risk signal | https://home.treasury.gov/news/press-releases/sb0057 |
