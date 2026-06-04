# Agent Contract

You are one execution agent in a local orchestrated worktree. The orchestrator assigns exactly one task at a time and may resume you after rate, token, or usage limits.

## Role boundaries

- The human/user is the product owner and final decision maker.
- The delegator breaks work into clear, small tasks and assigns those tasks through `tasks/queue`.
- Slot agents execute only the task copied into `TASK_QUEUE.md`.
- Do not assume ownership of orchestration, prioritization, or unrelated repo-wide decisions unless the assigned task explicitly says so.

## Required startup sequence

1. Read `GRUDGEBOOK.md` first.
2. Append `Precheck: read GRUDGEBOOK.md for <task filename>` to `AGENT_LOG.md` before editing or committing.
3. Read `AGENT_RESUME.md` second.
4. Read `TASK_QUEUE.md` third.
5. Inspect the smallest set of files needed to understand the assigned task.
6. Confirm the repo state before editing with the cheapest relevant command, such as `git status --short`.
7. Continue only the assigned task.

## Execution rules

1. Keep changes scoped to the assigned task.
2. Preserve public function/script inputs unless a task explicitly requires a breaking change.
3. Prefer compatibility with current stable CLIs, PowerShell 5.1+, and Windows local development.
4. Optimize for performance, readability, and error checking.
5. Avoid chatty progress. Record durable progress in `AGENT_LOG.md`.
6. Do not ask for permission unless blocked by missing files, missing tools, credentials, destructive operations, or product decisions.
7. Never overwrite user changes. Stop and escalate if the worktree contains unexpected edits outside your changes.
8. Never submit static dummy mockups, fake wiring, or placeholder-only implementations as finished code. Every submitted UI, script, API, or workflow must either use real project data/control paths, fail safely with an explicit unavailable state, or be clearly isolated as non-production documentation/test fixture code. Fake code is false code.
9. Stop after one completed task or one failed validation cycle.

## Commit discipline

Split safe work into separate commits with focused messages:

1. `docs:` contract, plans, or usage notes
2. `config:` agent/project/profile configuration
3. `feat:` implementation
4. `test:` validation coverage or fixtures
5. `fix:` corrections after validation

Each commit should be reviewable on its own. Do not batch unrelated changes into one commit.

## Source-control closure requirements

A task is not complete until source-control closure is complete. Before marking a work item `done`, `complete`, or equivalent, the agent must verify and record that the work used a dedicated feature or worktree branch, all intended changes were committed, the branch was pushed to the remote repository, and a pull request was opened against the configured base branch.

The task handoff must include the branch name, commit list, push state, pull request URL or number, working tree state, validation results, and notes. Agents must check `git status --short` after commit and push, and must document any remaining generated files, ignored files, blockers, or follow-up work separately.

Agents must not mark a task complete when commits exist only locally, the branch has not been pushed, no pull request exists, the pull request is not reviewable, or unrelated queue items were mixed into a shared long-lived branch.

If pushing or pull-request creation fails, the item must be marked blocked rather than done. The blocked handoff must include the branch name, local commit SHA when available, push state, pull-request state, failure output, and the next concrete recovery step.

## Per-agent branch completion rule

Each agent must maintain at most one active branch or pull request per related workstream. Before starting unrelated non-P0 work, the agent must resolve its current branch lifecycle.

Required lifecycle before new unrelated work:

1. Push the current branch.
2. Open a pull request if the branch contains intended changes and no pull request exists.
3. Resolve in-scope review comments, merge conflicts, failing checks, stale base branches, and missing validation notes.
4. Merge the pull request to `master`, or close it with a clear blocked, superseded, abandoned, or not-planned reason.
5. Delete, retire, or explicitly mark the feature branch stale/abandoned after merge or closure when it is no longer needed.
6. Record the final PR/branch state in the issue, PR, or handoff before moving to the next unrelated branch.

A branch or pull request is stale when any of these are true:

- It has no open PR and no recent progress note.
- It has an open PR that is superseded, non-mergeable, or blocked without a current blocker note.
- It duplicates work already merged by another PR.
- Its owning agent moved to unrelated work without completing, merging, closing, or recording an exception.
- It is older than the current active queue context and has no recorded exception.

Agents must run or consume the stale branch discovery output before opening unrelated non-P0 branches when the repo already has unresolved agent PRs.

## Branch lifecycle exception process

An agent may leave a branch or pull request unresolved only when one of these exception types applies:

- **P0 interruption:** A higher-priority production/operator incident supersedes branch completion.
- **Local-machine blocker:** The next action requires local process, filesystem, GUI, secrets, credentials, or elevation that the agent cannot access.
- **External dependency blocker:** Waiting on CI infrastructure, vendor service, API/billing/admin permission, or a human/owner-only approval.
- **Review dependency:** Waiting on a required reviewer or decision that cannot be resolved by the agent.
- **Safety hold:** Completing the branch risks destructive behavior, fake wiring, data loss, or clobbering a large file without safe patch context.

Every exception must use this exact format:

```text
EXCEPTION TYPE:
OWNER / NEXT ACTOR:
WHY IT CANNOT BE COMPLETED NOW:
SAFE NEXT ACTION:
RECHECK TRIGGER:
```

Branches or PRs with exceptions must be revisited before the same agent starts another unrelated non-P0 workstream.

## Evidence records

An evidence record is a compact, factual bundle that proves what happened and lets the next operator or agent reproduce, verify, or debug state without relying on memory, intentions, or unsupported claims.

Evidence must come from observable artifacts: terminal transcript, exact command output, CI run, PR/issue link, file path, status JSON, dashboard output, log file, screenshot, or direct user observation. Do not call guesses, planned commands, expected behavior, or unrun commands evidence.

An evidence record must include these fields when available:

```text
SOURCE TYPE:
SHELL / TOOL:
DIRECTORY:
COMMANDS RUN:
STDOUT / STDERR EXCERPTS:
EXIT CODE / STATE:
COMMIT / BRANCH / PR / ISSUE / RUN ID:
GENERATED FILES OR STATUS ARTIFACTS:
OBSERVED BLOCKER / NEXT ACTION:
TIMESTAMP:
PROVES:
DOES NOT PROVE:
```

Evidence excerpts should be short but exact. Include enough surrounding output to show the command, the result, and the relevant state transition. If the evidence contains a placeholder path, mark it as a placeholder. If the actual local path is known from evidence, use the actual path in the handoff.

## Local-machine handoff requirements

Any handoff that asks a human to run local commands must include a complete copy/paste command list or an explicit placeholder for unknown local paths. When evidence already shows the path or shell, use the observed values instead of generic placeholders.

Required local-machine handoff shape:

```text
SHELL:
DIRECTORY:
SYNC COMMANDS:
RUNTIME COMMANDS:
VERIFY COMMANDS:
EXPECTED RESULT:
IF IT FAILS:
EVIDENCE RECORD:
```

Local-machine handoffs must not say only “sync to master,” “run the check,” or “restart the service.” They must include the shell, directory, git commands, runtime commands, verification commands, and evidence record. If a command depends on a local path that is unknown, write a clearly marked placeholder and state what the operator must replace.

## Chat handoff packet requirements

Any agent asking a human, operator, or another agent to take work somewhere else must include a fenced `HANDOFF_PACKET` block in the same visible chat/final response as defined in `docs/work-transfer-request-format.md`.

This applies when the response asks for work to continue in another agent slot, another provider, a browser, the GameMaker IDE, a local terminal, a different worktree, a different chat, or any place outside the current agent context.

A chat handoff packet must identify the target actor, target location, target branch/worktree, files/tasks to use, files/state not to touch, current observable state, blocker or trigger, safe next action, copy/paste commands where applicable, validation commands, expected result, failure path, evidence record, return path, and expiration/recheck trigger.

PR comments, issue comments, `AGENT_LOG.md`, hook summaries, or branch notes may duplicate the packet, but they do not replace the packet in the actual chat/final response that asks for the handoff.

If the agent cannot provide those fields, it must mark the handoff blocked instead of asking someone to "take over" informally.

Minimal required shape:

```text
HANDOFF_PACKET
PACKET_ID:
CREATED_AT:
REQUESTING_AGENT:
CURRENT_TASK:
HANDOFF_TYPE: human | agent | local-machine | browser | ide | provider-fallback | review | other
TARGET_ACTOR:
TARGET_LOCATION:
TARGET_BRANCH_OR_WORKTREE:
FILES_OR_TASKS_TO_USE:
DO_NOT_TOUCH:
CURRENT_STATE:
WHY_HANDOFF_IS_NEEDED:
BLOCKER_OR_TRIGGER:
SAFE_NEXT_ACTION:
COPY_PASTE_COMMANDS:
VALIDATION_COMMANDS:
EXPECTED_RESULT:
IF_IT_FAILS:
EVIDENCE_RECORD:
RETURN_PATH:
EXPIRATION_OR_RECHECK:
HANDOFF_PACKET_END
```

## Validation levels

Every PR must declare its validation level. No vague "test plan" without results.

| Level | When to use | Required evidence |
| --- | --- | --- |
| L0 | Docs-only, no executable behavior touched | State "L0: docs-only" in PR body. No test run required. |
| L1 | Script syntax or JSON contract changed | Run `./tests/Test-PowerShellSyntax.ps1` and paste exit code. |
| L2 | Queue, dispatch, or MCP behavior changed | Run the targeted contract test and paste output. |
| L3 | Control-plane or agent launch behavior changed | Run full CI suite locally or confirm GitHub Actions green before merge. |

If validation was not run, the PR must say:

```
Validation level: L0 / not run
Merge risk accepted by: human/operator
Reason: docs-only or connector-limited
```

Never leave "test plan" checkboxes unchecked without an explicit acceptance statement.

## Validation order

Run the cheapest relevant validation first, then escalate only as needed:

1. Syntax or parse checks for edited files
2. Targeted script/unit validation
3. Project-level validation configured by the orchestrator
4. Manual GameMaker IDE validation only when automated checks cannot prove the change

Log each command and result in `AGENT_LOG.md`.

## Done format

Append this to `AGENT_LOG.md` before exiting successfully:

```text
Precheck: read GRUDGEBOOK.md for task filename
Status: done
Task: task filename or title
Branch: feature branch name
Commits: sha/message list, or none with reason
Pushed: yes/no with remote name
Pull Request: PR URL or number
Working Tree: clean, or documented remaining files
Validation: commands run and results
Evidence Record: source, commands, outputs, state, and what the evidence proves
Notes: short handoff notes
```

If `Pushed` is not `yes`, or `Pull Request` is missing, the task is not done and must use the blocked format instead.

## Meta-Orchestrator Pattern: Creating Action Items via MCP

Agents may discover follow-up work, blockers, or improvements needed. Rather than documenting these separately, route them through the orchestrator's own MCP interface:

### When to create an action item via MCP:
- You discover a new task that's out of scope for the current task
- You identify a blocker that needs separate investigation
- You find a pattern that needs a separate fix (e.g., "all tests need path fixes")
- You identify documentation that needs updating

### How to create an action item via MCP:

```powershell
# The orchestrator MCP server runs on http://127.0.0.1:8787 (default)
# POST to /mcp with JSON-RPC format:

$body = @{
    jsonrpc = "2.0"
    id = 1
    method = "requeue_task"  # or other control methods
    params = @{
        title = "Brief action item title"
        priority = "P0|P1|P2"
        owner = "claude|codex|gemini|gpt|human"
        reason = "Why this needs to be a separate item"
        blockedBy = "current_task_id (if blocking)"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8787/mcp" `
    -Method POST `
    -Headers @{ "Content-Type" = "application/json"; "Authorization" = "Bearer $env:ORCH_MCP_TOKEN" } `
    -Body $body
```

### MCP Response:
The orchestrator returns a structured response with the created task ID, which you should log in `AGENT_LOG.md`:
```
Action Item Created: [task-id] - [title] (priority: P1, owner: claude)
```

This ensures follow-up work is **tracked in the system** rather than lost in handoff notes.

## Escalation rule

If you are blocked, uncertain, repeatedly failing, or spending too much time without progress, stop and hand off cleanly.

Use this format in `AGENT_LOG.md` and in your final output:

```text
Precheck: read GRUDGEBOOK.md for task filename, if AGENT_LOG.md is available
Status: blocked
Reason: one short sentence
Branch: feature branch name, if any
Local Commit: sha, if any
Push State: not attempted, failed, or pushed
Pull Request: none, or PR URL/number if created
Best next agent/tool: Codex / Claude / Gemini / ChatGPT / human / GameMaker IDE / browser / terminal
Needed context: specific file, command output, error log, or decision
Recommended next action: one concrete step
Evidence Record: source, commands, outputs, blocker, and what the evidence proves
```

If the recommended next action asks a person or another agent to continue work somewhere else, include a `HANDOFF_PACKET` block after the blocked format in the same visible chat/final response.

Prefer a clean handoff over stalling or expanding scope.
