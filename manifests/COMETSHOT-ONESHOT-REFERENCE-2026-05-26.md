# Cometshot Oneshot Reference - 1@5/26

Status: record reference.

Source: operator request in Lantern OS browser session on 2026-05-26.

Command phrase:

```text
!cometshot !oneshot 100 times
```

Bounded interpretation:

Run one validated control-plane pass that checks the Lantern OS Garage app,
flat RAG house, local conversations, RAG cache intake, repo source status, docs,
skills, and MCP-visible boundaries. Do not perform 100 destructive runs, delete
repos, mutate boot settings, move tasks, or pretend unverified state is proven.

Reference key:

```text
1@5/26
```

## Yes

- Use `C:\tmp\lantern-os` as the control plane.
- Merge HFF, orchestrator, GM, and Lantern OS into one flat RAG house by
  source-labeled read-only ingestion.
- Store compressed RAG records.
- Store local conversations locally and keep raw logs ignored from git.
- Show Windows/boot boundaries in the UI.
- Auto-update the UI by refresh only.
- Mark old repos as source-evidence or archive-by-manifest.

## No

- No repo deletion.
- No local worktree deletion.
- No GitHub archive/delete action.
- No bootloader, BCD, firmware, partition, or default-boot mutation.
- No hidden features.
- No raw private image dump.
- No claim that dirty source repos are clean.
- No financial, medical, sensitive-domain, or geopolitical claim without source
  checks.

## Validation Target

```powershell
node apps\lantern-garage\validate.js
```
