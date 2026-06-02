# Lantern OS — Privacy and Offline Operation

This document describes what data stays on-device, what reaches external services, and the current state of age gating and parental consent.

---

## What Stays Local

The following data never leaves the device unless the operator explicitly exports or deploys it:

- **Dream Journal entries** — stored in `data/dream_journal/*.jsonl` on the local filesystem
- **Wallet ledger** — stored in `data/wallet/` as append-only JSONL
- **World-model belief state** — stored in `data/world-model/` as JSONL

All three are written by the local server (`apps/lantern-garage/server.js`) to the host filesystem. No background sync, no cloud backup, and no analytics pipeline reads these files.

---

## What Calls Cloud Providers

### Claude API (Anthropic)

When `ANTHROPIC_API_KEY` is set in the server environment, the Dream Journal chat endpoint (`POST /api/dream/chat`) may call the **Anthropic Claude API** to generate conversational replies. The message text sent by the user is included in the API request.

When `ANTHROPIC_API_KEY` is **not** set, the server falls back to a local rule-based reply engine (no external network call) or to a locally running **Ollama** instance if one is available.

No other cloud provider integrations are active in the default configuration.

### Railway (deployment only)

When deployed to Railway, the server process runs in Railway's cloud infrastructure. Data files written to disk on Railway are subject to Railway's storage and retention policies. Operators who require data sovereignty should run the local server only (`server.js` on their own hardware).

---

## Data Storage

- **Format:** Append-only JSONL (newline-delimited JSON). Records are never overwritten or deleted by the application.
- **Location:** Local filesystem under `data/`. No database engine is required.
- **No cloud sync by default.** Data does not leave the device unless the operator deploys to Railway or manually exports files.

---

## Logging Policy

- HTTP request method and path are logged to **stdout only** at server startup and on certain error conditions.
- There are no persistent access log files.
- There is no analytics, telemetry, or error-reporting service integrated into the server.

---

## Age Gating

No age verification is currently implemented in Lantern OS. The system is intended for adult operators and is not designed or tested for use by minors.

---

## Parental Consent

Parental consent flows are not yet implemented. Lantern OS is **not suitable for deployment to minors** without adding appropriate consent mechanisms, content filtering, and guardian notification features.

Operators who wish to offer Lantern OS to users under 13 (or the applicable legal age of digital consent in their jurisdiction) must implement these controls before doing so.

---

## Summary Table

| Data / Action | Stays local? | Notes |
|---|---|---|
| Dream Journal entries | Yes | `data/dream_journal/*.jsonl`; local disk only |
| Wallet ledger | Yes | `data/wallet/`; local disk only |
| World-model state | Yes | `data/world-model/`; local disk only |
| Dream chat message text | Conditional | Sent to Anthropic Claude API only when `ANTHROPIC_API_KEY` is set |
| HTTP request paths | Stdout only | No persistent log file; no analytics |
| Age verification | Not implemented | Adult operators only |
| Parental consent | Not implemented | Not suitable for minors without additional controls |
