# Lantern OS Dream Journal v1.0.1 — Release Convergence Report

**Date:** 2026-06-05
**Analyst:** Convergence Loop / Keystone
**Scope:** Dream Journal release readiness, code audit, and stabilization path

---

## Executive Summary

I recommend shipping v1.0.1 tomorrow only as a **stabilization patch**, not as the "full 3 Door Game" feature drop.

The strongest reason is scope discipline: the repo's own release notes and roadmap position v1.0.1 as the release where the interactive 3 Door Game becomes "full," which is a backward-compatible feature addition and therefore fits a minor bump better than a patch under SemVer. If you want to keep the tag v1.0.1, narrow tomorrow's scope to bug fixes, honesty fixes, CI recovery, and UX corrections; if you want to market a true 3 Door feature launch, move that marketing label to v1.1.0 instead.

The repo is **not launch-clean at HEAD**. The latest batch merge PR merged 14 branches into master, and Gmail connector results show failed runs on CI, OSS Repository Validation, Static Surface CI, and Convergence Manager for the merged master commit `395bffa`. That is a material launch blocker for a tomorrow release because the current static-surface workflow is not a cosmetic linter; it checks repo anchors, manifests, full pytest, and a Windows/PowerShell convergence boundary.

The highest-priority release gaps are concentrated in four places: command grammar is not implemented beyond `!debug`, agent selection is nondeterministic, the current 3 Doors flow is not image-first, and docs/privacy claims drift from the actual runtime. Those are the areas that should receive tomorrow's effort first.

---

## Release Recommendation

### Recommended version decision

**Recommended tomorrow decision:** keep the tag `v1.0.1`, but redefine tomorrow's release as **"Dream Journal v1.0.1 — stability and honesty patch"**. Do not announce the full interactive 3 Door Game tomorrow unless you also implement the missing command/mode routing and the image-first flow. The repo's own roadmap and release notes say v1.0.1 is where the 3 Door Game becomes "full," but SemVer reserves a patch release for backward-compatible bug fixes and a minor release for backward-compatible new functionality.

### Path options

| Path | Recommendation | Why |
|------|---------------|-----|
| **Patch path** | Ship v1.0.1 tomorrow as a stability release | Matches SemVer if scope is limited to bug fixes, CI cleanup, privacy/docs corrections, deterministic routing, and 3 Doors UX honesty. |
| **Feature path** | Rename the true 3 Door launch to v1.1.0 | Matches the roadmap/release-note promise that the 3 Door Game becomes "full" in the next feature-bearing release. |

### Needs vs wants for tomorrow

| Priority | Needs for tomorrow | Wants to defer |
|----------|-------------------|----------------|
| **P0** | Restore green release posture on master; fix command grammar expectations; make agent routing deterministic; remove or correctly label "image-first" 3 Doors claims; correct privacy/local-first release notes and docs; verify release notes against actual runtime. | Full interactive 3 Door Game marketing, image generation backend, deeper convergence feature claims. |
| **P1** | Fix stale release tooling and stale docs; verify export and search paths; run local smoke and regression suite; confirm model defaults and messaging. | Real vector similarity in `_multi_signal_score()`, full hff-api parity, full convergence I/O plumbing. |
| **P2** | Post-release observability cleanup and release automation polish. | Stable Diffusion door images, blockchain/AAPF expansion, guild-tier activation. |

---

## Suggested Changelog Entries

Use a curated changelog entry, not a commit dump. Keep a Changelog explicitly recommends grouping notable changes for humans rather than pasting commit diffs.

### Suggested CHANGELOG.MD entry (patch framing)

```markdown
## [1.0.1] — 2026-06-06 — Dream Journal Stability and Honesty Patch

### Fixed
- Deterministic agent selection in Dream Chat to reduce nondeterministic routing.
- Command handling clarified: unsupported bang-commands no longer silently behave like normal chat.
- Three Doors UX corrected so door-state behavior matches the documented experience.
- Provider settings persistence aligned with documented local secret handling.
- Release notes and user guide corrected to match actual runtime behavior and data paths.

### Changed
- Release messaging now distinguishes verified local behavior from planned future behavior.
- Launch validation now uses current repo files and current test paths.

### Verification
- Local Dream Chat smoke-tested on `apps/lantern-garage`.
- Node Dream Journal API tests passed.
- Multi-turn Dream Chat tests passed.
- Release blockers on master reviewed and either fixed or explicitly held.
```

---

## Code Audit and Priority Findings

### Recent commits, issues, and pull requests that matter most

The recent commit/PR stream shows exactly why tomorrow should be a stabilization release. A release-notes commit (`9733444`) introduced launch messaging that says the full 3 Door Game follows in v1.0.1; a hotfix commit (`5c4bffe`) restored `server.js` and `dream-chat.html` after base64 corruption and fixed a crashing `/api/dream/stats` typo; PR #169 added memory indexes and new tests; PR #172 overhauled the README; and PR #173 then batch-merged 14 branches into master, immediately followed by failed workflow notifications.

### Audit findings table

| Area | Finding | Why it matters | Exact files/functions |
|------|---------|---------------|----------------------|
| **Command grammar** | The client only special-cases `!debug`; every other non-empty input is appended as a user bubble and sent to the streaming endpoint. The server route also just forwards message into `dreamChatReply` / `handleStreamChat`. | There is no enforceable distinction today between "report," "export," and "3 Doors" style commands, so command-grammar expectations can drift silently. | `apps/lantern-garage/public/dream-chat.html` → `sendMessage()`, `streamAgentResponse()`; `apps/lantern-garage/routes/dream.js` → `/api/dream/chat`, `/api/dream/chat/stream` |
| **Mode classification** | `selectAgent()` adds `Math.random() * 3` to routing scores before sorting. | This makes routing nondeterministic, complicates reproducibility, benchmarking, regression tests, and user trust. | `apps/lantern-garage/lib/dream-chat.js` → `selectAgent()`, `dreamChatReply()` |
| **3 Doors image-first rule** | The runtime creates a hidden `[DOORS: ...]` line and parses it into text suggestions; the UI streams text tokens first and only appends the doors banner after `done`, and only when three suggestions exist. | The current implementation is not image-first. If you market it that way tomorrow, the release note will overclaim. | `apps/lantern-garage/lib/stream-chat.js` → `extractDoors()`, `doorsOrFallback()`, `handleStreamChat()`; `apps/lantern-garage/public/dream-chat.html` → `finishStream()`, `appendDoorsBanner()` |
| **Privacy and local-first honesty** | Release notes say nothing is uploaded to the cloud and entries live in browser local storage and `data/dreams/`; in reality, the active Node app posts prompts to Google/Anthropic when keys exist, stores settings by writing `.env`, reads `.env` from repo root, and stores journal entries under `data/dream_journal`. Also, the server binds to `0.0.0.0` when `PORT` is set. | This is the largest user-facing honesty risk in the release package. | `docs/release/RELEASE-NOTES-v1.0.0.md`; `docs/DREAM-JOURNAL-USER-GUIDE.md`; `apps/lantern-garage/routes/dream.js`; `apps/lantern-garage/lib/stream-chat.js`; `apps/lantern-garage/lib/dream-chat.js`; `apps/lantern-garage/server.js` |
| **Release tooling drift** | The PowerShell release validator is still labeled "Dream Journal v0," checks files like `public/app.js`, `data/dreamers`, `tests/e2e/dreamer-journal.spec.ts`, and other paths that are not reliable launch gates for the current surface. The docs also reference `docker-compose.dream-journal.yml` and `perf_dream_journal.py`, but search results surface those mainly from docs/archive while the Makefile still expects the compose file. | Launch-day checklists must not rely on stale validators. | `scripts/Test-DreamerJournalRelease.ps1`; `docs/DREAM-JOURNAL-QUICKSTART.md`; `docs/PR-DREAM-JOURNAL.md`; `Makefile` |
| **Memory/export honesty beyond the main app** | There are still explicit placeholder paths: `export_csf_stub()` returns `"CSF-v1-stub"`, hff-api `/recent` returns empty entries, and `convergence_io_route_on_slice()` is documented as a placeholder bridge. | These may not block tomorrow's Dream Journal patch, but they raise convergence-surface honesty risk and argue against broader feature claims. | `src/discord_lounge_bot/memory_layer.py`; `src/hff-api/routes/dream_journal.py`; `src/converged_tesseract.py` |

---

## Security and Privacy Risks

The repo's security policy says secrets belong in ignored local environment files or a secret manager and that only safe examples such as `.env.example` should be committed. The current Dream Journal provider-settings route writes directly to `.env` at repo root and hot-reloads values into `process.env`. That is convenient for a single operator machine, but it increases the chance of local secret sprawl and contradicts the stronger documentation language elsewhere.

The server defaults to `127.0.0.1`, which is good, but it explicitly switches to `0.0.0.0` whenever `PORT` is present, and the streaming endpoint returns permissive `Access-Control-Allow-Origin: *`. That combination is not inherently unsafe, but it means privacy claims must say "local by default; remote if you configure deployment/provider keys" rather than "nothing ever leaves your machine."

---

## Quick Fixes and Patch Outlines

### Patch A — deterministic agent routing

Remove randomness from `selectAgent()` and use a stable tie-breaker. This directly improves reproducibility and testing.

```javascript
// apps/lantern-garage/lib/dream-chat.js
function selectAgent(message) {
  const lower = String(message || "").toLowerCase();
  const scores = AGENT_PERSONAS.map((agent, index) => {
    let score = 0;
    const keywords = {
      lantern:  ["light", "flame", "steady", "safe", "home", "glow", "protect", "lantern"],
      blinkbug: ["static", "glitch", "tv", "crt", "caterpillar", "bug", "screen", "chaotic", "unhinged", "geeked", "windows", "xp"],
      keystone: ["truth", "anchor", "memory", "story", "pattern", "integrate", "return door", "hold", "remember"],
      waterfall:["flow", "water", "heal", "gentle", "emotion", "feeling"],
      xenon:    ["space", "ship", "navigate", "map", "course", "direction"],
      founder:  ["wish", "protect", "founder", "home", "return", "safety"],
    };
    for (const kw of (keywords[agent.id] || [agent.id])) {
      if (lower.includes(kw)) score += 10;
    }
    return { agent, score, index };
  });
  scores.sort((a, b) => b.score - a.score || a.index - b.index);
  return scores[0].agent;
}
```

### Patch B — add a real command router

Tomorrow's release should reserve command prefixes explicitly instead of letting them fall through as ordinary chat text.

```javascript
// shared utility
function parseBangCommand(input) {
  const m = String(input || "").trim().match(/^!(\S+)(?:\s+(.*))?$/);
  if (!m) return null;
  return { name: m[1].toLowerCase(), args: (m[2] || "").trim() };
}

// client or server
const cmd = parseBangCommand(message);
if (cmd?.name === "debug") { /* existing behavior */ }
if (cmd?.name === "three-doors") { /* set explicit mode */ }
if (cmd?.name === "report") { /* route to report generator or return unsupported */ }
if (cmd?.name === "export") { /* route to export endpoint or return unsupported */ }
if (cmd) return sendJson(res, { error: "unsupported_command", command: cmd.name }, 400);
```

### Patch C — stop writing provider keys to `.env`; prefer `.env.local`

The roadmap and contribution/security guidance already lean that way.

```javascript
// apps/lantern-garage/routes/dream.js
const envFilePath = path.join(repoRoot, ".env.local");

// apps/lantern-garage/server.js
const candidateEnvFiles = [
  path.resolve(__dirname, "..", "..", ".env.local"),
  path.resolve(__dirname, "..", "..", ".env"),
];
for (const envPath of candidateEnvFiles) {
  if (!fs.existsSync(envPath)) continue;
  fs.readFileSync(envPath, "utf8").split("\n").forEach((line) => {
    const m = line.match(/^([A-Z0-9_]+)\s*=\s*(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^['"]/g, "").replace(/['"]$/g, "");
  });
}
```

### Patch D — either implement image-first or stop claiming it

The clean release choice for tomorrow is to stop claiming image-first and describe the current state honestly as "three door suggestions rendered after the response." If you do want image-first, change the stream contract so the server emits a doors event before the main text, and have the client render the banner before the assistant body. The queued Stable Diffusion image route remains a future task, not current behavior.

---

## Test, Performance, and Grounding Plan

### Automated tests and local commands to run

The most trustworthy launch-day commands are the current repo tests and smoke checks, not the old v0 release validator. The changelog says the Node API suite and multi-turn suite were passing for v1.0.0, but the current master merge now has failing workflows, so tomorrow's gate should be "re-run locally, then re-run CI", not "assume still green."

```bash
git fetch origin
git checkout master
git pull --ff-only origin master
npm start --prefix apps/lantern-garage

# Local API smoke
curl -s http://127.0.0.1:4177/api/dream/stats
curl -s "http://127.0.0.1:4177/api/dream/search?text=release"
curl -s -OJ "http://127.0.0.1:4177/api/dream/export?format=jsonl"
curl -s -OJ "http://127.0.0.1:4177/api/dream/export?format=csv"

# Local regression suites
node tests/test_dream_journal_api.js
node tests/test_dream_chat_multiturns.js
node tests/test_dream_journal_chat.js
python -m pytest tests/test_dreamer_journal.py tests/test_dreamer_integration.py -q

# Command grammar / honesty checks
grep -Rni "Math.random()" apps/lantern-garage/lib/dream-chat.js
grep -Rni "export_csf_stub\|TODO: wire to actual\|placeholder bridge" src/
grep -Rni "Nothing is uploaded to a cloud\|local storage\|data/dreams/" docs README.md
```

### Performance and acceptance targets for tomorrow

The repo contains a historical Dream Journal benchmark document showing very strong latency and memory numbers, but that document describes a different lean container/service shape than the current active Node garage routes, so it should be treated as historical context, not current release evidence.

| Check | Recommended target | Why |
|-------|-------------------|-----|
| Server startup | local server reachable in under 5 seconds | Historical docs claim 2–3 seconds; use a slightly looser launch gate for the current Node surface. |
| `/api/dream/stats` | median under 150 ms locally | Current code rereads monthly JSONL files on each request, so do not set an unrealistically low threshold until caching exists. |
| `/api/dream/export` | valid CSV/JSONL output for existing entries | Export correctness matters more than raw speed tomorrow. |
| Dream chat first token | first SSE token under 2 seconds with a configured provider; under 500 ms for local fallback | Distinguishes normal provider latency from degraded/offline UX. |
| Determinism | same prompt routes to same agent in repeated runs | Directly fixes current reproducibility problem. |

### Grounding and stability checks

| Stability check | What to verify | Command or method |
|-----------------|---------------|-------------------|
| **Memory boundary honesty** | Turn 7 should not be silently treated as still in-window if the system only promises 6-turn chat history. | Send 8-turn scripted conversation; compare answer quality and assert the oldest turn is not referenced unless present in recent dream data. |
| **Private-IP handling** | Default bind should stay `127.0.0.1`; deployment exposure should be explicit. | Start locally with no `PORT`; confirm console says `127.0.0.1`. Then test with `PORT=4177` only in a non-production shell to verify exposure behavior. |
| **Partial-export honesty** | If export fails or becomes filtered later, responses must not pretend they are complete. | Verify CSV and JSONL both round-trip existing entries. Add a future response contract with `partial`, `count`, and `source_files` fields if export logic changes. |
| **Reproducibility** | Same prompt, same agent, same mode, same command handling. | Remove `Math.random()` and run 20 identical prompt trials. |
| **Model naming stability** | Decide whether docs should prefer cost/performance or newest stable model names. | Keep Gemini 2.5 Flash if cost/latency is the goal; otherwise explicitly test Gemini 3.5 Flash. |

If you implement structured trace logging later, use OpenTelemetry-style traces/spans rather than ad hoc strings. That matches the repo's planned issue and the official instrumentation model.

---

## Launch-Day Checklist and Rollback

### Release flow

| Step | Action | Exact command |
|------|--------|---------------|
| Freeze scope | Treat tomorrow as a patch unless you explicitly retag as v1.1.0. | `git checkout master && git pull --ff-only origin master` |
| Run local server | Bring up the active Dream Journal surface. | `npm start --prefix apps/lantern-garage` |
| Smoke core API | Validate stats, search, export, and chat. | `curl -s http://127.0.0.1:4177/api/dream/stats` |
| Run regressions | Run the current Node and Python suites. | `node tests/test_dream_journal_api.js && node tests/test_dream_chat_multiturns.js && node tests/test_dream_journal_chat.js && python -m pytest tests/test_dreamer_journal.py tests/test_dreamer_integration.py -q` |
| Docs honesty sweep | Remove or rewrite claims that say "nothing leaves your machine" if provider keys are configured, and correct `data/dreams/` / localStorage claims where needed. | `grep -Rni "Nothing is uploaded to a cloud\|local storage\|data/dreams/" docs README.md` |
| CI gate | Do not publish if master is still red. | Re-run the failed GitHub workflows from the UI or CLI after fixes. |

### Release commands

```bash
git tag v1.0.1
git push origin v1.0.1
gh release create v1.0.1 \
  --draft \
  --title "Dream Journal v1.0.1" \
  --notes-file docs/release/RELEASE-NOTES-v1.0.1.md
```

### Rollback flow

```bash
# move working tree back to the prior known-good release
git checkout v1.0.0

# if the v1.0.1 GitHub release was published prematurely
gh release delete v1.0.1 -y || true

# if the tag itself must be removed
git push --delete origin v1.0.1 || true
git tag -d v1.0.1 || true

# restart local app on prior version
npm start --prefix apps/lantern-garage
```

### Monitoring and user communication

For the first hour after launch, watch three things only: master workflow status, local smoke test pass/fail, and user-facing release note accuracy. Because the current repo has multiple failed workflow emails around the batch merge, a quiet post-launch period is not enough; you want explicit green evidence.

**Suggested user-facing release wording for tomorrow:**

> Dream Journal v1.0.1 is a stability and honesty patch. It tightens routing, corrects release-note drift, and improves Dream Chat reliability. The larger interactive 3 Door feature set remains in progress.

That wording matches both SemVer discipline and the repo's actual readiness far better than "full 3 Door Game shipped."

---

## Risks, Timeline, and Assumptions

### Risk assessment and mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Master is red at release time | High | High | Block publication until CI, OSS validation, static-surface CI, and convergence workflow failures are resolved or explicitly held. |
| Version/tag mismatch | High | High | Keep tomorrow as a patch or rename the feature launch to v1.1.0. |
| Privacy/local-first overclaim | High | High | Rewrite release notes and user guide to reflect provider-key behavior, `.env` persistence, and deployed-host exposure. |
| Mode/command confusion | High | Medium | Add explicit command parsing and unsupported-command responses. |
| Image-first claim drift | High | Medium | Remove claim or implement event-first/banner-first flow before launch notes go out. |
| Release validator drift | Medium | Medium | Use a trimmed launch checklist tomorrow; fix old PowerShell validator afterward. |

### Suggested timeline for tomorrow

Assuming America/New_York local operations and an afternoon release target:

| Window | Task | Owner |
|--------|------|-------|
| Morning | Scope freeze: decide patch-only versus feature launch. | Open / unassigned |
| Morning | Apply P0 patches: deterministic routing, command parser, doc honesty corrections. | Open / unassigned |
| Late morning | Local smoke + Node/Python regressions. | Open / unassigned |
| Early afternoon | Re-run failed GitHub workflows and verify green state on master. | Open / unassigned |
| Early afternoon | Draft release notes and announcements using patch framing. | Open / unassigned |
| Release window | Create draft tag/release, do final smoke, then publish. | Open / unassigned |
| First hour after release | Monitor workflows, local smoke, reports from users; rollback immediately if runtime issues appear. | Open / unassigned |

### Assumptions and limitations

The team size, CI authority, deployment platform, and release operator are not explicitly assigned in the repo materials reviewed, so all launch tasks are left open/unassigned. The repo clearly supports local-first operation and also contains cloud/deployment paths, but a specific deployment target was not assumed for tomorrow. The old Dream Journal benchmark and validator docs were not treated as current source of truth because their file paths and service shape drift from the active Node garage implementation.

---

## References

- [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html)
- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [Anthropic Model Docs](https://docs.anthropic.com/en/docs/about-claude/models/overview)
- [Gemini API Models](https://ai.google.dev/gemini-api/docs/models)
- [OpenTelemetry Traces](https://opentelemetry.io/docs/concepts/signals/traces/)
- PR #173: [batch: merge 14 clean unmerged branches to master](https://github.com/alex-place/lantern-os/pull/173)
- Issue #160: [BUG] `_multi_signal_score()` needs real vector similarity integration
