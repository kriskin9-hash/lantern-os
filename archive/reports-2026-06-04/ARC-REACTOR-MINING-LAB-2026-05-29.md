# Arc Reactor Mining Lab - 2026-05-29

Status: PDF-ready package candidate.

This report is intentionally a four-part package specification. It is not a
profit promise and not a miner installer.

## Page 1 - Executive Summary And Repo Touchpoints

Arc Reactor Mining Lab is a local-first, legal, operator-controlled package
inside `alex-place/lantern-os`. Its strongest version inventories the fleet,
routes hardware only into viable lanes, validates wallets and claims in
read-only mode, and emits receipts for tiny compliant sell-to-USD tests.

One shortcut rule: Lantern OS remains the front door. Mining Lab is an internal
card backed by real files, not a new dashboard or launcher.

| Touchpoint | Role |
|---|---|
| `skills/solo-mining/SKILL.md` | Skill contract and hard safety blocks |
| `docs/ARC-REACTOR-MINING-LAB.md` | Operator guide |
| `templates/*.csv` and `templates/mining-receipt.json` | Intake, wallet, feasibility, and receipt templates |
| `scripts/Get-HardwareInventory.ps1` | Windows inventory collector |
| `scripts/Test-MiningProfitability.ps1` | Formula implementation |
| `scripts/Install-LanternShortcut.ps1` | Single Lantern shortcut |
| `surfaces/tony-garage/index.html` | Backed Mining Lab card |

Diagram:

```text
          Inventory
             |
Wallets - Arc Reactor - Claims
             |
       Mining Lanes
             |
          Receipts
             |
        Tiny USD Seed
```

<!-- pagebreak -->

## Page 2 - Coin Feasibility And Formula

The correct feasibility model is not which coin the fleet can dominate. It is
which lane matches owned hardware, power price, heat/noise tolerance, off-ramp
availability, and operator risk.

| Coin | Hardware lane | Verdict |
|---|---|---|
| BTC | SHA-256 ASIC | Reject for CPU/GPU fleet |
| ETH | None | Wallet, claim, and microbuy only |
| XMR | CPU | Best learning lane |
| RVN | GPU | Experiment only |
| ETC | GPU or ETChash ASIC | Sunk-cost hardware only |
| LTC | Scrypt ASIC | ASIC only |
| DOGE | Scrypt ASIC | Usually evaluated with LTC economics |
| KAS | kHeavyHash ASIC | Owned ASIC only |

Universal model:

```text
coins_per_day = (effective_hashrate / network_hashrate) * block_reward * blocks_per_day * (1 - pool_fee)
gross_usd_day = coins_per_day * spot_price_usd
power_usd_day = (watts / 1000) * hours_per_day * power_usd_per_kwh
net_usd_day = gross_usd_day - power_usd_day
```

Power and profitability fields must be refreshed before every decision. Static
ROI claims are rejected.

<!-- pagebreak -->

## Page 3 - Wallet Matrix And Read-Only Claims

The wallet layer is the durable value of the lab. It can hold earned dust,
testnet balances, approved microbuys, watch-only balances, and later off-ramp
receipts without turning Lantern OS into a custody tool.

| Lane | What it is for | Boundary |
|---|---|---|
| Watch-only checks | BTC/ETH balance evidence | No private keys |
| Pool/P2Pool mining | Owned hardware rewards | No unauthorized devices |
| Testnet/faucets | Practice and screenshots | Not revenue |
| EVM claim guard | Selector review | No blind signing |
| Microbuys | Real tiny rows | Documented lawful venue |
| Receipt ledger | Proof of process | Append-only corrections |

Read-only scripts:

```text
skills/solo-mining/examples/read_only_eth_balance.py
skills/solo-mining/examples/read_only_btc_balance.py
skills/solo-mining/examples/claim_guard.py
```

Claim guard blocks `0x095ea7b3` for ERC-20 approvals and `0xa22cb465` for
ERC-721 setApprovalForAll. Those operations can authorize other parties to move
assets, so they require explicit human review.

<!-- pagebreak -->

## Page 4 - Commercial Package, Timeline, Acceptance Criteria, Sources

The sellable offer is not "buy a miner and get rich." The offer is: "I will
tell you what your hardware can actually do, set up safe watch-only wallet
checks, and stop you from wasting money on impossible mining lanes."

| Offer | Deliverables | Indicative price |
|---|---|---|
| Arc Reactor Mining Intake | hardware intake, wallet matrix, feasibility note | $49 |
| Arc Reactor Mining Lab Lite | intake, wallet matrix, read-only scripts, profitability sheet | $149 |
| Arc Reactor Mining Lab Full | Lite plus shortcut, report, off-ramp checklist | $249 |
| Monthly receipt audit | refreshed model, watch-only audit, receipt archive | $29-$49/mo |

Acceptance criteria:

| Area | Pass condition |
|---|---|
| Skill boundary | Blocks ETH mining, brute force, unauthorized transfers, hidden signing, fake ROI |
| Inventory | Writes non-empty CPU/GPU/RAM output and allows manual ASIC rows |
| Profitability | Computes gross, power cost, and net for a fixed fixture |
| ETH monitor | Uses `eth_getBalance` only |
| BTC monitor | Uses watch-only address APIs only |
| Claim guard | Rejects approve and setApprovalForAll selectors |
| Surface honesty | Mining Lab card links only to real files |
| Shortcut discipline | One Lantern shortcut; optional diagnostics only |
| Repo scope | No first-release gm-agent-orchestrator code changes |
| Reporting | Pilot emits receipt JSON and markdown report |

Sources: Ethereum proof-of-stake and JSON-RPC docs, Monero RandomX docs,
Ravencoin official KAWPOW page, Ethereum Classic mining guide, Kaspa homepage,
Blockstream Esplora API, EIP-20, EIP-721, EIA electricity data, and U.S.
Treasury digital asset broker reporting releases.
