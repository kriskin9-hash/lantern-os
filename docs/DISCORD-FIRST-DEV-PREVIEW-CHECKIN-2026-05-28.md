# Discord-First Dev Preview Check-In

**Status:** candidate public-safe tester handoff  
**Date:** 2026-05-28  
**Surface:** Lantern OS desktop/dev preview  
**Audience:** trusted outside tester using Discord most often

## Decision

Use a Discord-first showcase for the next update.

The tester said they use Discord the most and do not use AI all that much. That means the next useful demo should not lead with a broad Lantern OS theory pitch. It should show one practical loop inside the communication surface they already understand.

## Core message

```text
Lantern OS is not trying to replace Discord, GPT, Claude, or the phone.
It is a local control layer that helps you move between them with less friction.
```

## Demo loop to show

1. Install or open the current desktop preview.
2. Connect or view Discord-style messages.
3. Show how the local assistant reads the situation.
4. Stage a reply or action.
5. Show what is local, dev-only, unsafe, or ready to test.

## Plain-value framing

The point is not:

```text
look at my AI system
```

The point is:

```text
this reduces friction in the apps you already use
```

## Tester safety notes

For the outside tester, treat this as a dev preview, not production:

- do not enter private passwords into anything unfamiliar;
- do not run unknown scripts without asking the operator first;
- do not assume all buttons are finished;
- report where setup is confusing;
- report what feels useful versus fake;
- screenshot errors.

## Public-safe boundary

No NDA is required for the public-safe demo package.

Keep private or IP-sensitive material out of the test package:

- no secrets;
- no tokens;
- no private chat exports unless scrubbed;
- no hidden credentials;
- no unreviewed production claims;
- no claim that the package is secure until packaging and runtime behavior are independently checked.

Use this safer wording instead of overclaiming security:

```text
I am keeping the test package public-safe. Private mechanics and credentials are not included.
```

## Recommended package contents

- `README-FIRST.md`
- one-click start script, if already safe and tested locally;
- known-broken / known-dev section;
- 30-second screenshot or video path;
- visible approval gate before any message is posted;
- rollback/uninstall note;
- no private keys or local-only machine paths unless documented as local examples only.

## Acceptance check

A successful tester check-in should answer:

1. Can they open it?
2. Can they understand what it is for within 60 seconds?
3. Can they see a Discord-style message loop?
4. Can they tell what is real, mocked, local-only, or not ready?
5. Can they report setup confusion without needing to understand the whole Lantern OS system?

## Held validation

- Local preview at `http://127.0.0.1:4177/`: held; requires operator-machine evidence.
- Local MCP health: held.
- Dirty worktree state: held.
- Actual package/start script: held until inspected locally.
- Real Discord integration state: held until verified locally.
