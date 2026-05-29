# Payment Link Receipt — 2026-05-28

Status: held pending operator approval.

## Receipt

| Field | Value |
|---|---|
| Chosen provider | Manual invoice |
| Offer name | `Lantern Local RAG / Repo Cleanup Sprint` |
| Price or support model | Pilot invoice model; use the existing `$199-$499` pilot range and current draft invoice amount of `$199` unless operator approves a different scoped price. |
| Public/non-secret payment URL | Not stored. No public payment URL is approved for repository storage yet. |
| Account status | held |
| Fee/tax/refund notes | Manual invoice keeps provider fees undefined until the operator chooses and confirms the processor or payment rail. Taxes are not calculated in this repo record. Refund terms must be stated on the invoice or payment page before collecting funds. |
| Date created | 2026-05-28 |
| Operator approval | Not approved for payment URL storage or cash clearance. Operator approval required before publishing a payment URL in this repo. |
| Ledger boundary | Do not mark cleared cash until the payment provider and bank confirm funds cleared. |

## Cross-References

- Cash market/options note: `data/cash-loop/CASH-NOW-FREE-MARKETS-2026-05-28.md`
- Local wallet summary: `data/wallet/local-cash-wallet.json`
- Ledger event stream: `data/wallet/ledger.jsonl`

## Ledger Boundary Notes

- This receipt records payment-link readiness only; it is not a payment event.
- Do not increase `clearedCashUsd` in `data/wallet/local-cash-wallet.json` from this receipt alone.
- Do not append a cleared-payment ledger row to `data/wallet/ledger.jsonl` until provider and bank settlement evidence exists.
- If the operator later approves storing a public, non-secret payment URL, add only the public URL and keep credentials, API keys, account identifiers, customer private data, and bank details out of Git.
