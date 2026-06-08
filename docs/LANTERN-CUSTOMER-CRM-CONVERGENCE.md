# Lantern OS Customer CRM Convergence

**Status:** candidate / repo-safe architecture note  
**Date:** 2026-06-07 America/New_York  
**Scope:** OSS customer/contact tracking layer for Patreon and other sales/community sources  
**Safety boundary:** this document contains architecture and policy only. It contains no real customer records, credentials, raw exports, or private identifiers.

---

## Decision

Build the **Lantern Customer Bridge**, not a Lantern customer memory.

Primary candidate:

```text
Twenty CRM self-hosted
  + Lantern customer-sync adapters
  + encrypted private-data vault boundary
  + narrow MCP summary/action tools
```

Strict-OSS fallback:

```text
CiviCRM
  + Lantern customer-sync adapters
  + encrypted private-data vault boundary
  + narrow MCP summary/action tools
```

Rejected as the core customer system:

```text
Patreon alone
automation runner alone
Lantern RAG / CSF / CADD / symbolic memory alone
raw spreadsheet customer dump
```

Patreon is one source, not the system of record. Automation runners can assist but should not become the customer database. Lantern memory should preserve architecture, decisions, schemas, and redacted references only.

---

## Canonical flow

```text
Patreon / payment platforms / ecommerce / Discord / newsletter / manual leads
  -> source-specific sync adapters
  -> OSS CRM canonical customer/contact record
  -> Lantern entitlement/event ledger
  -> encrypted private-data vault for sensitive identifiers
  -> narrow MCP tools for safe chat access
```

The CRM holds operational relationship state. The vault holds sensitive identifiers. Lantern holds entitlement logic, policy, schema, audit references, and safe summaries.

---

## Storage boundary

### CRM may store

```text
customer profile
source IDs
patron/member status
currently entitled tier/status
safe support notes
safe tags and segments
non-sensitive contact metadata
external account linkage metadata
```

### Private-data vault stores

```text
private identifiers
raw source exports, if retained
source event payloads, if retained
source access credentials
token material
sensitive contact evidence
bulk export evidence
```

### Lantern repo/RAG/CSF/CADD may store

```text
schemas
adapter code
policy docs
redacted fixtures
hash/audit references
decision records
safe convergence summaries
```

Repo rule: never commit real customer records, raw source exports, production credentials, or private identifiers. This extends the existing Lantern private-house rule in `docs/LANTERN-LICENSE-WALLETS-APPLE-PAY.md`.

---

## Minimal object model

### Person

```text
id
primary_display_name
contact_ref_or_hash
source_summary
consent_state
safe_tags
created_at
updated_at
```

Do not require a real name. External identity providers may mask identity fields.

### ExternalIdentity

```text
id
person_id
source
external_account_id
external_member_id
external_campaign_id
identity_confidence
last_seen_at
```

### PatreonMembership

```text
id
person_id
external_identity_id
source_member_id
campaign_id
patron_status
currently_entitled_tier_ids
currently_entitled_tier_names
currently_entitled_amount_cents
lifetime_support_cents
last_charge_status
last_charge_date
last_seen_at
raw_event_ref
```

`raw_event_ref` must point to a vault/audit reference or hash, not raw source payload committed to Git.

### EntitlementEvent

```text
id
person_id
source
external_event_id
event_type
observed_at
normalized_status
license_wallet_effect: none | grant | revoke | review
audit_hash
```

Only conservative, verified paid/cleared entitlement states should grant access. Failed, pending, draft, disputed, or projected values must not be counted as cleared cash.

---

## Proposed repo structure

```text
docs/LANTERN-CUSTOMER-CRM-CONVERGENCE.md
rag/seeds/lantern-customer-crm-convergence-ingest-2026-06-07.md
services/customer-sync/
  patreon/
  twenty/
  lantern/
mcp/customer-tools/
```

---

## MCP allowlist

```text
get_customer_summary
list_active_patrons
list_recent_entitlement_changes
add_safe_contact_note
request_sensitive_data_access
```

Allowed tools should return least-privilege summaries. They should not expose raw vault contents or unrestricted contact exports.

---

## MCP denied or held by default

```text
bulk contact export
raw source payload exposure
credential/token exposure
unrestricted sensitive-data export
```

These actions require explicit operator approval, local vault validation, export reason, audit logging, and a rollback/deletion plan. Default state: `held`.

---

## Integration states

```text
ready: observed and usable in the current environment
partial: available with limits, auth gaps, missing validation, or incomplete scope
held: requires local machine, credentials, login, operator approval, secret, payment, or legal/compliance decision
missing: not visible
mismatch: advertised but not actually exposed
```

Customer-data access should default to `held` until a vault and audit path exist.

---

## Promotion requirements

```text
current Twenty CRM license and API capabilities verified
CiviCRM fallback documented
Patreon API scopes verified
source app created outside repo
secrets stored outside Git
private-data vault created and encrypted
redacted fixture data added
sync adapter tested with fake data
rollback path documented
MCP allowlist/denylist enforced
audit log created for customer-affecting actions
```

---

## Rollback path

```text
1. Disable source webhook endpoints.
2. Revoke source access outside Git.
3. Stop customer-sync worker.
4. Preserve audit receipts.
5. Delete redacted test data if needed.
6. Leave CRM source records untouched unless the operator requests cleanup.
7. Keep Lantern entitlement ledger in review/held state until reconciliation.
```

---

## Final convergence line

**Build the Lantern Customer Bridge, not a Lantern customer memory.**

CRM holds operational relationships. Vault holds sensitive identifiers. Lantern holds entitlement logic, policy, audit references, and safe MCP summaries.
