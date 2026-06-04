# Lantern OS Discord Community Operator Packet

Generated: 2026-05-26.

Status: proposed, dry-run only. No live Discord changes have been applied.

Purpose: give the operator a careful, admin-safe plan for setting up a friendly
Lantern OS Discord community around the local garage, RAG house, learning
packets, radio/listening rooms, and project coordination.

## Evidence

| Item | Current State |
|---|---|
| Local repo | `C:\tmp\lantern-os` |
| Community manifest | `manifests/DISCORD-COMMUNITY-CONVERGENCE.md` |
| Dry-run script | `scripts/Invoke-DiscordCommunityDryRun.ps1` |
| Discord token | Present in local environment |
| Voice channel setting | Present in local environment |
| Verified guild/server ID | Not present during last inspection |
| Live server mutation | Not applied |

## Boundary

This packet is for calm community setup. It is not an instruction to broadly
change a live server without review. Live changes require:

- verified target guild/server ID;
- current channel list;
- confirmed bot permissions;
- dry-run output;
- operator approval.

## Recommended Tone

Use warm, simple names:

- home base;
- welcome desk;
- study room;
- workshop;
- listening room;
- project board;
- helper;
- moderator review.

Avoid intense control language. The server should feel like a workshop people
can understand and trust.

## Proposed Server Map

| Category | Channel | Purpose | Setting |
|---|---|---|---|
| Welcome | `#welcome` | Short orientation and tone. | Read-only except moderators. |
| Welcome | `#start-here` | Current links and next step. | Keep short and current. |
| Workshop | `#lantern-garage` | Build updates, screenshots, local app status. | Main project channel. |
| Workshop | `#rag-house` | Sources, RAG intake, evidence labels. | No raw private dumps. |
| Workshop | `#cash-sprint` | Offers, invoices, outreach receipts, objections. | Factual cash state only. |
| Study | `#founder-wisdom` | Priors, evidence maps, careful review, decision cards. | Use consensus checkpoints. |
| Study | `#learning-packets` | School, art, math, and science packets. | Keep protected material private. |
| Audio | `#listening-room` | Radio status, playlists, media notes. | Rights checked first. |
| Audio | `Lounge` | Voice room for music, study, and check-ins. | Bot joins only when invited/configured. |
| Ops | `#ops-log` | Bot status, validation receipts, maintenance notes. | Keep non-secret. |
| Ops | `#moderator-review` | Soft moderation and safety review. | Trusted moderators only. |

## Welcome Message

```text
Welcome to Lantern OS.

This is a small local-first workshop for building useful tools, learning
packets, RAG notes, radio/listening rooms, and careful decision records.

We keep claims labeled, protect private material, and turn ideas into small
validated next steps.
```

## Server Settings

| Setting | Recommendation |
|---|---|
| Verification | Medium if public, low if private/invite-only. |
| Explicit media filter | On for public channels. |
| Default notifications | Mentions only. |
| Community features | Enable only when onboarding is ready. |
| Bot permissions | Least privilege: read/send messages, join/speak in selected voice channels. |
| Message management | Grant only if moderation workflow needs it. |
| Broad admin permissions | Avoid for bots unless reviewed and required. |

## Dry Run

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-DiscordCommunityDryRun.ps1
```

Expected behavior:

- reads the target guild only if `LANTERN_DISCORD_GUILD_ID` is set;
- prints existing and missing channels;
- applies no changes.

## Apply Decision

Do not apply live changes until a dry run shows:

- correct guild/server name;
- expected existing channels;
- exact proposed creates or reviews;
- no unexpected permission escalation.

## Current Decision

Hold live apply.

Reason: a verified guild/server ID was not present during the last inspection.
The correct next move is to set the target guild ID, run the dry run, review the
output, then approve or revise the channel map.
