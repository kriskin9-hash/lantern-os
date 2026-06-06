# Dream Journal v1.0.1 — Stability and Honesty Patch

**Release date:** 2026-06-06
**Tag:** `v1.0.1`

---

## Summary

This is a stabilization patch. It does not ship the full interactive 3 Door Game. That feature set remains in progress for a future minor release.

---

## What changed

### Fixed

- **Deterministic agent selection in Dream Chat.** Removed `Math.random()` from `selectAgent()` scoring. The same prompt now routes to the same agent on every run, which improves reproducibility, benchmarking, and user trust.
- **Command handling clarified.** Unsupported bang-commands (e.g., `!report`, `!export`, `!three-doors`) are now explicitly rejected on both the client and server instead of silently behaving like normal chat text.
- **Three Doors UX honesty.** The current flow renders three text suggestions after the assistant response. Docs and messaging no longer overclaim an "image-first" experience that does not yet exist.
- **Provider settings persistence aligned with documented local secret handling.** Settings are now written to `.env.local` instead of `.env` at the repo root. The server also loads `.env.local` before falling back to `.env`.
- **Release notes and user guide corrected** to match actual runtime behavior and data paths. Clarified that provider keys (if configured) send prompts to the respective AI service over HTTPS, and that journal entries live under `data/dream_journal/`.

### Changed

- Release messaging now distinguishes verified local behavior from planned future behavior.
- Launch validation now uses current repo files and current test paths.

---

## Verification

- Local Dream Chat smoke-tested on `apps/lantern-garage`.
- Node Dream Journal API tests passed.
- Multi-turn Dream Chat tests passed.
- Release blockers on master reviewed and either fixed or explicitly held.

---

## Upgrade path

```bash
git checkout master
git pull --ff-only origin master
npm start --prefix apps/lantern-garage
```

Then open **http://127.0.0.1:4177** in your browser.

---

Thank you for being here. Every dream you capture is yours, stored on your machine, waiting to tell you something.
