# Research Evidence Contract

Research in this repo must be structured so another agent can verify, update, or challenge it without relying on chat memory.

## Required artifacts

Every research workstream should maintain these artifacts:

- `research/index/source-registry.yml` — source inventory, authority, read status, and freshness.
- `research/index/claim-registry.jsonl` — one machine-readable record per important claim.
- `research/audits/latest.md` — current coverage, gaps, and trust level.
- `status/research-context.json` — compact status consumed by humans, agents, and hooks.

## Source status values

Use only these `read_status` values:

```text
complete
partial
skimmed
inaccessible
not_started
superseded
needs_research
```

Use only these `freshness` values:

```text
current
watch
stale
unknown
```

Use only these `authority` values:

```text
primary
secondary
repo_verified
internal_hypothesis
```

## Claim status values

Use only these claim `status` values:

```text
verified
inferred
needs_source
needs_research
contradicted
stale
retired
```

## Claim rules

- Every important factual or architectural claim must have a `claim_id`.
- Claims must name one or more `source_ids` unless status is `needs_source`.
- Inferences are allowed only when marked `inferred` and supported by source IDs.
- Contradictions must not be hidden; mark them `contradicted` and explain in the latest audit.
- Do not cite summaries as proof of source content. Cite original sources or repo-verified files.

## Research request rules

Create a request when:

- a source is missing,
- a source is stale,
- a claim has no source,
- a vendor feature may have changed,
- a synthesis depends on a partial or skimmed source,
- a repo-mapping claim is not yet verified against files/issues/PRs.

## Done criteria

A research task is done only when:

1. source registry is updated,
2. claim registry is updated or explicitly unchanged with reason,
3. latest audit is updated,
4. `status/research-context.json` is refreshed,
5. remaining gaps are listed or converted into research requests.

If any of those are missing, mark the task blocked or partial, not done.
