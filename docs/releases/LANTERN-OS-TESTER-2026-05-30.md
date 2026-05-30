# Lantern OS Tester Release - 2026-05-30

Status: public-safe Windows tester packet, not v1.0.0.

## Release Asset

Attach this file to the GitHub Release:

```text
artifacts/lantern-desktop-tester-latest.zip
```

Current local build:

```text
C:\tmp\lantern-os\artifacts\lantern-desktop-tester-latest.zip
```

Do not list `Lantern-OS-Free-Setup.exe` or
`Lantern-OS-Founder-20-Setup.exe` as available unless those exact release
assets are attached.

## Release Body

```text
Lantern OS Windows tester packet.

Status: public-safe tester build, not v1.0.0.

Download:
lantern-desktop-tester-latest.zip

Requirements:
Windows 10/11
Node.js 20 or newer

Run:
Extract the zip, then run:
.\Start-LanternDesktopTester.ps1

Open:
http://127.0.0.1:4177

Test:
- Dashboard opens.
- Chat answers.
- Demo deck explains what Lantern sells.
- Art Matrix opens.
- Lantern Reader opens public-safe evidence cards.
- Safe command lane shows !one, !converge, !superjarvis, and !near20.
- No screen asks for seed phrases, private keys, payment credentials, Discord tokens, AWS keys, or passwords.

Boundaries:
- This is not v1.0.0.
- No live Kalshi order is submitted by the tester packet.
- Kalshi near-term blocks are paper-only unless a separate authenticated trading lane is built and explicitly approved.
- The $20 founder/support lane is support only, not equity, not securities, not a token, not ownership, not admin access, not an investment return, and not a promise of profit.
- Installer names are future assets only unless attached to this release.
```

## Validation

Latest local validation:

```text
python -m pytest tests/test_command_entrypoint.py tests/test_kalshi_near_term_paper_block.py
```

Result: 7 passed.
