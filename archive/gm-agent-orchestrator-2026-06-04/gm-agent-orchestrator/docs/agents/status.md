# Agent Status

## Active setup

### LFM2-24B-A2B local

Status: active setup.

Purpose:

- repeated low-risk agent steps
- local routing
- summarization
- classification
- tool selection
- file triage
- test-output and log summarization

Restrictions:

- read-only by default
- no destructive actions
- no production code edits without review
- no autonomous loops
- no shell execution delegated from the model
- no secrets, credentials, or tokens in prompts

## Initializing / deferred

### Amp Agent

Status: initializing / deferred.

Reason:

- Windows native path is not the active setup path right now
- WSL reset/restart is deferred
- Amp remains a future preferred coding-agent path, not the current execution lane

Allowed next steps:

- document install options
- prepare guarded wrapper scripts
- keep Amp outside the active routing path until setup is stable
