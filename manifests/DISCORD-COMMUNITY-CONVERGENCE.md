# Discord Community Convergence

Generated: 2026-05-26.

Status: proposed, not applied to a live Discord server.

Evidence:

- `DISCORD_BOT_TOKEN` is present in the local environment.
- `LANTERN_VOICE_CHANNEL` is present in the local environment.
- No verified Discord guild/server ID was present during this pass.
- Existing local Lantern radio files live under `C:\Users\alexp\.lantern`.

Boundary: this packet is for friendly community setup, radio/listening, study
rooms, and project coordination. It is not an instruction to seize, lock down,
or broadly mutate a server. Live changes require current guild evidence and a
bot or user account with appropriate Discord permissions.

## Tone

Use calm, welcoming language. Prefer:

- home base;
- welcome desk;
- study room;
- workshop;
- listening room;
- project board;
- helper;
- moderator review.

## Proposed Channel Map

| Category | Channel | Purpose | Notes |
|---|---|---|---|
| Welcome | `#welcome` | Short orientation and community tone. | Read-only except moderators. |
| Welcome | `#start-here` | Links to Lantern OS, local pages, and current next step. | Keep short and current. |
| Workshop | `#lantern-garage` | Build updates, screenshots, local app status. | Main project channel. |
| Workshop | `#rag-house` | RAG intake, sources, evidence labels, retrieval notes. | No raw private dumps. |
| Workshop | `#cash-sprint` | Offers, invoices, outreach receipts, objections. | Factual cash state only. |
| Study | `#founder-wisdom` | Priors, evidence maps, careful review, decision cards. | Use consensus gates. |
| Study | `#learning-packets` | School/art/math/science packets. | Family/private material stays protected. |
| Audio | `#listening-room` | Radio status, playlists, public-domain/CC media notes. | Rights checked first. |
| Audio | `Lounge` | Voice room for music, study, and check-ins. | Bot joins only when invited/configured. |
| Ops | `#ops-log` | Bot status, validation receipts, maintenance notes. | Keep non-secret. |
| Ops | `#moderator-review` | Soft moderation and safety review. | Limited to trusted moderators. |

## Welcome Text Draft

```text
Welcome to Lantern OS.

This is a small local-first workshop for building useful tools, learning
packets, RAG notes, radio/listening rooms, and careful decision records.

We keep claims labeled, protect private material, and turn ideas into small
validated next steps.
```

## Server Settings Guidance

| Setting | Recommendation |
|---|---|
| Verification | Medium if public, low if private/invite-only. |
| Explicit media filter | On for public channels. |
| Default notifications | Mentions only. |
| Community features | Optional; enable only when public onboarding is ready. |
| Bot permissions | Least privilege: read/send messages, join/speak in selected voice channels, manage messages only if needed. |
| Admin permissions | Avoid broad admin for bots unless required and reviewed. |

## Apply Readiness

Do not apply automatically until:

- target guild/server ID is verified;
- current channel list is read;
- bot permissions are confirmed;
- proposed changes are shown as a dry run;
- operator approves the dry run.

## First Safe Action

Create or update a dry-run script that reads the current server, compares it to
this desired map, and prints the planned creates/renames/permission changes
without applying them.

Dry-run script:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-DiscordCommunityDryRun.ps1
```
