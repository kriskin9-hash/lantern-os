# User Identity and API Keys

Status: required implementation contract  
Related issue: #309

## Objective

Define per-user API key lifecycle with explicit rotation, expiration handling,
leak response, revocation closed loop, and spend controls.

## Key Lifecycle

### 1) Rotation cadence

- Default rotation cadence: every 90 days.
- High-risk contexts: every 30 days.
- Rotation reminder thresholds: 14 days and 3 days before due date.

### 2) Expiration handling

If a key expires mid-task:

1. mark task state `blocked_key_expired`;
2. stop further billable calls;
3. emit operator-visible error with provider/key alias (not secret);
4. do not auto-fallback to another user's key.

### 3) Leak response

Leak suspicion triggers include:

- key-like string detected in repo/log/transcript;
- push protection or secret scanner alert;
- provider breach notification;
- manual user/operator leak report.

Immediate response:

1. revoke key at provider;
2. mark key state `revoked`;
3. force local cache/process purge;
4. rotate replacement key;
5. file incident log with timestamps and scope.

### 4) Revocation closed loop

Revocation is complete only when all are true:

1. provider reports key revoked/disabled;
2. local key cache entry purged;
3. in-flight process env/context purged;
4. agent slot memory state no longer references key id;
5. follow-up probe confirms no further use.

A `revokedAt` timestamp alone is not sufficient.

## Deployment-Aware Storage Matrix

| Deployment | Preferred storage | Notes |
|---|---|---|
| Single-user Windows laptop | Windows Credential Manager + local policy file | acceptable when one OS user only |
| Shared workstation | tenant/user-scoped encrypted store with per-user access control | WCM alone is insufficient |
| School LAN / multi-operator node | service-managed secret store with tenant partitioning and audit | enforce tenant boundary |
| Multi-tenant server | dedicated secrets service + least-privilege runtime identity | mandatory for isolation |

## Spend Controls

1. Per-user monthly cap.
2. Per-user daily cap.
3. Per-task cap (hard stop).
4. Hard kill switch (admin/operator freeze).
5. Estimate-before-dispatch threshold requiring explicit approval.

### Critical rule

If per-task cap is hit, execution must stop. It must not silently retry with a
different key owner.

## Contract Evidence

See `tests/Test-UserApiKeyPolicyContracts.ps1`:

- revoked key cannot be served from cache post-revocation;
- per-task cap hit prevents fallback to unrelated key.
