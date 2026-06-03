# Convergence IO Engine (CIE)

**Version:** 1.0  
**Status:** Design Document  
**Date:** 2026-06-03  
**Owner:** Keystone

## Overview

The **Convergence IO Engine (CIE)** is a lightweight orchestration layer that wraps the CSF (Convergence-Fitted Searchable Binary Archive) system. It provides a clean, engine-style interface for reading, writing, indexing, and querying CSF data.

## Goals

- Abstract away direct CSF file manipulation
- Provide a consistent IO interface for Dream Journal, Crystallization Engine, and future agents
- Enable streaming, batch, and indexed access patterns
- Maintain CSF as the single source of truth

## Architecture

```
Convergence IO Engine (CIE)
├── Reader     → Read CSF files + indexes
├── Writer     → Write new CSF entries
├── Indexer    → Maintain fast lookup indexes
├── Querier    → Semantic + symbolic queries
└── Exporter   → Export to JSONL, Markdown, or other formats
```

## Core Interfaces (Proposed)

```python
class ConvergenceIOEngine:
    def write(self, csf: dict) -> str
    def read(self, csf_id: str) -> dict
    def query(self, filters: dict) -> list[dict]
    def index(self, csf: dict) -> None
    def export(self, csf_id: str, format: str = "jsonl") -> str
```

## Relationship to Existing Systems

- **CSF** — Storage format (source of truth)
- **Crystallization Engine** — Consumer of CIE
- **Dream Journal** — Primary writer via CIE
- **Discord Bot** — Can read/write via CIE

## Next Steps

1. Implement `ConvergenceIOEngine` class
2. Migrate existing CSF read/write logic into the engine
3. Update Crystallization Engine to use CIE
4. Add comprehensive tests

---
**Document Status:** Draft — Ready for implementation
