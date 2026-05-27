# Lantern OS Local Launch and Reboot Runbook

**Status:** local launch runbook  
**Repo:** `alex-place/lantern-os`  
**Default surface:** `surfaces/tony-garage/index.html`

---

## Purpose

Launch the Lantern OS repo app locally from the repo root without assuming GitHub Pages, remote tunnels, or destructive boot actions.

The launcher is:

```powershell
scripts/Start-LanternRepoApp.ps1
```

It serves the repo over localhost when Python is available, opens Tony Garage in the default browser, and optionally schedules a Windows reboot only when explicitly requested.

---

## Safe Launch

From `C:\tmp\lantern-os`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternRepoApp.ps1
```

Default URL:

```text
http://127.0.0.1:8787/surfaces/tony-garage/index.html
```

Use a custom port:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternRepoApp.ps1 -Port 8788
```

Launch without opening a browser:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternRepoApp.ps1 -NoBrowser
```

---

## Reboot Gate

Reboot is not automatic.

To launch and schedule a reboot after five minutes:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternRepoApp.ps1 -RebootAfterLaunch -RebootDelaySeconds 300
```

Abort a scheduled reboot:

```powershell
shutdown /a
```

The script refuses reboot delays under 60 seconds so the operator has time to abort.

---

## Validation Before Reboot

Run these before rebooting:

```powershell
git status --short --branch
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
python C:\Users\alexp\.codex\skills\.system\skill-creator\scripts\quick_validate.py .\skills\super-jarvis-lantern-os
git diff --check -- README.md docs manifests scripts skills reports .github
```

If any command fails, do not reboot for deployment. Fix and re-run the failing check.

---

## Published App Controls

Tony Garage links to:

- unified Super Jarvis skill;
- Apple Pay license wallet report;
- license wallet schema;
- private PIID vault policy;
- local launch/reboot runbook;
- RAG house;
- whitepaper / ADS artifacts;
- wallet ledger.

---

## Boundaries

Do not use this launcher to claim:

- public deployment;
- live Apple Pay checkout;
- live wallet funding;
- production payment processing;
- v1.0.0 release;
- verified MCP tunnel exposure;
- dual boot install completion.

Those require separate validation and explicit operator approval.
