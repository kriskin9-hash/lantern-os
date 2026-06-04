# Mookman $20 Wallet Install Fix

Date: 2026-05-26  
Branch: `fix/mookman-20-wallet-version` -> `master`  
Mode: private repo setup repair, no-secrets install path

## Failure Observed

Mookman ran the setup from `C:\Users\micah\Documents`, but Windows returned:

```text
git : The term 'git' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

Because Git was missing, the clone commands did not create either repo folder:

```text
C:\Users\micah\Documents\lantern-os
C:\Users\micah\Documents\gm-agent-orchestrator
```

The later `cd`, `start`, and `git status` commands failed only because the repo folders were never cloned.

## Fix

Install Git for Windows first, then reopen PowerShell.

Preferred command when Windows Package Manager is available:

```powershell
winget install --id Git.Git -e --source winget
```

After Git installs, close PowerShell, open a new PowerShell window, and verify:

```powershell
git --version
```

Then clone the private repos only after GitHub access is confirmed:

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

Inspect orchestrator without changing anything:

```powershell
cd $env:USERPROFILE\Documents\gm-agent-orchestrator
git status --short --branch
```

## $20 Wallet Version Today

The $20 wallet version is ready as a pending pilot/support lane, not equity or an investment return.

Files added in this branch:

```text
offers/MOOKMAN-20-WALLET-VERSION.md
ledger/mookman-20-wallet-version-2026-05-26.yaml
reports/MOOKMAN-20-WALLET-INSTALL-FIX-2026-05-26.md
```

The payment method must be chosen by the operator outside the repo. Do not commit payment secrets, Discord tokens, GitHub tokens, or account recovery information.

## Definition Of Done

1. Mookman installs Git.
2. Mookman reopens PowerShell.
3. `git --version` works.
4. `lantern-os` clones successfully.
5. Lantern Desktop opens.
6. `gm-agent-orchestrator` clones or reports access issue.
7. `$20` receipt metadata is recorded only after payment lands.
8. Arc Reactor confidence increases only if setup/payment evidence changes.
