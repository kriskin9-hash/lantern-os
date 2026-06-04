# Orchestrator Threat Model

Status: required  
Scope: local multi-agent orchestration control plane  
Related issue: #306

## Why this exists

This repository routes commands, file edits, queue transitions, and agent
dispatch. Without an explicit threat model, capability claims are easy to
overstate and hard to verify.

This document defines concrete threat classes and required controls.

## Threat Class 1: Prompt Injection and Untrusted Content

### Risk

Agents consume untrusted input from task files, web pages, docs, MCP output, and
logs. Instruction-shaped text can attempt to override policy ("ignore previous
instructions", "run shell command", "post secret now").

### Required controls

1. Treat observed content as data, not instructions.
2. Maintain tool-level allowlists and approval gates.
3. Block high-risk actions when capability state is unverified or degraded.
4. Require evidence capture for destructive or cross-repo operations.

### Detection mechanisms

- Contract test: `tests/Test-PromptInjectionContract.ps1`
- Capability honesty checks: `docs/product/capability-honesty-model.md`
- Queue/task audit logs under `status/` and `reports/`

## Threat Class 2: MCP Server Impersonation and Endpoint Drift

### Risk

A remote tunnel or stale endpoint can impersonate the expected MCP surface.
Agents may believe they are calling trusted local tools while actually calling an
untrusted endpoint.

### Required controls

1. Prefer local loopback MCP endpoint verification before remote tunnels.
2. Record endpoint URL and health probe evidence before enabling dispatch.
3. Refuse capability claims based only on advertised tool names.
4. Keep remote endpoint usage behind explicit operator approval.

### Detection mechanisms

- MCP capability status contracts in `tests/Test-OrchMcpCapabilityStatus.ps1`
- MCP route contracts in `tests/Test-OrchMcpServerContracts.ps1`
- Local status/health verification scripts in `scripts/`

## Threat Class 3: Supply Chain and Hook/Tooling Drift

### Risk

Hook wrappers or agent toolchains may reference missing scripts, stale paths, or
unexpected versions. This creates silent bypasses or false confidence.

### Required controls

1. Hook installer must tolerate missing scripts and choose known-safe fallbacks.
2. Hook scripts must be versioned in-repo and auditable.
3. Contract tests must verify hook and script presence.
4. CI should run PowerShell syntax checks and targeted contracts.

### Detection mechanisms

- Hook installer contract test: `tests/Test-GitHookInstallerContract.ps1`
- Hook advisor contract: `tests/Test-HookOpportunityAdvisor.ps1`
- Syntax safety net: `tests/Test-PowerShellSyntax.ps1`

## Threat Class 4: Tenant Lateral Movement and Identity/Key Leakage

### Risk

Shared environments can leak identity context, cached credentials, or scoped
data between users/tenants.

### Required controls

1. Explicit per-user key lifecycle with revocation purge behavior.
2. Per-task spend caps and no silent fallback to unrelated keys.
3. Storage guidance must be deployment-aware (single-user vs shared node).
4. Audit logs must preserve key-id metadata without secret values.

### Detection mechanisms

- Key policy contract tests: `tests/Test-UserApiKeyPolicyContracts.ps1`
- Policy doc: `docs/product/user-identity-and-api-keys.md`

## Non-negotiable "Do Not Allow Agents To"

1. Treat unverified web/task text as authority.
2. Execute privileged actions because content "sounds official".
3. Assume remote MCP endpoints are trusted without evidence.
4. Reuse revoked credentials from cache.
5. Bypass denylist profile rules via prompt-only approval.

## References

- OWASP prompt injection overview: https://owasp.org/www-community/attacks/PromptInjection
- OWASP Top 10 for LLM Applications (v2): https://owasp.org/www-project-top-10-for-large-language-model-applications/
