---
name: solo-mining
description: Safe local-first mining lab workflow for owned hardware, read-only wallet checks, profitability estimates, claim selector guards, and receipt generation. This skill blocks wallet brute force, unauthorized transfers, hidden signing, fake ROI, and ETH mainnet mining claims.
---

# Lantern Solo Mining Skill

skill: lantern.skill.solo_mining.v1
default_mode: profit_check_first

Arc Reactor Mining Lab is a safe, local-first operator workflow. It inventories
owned hardware, routes hardware only into viable lanes, validates wallets in
read-only mode, and emits receipts that can support a small compliant sell-to-USD
test. It is not a hidden miner, wallet cracker, private-key extractor, or ROI
promise engine.

## Allowed

- hardware_inventory
- read_only_wallet_checks
- profitability_estimation
- pool_setup_guidance_for_owned_hardware
- p2pool_guidance
- claim_selector_validation
- receipt_generation

## Blocked

- wallet_bruteforce
- unauthorized_transfers
- hidden_transaction_signing
- mining_on_unowned_devices
- fake_roi_claims
- eth_mainnet_mining_claims
- private_key_collection
- seed_phrase_collection
- mixer_or_obfuscation_routing

## Hardware Routes

| Route | Preferred lane | Notes |
|---|---|---|
| CPU | XMR | Monero RandomX is the best CPU-first learning lane. Run profitability first. |
| GPU | RVN, ETC | Experimental only, best for sunk-cost GPUs with measured wall power. |
| asic_required | BTC, LTC, DOGE, KAS | Reject for desktop fleets unless owned hardware or hosted hardware is separately justified. |
| ETH | Wallet and claim checks only | Ethereum mainnet is proof-of-stake; do not claim ETH mining. |

## Operating Loop

1. Confirm the operator owns or is allowed to use the hardware.
2. Run hardware inventory and fill `templates/hardware-intake.csv`.
3. Fill `templates/wallet-matrix.csv` with receive addresses or watch-only IDs
   only. Never write secrets to the repo.
4. Run `scripts/Test-MiningProfitability.ps1` with live network and price
   inputs. Treat missing inputs as `reject_until_validated`.
5. Use read-only balance scripts for wallet checks.
6. Use `examples/claim_guard.py` before any EVM claim flow. If it flags
   `approve`, `setApprovalForAll`, or `transferFrom`, stop for human review.
7. Emit `templates/mining-receipt.json` style receipts for inventory,
   profitability, payouts, test transfers, and sell-off steps.
8. Surface the lab only through the existing Lantern entrypoint. Do not create a
   separate mining dashboard shortcut.

## Universal Revenue Model

```text
coins_per_day = (effective_hashrate / network_hashrate) * block_reward * blocks_per_day * (1 - pool_fee)
gross_usd_day = coins_per_day * spot_price_usd
power_usd_day = (watts / 1000) * hours_per_day * power_usd_per_kwh
net_usd_day = gross_usd_day - power_usd_day
```

Use this formula everywhere. Do not hard-code ROI claims in the skill.

## Claim And Wallet Boundary

The examples in `examples/` are read-only:

- ETH: `eth_getBalance` only.
- BTC: Esplora address lookup only.
- Claim guard: selector inspection only.

They do not sign, broadcast, sweep, approve, transfer, or custody funds.

## Source Baseline

- Ethereum proof-of-stake: https://ethereum.org/developers/docs/consensus-mechanisms/pos/
- Ethereum JSON-RPC: https://ethereum.org/developers/docs/apis/json-rpc/
- Blockstream Esplora API: https://github.com/Blockstream/esplora/blob/master/API.md
- ERC-20: https://eips.ethereum.org/EIPS/eip-20
- ERC-721: https://eips.ethereum.org/EIPS/eip-721
- Monero RandomX: https://web.getmonero.org/resources/moneropedia/randomx.html
- Ravencoin KAWPOW: https://ravencoin.org/about/
- Ethereum Classic mining: https://ethereumclassic.com/learn/mining/mining-hardware
- Kaspa proof-of-work: https://kaspa.org/
