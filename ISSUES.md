# Lantern OS — Common Issues & Fixes

## Deploy

### "Direct push to master is blocked"
**Cause:** Pre-commit hook enforces PR-only workflow.  
**Fix:** Create a feature branch, push, open PR, merge via `gh pr merge --squash --delete-branch`.

### GitHub Actions workflow fails with "actions/checkout@v6 not found"
**Cause:** Non-existent action version.  
**Fix:** Use `@v4` for checkout and `@v5` for setup-python. Fixed in PR #204.

### GitHub Pages shows old version after deploy
**Cause:** CDN cache.  
**Fix:** Wait 2-5 minutes or append `?nocache=1` to URL.

### Netlify deploy rejected (403/422)
**Cause:** Account-level restrictions on free tier.  
**Fix:** Use GitHub Pages as primary static host; review Netlify plan/billing.

---

## Server

### Port 4177 already in use
**Symptom:** `Error: listen EADDRINUSE: address already in use :::4177`  
**Fix:**
```powershell
# Windows
Get-NetTCPConnection -LocalPort 4177 | Select-Object OwningProcess
Stop-Process -Id <PID>

# Or use a different port
$env:PORT=4178; npm run start
```

### AI chat returns "No provider configured"
**Cause:** No API keys set.  
**Fix:** Add at least one key to `.env.local`:
```bash
echo "GEMINI_API_KEY=your_key" > apps/lantern-garage/.env.local
```

### `all_providers_failed` error
**Cause:** All configured providers rejected the request (rate limit, bad key, network).  
**Fix:** Check provider keys, verify internet, check provider status pages, retry.

### Hot reload (`npm run dev`) not picking up changes
**Cause:** `node --watch` can miss rapid edits.  
**Fix:** Save file, wait 1s, or restart manually.

### Docker container exits immediately
**Cause:** Missing env vars or wrong port binding.  
**Fix:**
```bash
docker run -p 8080:8080 -e GEMINI_API_KEY="..." -e PORT=8080 lantern-os
```

---

## Chat

### Messages not appearing after send
**Cause:** Empty state still visible, scroll not triggered, or provider error.  
**Fix:**
- Scroll down in messages area to dismiss empty state
- Check browser console for errors
- Verify at least one provider key is set

### Parallax zoom not working
**Cause:** `.messages` container not scrollable (no scroll height).  
**Fix:** Empty state is `140vh` tall — scroll inside the messages panel, not the page body.

### Voice input (microphone) not responding
**Cause:** Browser permission denied, or no HTTPS on non-localhost.  
**Fix:**
- Grant microphone permission in browser
- Use `http://127.0.0.1:4177` (localhost exempt from HTTPS requirement)
- HTTPS required for mic on custom domains

---

## Git

### "monoworkstream" pre-commit hook blocks commits
**Cause:** An open PR already exists.  
**Fix:**
- Finish or close the existing PR first
- Or commit to the branch that already has an open PR
- Emergency bypass: `SKIP_MONOWORKSTREAM=1 git commit ...`

### Stale `gh-pages` branch diverged from master
**Cause:** Manual edits or failed deploys.  
**Fix:**
```bash
git push origin origin/master:gh-pages --force
```

---

## Convergence Loop

### `convergence-output.json` locked / cannot write
**Cause:** File open in another process.  
**Fix:** File is now in `.gitignore`. Close any editors holding the file lock.

### Missing source repo paths in `TMP-REPO-RAG-INDEX.json`
**Cause:** Paths changed after repo move.  
**Fix:** Update `localFolder` entries in `manifests/TMP-REPO-RAG-INDEX.json` to current absolute paths.

---

## Versioning

### Version badge shows "v1.0.0" instead of current version
**Cause:** Browser cached old `version.json`.  
**Fix:** Hard refresh (Ctrl+Shift+R) or clear cache.

---

## Windows-Specific

### `head` / `tail` command not found in PowerShell
**Cause:** Linux utilities not available in Windows PowerShell.  
**Fix:** Use PowerShell equivalents:
```powershell
# Instead of head -n 5
cat file.txt | Select-Object -First 5

# Instead of tail -n 5
cat file.txt | Select-Object -Last 5
```

### `convergence-output.json` parsing fails with `Select-Object : Property "issues" cannot be found`
**Cause:** JSON structure changed; property is `leadingIssues`, not `issues`.  
**Fix:** Update script to use `.leadingIssues` array.

---

## Reporting New Issues

1. Run `python src/convergence_io_engine.py health` for system state
2. Run `python src/convergence_io_engine.py loop` for full diagnostic
3. Include branch, commit, and OS version in report
