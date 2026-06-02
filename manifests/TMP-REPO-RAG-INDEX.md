# D:\tmp Repository RAG Index

Generated: 2026-05-31.

## Simple Answer

All repositories in `D:\tmp` are indexed here by GitHub origin and RAG intake
state. No local path is the source of truth; CI/CD checks out repos dynamically
and the RAG dollhouse tracks content states.

## What This Index Does

- Maps every `D:\tmp` folder to its canonical GitHub remote (if any).
- Assigns each repo a RAG intake state per `skills/lantern-rag-dollhouse/SKILL.md`.
- Replaces hardcoded local paths in scripts, configs, and docs with
  GitHub-metadata references.
- Provides the lookup table CI/CD workflows use to `actions/checkout` the
  correct repositories.

## Evidence / Source Discipline

- Git remotes verified by `git remote get-url origin` on 2026-05-31.
- Non-git folders marked as `not_yet_cloned` or `local_asset_copied`.
- Dirty-state evidence comes from `git status --short` at indexing time.

## Repo Index

| Local Folder | GitHub Origin | RAG State | Notes |
|---|---|---|---|
| `D:\tmp\lantern-os` | `https://github.com/alex-place/lantern-os.git` | `local_inspected` | Primary orchestrator repo. Convergence loop and CI/CD live here. |
| `D:\tmp\human-flourishing-frameworks-scan` | `https://github.com/human-flourishing-frameworks/human-flourishing-frameworks.git` | `local_inspected` | HFF main repo. Dirty (9 changes). |
| `D:\tmp\hff-master-clean` | `https://github.com/human-flourishing-frameworks/human-flourishing-frameworks.git` | `local_inspected` | HFF mirror. |
| `D:\tmp\hff-lantern-recovery` | `https://github.com/human-flourishing-frameworks/human-flourishing-frameworks.git` | `local_inspected` | HFF mirror. |
| `D:\tmp\hff-public-site` | `https://github.com/human-flourishing-frameworks/hff-public-site.git` | `local_inspected` | HFF public site. |
| `D:\tmp\hff-seven-validate` | `https://github.com/human-flourishing-frameworks/human-flourishing-frameworks.git` | `local_inspected` | HFF mirror. |
| `D:\tmp\lantern-symbolic-sandbox` | `https://github.com/alex-place/lantern-symbolic-sandbox.git` | `local_inspected` | Symbolic sandbox experiments. |
| `D:\tmp\lantern-discord` | *(none)* | `not_yet_cloned` | No `.git` directory. Treat as local-only or init repo. |
| `D:\tmp\lantern-os (1)` | *(none)* | `not_yet_cloned` | Duplicate folder, no `.git`. |
| `D:\tmp\lantern-os-skills` | *(none)* | `not_yet_cloned` | No `.git` directory. |
| `D:\tmp\lantern-os-zip-work` | *(none)* | `not_yet_cloned` | No `.git` directory. |
| `D:\tmp\hff-evidence-master-clean` | *(none)* | `not_yet_cloned` | No `.git` directory. |
| `D:\tmp\hff-release-candidate` | *(none)* | `not_yet_cloned` | No `.git` directory. |
| `C:\Users\alexp\Documents\gm-agent-orchestrator` | *(unknown)* | `held` | Referenced by convergence loop. Verify remote before promotion. |

## Proven

- `lantern-os` convergence loop runs clean (0 issues) after local-path fixes.
- `human-flourishing-frameworks-scan` has a valid GitHub remote.
- `hff-public-site` has a distinct GitHub remote.

## Held

- `gm-agent-orchestrator` remote not verified. Local path only.
- `lantern-discord` and other non-git folders need repo initialization or
  RAG-only treatment.

## Next Safe Action

1. Update all lantern-os scripts/configs to read `TMP-REPO-RAG-INDEX.md`
   instead of hardcoded paths.
2. Update CI/CD workflows to check out repos by GitHub origin from this index.
3. Verify `gm-agent-orchestrator` remote and add it to the index.
4. Init git repos for `lantern-discord` and other non-git folders, or mark
   them `local_asset_copied` if they are build artifacts only.

## Validation Path

1. Rerun `scripts/Invoke-LanternConvergenceLoop.ps1`.
2. Verify no `SOURCE-MISSING-*` or `SOURCE-GIT-STATUS-FAILED-*` issues.
3. Verify CI/CD workflows reference GitHub origins, not local paths.
