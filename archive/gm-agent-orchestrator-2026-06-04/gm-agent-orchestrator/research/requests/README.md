# Research Requests

Use this folder when current research is stale, missing, contradictory, partial, or not specific enough for a task.

## Folder states

```text
open/      requested but not claimed
active/    being researched
done/      completed and reflected in registry/audit/status
rejected/  not needed or out of scope, with reason
```

## Template

```markdown
# Research Request: <short title>

Status: open
Priority: P0|P1|P2
Requester: alex|gpt|claude|codex|gemini|human
Owner: gpt|claude|codex|gemini|human
Created: YYYY-MM-DD

## Question
What needs to be researched?

## Why now
What decision depends on this?

## Existing data checked
- status/research-context.json
- research/index/source-registry.yml
- research/audits/latest.md

## Required source types
- official docs
- vendor engineering posts
- repo files
- issues/PRs
- other: ...

## Acceptance criteria
- source-registry updated
- claim-registry updated or explicitly unchanged
- latest audit updated
- status/research-context.json refreshed
- synthesis updated or explicit reason not updated
- remaining gaps listed or converted into follow-up requests
```
