# OSS Intake Preference Policy

Status: active preference

## Preference

Prefer the lightest useful option:

```text
functions or methods > small dependencies > focused clones > C:\tmp sandbox
```

This is a preference, not an absolute law. Use heavier options when they are clearly safer, faster, or more correct.

## Meaning

1. First try existing local code, shell commands, small scripts, functions, methods, schemas, and patterns.
2. Add a dependency when it reduces risk or avoids fragile custom work.
3. Clone an external repo when source inspection, examples, tests, or license review are needed.
4. Use `C:\tmp` or another named sandbox for disposable external intake.
5. Do not promote temporary clones or dependency experiments without a receipt.

## Decision table

| Need | Preferred intake |
|---|---|
| Simple text transform | function / small script |
| Known stable library behavior | dependency |
| Need to inspect project structure or tests | focused clone |
| Unknown, risky, or temporary experiment | `C:\tmp` sandbox |
| Production path | promoted file with receipt and validation |

## RAGDoll intake rule

Store the distilled lesson, not the whole repo, unless full source is necessary.

Every promoted OSS intake should record:

- source URL;
- what was learned;
- why a function, dependency, clone, or sandbox was chosen;
- license note if relevant;
- promotion status: hold, candidate, or promote;
- validation performed.

## Windsurf application

For Windsurf-related OSS:

- prefer `.windsurfrules` examples and memory patterns over cloned repos;
- prefer prompt/rule snippets over dependencies;
- use official docs for product behavior;
- use community repos as examples, not authority;
- keep sessions short and validated.

## Boundary

Do not mass-clone into active worktrees.
Do not add dependencies for one-off tasks when a small function is enough.
Do not treat `C:\tmp` experiments as canonical without review.
Do not overwrite dirty worktrees during intake.
