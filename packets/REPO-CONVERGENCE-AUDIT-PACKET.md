# Repo Convergence Audit Packet

**Generated**: 2026-05-31  
**Offer**: Local RAG / Repo Cleanup Sprint  
**Price**: $199-$999  
**Persona**: Builder/Consultant with messy repos/docs  
**Domain**: Local AI/RAG Infrastructure & Convergence

---

## Simple Answer

A 1-2 hour sprint that turns your messy repo/docs into a clean, searchable RAG index with a convergence report. Uses local Ollama inference ($0 cost) and the Lantern OS RAG dollhouse.

---

## What It Actually Does

1. **Audit your repo state**: Git status, dirty worktrees, stale references, broken links
2. **Ingest to RAG dollhouse**: Flat file generation with source citations and asset hashes
3. **Run convergence analysis**: Local Ollama agent identifies TODOs, duplicates, unsafe claims
4. **Generate before/after report**: PDF showing cleanup results with evidence citations
5. **Deliver actionable next steps**: Prioritized issue list with Status Cube routing

---

## Evidence / Source Discipline

| Source | Evidence Class | Use |
|--------|----------------|-----|
| `skills/lantern-rag-dollhouse/` | `local_verified` | Flat file generation engine |
| `scripts/Invoke-OllamaAgent.ps1` | `local_verified` | Local inference worker |
| `config/agents.json` | `local_verified` | Agent fleet configuration |
| `manifests/evidence/STATUS-CUBE-CONVERGENCE-2026-05-31.md` | `local_verified` | Convergence report template |
| U.S. Chamber SMB AI report | `official_source` | Market validation |

---

## Proven / Held / Local-Only

**Proven**:
- Ollama agent slot 38 runs mistral locally ($0 cost)
- RAG dollhouse has ingested 90 source files
- Status Cube convergence achieved 2026-05-31
- Local wallet tracks invoices without fake revenue

**Held**:
- No external API calls during audit (local-only inference)
- No credential exposure (operator supplies repo access)
- No destructive mutations (read-only audit first)

**Local-Only**:
- All inference runs on operator hardware
- RAG index stored locally
- Before/after artifacts saved to local folder

---

## Next Safe Action

**For the buyer**:
1. Share repo path or clone URL
2. Grant read access (no write permissions needed)
3. Schedule 1-2 hour audit session
4. Receive before/after report with prioritized cleanup list

**For Lantern OS**:
1. Run `scripts/Invoke-LanternConvergenceLoop.ps1` on target repo
2. Generate RAG flat file via `skills/lantern-rag-dollhouse/`
3. Use Ollama agent for convergence analysis
4. Render PDF report with evidence citations

---

## Validation Path

1. **Before state**: Capture git status, file count, TODO count, broken link count
2. **Audit execution**: Run convergence loop + RAG ingestion + Ollama analysis
3. **After state**: Capture same metrics, compute delta
4. **Evidence attachment**: Cite all sources used in analysis
5. **Delivery**: PDF report + flat RAG file + prioritized action list

---

## Deliverables

| Artifact | Format | Purpose |
|----------|--------|---------|
| Before/After Report | PDF | Visual proof of cleanup |
| RAG Flat File | Markdown | Searchable knowledge index |
| Prioritized Issue List | Markdown | Actionable next steps |
| Status Cube Routing | Table | Safe decision matrix |
| Invoice | Markdown | Factual cash event |

---

## Pricing Model

| Tier | Scope | Price | Delivery |
|------|-------|-------|----------|
| Basic | Single repo audit (<100 files) | $199 | 1-hour session + report |
| Standard | Multi-repo audit (100-500 files) | $499 | 2-hour session + report |
| Premium | Fleet audit (500+ files + agent setup) | $999 | Half-day + ongoing support |

---

## Rights State

- **Source code**: Buyer retains full ownership
- **RAG index**: Buyer receives flat file (local-first)
- **Report**: Buyer receives PDF (can share internally)
- **Methodology**: Lantern OS retains IP on convergence process
- **Privacy**: No data leaves buyer's environment during audit

---

## Appendix: Example Before/After

### Before
```
Git status: 17 untracked files, 8 modified, 3 dirty worktrees
TODOs: 47 across 12 files
Broken links: 23
Stale references: 31
RAG index: Does not exist
```

### After
```
Git status: Clean working tree
TODOs: 12 (35 resolved, 35 held for later)
Broken links: 0 (all fixed or removed)
Stale references: 5 (26 resolved, 5 documented as held)
RAG index: Flat file with 90 sources, 42 asset hashes
Status Cube: All 4 axes converged
```

---

## Raw Commands

```powershell
# Run convergence loop on target repo
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1

# Generate RAG flat file
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Sync-RagAndPdf.ps1

# Run Ollama agent for convergence analysis
.\scripts\Invoke-OllamaAgent.ps1 -Prompt "Analyze convergence state and prioritize issues"

# Render PDF report
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Build-LanternConfidenceReport.ps1
```

---

## Receipts

- Ollama agent setup: <ref_file file="d:/tmp/lantern-os/docs/OLLAMA-AGENT-SETUP.md" />
- Agent fleet config: <ref_file file="d:/tmp/lantern-os/config/agents.json" />
- Status Cube convergence: <ref_file file="d:/tmp/lantern-os/manifests/evidence/STATUS-CUBE-CONVERGENCE-2026-05-31.md" />
- RAG dollhouse reference: <ref_file file="d:/tmp/lantern-os/skills/lantern-rag-dollhouse/references/LANTERN-OS-RAG-DOLLHOUSE.flat.md" />
