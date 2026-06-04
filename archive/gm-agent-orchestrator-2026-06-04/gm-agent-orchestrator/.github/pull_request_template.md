## Summary

<!-- What changed, in one short paragraph. -->

## Related issue / task

<!-- Link the GitHub issue and/or local task path. -->

- Issue:
- Task:

## Files changed

<!-- List the important files or directories changed. -->

-

## Safety / mutation scope

<!-- State what this PR does and does not mutate. -->

- [ ] Does not move live queue/active/done/failed tasks unless explicitly part of this PR
- [ ] Does not wake or reroute agents unless explicitly part of this PR
- [ ] Does not print secrets or environment dumps
- [ ] Uses repo-root/path containment for local file operations, where relevant

## Deterministic-first review

<!-- Prefer deterministic checks before model/tool-heavy review when possible. -->

- [ ] Checked whether this could be validated by static analysis, schema/JSON parsing, regex, diff inspection, or an existing contract test
- [ ] Added or reused deterministic validation where practical
- [ ] Used model/tool-heavy review only for semantic judgment, ambiguity, architecture, risk, or tradeoff review

## Industry-standard review readiness

<!-- These make the PR reviewable by another engineer, not just by the author/agent. -->

- [ ] Risk level declared: <!-- low / medium / high -->
- [ ] Validation evidence included below
- [ ] Rollback path included below
- [ ] Reviewer can understand the intent without reading every changed line
- [ ] Blocking comments / unresolved threads are addressed before merge

## Validation

<!-- Paste exact validation commands/results or explain why validation is not available. -->

```text
Not run yet.
```

## Agent branch lifecycle

- Branch:
- PR owner / next actor:
- Current status: <!-- ready / draft / blocked / superseded / needs local validation -->
- Open review comments addressed: <!-- yes/no/n/a -->
- Expected close path: <!-- merge / superseded by # / close not planned -->

## Rollback

<!-- State how to revert safely. For docs-only changes, say revert PR. For scripts/config, include backup/rollback path. -->

## Follow-up

<!-- One or two explicit follow-ups maximum. -->

-
