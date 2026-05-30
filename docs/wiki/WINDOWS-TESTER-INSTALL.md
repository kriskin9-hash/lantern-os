# Windows Tester Install

Status: GitHub Wiki source for a public Windows tester. Copy this page into the
Lantern OS wiki when releases are ready.

Audience: Gage or any Windows tester who asks, "What do I download?"

## Fast Answer

Download from the latest Lantern OS GitHub Release:

```text
https://github.com/alex-place/lantern-os/releases/latest
```

Use this today:

```text
lantern-desktop-tester-latest.zip
```

Future free installer asset, only when attached to the release:

```text
Lantern-OS-Free-Setup.exe
```

Future paid/support installer asset, only after Alex confirms the `$20` support
receipt and the file is attached to the release:

```text
Lantern-OS-Founder-20-Setup.exe
```

## Free Tester

1. Open `https://github.com/alex-place/lantern-os/releases/latest`.
2. Download `lantern-desktop-tester-latest.zip`.
3. Right-click the zip and choose `Extract All`.
4. Open the extracted folder.
5. Run:

```powershell
.\Start-LanternDesktopTester.ps1
```

6. If the browser does not open automatically, go to:

```text
http://127.0.0.1:4177
```

Report whether the dashboard opens, chat responds, links stay inside Lantern,
and the cloud panel does not claim a fake public mirror.

## $20 Founder/Support Tester

The `$20` version is a small founder/setup support lane. It is not equity, not
an investment return, not a token, not ownership, not admin access, and not a
promise of profit.

Payment/support link:

```text
https://ko-fi.com/alexplace
```

After payment clears, Alex records only non-sensitive receipt metadata in the
Lantern wallet ledger. Do not send card numbers, private payment tokens, seed
phrases, recovery codes, Discord bot tokens, or passwords through Lantern.

Install path:

1. Open `https://github.com/alex-place/lantern-os/releases/latest`.
2. Download `Lantern-OS-Founder-20-Setup.exe` only if it is attached there.
3. If it is not attached, download `lantern-desktop-tester-latest.zip`.
4. Run the installer or extract the zip and run
   `.\Start-LanternDesktopTester.ps1`.
5. Open Lantern and test the same front door:

```text
http://127.0.0.1:4177
```

If the founder `.exe` is not attached yet, use the zip. The support receipt
changes the support lane, not the security boundary.

## Zip Install

Use this current release asset:

```text
lantern-desktop-tester-latest.zip
```

Requirements:

```text
Windows 10/11
Node.js 20 or newer
```

Steps:

1. Download `lantern-desktop-tester-latest.zip` from the GitHub Release assets.
2. Right-click the zip and choose `Extract All`.
3. Open the extracted folder.
4. Run:

```powershell
.\Start-LanternDesktopTester.ps1
```

5. Open:

```text
http://127.0.0.1:4177
```

## What To Test

- Dashboard loads at the local front door.
- Chat answers without asking for secrets.
- Art Matrix opens and left/right panel controls work.
- `$1000` demo deck explains what Lantern sells.
- Lantern Reader opens the game-theory/wargame card:

```text
http://127.0.0.1:4177/view?path=manifests/evidence/game-theory-wargame-reader-2026-05-29.md
```

- Cloud panel says AWS is pending unless a verified AWS URL exists.
- Discord/voice features stay health-check gated.
- No old Tony Garage, Render, or random flat-file front page becomes the main
  surface.

## What Not To Enter

Never enter:

- seed phrases;
- private keys;
- card numbers;
- payment credentials;
- Discord bot tokens;
- AWS keys;
- passwords;
- recovery codes.

## Tester Reply Template

```text
I tested Lantern OS on Windows.

Install method:
Free exe / $20 founder exe / zip fallback

Result:
Dashboard opened: yes/no
Chat answered: yes/no
Art Matrix worked: yes/no
Any broken links:
Any confusing copy:
Screenshot attached: yes/no
```
