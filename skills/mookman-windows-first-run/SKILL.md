---
name: mookman-windows-first-run
description: Windows first-run setup and repair skill for Mookman1111 private Lantern OS onboarding, including Git-not-found recovery, $20 wallet receipt discipline, private repo access, and Discord lounge bot health-check gating.
---

# Mookman Windows First-Run Skill

Use this skill when Mookman1111 or another Windows helper cannot clone Lantern OS or gm-agent-orchestrator, especially when PowerShell reports that `git` is not recognized.

## Mission

Get a clean Windows machine from zero to Lantern Desktop without losing private-repo safety, leaking secrets, or pretending payment is investment.

## Core Diagnosis

If PowerShell says:

```text
git : The term 'git' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

then Git is not installed or Git is not on PATH. Do not continue clone commands until Git is fixed.

## Hot Fix Path

1. Install Git for Windows.
2. Close PowerShell.
3. Reopen PowerShell.
4. Run `git --version`.
5. Clone `lantern-os`.
6. Open `surfaces/lantern-desktop/index.html`.
7. Clone `gm-agent-orchestrator` only after GitHub access is confirmed.
8. Report `git status --short --branch` before changing anything.

## Commands For Mookman

Preferred Git install command when winget exists:

```powershell
winget install --id Git.Git -e --source winget
```

Verify after reopening PowerShell:

```powershell
git --version
```

Clone:

```powershell
cd $env:USERPROFILE\Documents
git clone https://github.com/alex-place/lantern-os.git
git clone https://github.com/alex-place/gm-agent-orchestrator.git
```

Open Lantern Desktop:

```powershell
cd $env:USERPROFILE\Documents\lantern-os
start .\surfaces\lantern-desktop\index.html
```

Inspect orchestrator, read-only:

```powershell
cd $env:USERPROFILE\Documents\gm-agent-orchestrator
git status --short --branch
```

## Private Repo Gate

If clone fails after Git is installed, check access before troubleshooting code:

- Mookman is signed into the correct GitHub account.
- Mookman has collaborator access to the private repo.
- HTTPS auth can complete in browser or credential manager.
- No token is pasted into chat, screenshots, PDFs, Discord, or GitHub files.

## $20 Wallet Version

Treat the $20 version as a pilot/support wallet entry, not equity or investment return.

Allowed:

- setup/support payment;
- non-sensitive receipt metadata;
- Discord health-check priority;
- Lantern OS wallet ledger entry.

Forbidden:

- equity claim;
- token claim;
- profit promise;
- admin access purchase;
- secret sharing;
- Discord-to-MCP execution rights.

## Discord Bot Gate

Do not build or run the Discord bot before setup is clean.

Order:

1. Git works.
2. Private repo access works.
3. Lantern Desktop opens.
4. Orchestrator status is reported.
5. Discord token/guild/channel/intents are checked without printing secrets.
6. Only then add status-only `/lantern-status`.

## Definition Of Done

This skill succeeds when:

- Git works on Mookman's machine;
- `lantern-os` clones;
- Lantern Desktop opens;
- orchestrator clone/status is known;
- $20 wallet is either pending or receipted without secrets;
- Discord/MCP remains canary-gated;
- Arc Reactor confidence changes only from evidence.
