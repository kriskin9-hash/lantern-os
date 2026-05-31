# Workflow Duplication Audit

Generated: `2026-05-31T04:54:57.095173+00:00`

## Summary

- Repositories scanned: `1`
- Workflows scanned: `5`
- Exact duplicate groups: `0`
- Governance reuse candidates: `2`

## Exact Duplicate Groups

No exact duplicate workflow files found.

## Governance Reuse Candidates

### `lantern-os` — `D:\tmp\lantern-os\.github\workflows\mcp-tunnel-canary.yml`
- Governance score: `1`
- Steps:
  - `Validate tunnel URL shape`
  - `Probe health and tool-discovery endpoints only`
  - `Upload canary result`
- Actions:
  - `actions/upload-artifact@v4`

### `lantern-os` — `D:\tmp\lantern-os\.github\workflows\static-surface-ci.yml`
- Governance score: `1`
- Steps:
  - `Verify shareholder index exists`
  - `Verify top-level operator files`
  - `Check required Lantern manifests`
  - `Verify HTML surface links`
  - `Install pytest`
  - `Run tests`
  - `Verify CI has parallel lanes and final summary gate`
  - `Summarize passed lanes`
