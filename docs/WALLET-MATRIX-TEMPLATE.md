# Wallet Matrix Template

Status: receive-address and watch-only template.

This matrix is for safe accumulation and evidence. It is not a key store.

## Rule

Use watch-only first and signing later. Keep seed phrases, private keys, hardware
wallet PINs, exchange passwords, and recovery documents out of Lantern OS.

## Columns

| Column | Meaning |
|---|---|
| Asset | BTC, ETH, XMR, LTC, DOGE, RVN, ETC, KAS, or another reviewed asset. |
| Network | Chain or testnet name. |
| Wallet app | Official wallet, hardware-wallet companion, or watch-only app. |
| Address / xpub / watch-only ID | Public receive address or watch-only identifier only. |
| Custody | Usually self-custody for operator-owned wallets. |
| Secret location | Offline only, hardware wallet, or other non-repo location. |
| Read-only monitor | Explorer, JSON-RPC, wallet RPC, or self-hosted node. |
| Off-ramp path | Exchange, broker, or held/manual review. |
| KYC needs | Expected identity/compliance requirement for fiat off-ramp. |
| First test txid | Transaction ID after a tiny test transfer. |
| Notes | Risk, support, or operator review notes. |

The CSV version lives at `templates/wallet-matrix.csv`.

## Safe Accumulation Lanes

| Lane | Fit | Boundary |
|---|---|---|
| Pool mining | XMR, RVN, ETC, ASIC lanes | Owned hardware only; no fake ROI. |
| P2Pool | XMR | No custody shortcut and no pool wallet assumption. |
| Testnet/faucets | Wallet UX and screenshots | Not revenue. Never count as real income. |
| Airdrop checks | ETH/EVM read-only validation | Never sign blindly. Inspect calldata first. |
| Microbuys | Real wallet rows without mining wars | Intentionally tiny, documented, lawful venue only. |
| Monitoring | All supported assets | No private keys in logs. |
