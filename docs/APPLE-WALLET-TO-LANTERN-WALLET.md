# Apple Wallet to Lantern Local Wallet Workflow

Status: safe local import workflow.

## Boundary

This workflow does **not** move money from Apple Wallet, Apple Cash, Apple Card, banks, debit cards, credit cards, or any payment network.

Lantern wallet remains:

```text
local_ledger_not_bank_or_crypto_wallet
```

The script only imports a manually exported CSV into Lantern's local ledger format for review.

## What It Can Import

- Apple Card statement CSV exported by the operator.
- Apple Cash or bank CSV exported by the operator.
- Manually prepared Apple Wallet transaction CSV.
- Generic finance CSV with columns such as Date, Description, Merchant, Amount, Status, Category.

## What It Will Not Do

- request Apple ID credentials;
- scrape Wallet.app;
- bypass Apple security;
- read card numbers or private credentials;
- move funds;
- mark revenue as cleared automatically;
- claim an Apple balance is spendable Lantern cash without operator review.

## Basic Use

```powershell
Set-Location C:\tmp\lantern-os

powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Import-AppleWalletExport.ps1 `
  -CsvPath "$env:USERPROFILE\Downloads\apple-wallet-export.csv" `
  -SourceType apple_wallet_manual
```

This writes:

```text
data/wallet/imports/<import-id>.jsonl
data/wallet/imports/<import-id>.summary.json
```

## Append After Review

Only after reviewing the normalized JSONL:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Import-AppleWalletExport.ps1 `
  -CsvPath "$env:USERPROFILE\Downloads\apple-wallet-export.csv" `
  -SourceType apple_wallet_manual `
  -AppendToLedger
```

## CSV Columns Supported

The importer attempts to map common columns:

| Lantern Field | Accepted Source Columns |
|---|---|
| transactionDate | Transaction Date, Date, Posting Date, Clearing Date, Created Date, Time, Timestamp |
| clearingDate | Clearing Date, Posted Date, Posting Date |
| description | Description, Name, Merchant, Payee, Memo, Transaction |
| merchant | Merchant, Name, Payee |
| category | Category, Type, Transaction Type |
| status | Status, State |
| amountUsd | Amount (USD), Amount, Debit, Credit, Net Amount, Total |

Long numeric sequences are redacted before writing description/merchant/category/status text.

## Load Door Rule

The door remains held until the wallet is loaded in Lantern terms:

1. CSV import exists;
2. summary exists;
3. operator reviewed imported rows;
4. optional append to `data/wallet/ledger.jsonl` completed;
5. cleared cash is still only counted when funds are actually cleared, not merely imported.

## Actual Money Movement

Use official Apple, bank, or payment-provider apps for actual transfers. Then record the cleared event in Lantern after confirmation.
