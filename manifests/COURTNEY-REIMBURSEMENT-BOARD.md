# Courtney Reimbursement Recovery Board

**Date:** 2026-06-02
**Classification:** Internal operator manifest
**Evidence class:** operator_asserted | local_verified required before promoting any claim

---

## Truth Statement

- No revenue is claimed until cash clears in the operator account.
- No outreach is claimed until sends are recorded in the outreach ledger.
- Courtney's funded costs are tracked as liabilities, not income.
- Every reimbursement state follows the same invariant as the main wallet:

```
cost_funded → reimbursement_due → payment_received
```

Only `payment_received` events, confirmed with evidence, reduce the outstanding balance.

---

## Feature Table

| Feature | Description | Status |
|---|---|---|
| **Public offer page** | Single published page listing one clear offer with price and deliverable | NOT STARTED |
| **Manual outreach queue** | Logged list of 3–5 named contacts per day; no mass email | NOT STARTED |
| **Outreach ledger** | Record of every sent message, reply, and outcome; no claims without log entry | NOT STARTED |
| **Courtney action surface** | Interface or checklist Courtney can use to log costs and request reimbursement | NOT STARTED |
| **Reimbursement ledger** | `data/wallet/courtney-reimbursement-ledger.jsonl` — tracks cost_funded, reimbursement_due, payment_received | IN PROGRESS |

---

## 24-Hour Recovery Sprint Steps

These steps are to be completed within 24 hours of this board being activated.

| Step | Action | Owner | Status |
|---|---|---|---|
| 1 | Confirm `data/wallet/courtney-reimbursement-ledger.jsonl` exists and format is correct | Alex | IN PROGRESS |
| 2 | Log all known Courtney-funded costs as `cost_funded` entries with date, amount, description, and evidence | Alex + Courtney | NOT STARTED |
| 3 | Compute total `reimbursement_due` balance from all logged cost entries | Alex | NOT STARTED |
| 4 | Draft one invoice or repayment plan covering the outstanding balance | Alex | NOT STARTED |
| 5 | Send the draft invoice or repayment plan to Courtney for review | Alex | NOT STARTED |
| 6 | Record Courtney's acknowledgement in the ledger as a `reimbursement_due` confirmation event | Alex | NOT STARTED |
| 7 | When payment is made, log as `payment_received` with transaction reference and amount | Alex | NOT STARTED |
| 8 | Verify outstanding balance reaches zero; close this sprint | Alex | NOT STARTED |

---

## Reimbursement Ledger Format Reference

File: `data/wallet/courtney-reimbursement-ledger.jsonl`

```jsonl
{"date": "ISO8601", "type": "cost_funded|reimbursement_due|payment_received", "amount_usd": 0.00, "description": "...", "evidence": "..."}
```

| Field | Meaning |
|---|---|
| `date` | ISO 8601 timestamp of the event |
| `type` | `cost_funded` = Courtney paid a cost; `reimbursement_due` = formal acknowledgement of debt; `payment_received` = cash confirmed received by Courtney |
| `amount_usd` | Dollar amount of the event (positive = cost or due; positive = received) |
| `description` | Human-readable description of what the cost or payment covers |
| `evidence` | Receipt path, invoice number, bank reference, or message thread ID |

---

## Guardrails

1. **No spam.** Manual outreach only. Every message is logged before being counted as sent. No bulk sends, no automated cold email, no purchased lists.

2. **No inflation of claims.** Do not log an outreach message as sent until it is actually sent. Do not log a payment as received until funds are confirmed. Do not present `reimbursement_due` as a cleared debt.

3. **No private data in Git.** This file tracks amounts and descriptions. Do not include Courtney's bank account details, card numbers, or any PIID in this manifest or the ledger file.

4. **No projection as fact.** If Courtney is expected to receive reimbursement but payment has not been made, the state is `reimbursement_due`, not `payment_received`.

5. **Operator approval required** before any reimbursement entry is marked `payment_received`. Two-party confirmation (Alex + Courtney) preferred.

---

## Source Paths

| Artifact | Path |
|---|---|
| Reimbursement ledger | `data/wallet/courtney-reimbursement-ledger.jsonl` |
| Main wallet ledger | `data/wallet/ledger.jsonl` |
| Wallet principles | `data/wallet/SATOSHI-STYLE-WALLET-PRINCIPLES.md` |
| Sales deck | `reports/ONE-WORLD-LEADER-SALES-DECK-2026-06-02.md` |
| This board | `manifests/COURTNEY-REIMBURSEMENT-BOARD.md` |

---

*Internal operator document. Not for public distribution without redaction of cost and identity details.*
