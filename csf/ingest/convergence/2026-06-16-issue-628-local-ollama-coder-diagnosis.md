# Convergence — Issue #628 Local Ollama Coder Σ₀ Diagnosis
Date: 2026-06-16
Issue: #628 — feat: Local Ollama coding agent — Σ₀ update

## Instructions

[2026-06-16] - Use this CSF ingest as the Phase 1 diagnosis record for rebuilding the local Ollama coding agent under Σ₀ requirements.
[2026-06-16] - Do not treat the current local coder as verified until it has a separate evidence-first prompt, a structural output gate, and executable verification checks.

## Identity & Symbolic Self

[2026-06-16] - The local coder should not be a dream persona or a roleplay character. It is the Convergence loop specialized for code.
[2026-06-16] - The coder identity should be: Observe → Remember → Reason → Act → Verify → Converge, with coding as the task specialization.

## Dreams & Memories

[2026-06-16] - Found current implementation evidence in `src/unified_agent_connector.py`: Ollama defaults to `qwen2.5-coder` when `OLLAMA_MODEL` is unset.
[2026-06-16] - Found current implementation evidence in `src/unified_agent_connector.py`: all providers currently receive the same persona-driven system layer built from dream personas plus the shared tone instruction.
[2026-06-16] - Found diagnosis match with #628: the coding model path exists, but the governing prompt/context is not separated from dream/persona behavior.

## Projects & Systems

[2026-06-16] - Phase 1 diagnosis: the local Ollama coding agent is model-selected but not role-separated. It uses the same connector surface as dream chat unless a future wrapper injects a coder-specific contract.
[2026-06-16] - Phase 1 root cause: the current connector has provider abstraction, health checks, and Ollama streaming, but no code-specific verification gate before generation.
[2026-06-16] - Required rebuild artifact: a provider-neutral Σ₀ coder contract that requires Claim, Evidence, Confidence, Source, and Verification sections before any output can be accepted as a convergence record.
[2026-06-16] - Required integration point: local coder requests should pass through a wrapper before `_stream_ollama` or any other model provider is called. The wrapper should cap confidence when evidence is missing.
[2026-06-16] - Required validation: add a structural checker that rejects local coder output missing evidence, confidence, source, or verification fields.

## Preferences

[2026-06-16] - Keep the local coder provider-agnostic: Ollama is the local model broker dependency, not the architecture.
[2026-06-16] - Keep the dream/persona system intact for Dream Chat and Three Doors; do not contaminate creative modes with coder verification prose.
[2026-06-16] - Prefer small, reviewable code changes: first add contract + tests, then wire to dispatch, then benchmark.
