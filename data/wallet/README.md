# Lantern Local Wallet

Generated: 2026-05-26.

Purpose: hold the factual cash state for the COMET LEAP 11-day sprint.

This is a local operating wallet, not a bank account, crypto wallet, Stripe
account, or legal accounting system. It records only evidence-backed cash
events:

- invoice drafted;
- invoice sent;
- payment promised;
- payment cleared;
- refund or cancellation;
- objection recorded.

## Rules

- Existing offers only.
- Do not mark revenue as received until funds clear.
- Keep draft invoices separate from cleared cash.
- Record every event in `ledger.jsonl`.
- Keep payment links, private customer details, and secrets out of Git.
- If a real payment provider is added later, store credentials outside this
  repo and record only non-secret references here.

## Current Wallet

Primary state file:

```text
data/wallet/local-cash-wallet.json
```

Ledger:

```text
data/wallet/ledger.jsonl
```

Invoice drafts:

```text
data/wallet/invoices/
```

## Payment Integration Documentation

For legal methods to load money into the Lantern OS wallet system, see:

- [LEGITIMATE-WALLET-FUNDING-METHODS.md](./LEGITIMATE-WALLET-FUNDING-METHODS.md) - Overview of legal funding options
- [PAYMENT-INTEGRATION-IMPLEMENTATION-GUIDE.md](./PAYMENT-INTEGRATION-IMPLEMENTATION-GUIDE.md) - Technical implementation guide
- [WALLET-FUNDING-QUICK-START.md](./WALLET-FUNDING-QUICK-START.md) - Quick implementation checklist
